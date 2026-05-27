# Asset Pipeline

## Background Layers

Place layer PNGs in `assets/backgrounds/`. Each file is optional — if missing, a procedural fallback is drawn.

| File | Layer | Parallax | Y | Description |
|---|---|---|---|---|
| `sky.png` | Sky | 0.0x (static) | 0 | Sky gradient, moon, stars |
| `far.png` | Far background | 0.12x | 0 | City skyline silhouette |
| `mid.png` | Mid background | 0.30x | 140 | Closer buildings with windows |
| `ground.png` | Ground/street | 0.0x (static) | 420 | Road surface, lane markings |

### Asset dimensions

Each image should be at least **960px wide** (screen width). They tile horizontally on scroll, so a seamless repeat is ideal.

| Layer | Recommended height | Expected content |
|---|---|---|
| `sky.png` | 180+ | Covers y=0..180 night sky |
| `far.png` | 260+ | Covers y=0..260 silhouettes |
| `mid.png` | 190+ | Covers y=140..330 buildings |
| `ground.png` | 120+ | Covers y=420..540 street texture |

### Parallax speed

- `far` scrolls at 12% of camera speed
- `mid` scrolls at 30% of camera speed
- `sky` and `ground` are static (0% parallax)

---

## Player Sprite Sheet

The game loads player walk and idle animation frames from either an exported sprite sheet or raw frame files.

### Option 1: Exported sprite sheet (preferred)

```bash
python tools/export_spritesheet.py \
  --input assets/sprites/player \
  --output assets/exports/player_sheet.png \
  --meta assets/exports/player_sheet.json \
  --columns 8 \
  --padding 2
```

The exporter packs all PNGs from `assets/sprites/player/` into a single sheet and writes a JSON metadata file. The game reads the JSON to locate frames tagged with `"animation": "walk"` or `"animation": "idle"`.

### Option 2: Raw frame files

If no sheet exists, the game falls back to loading individual PNGs from:

| Animation | Path pattern |
|---|---|
| Walk | `assets/sprites/player/walk_*.png` |
| Idle | `assets/sprites/player/idle_*.png` |

### Fallback

If neither sheet nor raw frames are found, the player is drawn as a colored rectangle.

---

## Supported Formats

All PNG images are loaded via `pygame.image.load()` with a Pillow (PIL) fallback if pygame's native loader fails. RGBA transparency is preserved.

---

## File Structure

```
assets/
├── backgrounds/
│   ├── sky.png        (optional)
│   ├── far.png        (optional)
│   ├── mid.png        (optional)
│   └── ground.png     (optional)
├── exports/
│   ├── player_sheet.png
│   └── player_sheet.json
├── sprites/
│   └── player/
│       ├── idle_00.png
│       ├── idle_01.png
│       ├── walk_00.png
│       ├── walk_01.png
│       └── punch_00.png
└── ui/                 (reserved)
```
