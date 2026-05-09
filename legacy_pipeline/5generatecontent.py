#!/usr/bin/env python3
"""Generate content images for each character in decomp.json.

Output filename follows the entry's `id` field, e.g. 5395.jpg.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    rag_root = Path(__file__).resolve().parents[1]
    project_root = rag_root.parent
    parser = argparse.ArgumentParser(
        description="Generate content images for each character in decomp.json."
    )
    parser.add_argument(
        "--decomp",
        type=Path,
        default=rag_root / "bank" / "decomp.json",
        help="Path to decomp.json",
    )
    parser.add_argument(
        "--font",
        type=Path,
        default=project_root / "data" / "SourceHanSansSC-Regular.otf",
        help="Path to sourcehansansSC-regular.otf",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=rag_root / "cases" / "content",
        help="Output directory for content images",
    )
    parser.add_argument(
        "--image-size",
        type=int,
        default=96,
        help="Final square content image size in pixels (FontDiffuser default: 96)",
    )
    parser.add_argument(
        "--render-size",
        type=int,
        default=128,
        help="Intermediate canvas size before resize (FontDiffuser ttf2im default: 128)",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=128,
        help="Fixed render font size on intermediate canvas",
    )
    parser.add_argument(
        "--resample",
        type=str,
        choices=["bilinear", "bicubic", "lanczos"],
        default="bilinear",
        help="Resampling method when render-size != image-size",
    )
    parser.add_argument(
        "--ext", type=str, default="jpg", choices=["jpg", "jpeg"], help="Image extension"
    )
    parser.add_argument(
        "--quality", type=int, default=95, help="JPEG quality (1-100)"
    )
    return parser.parse_args()


def load_decomp(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def render_char_image(
    char: str,
    font_path: Path,
    out_path: Path,
    image_size: int,
    render_size: int,
    font_size: int,
    resample: str,
    quality: int,
) -> None:
    img = Image.new("RGB", (render_size, render_size), color="white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(str(font_path), size=font_size)

    left, top, right, bottom = draw.textbbox((0, 0), char, font=font)
    text_w = right - left
    text_h = bottom - top
    x = (render_size - text_w) // 2 - left
    y = (render_size - text_h) // 2 - top
    draw.text((x, y), char, fill="black", font=font)

    resample_map = {
        "bilinear": Image.Resampling.BILINEAR,
        "bicubic": Image.Resampling.BICUBIC,
        "lanczos": Image.Resampling.LANCZOS,
    }
    if render_size != image_size:
        img = img.resize((image_size, image_size), resample_map[resample])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="JPEG", quality=quality)


def main() -> None:
    args = parse_args()

    if not args.decomp.exists():
        raise FileNotFoundError(f"decomp.json not found: {args.decomp}")
    if not args.font.exists():
        raise FileNotFoundError(f"font file not found: {args.font}")

    data = load_decomp(args.decomp)

    total = 0
    skipped = 0

    for key, item in data.items():
        if not isinstance(item, dict):
            skipped += 1
            continue

        char = item.get("character") or key
        char_id = item.get("id")
        if not char or not char_id:
            skipped += 1
            continue

        out_path = args.out_dir / f"{char_id}.{args.ext}"
        render_char_image(
            char=char,
            font_path=args.font,
            out_path=out_path,
            image_size=args.image_size,
            render_size=args.render_size,
            font_size=args.font_size,
            resample=args.resample,
            quality=args.quality,
        )
        total += 1

    print(f"Done. Generated {total} images into: {args.out_dir}")
    if skipped:
        print(f"Skipped {skipped} entries (missing/invalid fields).")


if __name__ == "__main__":
    main()
