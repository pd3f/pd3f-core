# `pdddf` [![PyPI](https://img.shields.io/pypi/v/pdddf.svg)](https://pypi.org/project/pdddf/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pdddf.svg)](https://pypi.org/project/pdddf/) [![PyPI - Downloads](https://img.shields.io/pypi/dm/pdddf)](https://pypistats.org/packages/pdddf)

*Experimental, use with care.*

Reconstruct text from PDFs with Machine Learning.

`pdddf` first uses [parsr](https://github.com/axa-group/Parsr) to chunk PDFs into lines and paragraphs.
Then, it uses [dehyphen](https://github.com/jfilter/dehyphen) (my package) to reconstruct the text in the most probable way.
The probabliby is derived by calculating the [perplexity](https://en.wikipedia.org/wiki/Perplexity#Perplexity_per_word) with [flair](https://github.com/flairNLP/flair)`s character-based language models.

It's mainly developed for German but should work with other languages as well. The project is still in an early stage. Expect rough edges and rapid changes. Documentation will get improved (at some point).

## Installation

```bash
pip install pdddf
```

or

```bash
poetry add pdddf
```

You need also a docker container of parsr running on `localhost:3001` ([script](./scripts/locale_parsr.sh)).

You may also use tunnel a remote parsr instance ([script](./scripts/locale_parsr.sh)) or choose a remote address.


## Usage

```python
from pdddf import extract

text, tables = extract(file_path, tables=False, experimental=False, force_gpu=False, lang="multi", parsr_location="localhost:3001")
```

`tables`: extract tables via parsr (with camelot / tabula), results into list of CSV strings,

`experimental`: leave out duplicate text in headers/footers and pull all footnotes to the end of the document. Working unreliable right now

`force_gpu`: Raise error if CUDA is not available

`lang`: Set the language, `de` for German, `en` for English, `es` for Spanish. Some fast (less accurate) models exists: `multi-v0-fast` [Background](https://github.com/jfilter/dehyphen#usage).

`parsr_location`: Setting a remote parsr location

### GPU Support (CUDA)

You need to set up your GPU with CUDA (lot's of work). [Here a guide for Ubuntu 18.04](https://towardsdatascience.com/deep-learning-gpu-installation-on-ubuntu-18-4-9b12230a1d31)

1. install [conda (via miniconda)](https://docs.conda.io/en/latest/miniconda.html) and [poetry](https://python-poetry.org/docs/)
2. create a new conda enviroment & activate it
3. Install [PyTorch](https://pytorch.org/) with CUDA: `conda install pytorch torchvision cudatoolkit=10.2 -c pytorch` (example)
4. Install pdddf with poetry: `poetry add pdddf`

Poetry realizes that it is run within a conda virtual env so it doesn't create a new one.
Since setting up CUDA is hard, install it with the most easy way (with conda).


## Background

### Parsr Config

At the heart of `pdddf` is the JSON output of parsr.
Some comments on how and why certains things were choosen.
[parsr's documentation about the different modules](https://github.com/axa-group/Parsr/tree/master/server/src/processing)

parsr has several module to classify text in PDFs.
They offer a list detections as well as an heading detection.
In my experience, the accuracy is to low, so we don't use it righw now.
This also means all the text is flat (no headings, different formattings etc.)

Include Drawing + Image Detection because we may need to understand what paragraph is following which other one. Etc.


`pageNumber`: Derived from header / footer of each page.
So it may be different from the array of pages.
Don't relay on `pageNumber` in the JSON output.

If `words-to-line-new` there is no error but the accuracy decreases.

```json
"words-to-line-new",
[
    "reading-order-detection",
```


## Developement

Use [poetry](https://python-poetry.org/).



## License

GPLv3