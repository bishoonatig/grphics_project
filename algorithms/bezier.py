import pygame
from shapes import Point


def bezier_point(points, t):

    n = len(points) - 1

    x = 0
    y = 0

    for i, p in enumerate(points):

        coeff = combination(n, i)

        blend = coeff * (
            (1 - t) ** (n - i)
        ) * (
            t ** i
        )

        x += blend * p.x
        y += blend * p.y

    return Point(x, y)


def combination(n, r):

    from math import factorial

    return factorial(n) // (
        factorial(r) *
        factorial(n-r)
    )


def draw_bezier(
    screen,
    control_points,
    color
):

    prev = control_points[0]

    t = 0

    while t <= 1:

        p = bezier_point(
            control_points,
            t
        )

        pygame.draw.line(
            screen,
            color,
            (prev.x, prev.y),
            (p.x, p.y),
            2
        )

        prev = p

        t += 0.01