import json
import math
import os
import sys
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

LEFT_PANEL = pygame.Rect(GAP, GAP, SIDEBAR_W, HEIGHT - 2 * GAP)
RIGHT_PANEL = pygame.Rect(WIDTH - INSPECTOR_W - GAP, GAP, INSPECTOR_W, HEIGHT - 2 * GAP)
TOP_BAR = pygame.Rect(LEFT_PANEL.right + GAP, GAP, RIGHT_PANEL.left - LEFT_PANEL.right - 2 * GAP, 74)
CANVAS = pygame.Rect(LEFT_PANEL.right + GAP, TOP_BAR.bottom + GAP, TOP_BAR.w, HEIGHT - TOP_BAR.bottom - 2 * GAP)
CLIP_RECT = pygame.Rect(CANVAS.x + 160, CANVAS.y + 96, CANVAS.w - 320, CANVAS.h - 192)


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


def draw_text(text, pos, font=FONT_SM, color=Color.TEXT):
    surf = font.render(text, True, color)
    screen.blit(surf, pos)
    return surf.get_rect(topleft=pos)


def draw_panel(rect):
    pygame.draw.rect(screen, Color.PANEL, rect, border_radius=10)
    pygame.draw.rect(screen, Color.BORDER, rect, 1, border_radius=10)


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
            self.add({"type": "dda" if mode == "DDA" else "bresenham", "x1": x1, "y1": y1, "x2": x2, "y2": y2})
        elif "Circle" in mode and len(points) == 2:
            xc, yc = points[0]
            x2, y2 = points[1]
            radius = int(math.hypot(x2 - xc, y2 - yc))
            self.add({"type": "midpoint_circle" if mode == "Midpoint Circle" else "bresenham_circle", "xc": xc, "yc": yc, "r": radius})
        elif mode == "Polygon" and len(points) == 4:
            self.add({"type": "polygon", "points": [Point(x, y) for x, y in points]})
        elif mode == "Bezier" and len(points) == 4:
            self.add({"type": "bezier", "points": [Point(x, y) for x, y in points]})
        elif mode == "B-Spline" and len(points) == 4:
            self.add({"type": "bspline", "points": [Point(x, y) for x, y in points]})
        elif mode == "Clip Line" and len(points) == 2:
            x1, y1 = points[0]
            x2, y2 = points[1]
            result = cohen_sutherland_clip(x1, y1, x2, y2, CLIP_RECT.left, CLIP_RECT.top, CLIP_RECT.right, CLIP_RECT.bottom)
            if result:
                x1, y1, x2, y2 = result
                self.add({"type": "dda", "x1": x1, "y1": y1, "x2": x2, "y2": y2}, "Clipped line added")
            else:
                self.app.pending_points.clear()
                self.app.toast("Line rejected by clipping window")
        elif mode == "Clip Polygon" and len(points) == 4:
            poly = [Point(x, y) for x, y in points]
            clipped = clip_polygon(poly, CLIP_RECT.left, CLIP_RECT.top, CLIP_RECT.right, CLIP_RECT.bottom)
            self.add({"type": "polygon", "points": clipped}, "Clipped polygon added")

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
            clock.tick(FPS)


if __name__ == "__main__":
    App().run()
    pygame.quit()
    sys.exit()
