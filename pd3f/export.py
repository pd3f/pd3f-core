"""Main class of this package.

Transforms parsr's JSON to an internal document format, exports to text.
"""

import json
import logging
import string
from collections import Counter
from functools import cached_property
from pathlib import Path

from cleantext import clean, fix_bad_unicode

from .dehyphen_wrapper import dehyphen_paragraph, newline_or_not
from .doc_info import (
    DocumentInfo,
    avg_word_space,
    most_used_font,
    remove_duplicates,
    roughly_same_font,
    remove_page_number_header_footer,
)
from .doc_output import DocumentOutput, Element
from .parsr_wrapper import run_parsr

logger = logging.getLogger(__name__)


def extract(
    file_path,
    tables=False,
    experimental=False,
    force_gpu=False,
    lang="multi",
    parsr_location="localhost:3001",
    fast=False,
    **kwargs,
):
    """Outward facing api
    """
    if force_gpu:
        import torch

        if not torch.cuda.is_available():
            raise ValueError("not using CUDA (GPU)")
        else:
            logger.debug("using CUDA")

    input_json, tables_csv = run_parsr(
        file_path, check_tables=tables, parsr_location=parsr_location, fast=fast
    )
    e = Export(
        input_json,
        seperate_header_footer=experimental,
        footnotes_last=experimental,
        remove_page_number=experimental,
        lang=lang,
        fast=fast,
        **kwargs,
    )
    return e.text(), tables_csv


class LinesWithNone:
    """Utility class to make it easier to work with lines that may be None (invalid).
    """

    def __init__(self, lines, raw_lines) -> None:
        self.lines = lines
        self.raw_lines = raw_lines
        self.first_line = 0
        self.last_line = len(lines) - 1

        for l in lines:
            if l is None:
                self.first_line += 1
            else:
                break

        for l in reversed(lines):
            if l is None:
                self.last_line -= 1
            else:
                break

    def __getitem__(self, key):
        return self.lines[key]

    @cached_property
    def valid(self):
        return [l for l in self.lines if not l is None]

    def __iter__(self):
        self.cur = self.first_line
        return self

    def __next__(self):
        if self.cur <= self.last_line:
            cur_tmp = self.cur
            while self.cur <= self.last_line:
                self.cur += 1
                if len(self.lines) == self.cur or not self.lines[self.cur] is None:
                    break
            return cur_tmp
        else:
            raise StopIteration

    def __len__(self):
        return len(self.valid)


