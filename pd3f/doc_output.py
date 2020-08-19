"""Document represenation after extraction stuff from parsr
"""

import logging
import re

from .dehyphen_wrapper import is_split_paragraph
from .utils import flatten

logger = logging.getLogger(__name__)


class DocumentOutput:
    def __init__(self, data, header, footer, order, lang):
        self.data = data or []
        self.header = header or []
        self.footer = footer or []
        self.order = order or []
        self.lang = lang
        self.merged_elements = {}

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def get_element(self, elem_id):
        """Returns element from the data. Returns `None` if the element is not part out of the output anymore.
        """
        if elem_id in self.merged_elements:
            elem_id = self.merged_elements[elem_id]
        result = list(filter(lambda x: x.id == elem_id, self))

        # `result` may be empty if the elem was port of footer / header and is gone now (due to dudeplication)
        if len(result) == 1:
            return result[0]
        return None

    def get_first_of_type_on_page(self, find_types, idx_page):
        for ele_id in self.order[idx_page]:
            ele = self.get_element(ele_id)
            if ele is None:
                continue
            if ele.type in find_types:
                return ele
        return None

    def get_last_of_type_on_page(self, find_types, idx_page):
        for ele_id in reversed(self.order[idx_page]):
            ele = self.get_element(ele_id)
            if ele is None:
                continue
            if ele.type in find_types:
                return ele
        return None

    def reverse_page_break(self):
        """join paragraphs that were split between pages

        gets complicated when footnotes are not re-ordered
        """
        for idx, page in enumerate(self.order[:-1]):
            logger.info(f"reversing page break page #{idx}")
            last_element = self.get_last_of_type_on_page(("body", "heading"), idx)
            next_element = self.get_first_of_type_on_page(("body", "heading"), idx + 1)

            if last_element is None or next_element is None:
                logger.debug("some element is none, cannot test")
                continue

            if last_element.type == "heading" or next_element.type == "heading":
                logger.debug("some element is a header, cannot test")
                continue

            # It cannot contain newlines
            if last_element.ends_newline:
                logger.debug(
                    f"the last element has ends with a newline. Do not try to join with the next one."
                )
                continue

            fixed = is_split_paragraph(last_element, next_element, self.lang)
            if fixed is None:
                logger.debug("looks like a split paragraph")
                continue

            logger.debug("joining the following paragraphs")
            logger.debug(f"{last_element}\n{next_element}\n{fixed}")

            # set new paragraph
            self[self.data.index(last_element)] = fixed
            self.data.remove(next_element)
            self.merged_elements[next_element.id] = last_element.id

    def reorder_footnotes(self):
        new_data, all_footsnotes = [], []
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

        txt += "\n\n".join([str(x) for x in flatten(self.header)])

        for element in self:
            if markdown and element.type == "heading":
                # prepend dashes
                txt += "#" * element.level + " "
            txt += str(element)

        txt += "\n\n".join([str(x) for x in flatten(self.footer)])

        # hotfix, there are sometimes too many newlines
        txt = re.sub(r"(\n){3,}", "\n\n", txt)
        return txt


class Element:
    def __init__(
        self,
        element_type,
        lines,
        element_id,
        idx_page=None,
        num_newlines=0,
        level=None,
        ends_newline=None,
    ):
        assert element_type in ("body", "heading", "footnotes")
        self.type = element_type
        self.lines = lines
        self.id = element_id
        self.level = level
        self.idx_page = idx_page
        self.num_newlines = num_newlines
        self.ends_newline = ends_newline

        for x in lines:
            assert len(x) > 0

    def __getitem__(self, key):
        return self.lines[key]

    def __str__(self):
        # FIXME
        if self.type == "footnotes":
            return "".join([" ".join(line) for line in self.lines]) + "\n"
        return "".join([" ".join(line) for line in self.lines]) + "\n\n"

    def __add__(self, other_element):
        assert self.type == other_element.type
        self.lines += other_element.lines
        return self

    def __len__(self):
        return len(self.lines)
