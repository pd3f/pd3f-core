"""Statistics etc.
"""


from collections import Counter

from .utils import flatten


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


def extract_elements(outer_element, element_type):
    def traverse(element):
        if type(element) is dict:
            if "type" in element and element["type"] == element_type:
                return element
            if "content" in element:
                return traverse(element["content"])
            return None
        if type(element) is list:
            return [traverse(e) for e in element]

    return [
        x for x in flatten(traverse(outer_element), keep_dict=True) if x is not None
    ]


def font_stats(outer_element):
    return [x["font"] for x in extract_elements(outer_element, "word")]


def most_used_font(element):
    return Counter(font_stats(element)).most_common(1)[0][0]


def get_lineheight(l1, l2):
    return l2["box"]["t"] - l1["box"]["t"] - l1["box"]["h"]


class DocumentInfo:
    def __init__(self, input_data, debug) -> None:
        self.input_data = input_data
        self.debug = debug

        self.document_font_stats()
        self.document_paragraph_stats()
        self.element_order_page()

        # free memory (code should have been re-written but whatehver)
        del self.input_data

    def document_paragraph_stats(self):
        """
        """

        def calc_line_space(lines):
            if len(lines) <= 1:
                return []
            lineheights = []
            for i, _ in enumerate(lines[:-1]):
                lineheights.append(get_lineheight(lines[i], lines[i + 1]))
            return lineheights

        self.counter_width = Counter()
        self.counter_height = Counter()
        self.counter_lineheight = Counter()

        for p in self.input_data["pages"]:
            for e in p["elements"]:
                li = extract_elements(e, "line")
                self.counter_width.update([x["box"]["w"] for x in li])
                self.counter_height.update([x["box"]["h"] for x in li])
                self.counter_lineheight.update(calc_line_space(li))

        values = []
        counts = []
        for value, count in self.counter_width.most_common(10):
            values.append(value)
            counts.append(count)

        min_i = None
        for i, _ in enumerate(counts):
            if sum(counts[:i]) > sum(counts) / 2:
                min_i = i
                break

        self.stats_line_width = values[min_i]

        if self.debug:
            print(f"body line width: {self.stats_line_width}")
            print("counter width: ", self.counter_width.most_common(3))
            print("counter height: ", self.counter_height.most_common(3))
            print("counter lineheight: ", self.counter_lineheight.most_common(3))

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

    def is_body_lineheight(self, l1, l2):
        lh = get_lineheight(l1, l2)
        # check!

    def element_order_page(self):
        """Save the order of paragraphes for each page
        """
        self.order_page = []
        self.id_to_elem = {}
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
                self.id_to_elem[e["id"]] = e
            self.order_page.append(per_page)
