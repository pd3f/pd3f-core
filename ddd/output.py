import json
from pathlib import Path

# https://github.com/axa-group/Parsr/blob/365ad388fd5dc7ff9c3fa7db28f45460baa899b0/server/src/output/markdown/MarkdownExporter.ts


def line_to_words(line):
    results = []
    for word in line["content"]:
        if word["type"] == "word":
            results.append(word["content"])
    return results


def fix_lines(lines):
    lines = map(line_to_words, lines)
    return " ".join([" ".join(l) for l in lines]) + "\n\n"


def export_heading(e):
    return e["level"] * "#" + " " + fix_lines(e["content"])


def export_paragraph(e):
    return fix_lines(e["content"])


def export(document, remove_header=True, remove_footer=True):
    txt = ""
    for page in document["pages"]:
        for element in page["elements"]:
            if (
                remove_header
                and "isHeader" in element["properties"]
                and element["properties"]["isHeader"]
            ):
                continue
            if (
                remove_footer
                and "isFooter" in element["properties"]
                and element["properties"]["isFooter"]
            ):
                continue
            if element["type"] == "heading":
                txt += export_heading(element)
            if element["type"] == "paragraph":
                txt += export_paragraph(element)
    return txt


jdata = json.loads(Path("out/data.json").read_text())


txt = export(jdata)

Path("test.txt").write_text(txt)
