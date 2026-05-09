from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from common import BLIND_PAIRS_PATH, GROUP_MAPPING_PATH, LAYER2_ANN_PATH, LAYER2_RESULT_PATH, load_csv, save_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan A Script 11: analyze_layer2.py")
    parser.add_argument("--blind-pairs", type=Path, default=BLIND_PAIRS_PATH, help="blind_eval_pairs.csv")
    parser.add_argument("--group-mapping", type=Path, default=GROUP_MAPPING_PATH, help="group_mapping_private.csv")
    parser.add_argument("--annotation", type=Path, default=LAYER2_ANN_PATH, help="layer2_annotation.csv")
    parser.add_argument("--out", type=Path, default=LAYER2_RESULT_PATH, help="layer2_results.csv")
    return parser.parse_args()


def _parse_tags(tag_text: str) -> set[str]:
    if not tag_text:
        return set()
    raw = tag_text.replace("|", ",").replace(";", ",")
    return {x.strip().lower() for x in raw.split(",") if x.strip()}


def _build_annotation_template(path: Path, pair_rows: list[dict]) -> None:
    rows = []
    for p in pair_rows:
        rows.append(
            {
                "pair_id": p.get("pair_id", ""),
                "evaluator_id": "",
                "choice": "",
                "reason_tags": "",
                "free_note": "",
            }
        )
    save_csv(path, rows, ["pair_id", "evaluator_id", "choice", "reason_tags", "free_note"])


def main() -> None:
    args = parse_args()
    pair_rows = load_csv(args.blind_pairs)
    mapping_rows = load_csv(args.group_mapping)
    if not args.annotation.exists():
        _build_annotation_template(args.annotation, pair_rows)
        print(f"annotation template created: {args.annotation.as_posix()}")
        print("please fill labels then rerun analyze_layer2.py")
        return

    ann_rows = load_csv(args.annotation)
    pair_map = {x["pair_id"]: x for x in pair_rows}
    group_map = {x["pair_id"]: x for x in mapping_rows}

    stat = defaultdict(Counter)
    for ann in ann_rows:
        pair_id = ann.get("pair_id", "")
        if pair_id not in pair_map or pair_id not in group_map:
            continue
        comparison = pair_map[pair_id].get("comparison_type", "")
        mapping = group_map[pair_id]
        left_g = mapping.get("left_true_group", "")
        right_g = mapping.get("right_true_group", "")
        choice = (ann.get("choice") or "").strip().lower()
        tags = _parse_tags(ann.get("reason_tags", ""))
        style_only = tags == {"style preference only"}
        has_structural_reason = bool(tags - {"style preference only"})

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
            if has_structural_reason:
                stat[comparison]["structural_reason_count"] += 1
            if style_only:
                stat[comparison]["style_only_count"] += 1
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
                "style_only_count": c.get("style_only_count", 0),
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
            "style_only_count",
        ],
    )
    print(f"wrote layer2 results rows={len(out_rows)}: {args.out.as_posix()}")


if __name__ == "__main__":
    main()

