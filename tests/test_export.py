from pd3f.doc_output import DocumentOutput
from pd3f.export import Export


def line(*words):
    return {
        "type": "line",
        "content": [{"type": "word", "content": w, "font": 1} for w in words],
    }


def test_export_heading():
    heading = {
        "id": 1,
        "type": "heading",
        "level": 2,
        "content": [line("1.", "Streitbeilegung", "durch"), line("das", "Ministerium")],
    }
    element = Export.__new__(Export).export_heading(heading)
    doc = DocumentOutput([element], None, None, [], "de")

    assert doc.markdown() == "## 1. Streitbeilegung durch das Ministerium\n\n"
