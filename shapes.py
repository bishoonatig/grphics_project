from OpenGL.GL import *

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def draw_shape(shape):

    glBegin(GL_LINE_LOOP)

    for p in shape:
        glVertex2f(p.x, p.y)

    glEnd()


def create_rectangle():

    return [
        Point(100, 100),
        Point(200, 100),
        Point(200, 200),
        Point(100, 200)
    ]


def create_triangle():

    return [
        Point(0, 100),
        Point(-100, -100),
        Point(100, -100)
    ]