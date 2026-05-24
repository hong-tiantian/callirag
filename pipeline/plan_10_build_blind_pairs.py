from __future__ import annotations

import argparse
import hashlib
import random
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common import (
    BLIND_DIR,
    BLIND_PAIR_SHEET_DIR,
    BLIND_PAIR_SHEET_INDEX_PATH,
    BLIND_PAIRS_PATH,
    EXPERIMENT_MANIFEST_PATH,
    GROUP_MAPPING_PATH,
    REPO_ROOT,
    load_csv,
    save_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan A step 10: build_blind_pairs.py")
    parser.add_argument("--experiment-manifest", type=Path, default=EXPERIMENT_MANIFEST_PATH, help="experiment_manifest.csv")
    parser.add_argument("--out-pairs", type=Path, default=BLIND_PAIRS_PATH, help="blind_eval_pairs.csv")
    parser.add_argument("--out-mapping", type=Path, default=GROUP_MAPPING_PATH, help="group_mapping_private.csv")
    parser.add_argument("--blind-dir", type=Path, default=BLIND_DIR, help="blind_images directory")
    parser.add_argument("--pair-sheet-dir", type=Path, default=BLIND_PAIR_SHEET_DIR, help="blind pair sheets directory")
    parser.add_argument(
        "--out-sheet-index",
        type=Path,
        default=BLIND_PAIR_SHEET_INDEX_PATH,
        help="blind_pair_sheet_index.csv",
    )
    parser.add_argument("--seed", type=int, default=2026, help="blinding random seed")
    return parser.parse_args()


def _hash_name(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12] + ".png"


def _stable_hidden_id(prefix: str, text: str, mod: int) -> str:
    value = int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:8], 16) % mod
    return f"{prefix}{value:03d}" if mod >= 100 else f"{prefix}{value:02d}"


def _resolve_repo_path(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else REPO_ROOT / path


def _load_sheet_font() -> ImageFont.ImageFont:
    return ImageFont.load_default()


def _fit_image(path: Path, max_size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    return image


def _paste_centered(canvas: Image.Image, image: Image.Image, box: tuple[int, int, int, int]) -> None:
    left, top, right, bottom = box
    x = left + (right - left - image.width) // 2
    y = top + (bottom - top - image.height) // 2
    canvas.paste(image, (x, y))


def _create_pair_sheet(pair_id: str, content_path: Path, left_path: Path, right_path: Path, out_path: Path) -> None:
    font = _load_sheet_font()
    margin = 32
    header_h = 48
    label_h = 32
    panel_w = 300
    panel_h = 360
    gap = 28
    width = margin * 2 + panel_w * 3 + gap * 2
    height = margin * 2 + header_h + label_h + panel_h

    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, margin), pair_id, fill="black", font=font)

    left_label_y = margin + header_h
    target_x = margin
    left_x = margin + panel_w + gap
    right_x = margin + (panel_w + gap) * 2
    draw.text((target_x, left_label_y), "Target", fill="black", font=font)
    draw.text((left_x, left_label_y), "Left", fill="black", font=font)
    draw.text((right_x, left_label_y), "Right", fill="black", font=font)

    panel_y = left_label_y + label_h
    target_box = (target_x, panel_y, target_x + panel_w, panel_y + panel_h)
    left_box = (left_x, panel_y, left_x + panel_w, panel_y + panel_h)
    right_box = (right_x, panel_y, right_x + panel_w, panel_y + panel_h)
    draw.rectangle(target_box, outline="black", width=1)
    draw.rectangle(left_box, outline="black", width=1)
    draw.rectangle(right_box, outline="black", width=1)

    content_img = _fit_image(content_path, (panel_w - 20, panel_h - 20))
    left_img = _fit_image(left_path, (panel_w - 20, panel_h - 20))
    right_img = _fit_image(right_path, (panel_w - 20, panel_h - 20))
    _paste_centered(canvas, content_img, target_box)
    _paste_centered(canvas, left_img, left_box)
    _paste_centered(canvas, right_img, right_box)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def _append_pair(
    *,
    args: argparse.Namespace,
    rng: random.Random,
    pair_idx: int,
    target: str,
    comp_type: str,
    left_src: dict | None,
    right_src: dict | None,
    pairs: list[dict],
    mapping: list[dict],
    sheet_index: list[dict],
) -> int:
    if left_src is None or right_src is None:
        return pair_idx
    content_path = _resolve_repo_path((left_src.get("content_path") or right_src.get("content_path") or "").strip())
    left_path = _resolve_repo_path(left_src.get("output_path", ""))
    right_path = _resolve_repo_path(right_src.get("output_path", ""))
    if not content_path.is_file() or not left_path.is_file() or not right_path.is_file():
        return pair_idx

    if rng.random() < 0.5:
        img_l_src, img_r_src = left_src, right_src
    else:
        img_l_src, img_r_src = right_src, left_src

    left_blind = _hash_name(f"{pair_idx}-L-{img_l_src['output_path']}")
    right_blind = _hash_name(f"{pair_idx}-R-{img_r_src['output_path']}")
    left_dst = args.blind_dir / left_blind
    right_dst = args.blind_dir / right_blind
    shutil.copy2(_resolve_repo_path(img_l_src["output_path"]), left_dst)
    shutil.copy2(_resolve_repo_path(img_r_src["output_path"]), right_dst)

    pair_id = f"P{pair_idx:04d}"
    target_hidden = _stable_hidden_id("T", target, 1000)
    sheet_path = args.pair_sheet_dir / f"{pair_id}.png"
    _create_pair_sheet(pair_id, content_path, left_dst, right_dst, sheet_path)
    pairs.append(
        {
            "pair_id": pair_id,
            "target_char_hidden_id": target_hidden,
            "target_content_image": content_path.as_posix(),
            "left_image": left_dst.as_posix(),
            "right_image": right_dst.as_posix(),
            "comparison_type": comp_type,
            "left_source_group_hidden": _stable_hidden_id("G", img_l_src["group"], 97),
            "right_source_group_hidden": _stable_hidden_id("G", img_r_src["group"], 97),
        }
    )
    sheet_index.append(
        {
            "pair_id": pair_id,
            "sheet_image": sheet_path.as_posix(),
        }
    )
    mapping.append(
        {
            "pair_id": pair_id,
            "target_char": target,
            "comparison_type": comp_type,
            "content_path": left_src.get("content_path") or right_src.get("content_path"),
            "left_true_group": img_l_src["group"],
            "right_true_group": img_r_src["group"],
            "left_output_path": img_l_src["output_path"],
            "right_output_path": img_r_src["output_path"],
        }
    )
    return pair_idx + 1


