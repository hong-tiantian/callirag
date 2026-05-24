from __future__ import annotations

import argparse
from pathlib import Path

from common import BANK_ENRICHED_PATH, CASE_MANIFEST_PATH, LAYER1_VIS_DIR, TOPK_MANIFEST_PATH, load_csv, load_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan A step 06: export_layer1_visuals.py")
    parser.add_argument("--case-manifest", type=Path, default=CASE_MANIFEST_PATH, help="case_manifest.csv")
    parser.add_argument("--topk-manifest", type=Path, default=TOPK_MANIFEST_PATH, help="retrieval_topk_manifest.csv")
    parser.add_argument("--bank-enriched", type=Path, default=BANK_ENRICHED_PATH, help="bank_enriched.json")
    parser.add_argument("--out-dir", type=Path, default=LAYER1_VIS_DIR, help="layer1_visuals output directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    case_rows = load_csv(args.case_manifest)
    topk_rows = load_csv(args.topk_manifest)
    _ = load_json(args.bank_enriched)  # keep explicit dependency per Plan A script interface

    by_target: dict[str, list[dict]] = {}
    for row in topk_rows:
        by_target.setdefault(row.get("target_char", ""), []).append(row)

    count = 0
    for case in case_rows:
        target = case.get("target_char", "")
        if not target:
            continue
        rows = by_target.get(target, [])
        rows_struct = [x for x in rows if x.get("retrieval_type") == "structural"]
        rows_rand = [x for x in rows if x.get("retrieval_type") == "random"]

        out_md = args.out_dir / f"{target}.md"
        lines = [
            f"# Layer1 Visual Pack - {target}",
            "",
            f"- target_char: `{target}`",
            f"- ids: `{case.get('ids','')}`",
            f"- layout: `{case.get('layout','')}`",
            f"- stroke_count: `{case.get('stroke_count','')}`",
            f"- baseline_output_path: `{case.get('baseline_output_path','')}`",
            f"- baseline_failure_note: `{case.get('baseline_failure_note','')}`",
            "",
            "## structural top-k",
            "",
            "| rank | bank_id | char | wxz_path | score | reason |",
            "|---:|---|---|---|---:|---|",
        ]
        for r in sorted(rows_struct, key=lambda x: int(x.get("rank") or 0)):
            lines.append(
                f"| {r.get('rank')} | {r.get('bank_id')} | {r.get('retrieved_char')} | "
                f"{r.get('wxz_path')} | {r.get('score')} | {r.get('reason')} |"
            )

        lines += [
            "",
            "## random top-k",
            "",
            "| rank | bank_id | char | wxz_path | reason |",
            "|---:|---|---|---|---|",
        ]
        for r in sorted(rows_rand, key=lambda x: int(x.get("rank") or 0)):
            lines.append(
                f"| {r.get('rank')} | {r.get('bank_id')} | {r.get('retrieved_char')} | "
                f"{r.get('wxz_path')} | {r.get('reason')} |"
            )
        out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
        count += 1

    print(f"wrote layer1 visuals for {count} targets: {args.out_dir.as_posix()}")


if __name__ == "__main__":
    main()

