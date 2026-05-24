from __future__ import annotations

import argparse
import random
from pathlib import Path

from common import (
    BANK_ENRICHED_PATH,
    CASE_MANIFEST_PATH,
    NON_TRIVIAL_PATH,
    SIM_LAYER_PATH,
    TOPK_MANIFEST_PATH,
    load_csv,
    load_json,
    save_csv,
    save_json,
    stroke_similarity,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan A step 05: retrieve_structural.py")
    parser.add_argument("--case-manifest", type=Path, default=CASE_MANIFEST_PATH, help="case_manifest.csv")
    parser.add_argument("--bank-enriched", type=Path, default=BANK_ENRICHED_PATH, help="bank_enriched.json")
    parser.add_argument("--non-trivial-json", type=Path, default=NON_TRIVIAL_PATH, help="non_trivial_components.json")
    parser.add_argument("--decomp-json", type=Path, default=Path(__file__).resolve().parents[1] / "bank" / "decomp.json")
    parser.add_argument("--sim-out", type=Path, default=SIM_LAYER_PATH, help="sim_layer.json")
    parser.add_argument("--topk-out", type=Path, default=TOPK_MANIFEST_PATH, help="retrieval_topk_manifest.csv")
    parser.add_argument("--topk", type=int, default=5, help="Top-k size")
    parser.add_argument("--seed", type=int, default=2026, help="Fixed random seed")
    return parser.parse_args()


def _score(target: dict, cand: dict) -> tuple[float, dict]:
    t_non = set(target["non_trivial_components"])
    c_non = set(cand.get("non_trivial_components", []) or [])
    shared_non = sorted(t_non & c_non)

    t_top = set(target["top_level_components"])
    c_top = set(cand.get("top_level_components", []) or [])
    shared_top = sorted(t_top & c_top)

    layout_match = 1 if target["layout"] and cand.get("layout") == target["layout"] else 0
    t_stroke = target["stroke_count"]
    c_stroke = int(cand.get("stroke_count") or 0)
    stroke_score = stroke_similarity(t_stroke, c_stroke)
    stroke_gap = abs(t_stroke - c_stroke)

    score = 3 * len(shared_non) + 2 * layout_match + 2 * len(shared_top) + 1 * stroke_score
    reason = (
        f"shared_non_trivial={shared_non}; shared_top_level={shared_top}; "
        f"layout_match={bool(layout_match)}; stroke_gap={stroke_gap}"
    )
    detail = {
        "layout_match": bool(layout_match),
        "shared_components": shared_non,
        "shared_top_level_components": shared_top,
        "stroke_count_gap": stroke_gap,
        "reason": reason,
    }
    return float(score), detail


def main() -> None:
    args = parse_args()
    case_rows = load_csv(args.case_manifest)
    bank = load_json(args.bank_enriched)
    ontology = load_json(args.non_trivial_json)
    include = {x["component"] for x in ontology if x.get("include") is True}
    decomp = load_json(args.decomp_json)

    rng = random.Random(args.seed)
    sim_out: dict[str, list[dict]] = {}
    topk_rows: list[dict] = []

    for row in case_rows:
        target_char = (row.get("target_char") or "").strip()
        if not target_char:
            continue
        target_decomp = decomp.get(target_char, {})
        target_non = [c for c in (target_decomp.get("leaf_components", []) or []) if c in include]
        if not target_non:
            target_non = [c for c in (target_decomp.get("retrieval_components", []) or []) if c in include]
        target = {
            "char": target_char,
            "layout": row.get("layout", ""),
            "stroke_count": int(row.get("stroke_count") or 0),
            "top_level_components": target_decomp.get("top_level_components", []) or [],
            "non_trivial_components": target_non,
        }

        filtered = []
        seen_paths = set()
        for cand in bank:
            if cand.get("valid_for_retrieval") is not True:
                continue
            if cand.get("character") == target_char:
                continue
            if float(cand.get("ocr_conf") or 0.0) < 0.9:
                continue
            if bool(cand.get("has_unknown")):
                continue
            wxz_path = cand.get("wxz_path")
            if not wxz_path or wxz_path in seen_paths:
                continue
            seen_paths.add(wxz_path)
            filtered.append(cand)

        scored = []
        for cand in filtered:
            score, detail = _score(target, cand)
            scored.append((score, cand, detail))
        scored.sort(key=lambda x: x[0], reverse=True)
        topk_struct = scored[: args.topk]

        sim_items = []
        for rank, (score, cand, detail) in enumerate(topk_struct, start=1):
            rec = {
                "rank": rank,
                "bank_id": cand.get("bank_id"),
                "character": cand.get("character"),
                "wxz_path": cand.get("wxz_path"),
                "score": round(score, 4),
                **detail,
            }
            sim_items.append(rec)
            topk_rows.append(
                {
                    "target_char": target_char,
                    "retrieval_type": "structural",
                    "rank": rank,
                    "bank_id": rec["bank_id"],
                    "retrieved_char": rec["character"],
                    "wxz_path": rec["wxz_path"],
                    "score": rec["score"],
                    "layout_match": rec["layout_match"],
                    "shared_components": "|".join(rec["shared_components"]),
                    "shared_top_level_components": "|".join(rec["shared_top_level_components"]),
                    "stroke_count_gap": rec["stroke_count_gap"],
                    "reason": rec["reason"],
                }
            )
        sim_out[target_char] = sim_items

        k = min(args.topk, len(filtered))
        rand_items = rng.sample(filtered, k) if k > 0 else []
        for rank, cand in enumerate(rand_items, start=1):
            _, detail = _score(target, cand)
            topk_rows.append(
                {
                    "target_char": target_char,
                    "retrieval_type": "random",
                    "rank": rank,
                    "bank_id": cand.get("bank_id"),
                    "retrieved_char": cand.get("character"),
                    "wxz_path": cand.get("wxz_path"),
                    "score": "",
                    "layout_match": detail["layout_match"],
                    "shared_components": "|".join(detail["shared_components"]),
                    "shared_top_level_components": "|".join(detail["shared_top_level_components"]),
                    "stroke_count_gap": detail["stroke_count_gap"],
                    "reason": f"uniform_sample_seed={args.seed}",
                }
            )

    save_json(args.sim_out, sim_out)
    fieldnames = [
        "target_char",
        "retrieval_type",
        "rank",
        "bank_id",
        "retrieved_char",
        "wxz_path",
        "score",
        "layout_match",
        "shared_components",
        "shared_top_level_components",
        "stroke_count_gap",
        "reason",
    ]
    save_csv(args.topk_out, topk_rows, fieldnames)
    print(f"wrote sim_layer: {args.sim_out.as_posix()}")
    print(f"wrote topk manifest rows={len(topk_rows)}: {args.topk_out.as_posix()}")


if __name__ == "__main__":
    main()

