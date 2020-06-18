import json
from pathlib import Path
from collections import Counter

from .utils import flatten

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


class Export:
    def __init__(self, input_json, remove_header=True, remove_footer=True):
        self.input_data = json.loads(Path(input_json).read_text())
        self.remove_header = remove_header
        self.remove_footer = remove_footer

        self.font_stats()
        self.export()

    def export(self):
        cleaned_data = []
        for page in self.input_data["pages"]:
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
                    cleaned_data.append(self.export_paragraph(element))

        self.export_data = cleaned_data

    def font_stats(self):
        """Get statistics about font usage
        """

        def traverse(element):
            if type(element) is dict:
                if "font" in element:
                    return element["font"]
                if "content" in element:
                    return traverse(element["content"])
                return None
            if type(element) is list:
                return [traverse(e) for e in element]

        c = Counter()
        for p in self.input_data["pages"]:
            for e in p["elements"]:
                res = [x for x in flatten(traverse(e)) if x is not None]
                c.update(res)
        self.font_counter = c
        print(c)

    def add_linebreak(self, line, next_line, paragraph):
        avg_space = avg_word_space(line)
        space_para_line = line["box"]["l"] - paragraph["box"]["l"]
        available_space = (
            paragraph["box"]["w"] - line["box"]["w"] - avg_space - space_para_line
        )
        return available_space >= next_line["content"][0]["box"]["w"]

    def line_to_words(self, line, as_string=False):
        results = []
        for word in line["content"]:
            if word["type"] == "word":
                results.append(word["content"])

        if as_string:
            return " ".join(results)
        return results

    def lines_to_paragraph(self, paragraph):
        lines = paragraph["content"]
        string_lines = [self.line_to_words(l) for l in lines]

        if self.detect_footnotes(paragraph):
            pass

        # don't test on last line
        for i in range(0, len(lines) - 1):
            # decide whether newline or simple space
            if self.add_linebreak(lines[i], lines[i + 1], paragraph):
                string_lines[i].append("\n")
            else:
                string_lines[i].append(" ")

        return {"lines": string_lines, "type": "body"}

    def to_markdown(self):
        return self.to_text(markdown=True)

    def to_text(self, markdown=False):
        txt = ""
        for l in self.export_data:
            if markdown and l["type"] == "heading":
                # prepend dashes
                txt += "#" * l["level"] + " "
            if l["type"] == "body" or l["type"] == "heading":
                txt += "".join([" ".join(line) for line in l["lines"]]) + "\n\n"
        return txt

    def export_heading(self, e):
        return {
            "lines": self.lines_to_paragraph(e)["lines"],
            "type": "heading",
            "level": e["level"],
        }

    def export_paragraph(self, e):
        return self.lines_to_paragraph(e)

    def save_text(self, output_path):
        Path(output_path).write_text(self.to_text())

    def save_markdown(self, output_path):
        Path(output_path).write_text(self.to_markdown())

    def detect_footnotes(self, paragraph):
        pass

    # based on font: (smaller)
    # location bottom
