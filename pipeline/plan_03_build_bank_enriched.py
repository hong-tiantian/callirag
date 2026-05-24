from __future__ import annotations

import argparse
from pathlib import Path

from common import BANK_ENRICHED_PATH, NON_TRIVIAL_PATH, is_existing_image, load_json, ordered_unique, save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan A step 03: build_bank_enriched.py")
    parser.add_argument(
        "--bank-json",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "bank" / "wxz_bank.json",
        help="Original bank json path",
    )
    parser.add_argument(
        "--non-trivial-json",
        type=Path,
        default=NON_TRIVIAL_PATH,
        help="non_trivial_components.json path",
    )
    parser.add_argument(
        "--strict-image-check",
        action="store_true",
        help="If set, wxz image must exist locally to be valid_for_retrieval",
    )
    parser.add_argument("--out", type=Path, default=BANK_ENRICHED_PATH, help="Output bank_enriched.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bank = load_json(args.bank_json)
    ontology = load_json(args.non_trivial_json)
    include_set = {x["component"] for x in ontology if x.get("include") is True}

    enriched = []
    valid_count = 0
    for row in bank:
        rec = dict(row)
        comp_candidates = (row.get("retrieval_components", []) or []) + (row.get("top_level_components", []) or [])
        comp_candidates += row.get("leaf_components", []) or []
        non_trivial_components = [c for c in ordered_unique(comp_candidates) if c in include_set]

        reasons = []
        image_exists = is_existing_image(rec.get("wxz_path"))
        if not rec.get("character"):
            reasons.append("character_null")
        if float(rec.get("ocr_conf") or 0.0) < 0.9:
            reasons.append("ocr_conf_below_0.9")
        if bool(rec.get("has_unknown")):
            reasons.append("has_unknown_true")
        if not rec.get("wxz_path"):
            reasons.append("wxz_path_missing")
        elif args.strict_image_check and not image_exists:
            reasons.append("wxz_image_not_found")

        valid = len(reasons) == 0
        if valid:
            valid_count += 1

        rec["non_trivial_components"] = non_trivial_components
        rec["image_exists_local"] = image_exists
        rec["valid_for_retrieval"] = valid
        rec["exclude_reason"] = None if valid else ";".join(reasons)
        enriched.append(rec)

    save_json(args.out, enriched)
    print(f"wrote {len(enriched)} entries: {args.out.as_posix()}")
    print(f"valid_for_retrieval=true: {valid_count}")


if __name__ == "__main__":
    main()

