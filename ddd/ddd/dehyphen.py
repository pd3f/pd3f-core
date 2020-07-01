import dehyphen as dh
from joblib import Memory

memory = Memory("~/.cache/ddd/dehyphen", verbose=0)

# dehyphenation
@memory.cache
def dehyphen(lines):
    return dh.dehyphen(lines)


@memory.cache
def is_split_paragraph(para1, para2):
    return None
