import dehyphen as dh
import dehyphen.score_flair as dhsf
from joblib import Memory

memory = Memory("~/.cache/ddd/dehyphen", verbose=0)

# dehyphenation
@memory.cache
def dehyphen(lines):
    return dh.dehyphen_paragraph(lines)


@memory.cache
def is_split_paragraph(*args):
    return dh.join_paragraphs_if_cool(*args)


# put in dehyphen
def newline_or_not(l1, l2):
    texts = [l1, l2, l1 + " " + l2]
    scores = dhsf.score(texts)
    best_score_idx = scores.index(min(scores))
    return best_score_idx != 2
