"""Shared constants, colours and the per-level tables of the arcade original.

The level tables (speeds, frightened times, Elroy thresholds, scatter/chase
timings, ghost house release limits) follow "The Pac-Man Dossier".
"""

TILE = 8
COLS = 28
ROWS = 31
SCREEN_W = 224          # native arcade resolution (28 x 36 tiles)
SCREEN_H = 288
MAZE_TOP = 3 * TILE     # three rows of score display above the maze
FPS = 60
FULL_SPEED = 75.75757625 / 60.0   # pixels per frame at "100%" speed

UP = (0, -1)
LEFT = (-1, 0)
DOWN = (0, 1)
RIGHT = (1, 0)
DIRS = (UP, LEFT, DOWN, RIGHT)      # also the arcade's tie-break order


def opposite(d):
    return (-d[0], -d[1])


# Arcade palette
BLACK = (0, 0, 0)
WALL_BLUE = (33, 33, 255)
WHITE = (222, 222, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
PINK = (255, 184, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 184, 82)
PEACH = (255, 184, 151)
BLUE = (33, 33, 255)
BROWN = (222, 151, 81)
GREEN = (0, 222, 0)

GHOST_COLORS = (RED, PINK, CYAN, ORANGE)
GHOST_NAMES = ("BLINKY", "PINKY", "INKY", "CLYDE")
GHOST_NICKNAMES = ("SHADOW", "SPEEDY", "BASHFUL", "POKEY")

# Positions in maze pixel coordinates (maze row 0 is screen row 3)
PAC_START = (112.0, 188.0)
DOOR_X, DOOR_Y = 112.0, 92.0          # tile just above the ghost house door
HOUSE_Y = 116.0                        # vertical centre of the ghost house
HOUSE_TOP, HOUSE_BOTTOM = 112.0, 120.0
GHOST_HOME_X = (112.0, 112.0, 96.0, 128.0)
SCATTER_TARGETS = ((25, -3), (2, -3), (27, 32), (0, 32))
FRUIT_X, FRUIT_Y = 112.0, 140.0
FRUIT_ROW = 17
TUNNEL_ROW = 14
WRAP_WIDTH = 240
# Tiles where ghosts may not choose to turn upwards (scatter/chase only)
RED_ZONE = frozenset({(12, 11), (15, 11), (12, 23), (15, 23)})

TOTAL_DOTS = 244
EXTRA_LIFE_SCORE = 10000
EYES_SPEED = 2.0
HOUSE_SPEED = FULL_SPEED * 0.5

GHOST_POINTS = (200, 400, 800, 1600)
FRUIT_POINTS = (100, 300, 500, 700, 1000, 2000, 3000, 5000)
FRUIT_NAMES = ("CHERRY", "STRAWBERRY", "ORANGE", "APPLE", "MELON",
               "GALAXIAN", "BELL", "KEY")
INTERMISSION_AFTER = {2: 1, 5: 2, 9: 3, 13: 3, 17: 3}
KILL_SCREEN_LEVEL = 256

_PAC = ((0.80, 0.90), (0.90, 0.95), (1.00, 1.00), (0.90, 0.90))
_GHOST = ((0.75, 0.50, 0.40), (0.85, 0.55, 0.45),
          (0.95, 0.60, 0.50), (0.95, 0.60, 0.50))
_ELROY = ((0.80, 0.85), (0.90, 0.95), (1.00, 1.05), (1.00, 1.05))
_ELROY_DOTS = (20, 30, 40, 40, 40, 50, 50, 50, 60, 60, 60,
               80, 80, 80, 100, 100, 100, 100, 120)
_FRIGHT = ((6, 5), (5, 5), (4, 5), (3, 5), (2, 5), (5, 5), (2, 5), (2, 5),
           (1, 3), (5, 5), (2, 5), (1, 3), (1, 3), (3, 5), (1, 3), (1, 3),
           (0, 0), (1, 3))
_FRUIT = (0, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6)


def _band(level):
    if level == 1:
        return 0
    if level <= 4:
        return 1
    if level <= 20:
        return 2
    return 3


def pac_speeds(level):
    """(normal, energized) Pac-Man speed in pixels per frame."""
    normal, fright = _PAC[_band(level)]
    return normal * FULL_SPEED, fright * FULL_SPEED


def ghost_speeds(level):
    """(normal, frightened, tunnel) ghost speed in pixels per frame."""
    return tuple(v * FULL_SPEED for v in _GHOST[_band(level)])


def elroy_params(level):
    """(dots left for Elroy 1, speed 1, dots left for Elroy 2, speed 2)."""
    dots = _ELROY_DOTS[min(level, len(_ELROY_DOTS)) - 1]
    s1, s2 = _ELROY[_band(level)]
    return dots, s1 * FULL_SPEED, dots // 2, s2 * FULL_SPEED


def fright_params(level):
    """(frightened duration in frames, number of flashes)."""
    if level > len(_FRIGHT):
        return 0, 0
    seconds, flashes = _FRIGHT[level - 1]
    return seconds * FPS, flashes


def fruit_for_level(level):
    return _FRUIT[level - 1] if level <= len(_FRUIT) else 7


def mode_schedule(level):
    """Alternating scatter/chase durations in frames; chase is permanent after."""
    if level == 1:
        secs = (7, 20, 7, 20, 5, 20, 5)
    elif level <= 4:
        secs = (7, 20, 7, 20, 5, 1033, 1 / 60)
    else:
        secs = (5, 20, 5, 20, 5, 1037, 1 / 60)
    return [max(1, round(s * FPS)) for s in secs]


def release_limits(level):
    """Personal dot limits for leaving the house, indexed by ghost."""
    if level == 1:
        return (0, 0, 30, 60)
    if level == 2:
        return (0, 0, 0, 50)
    return (0, 0, 0, 0)


def dot_timeout(level):
    """Frames without eating before the next ghost is forced out."""
    return 4 * FPS if level < 5 else 3 * FPS
