"""Interaction with `dehyphen`, cache results"""

from functools import lru_cache
from importlib.metadata import version

from dehyphen import FlairScorer
from joblib import Memory

# one cache per dehyphen version, its results change between versions
memory = Memory(f"~/.cache/pd3f/dehyphen-{version('dehyphen')}", verbose=0, compress=5)
# cache max 100mb, keeps the most recently used results
memory.reduce_size(bytes_limit=100 * 1000 * 1000)


@lru_cache
def get_scorer(lang):
    """Load each language model only once per process."""
    # simplify Flair's naming of models
    if lang.endswith("-fast"):
        return FlairScorer(lang=lang[:-5], fast=True)
    return FlairScorer(lang=lang)


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
    """Decide whether to add a newline or not."""
    # Flair does not work with only one char, thus this special case
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
    # Flair does not work with only one char, thus this special case
    if len(text) == 1:
        return float("inf")
    return scorer.score([text])[0]
