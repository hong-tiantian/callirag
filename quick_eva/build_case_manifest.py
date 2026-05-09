from __future__ import annotations

import argparse
from pathlib import Path

from common import CASES_DIR, CASE_MANIFEST_PATH, LEGACY_OUTPUTS_DIR, ROOT, load_csv, load_json, repo_relative_path, save_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan A Script 1: build_case_manifest.py")
    parser.add_argument(
        "--case-assets-csv",
        type=Path,
        default=CASES_DIR / "case_assets_15.csv",
        help="Preferred case asset mapping CSV (case_id, target_char, ...).",
    )
    parser.add_argument(
        "--target-csv",
        type=Path,
        default=ROOT / "cases" / "wxz_gt_chars.csv",
        help="Target list CSV with columns: 编号, 字符",
    )
    parser.add_argument(
        "--decomp-json",
        type=Path,
        default=ROOT / "bank" / "decomp.json",
        help="Decomposition json used for ids/layout/strokes",
    )
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        default=CASES_DIR / "baseline",
        help="Baseline output root (prefer callirag/cases/baseline)",
    )
    parser.add_argument("--out", type=Path, default=CASE_MANIFEST_PATH, help="Output case_manifest.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    use_assets = args.case_assets_csv.exists()
    rows_in = load_csv(args.case_assets_csv if use_assets else args.target_csv)
    decomp = load_json(args.decomp_json)
    repo_root = ROOT.parent

    rows_out: list[dict] = []
    for row in rows_in:
        target_char = (row.get("target_char") or row.get("字符") or "").strip()
        case_id = (row.get("case_id") or row.get("编号") or "").strip()
        if not target_char:
            continue

        d = decomp.get(target_char, {})
        baseline_single = args.baseline_dir / case_id / "out_single.png"
        baseline_with_cs = args.baseline_dir / case_id / "out_with_cs.jpg"
        # Backward-compat fallback for old layout under outputs/baseline.
        old_baseline_single = LEGACY_OUTPUTS_DIR / "baseline" / case_id / "out_single.png"
        old_baseline_with_cs = LEGACY_OUTPUTS_DIR / "baseline" / case_id / "out_with_cs.jpg"
        if baseline_single.exists():
            baseline_path = baseline_single.relative_to(repo_root).as_posix()
        elif baseline_with_cs.exists():
            baseline_path = baseline_with_cs.relative_to(repo_root).as_posix()
        elif old_baseline_single.exists():
            baseline_path = old_baseline_single.relative_to(repo_root).as_posix()
        elif old_baseline_with_cs.exists():
            baseline_path = old_baseline_with_cs.relative_to(repo_root).as_posix()
        else:
            baseline_path = ""
        content_path = repo_relative_path("cases", "content", f"{case_id}.jpg")

        rows_out.append(
            {
                "target_char": target_char,
                "stroke_count": d.get("stroke_count", ""),
                "ids": d.get("ids", ""),
                "layout": d.get("layout", ""),
                "baseline_readable": "yes",
                "baseline_failure_type": "local_detail_collapse",
                "baseline_failure_note": "",
                "selection_reason": "manual_baseline_inspection",
                "case_id": case_id,
                "content_path": content_path,
                "baseline_output_path": baseline_path,
            }
        )

    fieldnames = [
        "target_char",
        "stroke_count",
        "ids",
        "layout",
        "baseline_readable",
        "baseline_failure_type",
        "baseline_failure_note",
        "selection_reason",
        "case_id",
        "content_path",
        "baseline_output_path",
    ]
    save_csv(args.out, rows_out, fieldnames)
    print(f"wrote {len(rows_out)} rows: {args.out.as_posix()}")


if __name__ == "__main__":
    main()

