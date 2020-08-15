# `pd3f-core` [![PyPI](https://img.shields.io/pypi/v/pd3f.svg)](https://pypi.org/project/pd3f/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pd3f.svg)](https://pypi.org/project/pd3f/) [![PyPI - Downloads](https://img.shields.io/pypi/dm/pd3f)](https://pypistats.org/packages/pd3f)

*Experimental, use with care.*

Python Package to **reconstruct** the original **continuous text** from **PDFs** with language models.
`pd3f-core` assumes your PDF is either text-based or already OCRd.
Checkout out [pd3f](https://github.com/pd3f/pd3f) for a full Docker-based text extraction pipeline using `pd3f-core`.

👉 [pd3f - PDF Text Extractor](https://github.com/pd3f/pd3f)

`pd3f-core` first uses [Parsr](https://github.com/axa-group/Parsr) to chunk PDFs into lines and paragraphs.
Then, it uses the Python package [dehyphen](https://github.com/jfilter/dehyphen) to reconstruct the paragraphs in the most probable way.
The probability is derived by calculating the [perplexity](https://en.wikipedia.org/wiki/Perplexity) with [Flair](https://github.com/flairNLP/flair)'s character-based [language models](https://machinelearningmastery.com/statistical-language-modeling-and-neural-language-models/).
Unnecessary hyphens are removed, space or new lines are kept or dropt depending on the surround words.

It's mainly developed for German but should work with other languages as well.
The project is still in an early stage.
Expect rough edges and rapid changes.
Documentation will get improved (at some point).

## Features

### Dehyphenation of Lines

Check if two lines can be joined by removing hyphens ('-').

### Reasonable Joining of Lines

Decide between adding a simple space (' ') or a new line ('\n') when joining lines.

### Reverse Page Break (Experimental)

Check if the last paragraph of a page und the first paragraph of the following page can be joined.

### Footnote to Endnotes (Experimental)

In order to join paragraphs (and reverse page breaks), detect footnotes and turn them into endnotes.
For now, the footnotes are pulled to the end of a file.

### Deduplication of Pager Header / Footer (Experimental)

If the header or the footer are the same for all pages, only display them once.
Headers are pulled to the start of the document and footer to the end.
Some heuristic based on the similarity of footers are used. (Jaccard distance for text, and compare overlapping shapes)

<!-- TODO -->
<!-- Special case for OCRd PDFs: Choose the Header / Footer with the best Flair score to display.
Since header / footer are small, the OCR may fail to get the text output. -->


## Installation

```bash
pip install pd3f
```

or

```bash
poetry add pd3f
```

You need also a docker container of Parsr running on `localhost:3001` ([script](./scripts/locale_parsr.sh)).

You may also use tunnel a remote Parsr instance ([script](./scripts/locale_parsr.sh)) or choose a remote address.


## Usage

```python
from pd3f import extract

text, tables = extract(file_path, tables=False, experimental=False, force_gpu=False, lang="multi", fast=False, parsr_location="localhost:3001")
```

`file_path`: path a to a PDF. If it's a scanned PDF it needs to get OCR beforehand (outside of this package).

`tables`: extract tables via Parsr (with Camelot / Tabula), results into list of CSV strings

`experimental`: leave out duplicate text in headers / footers and turn footnotes to endnotes. Working unreliable right now.

`force_gpu`: Raise error if CUDA is not available

`lang`: Set the language, `de` for German, `en` for English, `es` for Spanish, `fr` for French. Some fast (less accurate) models exists.
So set `multi-v0-fast` to get fast model for German, French (and some other languages). [Background](https://github.com/jfilter/dehyphen#usage)

`fast`: Drop some Parsr steps to speed up computations

`parsr_location`: Set Parsr location

### GPU Support (CUDA)

Using CUDA speeds up the evaluation with Flair.
But you need an (expensive) GPU.
You need to set up your GPU with CUDA.
[Here a guide for Ubuntu 18.04](https://towardsdatascience.com/deep-learning-gpu-installation-on-ubuntu-18-4-9b12230a1d31)

1. install [conda (via miniconda)](https://docs.conda.io/en/latest/miniconda.html) and [poetry](https://python-poetry.org/docs/)
2. create a new conda enviroment & activate it
3. Install [PyTorch](https://pytorch.org/) with CUDA: `conda install pytorch torchvision cudatoolkit=10.2 -c pytorch` (example)
4. Install `pd3f-core` with poetry: `poetry add pd3f`

Poetry realizes that it is run within a conda virtual env so it doesn't create a new one.
Since setting up CUDA is hard, install it with the most easy way (with conda).


## Background

### Parsr Config

At the heart of `pd3f-core` is the JSON output of Parsr.
Some comments on how and why certain things were chosen.
[Parsr's documentation about the different modules](https://github.com/axa-group/Parsr/tree/master/server/src/processing)

Parsr has several module to classify paragraphs into certain types.
They offer a list detections as well as an heading detection.
In my experience, the accuracy is too low for both, so we don't use it right now.
This also means all the extracted (output) text is flat (no headings, different formattings etc.).

We enable Drawing + Image Detection because we may need to understand what paragraph is following which other one.
This may be helpful when to decide whether to join paragraphs.
But it's dropped when activating the `fast` setting.

In the JSON output is a field `pageNumber`.
This comes from the page detection module.
So `pageNumber` is derived from header / footer of each page.
So it may be different from the index in the page array.
Don't relay on `pageNumber` in the JSON output.

`words-to-line-new` has be used like this.
There is no error but the accuracy decreases if it used otherwise.

```json
"words-to-line-new",
[
    "reading-order-detection",
```

Don't do OCR with Parsr because the results are worse than OCRmyPDF (because the latter uses image preprocessing).

## Future Work / TODO

- make reverse page break work without requiring the experimental features

## Developement

Install and use [poetry](https://python-poetry.org/).

## License

GPLv3