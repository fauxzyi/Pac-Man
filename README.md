# Pac-Man

A recreation of Pac-Man in Python with pygame. The game draws at the original 224×288 resolution and scales the picture up with sharp pixels.
All sprites, the maze and the font are pixel art modelled on the original.
The sound effects and music are synthesized when the game starts, so there are no asset files.

## Running

First install pygame
```bash
pip install pygame
```
Or if using python 3.14
```bash
pip install pygame-ce
```

Then run main.py

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
