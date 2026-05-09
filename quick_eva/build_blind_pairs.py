from __future__ import annotations

import argparse
import hashlib
import random
import shutil
from pathlib import Path

from common import BLIND_DIR, BLIND_PAIRS_PATH, EXPERIMENT_MANIFEST_PATH, GROUP_MAPPING_PATH, REPO_ROOT, load_csv, save_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan A Script 10: build_blind_pairs.py")
    parser.add_argument("--experiment-manifest", type=Path, default=EXPERIMENT_MANIFEST_PATH, help="experiment_manifest.csv")
    parser.add_argument("--out-pairs", type=Path, default=BLIND_PAIRS_PATH, help="blind_eval_pairs.csv")
    parser.add_argument("--out-mapping", type=Path, default=GROUP_MAPPING_PATH, help="group_mapping_private.csv")
    parser.add_argument("--blind-dir", type=Path, default=BLIND_DIR, help="blind_images directory")
    parser.add_argument("--seed", type=int, default=2026, help="blinding random seed")
    return parser.parse_args()


def _hash_name(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12] + ".png"


def _resolve_repo_path(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else REPO_ROOT / path


def main() -> None:
    args = parse_args()
    args.blind_dir.mkdir(parents=True, exist_ok=True)
    rows = load_csv(args.experiment_manifest)
    by_target: dict[str, list[dict]] = {}
    for r in rows:
        by_target.setdefault(r.get("target_char", ""), []).append(r)

    rng = random.Random(args.seed)
    pairs = []
    mapping = []
    pair_idx = 1

    for target, items in by_target.items():
        group_a = next((x for x in items if x.get("group") == "A"), None)
        group_c = next((x for x in items if x.get("group") == "C"), None)
        group_b0 = next((x for x in items if x.get("group") == "B" and str(x.get("ref_selection_seed", "")) == "0"), None)
        group_d3 = next((x for x in items if x.get("group") == "D" and str(x.get("retrieval_rank", "")) == "3"), None)
        group_d5 = next((x for x in items if x.get("group") == "D" and str(x.get("retrieval_rank", "")) == "5"), None)

        candidates = [
            ("A_vs_C", group_a, group_c),
            ("B_vs_C", group_b0, group_c),
            ("C_rank1_vs_D_rank3", group_c, group_d3),
            ("C_rank1_vs_D_rank5", group_c, group_d5),
        ]
        for comp_type, left_src, right_src in candidates:
            if left_src is None or right_src is None:
                continue
            left_path = _resolve_repo_path(left_src.get("output_path", ""))
            right_path = _resolve_repo_path(right_src.get("output_path", ""))
            if not left_path.is_file() or not right_path.is_file():
                continue

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
            target_hidden = f"T{abs(hash(target)) % 1000:03d}"
            pairs.append(
                {
                    "pair_id": pair_id,
                    "target_char_hidden_id": target_hidden,
                    "left_image": left_dst.as_posix(),
                    "right_image": right_dst.as_posix(),
                    "comparison_type": comp_type,
                    "left_source_group_hidden": f"G{abs(hash(img_l_src['group'])) % 97:02d}",
                    "right_source_group_hidden": f"G{abs(hash(img_r_src['group'])) % 97:02d}",
                }
            )
            mapping.append(
                {
                    "pair_id": pair_id,
                    "target_char": target,
                    "comparison_type": comp_type,
                    "left_true_group": img_l_src["group"],
                    "right_true_group": img_r_src["group"],
                    "left_output_path": img_l_src["output_path"],
                    "right_output_path": img_r_src["output_path"],
                }
            )
            pair_idx += 1

    save_csv(
        args.out_pairs,
        pairs,
        [
            "pair_id",
            "target_char_hidden_id",
            "left_image",
            "right_image",
            "comparison_type",
            "left_source_group_hidden",
            "right_source_group_hidden",
        ],
    )
    save_csv(
        args.out_mapping,
        mapping,
        [
            "pair_id",
            "target_char",
            "comparison_type",
            "left_true_group",
            "right_true_group",
            "left_output_path",
            "right_output_path",
        ],
    )
    print(f"wrote blind pairs={len(pairs)}: {args.out_pairs.as_posix()}")
    print(f"wrote private mapping={len(mapping)}: {args.out_mapping.as_posix()}")


if __name__ == "__main__":
    main()

