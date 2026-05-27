# BeatEmUp — Project Memory

## Project Overview
2D beat-'em-up built with **Pygame 2.6.1** on **Python 3.14**. Modular architecture under `beatemup/` package.

## Critical Technical Constraints

### Font Rendering
`pygame.font` has a **circular import bug on pygame 2.6.1 + Python 3.14** (font.py → sysfont.py → font.py). Do NOT use `pygame.font.SysFont()` or `pygame.font.Font()`. Instead, use `pygame._freetype` directly via the `_FontWrapper` class:

```python
from pygame._freetype import Font as _FtFont, init as _ft_init
_ft_init()
class _FontWrapper:
    def __init__(self, file, size):
        self._f = _FtFont(file, size)
    def render(self, text, antialias, color, background=None):
        s, _ = self._f.render(text, color, background)
        return s
font = _FontWrapper(None, 20)
```

Always pass `font` as a parameter to render functions — never create new font instances inside draw functions.

## Stage Flow
- Stage = 4 zones (zone 0-3, zone 3 is boss)
- Each zone has `waves_per_zone` (3) waves of enemies
- Final zone: waves 1-2 are regular enemies, wave 3 trigger spawns boss
- Boss defeated → `stage_complete = True`, `game_cleared = True`
- **Stage Complete screen** shows stats; player presses **J** to continue
- `advance_to_next_stage()` resets zones/HP/power but preserves total score and lives
- Difficulty scales +15% per stage

### Key State Fields (GameState)
- `stage_complete: bool` — frozen state between stages
- `stage_score: int` — score earned this stage (for results screen)
- `enemies_killed_this_stage: int`
- `score_popups: list` — floating score text entries `{"text", "x", "y", "timer"}`
- `controls_timer: int` — counts up to `CONTROLS_FADE_FRAMES` (300) for hint fade

## Combat System
- **J attack**: Immediate trigger on single press (was 3-tap combo). Cooldown 15 frames. Timer window 10 frames.
- **K kick**: Immediate trigger. Cooldown 15 frames. Timer window 8 frames. Radius 76px.
- **L power attack**: Consumes 100 power meter. Radius 120px.
- **Space jump**: Jump + attack = jump attack (+4 damage, larger radius).
- **Double-tap direction**: Sprint (1.85x speed, 150 frames).

## Attack Implementation Rules
- Player attacks use `try_free_attack()` and `try_kick_attack()` with `consume_cooldown=False` — cooldown is set once by the caller before the enemy loop.
- NEVER use miss/chance logic for player attacks. `should_attack_hit()` / `calculate_attack_accuracy()` is enemies-only.
- `try_kick_attack()` must always hit on hitbox collision (deterministic, like `try_free_attack`).

## Hitbox Visualization
- J attack hitbox: drawn via `draw_player_free_attack_hitbox()` using `player_attack_timer > 0`
- K kick hitbox: drawn via `draw_player_kick_hitbox()` using `player_kick_active > 0` (timer-based, 8 frames)
- Kick hitbox radius uses `KICK_ATTACK_RANGE` (76), NOT the regular attack radius (46/58)

## UI Layout
- **HP bar**: top-left, always renders
- **Lives**: below HP bar, always renders
- **Power bar**: below lives, always renders
- **Zone panel**: top-right, always renders background; text needs font
- **Controls hint**: fades out over 300 frames
- **All text rendering guarded**: `if font is None: return` — non-text elements must render before this check
- **Boss HP bar**: centered top, large, only when boss alive
- **Score popups**: floating "+100"/"+500" at enemy death position, 30-frame lifetime

## Score Tracking
- Enemy kill scores go to both `state.score` and `state.stage_score`
- Kill popups track enemy position at death
- `enemies_killed_this_stage` tracks non-boss kills only
- Zone completion adds `SCORE_PER_STAGE_COMPLETE` to both `state.score` and `state.stage_score`

## Background Layer Dimensions

Loaded from `assets/backgrounds/{sky,far,mid,ground,foreground}.png`. All layers are tiled horizontally via `_tile_blit()` (two blits side-by-side), so each image must be at least **`WIDTH` (960px)** wide for seamless wrapping. Recommended dimensions:

