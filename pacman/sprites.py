"""Pixel-art sprites recreated from the arcade sprite sheet.

Everything is built at the native arcade resolution (16x16 sprites) from
bitmaps or pixel rules, then the whole screen is scaled up with nearest
neighbour filtering so the chunky look is preserved.
"""

import math

import pygame

from .constants import (BLUE, BROWN, CYAN, DIRS, DOWN, GHOST_COLORS, GHOST_POINTS,
                        FRUIT_POINTS, GREEN, LEFT, PEACH, PINK, RED, RIGHT, UP,
                        WHITE, YELLOW)


def _surface(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def bitmap(rows, palette, box=(16, 16)):
    """Build a surface from strings; the image is centred inside ``box``."""
    h = len(rows)
    w = max(len(r) for r in rows)
    box = box or (w, h)
    surf = _surface(*box)
    ox, oy = (box[0] - w) // 2, (box[1] - h) // 2
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            color = palette.get(ch)
            if color:
                surf.set_at((ox + x, oy + y), color)
    return surf


# ---------------------------------------------------------------- Pac-Man
def pac_frame(facing, half_angle, size=16, radius=6.5, color=YELLOW):
    """A Pac-Man disc with a wedge-shaped mouth of the given half angle."""
    surf = _surface(size, size)
    c = size // 2 - 1
    fx, fy = facing
    r2 = radius * radius
    for y in range(size):
        for x in range(size):
            dx, dy = x - c, y - c
            if dx * dx + dy * dy > r2:
                continue
            if half_angle >= 180:
                continue
            if half_angle > 0 and (dx or dy):
                cos_a = (dx * fx + dy * fy) / math.hypot(dx, dy)
                if math.degrees(math.acos(max(-1.0, min(1.0, cos_a)))) < half_angle:
                    continue
            surf.set_at((x, y), color)
    return surf


def pop_frame():
    """The little burst Pac-Man leaves behind at the end of his death."""
    surf = _surface(16, 16)
    c = 7
    for k in range(8):
        a = k * math.pi / 4
        for r in (3, 4, 5):
            x = c + round(math.cos(a) * r)
            y = c + round(math.sin(a) * r)
            surf.set_at((x, y), YELLOW)
    return surf


# ---------------------------------------------------------------- Ghosts
GHOST_BODY = (
    ".....####.....",
    "...########...",
    "..##########..",
    ".############.",
    ".############.",
    ".############.",
    "##############",
    "##############",
    "##############",
    "##############",
    "##############",
    "##############",
)
GHOST_FEET = (
    ("##.###..###.##", "#...##..##...#"),
    ("####.####.####", ".##...##...##."),
)
EYE_WHITE = (".##.", "####", "####", "####", ".##.")
# (left eye origin, right eye origin, pupil offset inside the eye)
EYE_LAYOUT = {
    LEFT: ((1, 3), (7, 3), (0, 2)),
    RIGHT: ((3, 3), (9, 3), (2, 2)),
    UP: ((2, 2), (8, 2), (1, 0)),
    DOWN: ((2, 4), (8, 4), (1, 3)),
}
FRIGHT_EYES = ((4, 5), (8, 5))
FRIGHT_MOUTH = ("..##..##..##..", ".#..##..##..#.")


def _plot_rows(surf, rows, color, ox, oy, bit="#"):
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == bit:
                surf.set_at((ox + x, oy + y), color)


def draw_eyes(surf, direction, ox=1, oy=1):
    (lx, ly), (rx, ry), (px, py) = EYE_LAYOUT[direction]
    for ex, ey in ((lx, ly), (rx, ry)):
        _plot_rows(surf, EYE_WHITE, WHITE, ox + ex, oy + ey)
        for y in range(2):
            for x in range(2):
                surf.set_at((ox + ex + px + x, oy + ey + py + y), BLUE)


def ghost_body(color, frame):
    surf = _surface(16, 16)
    _plot_rows(surf, GHOST_BODY + GHOST_FEET[frame], color, 1, 1)
    return surf


def ghost_frame(color, direction, frame):
    surf = ghost_body(color, frame)
    draw_eyes(surf, direction)
    return surf


def fright_frame(frame, flash):
    body, face = (WHITE, RED) if flash else (BLUE, PEACH)
    surf = ghost_body(body, frame)
    for ex, ey in FRIGHT_EYES:
        for y in range(2):
            for x in range(2):
                surf.set_at((1 + ex + x, 1 + ey + y), face)
    _plot_rows(surf, FRIGHT_MOUTH, face, 1, 1 + 9)
    return surf


def eyes_frame(direction):
    surf = _surface(16, 16)
    draw_eyes(surf, direction)
    return surf


# ---------------------------------------------------------------- Fruit
FRUIT_PALETTE = {
    "r": RED, "w": WHITE, "b": BROWN, "g": GREEN, "o": (255, 184, 82),
    "y": YELLOW, "B": BLUE, "c": CYAN, "p": PEACH, "G": (0, 150, 0),
}


def _cherry():
    grid = [["."] * 14 for _ in range(14)]

    def line(x0, y0, x1, y1):
        steps = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(steps + 1):
            grid[round(y0 + (y1 - y0) * i / steps)][round(x0 + (x1 - x0) * i / steps)] = "b"

    line(3, 6, 10, 1)
    line(10, 8, 10, 1)
    line(10, 1, 12, 0)
    ball = (".rrrr.", "rrrrrr", "rrrrrr", "rwrrrr", "rrwrrr", ".rrrr.")
    for bx, by in ((0, 6), (7, 8)):
        for y, row in enumerate(ball):
            for x, ch in enumerate(row):
                if ch != ".":
                    grid[by + y][bx + x] = ch
    return ["".join(r) for r in grid]


FRUIT_ROWS = (
    _cherry(),
    (  # strawberry
        ".....g..g.....",
        "...gggggggg...",
        "..rrggggggrr..",
        ".rrrrggggrrrr.",
        ".rwrrrrrrrrwr.",
        "rrrrrwrrwrrrrr",
        "rwrrrrrrrrrrwr",
        "rrrrwrrrrwrrrr",
        ".rrrrrrwrrrrr.",
        ".rwrrrrrrrrwr.",
        "..rrrwrrwrrr..",
        "...rrrrrrrr...",
        ".....rrrr.....",
    ),
    (  # orange
        "......b.......",
        "......bggg....",
        "....ooggggg...",
        "..oooooggo....",
        ".oooooooooooo.",
        "oooooooooooooo",
        "oooooooooooooo",
        "oooooooooooooo",
        "oooooooooooooo",
        ".oooooooooooo.",
        ".oooooooooooo.",
        "..oooooooooo..",
        "....oooooo....",
    ),
    (  # apple
        "......b.......",
        ".......b......",
        "..rrrr.b.rrr..",
        ".rrrrrrrrrrrr.",
        "rrrrrrrrrrrrrr",
        "rrwrrrrrrrrrrr",
        "rwrrrrrrrrrrrr",
        "rwrrrrrrrrrrrr",
        "rwrrrrrrrrrrrr",
        "rrwrrrrrrrrrrr",
        ".rrrrrrrrrrrr.",
        ".rrrrrrrrrrrr.",
        "..rrrrrrrrrr..",
        "...rrr..rrr...",
    ),
    (  # melon
        "......b.......",
        "...gg.b.......",
        "..gggbb.......",
        "....GGgGG.....",
        "..GGgGGgGGgG..",
        ".GgGGwGGgGGwG.",
        ".GgGGGgGGwGgG.",
        "GwGGgGGgGGGgGG",
        "GgGwGgGGwGgGwG",
        "GGgGGGwGgGGgGG",
        ".GwGgGGgGGwGG.",
        ".GGgGwGGgGGgG.",
        "..GGGgGGwGgG..",
        "....GGgGGG....",
    ),
    (  # galaxian flagship
        "......y......",
        ".....yyy.....",
        "....yyyyy....",
        "B...rrrrr...B",
        "B..rrrrrrr..B",
        "BB.rryyyrr.BB",
        "BBBrryyyrrBBB",
        "BBBByyyyyBBBB",
        ".BBB.yyy.BBB.",
        "..BB..y..BB..",
        "...B..y..B...",
        "......y......",
    ),
    (  # bell
        "......yy......",
        ".....yyyy.....",
        "....yyyyyy....",
        "...yywyyyyy...",
        "...ywyyyyyy...",
        "..yywyyyyyyy..",
        "..ywyyyyyyyy..",
        "..ywyyyyyyyy..",
        ".yywyyyyyyyyy.",
        ".yyyyyyyyyyyy.",
        "yyyyyyyyyyyyyy",
        "yccccccccccccy",
        "......ww......",
        "......ww......",
    ),
    (  # key
        "....cccccc....",
        "...cc....cc...",
        "...cc....cc...",
        "...cccccccc...",
        "......ww......",
        "......ww......",
        "......wwww....",
        "......ww......",
        "......wwww....",
        "......ww......",
        "......ww......",
        "......wwww....",
        "......ww......",
    ),
)

# ---------------------------------------------------------------- Points
MINI_DIGITS = {
    "0": ("###", "#.#", "#.#", "#.#", "###"),
    "1": (".#.", "##.", ".#.", ".#.", "###"),
    "2": ("###", "..#", "###", "#..", "###"),
    "3": ("###", "..#", "###", "..#", "###"),
    "4": ("#.#", "#.#", "###", "..#", "..#"),
    "5": ("###", "#..", "###", "..#", "###"),
    "6": ("###", "#..", "###", "#.#", "###"),
    "7": ("###", "..#", "..#", "..#", "..#"),
    "8": ("###", "#.#", "###", "#.#", "###"),
    "9": ("###", "#.#", "###", "..#", "###"),
}


def points_frame(value, color):
    text = str(value)
    width = len(text) * 4 - 1
    surf = _surface(max(16, width), 16)
    ox = (surf.get_width() - width) // 2
    for i, ch in enumerate(text):
        _plot_rows(surf, MINI_DIGITS[ch], color, ox + i * 4, 5)
    return surf


# ---------------------------------------------------------------- Intermission extras
NAIL = ("w", "w", "p")
NAKED_BLINKY = (
    (
        ".....rrrr.......",
        "...rrrrrrrr.....",
        "..rrrwwrrwwr....",
        "..rrrwBrrwBr....",
        ".rrrrrrrrrrrr...",
        "rrrrrrrrrrrrrr..",
        "rrrrrrrrrrrrrr..",
        ".rr..rr..rr.rr..",
        ".r....r...r..r..",
    ),
    (
        ".....rrrr.......",
        "...rrrrrrrr.....",
        "..rrrwwrrwwr....",
        "..rrrwBrrwBr....",
        ".rrrrrrrrrrrr...",
        "rrrrrrrrrrrrrr..",
        "rrrrrrrrrrrrrr..",
        "..rr.rr..rr.rr..",
        "..r...r...r..r..",
    ),
)
CLOAK = (
    "..rrrrr.",
    ".rrrrrrr",
    "rrrrrrrr",
    "rr.rr.rr",
    "r...r..r",
)


class Sprites:
    def __init__(self):
        frames = (0, 22, 45)            # closed, half open, wide open
        self.pac = {d: [pac_frame(d, a) for a in frames] for d in DIRS}
        self.pac_death = [pac_frame(UP, a) for a in
                          (25, 40, 55, 70, 85, 100, 115, 130, 145, 160, 175)]
        self.pac_pop = pop_frame()
        self.pac_big = {d: [pac_frame(d, a, size=32, radius=13.5) for a in frames]
                        for d in (LEFT, RIGHT)}
        self.life = self.pac[LEFT][1]

        self.ghost = [{d: [ghost_frame(c, d, f) for f in (0, 1)] for d in DIRS}
                      for c in GHOST_COLORS]
        self.fright = [[fright_frame(f, flash) for flash in (False, True)] for f in (0, 1)]
        self.eyes = {d: eyes_frame(d) for d in DIRS}

        self.fruit = [bitmap(rows, FRUIT_PALETTE) for rows in FRUIT_ROWS]
        self.ghost_points = [points_frame(p, CYAN) for p in GHOST_POINTS]
        self.fruit_points = [points_frame(p, PINK) for p in FRUIT_POINTS]

        # intermission characters
        self.nail = bitmap(NAIL, {"w": WHITE, "p": PEACH}, box=None)
        self.patched = [self._patched(f) for f in (0, 1)]
        self.torn = {d: self._torn(d) for d in (LEFT, RIGHT, DOWN)}
        self.naked = [bitmap(rows, {"r": RED, "w": WHITE, "B": BLUE}) for rows in NAKED_BLINKY]
        self.cloak = bitmap(CLOAK, {"r": RED}, box=None)

    def _patched(self, frame):
        surf = ghost_frame(RED, LEFT, frame)
        for y in range(9, 13):
            for x in range(9, 14):
                surf.set_at((x, y), PEACH)
        for x in range(9, 14, 2):
            surf.set_at((x, 11), RED)
        return surf

    def _torn(self, direction):
        surf = ghost_frame(RED, direction, 0)
        for y in range(11, 16):
            for x in range(10, 16):
                surf.set_at((x, y), (0, 0, 0, 0))
        for y in range(12, 15):
            surf.set_at((11, y), PEACH)
            surf.set_at((12, y), PEACH)
        return surf
