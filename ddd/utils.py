"""Utility functions
"""

import json
from collections import Iterable
from collections.abc import Mapping


def update_dict(d, u):
    for k, v in u.items():
        if isinstance(v, Mapping):
            d[k] = update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def write_dict(d, fn):
    if not type(fn) == str:
        fn = str(fn)
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)


def flatten(items, keep_dict=False):
    """Yield items from any nested iterable; see Reference.
    # https://stackoverflow.com/a/40857703/4028896

    keep_dict: do not flatten dicts
    """
    if items is None:
        return
    if keep_dict and isinstance(items, Mapping):
        yield items
    else:
        for x in items:
            if (
                isinstance(x, Iterable)
                and not isinstance(x, (str, bytes))
                and (not keep_dict or not isinstance(x, Mapping))
            ):
                for sub_x in flatten(x, keep_dict):
                    yield sub_x
            else:
                yield x
