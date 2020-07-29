from dehyphen import FlairScorer
from joblib import Memory

memory = Memory("~/.cache/ddd/dehyphen", verbose=0)

scorer = FlairScorer(lang="de")

# dehyphenation
@memory.cache
def dehyphen_paragraph(lines):
    return scorer.dehyphen_paragraph(lines)


@memory.cache
def is_split_paragraph(*args):
    return scorer.is_split_paragraph(*args)


@memory.cache
def newline_or_not(l1, l2):
    # put in dehyphen?
    # "flair does not work with only one char"
    if len(l1) == 1 and len(l1[0]) == 1:
        return True
    if len(l2) == 1 and len(l2[0]) == 1:
        return False

    texts = [l1, l2, l1 + " " + l2]
    scores = scorer.score(texts)
    best_score_idx = scores.index(min(scores))
    return best_score_idx != 2
