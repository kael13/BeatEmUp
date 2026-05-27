"""
Sprite export helper.

Usage:
python tools/export_spritesheet.py --input assets/sprites/player --output assets/exports/player_sheet.png --meta assets/exports/player_sheet.json

Expected input folder naming (recommended):
idle_00.png, idle_01.png, walk_00.png, walk_01.png, punch_00.png, ...
"""

import argparse
import json
from pathlib import Path
from PIL import Image


def collect_frames(folder: Path):
    frames = sorted([p for p in folder.glob("*.png")])
    if not frames:
        raise ValueError(f"No PNG frames found in: {folder}")
    return frames


def build_sheet(frame_paths, out_path: Path, meta_path: Path, columns: int = 8, padding: int = 2, scale: float = 1.0):
    raw_images = [Image.open(p).convert("RGBA") for p in frame_paths]
    if scale != 1.0:
        images = []
        for img in raw_images:
            nw = int(img.width * scale)
            nh = int(img.height * scale)
            images.append(img.resize((nw, nh), Image.LANCZOS))
    else:
        images = raw_images

    w = max(img.width for img in images)
    h = max(img.height for img in images)

    rows = (len(images) + columns - 1) // columns
    sheet_w = columns * w + (columns - 1) * padding
    sheet_h = rows * h + (rows - 1) * padding

    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    meta = {
        "frame_size": {"w": w, "h": h},
        "columns": columns,
        "padding": padding,
        "scale": scale,
        "frames": []
    }

    for i, (path, img) in enumerate(zip(frame_paths, images)):
        col = i % columns
        row = i // columns
        x = col * (w + padding)
        y = row * (h + padding)
        sheet.paste(img, (x, y), img)

        name = path.stem
        anim = name.split("_")[0] if "_" in name else "default"

        meta["frames"].append(
            {
                "name": name,
                "animation": anim,
                "x": x,
                "y": y,
                "w": img.width,
                "h": img.height,
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Folder with PNG frames")
    parser.add_argument("--output", required=True, help="Output spritesheet PNG path")
    parser.add_argument("--meta", required=True, help="Output JSON metadata path")
    parser.add_argument("--columns", type=int, default=8)
    parser.add_argument("--padding", type=int, default=2)
    parser.add_argument("--scale", type=float, default=1.0, help="Upscale factor (e.g. 2.0 for 2x)")
    args = parser.parse_args()

    input_dir = Path(args.input)
    frames = collect_frames(input_dir)
    build_sheet(frames, Path(args.output), Path(args.meta), args.columns, args.padding, args.scale)

    print(f"Exported {len(frames)} frames -> {args.output}")
    print(f"Metadata -> {args.meta}")


if __name__ == "__main__":
    main()
