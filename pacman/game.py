"""A game in progress: levels, players, scoring and the arcade rules."""

import random
from collections import deque

from . import font
from .actors import Ghost, Pacman
from .constants import (CYAN, DIRS, EXTRA_LIFE_SCORE, FRUIT_POINTS, FRUIT_ROW, FRUIT_X,
                        FRUIT_Y, GHOST_POINTS, INTERMISSION_AFTER, KILL_SCREEN_LEVEL,
                        MAZE_TOP, RED, TOTAL_DOTS, TUNNEL_ROW, YELLOW, BLACK, EYES_SPEED,
                        HOUSE_SPEED, COLS, dot_timeout, elroy_params, fright_params,
                        fruit_for_level, ghost_speeds, mode_schedule, opposite, pac_speeds,
                        release_limits)
from .cutscenes import Cutscene
from .sound import SilentSound

START_MUSIC_FRAMES = 260
READY_FRAMES = 120
PLAYER_INTRO_FRAMES = 120
DEATH_FREEZE = 60
DEATH_FRAME_TIME = 8
DEATH_TOTAL = DEATH_FREEZE + 11 * DEATH_FRAME_TIME + 16 + 50
FLASH_START = 60
FLASH_FRAMES = 12
FLASH_COUNT = 8
LEVEL_DONE_TOTAL = FLASH_START + FLASH_FRAMES * FLASH_COUNT + 30
GAME_OVER_FRAMES = 180


class PlayerState:
    def __init__(self, num):
        self.num = num
        self.score = 0
        self.lives = 3
        self.level = 1
        self.pellets = set()
        self.dots_eaten = 0
        self.extra_awarded = False
        self.died_this_level = False
        self.ghost_counters = [0, 0, 0, 0]