| Layer | Parallax | Y pos | Min Width | Recommended Height | Vertical Coverage |
|---|---|---|---|---|---|
| `sky` | 0.0 | 0 | 960 | ~540 (full screen) | Gradient sky covering screen top |
| `far` | 0.12 | 0 | 960 | ~200 | Buildings up to ~185px tall from y=0 |
| `mid` | 0.30 | 140 | 960 | ~310 | Buildings from y=140 down to ~y=450 |
| `ground` | 0.0 | 420 | 960 | ~120 | Street from y=420 to bottom (540) |
| `foreground` | 0.60 | 0 | 960 | ~540 | Renders **after** fighters (on top). Use RGBA for transparent regions |

Surfaces smaller than 960px wide will show gaps when the parallax offset wraps. Height can be smaller than recommended if the extra area is obstructed by layers above it (e.g. `mid` doesn't need pixels above y=140 since `far`/`sky` sit behind it).

## Sprite Asset Resolutions

### Player Frames
Source frames under `assets/sprites/player/` must be **128×128 px** each. The runtime scaler (`models.py:37-45`) renders them at **350px height** (width auto from aspect ratio). If you change source dimensions, also update `_sprite_src_height=128` and `_sprite_bottom_pad=48` in `models.py:29-31` to keep the vertical offset correct.

| Animation | Frames | Naming Pattern |
|---|---|---|
| Idle | 10 | `idle_00.png` – `idle_09.png` |
| Walk | 10 | `walk_00.png` – `walk_09.png` |
| Run | 10 | `run_00.png` – `run_09.png` |
| Attack | 3 | `attack_a_00.png` – `attack_a_02.png` |

### Sprite Sheet Export
Tool: `tools/export_spritesheet.py`
- Flags: `--columns` (default 8), `--padding` (default 2), `--scale` (default 1.0)
- Current export used: `--columns 10 --padding 2 --scale 3.0`
- Output: `assets/exports/player_sheet.png` + `player_sheet.json` with per-frame metadata

### Enemies
Enemies use sprite frames from `assets/sprites/enemy/`. All PNGs in the folder are loaded, sorted alphabetically, and played as a looping animation at 8 frames per tick. Design frames at the same source resolution as the player (128×128 px) so the scaler and vertical offset match correctly.

| Asset | Naming Pattern | Example |
|---|---|---|
| Demon fly | `{name}{frame:03d}.png` | `demon_fly000.png` – `demon_fly003.png` |
| Demon attack | `{name}{frame:03d}.png` | `demon_attack000.png` – `demon_attack007.png` |
| Demon death | `{name}_{frame:03d}.png` | `demon_death_000.png` – `demon_death_006.png` |

Enemy animation plays per-enemy based on their state:
- **fly**: looping (4 frames, 8 ticks/frame)
- **attack**: triggers on attack, plays once then returns to fly (8 frames, 3 ticks/frame)
- **death**: triggers on death, plays once then freezes on last frame (7 frames, 4 ticks/frame)

Fallback: colored rectangles (60×90 px hitbox) when no sprites present. See `render.py:124-156`.

## Asset Pipeline
- Sprite sheet export: `tools/export_spritesheet.py`
- Expected naming: `idle_00.png`, `walk_00.png`, `punch_00.png`, etc.
- Fallback: colored rectangles when no sprites are present

## Test Commands
```bash
PYTHONPATH="$PWD" pytest -q
PYTHONPATH="$PWD" python -m py_compile beatemup/*.py
```

## Constants (`constants.py`)
- `ZONE_COUNT = 4`, `ZONE_WIDTH = 950`
- `SCORE_PER_ENEMY = 100`, `SCORE_PER_BOSS = 500`, `SCORE_PER_STAGE_COMPLETE = 1000`
- `SCORE_POPUP_DURATION = 30`, `CONTROLS_FADE_FRAMES = 300`
- `KICK_DAMAGE = 12`, `KICK_BOSS_DAMAGE = 14`, `KICK_COOLDOWN_FRAMES = 15`, `KICK_ATTACK_RANGE = 76`
- `DIFFICULTY_SCALE_PER_STAGE = 0.15`
