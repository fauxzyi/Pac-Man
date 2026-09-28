"""The three coffee-break intermissions shown between levels."""

from .constants import LEFT, RIGHT, DOWN, RED

ROW_Y = 164          # screen y of the characters' centres


class Cutscene:
    def __init__(self, sprites, act):
        self.s = sprites
        self.act = act
        self.t = 0
        self.done = False
        self.stage = 0
        self.stage_t = 0
        self.pac_x = 250.0
        self.ghost_x = 290.0
        self.tear_t = 0

    def _next(self):
        self.stage += 1
        self.stage_t = 0

    def update(self):
        self.t += 1
        self.stage_t += 1
        getattr(self, "_act%d" % self.act)()

    # Act I: Blinky chases Pac-Man off screen, then a giant Pac-Man chases him back
    def _act1(self):
        if self.stage == 0:
            self.pac_x -= 1.25
            self.ghost_x -= 1.32
            if self.ghost_x < -24:
                self._next()
        elif self.stage == 1:
            if self.stage_t > 60:
                self.ghost_x, self.pac_x = -16.0, -80.0
                self._next()
        else:
            self.ghost_x += 0.8
            self.pac_x += 0.85
            if self.pac_x > 260:
                self.done = True

    # Act II: Blinky snags his cloak on a nail and it tears
    NAIL_X = 128

    def _act2(self):
        if self.stage == 0:
            self.pac_x -= 1.25
            self.ghost_x -= 1.32
            if self.ghost_x <= self.NAIL_X - 4:
                self._next()
        elif self.stage == 1:          # the cloak stretches
            self.pac_x -= 1.25
            self.ghost_x -= 0.12
            if self.stage_t > 90:
                self._next()
        elif self.stage == 2:          # torn: Blinky looks back at the damage
            self.pac_x -= 1.25
            if self.stage_t > 90:
                self._next()
        elif self.stage_t > 150:       # ...and then at the player
            self.done = True

    # Act III: patched-up Blinky gives chase, then retreats dragging his cloak
    def _act3(self):
        if self.stage == 0:
            self.pac_x -= 1.25
            self.ghost_x -= 1.32
            if self.ghost_x < -24:
                self._next()
        elif self.stage == 1:
            if self.stage_t > 60:
                self.ghost_x = -30.0
                self._next()
        else:
            self.ghost_x += 0.7
            if self.ghost_x > 270:
                self.done = True

    # ------------------------------------------------------------ drawing
    def _blit(self, surf, img, x, y=ROW_Y):
        surf.blit(img, (round(x) - img.get_width() // 2, round(y) - img.get_height() // 2))

    def draw(self, surf):
        s = self.s
        anim = (self.t // 2) % 4
        pac_frame = (0, 1, 2, 1)[anim]
        feet = (self.t // 8) % 2
        if self.act == 1:
            if self.stage == 0:
                self._blit(surf, s.pac[LEFT][pac_frame], self.pac_x)
                self._blit(surf, s.ghost[0][LEFT][feet], self.ghost_x)
            elif self.stage == 2:
                self._blit(surf, s.fright[feet][False], self.ghost_x)
                self._blit(surf, s.pac_big[RIGHT][pac_frame], self.pac_x, ROW_Y - 8)
        elif self.act == 2:
            self._blit(surf, s.nail, self.NAIL_X, ROW_Y + 5)
            self._blit(surf, s.pac[LEFT][pac_frame], self.pac_x)
            if self.stage == 0:
                self._blit(surf, s.ghost[0][LEFT][feet], self.ghost_x)
            elif self.stage == 1:
                stretch = int(self.stage_t / 90 * 10)
                gx = round(self.ghost_x)
                surf.fill(RED, (gx + 5, ROW_Y + 3, max(1, self.NAIL_X - gx - 4), 3))
                surf.fill(RED, (gx + 5, ROW_Y + 1, max(1, stretch), 2))
                self._blit(surf, s.ghost[0][LEFT][feet], self.ghost_x)
            else:
                look = RIGHT if self.stage == 2 else DOWN
                self._blit(surf, s.torn[look], self.ghost_x)
                surf.fill(RED, (self.NAIL_X - 1, ROW_Y + 3, 4, 3))
        else:
            if self.stage == 0:
                self._blit(surf, s.pac[LEFT][pac_frame], self.pac_x)
                self._blit(surf, s.patched[feet], self.ghost_x)
            elif self.stage == 2:
                self._blit(surf, s.naked[feet], self.ghost_x)
                self._blit(surf, s.cloak, self.ghost_x - 14, ROW_Y + 4)
