"""Attract mode: the "CHARACTER / NICKNAME" roll call and the energizer chase."""

from . import font
from .constants import (BLACK, GHOST_COLORS, GHOST_NAMES, GHOST_NICKNAMES,
                        LEFT, PEACH, RIGHT, WHITE, CYAN, ORANGE)

GHOST_STEP = 120
CHASE_START = 60 + 4 * GHOST_STEP + 180
CHASE_Y = 20 * 8 + 4
ENERGIZER_X = 4 * 8 + 4


class Attract:
    def __init__(self, app):
        self.app = app
        self.s = app.sprites
        self.t = 0
        self.done = False
        self.pac_x = 240.0
        self.pac_dir = LEFT
        self.ghosts = [[260.0 + 18 * i, True] for i in range(4)]   # [x, alive]
        self.energized = False
        self.freeze = 0
        self.eaten = 0
        self.last_eat = None
        self.end_t = None

    def update(self):
        self.t += 1
        if self.t < CHASE_START:
            return
        if self.freeze:
            self.freeze -= 1
            if not self.freeze:
                self.last_eat = None
            return
        if not self.energized:
            self.pac_x -= 1.0
            for g in self.ghosts:
                g[0] -= 1.05
            if self.pac_x <= ENERGIZER_X:
                self.energized = True
                self.pac_dir = RIGHT
        else:
            self.pac_x += 1.0
            for i, g in enumerate(self.ghosts):
                if not g[1]:
                    continue
                g[0] += 0.5
                if abs(g[0] - self.pac_x) < 4:
                    g[1] = False
                    self.last_eat = (g[0], self.eaten)
                    self.eaten += 1
                    self.freeze = 60
                    break
            if self.pac_x > 250 and self.end_t is None:
                self.end_t = self.t
        if self.end_t and self.t - self.end_t > 60:
            self.done = True

    def _blit(self, surf, img, x, y):
        surf.blit(img, (round(x) - img.get_width() // 2, round(y) - img.get_height() // 2))

    def draw(self, surf):
        t, s = self.t, self.s
        surf.fill(BLACK)
        self.app.draw_scores(surf, [0], None, False)
        font.draw_text(surf, "CHARACTER / NICKNAME", 7, 5, WHITE)
        for i in range(4):
            start = 60 + i * GHOST_STEP
            row = 7 + 3 * i
            if t >= start:
                self._blit(surf, s.ghost[i][RIGHT][0], 4 * 8 + 4, row * 8 + 4)
            if t >= start + 40:
                font.draw_text(surf, "-" + GHOST_NICKNAMES[i], 7, row, GHOST_COLORS[i])
            if t >= start + 70:
                font.draw_text(surf, '"' + GHOST_NAMES[i] + '"', 18, row, GHOST_COLORS[i])

        blink = (t // 10) % 2 == 0
        if t >= 60 + 4 * GHOST_STEP:
            surf.fill(PEACH, (10 * 8 + 3, 25 * 8 + 3, 2, 2))
            font.draw_text(surf, "10 PTS", 12, 25, WHITE)
            if blink:
                surf.blit(self.app.maze.energizer_img, (10 * 8, 27 * 8))
            font.draw_text(surf, "50 PTS", 12, 27, WHITE)
        if t >= 60 + 4 * GHOST_STEP + 60:
            if not self.energized and blink:
                surf.blit(self.app.maze.energizer_img, (ENERGIZER_X - 4, CHASE_Y - 4))

        if t >= CHASE_START:
            anim = (0, 1, 2, 1)[(t // 2) % 4]
            if not self.last_eat:
                self._blit(surf, s.pac[self.pac_dir][anim], self.pac_x, CHASE_Y)
            feet = (t // 8) % 2
            for i, (x, alive) in enumerate(self.ghosts):
                if not alive:
                    continue
                if self.energized:
                    flash = False
                    img = s.fright[feet][flash]
                else:
                    img = s.ghost[i][LEFT][feet]
                self._blit(surf, img, x, CHASE_Y)
            if self.last_eat:
                x, n = self.last_eat
                self._blit(surf, s.ghost_points[n], x, CHASE_Y)

        if (t // 30) % 2 == 0:
            font.draw_text(surf, "PRESS ENTER", 8, 33, ORANGE)
        self.app.draw_credits(surf)


def draw_start_screen(app, surf):
    """Shown once a coin has been inserted."""
    surf.fill(BLACK)
    app.draw_scores(surf, [0], None, False)
    font.draw_text(surf, "PUSH START BUTTON", 6, 14, ORANGE)
    if app.credits >= 2:
        font.draw_text(surf, "1 OR 2 PLAYERS", 7, 18, CYAN)
    else:
        font.draw_text(surf, "1 PLAYER ONLY", 8, 18, CYAN)
    font.draw_text(surf, "BONUS PAC-MAN FOR 10000 PTS", 1, 22, PEACH)
    font.draw_text(surf, "1 OR ENTER - ONE PLAYER", 2, 30, WHITE)
    font.draw_text(surf, "2 - TWO PLAYERS", 2, 31, WHITE)
    app.draw_credits(surf)

