from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from PIL import Image, ImageDraw, ImageFont

from common import BANK_DIR, CASES_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate content images for wxz ids using Source Han Sans SC."
    )
    parser.add_argument(
        "--content-dir",
        type=Path,
        default=CASES_DIR / "content",
        help="Output content image directory.",
    )
    parser.add_argument(
        "--font-path",
        type=Path,
        default=Path("SourceHanSansSC-Normal.otf"),
        help="Path to .otf/.ttf font file.",
    )
    parser.add_argument(
        "--ids",
        type=str,
        default="",
        help="Comma-separated ids (e.g. 20,21,100).",
    )
    parser.add_argument(
        "--id-file",
        type=Path,
        default=None,
        help="Optional text file containing one id per line.",
    )
    parser.add_argument(
        "--wxz-bank",
        type=Path,
        default=BANK_DIR / "wxz_bank.json",
        help="wxz_bank.json used to map id -> character.",
    )
    parser.add_argument(
        "--char-csv",
        type=Path,
        default=CASES_DIR / "wxz_gt_chars.csv",
        help="Optional id-char csv (编号, 字符) with higher priority than bank.",
    )
    parser.add_argument(
        "--default-size",
        type=int,
        default=96,
        help="Fallback square size if content dir has no existing jpg.",
    )
    parser.add_argument(
        "--margin-ratio",
        type=float,
        default=0.08,
        help="Padding ratio around glyph (0.08 -> 8%% each side).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing content images for selected ids.",
    )
    return parser.parse_args()


def _norm_id(x: str) -> str:
    x = x.strip()
    if not x:
        return ""
    # Keep numeric ids zero-padded to 4, preserving larger ids (e.g. 6232).
    if x.isdigit():
        return f"{int(x):04d}"
    return x


def load_ids(ids_text: str, id_file: Path | None) -> List[str]:
    items: List[str] = []
    if ids_text.strip():
        items.extend(_norm_id(x) for x in ids_text.split(","))
    if id_file:
        for line in id_file.read_text(encoding="utf-8").splitlines():
            items.append(_norm_id(line))
    # de-dup while preserving order
    seen = set()
    out = []
    for x in items:
        if not x or x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def load_char_map_from_csv(csv_path: Path) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    if not csv_path.exists():
        return mapping
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            idx = _norm_id(str(row.get("编号", "")))
            ch = str(row.get("字符", "")).strip()
            if idx and ch:
                mapping[idx] = ch
    return mapping


def load_char_map_from_bank(bank_path: Path) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    if not bank_path.exists():
        return mapping
    data = json.loads(bank_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return mapping
    for row in data:
        wxz_path = str(row.get("wxz_path", "")).strip()
        ch = str(row.get("character", "")).strip()
        if not wxz_path or not ch:
            continue
        img_name = Path(wxz_path).name
        idx = _norm_id(Path(img_name).stem)
        if idx:
            mapping[idx] = ch
    return mapping


def infer_common_size(content_dir: Path, fallback: int) -> int:
    jpgs = sorted(content_dir.glob("*.jpg"))
    if not jpgs:
        return fallback
    counter: Counter[Tuple[int, int]] = Counter()
    for p in jpgs[:800]:
        try:
            with Image.open(p) as im:
                counter[im.size] += 1
        except Exception:
            continue
    if not counter:
        return fallback
    (w, h), _ = counter.most_common(1)[0]
    if w != h:
        return fallback
    return w


def pick_size_for_id(content_dir: Path, idx: str, default_size: int) -> int:
    p = content_dir / f"{idx}.jpg"
    if p.exists():
        try:
            with Image.open(p) as im:
                if im.size[0] == im.size[1]:
                    return im.size[0]
        except Exception:
            pass
    return default_size


def fit_font_size(
    text: str,
    font_path: Path,
    image_size: int,
    margin_ratio: float,
    min_size: int = 10,
    max_size: int = 220,
) -> int:
    target = int(image_size * (1 - 2 * margin_ratio))
    best = min_size
    lo, hi = min_size, max_size
    while lo <= hi:
        mid = (lo + hi) // 2
        font = ImageFont.truetype(str(font_path), size=mid)
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if w <= target and h <= target:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def render_char_image(ch: str, size: int, font_path: Path, margin_ratio: float) -> Image.Image:
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    font_size = fit_font_size(ch, font_path, size, margin_ratio)
    font = ImageFont.truetype(str(font_path), size=font_size)
    bbox = draw.textbbox((0, 0), ch, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (size - w) / 2 - bbox[0]
    y = (size - h) / 2 - bbox[1]
    draw.text((x, y), ch, fill="black", font=font)
    return img


def main() -> None:
    args = parse_args()
    content_dir: Path = args.content_dir
    content_dir.mkdir(parents=True, exist_ok=True)

    if not args.font_path.exists():
        fallback_fonts = [
            Path("sourcehansanssc-normal.otf"),
            Path("SourceHanSansSC-Normal.otf"),
        ]
        matched = next((p for p in fallback_fonts if p.exists()), None)
        if matched:
            args.font_path = matched
        else:
            raise FileNotFoundError(f"font not found: {args.font_path}")

    ids = load_ids(args.ids, args.id_file)
    if not ids:
        raise ValueError("No ids provided. Use --ids or --id-file.")

    char_map = load_char_map_from_bank(args.wxz_bank)
    char_map.update(load_char_map_from_csv(args.char_csv))

    default_size = infer_common_size(content_dir, args.default_size)
    print(f"[info] inferred default content size: {default_size}x{default_size}")

    created = 0
    skipped_exist = 0
    skipped_no_char: List[str] = []

    for idx in ids:
        out_path = content_dir / f"{idx}.jpg"
        if out_path.exists() and not args.overwrite:
            skipped_exist += 1
            continue

        ch = char_map.get(idx, "").strip()
        if not ch:
            skipped_no_char.append(idx)
            continue
        # Keep a single visible glyph as content target.
        ch = ch[0]

        img_size = pick_size_for_id(content_dir, idx, default_size)
        img = render_char_image(ch, img_size, args.font_path, args.margin_ratio)
        img.save(out_path, format="JPEG", quality=95)
        created += 1

    print(f"[done] created={created}, skipped_existing={skipped_exist}, no_char={len(skipped_no_char)}")
    if skipped_no_char:
        print("[no_char_ids] " + ",".join(skipped_no_char))


if __name__ == "__main__":
    main()