class Export:
    """Process parsr's JSON output into an internal document represeation. This is the beginning of the pipeline.
    Not all the magic is happing here.
    """

    def __init__(
        self,
        input_json,
        remove_punct_paragraph=True,
        seperate_header_footer=True,
        remove_duplicate_header_footer=True,
        remove_page_number=True,
        remove_header=False,
        remove_footer=False,
        remove_hyphens=True,
        footnotes_last=True,
        ocrd=None,
        lang="multi",
        fast=False,
    ):
        if type(input_json) is str:
            self.input_data = json.loads(Path(input_json).read_text())
        elif isinstance(input_json, Path):
            self.input_data = json.loads(input_json.read_text())
        elif type(input_json) is dict:
            self.input_data = input_json
        else:
            raise ValueError("problem with reading input json data")

        self.remove_punct_paragraph = remove_punct_paragraph
        self.seperate_header_footer = seperate_header_footer
        self.remove_duplicate_header_footer = remove_duplicate_header_footer
        self.remove_page_number = remove_page_number
        self.remove_header = remove_header
        self.remove_footer = remove_footer
        self.remove_hyphens = remove_hyphens
        self.footnotes_last = footnotes_last
        self.ocrd = ocrd  # not used atm
        self.lang = lang  # name of Flair model (where the language is included)

        if seperate_header_footer and any((remove_footer, remove_header)):
            raise ValueError(
                "if `seperate_header_footer=True` cannot remove header/footer"
            )

        # This feature is kind of buggy right now, improve in future.
        # The same looking font is sometimes super different for OCRd PDFs. Is it a bug?
        self.consider_font_size_linebreak = False

        if fast:
            # In the fast mode, not all elments are classified via Parsr. So we may have some leftover values with None.
            # pd3f-core only works with non-none elements so remove them here.

            # FIXME: This is dirty because `fast` is also encoded in `lang`
            self.delete_none_elements()

        self.info = DocumentInfo(self.input_data)
        self.fix_headers_footers()
        self.export()

    def delete_none_elements(self):
        for p in self.input_data["pages"]:
            p["elements"] = list(filter(None, p["elements"]))

    def export_header_footer(self):
        headers, footers = [], []

        for idx_page, page in enumerate(self.input_data["pages"]):
            header_per_page, footer_per_page = [], []
            for element in page["elements"]:
                if (
                    "isHeader" in element["properties"]
                    and element["properties"]["isHeader"]
                ):
                    header_per_page.append(element)

                if (
                    "isFooter" in element["properties"]
                    and element["properties"]["isFooter"]
                ):
                    footer_per_page.append(element)
            headers.append(header_per_page)
            footers.append(footer_per_page)

        if self.remove_duplicate_header_footer:
            headers = remove_duplicates(headers, self.lang)
            footers = remove_duplicates(footers, self.lang)

        cleaned_header, cleaned_footer, footnotes = [], [], []
        for idx_page, (header_per_page, footer_per_page) in enumerate(
            zip(headers, footers)
        ):
            for e in header_per_page:
                result_para = self.export_paragraph(e, idx_page, test_footnote=False)
                result_para and cleaned_header.append(result_para)

            for e in footer_per_page:
                result_para = self.export_paragraph(e, idx_page)
                if result_para is not None:
                    if result_para.type == "footnotes":
                        footnotes.append(result_para)
                    else:
                        cleaned_footer.append(result_para)

        return cleaned_header, cleaned_footer, footnotes

    def fix_headers_footers(self):
        """The output for header and footer for Parsr is not the best. Make use of some simple heuristics based on the font to improve it.
        """
        for idx_page, page in enumerate(self.input_data["pages"]):
            for idx_e, e in enumerate(page["elements"]):
                if "isHeader" in e["properties"] and e["properties"]["isHeader"]:
                    if self.info.is_body_paragrah(e):
                        del self.input_data["pages"][idx_page]["elements"][idx_e][
                            "properties"
                        ]["isHeader"]
                if "isFooter" in e["properties"] and e["properties"]["isFooter"]:
                    if self.info.is_body_paragrah(e):
                        del self.input_data["pages"][idx_page]["elements"][idx_e][
                            "properties"
                        ]["isFooter"]

    def export(self):
        cleaned_header, cleaned_footer, new_footnotes = None, None, None

        if self.seperate_header_footer:
            cleaned_header, cleaned_footer, new_footnotes = self.export_header_footer()

        cleaned_data = []
        for idx_page, page in enumerate(self.input_data["pages"]):
            logger.info(f"export page #{idx_page}")
            for element in page["elements"]:
                if (
                    (self.seperate_header_footer or self.remove_header)
                    and "isHeader" in element["properties"]
                    and element["properties"]["isHeader"]
                ):
                    continue
                if (
                    (self.seperate_header_footer or self.remove_footer)
                    and "isFooter" in element["properties"]
                    and element["properties"]["isFooter"]
                ):
                    continue
                # currently not used
                if element["type"] == "heading":
                    cleaned_data.append(self.export_heading(element))
                if element["type"] == "paragraph":
                    result_para = self.export_paragraph(element, idx_page)
                    result_para and cleaned_data.append(result_para)

            # only append new foofnotes here, most likel get reorced anyhow
            if new_footnotes is not None:
                footer_on_this_page = [
                    x for x in new_footnotes if x.idx_page == idx_page
                ]
                cleaned_data += footer_on_this_page

        if self.remove_page_number:
            cleaned_header = remove_page_number_header_footer(cleaned_header)
            cleaned_footer = remove_page_number_header_footer(cleaned_footer)

        self.doc = DocumentOutput(
            cleaned_data,
            cleaned_header,
            cleaned_footer,
            self.info.order_page,
            self.lang,
        )
        self.footnotes_last and self.doc.reorder_footnotes()

        # only do if footnootes are reordered
        self.footnotes_last and self.remove_hyphens and self.doc.reverse_page_break()

    def add_linebreak(
        self, line, next_line, text_line, text_next_line, paragraph, num_lines
    ):
        # experimental
        if self.consider_font_size_linebreak:
            line_font = most_used_font(line)
            next_line_font = most_used_font(next_line)
            if not roughly_same_font(
                self.info.font_info[line_font], self.info.font_info[next_line_font]
            ):
                logger.debug(" ".join("font", line_font, next_line_font))
                return True

        avg_space = avg_word_space(line)
        space_para_line = line["box"]["l"] - paragraph["box"]["l"]
        available_space = (
            paragraph["box"]["w"] - line["box"]["w"] - avg_space - space_para_line
        )

        # if there is no next line
        if next_line is None or not next_line or text_next_line is None:
            if available_space > avg_space:
                # if text_line[-1].strip()[-1] in string.punctuation:
                logger.debug(
                    f"No next line, but adding \\n, avail space: {available_space} avg space: {avg_space} {text_line}"
                )
                return True
            else:
                if num_lines == 1:
                    return True
                # if num_lines == 2:
                #     return True
                logger.debug(f"No next line, but adding space {text_line}")
                return False

        if available_space >= next_line["content"][0]["box"]["w"]:
            logger.debug(
                f"There is enough space on the lext for the next word. So adding a linebreak between {text_line}{text_next_line}"
            )
            return True

        if self.info.on_same_page(line, next_line):
            if self.info.seperate_lines(line, next_line):
                logger.debug("lines should be seperated")
                logger.debug(f"{text_line} {text_next_line}")
                return True

        # TODO: a more reasonable way (e.g. check if it spans whole width)
        if len(text_line) > 5:
            return False

        # if it ends with a string, it most likly that flair test will fail anyhow
        if text_line[-1].strip()[-1] in string.punctuation:
            return False

        logger.debug("testing the lines: ")
        logger.debug(f"{text_line} {text_next_line}")
        return newline_or_not(" ".join(text_line), " ".join(text_next_line), self.lang)

    def line_to_words(self, line):
        words, fonts = [], []
        for word in line["content"]:
            if word["type"] == "word":
                w_fixed = word["content"]
                w_fixed = fix_bad_unicode(w_fixed).strip()
                words.append(w_fixed)
                fonts.append(word["font"])
        return words, fonts

    def lines_to_paragraph(self, paragraph, idx_page, test_footnote):
        def no_alphanum_char(text):
            """Checks if text only contains non-alpha-num chars, e.g. puncts
            """
            text = clean(text, no_punct=True)
            return any([x.isalnum() for x in text])

        raw_lines = paragraph["content"]
        font_counter = Counter()
        lines = []

        for l in raw_lines:
            rl, rf = self.line_to_words(l)

            if len(rl) == 0:
                lines.append(None)
            else:
                # "".isalnum() => False, so only check for lenth?
                if not self.remove_punct_paragraph or any(map(no_alphanum_char, rl)):
                    lines.append(rl)
                    font_counter.update(rf)
                else:
                    logger.debug(f"removing {rl} because not alpha num")
                    lines.append(None)

        lines = LinesWithNone(lines, raw_lines)

        # NB: the returned paragraph can be None (invalid)
        if len(lines.valid) == 0:
            return None

        if test_footnote and self.is_footnotes_paragraph(
            paragraph, font_counter, idx_page, lines
        ):
            # don't test on last line
            for i in list(lines)[:-1]:
                # decide whether newline or simple space
                if self.add_linebreak(
                    raw_lines[i],
                    raw_lines[i + 1],
                    lines[i],
                    lines[i + 1],
                    paragraph,
                    len(lines),
                ):
                    lines[i].append("\n")
                else:
                    # skip if next line was removed
                    if lines[i + 1] is None:
                        lines[i].append("\n")
                        continue
                    # if the first chars are digits -> footnote
                    # but ensure that the first digit has a different font then the last word on the previous line
                    if (
                        lines[i][0].isnumeric()
                        and lines[i + 1][0].isnumeric()
                        and raw_lines[i + 1]["content"][0]["font"]
                        != raw_lines[i]["content"][-1]["font"]
                    ):
                        lines[i].append("\n")
                    else:
                        lines[i].append(" ")
            # TODO: dehyphen
            return Element("footnotes", lines.valid, paragraph["id"], idx_page=idx_page)
        else:
            # ordinary paragraph
            num_newlines = 0
            ends_newline = False
            # don't test on last line
            for i in lines:
                # decide whether newline or simple space
                if self.add_linebreak(
                    raw_lines[i],
                    i != lines.last_line and raw_lines[i + 1],
                    lines[i],
                    i != lines.last_line and lines[i + 1],
                    paragraph,
                    len(lines),
                ):
                    lines[i][-1] += "\n"
                    logger.debug(f"adding newline here {lines[i]}")
                    num_newlines += 1
                    if i == lines.last_line:
                        ends_newline = True
                else:
                    if i == lines.last_line:
                        logger.debug("last line, not adding space")
                    else:
                        lines[i][-1] += " "

            # finally remove Nones here
            lines = lines.valid

            if self.remove_hyphens:
                lines = dehyphen_paragraph(lines, lang=self.lang)

            return Element(
                "body",
                lines,
                paragraph["id"],
                idx_page=idx_page,
                num_newlines=num_newlines,
                ends_newline=ends_newline,
            )

    # not working right now
    def export_heading(self, e):
        raw_lines = e["content"]
        lines = []
        for l in raw_lines:
            rl, _ = self.line_to_words(l)
            lines.append(rl)
        return Element("heading", lines, e["id"], e["level"])

    def export_paragraph(self, e, idx_page, test_footnote=True):
        return self.lines_to_paragraph(e, idx_page, test_footnote)

    def is_footnotes_paragraph(self, paragraph, counter, idx_page, lines):
        # TODO: more heuristic: 1. do numbers appear in text? 2. is there a drawing in it
        # right now it expects the footnote paragraph to consists of a single paragraph

        para_font = counter.most_common(1)[0][0]

        # footnotes has to be different
        if para_font == self.info.body_font:
            return False

        # footnotes has to be smaller
        if (
            self.info.font_info[para_font]["size"]
            > self.info.font_info[self.info.body_font]["size"]
        ):
            return False

        # can't be empty
        if len(self.info.order_page[idx_page]) == 0:
            return False

        # check if this is the last paragraph
        if self.info.order_page[idx_page][-1] != paragraph["id"]:
            return False

        # if the previous element ends with `:` it expects something, so it can't be the last paragraph
        if len(self.info.order_page[idx_page]) > 1:
            prev_elem = self.info.id_to_elem[self.info.order_page[idx_page][-2]]
            prev_elem_words, _ = self.line_to_words(prev_elem["content"][-1])
            if prev_elem_words[-1].endswith(":"):
                logger.debug(f"Id of cur para: {paragraph['id']}")
                logger.debug(
                    f"not a footnote para because of : in {prev_elem_words[-1]}"
                )
                return False

        # first line has to start with a numeral
        if not lines.valid[0][0].strip()[0].isnumeric():
            return False

        return True

    def markdown(self):
        return self.doc.markdown()

    def text(self):
        return self.doc.text()

    def save_markdown(self, output_path):
        Path(output_path).write_text(self.markdown())

    def save_text(self, output_path):
        Path(output_path).write_text(self.text())
