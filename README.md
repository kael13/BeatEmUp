# Python Beat 'Em Up Starter

A lightweight, Python-based beat-'em-up starter using `pygame`, with a built-in sprite-sheet exporter for asset pipelines.

## Includes
- Playable prototype (`main.py`)
- Stage-based fighter movement, combo attack, sprint, HP/lives, reset flow
- Asset folder structure for sprites/background/UI
- Sprite-sheet export tool (`tools/export_spritesheet.py`) + JSON frame metadata
- Modular game code in `beatemup/` for scalability

## Stage Flow
- `Zone 1`: player spawns on the left with a short spawn animation and can roam forward.
- Entering the next zone triggers enemy encounters waiting in that zone.
- Clearing a zone unlocks progression to the next zone.
- `Zone 4` is the final boss fight.
- Reach and clear the boss to complete the stage.

## Code Structure

```text
beatemup/
  constants.py   # Tunable gameplay/screen constants
  models.py      # Data models (fighter, game state)
  systems.py     # Movement, combat, AI, camera, spawning
  render.py      # Background, fighters, HUD drawing
  game.py        # Main game loop orchestration
main.py          # Thin entrypoint
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Game

```bash
python3 main.py
```

## Run Tests

```bash
pytest -q
```

Controls:
- Move: `WASD` or `Arrow Keys`
- Attack: `J`
- Kick: `K`
- Force enemy attack test: (unused)
- Restart: `R`

## Asset/Sprite Pipeline

Put animation frames in:
- `assets/sprites/player/`
- `assets/sprites/enemy/`

Recommended file names:
- `idle_00.png`, `idle_01.png`
- `walk_00.png`, `walk_01.png`
- `punch_00.png`, ...

Export a sprite sheet:

```bash
python3 tools/export_spritesheet.py \
  --input assets/sprites/player \
  --output assets/exports/player_sheet.png \
  --meta assets/exports/player_sheet.json \
  --columns 8 \
  --padding 2
```

The JSON contains frame positions/sizes for easy runtime loading.

## Combat System
- **Regular Attack (J)**: Standard attack with combo system
- **Kick Attack (K)**: Quick kick attack with faster recovery but shorter range
- **Jump Attack**: Automatic when jumping + attacking
- **Special Attack (L)**: Power attack that consumes power meter

*Note: Kick attack hitbox is visible in yellow for debugging purposes, matching the regular attack hitbox style*

## Next Upgrade Ideas
- Add animation playback from exported JSON
- Add combo chains and knockback
- Add multiple enemies + wave spawner
- Add camera bounds + parallax background
