import json
from collections import Counter
from pathlib import Path

from tqdm import tqdm

from .dehyphen import dehyphen
from .element import Document, Element
from .utils import flatten

# TODO: What to do with list?

# see this for more
# https://github.com/axa-group/Parsr/blob/365ad388fd5dc7ff9c3fa7db28f45460baa899b0/server/src/output/markdown/MarkdownExporter.ts


def avg_word_space(line):
    # util for words / lines
    # from https://github.com/axa-group/Parsr/blob/69e6b9bf33f1cc43d5a87d428cedf1132ccc48e8/server/src/types/DocumentRepresentation/Paragraph.ts#L460
    def calc_margins(index, word):
        if index > 0:
            return word["box"]["l"] - (
                line["content"][index - 1]["box"]["l"]
                + line["content"][index - 1]["box"]["w"]
            )
        return 0

    margins = [calc_margins(i, w) for i, w in enumerate(line["content"])]
    return sum(margins) / len(margins)


def roughly_same_font(f1, f2):
    assert f1["sizeUnit"] == "px"
    assert f2["sizeUnit"] == "px"
    return abs(f1["size"] - f2["size"]) < max(f1["size"], f2["size"]) * 0.2


def font_stats(outer_element):
    def traverse(element):
        if type(element) is dict:
            if "font" in element:
                return element["font"]
            if "content" in element:
                return traverse(element["content"])
            return None
        if type(element) is list:
            return [traverse(e) for e in element]

    return [x for x in flatten(traverse(outer_element)) if x is not None]


def most_used_font(element):
    return Counter(font_stats(element)).most_common(1)[0][0]


class Export:
    """Process parsr's JSON output into an internal document represeation. This is the beginning of the pipeline.
    Not all the magic is happing here.
    """

    def __init__(
        self,
        input_json,
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

        self.remove_header = remove_header
        self.remove_footer = remove_footer
        self.remove_hyphens = remove_hyphens
        self.footnotes_last = footnotes_last
        self.debug = debug

        # This feature is kind of buggy right now, improve in future.
        # The same looking font is sometimes super different for parsr. Is it a bug?
        self.consider_font_size_linebreak = False

        self.document_font_stats()
        self.element_order_page()

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
                    cleaned_data.append(
                        self.export_paragraph(element, page["pageNumber"])
                    )

        self.doc = Document(cleaned_data, self.order_page)
        self.footnotes_last and self.doc.reorder_footnotes()

        # only do if footnootes are reordered
        self.footnotes_last and self.remove_hyphens and self.doc.reverse_page_break(
            debug=self.debug
        )

    def element_order_page(self):
        """Save the order of paragraphes for each page
        """
        self.order_page = []
        for p in self.input_data["pages"]:
            per_page = []
            for e in p["elements"]:
                if not e["type"] in ("paragraph", "heading"):
                    continue
                if "isHeader" in e["properties"] and e["properties"]["isHeader"]:
                    continue
                if "isFooter" in e["properties"] and e["properties"]["isFooter"]:
                    continue

                per_page.append(e["id"])
            self.order_page.append(per_page)

    def document_font_stats(self):
        """Get statistics about font usage in the document
        """
        c = Counter()
        for p in self.input_data["pages"]:
            for e in p["elements"]:
                c.update(font_stats(e))
        self.body_font = c.most_common(1)[0][0]
        self.font_counter = c
        self.font_info = {}
        for x in self.input_data["fonts"]:
            self.font_info[x["id"]] = x
            assert x["sizeUnit"] == "px"

    def add_linebreak(self, line, next_line, paragraph):
        line_font = most_used_font(line)
        next_line_font = most_used_font(next_line)
        if self.consider_font_size_linebreak and not roughly_same_font(
            self.font_info[line_font], self.font_info[next_line_font]
        ):
            print("font", line_font, next_line_font)
            return True

        avg_space = avg_word_space(line)
        space_para_line = line["box"]["l"] - paragraph["box"]["l"]
        available_space = (
            paragraph["box"]["w"] - line["box"]["w"] - avg_space - space_para_line
        )
        return available_space >= next_line["content"][0]["box"]["w"]

    def line_to_words(self, line):
        results = []
        fonts = []
        for word in line["content"]:
            if word["type"] == "word":
                results.append(word["content"])
                fonts.append(word["font"])
        return results, fonts

    def lines_to_paragraph(self, paragraph, page_number):
        raw_lines = paragraph["content"]
        font_counter = Counter()
        lines = []

        for l in raw_lines:
            rl, rf = self.line_to_words(l)
            lines.append(rl)
            font_counter.update(rf)

        if self.is_footnotes_paragraph(paragraph, font_counter, page_number):
            # don't test on last line
            for i in range(0, len(lines) - 1):
                # decide whether newline or simple space
                if self.add_linebreak(raw_lines[i], raw_lines[i + 1], paragraph):
                    lines[i].append("\n")
                else:
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

            return Element("footnotes", lines, paragraph["id"])
        else:
            # ordinary paragraph
            # don't test on last line
            for i in range(0, len(lines) - 1):
                # decide whether newline or simple space
                if self.add_linebreak(raw_lines[i], raw_lines[i + 1], paragraph):
                    lines[i][-1] += "\n"
                else:
                    lines[i][-1] += " "

            if self.remove_hyphens:
                lines = dehyphen(lines)
            return Element("body", lines, paragraph["id"])

    def export_heading(self, e):
        raw_lines = e["content"]
        lines = []
        for l in raw_lines:
            rl, _ = self.line_to_words(l)
            lines.append(rl)
        return Element("heading", lines, e["id"], e["level"])

    def export_paragraph(self, e, page_number):
        return self.lines_to_paragraph(e, page_number)

    def is_footnotes_paragraph(self, paragraph, counter, page_number):
        # TODO: more heuristic: 1. do numbers appear in text? 2. is there a drawing in it
        para_font = counter.most_common(1)[0][0]

        # footnotes has to be different
        if para_font == self.body_font:
            return False

        # footnotes has to be smaller
        if self.font_info[para_font]["size"] > self.font_info[self.body_font]["size"]:
            return False

        # check if this is the last paragraph
        return self.order_page[page_number - 1][-1] == paragraph["id"]

    def save_markdown(self, output_path):
        Path(output_path).write_text(self.doc.markdown())

    def save_text(self, output_path):
        Path(output_path).write_text(self.doc.text())
