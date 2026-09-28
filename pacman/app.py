"""Window, input handling and the top-level attract / game state machine."""

import argparse
import os

import pygame

from . import font
from .attract import Attract, draw_start_screen
from .constants import (DOWN, FPS, LEFT, RIGHT, SCREEN_H, SCREEN_W, UP, WHITE, YELLOW)
from .game import Game
from .maze import Maze
from .sound import SoundManager
from .sprites import Sprites

HIGHSCORE_FILE = os.path.join(os.path.expanduser("~"), ".pygame_pacman_highscore")

DIR_KEYS = {
    pygame.K_UP: UP, pygame.K_w: UP,
    pygame.K_DOWN: DOWN, pygame.K_s: DOWN,
    pygame.K_LEFT: LEFT, pygame.K_a: LEFT,
    pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT,
}
START1_KEYS = {pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_1, pygame.K_KP1}
START2_KEYS = {pygame.K_2, pygame.K_KP2}
COIN_KEYS = {pygame.K_c, pygame.K_5, pygame.K_KP5}


class App:
    def __init__(self, scale=None, muted=False):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("PAC-MAN")
        self.canvas = pygame.Surface((SCREEN_W, SCREEN_H))
        self._open_window(scale)
        self.clock = pygame.time.Clock()
        self.sprites = Sprites()
        self.maze = Maze()
        self.sound = SoundManager(muted)
        self.highscore = self._load_highscore()
        self.credits = 0
        self.frame = 0
        self.paused = False
        self.held = []
        self.want = None
        self.game = None
        self.attract = Attract(self)
        self.state = "attract"

    # ------------------------------------------------------------ window
    def _open_window(self, scale):
        self.scaled = False
        if scale is None:
            try:
                self.window = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.SCALED)
                self.scaled = True
                return
            except pygame.error:
                scale = 2
        self.window = pygame.display.set_mode((SCREEN_W * scale, SCREEN_H * scale))

    def _present(self):
        if self.scaled:
            self.window.blit(self.canvas, (0, 0))
        else:
            pygame.transform.scale(self.canvas, self.window.get_size(), self.window)
        pygame.display.flip()

    # ------------------------------------------------------------ high score
    def _load_highscore(self):
        try:
            with open(HIGHSCORE_FILE) as f:
                return int(f.read().strip() or 0)
        except (OSError, ValueError):
            return 0

    def save_highscore(self):
        try:
            with open(HIGHSCORE_FILE, "w") as f:
                f.write(str(self.highscore))
        except OSError:
            pass

    # ------------------------------------------------------------ shared HUD
    def draw_scores(self, surf, scores, active, blink):
        hide = blink and (self.frame // 16) % 2 == 1
        if not (hide and active == 0):
            font.draw_text(surf, "1UP", 3, 0, WHITE)
        font.draw_text(surf, "HIGH SCORE", 9, 0, WHITE)
        if len(scores) > 1 and not (hide and active == 1):
            font.draw_text(surf, "2UP", 22, 0, WHITE)
        font.draw_text_right(surf, str(scores[0]) if scores[0] else "00", 6, 1, WHITE)
        if self.highscore:
            font.draw_text_right(surf, str(self.highscore), 16, 1, WHITE)
        if len(scores) > 1:
            font.draw_text_right(surf, str(scores[1]) if scores[1] else "00", 25, 1, WHITE)

    def draw_credits(self, surf):
        font.draw_text(surf, "CREDIT %2d" % min(self.credits, 99), 2, 35, WHITE)

    # ------------------------------------------------------------ flow
    def start_game(self, players):
        self.credits = max(0, self.credits - players)
        self.game = Game(self, players)
        self.state = "game"
        self.paused = False
        self.held.clear()
        self.want = None

    def to_attract(self):
        self.sound.stop_all()
        self.save_highscore()
        self.game = None
        self.paused = False
        self.attract = Attract(self)
        self.state = "attract"

    def on_key(self, key):
        if key in DIR_KEYS:
            if key in self.held:
                self.held.remove(key)
            self.held.append(key)
            self.want = DIR_KEYS[key]
            return True
        if key == pygame.K_ESCAPE:
            if self.state in ("game", "start_screen"):
                self.to_attract()
                return True
            return False
        if key in (pygame.K_F11, pygame.K_f):
            try:
                pygame.display.toggle_fullscreen()
            except pygame.error:
                pass
        elif key == pygame.K_m:
            self.sound.toggle_mute()
        elif key == pygame.K_p and self.state == "game":
            self.paused = not self.paused
            if self.sound.enabled:
                if self.paused:
                    pygame.mixer.pause()
                else:
                    pygame.mixer.unpause()
        elif key in COIN_KEYS and self.state != "game":
            self.credits = min(self.credits + 1, 99)
            self.sound.play("credit")
            self.game = None
            self.state = "start_screen"
        elif key in START1_KEYS and self.state != "game":
            self.start_game(1)
        elif key in START2_KEYS and self.state != "game":
            self.start_game(2)
        return True

    def on_key_up(self, key):
        if key in self.held:
            self.held.remove(key)
            if self.held:
                self.want = DIR_KEYS[self.held[-1]]

    def update(self):
        self.frame += 1
        if self.state == "attract":
            self.attract.update()
            if self.attract.done:
                self.game = Game(self, 1, demo=True)
                self.state = "demo"
        elif self.state == "demo":
            self.game.update(None)
            if self.game.finished:
                self.to_attract()
        elif self.state == "game":
            self.game.update(self.want)
            if self.game.finished:
                self.to_attract()

    def draw(self):
        surf = self.canvas
        if self.state == "attract":
            self.attract.draw(surf)
        elif self.state == "start_screen":
            draw_start_screen(self, surf)
        else:
            self.game.draw(surf)
            if self.state == "demo":
                self.draw_credits(surf)
            if self.paused:
                font.draw_text(surf, "PAUSED", 11, 17, YELLOW)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = self.on_key(event.key)
                elif event.type == pygame.KEYUP:
                    self.on_key_up(event.key)
            if not self.paused:
                self.update()
            self.draw()
            self._present()
            self.clock.tick(FPS)
        self.save_highscore()
        pygame.quit()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Pac-Man, recreated with pygame.")
    parser.add_argument("--scale", type=int, help="fixed integer window scale (default: fit the desktop)")
    parser.add_argument("--mute", action="store_true", help="start with sound muted")
    args = parser.parse_args(argv)
    App(scale=args.scale, muted=args.mute).run()
