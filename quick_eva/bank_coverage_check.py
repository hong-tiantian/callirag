from __future__ import annotations

import argparse
from pathlib import Path

from common import BANK_COVERAGE_PATH, BANK_ENRICHED_PATH, CASE_MANIFEST_PATH, NON_TRIVIAL_PATH, load_csv, load_json, save_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan A Script 4: bank_coverage_check.py")
    parser.add_argument("--case-manifest", type=Path, default=CASE_MANIFEST_PATH, help="case_manifest.csv")
    parser.add_argument("--bank-enriched", type=Path, default=BANK_ENRICHED_PATH, help="bank_enriched.json")
    parser.add_argument("--non-trivial-json", type=Path, default=NON_TRIVIAL_PATH, help="non_trivial_components.json")
    parser.add_argument("--decomp-json", type=Path, default=Path(__file__).resolve().parents[1] / "bank" / "decomp.json")
    parser.add_argument("--out", type=Path, default=BANK_COVERAGE_PATH, help="bank_coverage.csv")
    return parser.parse_args()


def _coverage_status(shared_cnt: int, layout_cnt: int, stroke_sim_cnt: int) -> str:
    if shared_cnt >= 20 and layout_cnt >= 20:
        return "Good"
    if shared_cnt >= 5 or layout_cnt >= 5 or stroke_sim_cnt >= 10:
        return "Weak"
    return "None"


def main() -> None:
    args = parse_args()
    case_rows = load_csv(args.case_manifest)
    bank = load_json(args.bank_enriched)
    ontology = load_json(args.non_trivial_json)
    include = {x["component"] for x in ontology if x.get("include") is True}
    decomp = load_json(args.decomp_json)

    valid_bank = [x for x in bank if x.get("valid_for_retrieval") is True]
    out_rows: list[dict] = []
    for row in case_rows:
        target_char = (row.get("target_char") or "").strip()
        if not target_char:
            continue
        target_layout = row.get("layout", "")
        target_strokes = int(row.get("stroke_count") or 0)
        target_top = set((decomp.get(target_char, {}) or {}).get("top_level_components", []) or [])
        target_comps = set([c for c in (decomp.get(target_char, {}) or {}).get("leaf_components", []) or [] if c in include])
        if not target_comps:
            target_comps = set([c for c in (decomp.get(target_char, {}) or {}).get("retrieval_components", []) or [] if c in include])

        candidates = [x for x in valid_bank if x.get("character") != target_char]
        shared_count = 0
        same_layout = 0
        similar_stroke = 0
        top_level_overlap = 0
        fine_detail = 0

        for cand in candidates:
            cand_comps = set(cand.get("non_trivial_components", []) or [])
            cand_top = set(cand.get("top_level_components", []) or [])
            shared = target_comps & cand_comps
            if shared:
                shared_count += 1
            if target_layout and cand.get("layout") == target_layout:
                same_layout += 1
            c_strokes = int(cand.get("stroke_count") or 0)
            if abs(c_strokes - target_strokes) <= 5:
                similar_stroke += 1
            if target_top & cand_top:
                top_level_overlap += 1
            if shared and cand.get("layout") == target_layout and abs(c_strokes - target_strokes) <= 5:
                fine_detail += 1

        out_rows.append(
            {
                "target_char": target_char,
                "stroke_count": row.get("stroke_count", ""),
                "ids": row.get("ids", ""),
                "layout": target_layout,
                "valid_bank_size": len(candidates),
                "shared_component_candidate_count": shared_count,
                "same_layout_candidate_count": same_layout,
                "similar_stroke_count_candidate_count": similar_stroke,
                "top_level_overlap_count": top_level_overlap,
                "fine_detail_candidate_count": fine_detail,
                "coverage_status": _coverage_status(shared_count, same_layout, similar_stroke),
            }
        )

    fieldnames = [
        "target_char",
        "stroke_count",
        "ids",
        "layout",
        "valid_bank_size",
        "shared_component_candidate_count",
        "same_layout_candidate_count",
        "similar_stroke_count_candidate_count",
        "top_level_overlap_count",
        "fine_detail_candidate_count",
        "coverage_status",
    ]
    save_csv(args.out, out_rows, fieldnames)
    print(f"wrote {len(out_rows)} rows: {args.out.as_posix()}")


if __name__ == "__main__":
    main()

