import json
from shapes import Point


def save_shapes(shapes):

    data = []

    for shape in shapes:

        # make a shallow copy so we don't mutate the live shape dict
        entry = dict(shape)

        if "points" in entry:
            pts = []
            for p in entry["points"]:
                # support both Point objects and plain tuples
                if hasattr(p, "x"):
                    pts.append([p.x, p.y])
                else:
                    pts.append(list(p))
            entry["points"] = pts

        data.append(entry)

    # "w" overwrites each time so the file stays valid JSON
    with open("drawing.json", "w") as f:
        json.dump(data, f, indent=2)


def load_shapes():

    try:
        with open("drawing.json", "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    shapes = []

    for entry in data:

        shape = dict(entry)

        # convert raw [x, y] pairs back to Point objects
        if "points" in shape:
            shape["points"] = [Point(p[0], p[1]) for p in shape["points"]]

        shapes.append(shape)

    return shapes