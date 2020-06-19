import json

from collections import abc, Iterable


def update_dict(d, u):
    for k, v in u.items():
        if isinstance(v, abc.Mapping):
            d[k] = update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def write_dict(d, fn):
    if not type(fn) == str:
        fn = str(fn)
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)


# https://stackoverflow.com/a/40857703/4028896
def flatten(items):
    """Yield items from any nested iterable; see Reference."""
    if items is None:
        return
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatten(x):
                yield sub_x
        else:
            yield x
