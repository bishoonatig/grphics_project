def draw_circle_points(screen, xc, yc, x, y, color):

    points = [
        (xc + x, yc + y),
        (xc - x, yc + y),
        (xc + x, yc - y),
        (xc - x, yc - y),
        (xc + y, yc + x),
        (xc - y, yc + x),
        (xc + y, yc - x),
        (xc - y, yc - x)
    ]

    for point in points:

        if 0 <= point[0] < screen.get_width() and 0 <= point[1] < screen.get_height():
            screen.set_at(point, color)


# ---------------- MIDPOINT CIRCLE ----------------

def draw_midpoint_circle(screen, xc, yc, r, color):

    x = 0
    y = r

    p = 1 - r

    draw_circle_points(screen, xc, yc, x, y, color)

    while x < y:

        x += 1

        if p < 0:
            p += 2 * x + 1

        else:
            y -= 1
            p += 2 * (x - y) + 1

        draw_circle_points(screen, xc, yc, x, y, color)


# ---------------- BRESENHAM CIRCLE ----------------

def draw_bresenham_circle(screen, xc, yc, r, color):

    x = 0
    y = r

    d = 3 - 2 * r

    while x <= y:

        draw_circle_points(screen, xc, yc, x, y, color)

        if d < 0:

            d = d + 4 * x + 6

        else:

            d = d + 4 * (x - y) + 10
            y -= 1

        x += 1