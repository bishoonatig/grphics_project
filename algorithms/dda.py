def draw_dda(screen, x1, y1, x2, y2, color):

    dx = x2 - x1
    dy = y2 - y1

    steps = max(abs(dx), abs(dy))
    if steps == 0:
        screen.set_at((round(x1), round(y1)), color)
        return

    x_increment = dx / steps
    y_increment = dy / steps

    x = x1
    y = y1

    for i in range(steps + 1):

        screen.set_at((round(x), round(y)), color)

        x += x_increment
        y += y_increment
