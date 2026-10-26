# `pd3f-core` [![PyPI](https://img.shields.io/pypi/v/pd3f.svg)](https://pypi.org/project/pd3f/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pd3f.svg)](https://pypi.org/project/pd3f/) [![PyPI - Downloads](https://img.shields.io/pypi/dm/pd3f)](https://pypistats.org/packages/pd3f)

_Experimental, use with care._

`pd3f-core` is a Python package to **reconstruct** the original **continuous text** from **PDFs** with language models.
It assumes your PDF is either text-based or already OCRd.
`pd3f-core` is at the heart of [pd3f](https://github.com/pd3f/pd3f), a Docker-based text extraction pipeline that includes OCR and a web interface.

`pd3f-core` first uses [Parsr](https://github.com/axa-group/Parsr) to chunk PDFs into lines and paragraphs.
Then it uses [dehyphen](https://github.com/pd3f/dehyphen) to reconstruct the paragraphs in the most probable way.
The probability is derived from the [perplexity](https://en.wikipedia.org/wiki/Perplexity) of character-based [Flair](https://github.com/flairNLP/flair) language models.
Unnecessary hyphens are removed, and spaces or new lines are kept or dropped depending on the surrounding words.

It is mainly developed for German but works with other languages as well.

## Documentation

- API documentation: <https://pd3f.github.io/pd3f-core/>
- Documentation of the full pipeline: <https://pd3f.com/docs/>

## Features

- **Dehyphenation of lines**: join two lines by removing a hyphen ('-') if the language model prefers the joined word.
- **Joining lines**: decide between a space (' ') and a new line ('\n') when joining lines.
- **Reversing page breaks** (experimental): join the last paragraph of a page with the first paragraph of the next page.
- **Footnotes to endnotes** (experimental): detect footnotes and move them to the end of the text, so the paragraphs around them can be joined.
- **Deduplication of headers and footers** (experimental): headers and footers that repeat on every page are shown once, at the start and the end of the text.
  Similarity is judged by text (Jaccard distance) and by position on the page.

## Installation

Requires Python 3.10 or newer.

```bash
pip install pd3f
```

`pd3f-core` sends every PDF to a Parsr server.
The [`docker-compose.yml`](docker-compose.yml) in this repo starts one on `localhost:3001`, plus the Parsr UI on `localhost:8080`:

```bash
docker compose up
```

The Parsr images are only published for amd64 and run emulated on ARM machines such as Apple Silicon, which is slow.
[`scripts/remote_parsr.sh`](scripts/remote_parsr.sh) starts Parsr on a remote Docker host and tunnels both ports to `localhost`.

## Usage

```python
from pd3f import extract

text, tables = extract(
    "document.pdf",
    tables=False,
    experimental=False,
    force_gpu=False,
    lang="multi",
    fast=False,
    parsr_location="localhost:3001",
)
```

| Parameter | Meaning |
| --- | --- |
| `tables` | Also extract tables. `tables` is then a list of CSV strings, ordered by page; otherwise it is `None`. |
| `experimental` | Turn on the experimental features listed above. |
| `force_gpu` | Raise a `ValueError` if CUDA is not available. |
| `lang` | Flair language model: `de`, `en`, `es`, `fr`, `multi` and others; see [dehyphen](https://github.com/pd3f/dehyphen#usage). Some have a smaller `-fast` variant, e.g. `multi-v0-fast` or `en-fast`. |
| `fast` | Skip Parsr's drawing and image detection. |
| `parsr_location` | Host and port of the Parsr server. |

`parsr_config` and `parsr_adjust_cleaner_config` change the Parsr configuration; see the [API documentation](https://pd3f.github.io/pd3f-core/export.html#pd3f.export.extract).
Further keyword arguments go to [`Export`](https://pd3f.github.io/pd3f-core/export.html#pd3f.export.Export), e.g. `remove_hyphens=False`.

### Models, caches and GPU

The language models are downloaded on first use to `~/.flair`, or to `$FLAIR_CACHE_ROOT` if set.
The scores computed by dehyphen are cached in `~/.cache/pd3f/dehyphen`, which is trimmed to 100 MB whenever `pd3f` is imported.

The models run on a CUDA GPU if PyTorch finds one, otherwise on the CPU.
On x86-64 Linux, `pip install torch` installs the CUDA build; to save the download on machines without a GPU, install the CPU build first:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install pd3f
```

## Parsr configuration

`pd3f-core` builds on Parsr's JSON output; its base configuration is [`pd3f/pd3fConfig.json`](pd3f/pd3fConfig.json).
See [Parsr's module documentation](https://github.com/axa-group/Parsr/tree/master/server/src/processing) for the individual cleaners.

- Parsr's list and heading detection are off because their accuracy was too low.
  The extracted text is therefore flat: no headings, no formatting.
- Drawing and image detection are on, because they help to decide which paragraph follows which.
  `fast=True` turns them off.
- Table detection runs only if `tables=True`.
- `pageNumber` in Parsr's JSON comes from the page-number detection, i.e. from the headers and footers.
  It can differ from the index of the page in the `pages` array; do not rely on it.
- `words-to-line-new` has to come directly before `reading-order-detection`.
  The other order raises no error but lowers the accuracy.
- Do not use Parsr's OCR. [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) preprocesses the images and gives better results; [pd3f](https://github.com/pd3f/pd3f) uses it.

## Development

```bash
poetry install
poetry run ruff check .
poetry run pytest
```

`tests/test_pdfs.py` compares the output for real PDFs (stored with Git LFS) with reference texts.
It needs Parsr on `localhost:3001` and downloads the `multi-v0-fast` models.
`pytest --ignore tests/test_pdfs.py` runs everything else offline.

The API documentation is built with pdoc3 and published to GitHub Pages for every tag, see [`.github/workflows/publish_docs.yml`](.github/workflows/publish_docs.yml).

`development/` holds the notebooks and notes of the original research; they are not maintained.

## License

Affero General Public License 3.0
