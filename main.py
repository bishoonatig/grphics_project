import json
import math
import os
import sys
from io import BytesIO
from dataclasses import dataclass

import pygame

from shapes import Point
from algorithms.animation import animate_translation
from algorithms.bezier import draw_bezier
from algorithms.bresenham import draw_bresenham
from algorithms.bspline import draw_bspline
from algorithms.circle import draw_bresenham_circle, draw_midpoint_circle
from algorithms.clipping import clip_polygon, cohen_sutherland_clip
from algorithms.dda import draw_dda
from algorithms.performance import compare
from algorithms.save_load import load_shapes, save_shapes
from algorithms.transformations import (
    reflect_x,
    reflect_y,
    rotate,
    scale,
    shear_x,
    shear_y,
    translate,
)


pygame.init()

WIDTH, HEIGHT = 1366, 768
FPS = 60
SIDEBAR_W = 272
INSPECTOR_W = 292
GAP = 18

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("VectorLab Studio")
clock = pygame.time.Clock()

class MathSurfaceRenderer:
    def __init__(self):
        self.available = None
        self._figure_class = None
        self._canvas_class = None
        self._cache = {}

    def ensure_backend(self):
        if self.available is not None:
            return self.available
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg
        except ImportError:
            self.available = False
            return False
        self._figure_class = Figure
        self._canvas_class = FigureCanvasAgg
        self.available = True
        return True

    def render_block(self, formulas, max_width, max_height, color):
        formulas = [formula for formula in formulas if formula]
        if not formulas:
            return None
        cache_key = (tuple(formulas), max_width, max_height, color)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        if not self.ensure_backend():
            panel = self.render_fallback(formulas, max_width, max_height, color)
            self._cache[cache_key] = panel
            return panel

        font_size = self.pick_font_size(formulas, max_width, max_height)
        surfaces = []
        total_height = 0
        max_surface_width = 0
        for formula in formulas:
            surface = self.render_formula(formula, font_size, color)
            if surface is None:
                continue
            surfaces.append(surface)
            total_height += surface.get_height()
            max_surface_width = max(max_surface_width, surface.get_width())

        if not surfaces:
            panel = self.render_fallback(formulas, max_width, max_height, color)
            self._cache[cache_key] = panel
            return panel

        spacing = 8
        total_height += spacing * (len(surfaces) - 1)
        panel = pygame.Surface((max_surface_width, total_height), pygame.SRCALPHA)
        y = 0
        for surface in surfaces:
            panel.blit(surface, (0, y))
            y += surface.get_height() + spacing

        if panel.get_width() > max_width or panel.get_height() > max_height:
            scale = min(max_width / max(1, panel.get_width()), max_height / max(1, panel.get_height()))
            scaled_size = (
                max(1, int(panel.get_width() * scale)),
                max(1, int(panel.get_height() * scale)),
            )
            panel = pygame.transform.smoothscale(panel, scaled_size)
        self._cache[cache_key] = panel
        return panel

    def pick_font_size(self, formulas, max_width, max_height):
        for font_size in range(28, 11, -2):
            widths = []
            heights = []
            for formula in formulas:
                size = self.measure_formula(formula, font_size)
                if size is None:
                    return 20
                widths.append(size[0])
                heights.append(size[1])
            total_height = sum(heights) + 8 * (len(heights) - 1)
            if max(widths) <= max_width and total_height <= max_height:
                return font_size
        return 12

    def measure_formula(self, formula, font_size):
        try:
            figure = self._figure_class(figsize=(1, 1), dpi=200)
            canvas = self._canvas_class(figure)
            text = figure.text(0, 0, formula, fontsize=font_size)
            canvas.draw()
            bbox = text.get_window_extent(canvas.get_renderer())
            return math.ceil(bbox.width), math.ceil(bbox.height)
        except Exception:
            return None

    def render_formula(self, formula, font_size, color):
        try:
            width, height = self.measure_formula(formula, font_size)
            if width is None or height is None:
                return None
            figure = self._figure_class(figsize=(width / 200, height / 200), dpi=200)
            figure.patch.set_alpha(0)
            canvas = self._canvas_class(figure)
            rgb = tuple(channel / 255 for channel in color)
            figure.text(0, 0, formula, fontsize=font_size, color=rgb)
            image = BytesIO()
            canvas.print_png(image)
            image.seek(0)
            return pygame.image.load(image, "math.png").convert_alpha()
        except Exception:
            return None

    def render_fallback(self, formulas, max_width, max_height, color):
        lines = [clipped_text(formula.strip("$"), FONT_SM, max_width) for formula in formulas]
        rendered = [FONT_SM.render(line, True, color) for line in lines]
        total_height = sum(surface.get_height() for surface in rendered) + 6 * max(0, len(rendered) - 1)
        panel = pygame.Surface((max(surface.get_width() for surface in rendered), total_height), pygame.SRCALPHA)
        y = 0
        for surface in rendered:
            panel.blit(surface, (0, y))
            y += surface.get_height() + 6
        if panel.get_width() > max_width or panel.get_height() > max_height:
            scale = min(max_width / max(1, panel.get_width()), max_height / max(1, panel.get_height()))
            panel = pygame.transform.smoothscale(
                panel,
                (max(1, int(panel.get_width() * scale)), max(1, int(panel.get_height() * scale))),
            )
        return panel


class Color:
    APP = (9, 13, 22)
    PANEL = (17, 24, 39)
    PANEL_ALT = (24, 34, 53)
    FIELD = (12, 18, 30)
    BORDER = (48, 61, 82)
    GRID = (30, 41, 59)
    TEXT = (226, 232, 240)
    MUTED = (148, 163, 184)
    FADED = (100, 116, 139)
    INK = (241, 245, 249)
    BLUE = (96, 165, 250)
    CYAN = (34, 211, 238)
    GREEN = (74, 222, 128)
    RED = (251, 113, 133)
    ORANGE = (251, 191, 36)
    VIOLET = (167, 139, 250)
    SELECT = (56, 189, 248)
    SELECT_SOFT = (8, 47, 73)

    @classmethod
    def apply(cls, theme):
        for name, value in theme.items():
            setattr(cls, name, value)


DARK_THEME = {
    "APP": (9, 13, 22),
    "PANEL": (17, 24, 39),
    "PANEL_ALT": (24, 34, 53),
    "FIELD": (12, 18, 30),
    "BORDER": (48, 61, 82),
    "GRID": (30, 41, 59),
    "TEXT": (226, 232, 240),
    "MUTED": (148, 163, 184),
    "FADED": (100, 116, 139),
    "INK": (241, 245, 249),
    "BLUE": (96, 165, 250),
    "CYAN": (34, 211, 238),
    "GREEN": (74, 222, 128),
    "RED": (251, 113, 133),
    "ORANGE": (251, 191, 36),
    "VIOLET": (167, 139, 250),
    "SELECT": (56, 189, 248),
    "SELECT_SOFT": (8, 47, 73),
}

LIGHT_THEME = {
    "APP": (243, 246, 250),
    "PANEL": (255, 255, 255),
    "PANEL_ALT": (248, 250, 252),
    "FIELD": (241, 245, 249),
    "BORDER": (214, 222, 232),
    "GRID": (234, 240, 247),
    "TEXT": (22, 32, 48),
    "MUTED": (91, 105, 125),
    "FADED": (148, 163, 184),
    "INK": (15, 23, 42),
    "BLUE": (37, 99, 235),
    "CYAN": (8, 145, 178),
    "GREEN": (22, 163, 74),
    "RED": (225, 29, 72),
    "ORANGE": (217, 119, 6),
    "VIOLET": (124, 58, 237),
    "SELECT": (14, 165, 233),
    "SELECT_SOFT": (224, 242, 254),
}


FONT_XS = pygame.font.SysFont("Segoe UI", 13)
FONT_SM = pygame.font.SysFont("Segoe UI", 15)
FONT_MD = pygame.font.SysFont("Segoe UI", 17)
FONT_LG = pygame.font.SysFont("Segoe UI Semibold", 22)
FONT_TITLE = pygame.font.SysFont("Segoe UI Semibold", 29)
FONT_MONO = pygame.font.SysFont("Consolas", 15)
FONT_FORMULA_TITLE = pygame.font.SysFont("Cambria Math", 15, bold=True)

