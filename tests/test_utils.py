from pd3f.utils import *


def test_flatten():
    assert list(flatten([["a"], [[["b"]]]])) == ["a", "b"]
    assert list(flatten([["a"], [[["b"]]]], keep_dict=True)) == ["a", "b"]
    assert list(flatten([["a"], [[[{"b": "c"}]]]], keep_dict=True)) == ["a", {"b": "c"}]
