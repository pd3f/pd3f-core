# DDD

Extraact text from PDFs.

It's built upon [parsr]() that's 


## Parsr Config

Why no heading / list detection?

The feature is pretty broken right now. The false positive of these feature will result in broken text. So let's remove it for now and wait until the results improve.

pageNumber: Derived from header / footer of each page

So it may be different from the array of pages


Include Drawing + Image Detection because we may need to understand what paragraph is following which other one. Etc.



# see this for more
# https://github.com/axa-group/Parsr/blob/365ad388fd5dc7ff9c3fa7db28f45460baa899b0/server/src/output/markdown/MarkdownExporter.ts



    "words-to-line-new",
    [
      "reading-order-detection",


### Using with GPU (CUDA)


0. install [conda]() and [poety]()
1. create a new conda enviroment & activate it
1. Install PyTorch with CUDA
2. Install pdddf with poetry

Poetry realizes that it is run within a conda virtual env so it doesn't create a new one.
Since setting up CUDA is hard, use the most easy way (with conda)


## Developement

Use [poetry](https://python-poetry.org/).



## License

GPLv3