import dehyphen as dh
from joblib import Memory

memory = Memory("~/.cache/ddd/dehyphen", verbose=0)

# dehyphenation
@memory.cache
def dehyphen(lines):
    return dh.dehyphen_paragraph(lines)


@memory.cache
def is_split_paragraph(*args):
    return dh.join_paragraphs_if_cool(*args)
