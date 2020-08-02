from functools import lru_cache

from joblib import Memory

from dehyphen import FlairScorer


# cache max 100mb
memory = Memory(
    "~/.cache/ddd/dehyphen", verbose=0, compress=5, bytes_limit=100 * 1000 * 1000
)


scorer = None


def get_scorer(lang):
    global scorer
    if scorer is None:
        scorer = FlairScorer(lang=lang)
    return scorer


# dehyphenation
@memory.cache
def dehyphen_paragraph(lines, lang):
    scorer = get_scorer(lang)
    return scorer.dehyphen_paragraph(lines)


@memory.cache
def is_split_paragraph(p1, p2, lang):
    scorer = get_scorer(lang)
    return scorer.is_split_paragraph(p1, p2)


@memory.cache
def newline_or_not(l1, l2, lang):
    # put in dehyphen?
    # "flair does not work with only one char"
    if len(l1) == 1 and len(l1[0]) == 1:
        return True
    if len(l2) == 1 and len(l2[0]) == 1:
        return False
    scorer = get_scorer(lang)

    texts = [l1, l2, l1 + " " + l2]
    scores = scorer.score(texts)
    best_score_idx = scores.index(min(scores))
    return best_score_idx != 2


@lru_cache
def single_score(text, lang):
    scorer = get_scorer(lang)
    if len(text) == 1:
        return 99999999999
    return scorer.score([text])[0]