LEFT_PANEL = pygame.Rect(GAP, GAP, SIDEBAR_W, HEIGHT - 2 * GAP)
RIGHT_PANEL = pygame.Rect(WIDTH - INSPECTOR_W - GAP, GAP, INSPECTOR_W, HEIGHT - 2 * GAP)
TOP_BAR = pygame.Rect(LEFT_PANEL.right + GAP, GAP, RIGHT_PANEL.left - LEFT_PANEL.right - 2 * GAP, 74)
CANVAS = pygame.Rect(LEFT_PANEL.right + GAP, TOP_BAR.bottom + GAP, TOP_BAR.w, HEIGHT - TOP_BAR.bottom - 2 * GAP)
CLIP_RECT = pygame.Rect(CANVAS.x + 160, CANVAS.y + 96, CANVAS.w - 320, CANVAS.h - 192)
MATH_RENDERER = MathSurfaceRenderer()


DRAW_TOOLS = [
    ("DDA", "DDA Line", "/", "1", pygame.K_1, "BLUE", 2),
    ("Bresenham", "Bresenham Line", "BR", "2", pygame.K_2, "RED", 2),
    ("Midpoint Circle", "Midpoint Circle", "O", "3", pygame.K_3, "CYAN", 2),
    ("Bresenham Circle", "Bresenham Circle", "BC", "4", pygame.K_4, "INK", 2),
    ("Polygon", "Polygon", "[]", "P", pygame.K_p, "VIOLET", 4),
    ("Bezier", "Bezier Curve", "~", "7", pygame.K_7, "GREEN", 4),
    ("B-Spline", "B-Spline", "SP", "8", pygame.K_8, "INK", 4),
    ("Clip Line", "Clip Line", "<>", "5", pygame.K_5, "ORANGE", 2),
    ("Clip Polygon", "Clip Polygon", "CP", "6", pygame.K_6, "ORANGE", 4),
]

DRAW_TOOL_BY_MODE = {tool[0]: tool for tool in DRAW_TOOLS}


def tool_color(tool):
    return getattr(Color, tool[5])


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    key: str
    action: str
    value: object = None
    active: bool = False
    disabled: bool = False

    def draw(self, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos) and not self.disabled
        fill = Color.PANEL
        border = Color.BORDER
        text = Color.TEXT
        if self.disabled:
            fill = Color.FIELD
            text = Color.FADED
        elif self.active:
            fill = Color.SELECT_SOFT
            border = Color.SELECT
            text = Color.TEXT
        elif hovered:
            fill = Color.PANEL_ALT
            border = (71, 85, 105)

        pygame.draw.rect(screen, fill, self.rect, border_radius=8)
        pygame.draw.rect(screen, border, self.rect, 1, border_radius=8)

        chip = pygame.Rect(self.rect.x + 10, self.rect.centery - 12, 30, 24)
        chip_fill = Color.SELECT if self.active else Color.FIELD
        pygame.draw.rect(screen, chip_fill, chip, border_radius=6)
        pygame.draw.rect(screen, Color.BORDER, chip, 1, border_radius=6)
        icon_color = Color.APP if self.active else Color.TEXT
        icon_surf = FONT_XS.render(self.key, True, icon_color)
        screen.blit(icon_surf, icon_surf.get_rect(center=chip.center))

        label_font = FONT_SM if FONT_SM.size(self.label)[0] <= self.rect.w - 56 else FONT_XS
        label_surf = label_font.render(self.label, True, text)
        screen.blit(label_surf, label_surf.get_rect(midleft=(self.rect.x + 50, self.rect.centery)))


@dataclass
class AlgorithmPreview:
    shape: dict
    title: str
    equations: list
    render_method: str
    headers: list
    rows: list
    pixels: list
    color_name: str
    started_at: int = 0
    scroll: int = 0
    h_scroll: int = 0
    follow_latest: bool = True
    equation_surface: object = None
    equation_size: tuple = (0, 0)
    equation_color: tuple = None



def draw_text(text, pos, font=FONT_SM, color=Color.TEXT):
    surf = font.render(text, True, color)
    screen.blit(surf, pos)
    return surf.get_rect(topleft=pos)


def draw_panel(rect):
    pygame.draw.rect(screen, Color.PANEL, rect, border_radius=10)
    pygame.draw.rect(screen, Color.BORDER, rect, 1, border_radius=10)


def clipped_text(text, font, max_width):
    text = str(text)
    if font.size(text)[0] <= max_width:
        return text
    suffix = "..."
    available = max_width - font.size(suffix)[0]
    clipped = ""
    for char in text:
        if font.size(clipped + char)[0] > available:
            break
        clipped += char
    return clipped + suffix


def wrap_text_lines(text, font, max_width, max_lines=3):
    words = str(text).split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
            if len(lines) == max_lines - 1:
                break
    if len(lines) < max_lines:
        remaining = current if len(lines) < max_lines - 1 else clipped_text(current, font, max_width)
        lines.append(remaining)
    return lines[:max_lines]


def ordered_unique(points):
    seen = set()
    result = []
    for point in points:
        key = (int(round(point[0])), int(round(point[1])))
        if key not in seen:
            seen.add(key)
            result.append(key)
    return result


