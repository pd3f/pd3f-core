import pytest
from dehyphen.dehyphen import Scorer

from pd3f import dehyphen_wrapper, doc_output
from pd3f.doc_output import DocumentOutput, Element


class ShortestScorer(Scorer):
    """Prefers the shortest text, so it joins paragraphs and removes hyphens."""

    def score(self, texts):
        return [len(t) for t in texts]


@pytest.fixture(autouse=True)
def shortest_scorer(monkeypatch):
    monkeypatch.setattr(dehyphen_wrapper, "get_scorer", lambda lang: ShortestScorer())
    # bypass the disk cache
    monkeypatch.setattr(
        doc_output, "is_split_paragraph", dehyphen_wrapper.is_split_paragraph.func
    )


def test_reverse_page_break():
    first = Element("body", [["die", "finan-"]], 1, idx_page=0)
    second = Element("body", [["ziellen "], ["Interessen"]], 2, idx_page=1)
    doc = DocumentOutput([first, second], None, None, [[1], [2]], "de")

    doc.reverse_page_break()

    assert doc.text() == "die finanziellen Interessen\n\n"
    assert doc.get_element(2) is first


def test_joined_paragraph_ends_like_its_second_part():
    first = Element("body", [["die", "finan-"]], 1, idx_page=0)
    second = Element("body", [["ziellen "], ["Mittel.\n"]], 2, ends_newline=True)
    third = Element("body", [["Weiterhin"]], 3, idx_page=2)
    doc = DocumentOutput([first, second, third], None, None, [[1], [2], [3]], "de")

    doc.reverse_page_break()

    assert doc.text() == "die finanziellen Mittel.\n\nWeiterhin\n\n"
    assert first.ends_newline
