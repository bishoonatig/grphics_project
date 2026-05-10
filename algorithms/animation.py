from algorithms.transformations import translate


def animate_translation(pts, steps=20, dx=10, dy=0):
    """
    Returns a list of frames.
    Each frame is a list of Point objects representing
    the translated positions at that step.
    Works for any shape: line, circle center, polygon,
    bezier, bspline.
    """
    frames = []

    for i in range(1, steps + 1):
        new_pts = translate(pts, dx * i, dy * i)
        frames.append(new_pts)

    return frames