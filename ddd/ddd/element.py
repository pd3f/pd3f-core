from .dehyphen import is_split_paragraph


class Document:
    def __init__(self, data, order):
        self.data = data or []
        self.order = order or []

    def __getitem__(self, key):
        return self.data[key]

    def get_element(self, elem):
        return filter(lambda x: x["id"] == elem["id"], self.data).next()

    def join_paragraphs(self):
        """join paragraphs that were split between pages

        gets complicated when footnotes are not re-ordered
        """
        for idx, page in enumerate(self.order[:-1]):
            for para in reversed(page):
                proc_para = self.get_element(para)
                # special because of footnotes
                if proc_para["type"] == "body":
                    next_page_first = self.get_element(self.order[idx + 1][0])
                    if is_split_paragraph(proc_para, next_page_first):
                        pass

    def reorder_footnotes(self):
        new_data = []
        all_footsnotes = []
        for element in self:
            if element.type == "footnotes":
                all_footsnotes.append(element)
            else:
                new_data.append(element)

        self.data = new_data + all_footsnotes

    def markdown(self):
        return self.text(markdown=True)

    def text(self, markdown=False):
        txt = ""
        for element in self.data:
            if markdown and element.type == "heading":
                # prepend dashes
                txt += "#" * element.level + " "
            txt += str(element)
        return txt


class Element:
    def __init__(self, element_type, lines, element_id, level=None):
        assert element_type in ("body", "heading", "footnotes")
        self.type = element_type
        self.lines = lines
        self.id = element_id
        self.level = level

    def __str__(self):
        return "".join([" ".join(line) for line in self.lines]) + "\n\n"

    def dehyphen_join(self, other_element):
        self.lines += other_element.lines
