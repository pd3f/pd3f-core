"""Compare geometric shapes
"""

from shapely.geometry import MultiPoint, box


def bbox(points):
    assert len(points) >= 4
    h = MultiPoint(points).convex_hull
    return box(*h.bounds)


def sim_bbox(e1, e2):
    b1 = bbox(e1)
    b2 = bbox(e2)
    shared_area = b1.intersection(b2).area
    return shared_area / max(b1.area, b2.area)
