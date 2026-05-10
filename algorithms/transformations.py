import math
from shapes import Point


def centroid(points):
    if not points:
        return Point(0, 0)
    return Point(
        sum(p.x for p in points) / len(points),
        sum(p.y for p in points) / len(points),
    )


def transform_points(points, mapper):
    return [mapper(p) for p in points]


def translate(points, tx, ty):
    return transform_points(points, lambda p: Point(p.x + tx, p.y + ty))


def rotate(points, angle_degrees, origin=None):
    origin = origin or centroid(points)
    radians = math.radians(angle_degrees)
    cos_a = math.cos(radians)
    sin_a = math.sin(radians)

    def mapper(p):
        x = p.x - origin.x
        y = p.y - origin.y
        return Point(
            origin.x + x * cos_a - y * sin_a,
            origin.y + x * sin_a + y * cos_a,
        )

    return transform_points(points, mapper)


def scale(points, sx, sy=None, origin=None):
    sy = sx if sy is None else sy
    origin = origin or centroid(points)

    def mapper(p):
        return Point(
            origin.x + (p.x - origin.x) * sx,
            origin.y + (p.y - origin.y) * sy,
        )

    return transform_points(points, mapper)


def reflect_x(points, axis_y=None):
    axis_y = centroid(points).y if axis_y is None else axis_y
    return transform_points(points, lambda p: Point(p.x, 2 * axis_y - p.y))


def reflect_y(points, axis_x=None):
    axis_x = centroid(points).x if axis_x is None else axis_x
    return transform_points(points, lambda p: Point(2 * axis_x - p.x, p.y))


def shear_x(points, shx, origin=None):
    origin = origin or centroid(points)
    return transform_points(
        points,
        lambda p: Point(origin.x + (p.x - origin.x) + shx * (p.y - origin.y), p.y),
    )


def shear_y(points, shy, origin=None):
    origin = origin or centroid(points)
    return transform_points(
        points,
        lambda p: Point(p.x, origin.y + (p.y - origin.y) + shy * (p.x - origin.x)),
    )
