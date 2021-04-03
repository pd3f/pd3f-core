from pd3f.utils import *


def test_flatten():
    assert list(flatten([["a"], [[["b"]]]])) == ["a", "b"]
    assert list(flatten([["a"], [[["b"]]]], keep_dict=True)) == ["a", "b"]
    assert list(flatten([["a"], [[[{"b": "c"}]]]], keep_dict=True)) == ["a", {"b": "c"}]


def test_update_dict():
    target = {"a": 1, "b": 2}
    source = {"b": 4, "c": 5}

    assert update_dict(target, source) == {"a": 1, "b": 4, "c": 5}

    assert update_dict(target, {"b": [[{"d": 5}]]}) == {"a": 1, "b": [[{"d": 5}]], "c": 5}