def trace_dda_pixels(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    steps = int(max(abs(dx), abs(dy)))
    if steps == 0:
        pixel = (round(x1), round(y1))
        return [["0", f"{x1:.2f}", f"{y1:.2f}", pixel]], [pixel]

    x_inc = dx / steps
    y_inc = dy / steps
    x = x1
    y = y1
    rows = []
    pixels = []
    for step in range(steps + 1):
        pixel = (round(x), round(y))
        rows.append([step, f"{x:.2f}", f"{y:.2f}", pixel])
        pixels.append(pixel)
        x += x_inc
        y += y_inc
    return rows, ordered_unique(pixels)


def trace_bresenham_pixels(x1, y1, x2, y2):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    rows = []
    pixels = []
    step = 0
    while True:
        pixels.append((x1, y1))
        rows.append([step, x1, y1, err, 2 * err])
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy
        step += 1
    return rows, pixels


def circle_octant_pixels(xc, yc, x, y):
    return [
        (xc + x, yc + y),
        (xc - x, yc + y),
        (xc + x, yc - y),
        (xc - x, yc - y),
        (xc + y, yc + x),
        (xc - y, yc + x),
        (xc + y, yc - x),
        (xc - y, yc - x),
    ]


def trace_midpoint_circle_pixels(xc, yc, r):
    x = 0
    y = r
    p = 1 - r
    rows = []
    pixels = []
    step = 0
    while x <= y:
        octants = circle_octant_pixels(xc, yc, x, y)
        rows.append([step, x, y, p, str(octants)])
        pixels.extend(octants)
        x += 1
        if p < 0:
            p += 2 * x + 1
        else:
            y -= 1
            p += 2 * (x - y) + 1
        step += 1
    return rows, ordered_unique(pixels)


def trace_bresenham_circle_pixels(xc, yc, r):
    x = 0
    y = r
    d = 3 - 2 * r
    rows = []
    pixels = []
    step = 0
    while x <= y:
        octants = circle_octant_pixels(xc, yc, x, y)
        rows.append([step, x, y, d, str(octants)])
        pixels.extend(octants)
        if d < 0:
            d += 4 * x + 6
        else:
            d += 4 * (x - y) + 10
            y -= 1
        x += 1
        step += 1
    return rows, ordered_unique(pixels)


def polyline_pixels(points, closed=False):
    if len(points) < 2:
        return []
    pixels = []
    pairs = list(zip(points, points[1:]))
    if closed:
        pairs.append((points[-1], points[0]))
    for start, end in pairs:
        _, segment = trace_dda_pixels(start.x, start.y, end.x, end.y)
        pixels.extend(segment)
    return ordered_unique(pixels)


def trace_bezier_shape(points):
    rows = []
    curve_points = []
    step = 0
    t = 0
    while t <= 1.0001:
        p = draw_bezier_point(points, t)
        rows.append([step, f"{t:.2f}", f"{p.x:.2f}", f"{p.y:.2f}", (round(p.x), round(p.y))])
        curve_points.append(p)
        t += 0.02
        step += 1
    return rows, polyline_pixels(curve_points)


def draw_bezier_point(points, t):
    n = len(points) - 1
    x = 0
    y = 0
    for i, p in enumerate(points):
        coeff = math.factorial(n) // (math.factorial(i) * math.factorial(n - i))
        blend = coeff * ((1 - t) ** (n - i)) * (t ** i)
        x += blend * p.x
        y += blend * p.y
    return Point(x, y)


def trace_bspline_shape(points):
    n = len(points)
    k = 3
    knots = list(range(n + k))
    rows = []
    curve_points = []
    step = 0
    t = k - 1
    while t < n:
        x = 0
        y = 0
        for i in range(n):
            b = bspline_basis_value(i, k, t, knots)
            x += points[i].x * b
            y += points[i].y * b
        rows.append([step, f"{t:.2f}", f"{x:.2f}", f"{y:.2f}", (round(x), round(y))])
        curve_points.append(Point(x, y))
        t += 0.04
        step += 1
    return rows, polyline_pixels(curve_points)


def bspline_basis_value(i, k, t, knots):
    if k == 1:
        return 1 if knots[i] <= t < knots[i + 1] else 0
    left = 0
    right = 0
    d1 = knots[i + k - 1] - knots[i]
    if d1 != 0:
        left = ((t - knots[i]) / d1) * bspline_basis_value(i, k - 1, t, knots)
    d2 = knots[i + k] - knots[i + 1]
    if d2 != 0:
        right = ((knots[i + k] - t) / d2) * bspline_basis_value(i + 1, k - 1, t, knots)
    return left + right


def build_algorithm_preview(mode, shape, original_points=None):
    color_name = DRAW_TOOL_BY_MODE[mode][5]
    if mode == "DDA":
        rows, pixels = trace_dda_pixels(shape["x1"], shape["y1"], shape["x2"], shape["y2"])
        return AlgorithmPreview(
            shape,
            "DDA Line Algorithm",
            [
                r"$\mathrm{Digital\ Differential\ Analyzer\ Line}$",
                r"$x_k = x_1 + k \left(\frac{\Delta x}{N}\right)$",
                r"$y_k = y_1 + k \left(\frac{\Delta y}{N}\right), \quad N = \max \left(|\Delta x|, |\Delta y|\right)$",
            ],
            "Used Digital Differential Analyzer algorithm to draw the line.",
            ["k", "x", "y", "pixel"],
            rows,
            pixels,
            color_name,
        )
    if mode == "Bresenham":
        rows, pixels = trace_bresenham_pixels(shape["x1"], shape["y1"], shape["x2"], shape["y2"])
        return AlgorithmPreview(
            shape,
            "Bresenham Line Algorithm",
            [
                r"$\mathrm{Bresenham\ Line\ Decision\ Parameter}$",
                r"$p_0 = 2\Delta y - \Delta x$",
                r"$p_{k+1} = p_k + 2\Delta y \quad \mathrm{or} \quad p_k + 2\Delta y - 2\Delta x$",
            ],
            "Used Bresenham line algorithm to draw the line.",
            ["k", "x", "y", "err", "2err"],
            rows,
            pixels,
            color_name,
        )
    if mode == "Midpoint Circle":
        rows, pixels = trace_midpoint_circle_pixels(shape["xc"], shape["yc"], shape["r"])
        return AlgorithmPreview(
            shape,
            "Midpoint Circle Algorithm",
            [
                r"$\mathrm{Midpoint\ Circle\ Equation:}\ x^2 + y^2 = r^2$",
                r"$F(x,y) = x^2 + y^2 - r^2$",
                r"$p_0 = 1 - r,\quad p_k = F(x_k + 1,\ y_k - \frac{1}{2})$",
            ],
            "Used Midpoint Circle algorithm to draw the circle.",
            ["k", "x", "y", "p", "8 symmetric pixels"],
            rows,
            pixels,
            color_name,
        )
    if mode == "Bresenham Circle":
        rows, pixels = trace_bresenham_circle_pixels(shape["xc"], shape["yc"], shape["r"])
        return AlgorithmPreview(
            shape,
            "Bresenham Circle Algorithm",
            [
                r"$\mathrm{Bresenham\ Circle\ Equation:}\ x^2 + y^2 = r^2$",
                r"$d_0 = 3 - 2r$",
                r"$d_{k+1} = d_k + 4x_k + 6 \quad \mathrm{or} \quad d_k + 4(x_k - y_k) + 10$",
            ],
            "Used Bresenham circle algorithm to draw the circle.",
            ["k", "x", "y", "d", "8 symmetric pixels"],
            rows,
            pixels,
            color_name,
        )
    if mode == "Bezier":
        rows, pixels = trace_bezier_shape(shape["points"])
        return AlgorithmPreview(
            shape,
            "Bezier Curve Algorithm",
            [
                r"$\mathrm{B\acute{e}zier\ Curve}$",
                r"$B(t)=\sum_{i=0}^{n} B_{i,n}(t)P_i$",
                r"$B_{i,n}(t)=\binom{n}{i}(1-t)^{n-i}t^i$",
            ],
            "Used Digital Differential Analyzer algorithm between successive Bezier sample points.",
            ["k", "t", "x", "y", "pixel"],
            rows,
            pixels,
            color_name,
        )
    if mode == "B-Spline":
        rows, pixels = trace_bspline_shape(shape["points"])
        return AlgorithmPreview(
            shape,
            "B-Spline Algorithm",
            [
                r"$\mathrm{B\!-\!Spline\ Curve}$",
                r"$P(t)=\sum_{i=0}^{n}N_{i,k}(t)P_i$",
                r"$N_{i,k}(t)=\frac{t-t_i}{t_{i+k-1}-t_i}N_{i,k-1}(t)+\frac{t_{i+k}-t}{t_{i+k}-t_{i+1}}N_{i+1,k-1}(t)$",
            ],
            "Used Digital Differential Analyzer algorithm between successive B-spline sample points.",
            ["k", "t", "x", "y", "pixel"],
            rows,
            pixels,
            color_name,
        )
    if mode == "Clip Line":
        rows = [["input", original_points[0], original_points[1], "clip window"], ["output", (shape["x1"], shape["y1"]), (shape["x2"], shape["y2"]), "accepted"]]
        _, pixels = trace_dda_pixels(shape["x1"], shape["y1"], shape["x2"], shape["y2"])
        return AlgorithmPreview(
            shape,
            "Cohen-Sutherland Line Clipping",
            [
                r"$\mathrm{Cohen\!-\!Sutherland\ Intersection}$",
                r"$x=x_1+(x_2-x_1)\left(\frac{y_{\mathrm{boundary}}-y_1}{y_2-y_1}\right)$",
                r"$y=y_1+(y_2-y_1)\left(\frac{x_{\mathrm{boundary}}-x_1}{x_2-x_1}\right)$",
            ],
            "Used Cohen-Sutherland clipping, then used Digital Differential Analyzer algorithm to draw the clipped line.",
            ["step", "p1", "p2", "result"],
            rows,
            pixels,
            color_name,
        )
    if mode == "Clip Polygon":
        rows = [[index, f"{point.x:.0f}", f"{point.y:.0f}", "inside"] for index, point in enumerate(shape["points"])]
        return AlgorithmPreview(
            shape,
            "Sutherland-Hodgman Polygon Clipping",
            [
                r"$\mathrm{Sutherland\!-\!Hodgman\ Intersection}$",
                r"$x=x_1+(x_2-x_1)\left(\frac{y_{\mathrm{boundary}}-y_1}{y_2-y_1}\right)$",
                r"$y=y_1+(y_2-y_1)\left(\frac{x_{\mathrm{boundary}}-x_1}{x_2-x_1}\right)$",
            ],
            "Used Sutherland-Hodgman clipping, then used Digital Differential Analyzer algorithm for polygon edges.",
            ["vertex", "x", "y", "status"],
            rows,
            polyline_pixels(shape["points"], closed=True),
            color_name,
        )
    rows = [[index, f"{point.x:.0f}", f"{point.y:.0f}", "connect"] for index, point in enumerate(shape["points"])]
    return AlgorithmPreview(
        shape,
        "Polygon Edge Drawing",
        [
            r"$\mathrm{Polygon\ Edge\ Parametric\ Form}$",
            r"$P(t)=P_i+t(P_{i+1}-P_i)$",
            r"$0 \leq t \leq 1$",
        ],
        "Used Digital Differential Analyzer algorithm for the polygon edges.",
        ["vertex", "x", "y", "action"],
        rows,
        polyline_pixels(shape["points"], closed=True),
        color_name,
    )


class ShapeAPI:
    @staticmethod
    def points(shape):
        if shape["type"] in ("dda", "bresenham"):
            return [Point(shape["x1"], shape["y1"]), Point(shape["x2"], shape["y2"])]
        if shape["type"] in ("polygon", "bezier", "bspline"):
            return shape["points"]
        if "circle" in shape["type"]:
            return [Point(shape["xc"], shape["yc"])]
        return []

    @staticmethod
    def rebuild(shape, points):
        if shape["type"] in ("dda", "bresenham"):
            return {**shape, "x1": points[0].x, "y1": points[0].y, "x2": points[1].x, "y2": points[1].y}
        if shape["type"] in ("polygon", "bezier", "bspline"):
            return {**shape, "points": points}
        if "circle" in shape["type"]:
            return {**shape, "xc": points[0].x, "yc": points[0].y}
        return shape

    @staticmethod
    def clamp(points):
        clamped = []
        for point in points:
            clamped.append(
                Point(
                    max(CANVAS.left + 2, min(CANVAS.right - 2, point.x)),
                    max(CANVAS.top + 2, min(CANVAS.bottom - 2, point.y)),
                )
            )
        return clamped

    @staticmethod
    def bounds(shape):
        if "circle" in shape["type"]:
            r = shape["r"]
            return pygame.Rect(shape["xc"] - r, shape["yc"] - r, 2 * r, 2 * r)
        pts = ShapeAPI.points(shape)
        if not pts:
            return pygame.Rect(0, 0, 0, 0)
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        return pygame.Rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    @staticmethod
    def hit_score(shape, pos):
        x, y = pos
        if "circle" in shape["type"]:
            dist = abs(math.hypot(x - shape["xc"], y - shape["yc"]) - shape["r"])
            return dist if dist <= 12 else None
        pts = ShapeAPI.points(shape)
        best = None
        for point in pts:
            dist = math.hypot(x - point.x, y - point.y)
            best = dist if best is None else min(best, dist)
        rect = ShapeAPI.bounds(shape).inflate(18, 18)
        if rect.collidepoint(pos):
            return best or 0
        return best if best is not None and best <= 14 else None


class DrawingAPI:
    def __init__(self, app):
        self.app = app

    def finish_if_ready(self):
        mode = self.app.mode
        points = self.app.pending_points

        if mode in ("DDA", "Bresenham") and len(points) == 2:
            x1, y1 = points[0]
            x2, y2 = points[1]
            self.preview({"type": "dda" if mode == "DDA" else "bresenham", "x1": x1, "y1": y1, "x2": x2, "y2": y2})
        elif "Circle" in mode and len(points) == 2:
            xc, yc = points[0]
            x2, y2 = points[1]
            radius = int(math.hypot(x2 - xc, y2 - yc))
            self.preview({"type": "midpoint_circle" if mode == "Midpoint Circle" else "bresenham_circle", "xc": xc, "yc": yc, "r": radius})
        elif mode == "Polygon" and len(points) == 4:
            self.preview({"type": "polygon", "points": [Point(x, y) for x, y in points]})
        elif mode == "Bezier" and len(points) == 4:
            self.preview({"type": "bezier", "points": [Point(x, y) for x, y in points]})
        elif mode == "B-Spline" and len(points) == 4:
            self.preview({"type": "bspline", "points": [Point(x, y) for x, y in points]})
        elif mode == "Clip Line" and len(points) == 2:
            x1, y1 = points[0]
            x2, y2 = points[1]
            result = cohen_sutherland_clip(x1, y1, x2, y2, CLIP_RECT.left, CLIP_RECT.top, CLIP_RECT.right, CLIP_RECT.bottom)
            if result:
                x1, y1, x2, y2 = result
                self.preview({"type": "dda", "x1": x1, "y1": y1, "x2": x2, "y2": y2}, "Clipped line added")
            else:
                self.app.pending_points.clear()
                self.app.toast("Line rejected by clipping window")
        elif mode == "Clip Polygon" and len(points) == 4:
            poly = [Point(x, y) for x, y in points]
            clipped = clip_polygon(poly, CLIP_RECT.left, CLIP_RECT.top, CLIP_RECT.right, CLIP_RECT.bottom)
            self.preview({"type": "polygon", "points": clipped}, "Clipped polygon added")

    def preview(self, shape, message=None):
        self.app.preview_message = message
        self.app.algorithm_preview = build_algorithm_preview(self.app.mode, shape, list(self.app.pending_points))
        self.app.algorithm_preview.started_at = pygame.time.get_ticks()
        self.app.pending_points.clear()
        self.app.toast("Review algorithm steps")

    def add(self, shape, message=None):
        self.app.shapes.append(shape)
        self.app.selected_index = len(self.app.shapes) - 1
        self.app.pending_points.clear()
        self.app.toast(message or "Shape added")


class TransformAPI:
    def __init__(self, app):
        self.app = app

    def apply(self, name):
        selected = self.app.selected_shape()
        if selected is None:
            self.app.toast("Select a shape first")
            return

        if "circle" in selected["type"] and name in ("scale_down", "scale_up"):
            factor = 0.9 if name == "scale_down" else 1.1
            max_radius = int(
                min(
                    selected["xc"] - CANVAS.left - 2,
                    CANVAS.right - selected["xc"] - 2,
                    selected["yc"] - CANVAS.top - 2,
                    CANVAS.bottom - selected["yc"] - 2,
                )
            )
            selected["r"] = max(4, min(max_radius, int(selected["r"] * factor)))
            self.app.toast(f"Circle radius: {selected['r']}")
            return

        points = ShapeAPI.points(selected)
        if name == "left":
            new_points = translate(points, -18, 0)
        elif name == "right":
            new_points = translate(points, 18, 0)
        elif name == "up":
            new_points = translate(points, 0, -18)
        elif name == "down":
            new_points = translate(points, 0, 18)
        elif name == "rotate_ccw":
            new_points = rotate(points, -15)
        elif name == "rotate_cw":
            new_points = rotate(points, 15)
        elif name == "scale_down":
            new_points = scale(points, 0.9)
        elif name == "scale_up":
            new_points = scale(points, 1.1)
        elif name == "reflect_x":
            new_points = reflect_x(points)
        elif name == "reflect_y":
            new_points = reflect_y(points)
        elif name == "shear_left":
            new_points = shear_x(points, -0.18)
        elif name == "shear_right":
            new_points = shear_x(points, 0.18)
        elif name == "shear_up":
            new_points = shear_y(points, -0.18)
        elif name == "shear_down":
            new_points = shear_y(points, 0.18)
        else:
            return

        self.app.shapes[self.app.selected_index] = ShapeAPI.rebuild(selected, ShapeAPI.clamp(new_points))
        self.app.toast("Operation applied")


class Renderer:
    def __init__(self, app):
        self.app = app
        self.buttons = []

    def fit_text(self, text, font, max_width):
        if font.size(text)[0] <= max_width:
            return text
        suffix = "..."
        available = max_width - font.size(suffix)[0]
        clipped = ""
        for char in text:
            if font.size(clipped + char)[0] > available:
                break
            clipped += char
        return clipped + suffix

    def render(self):
        self.buttons = []
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(Color.APP)
        self.sidebar(mouse_pos)
        self.topbar()
        self.canvas()
        self.draw_shapes()
        self.pending_points()
        self.inspector(mouse_pos)
        self.compare_overlay()
        self.json_overlay()
        self.algorithm_preview_overlay()
        pygame.display.update()

    def sidebar(self, mouse_pos):
        draw_panel(LEFT_PANEL)
        draw_text("VectorLab", (LEFT_PANEL.x + 18, LEFT_PANEL.y + 16), FONT_TITLE, Color.INK)
        draw_text("Graphics Studio", (LEFT_PANEL.x + 20, LEFT_PANEL.y + 52), FONT_SM, Color.MUTED)

        y = LEFT_PANEL.y + 92
        draw_text("DRAW API", (LEFT_PANEL.x + 18, y), FONT_XS, Color.MUTED)
        y += 22
        for mode, label, icon, shortcut, _, _, _ in DRAW_TOOLS:
            button = Button(
                pygame.Rect(LEFT_PANEL.x + 14, y, LEFT_PANEL.w - 28, 36),
                f"{label}  ({shortcut})",
                icon,
                "mode",
                mode,
                active=mode == self.app.mode,
            )
            button.draw(mouse_pos)
            self.buttons.append(button)
            y += 42

        y += 8
        draw_text("FILES", (LEFT_PANEL.x + 18, y), FONT_XS, Color.MUTED)
        y += 24
        for label, key, action in [
            ("Save Drawing  (K)", "SV", "save"),
            ("Load + Inspect  (L)", "LD", "load"),
            ("Compare Algorithms  (M)", "CP", "benchmark"),
            ("Theme  (D)", "DM" if self.app.theme_name == "dark" else "LM", "toggle_theme"),
            ("Clear Canvas  (C)", "XX", "clear"),
        ]:
            disabled = action == "save" and not self.app.shapes
            button = Button(pygame.Rect(LEFT_PANEL.x + 14, y, LEFT_PANEL.w - 28, 34), label, key, action, disabled=disabled)
            button.draw(mouse_pos)
            self.buttons.append(button)
            y += 40

    def topbar(self):
        draw_panel(TOP_BAR)
        tool = DRAW_TOOL_BY_MODE[self.app.mode]
        need = tool[6]
        badge = pygame.Rect(TOP_BAR.x + 16, TOP_BAR.y + 12, 164, 28)
        pygame.draw.rect(screen, Color.SELECT_SOFT, badge, border_radius=8)
        pygame.draw.rect(screen, Color.SELECT, badge, 1, border_radius=8)
        draw_text(tool[1], (badge.x + 12, badge.y + 5), FONT_SM, Color.TEXT)

        draw_text(f"{len(self.app.pending_points)} / {need} points", (TOP_BAR.x + 198, TOP_BAR.y + 17), FONT_MD, Color.TEXT)
        selected = self.app.selected_index + 1 if self.app.selected_index is not None else "-"
        draw_text(f"Selected: {selected}", (TOP_BAR.right - 230, TOP_BAR.y + 17), FONT_SM, Color.MUTED)
        draw_text(f"Shapes: {len(self.app.shapes)}", (TOP_BAR.right - 112, TOP_BAR.y + 17), FONT_SM, Color.MUTED)

        if pygame.time.get_ticks() < self.app.toast_until:
            toast_rect = pygame.Rect(TOP_BAR.x + 16, TOP_BAR.y + 46, TOP_BAR.w - 32, 20)
            pygame.draw.rect(screen, Color.FIELD, toast_rect, border_radius=5)
            message = self.fit_text(self.app.toast_message, FONT_XS, toast_rect.w - 18)
            draw_text(message, (toast_rect.x + 9, toast_rect.y + 2), FONT_XS, Color.MUTED)

    def canvas(self):
        pygame.draw.rect(screen, Color.PANEL, CANVAS, border_radius=10)
        pygame.draw.rect(screen, Color.BORDER, CANVAS, 1, border_radius=10)

        for x in range(CANVAS.left + 24, CANVAS.right, 24):
            pygame.draw.line(screen, Color.GRID, (x, CANVAS.top + 1), (x, CANVAS.bottom - 1))
        for y in range(CANVAS.top + 24, CANVAS.bottom, 24):
            pygame.draw.line(screen, Color.GRID, (CANVAS.left + 1, y), (CANVAS.right - 1, y))

        overlay = pygame.Surface(CLIP_RECT.size, pygame.SRCALPHA)
        overlay.fill((56, 189, 248, 22))
        screen.blit(overlay, CLIP_RECT)
        pygame.draw.rect(screen, Color.SELECT, CLIP_RECT, 2, border_radius=4)
        draw_text("CLIPPING WINDOW", (CLIP_RECT.x + 12, CLIP_RECT.y + 10), FONT_XS, Color.SELECT)

    def draw_shapes(self):
        for index, shape in enumerate(self.app.shapes):
            selected = index == self.app.selected_index
            if shape["type"] == "dda":
                draw_dda(screen, int(shape["x1"]), int(shape["y1"]), int(shape["x2"]), int(shape["y2"]), Color.BLUE)
            elif shape["type"] == "bresenham":
                draw_bresenham(screen, int(shape["x1"]), int(shape["y1"]), int(shape["x2"]), int(shape["y2"]), Color.RED)
            elif shape["type"] == "midpoint_circle":
                draw_midpoint_circle(screen, int(shape["xc"]), int(shape["yc"]), int(shape["r"]), Color.CYAN)
            elif shape["type"] == "bresenham_circle":
                draw_bresenham_circle(screen, int(shape["xc"]), int(shape["yc"]), int(shape["r"]), Color.INK)
            elif shape["type"] == "polygon":
                pts = [(p.x, p.y) for p in shape["points"]]
                if len(pts) >= 2:
                    pygame.draw.polygon(screen, Color.VIOLET, pts, 2)
            elif shape["type"] == "bezier":
                draw_bezier(screen, shape["points"], Color.GREEN)
            elif shape["type"] == "bspline":
                draw_bspline(screen, shape["points"], Color.INK)

            if selected:
                pygame.draw.rect(screen, Color.SELECT, ShapeAPI.bounds(shape).inflate(18, 18), 2, border_radius=6)

    def pending_points(self):
        tool = DRAW_TOOL_BY_MODE[self.app.mode]
        color = tool_color(tool)
        for index, point in enumerate(self.app.pending_points):
            pygame.draw.circle(screen, Color.PANEL, point, 9)
            pygame.draw.circle(screen, color, point, 6)
            label = FONT_XS.render(str(index + 1), True, (255, 255, 255))
            screen.blit(label, label.get_rect(center=point))
        if len(self.app.pending_points) > 1:
            pygame.draw.lines(screen, color, False, self.app.pending_points, 1)

    def inspector(self, mouse_pos):
        draw_panel(RIGHT_PANEL)
        draw_text("Operations", (RIGHT_PANEL.x + 18, RIGHT_PANEL.y + 16), FONT_LG, Color.INK)
        selected = self.app.selected_shape()
        subtitle = "Shape center is the transform pivot" if selected else "Right-click a shape to select"
        draw_text(subtitle, (RIGHT_PANEL.x + 18, RIGHT_PANEL.y + 46), FONT_SM, Color.MUTED)

        y = RIGHT_PANEL.y + 76
        groups = [
            ("MOVE", [("Left", "<", "left"), ("Right", ">", "right"), ("Up", "^", "up"), ("Down", "v", "down")]),
            ("ROTATE", [("-15 deg  (Q)", "CC", "rotate_ccw"), ("+15 deg  (E)", "CW", "rotate_cw")]),
            ("SCALE", [("90%  (-)", "-", "scale_down"), ("110%  (+)", "+", "scale_up")]),
            ("REFLECT", [("Flip X  (X)", "FX", "reflect_x"), ("Flip Y  (Y)", "FY", "reflect_y")]),
            ("SHEAR", [("X-  (H)", "X-", "shear_left"), ("X+  (J)", "X+", "shear_right"), ("Y-  (U)", "Y-", "shear_up"), ("Y+  (I)", "Y+", "shear_down")]),
            ("CLIP WINDOW", [("W-  ([)", "W-", "clip_w_down"), ("W+  (])", "W+", "clip_w_up"), ("H-  (;)", "H-", "clip_h_down"), ("H+  (')", "H+", "clip_h_up")]),
        ]

        for title, items in groups:
            draw_text(title, (RIGHT_PANEL.x + 18, y), FONT_XS, Color.MUTED)
            y += 22
            for i, (label, key, action) in enumerate(items):
                col = i % 2
                row = i // 2
                rect = pygame.Rect(RIGHT_PANEL.x + 14 + col * 132, y + row * 34, 124, 30)
                disabled = selected is None and not action.startswith("clip_")
                button = Button(rect, label, key, action, disabled=disabled)
                button.draw(mouse_pos)
                self.buttons.append(button)
            y += ((len(items) + 1) // 2) * 34 + 9

        y -= 6
        draw_text("Selected Shape", (RIGHT_PANEL.x + 18, y), FONT_XS, Color.MUTED)
        y += 24
        if selected:
            details = [
                f"Index: {self.app.selected_index + 1}",
                f"Type: {selected['type']}",
                f"Radius: {selected['r']}" if "circle" in selected["type"] else f"Points: {len(ShapeAPI.points(selected))}",
            ]
        else:
            details = ["No active selection"]
        for item in details:
            draw_text(item, (RIGHT_PANEL.x + 18, y), FONT_SM, Color.TEXT)
            y += 20

        y = RIGHT_PANEL.bottom - 62
        bottom_buttons = [
            ("Delete  (Del)", "DL", "delete"),
            ("Animate  (A)", "AN", "animate"),
        ]
        for i, (label, key, action) in enumerate(bottom_buttons):
            rect = pygame.Rect(RIGHT_PANEL.x + 14 + i * 132, y, 124, 36)
            button = Button(rect, label, key, action, disabled=selected is None)
            button.draw(mouse_pos)
            self.buttons.append(button)

    def json_overlay(self):
        if not self.app.show_json:
            return
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((15, 23, 42, 130))
        screen.blit(veil, (0, 0))

        modal = pygame.Rect(170, 80, WIDTH - 340, HEIGHT - 160)
        pygame.draw.rect(screen, Color.FIELD, modal, border_radius=10)
        pygame.draw.rect(screen, (71, 85, 105), modal, 1, border_radius=10)
        draw_text("drawing.json", (modal.x + 24, modal.y + 20), FONT_LG, (255, 255, 255))
        draw_text("Press any key", (modal.right - 122, modal.y + 25), FONT_SM, (203, 213, 225))

        max_lines = (modal.h - 76) // 20
        for i, line in enumerate(self.app.json_lines[:max_lines]):
            color = (186, 230, 253) if i % 2 == 0 else (226, 232, 240)
            line_surf = FONT_MONO.render(line, True, color)
            screen.blit(line_surf, (modal.x + 24, modal.y + 62 + i * 20))

    def compare_overlay(self):
        if not self.app.show_compare:
            return
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((15, 23, 42, 130))
        screen.blit(veil, (0, 0))

        modal = pygame.Rect(230, 118, WIDTH - 460, HEIGHT - 236)
        pygame.draw.rect(screen, Color.FIELD, modal, border_radius=10)
        pygame.draw.rect(screen, Color.BORDER, modal, 1, border_radius=10)
        draw_text("Algorithm Comparison", (modal.x + 24, modal.y + 20), FONT_LG, Color.TEXT)
        draw_text("Press any key", (modal.right - 122, modal.y + 25), FONT_SM, Color.MUTED)

        y = modal.y + 70
        for line in self.app.compare_lines:
            draw_text(line, (modal.x + 28, y), FONT_MONO, Color.TEXT)
            y += 26

    def algorithm_preview_overlay(self):
        preview = self.app.algorithm_preview
        if preview is None:
            return

        now = pygame.time.get_ticks()
        elapsed = now - preview.started_at
        row_interval = max(12, min(95, 4000 // max(1, len(preview.rows))))
        pixel_interval = max(2, min(10, 4000 // max(1, len(preview.pixels))))
        row_count = min(len(preview.rows), max(1, elapsed // row_interval + 1))
        pixel_count = min(len(preview.pixels), max(1, elapsed // pixel_interval + 1))

        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((15, 23, 42, 155))
        screen.blit(veil, (0, 0))

        modal = pygame.Rect(92, 54, WIDTH - 184, HEIGHT - 108)
        top_panel_h = 140
        equation_panel = pygame.Rect(modal.x + 24, modal.y + 22, modal.w - 300, top_panel_h)
        method_panel = pygame.Rect(equation_panel.right + 24, modal.y + 22, modal.right - equation_panel.right - 48, top_panel_h)
        equation_rect = pygame.Rect(equation_panel.x + 16, equation_panel.y + 36, equation_panel.w - 32, equation_panel.h - 46)
        method_rect = pygame.Rect(method_panel.x + 16, method_panel.y + 36, method_panel.w - 32, method_panel.h - 46)
        table_rect = pygame.Rect(modal.x + 24, equation_panel.bottom + 16, 610, modal.bottom - equation_panel.bottom - 40)
        pixel_rect = pygame.Rect(table_rect.right + 24, table_rect.y, modal.right - table_rect.right - 48, table_rect.h)

        pygame.draw.rect(screen, Color.FIELD, modal, border_radius=10)
        pygame.draw.rect(screen, Color.BORDER, modal, 1, border_radius=10)
        pygame.draw.rect(screen, Color.PANEL, equation_panel, border_radius=8)
        pygame.draw.rect(screen, Color.BORDER, equation_panel, 1, border_radius=8)
        pygame.draw.rect(screen, Color.PANEL, method_panel, border_radius=8)
        pygame.draw.rect(screen, Color.BORDER, method_panel, 1, border_radius=8)

        draw_text(preview.title, (equation_panel.x + 14, equation_panel.y + 10), FONT_FORMULA_TITLE, Color.TEXT)
        equation_bounds = (equation_rect.w, equation_rect.h)
        if preview.equation_surface is None or preview.equation_size != equation_bounds or preview.equation_color != Color.CYAN:
            preview.equation_surface = MATH_RENDERER.render_block(
                preview.equations,
                equation_bounds[0],
                equation_bounds[1],
                Color.CYAN,
            )
            preview.equation_size = equation_bounds
            preview.equation_color = Color.CYAN
        equation_surface = preview.equation_surface
        if equation_surface is not None:
            equation_x = equation_rect.x
            equation_y = equation_rect.y + max(0, (equation_rect.h - equation_surface.get_height()) // 2)
            screen.blit(equation_surface, (equation_x, equation_y))

        draw_text("Rendering Method", (method_panel.x + 14, method_panel.y + 10), FONT_FORMULA_TITLE, Color.MUTED)
        method_lines = wrap_text_lines(preview.render_method, FONT_SM, method_rect.w, max_lines=3)
        method_y = method_rect.y + 18
        for line in method_lines:
            draw_text(line, (method_rect.x, method_y), FONT_SM, Color.TEXT)
            method_y += 20
        draw_text("Esc to draw", (modal.right - 96, modal.bottom - 28), FONT_XS, Color.MUTED)

        pygame.draw.rect(screen, Color.PANEL, table_rect, border_radius=8)
        pygame.draw.rect(screen, Color.BORDER, table_rect, 1, border_radius=8)
        pygame.draw.rect(screen, Color.PANEL, pixel_rect, border_radius=8)
        pygame.draw.rect(screen, Color.BORDER, pixel_rect, 1, border_radius=8)

        self.draw_preview_table(preview, table_rect, row_count)
        self.draw_preview_pixels(preview, pixel_rect, pixel_count)

    def draw_preview_table(self, preview, rect, row_count):
        col_count = len(preview.headers)
        scrollbar_w = 16
        viewport_w = rect.w - 32 - scrollbar_w
        col_widths = self.preview_column_widths(preview)
        content_w = sum(col_widths)
        max_h_scroll = max(0, content_w - viewport_w)
        preview.h_scroll = max(0, min(preview.h_scroll, max_h_scroll))
        y = rect.y + 16
        x = rect.x + 16 - preview.h_scroll
        old_clip = screen.get_clip()
        clip_rect = pygame.Rect(rect.x + 16, rect.y + 8, viewport_w, rect.h - 46)
        screen.set_clip(clip_rect)

        col_x = x
        for index, header in enumerate(preview.headers):
            col_w = col_widths[index]
            label = clipped_text(header, FONT_XS, col_w - 10)
            draw_text(label, (col_x, y), FONT_XS, Color.MUTED)
            col_x += col_w
        y += 24
        screen.set_clip(old_clip)
        pygame.draw.line(screen, Color.BORDER, (rect.x + 14, y - 5), (rect.right - 28, y - 5))

        max_rows = max(1, (rect.bottom - y - 62) // 22)
        max_start = max(0, row_count - max_rows)
        if preview.follow_latest:
            preview.scroll = max_start
        else:
            preview.scroll = max(0, min(preview.scroll, max_start))
        start = preview.scroll
        visible_rows = preview.rows[start:row_count]
        visible_rows = visible_rows[:max_rows]
        body_clip = pygame.Rect(rect.x + 16, y - 2, viewport_w, max_rows * 22 + 4)
        screen.set_clip(body_clip)
        for row_index, row in enumerate(visible_rows):
            row_y = y + row_index * 22
            if (start + row_index) % 2 == 0:
                stripe = pygame.Rect(rect.x + 10, row_y - 2, rect.w - 40, 20)
                pygame.draw.rect(screen, Color.FIELD, stripe, border_radius=4)
            col_x = x
            for col_index, value in enumerate(row[:col_count]):
                col_w = col_widths[col_index]
                label = clipped_text(value, FONT_MONO, col_w - 10)
                draw_text(label, (col_x, row_y), FONT_MONO, Color.TEXT)
                col_x += col_w
        screen.set_clip(old_clip)

        self.draw_preview_scrollbars(rect, row_count, max_rows, start, preview.h_scroll, max_h_scroll)
        footer = f"{row_count} / {len(preview.rows)} steps"
        draw_text(footer, (rect.x + 16, rect.bottom - 24), FONT_XS, Color.MUTED)

    def preview_column_widths(self, preview):
        widths = []
        for index, header in enumerate(preview.headers):
            width = max(120, FONT_XS.size(str(header))[0] + 28)
            for row in preview.rows:
                if index < len(row):
                    width = max(width, min(380, FONT_MONO.size(str(row[index]))[0] + 28))
            widths.append(width)
        return widths

    def draw_preview_scrollbars(self, rect, row_count, max_rows, start, h_scroll, max_h_scroll):
        v_track = pygame.Rect(rect.right - 22, rect.y + 38, 8, rect.h - 90)
        pygame.draw.rect(screen, Color.FIELD, v_track, border_radius=4)
        pygame.draw.rect(screen, Color.BORDER, v_track, 1, border_radius=4)
        if row_count <= max_rows:
            thumb_h = v_track.h
            thumb_y = v_track.y
        else:
            thumb_h = max(28, int(v_track.h * (max_rows / row_count)))
            thumb_range = max(1, v_track.h - thumb_h)
            thumb_y = v_track.y + int(thumb_range * (start / max(1, row_count - max_rows)))
        pygame.draw.rect(screen, Color.SELECT, (v_track.x, thumb_y, v_track.w, thumb_h), border_radius=4)

        h_track = pygame.Rect(rect.x + 16, rect.bottom - 44, rect.w - 54, 8)
        pygame.draw.rect(screen, Color.FIELD, h_track, border_radius=4)
        pygame.draw.rect(screen, Color.BORDER, h_track, 1, border_radius=4)
        if max_h_scroll <= 0:
            thumb_w = h_track.w
            thumb_x = h_track.x
        else:
            thumb_w = max(36, int(h_track.w * (h_track.w / (h_track.w + max_h_scroll))))
            thumb_range = max(1, h_track.w - thumb_w)
            thumb_x = h_track.x + int(thumb_range * (h_scroll / max_h_scroll))
        pygame.draw.rect(screen, Color.SELECT, (thumb_x, h_track.y, thumb_w, h_track.h), border_radius=4)

    def draw_preview_pixels(self, preview, rect, pixel_count):
        draw_text("Pixel output", (rect.x + 16, rect.y + 14), FONT_SM, Color.TEXT)
        draw_text(f"{pixel_count} / {len(preview.pixels)} pixels", (rect.x + 16, rect.y + 38), FONT_XS, Color.MUTED)
        square_size = min(rect.w - 36, rect.h - 86)
        viewport = pygame.Rect(0, 0, square_size, square_size)
        viewport.center = (rect.centerx, rect.y + 68 + square_size // 2)
        pygame.draw.rect(screen, Color.FIELD, viewport, border_radius=6)

        if not preview.pixels:
            draw_text("No visible pixels", (viewport.x + 16, viewport.y + 16), FONT_SM, Color.MUTED)
            return

        xs = [point[0] for point in preview.pixels]
        ys = [point[1] for point in preview.pixels]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(1, max_x - min_x + 1)
        span_y = max(1, max_y - min_y + 1)
        scale = min((viewport.w - 28) / span_x, (viewport.h - 28) / span_y)
        scale = max(0.05, scale)
        dot_size = max(1, min(9, int(scale)))
        drawn_w = span_x * scale
        drawn_h = span_y * scale
        origin_x = viewport.centerx - drawn_w / 2
        origin_y = viewport.centery - drawn_h / 2
        draw_color = getattr(Color, preview.color_name)

        for x, y in preview.pixels[:pixel_count]:
            px = int(origin_x + (x - min_x) * scale)
            py = int(origin_y + (y - min_y) * scale)
            pygame.draw.rect(screen, draw_color, (px, py, dot_size, dot_size), border_radius=1)


class App:
    def __init__(self):
        self.theme_name = "dark"
        Color.apply(DARK_THEME)
        self.mode = "DDA"
        self.pending_points = []
        self.shapes = []
        self.selected_index = None
        self.toast_message = "Ready"
        self.toast_until = 0
        self.show_json = False
        self.show_compare = False
        self.algorithm_preview = None
        self.preview_message = None
        self.json_lines = []
        self.compare_lines = []
        self.drawing = DrawingAPI(self)
        self.transforms = TransformAPI(self)
        self.renderer = Renderer(self)

    def selected_shape(self):
        if self.selected_index is None:
            return None
        if not (0 <= self.selected_index < len(self.shapes)):
            self.selected_index = None
            return None
        return self.shapes[self.selected_index]

    def toast(self, message, ms=1800):
        self.toast_message = message
        self.toast_until = pygame.time.get_ticks() + ms

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        Color.apply(LIGHT_THEME if self.theme_name == "light" else DARK_THEME)
        self.toast(f"{self.theme_name.title()} mode")

    def set_mode(self, mode):
        self.mode = mode
        self.pending_points.clear()
        self.toast(f"{DRAW_TOOL_BY_MODE[mode][1]} selected")

    def select_at(self, pos):
        best = None
        for index, shape in enumerate(self.shapes):
            score = ShapeAPI.hit_score(shape, pos)
            if score is not None and (best is None or score < best[0]):
                best = (score, index)
        if best:
            self.selected_index = best[1]
            self.toast(f"Selected shape {best[1] + 1}")
        else:
            self.toast("No shape at pointer")

    def save(self):
        save_shapes(self.shapes)
        self.toast("Saved drawing.json")

    def commit_preview(self):
        if self.algorithm_preview is None:
            return
        shape = self.algorithm_preview.shape
        message = self.preview_message or "Shape added"
        self.algorithm_preview = None
        self.preview_message = None
        self.drawing.add(shape, message)

    def load(self):
        self.shapes = load_shapes()
        self.selected_index = len(self.shapes) - 1 if self.shapes else None
        self.load_json_lines()
        self.show_json = True
        self.toast("Loaded drawing.json")

    def load_json_lines(self):
        if not os.path.exists("drawing.json"):
            self.json_lines = ["[drawing.json not found]"]
            return
        try:
            with open("drawing.json", "r") as file:
                self.json_lines = json.dumps(json.load(file), indent=2).splitlines()
        except Exception as exc:
            self.json_lines = [f"Error reading drawing.json: {exc}"]

    def benchmark(self):
        surface = pygame.Surface((720, 420))
        line_args = (surface, 24, 28, 690, 380, Color.INK)
        circle_args = (surface, 360, 210, 150, Color.INK)
        curve_points = [Point(40, 330), Point(170, 40), Point(520, 70), Point(680, 330)]

        def run_many(func, args, count):
            def wrapped():
                for _ in range(count):
                    func(*args)
            return compare(wrapped)

        dda_time = run_many(draw_dda, line_args, 180)
        bres_time = run_many(draw_bresenham, line_args, 180)
        midpoint_time = run_many(draw_midpoint_circle, circle_args, 120)
        bres_circle_time = run_many(draw_bresenham_circle, circle_args, 120)
        bezier_time = run_many(draw_bezier, (surface, curve_points, Color.INK), 90)
        bspline_time = run_many(draw_bspline, (surface, curve_points, Color.INK), 90)

        self.compare_lines = [
            "Repeated draw benchmark on an offscreen surface",
            "",
            f"Line:    DDA {dda_time:.6f}s    Bresenham {bres_time:.6f}s",
            f"Circle:  Midpoint {midpoint_time:.6f}s    Bresenham {bres_circle_time:.6f}s",
            f"Curve:   Bezier {bezier_time:.6f}s    B-Spline {bspline_time:.6f}s",
            "",
            "Lower time is faster for this run.",
        ]
        self.show_compare = True
        self.toast("Algorithm comparison ready", 2200)

    def clear(self):
        self.shapes.clear()
        self.pending_points.clear()
        self.algorithm_preview = None
        self.preview_message = None
        self.selected_index = None
        self.toast("Canvas cleared")

    def delete_selected(self):
        if self.selected_index is None:
            self.toast("Select a shape first")
            return
        del self.shapes[self.selected_index]
        if not self.shapes:
            self.selected_index = None
        else:
            self.selected_index = min(self.selected_index, len(self.shapes) - 1)
        self.toast("Selected shape deleted")

    def resize_clip(self, dw, dh):
        center = CLIP_RECT.center
        new_w = max(120, min(CANVAS.w - 48, CLIP_RECT.w + dw))
        new_h = max(100, min(CANVAS.h - 48, CLIP_RECT.h + dh))
        CLIP_RECT.size = (new_w, new_h)
        CLIP_RECT.center = center
        CLIP_RECT.clamp_ip(CANVAS.inflate(-24, -24))
        self.toast(f"Clip window: {CLIP_RECT.w} x {CLIP_RECT.h}")

    def animate(self):
        selected = self.selected_shape()
        if selected is None:
            self.toast("Select a shape first")
            return
        frames = animate_translation(ShapeAPI.points(selected), steps=24, dx=8, dy=0)
        original = selected
        for frame in frames:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            self.shapes[self.selected_index] = ShapeAPI.rebuild(original, ShapeAPI.clamp(frame))
            self.renderer.render()
            pygame.time.delay(28)
        self.shapes[self.selected_index] = original
        self.toast("Animation preview complete")

    def dispatch(self, action, value=None):
        if action == "mode":
            self.set_mode(value)
        elif action == "save":
            self.save()
        elif action == "load":
            self.load()
        elif action == "benchmark":
            self.benchmark()
        elif action == "toggle_theme":
            self.toggle_theme()
        elif action == "delete":
            self.delete_selected()
        elif action == "clip_w_down":
            self.resize_clip(-40, 0)
        elif action == "clip_w_up":
            self.resize_clip(40, 0)
        elif action == "clip_h_down":
            self.resize_clip(0, -40)
        elif action == "clip_h_up":
            self.resize_clip(0, 40)
        elif action == "clear":
            self.clear()
        elif action == "animate":
            self.animate()
        else:
            self.transforms.apply(action)

    def handle_key(self, event):
        if self.algorithm_preview is not None:
            if event.key == pygame.K_ESCAPE:
                self.commit_preview()
            elif event.key == pygame.K_UP:
                self.scroll_preview(-1)
            elif event.key == pygame.K_DOWN:
                self.scroll_preview(1)
            elif event.key == pygame.K_LEFT:
                self.scroll_preview_horizontal(-1)
            elif event.key == pygame.K_RIGHT:
                self.scroll_preview_horizontal(1)
            return
        if self.show_json:
            self.show_json = False
            return
        if self.show_compare:
            self.show_compare = False
            return

        for mode, _, _, _, key, _, _ in DRAW_TOOLS:
            if event.key == key:
                self.set_mode(mode)
                return

        keymap = {
            pygame.K_k: "save",
            pygame.K_l: "load",
            pygame.K_m: "benchmark",
            pygame.K_d: "toggle_theme",
            pygame.K_c: "clear",
            pygame.K_a: "animate",
            pygame.K_DELETE: "delete",
            pygame.K_BACKSPACE: "delete",
            pygame.K_LEFT: "left",
            pygame.K_RIGHT: "right",
            pygame.K_UP: "up",
            pygame.K_DOWN: "down",
            pygame.K_LEFTBRACKET: "clip_w_down",
            pygame.K_RIGHTBRACKET: "clip_w_up",
            pygame.K_SEMICOLON: "clip_h_down",
            pygame.K_QUOTE: "clip_h_up",
            pygame.K_q: "rotate_ccw",
            pygame.K_e: "rotate_cw",
            pygame.K_MINUS: "scale_down",
            pygame.K_EQUALS: "scale_up",
            pygame.K_x: "reflect_x",
            pygame.K_y: "reflect_y",
            pygame.K_h: "shear_left",
            pygame.K_j: "shear_right",
            pygame.K_u: "shear_up",
            pygame.K_i: "shear_down",
        }
        if event.key in keymap:
            self.dispatch(keymap[event.key])

    def handle_mouse(self, event):
        if self.algorithm_preview is not None:
            if event.button in (4, 5):
                direction = 1 if event.button == 5 else -1
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.scroll_preview_horizontal(direction)
                else:
                    self.scroll_preview(direction)
            return
        if self.show_json or self.show_compare:
            return
        for button in self.renderer.buttons:
            if button.rect.collidepoint(event.pos) and not button.disabled:
                self.dispatch(button.action, button.value)
                return
        if event.button == 3 and CANVAS.collidepoint(event.pos):
            self.select_at(event.pos)
        elif event.button == 1 and CANVAS.collidepoint(event.pos):
            self.pending_points.append(event.pos)
            self.drawing.finish_if_ready()

    def handle_mousewheel(self, event):
        if self.algorithm_preview is not None:
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                self.scroll_preview_horizontal(-event.y)
            else:
                self.scroll_preview(-event.y)

    def scroll_preview(self, direction):
        preview = self.algorithm_preview
        if preview is None:
            return
        preview.follow_latest = False
        now = pygame.time.get_ticks()
        elapsed = now - preview.started_at
        row_interval = max(12, min(95, 4000 // max(1, len(preview.rows))))
        row_count = min(len(preview.rows), max(1, elapsed // row_interval + 1))
        max_rows = max(1, (HEIGHT - 108 - 76 - 16 - 40 - 40 - 62) // 22)
        max_start = max(0, row_count - max_rows)
        preview.scroll = max(0, min(max_start, preview.scroll + direction * 3))
        if preview.scroll >= max_start:
            preview.follow_latest = True

    def scroll_preview_horizontal(self, direction):
        preview = self.algorithm_preview
        if preview is None:
            return
        col_widths = self.renderer.preview_column_widths(preview)
        content_w = sum(col_widths)
        viewport_w = 610 - 32 - 16
        max_h_scroll = max(0, content_w - viewport_w)
        preview.h_scroll = max(0, min(max_h_scroll, preview.h_scroll + direction * 60))

    def run(self):
        running = True
        while running:
            self.renderer.render()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse(event)
                elif event.type == pygame.MOUSEWHEEL:
                    self.handle_mousewheel(event)
            clock.tick(FPS)


if __name__ == "__main__":
    App().run()
    pygame.quit()
    sys.exit()
