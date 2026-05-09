from __future__ import annotations

import argparse
from pathlib import Path

from common import LAYER1_ANN_PATH, LAYER1_RESULT_PATH, TOPK_MANIFEST_PATH, load_csv, save_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan A Script 7: analyze_layer1.py")
    parser.add_argument("--annotation", type=Path, default=LAYER1_ANN_PATH, help="layer1_annotation.csv")
    parser.add_argument("--topk-manifest", type=Path, default=TOPK_MANIFEST_PATH, help="retrieval_topk_manifest.csv")
    parser.add_argument("--out", type=Path, default=LAYER1_RESULT_PATH, help="layer1_results.csv")
    return parser.parse_args()


def _to_bool(v: str | None) -> bool:
    s = (v or "").strip().lower()
    return s in {"1", "true", "yes", "y"}


def _build_template(path: Path, topk_rows: list[dict]) -> None:
    template = []
    for r in topk_rows:
        template.append(
            {
                "target_char": r.get("target_char", ""),
                "retrieval_type": r.get("retrieval_type", ""),
                "rank": r.get("rank", ""),
                "bank_id": r.get("bank_id", ""),
                "retrieved_char": r.get("retrieved_char", ""),
                "contains_key_component": "",
                "layout_match": "",
                "fine_detail_relevant": "",
                "dense_region_match": "",
                "useful_for_failure_note": "",
                "annotation_note": "",
            }
        )
    fieldnames = [
        "target_char",
        "retrieval_type",
        "rank",
        "bank_id",
        "retrieved_char",
        "contains_key_component",
        "layout_match",
        "fine_detail_relevant",
        "dense_region_match",
        "useful_for_failure_note",
        "annotation_note",
    ]
    save_csv(path, template, fieldnames)


def _metric(rows: list[dict], metric_col: str, k: int) -> tuple[int, int]:
    subset = [r for r in rows if int(r.get("rank") or 0) <= k]
    if not subset:
        return 0, 0
    num = sum(1 for r in subset if _to_bool(r.get(metric_col)))
    return num, len(subset)


def main() -> None:
    args = parse_args()
    topk_rows = load_csv(args.topk_manifest)
    if not args.annotation.exists():
        _build_template(args.annotation, topk_rows)
        print(f"annotation template created: {args.annotation.as_posix()}")
        print("please fill labels then rerun analyze_layer1.py")
        return

    ann = load_csv(args.annotation)
    results = []
    for retrieval_type in ["structural", "random"]:
        rows_t = [r for r in ann if r.get("retrieval_type") == retrieval_type]
        for k in [1, 3, 5]:
            for metric_name, col in [
                ("component_hit_rate", "contains_key_component"),
                ("layout_match_rate", "layout_match"),
                ("fine_detail_relevance_rate", "useful_for_failure_note"),
            ]:
                num, den = _metric(rows_t, col, k)
                results.append(
                    {
                        "retrieval_type": retrieval_type,
                        "metric": metric_name,
                        "k": k,
                        "numerator": num,
                        "denominator": den,
                        "value": round(num / den, 6) if den else "",
                    }
                )

    save_csv(
        args.out,
        results,
        ["retrieval_type", "metric", "k", "numerator", "denominator", "value"],
    )
    print(f"wrote layer1 results: {args.out.as_posix()}")


if __name__ == "__main__":
    main()