def main() -> None:
    args = parse_args()
    args.blind_dir.mkdir(parents=True, exist_ok=True)
    args.pair_sheet_dir.mkdir(parents=True, exist_ok=True)
    rows = load_csv(args.experiment_manifest)
    by_target: dict[str, list[dict]] = {}
    for r in rows:
        by_target.setdefault(r.get("target_char", ""), []).append(r)

    rng = random.Random(args.seed)
    pairs = []
    mapping = []
    sheet_index = []
    pair_idx = 1

    target_items = list(by_target.items())

    for target_idx, (target, items) in enumerate(target_items):
        group_a = next((x for x in items if x.get("group") == "A"), None)
        group_c = next((x for x in items if x.get("group") == "C"), None)
        random_seed = target_idx % 5
        group_b = next(
            (x for x in items if x.get("group") == "B" and str(x.get("ref_selection_seed", "")) == str(random_seed)),
            None,
        )
        group_d3 = next((x for x in items if x.get("group") == "D" and str(x.get("retrieval_rank", "")) == "3"), None)
        group_d5 = next((x for x in items if x.get("group") == "D" and str(x.get("retrieval_rank", "")) == "5"), None)

        candidates = [
            ("A_vs_C", group_a, group_c),
            (f"B_seed{random_seed}_vs_C", group_b, group_c),
            ("C_rank1_vs_D_rank3", group_c, group_d3),
            ("C_rank1_vs_D_rank5", group_c, group_d5),
        ]
        for comp_type, left_src, right_src in candidates:
            pair_idx = _append_pair(
                args=args,
                rng=rng,
                pair_idx=pair_idx,
                target=target,
                comp_type=comp_type,
                left_src=left_src,
                right_src=right_src,
                pairs=pairs,
                mapping=mapping,
                sheet_index=sheet_index,
            )

    for target_idx, (target, items) in enumerate(target_items):
        group_c = next((x for x in items if x.get("group") == "C"), None)
        primary_seed = target_idx % 5
        for seed in [0, 1, 2, 3, 4]:
            if seed == primary_seed:
                continue
            group_b = next(
                (x for x in items if x.get("group") == "B" and str(x.get("ref_selection_seed", "")) == str(seed)),
                None,
            )
            pair_idx = _append_pair(
                args=args,
                rng=rng,
                pair_idx=pair_idx,
                target=target,
                comp_type=f"B_seed{seed}_vs_C",
                left_src=group_b,
                right_src=group_c,
                pairs=pairs,
                mapping=mapping,
                sheet_index=sheet_index,
            )

    save_csv(
        args.out_pairs,
        pairs,
        [
            "pair_id",
            "target_char_hidden_id",
            "target_content_image",
            "left_image",
            "right_image",
            "comparison_type",
            "left_source_group_hidden",
            "right_source_group_hidden",
        ],
    )
    save_csv(args.out_sheet_index, sheet_index, ["pair_id", "sheet_image"])
    save_csv(
        args.out_mapping,
        mapping,
        [
            "pair_id",
            "target_char",
            "comparison_type",
            "content_path",
            "left_true_group",
            "right_true_group",
            "left_output_path",
            "right_output_path",
        ],
    )
    print(f"wrote blind pairs={len(pairs)}: {args.out_pairs.as_posix()}")
    print(f"wrote blind pair sheets={len(sheet_index)}: {args.pair_sheet_dir.as_posix()}")
    print(f"wrote blind pair sheet index={len(sheet_index)}: {args.out_sheet_index.as_posix()}")
    print(f"wrote private mapping={len(mapping)}: {args.out_mapping.as_posix()}")


if __name__ == "__main__":
    main()

