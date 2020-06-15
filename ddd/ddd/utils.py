import collections.abc
import json


def update_dict(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def write_dict(d, fn):
    if not type(fn) == str:
        fn = str(fn)
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)
