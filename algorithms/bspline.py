import pygame
from shapes import Point


def b_spline_basis(i, k, t, knots):

    if k == 1:

        if knots[i] <= t < knots[i+1]:
            return 1

        return 0

    left = 0
    right = 0

    d1 = knots[i+k-1] - knots[i]

    if d1 != 0:

        left = (
            (t - knots[i]) / d1
        ) * b_spline_basis(
            i,
            k-1,
            t,
            knots
        )

    d2 = knots[i+k] - knots[i+1]

    if d2 != 0:

        right = (
            (knots[i+k] - t) / d2
        ) * b_spline_basis(
            i+1,
            k-1,
            t,
            knots
        )

    return left + right


def draw_bspline(
    screen,
    points,
    color
):

    n = len(points)
    k = 3

    knots = list(range(n + k))

    prev = None

    t = k - 1

    while t < n:

        x = 0
        y = 0

        for i in range(n):

            b = b_spline_basis(
                i,
                k,
                t,
                knots
            )

            x += points[i].x * b
            y += points[i].y * b

        if prev:

            pygame.draw.line(
                screen,
                color,
                (prev.x, prev.y),
                (x, y),
                2
            )

        prev = Point(x, y)

        t += 0.02