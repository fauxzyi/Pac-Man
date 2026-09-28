"""The arcade maze: layout, walkability, pellets and wall rendering."""

import random

import pygame

from .constants import COLS, PEACH, PINK, ROWS, TILE, TUNNEL_ROW, WALL_BLUE, WHITE
from . import font

# '#' wall   '.' dot   'o' energizer   ' ' open (no dot)
# '-' ghost house door   '_' empty space outside the playfield
LAYOUT = (
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#o####.#####.##.#####.####o#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.##### ## #####.######",
    "_____#.##### ## #####.#_____",
    "_____#.##          ##.#_____",
    "_____#.## ###--### ##.#_____",
    "######.## #      # ##.######",
    "      .   #      #   .      ",
    "######.## #      # ##.######",
    "_____#.## ######## ##.#_____",
    "_____#.##          ##.#_____",
    "_____#.## ######## ##.#_____",
    "######.## ######## ##.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#o..##.......  .......##..o#",
    "###.##.##.########.##.##.###",
    "###.##.##.########.##.##.###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#.##########.##.##########.#",
    "#..........................#",
    "############################",
)

ENERGIZER = (
    "..####..",
    ".######.",
    "########",
    "########",
    "########",
    "########",
    ".######.",
    "..####..",
)


def _render_walls(color):
    """Draw the arcade-style outlined walls.

    The wall tiles are turned into a pixel mask, eroded so the outline sits
    inside the wall tiles, corner-rounded, and finally reduced to its
    one-pixel boundary.  One-tile-thick walls (the border and the ghost
    house) therefore come out as the arcade's double lines, thick blocks as
    single rounded outlines.
    """
    padx, pady = 2, 2
    gw, gh = COLS + 2 * padx, ROWS + 2 * pady
    width, height = gw * TILE, gh * TILE
    full = (1 << width) - 1

    def is_wall(c, r):
        if not 0 <= r < ROWS:
            return False
        if not 0 <= c < COLS:
            # the side boxes around the tunnels run off the edge of the screen
            if not 9 <= r <= 19:
                return False
            c = 0 if c < 0 else COLS - 1
        return LAYOUT[r][c] == "#"

    rows = []
    for r in range(gh):
        bits = 0
        for c in range(gw):
            if is_wall(c - padx, r - pady):
                bits |= 0xFF << (c * TILE)
        rows.extend([bits] * TILE)

    def shift(v, dx):          # bit x of the result = bit x+dx of v
        return v >> dx if dx >= 0 else (v << -dx) & full

    def erode(src, offsets):
        out = []
        for y in range(height):
            acc = full
            for dx, dy in offsets:
                yy = y + dy
                acc &= shift(src[yy], dx) if 0 <= yy < height else 0
                if not acc:
                    break
            out.append(acc)
        return out

    disc = [(dx, dy) for dx in range(-2, 3) for dy in range(-2, 3) if dx * dx + dy * dy <= 4]
    region = erode(rows, disc)
    for _ in range(2):          # shave convex corners for the rounded look
        rounded = []
        for y in range(height):
            v = region[y]
            up = region[y - 1] if y > 0 else 0
            down = region[y + 1] if y < height - 1 else 0
            left, right = shift(v, -1), shift(v, 1)
            rounded.append(v & ~(((~up | ~down) & (~left | ~right)) & full))
        region = rounded
    inner = erode(region, [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)])

    surf = pygame.Surface((COLS * TILE, ROWS * TILE), pygame.SRCALPHA)
    for y in range(ROWS * TILE):
        v = (region[y + pady * TILE] & ~inner[y + pady * TILE]) >> (padx * TILE)
        x = 0
        while v and x < COLS * TILE:
            if v & 1:
                surf.set_at((x, y), color)
            v >>= 1
            x += 1
    # ghost house door
    door = pygame.Rect(13 * TILE - 2, 12 * TILE + 3, 2 * TILE + 4, 2)
    surf.fill(PINK if color == WALL_BLUE else (0, 0, 0, 0), door)
    return surf


class Maze:
    def __init__(self):
        self.dots = set()
        self.energizers = set()
        for r, row in enumerate(LAYOUT):
            for c, ch in enumerate(row):
                if ch == ".":
                    self.dots.add((c, r))
                elif ch == "o":
                    self.energizers.add((c, r))
        self.blue = _render_walls(WALL_BLUE)
        self.white = _render_walls(WHITE)
        self.energizer_img = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        for y, row in enumerate(ENERGIZER):
            for x, ch in enumerate(row):
                if ch == "#":
                    self.energizer_img.set_at((x, y), PEACH)
        self._garbage = None

    def cell(self, c, r):
        if 0 <= c < COLS and 0 <= r < ROWS:
            return LAYOUT[r][c]
        if r == TUNNEL_ROW:
            return " "
        return "#"

    def blocked(self, c, r):
        """True if neither Pac-Man nor a roaming ghost may enter the tile."""
        return self.cell(c, r) in "#_-"

    def fresh_pellets(self, level):
        pellets = self.dots | self.energizers
        if level == 256:
            # the split-screen kill screen: the right half is corrupted and
            # its dots are gone, so the level can never be cleared
            pellets = {p for p in pellets if p[0] < COLS // 2}
        return pellets

    def draw_pellets(self, surf, pellets, top, show_energizers=True):
        for (c, r) in pellets:
            if (c, r) in self.energizers:
                if show_energizers:
                    surf.blit(self.energizer_img, (c * TILE, top + r * TILE))
            else:
                surf.fill(PEACH, (c * TILE + 3, top + r * TILE + 3, 2, 2))

    def draw_kill_screen(self, surf):
        """Garbage tiles over the right half, as on the real level 256."""
        if self._garbage is None:
            rng = random.Random(256)
            chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-!./\"@"
            colors = [WALL_BLUE, PEACH, PINK, (255, 0, 0), (0, 255, 255), (255, 184, 82), WHITE]
            self._garbage = [(c, r, rng.choice(chars), rng.choice(colors))
                             for r in range(3, 34) for c in range(COLS // 2, COLS)
                             if rng.random() < 0.55]
        surf.fill((0, 0, 0), (COLS // 2 * TILE, 3 * TILE, COLS // 2 * TILE, 31 * TILE))
        for c, r, ch, color in self._garbage:
            font.draw_text(surf, ch, c, r, color)
