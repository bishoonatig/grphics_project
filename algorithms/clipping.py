from shapes import Point

# =========================
# COHEN SUTHERLAND
# =========================

INSIDE = 0
LEFT = 1
RIGHT = 2
BOTTOM = 4
TOP = 8


def compute_code(x, y, xmin, ymin, xmax, ymax):

    code = INSIDE

    if x < xmin:
        code |= LEFT

    elif x > xmax:
        code |= RIGHT

    if y < ymin:
        code |= TOP

    elif y > ymax:
        code |= BOTTOM

    return code


def cohen_sutherland_clip(
    x1, y1,
    x2, y2,
    xmin, ymin,
    xmax, ymax
):

    code1 = compute_code(
        x1, y1,
        xmin, ymin,
        xmax, ymax
    )

    code2 = compute_code(
        x2, y2,
        xmin, ymin,
        xmax, ymax
    )

    accept = False

    while True:

        # completely inside
        if code1 == 0 and code2 == 0:
            accept = True
            break

        # completely outside
        elif (code1 & code2) != 0:
            break

        else:

            x = 0
            y = 0

            code_out = code1 if code1 != 0 else code2

            # TOP
            if code_out & TOP:

                x = x1 + (x2 - x1) * (
                    ymin - y1
                ) / (y2 - y1)

                y = ymin

            # BOTTOM
            elif code_out & BOTTOM:

                x = x1 + (x2 - x1) * (
                    ymax - y1
                ) / (y2 - y1)

                y = ymax

            # RIGHT
            elif code_out & RIGHT:

                y = y1 + (y2 - y1) * (
                    xmax - x1
                ) / (x2 - x1)

                x = xmax

            # LEFT
            elif code_out & LEFT:

                y = y1 + (y2 - y1) * (
                    xmin - x1
                ) / (x2 - x1)

                x = xmin

            if code_out == code1:

                x1 = x
                y1 = y

                code1 = compute_code(
                    x1, y1,
                    xmin, ymin,
                    xmax, ymax
                )

            else:

                x2 = x
                y2 = y

                code2 = compute_code(
                    x2, y2,
                    xmin, ymin,
                    xmax, ymax
                )

    if accept:
        return (
            int(x1),
            int(y1),
            int(x2),
            int(y2)
        )

    return None


# =========================
# SUTHERLAND HODGMAN
# =========================

def inside(p, edge, xmin, ymin, xmax, ymax):

    x, y = p.x, p.y

    if edge == "LEFT":
        return x >= xmin

    if edge == "RIGHT":
        return x <= xmax

    if edge == "TOP":
        return y >= ymin

    if edge == "BOTTOM":
        return y <= ymax


def intersection(s, e, edge,
                 xmin, ymin,
                 xmax, ymax):

    x1, y1 = s.x, s.y
    x2, y2 = e.x, e.y

    if x1 == x2:
        m = None
    else:
        m = (y2 - y1) / (x2 - x1)

    if edge == "LEFT":

        x = xmin
        y = y1 + m * (xmin - x1)

    elif edge == "RIGHT":

        x = xmax
        y = y1 + m * (xmax - x1)

    elif edge == "TOP":

        y = ymin

        if m is None:
            x = x1
        else:
            x = x1 + (ymin - y1) / m

    else:

        y = ymax

        if m is None:
            x = x1
        else:
            x = x1 + (ymax - y1) / m

    return Point(x, y)


def clip_polygon(
    polygon,
    xmin, ymin,
    xmax, ymax
):

    edges = [
        "LEFT",
        "RIGHT",
        "TOP",
        "BOTTOM"
    ]

    output = polygon

    for edge in edges:

        input_list = output
        output = []

        if not input_list:
            break

        s = input_list[-1]

        for e in input_list:

            if inside(
                e, edge,
                xmin, ymin,
                xmax, ymax
            ):

                if not inside(
                    s, edge,
                    xmin, ymin,
                    xmax, ymax
                ):

                    output.append(
                        intersection(
                            s, e,
                            edge,
                            xmin, ymin,
                            xmax, ymax
                        )
                    )

                output.append(e)

            elif inside(
                s, edge,
                xmin, ymin,
                xmax, ymax
            ):

                output.append(
                    intersection(
                        s, e,
                        edge,
                        xmin, ymin,
                        xmax, ymax
                    )
                )

            s = e

    return output