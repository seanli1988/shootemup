# Simple Python Shoot'em Up

This is a beginner-friendly 2D arcade shoot'em up made with **Python + Pygame**.

## Features

- Player jet moves up, down, left, right
- Player fires **5 bullets per second**
- Enemy team fires **2 bullets per second**
- **No time limit** (you play until you win or lose)
- Difficulty levels:
  - Easy: 2 rows of enemies
  - Medium: 3 rows of enemies
  - Hard: 3 rows, more enemies and faster movement/bullets

## Controls

- Move: Arrow keys or `W A S D`
- Shoot: `Space`
- Choose level in menu: `1`, `2`, `3`
- Restart to menu after game ends: `R`
- Quit: `Esc`

## Run

1. Install pygame:

```bash
pip install pygame
```

2. Start the game:

```bash
python main.py
```

## Notes

- The code is intentionally simple and heavily commented for learning.
- You can tweak values in `DIFFICULTIES` inside `main.py` to rebalance the game.
