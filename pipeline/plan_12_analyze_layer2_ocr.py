from __future__ import annotations

import argparse
import statistics
from collections import defaultdict
from pathlib import Path

from paddleocr import PaddleOCR

from common import EXPERIMENT_MANIFEST_PATH, REPO_ROOT, load_csv, save_csv


GROUP_MAP = {
    "A": "A",
    "B": "B",
    "C": "C",
    "D": "D",
    "fixed_baseline": "A",
    "uniform_random": "B",
    "structural_top1": "C",
    "rank_ablation": "D",
}
GROUP_ORDER = ("A", "B", "C", "D")
DETAIL_FIELDS = ["target_char", "group", "output_path", "ocr_top1", "ocr_confidence", "ocr_correct"]
DEBUG_FIELDS = DETAIL_FIELDS + ["ocr_raw_text"]
SUMMARY_FIELDS = [
    "group",
    "n_samples",
    "ocr_top1_accuracy",
    "mean_ocr_confidence",
    "median_ocr_confidence",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan A optional step 12: Layer2 OCR top-1 analysis by A/B/C/D groups")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=EXPERIMENT_MANIFEST_PATH,
        help="Input experiment_manifest.csv",
    )
    parser.add_argument(
        "--detail-out",
        type=Path,
        default=REPO_ROOT / "callirag" / "metrics" / "layer2_ocr_detail.csv",
        help="Detail csv output path (6 required columns)",
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=REPO_ROOT / "callirag" / "metrics" / "layer2_ocr_summary_by_group.csv",
        help="Summary csv output path",
    )
    parser.add_argument(
        "--debug-out",
        type=Path,
        default=REPO_ROOT / "callirag" / "metrics" / "layer2_ocr_debug.csv",
        help="Optional debug csv output path (includes ocr_raw_text)",
    )
    parser.add_argument(
        "--write-debug",
        action="store_true",
        help="Write debug csv with ocr_raw_text",
    )
    return parser.parse_args()


def _normalize_group(raw_group: str, raw_note: str) -> str:
    group = (raw_group or "").strip()
    note = (raw_note or "").strip()
    if group in GROUP_MAP:
        return GROUP_MAP[group]
    if note in GROUP_MAP:
        return GROUP_MAP[note]
    return group


def _resolve_image_path(path_text: str) -> Path:
    raw = (path_text or "").strip()
    if not raw:
        return Path("")
    p = Path(raw)
    if p.is_absolute():
        return p
    return REPO_ROOT / raw


def _run_ocr(ocr: PaddleOCR, image_path: Path) -> tuple[str, str, str]:
    if not image_path.exists():
        return "", "", ""

    result = ocr.predict(str(image_path))
    if not result:
        return "", "", ""

    rec = result[0] or {}
    texts = rec.get("rec_texts", []) or []
    scores = rec.get("rec_scores", []) or []
    if not texts:
        return "", "", ""

    raw_text = str(texts[0]) if texts[0] is not None else ""
    top1 = raw_text[:1] if raw_text else ""

    conf = ""
    if scores:
        try:
            conf = f"{float(scores[0]):.6f}"
        except (ValueError, TypeError):
            conf = ""

    return top1, conf, raw_text


def _safe_float(value: str) -> float | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def main() -> None:
    args = parse_args()
    rows = load_csv(args.manifest)
    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        lang="ch",
        enable_mkldnn=False,
    )

    detail_rows: list[dict] = []
    debug_rows: list[dict] = []
    missing_count = 0

    for row in rows:
        target_char = (row.get("target_char") or "").strip()
        group = _normalize_group(row.get("group", ""), row.get("note", ""))
        output_path = (row.get("output_path") or "").strip()
        image_path = _resolve_image_path(output_path)

        if not image_path.exists():
            missing_count += 1

        ocr_top1, ocr_confidence, ocr_raw_text = _run_ocr(ocr, image_path)
        ocr_correct = "1" if ocr_top1 == target_char and target_char else "0"

        detail_rows.append(
            {
                "target_char": target_char,
                "group": group,
                "output_path": output_path,
                "ocr_top1": ocr_top1,
                "ocr_confidence": ocr_confidence,
                "ocr_correct": ocr_correct,
            }
        )
        debug_rows.append(
            {
                "target_char": target_char,
                "group": group,
                "output_path": output_path,
                "ocr_top1": ocr_top1,
                "ocr_confidence": ocr_confidence,
                "ocr_correct": ocr_correct,
                "ocr_raw_text": ocr_raw_text,
            }
        )

    save_csv(args.detail_out, detail_rows, DETAIL_FIELDS)
    if args.write_debug:
        save_csv(args.debug_out, debug_rows, DEBUG_FIELDS)

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in detail_rows:
        grouped[(row.get("group") or "").strip()].append(row)

    summary_rows: list[dict] = []
    for group in GROUP_ORDER:
        items = grouped.get(group, [])
        n_samples = len(items)
        if n_samples == 0:
            summary_rows.append(
                {
                    "group": group,
                    "n_samples": "0",
                    "ocr_top1_accuracy": "",
                    "mean_ocr_confidence": "",
                    "median_ocr_confidence": "",
                }
            )
            continue

        correct_sum = sum(int(x.get("ocr_correct", "0") or "0") for x in items)
        confs = [_safe_float(x.get("ocr_confidence", "")) for x in items]
        conf_values = [x for x in confs if x is not None]

        mean_conf = f"{statistics.fmean(conf_values):.6f}" if conf_values else ""
        median_conf = f"{statistics.median(conf_values):.6f}" if conf_values else ""

        summary_rows.append(
            {
                "group": group,
                "n_samples": str(n_samples),
                "ocr_top1_accuracy": f"{(correct_sum / n_samples):.6f}",
                "mean_ocr_confidence": mean_conf,
                "median_ocr_confidence": median_conf,
            }
        )

    save_csv(args.summary_out, summary_rows, SUMMARY_FIELDS)

    print(f"manifest rows={len(rows)}")
    print(f"missing image count={missing_count}")
    print(f"detail written: {args.detail_out.as_posix()}")
    print(f"summary written: {args.summary_out.as_posix()}")
    if args.write_debug:
        print(f"debug written: {args.debug_out.as_posix()}")


if __name__ == "__main__":
    main()