class Game:
    def __init__(self, app, num_players=1, demo=False):
        self.app = app
        self.maze = app.maze
        self.sprites = app.sprites
        self.demo = demo
        self.sound = SilentSound() if demo else app.sound
        self.players = [PlayerState(i) for i in range(num_players)]
        if demo:
            self.players[0].lives = 1
        self.cur = 0
        self.pac = Pacman()
        self.ghosts = [Ghost(i) for i in range(4)]
        self.rng = random.Random()
        self.finished = False
        self.frame = 0
        self.show_player = False
        self.cutscene = None
        self._ai_tile = None
        self._ai_dir = None
        for player in self.players:
            self._setup_level(player)
        self._reset_actors()
        if demo:
            self._set_phase("play")
        else:
            self._set_phase("start")
            self.sound.stop_all()
            self.sound.play("start")

    # ------------------------------------------------------------ helpers
    @property
    def p(self):
        return self.players[self.cur]

    @property
    def mode(self):
        if self.mode_idx < len(self.schedule) and self.mode_idx % 2 == 0:
            return "scatter"
        return "chase"

    def _set_phase(self, name):
        self.phase = name
        self.phase_t = 0
        if name != "play":
            self.sound.stop_loop()

    def _setup_level(self, player):
        player.pellets = self.maze.fresh_pellets(player.level)
        player.dots_eaten = 0
        player.died_this_level = False
        player.ghost_counters = [0, 0, 0, 0]

    def _reset_actors(self):
        self.pac.reset()
        for g in self.ghosts:
            g.reset()
        self.schedule = mode_schedule(self.p.level)
        self.mode_idx = 0
        self.mode_timer = 0
        self.fright_timer = 0
        self.fright_flashes = 0
        self.ghost_combo = 0
        self.dot_timer = 0
        self.global_active = self.p.died_this_level
        self.global_count = 0
        self.elroy_suspended = self.p.died_this_level
        self.fruit_timer = 0
        self.fruit_score_timer = 0
        self.eaten = None

    def _add_score(self, points):
        if self.demo:
            return
        p = self.p
        p.score += points
        if not p.extra_awarded and p.score >= EXTRA_LIFE_SCORE:
            p.extra_awarded = True
            p.lives += 1
            self.sound.play("extra_life")
        if p.score > self.app.highscore:
            self.app.highscore = p.score

    def elroy_level(self):
        if self.elroy_suspended or self.ghosts[0].frightened:
            return 0
        d1, _, d2, _ = elroy_params(self.p.level)
        remaining = TOTAL_DOTS - self.p.dots_eaten
        if remaining <= d2:
            return 2
        if remaining <= d1:
            return 1
        return 0

    # ------------------------------------------------------------ update
    def update(self, want):
        self.frame += 1
        self.phase_t += 1
        getattr(self, "_phase_" + self.phase)(want)

    def _phase_start(self, want):
        if self.phase_t >= START_MUSIC_FRAMES:
            self._set_phase("play")

    def _phase_ready(self, want):
        total = READY_FRAMES + (PLAYER_INTRO_FRAMES if self.show_player else 0)
        if self.phase_t >= total:
            self._set_phase("play")

    def _phase_play(self, want):
        p = self.p
        if self.demo:
            want = self._ai_want()
        if want:
            self.pac.want = want

        if self.fright_timer > 0:
            self.fright_timer -= 1
            if self.fright_timer == 0:
                for g in self.ghosts:
                    g.frightened = False
        elif self.mode_idx < len(self.schedule):
            self.mode_timer += 1
            if self.mode_timer >= self.schedule[self.mode_idx]:
                self.mode_idx += 1
                self.mode_timer = 0
                for g in self.ghosts:
                    g.reverse()

        normal, energized = pac_speeds(p.level)
        self.pac.update(self.maze, energized if self.fright_timer else normal)
        self._eat(self.pac.tile())
        if self.phase != "play" or self._collide():
            return

        self._update_house()
        for g in self.ghosts:
            g.update(self, self._ghost_speed(g))
        if self._collide():
            return

        if self.fruit_timer > 0:
            self.fruit_timer -= 1
            if self.pac.tile()[1] == FRUIT_ROW and abs(self.pac.x - FRUIT_X) < 6:
                self.fruit_timer = 0
                self.fruit_score_timer = 120
                self._add_score(FRUIT_POINTS[fruit_for_level(p.level)])
                self.sound.play("eat_fruit")
        if self.fruit_score_timer > 0:
            self.fruit_score_timer -= 1
        if self.elroy_suspended and self.ghosts[3].state != "house":
            self.elroy_suspended = False
        self._update_loop_sound()

    def _phase_eat_ghost(self, want):
        if want:
            self.pac.want = want
        if self.phase_t >= 60:
            self.eaten = None
            self._set_phase("play")

    def _phase_dying(self, want):
        if self.phase_t == DEATH_FREEZE:
            self.sound.play("death")
        if self.phase_t < DEATH_TOTAL:
            return
        p = self.p
        p.lives -= 1
        p.died_this_level = True
        if self.demo:
            self.finished = True
        elif p.lives <= 0:
            self._set_phase("game_over")
            self.app.save_highscore()
        else:
            other = (self.cur + 1) % len(self.players)
            self.show_player = other != self.cur and self.players[other].lives > 0
            if self.show_player:
                self.cur = other
            self._reset_actors()
            self._set_phase("ready")

    def _phase_game_over(self, want):
        if self.phase_t < GAME_OVER_FRAMES:
            return
        alive = [i for i, pl in enumerate(self.players) if pl.lives > 0]
        if not alive:
            self.finished = True
            return
        self.cur = alive[0]
        self.show_player = True
        self._reset_actors()
        self._set_phase("ready")

    def _phase_level_done(self, want):
        if self.phase_t < LEVEL_DONE_TOTAL:
            return
        p = self.p
        act = INTERMISSION_AFTER.get(p.level)
        p.level = min(p.level + 1, KILL_SCREEN_LEVEL)
        self._setup_level(p)
        self._reset_actors()
        self.show_player = False
        if act and not self.demo:
            self.cutscene = Cutscene(self.sprites, act)
            self.sound.play("intermission")
            self._set_phase("intermission")
        elif self.demo:
            self.finished = True
        else:
            self._set_phase("ready")

    def _phase_intermission(self, want):
        self.cutscene.update()
        if self.cutscene.done:
            self.cutscene = None
            self.sound.stop_all()
            self._set_phase("ready")

    # ------------------------------------------------------------ rules
    def _eat(self, tile):
        p = self.p
        if tile not in p.pellets:
            return
        p.pellets.discard(tile)
        energizer = tile in self.maze.energizers
        self._add_score(50 if energizer else 10)
        self.pac.stall = 3 if energizer else 1
        p.dots_eaten += 1
        self.dot_timer = 0
        self._count_dot()
        self.sound.chomp()
        if energizer:
            self._energize()
        if p.dots_eaten in (70, 170):
            self.fruit_timer = self.rng.randint(560, 600)
            self.fruit_score_timer = 0
        if p.dots_eaten >= TOTAL_DOTS:
            self.sound.stop_all()
            self._set_phase("level_done")

    def _energize(self):
        frames, flashes = fright_params(self.p.level)
        for g in self.ghosts:
            g.reverse()
        self.ghost_combo = 0
        if frames:
            self.fright_timer = frames
            self.fright_flashes = flashes
            for g in self.ghosts:
                if g.state not in ("eyes", "entering"):
                    g.frightened = True

    def _collide(self):
        pt = self.pac.tile()
        for g in self.ghosts:
            if g.state in ("eyes", "entering") or g.tile() != pt:
                continue
            if g.frightened:
                self.ghost_combo = min(self.ghost_combo + 1, 4)
                points = GHOST_POINTS[self.ghost_combo - 1]
                self._add_score(points)
                g.frightened = False
                g.state = "eyes"
                self.eaten = (g, self.ghost_combo - 1)
                self._set_phase("eat_ghost")
                self.sound.play("eat_ghost")
            else:
                self.sound.stop_all()
                self._set_phase("dying")
            return True
        return False

    def _count_dot(self):
        g = self.ghosts
        if self.global_active:
            self.global_count += 1
            if self.global_count == 7 and g[1].state == "house":
                g[1].state = "leaving"
            elif self.global_count == 17 and g[2].state == "house":
                g[2].state = "leaving"
            elif self.global_count == 32 and g[3].state == "house":
                self.global_active = False
                self.global_count = 0
        else:
            for ghost in g[1:]:
                if ghost.state == "house":
                    self.p.ghost_counters[ghost.idx] += 1
                    break

    def _update_house(self):
        waiting = [g for g in self.ghosts[1:] if g.state == "house"]
        if not waiting:
            self.dot_timer = 0
            return
        preferred = waiting[0]
        limit = release_limits(self.p.level)[preferred.idx]
        if not self.global_active and self.p.ghost_counters[preferred.idx] >= limit:
            preferred.state = "leaving"
            return
        self.dot_timer += 1
        if self.dot_timer >= dot_timeout(self.p.level):
            self.dot_timer = 0
            preferred.state = "leaving"

    def _ghost_speed(self, g):
        if g.state in ("eyes", "entering"):
            return EYES_SPEED
        if g.state in ("house", "leaving"):
            return HOUSE_SPEED
        normal, frightened, tunnel = ghost_speeds(self.p.level)
        tx, ty = g.tile()
        if ty == TUNNEL_ROW and (tx <= 5 or tx >= 22):
            return tunnel
        if g.frightened:
            return frightened
        if g.idx == 0:
            level = self.elroy_level()
            if level:
                _, s1, _, s2 = elroy_params(self.p.level)
                return s1 if level == 1 else s2
        return normal

    def _update_loop_sound(self):
        if any(g.state in ("eyes", "entering") for g in self.ghosts):
            self.sound.loop("eyes")
        elif self.fright_timer:
            self.sound.loop("fright")
        else:
            remaining = TOTAL_DOTS - self.p.dots_eaten
            level = sum(remaining <= n for n in (150, 100, 60, 30))
            self.sound.loop("siren%d" % level)

    # ------------------------------------------------------------ demo AI
    def _ai_want(self):
        pac = self.pac
        here = pac.tile()
        if here == self._ai_tile and self._ai_dir:
            return self._ai_dir
        self._ai_tile = here
        danger = set()
        prey = set()
        for g in self.ghosts:
            if g.state != "active":
                continue
            gx, gy = g.tile()
            if g.frightened:
                prey.add((gx, gy))
                continue
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    if abs(dx) + abs(dy) <= 3:
                        danger.add((gx + dx, gy + dy))
        targets = self.p.pellets | prey
        best, best_score = None, None
        for d in DIRS:
            n = (here[0] + d[0], here[1] + d[1])
            if self.maze.blocked(*n):
                continue
            score = self._bfs(n, here, targets, danger)
            if n in danger:
                score += 500
            if d == opposite(pac.dir):
                score += 3
            if best_score is None or score < best_score:
                best, best_score = d, score
        self._ai_dir = best
        return best

    def _bfs(self, start, came_from, targets, danger):
        def norm(t):
            c, r = t
            if r == TUNNEL_ROW:
                c %= COLS
            return c, r

        start = norm(start)
        seen = {start, norm(came_from)}
        queue = deque([(start, 0)])
        while queue:
            (c, r), dist = queue.popleft()
            if (c, r) in targets:
                return dist
            if dist > 60:
                break
            for dx, dy in DIRS:
                n = norm((c + dx, r + dy))
                if n in seen or n in danger or self.maze.blocked(*n):
                    continue
                seen.add(n)
                queue.append((n, dist + 1))
        return 100

    # ------------------------------------------------------------ drawing
    def draw(self, surf):
        ph, t, p = self.phase, self.phase_t, self.p
        if ph == "intermission":
            surf.fill(BLACK)
            self.cutscene.draw(surf)
            self.draw_hud(surf)
            return
        surf.fill(BLACK)
        flashing = ph == "level_done" and t >= FLASH_START
        white = flashing and ((t - FLASH_START) // FLASH_FRAMES) % 2 == 0 \
            and t < FLASH_START + FLASH_FRAMES * FLASH_COUNT
        surf.blit(self.maze.white if white else self.maze.blue, (0, MAZE_TOP))
        blink = ph in ("play", "eat_ghost") and (self.frame // 10) % 2 == 1
        self.maze.draw_pellets(surf, p.pellets, MAZE_TOP, show_energizers=not blink)
        if p.level == KILL_SCREEN_LEVEL:
            self.maze.draw_kill_screen(surf)

        intro = (ph == "start" and t < PLAYER_INTRO_FRAMES) or \
                (ph == "ready" and self.show_player and t < PLAYER_INTRO_FRAMES)
        actors = not intro and ph != "game_over"
        ghosts_visible = actors and not (ph == "dying" and t >= DEATH_FREEZE) and \
            not (ph == "level_done" and t >= FLASH_START)

        if self.fruit_timer and ph in ("play", "eat_ghost") or \
                (self.fruit_timer and ph == "dying" and t < DEATH_FREEZE):
            self._blit_centered(surf, self.sprites.fruit[fruit_for_level(p.level)], FRUIT_X, FRUIT_Y)
        if self.fruit_score_timer:
            self._blit_centered(surf, self.sprites.fruit_points[fruit_for_level(p.level)], FRUIT_X, FRUIT_Y)

        if actors and ph != "eat_ghost":
            self._draw_pac(surf)
        if ghosts_visible:
            eaten = self.eaten[0] if self.eaten else None
            for g in self.ghosts:
                if g is not eaten:
                    self._blit_centered(surf, self._ghost_sprite(g), g.x, g.y)
        if self.eaten:
            g, n = self.eaten
            self._blit_centered(surf, self.sprites.ghost_points[n], g.x, g.y)

        if ph in ("start", "ready"):
            font.draw_text(surf, "READY!", 11, 20, YELLOW)
        if intro:
            font.draw_text(surf, "PLAYER ONE" if self.cur == 0 else "PLAYER TWO", 9, 14, CYAN)
        if ph == "game_over" or self.demo:
            font.draw_text(surf, "GAME  OVER", 9, 20, RED)
            if ph == "game_over" and len(self.players) > 1:
                font.draw_text(surf, "PLAYER ONE" if self.cur == 0 else "PLAYER TWO", 9, 14, CYAN)
        self.draw_hud(surf)

    def _blit_centered(self, surf, img, x, y):
        surf.blit(img, (round(x) - img.get_width() // 2, round(y) + MAZE_TOP - img.get_height() // 2))

    def _draw_pac(self, surf):
        s = self.sprites
        if self.phase == "dying" and self.phase_t >= DEATH_FREEZE:
            k = (self.phase_t - DEATH_FREEZE) // DEATH_FRAME_TIME
            if k < len(s.pac_death):
                img = s.pac_death[k]
            elif k < len(s.pac_death) + 2:
                img = s.pac_pop
            else:
                return
        else:
            img = s.pac[self.pac.dir][self.pac.frame_index()]
        self._blit_centered(surf, img, self.pac.x, self.pac.y)

    def _ghost_sprite(self, g):
        s = self.sprites
        frame = (self.frame // 8) % 2
        if g.state in ("eyes", "entering"):
            return s.eyes[g.dir]
        if g.frightened:
            flash = self.fright_timer <= self.fright_flashes * 28 and (self.fright_timer // 14) % 2 == 1
            return s.fright[frame][flash]
        return s.ghost[g.idx][g.dir][frame]

    def draw_hud(self, surf):
        p = self.p
        blink = self.phase == "play" and not self.demo
        self.app.draw_scores(surf, [pl.score for pl in self.players], self.cur, blink)
        if self.demo:
            return
        intro = self.phase == "start" and self.phase_t < PLAYER_INTRO_FRAMES
        spare = p.lives if intro else p.lives - 1
        if self.phase == "game_over":
            spare = 0
        for i in range(max(0, min(spare, 5))):
            surf.blit(self.sprites.life, (16 + i * 16, 272))
        lo = max(1, p.level - 6)
        for i, level in enumerate(range(lo, p.level + 1)):
            surf.blit(self.sprites.fruit[fruit_for_level(level)], (192 - i * 16, 272))
