"""Pac-Man and ghost movement, including the arcade targeting rules."""

import math

from .constants import (DIRS, DOOR_X, DOOR_Y, DOWN, GHOST_HOME_X, HOUSE_BOTTOM,
                        HOUSE_TOP, HOUSE_Y, LEFT, PAC_START, RED_ZONE, RIGHT,
                        SCATTER_TARGETS, TILE, UP, WRAP_WIDTH, opposite)


def approach(value, target, step):
    if value < target:
        return min(value + step, target)
    if value > target:
        return max(value - step, target)
    return value


def wrap_x(x):
    """Tunnel wrap-around."""
    if x < -TILE:
        return x + WRAP_WIDTH
    if x >= WRAP_WIDTH - TILE:
        return x - WRAP_WIDTH
    return x


def tile_of(x, y):
    return int(x // TILE), int(y // TILE)


class Pacman:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x, self.y = PAC_START
        self.dir = LEFT
        self.want = LEFT
        self.anim = 0
        self.stall = 0          # frames to wait after eating a dot
        self.moving = False

    def tile(self):
        return tile_of(self.x, self.y)

    def update(self, maze, speed):
        if self.stall:
            self.stall -= 1
            return
        tx, ty = self.tile()
        cx, cy = tx * TILE + 4, ty * TILE + 4
        want = self.want
        if want and want != self.dir:
            if want == opposite(self.dir) or not maze.blocked(tx + want[0], ty + want[1]):
                self.dir = want
        dx, dy = self.dir
        ox, oy = self.x, self.y
        # Moving along one axis while being pulled to the lane centre on the
        # other gives the arcade's "cornering" (pre-turn / post-turn) speed-up.
        if dx:
            self.y = approach(self.y, cy, speed)
            if maze.blocked(tx + dx, ty):
                self.x = approach(self.x, cx, speed)
            else:
                self.x += dx * speed
        else:
            self.x = approach(self.x, cx, speed)
            if maze.blocked(tx, ty + dy):
                self.y = approach(self.y, cy, speed)
            else:
                self.y += dy * speed
        self.x = wrap_x(self.x)
        self.moving = self.x != ox or self.y != oy
        if self.moving:
            self.anim += 1

    def frame_index(self):
        return (0, 1, 2, 1)[(self.anim // 2) % 4]


class Ghost:
    """A ghost.  ``state`` is one of:

    house     waiting inside the ghost house, bobbing up and down
    leaving   moving out through the door
    active    roaming the maze (possibly frightened)
    eyes      eaten, eyes heading back to the house
    entering  eyes dropping down into the house to be revived
    """

    def __init__(self, idx):
        self.idx = idx
        self.scatter_target = SCATTER_TARGETS[idx]
        self.home_x = GHOST_HOME_X[idx]
        self.reset()

    def reset(self):
        if self.idx == 0:
            self.x, self.y = DOOR_X, DOOR_Y
            self.state = "active"
            self.dir = LEFT
        else:
            self.x, self.y = self.home_x, HOUSE_Y
            self.state = "house"
            self.dir = DOWN if self.idx == 1 else UP
        self.frightened = False
        self.decided = None

    def tile(self):
        return tile_of(self.x, self.y)

    def reverse(self):
        if self.state == "active":
            self.dir = opposite(self.dir)

    # ------------------------------------------------------------ movement
    def update(self, game, speed):
        state = self.state
        if state == "house":
            self.y += self.dir[1] * speed
            if self.y <= HOUSE_TOP:
                self.y, self.dir = HOUSE_TOP, DOWN
            elif self.y >= HOUSE_BOTTOM:
                self.y, self.dir = HOUSE_BOTTOM, UP
        elif state == "leaving":
            if self.x != DOOR_X:
                if self.y != HOUSE_Y:
                    self.dir = UP if self.y > HOUSE_Y else DOWN
                    self.y = approach(self.y, HOUSE_Y, speed)
                else:
                    self.dir = LEFT if self.x > DOOR_X else RIGHT
                    self.x = approach(self.x, DOOR_X, speed)
            else:
                self.dir = UP
                self.y = approach(self.y, DOOR_Y, speed)
                if self.y == DOOR_Y:
                    self.state = "active"
                    self.dir = LEFT
                    self.decided = None
        elif state == "entering":
            if self.y != HOUSE_Y:
                self.dir = DOWN
                self.y = approach(self.y, HOUSE_Y, speed)
            elif self.x != self.home_x:
                self.dir = LEFT if self.x > self.home_x else RIGHT
                self.x = approach(self.x, self.home_x, speed)
            else:
                self.state = "leaving"
                self.frightened = False
        else:
            self._move_in_maze(game, speed)

    def _move_in_maze(self, game, step):
        for _ in range(8):
            if step <= 1e-7:
                return
            dx, dy = self.dir
            if self.state == "eyes" and dy == 0 and abs(self.y - DOOR_Y) < 1e-6:
                gap = (DOOR_X - self.x) * dx
                if 0 <= gap <= step:
                    self.x = DOOR_X
                    self.state = "entering"
                    return
            horizontal = dx != 0
            pos = self.x if horizontal else self.y
            sign = dx if horizontal else dy
            k = (pos - 4) / TILE
            centre = (math.ceil(k - 1e-9) if sign > 0 else math.floor(k + 1e-9)) * TILE + 4
            dist = abs(centre - pos)
            if dist < 1e-7 and self.decided == self._tile_with(centre, horizontal):
                centre += sign * TILE
                dist = TILE
            if step < dist:
                self._set_axis(pos + sign * step, horizontal)
                return
            step -= dist
            self._set_axis(centre, horizontal)
            here = self.tile()
            self.decided = here
            self._choose_direction(game, here)

    def _tile_with(self, value, horizontal):
        if horizontal:
            return tile_of(value, self.y)
        return tile_of(self.x, value)

    def _set_axis(self, value, horizontal):
        if horizontal:
            self.x = wrap_x(value)
        else:
            self.y = value

    def _choose_direction(self, game, tile):
        tx, ty = tile
        roaming = self.state == "active" and not self.frightened
        options = []
        for d in DIRS:
            if d == opposite(self.dir):
                continue
            if d == UP and roaming and tile in RED_ZONE:
                continue
            if game.maze.blocked(tx + d[0], ty + d[1]):
                continue
            options.append(d)
        if not options:
            self.dir = opposite(self.dir)
            return
        if self.frightened and self.state == "active":
            start = game.rng.randrange(4)
            for i in range(4):
                d = DIRS[(start + i) % 4]
                if d in options:
                    self.dir = d
                    return
        target = self.target(game)
        self.dir = min(options, key=lambda d: ((tx + d[0] - target[0]) ** 2 +
                                               (ty + d[1] - target[1]) ** 2, DIRS.index(d)))

    # ------------------------------------------------------------ targeting
    def target(self, game):
        if self.state == "eyes":
            return (13, 11)
        pac = game.pac
        ptx, pty = pac.tile()
        pdx, pdy = pac.dir
        if self.idx == 0:          # Blinky: straight for Pac-Man (always, as Elroy)
            if game.mode == "scatter" and not game.elroy_level():
                return self.scatter_target
            return ptx, pty
        if game.mode == "scatter":
            return self.scatter_target
        if self.idx == 1:          # Pinky: four tiles ahead (with the "up" overflow bug)
            tx, ty = ptx + 4 * pdx, pty + 4 * pdy
            if pac.dir == UP:
                tx -= 4
            return tx, ty
        if self.idx == 2:          # Inky: Blinky's vector through two tiles ahead, doubled
            px, py = ptx + 2 * pdx, pty + 2 * pdy
            if pac.dir == UP:
                px -= 2
            bx, by = game.ghosts[0].tile()
            return 2 * px - bx, 2 * py - by
        gx, gy = self.tile()       # Clyde: chase until within eight tiles
        if (gx - ptx) ** 2 + (gy - pty) ** 2 > 64:
            return ptx, pty
        return self.scatter_target
