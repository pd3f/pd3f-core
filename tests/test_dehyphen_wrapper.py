from pd3f import dehyphen_wrapper


def test_one_scorer_per_language(monkeypatch):
    monkeypatch.setattr(dehyphen_wrapper, "FlairScorer", lambda **kw: kw)
    dehyphen_wrapper.get_scorer.cache_clear()

    de = dehyphen_wrapper.get_scorer("de")
    assert de == {"lang": "de"}
    assert dehyphen_wrapper.get_scorer("de") is de
    assert dehyphen_wrapper.get_scorer("multi-v0-fast") == {
        "lang": "multi-v0",
        "fast": True,
    }
    dehyphen_wrapper.get_scorer.cache_clear()
