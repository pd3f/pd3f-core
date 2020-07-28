import json
import string
from collections import Counter
from pathlib import Path

from cleantext import clean
from tqdm import tqdm

from .dehyphen import dehyphen, newline_or_not
from .docinfo import DocumentInfo, avg_word_space, most_used_font, roughly_same_font
from .element import Document, Element

# see this for more
# https://github.com/axa-group/Parsr/blob/365ad388fd5dc7ff9c3fa7db28f45460baa899b0/server/src/output/markdown/MarkdownExporter.ts


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
                if not self.cur is None:
                    break
            return cur_tmp
        else:
            raise StopIteration

    def __len__(self):
        return len(self.valid())


class Export:
    """Process parsr's JSON output into an internal document represeation. This is the beginning of the pipeline.
    Not all the magic is happing here.
    """

    def __init__(
        self,
        input_json,
        remove_punct_paragraph=True,
        remove_header=True,
        remove_footer=True,
        remove_hyphens=True,
        footnotes_last=True,
        debug=False,
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
        self.remove_header = remove_header
        self.remove_footer = remove_footer
        self.remove_hyphens = remove_hyphens
        self.footnotes_last = footnotes_last
        self.debug = debug

        # This feature is kind of buggy right now, improve in future.
        # The same looking font is sometimes super different for OCRd PDFs. Is it a bug?
        self.consider_font_size_linebreak = False

        self.info = DocumentInfo(self.input_data, self.debug)

        self.export()

    def export(self):
        cleaned_data = []
        for page in tqdm(self.input_data["pages"], desc="exporting pages"):
            for element in page["elements"]:
                if (
                    self.remove_header
                    and "isHeader" in element["properties"]
                    and element["properties"]["isHeader"]
                ):
                    continue
                if (
                    self.remove_footer
                    and "isFooter" in element["properties"]
                    and element["properties"]["isFooter"]
                ):
                    continue
                if element["type"] == "heading":
                    cleaned_data.append(self.export_heading(element))
                if element["type"] == "paragraph":
                    result_para = self.export_paragraph(element, page["pageNumber"])
                    result_para and cleaned_data.append(result_para)

        self.doc = Document(cleaned_data, self.info.order_page)
        self.footnotes_last and self.doc.reorder_footnotes()

        # only do if footnootes are reordered
        self.footnotes_last and self.remove_hyphens and self.doc.reverse_page_break(
            debug=self.debug
        )

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
                print("font", line_font, next_line_font)
                return True

        avg_space = avg_word_space(line)
        space_para_line = line["box"]["l"] - paragraph["box"]["l"]
        available_space = (
            paragraph["box"]["w"] - line["box"]["w"] - avg_space - space_para_line
        )

        # if there is no next line
        if next_line is None or not next_line:
            if available_space > avg_space:
                # if text_line[-1].strip()[-1] in string.punctuation:
                if self.debug:
                    print(f"No next line, but adding \\n {text_line}")
                return True
            else:
                if num_lines == 1:
                    return True
                # if num_lines == 2:
                #     return True
                if self.debug:
                    print(f"No next line, but adding space {text_line}")
                return False

        if available_space >= next_line["content"][0]["box"]["w"]:
            if self.debug:
                print(
                    f"There is enough space on the lext for the next word. So adding a linebreak between {text_line}{text_next_line}"
                )
            return True

        # get_max_lineheight of paragrah

        # TODO: a more reasonable way (e.g. check if it spans whole width)
        if len(text_line) > 5:
            return False

        # if it ends with a string, it most likle the flair test will fail anyhow
        if text_line[-1].strip()[-1] in string.punctuation:
            return False

        if self.debug:
            print("testing the lines: ")
            print(text_line, text_next_line)
        return newline_or_not(" ".join(text_line), " ".join(text_next_line))

    def line_to_words(self, line):
        words = []
        fonts = []
        for word in line["content"]:
            if word["type"] == "word":
                words.append(word["content"])
                fonts.append(word["font"])
        return words, fonts

    def lines_to_paragraph(self, paragraph, page_number):
        raw_lines = paragraph["content"]
        font_counter = Counter()
        lines = []

        for l in raw_lines:
            rl, rf = self.line_to_words(l)

            # "".isalnum() => False, so only check for lenth?
            if not self.remove_punct_paragraph or any(
                [clean(x, no_punct=True).isalnum() for x in rl]
            ):
                lines.append(rl)
                font_counter.update(rf)
            else:
                if self.debug:
                    print(f"removing {rl} because not alpha num")
                lines.append(None)

        lines = LinesWithNone(lines, raw_lines)

        # NB: the returned paragraph can be None (invalid)
        if len(lines.valid()) == 0:
            return None

        if self.is_footnotes_paragraph(paragraph, font_counter, page_number, lines):
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
            return Element("footnotes", lines.valid(), paragraph["id"])
        else:
            # ordinary paragraph
            num_newlines = 0
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
                    if self.debug:
                        print(f"adding newline here {lines[i]}")
                    num_newlines += 1
                else:
                    lines[i][-1] += " "

            # finally remove Nones here
            lines = lines.valid()
            if self.remove_hyphens:
                lines = dehyphen(lines)
            return Element("body", lines, paragraph["id"], num_newlines=num_newlines)

    # not looking for headings right now
    def export_heading(self, e):
        raw_lines = e["content"]
        lines = []
        for l in raw_lines:
            rl, _ = self.line_to_words(l)
            lines.append(rl)
        return Element("heading", lines, e["id"], e["level"])

    def export_paragraph(self, e, page_number):
        return self.lines_to_paragraph(e, page_number)

    def is_footnotes_paragraph(self, paragraph, counter, page_number, lines):
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

        # check if this is the last paragraph
        if self.info.order_page[page_number - 1][-1] != paragraph["id"]:
            return False

        # if the previous element ends with `:` it expects something, so it can't be the last paragraph
        if len(self.info.order_page[page_number - 1]) > 1:
            prev_elem = self.info.id_to_elem[self.info.order_page[page_number - 1][-2]]
            prev_elem_words, _ = self.line_to_words(prev_elem["content"][-1])
            if prev_elem_words[-1].endswith(":"):
                if self.debug:
                    print(f"Id of cur para: {paragraph['id']}")
                    print(f"not a footnote para because of : in {prev_elem_words[-1]}")
                return False

        # first line has to start with a numeral
        if not lines.valid()[0][0].strip()[0].isnumeric():
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
