from pathlib import Path

from pd3f import extract


def test_fast_experimental():

    for dir in Path("tests/test_data").glob("*"):
        if not dir.is_dir():
            continue
        pdf_path = next(dir.glob("*.pdf"))

        # strip to remove newlines of test files (because files should end with an empty line)
        ouput_text = next(dir.glob("*fast_experimental.txt")).read_text().strip()

        text, _ = extract(
            str(pdf_path),
            tables=False,
            experimental=True,
            lang="multi-v0-fast",
            fast=True,
        )

        assert text.strip() == ouput_text
