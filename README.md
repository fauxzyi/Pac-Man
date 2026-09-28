# Pac-Man

A recreation of the 1980 arcade Pac-Man in Python with pygame. The game draws at the arcade's
native 224×288 resolution and scales the picture up with sharp pixels. All sprites, the maze and
the font are pixel art modelled on the original. The sound effects and music are synthesized
when the game starts, so there are no asset files.

## Running

```bash
pip install -r requirements.txt
python main.py            # or: python -m pacman
python main.py --scale 3  # fixed window size (by default it fits your desktop)
python main.py --mute
```

## Controls

| Key | Action |
| --- | --- |
| Arrow keys **or** W A S D | Move Pac-Man. Turns are buffered, so press a direction early and Pac-Man takes the next opening. |
| Enter / Space / 1 | Start a 1-player game |
| 2 | Start a 2-player game (players take turns) |
| C / 5 | Insert a coin (shows the "PUSH START BUTTON" screen) |
| P | Pause |
| M | Mute or unmute |
| F / F11 | Toggle fullscreen |
| Esc | Leave the game, or quit from the title screen |

## Features from the original

- The exact 28×31 maze: 240 dots, 4 flashing energizers, and wrap-around tunnels.
- Distinct ghost personalities:
  - **Blinky** chases Pac-Man directly.
  - **Pinky** aims four tiles ahead, including the original's "up" targeting bug.
  - **Inky** uses Blinky's position to pick his target.
  - **Clyde** gives up and retreats when he gets close.
- Scatter and chase waves with the original per-level timings. Ghosts reverse direction whenever the mode changes.
- Frightened mode with durations and flash counts that change per level. Eaten ghosts score 200 → 400 → 800 → 1600, and their eyes race back to the ghost house to revive.
- Ghost-house release rules: per-ghost dot counters, a global counter after you lose a life, and a timer that forces a ghost out if you stop eating.
- "Cruise Elroy": Blinky speeds up as the dots run low.
- Tiles above the ghost house and above Pac-Man's start where ghosts can't turn upward.
- Ghosts slow down in the tunnels.
- Pac-Man pauses briefly after each dot, and gains speed by cutting corners.
- Speed tables for Pac-Man and the ghosts that change with the level.
- Bonus fruit appears after 70 and 170 dots: cherry, strawberry, orange, apple, melon, Galaxian, bell, then key. The fruit row at the bottom right tracks your levels.
- An extra life at 10,000 points. The high score is saved to `~/.pygame_pacman_highscore`.
- Death animation, flashing maze when a level is cleared, and "READY!" and "GAME OVER" messages.
- Two-player alternating play. Each player keeps their own maze, level and lives.
- The three coffee-break intermissions, after levels 2, 5, 9, 13 and 17.
- Attract mode with the "CHARACTER / NICKNAME" roll call, the energizer chase, and a computer-played demo.
- The level 256 split-screen kill screen.
- Sound: intro tune, the waka-waka chomp, the siren (which speeds up as dots run out), frightened and returning-eyes sounds, eating ghosts and fruit, death, extra life and the intermission tune.

## Code layout

```
pacman/
  app.py        window, input, attract/game state machine
  game.py       rules, scoring, levels, players, demo AI, drawing
  actors.py     Pac-Man movement and ghost movement/targeting
  maze.py       maze layout, pellets, arcade-style wall rendering
  sprites.py    pixel-art sprites
  font.py       arcade bitmap font
  sound.py      synthesized sound effects and music
  attract.py    title/attract screens
  cutscenes.py  intermissions
  constants.py  colours, positions and per-level tables
```
