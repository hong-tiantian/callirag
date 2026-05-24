from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from common import (
    BLIND_PAIR_SHEET_DIR,
    BLIND_PAIRS_PATH,
    GROUP_MAPPING_PATH,
    LAYER2_ANN_PATH,
    LAYER2_RESULT_PATH,
    load_csv,
    save_csv,
)


REASON_TAGS = ("local_detail_better", "component_structure_better")
REASON_TAG_SET = set(REASON_TAGS)
CHOICES = ("left better", "right better", "tie", "unclear")
FREE_NOTE_EXAMPLE = "右图局部更完整；左图有 missing stroke / wrong connection"
ANNOTATION_FIELDNAMES = [
    "pair_id",
    "sheet_image",
    "evaluator_id",
    "choice",
    "reason_tags",
    "free_note",
    "allowed_choices",
    "allowed_reason_tags",
    "free_note_example",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan A step 11: analyze_layer2.py")
    parser.add_argument("--blind-pairs", type=Path, default=BLIND_PAIRS_PATH, help="blind_eval_pairs.csv")
    parser.add_argument("--group-mapping", type=Path, default=GROUP_MAPPING_PATH, help="group_mapping_private.csv")
    parser.add_argument("--annotation", type=Path, default=LAYER2_ANN_PATH, help="layer2_annotation.csv")
    parser.add_argument("--out", type=Path, default=LAYER2_RESULT_PATH, help="layer2_results.csv")
    parser.add_argument(
        "--refresh-template",
        action="store_true",
        help="Refresh annotation helper columns while preserving existing labels",
    )
    return parser.parse_args()


def _parse_tags(tag_text: str) -> set[str]:
    if not tag_text:
        return set()
    raw = tag_text.replace("|", ",").replace(";", ",")
    return {x.strip().lower() for x in raw.split(",") if x.strip()}


def _normalize_choice(choice_text: str) -> str:
    choice = choice_text.strip().lower()
    aliases = {
        "left": "left better",
        "right": "right better",
    }
    return aliases.get(choice, choice)


def _comparison_family(comparison_type: str) -> str:
    if comparison_type.startswith("B_seed") and comparison_type.endswith("_vs_C"):
        return "B_vs_C"
    return comparison_type


def _sheet_image_path(pair_id: str) -> str:
    return (BLIND_PAIR_SHEET_DIR / f"{pair_id}.png").as_posix()


def _build_annotation_template(path: Path, pair_rows: list[dict], existing_rows: list[dict] | None = None) -> None:
    existing_by_pair = {row.get("pair_id", ""): row for row in existing_rows or []}
    rows = []
    for p in pair_rows:
        pair_id = p.get("pair_id", "")
        existing = existing_by_pair.get(pair_id, {})
        rows.append(
            {
                "pair_id": pair_id,
                "sheet_image": _sheet_image_path(pair_id),
                "evaluator_id": existing.get("evaluator_id", ""),
                "choice": existing.get("choice", ""),
                "reason_tags": existing.get("reason_tags", ""),
                "free_note": existing.get("free_note", ""),
                "allowed_choices": "|".join(CHOICES),
                "allowed_reason_tags": "|".join(REASON_TAGS),
                "free_note_example": FREE_NOTE_EXAMPLE,
            }
        )
    save_csv(path, rows, ANNOTATION_FIELDNAMES)


def main() -> None:
    args = parse_args()
    pair_rows = load_csv(args.blind_pairs)
    mapping_rows = load_csv(args.group_mapping)
    if not args.annotation.exists():
        _build_annotation_template(args.annotation, pair_rows)
        print(f"annotation template created: {args.annotation.as_posix()}")
        print("please fill labels then rerun analyze_layer2.py")
        return
    if args.refresh_template:
        existing_rows = load_csv(args.annotation)
        _build_annotation_template(args.annotation, pair_rows, existing_rows)
        print(f"annotation template refreshed: {args.annotation.as_posix()}")
        return

    ann_rows = load_csv(args.annotation)
    pair_map = {x["pair_id"]: x for x in pair_rows}
    group_map = {x["pair_id"]: x for x in mapping_rows}

    stat = defaultdict(Counter)
    for ann in ann_rows:
        pair_id = ann.get("pair_id", "")
        if pair_id not in pair_map or pair_id not in group_map:
            continue
        comparison = _comparison_family(pair_map[pair_id].get("comparison_type", ""))
        mapping = group_map[pair_id]
        left_g = mapping.get("left_true_group", "")
        right_g = mapping.get("right_true_group", "")
        choice = _normalize_choice(ann.get("choice") or "")
        tags = _parse_tags(ann.get("reason_tags", ""))
        structural_tags = tags & REASON_TAG_SET
        unknown_tags = tags - REASON_TAG_SET

        if choice in {"tie"}:
            stat[comparison]["tie_count"] += 1
        elif choice in {"unclear"}:
            stat[comparison]["unclear_count"] += 1
        elif choice in {"left better", "right better"}:
            win_group = left_g if choice == "left better" else right_g
            lose_group = right_g if choice == "left better" else left_g
            if win_group == "C":
                stat[comparison]["C_win_count"] += 1
            else:
                stat[comparison]["baseline_or_random_win_count"] += 1
            if structural_tags:
                stat[comparison]["structural_reason_count"] += 1
            for tag in REASON_TAGS:
                if tag in structural_tags:
                    stat[comparison][f"{tag}_count"] += 1
            if unknown_tags:
                stat[comparison]["unknown_reason_tag_count"] += 1
            stat[comparison]["total_binary"] += 1
            stat[comparison][f"win_{win_group}_over_{lose_group}"] += 1

    out_rows = []
    for comparison_type in sorted(stat.keys()):
        c = stat[comparison_type]
        denom = c.get("C_win_count", 0) + c.get("baseline_or_random_win_count", 0)
        out_rows.append(
            {
                "comparison_type": comparison_type,
                "C_win_count": c.get("C_win_count", 0),
                "baseline_or_random_win_count": c.get("baseline_or_random_win_count", 0),
                "tie_count": c.get("tie_count", 0),
                "unclear_count": c.get("unclear_count", 0),
                "C_win_rate": round(c.get("C_win_count", 0) / denom, 6) if denom else "",
                "structural_reason_count": c.get("structural_reason_count", 0),
                "local_detail_better_count": c.get("local_detail_better_count", 0),
                "component_structure_better_count": c.get("component_structure_better_count", 0),
                "unknown_reason_tag_count": c.get("unknown_reason_tag_count", 0),
            }
        )

    save_csv(
        args.out,
        out_rows,
        [
            "comparison_type",
            "C_win_count",
            "baseline_or_random_win_count",
            "tie_count",
            "unclear_count",
            "C_win_rate",
            "structural_reason_count",
            "local_detail_better_count",
            "component_structure_better_count",
            "unknown_reason_tag_count",
        ],
    )
    print(f"wrote layer2 results rows={len(out_rows)}: {args.out.as_posix()}")


if __name__ == "__main__":
    main()

