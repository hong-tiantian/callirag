#!/usr/bin/env python3
"""Random baseline for retrieval component coverage comparison.

Usage:  python 8random_baseline.py
Outputs:
  - retrieval_data_prepare/outputs/random_baseline_results.json
  - retrieval_data_prepare/random_vs_structural_summary.md
"""

from __future__ import annotations

import importlib.util
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "bank" / "wxz_bank.json"
STRUCTURAL_REPORT_PATH = ROOT / "bank" / "RETRIEVAL_TEST.md"
OUTPUT_JSON_PATH = ROOT / "outputs" / "random_baseline_results.json"
OUTPUT_MD_PATH = ROOT / "random_vs_structural_summary.md"

TARGET_CHARS = ["璨", "霆", "鳞", "彎", "瘻", "秦", "赢", "諢"]
N_SEEDS = 30
SAMPLE_SIZE = 5


def _load_retrieve6_module():
    p = ROOT / "pipeline" / "6retrieve.py"
    spec = importlib.util.spec_from_file_location("_retrieve6", str(p))
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_r6 = _load_retrieve6_module()


def _parse_structural_report(report_text: str) -> dict[str, dict]:
    structural: dict[str, dict] = {}
    lines = report_text.splitlines()

    for ch in TARGET_CHARS:
        header = f"## {ch}"
        if header not in lines:
            raise RuntimeError(f"Cannot find section header '{header}' in structural report.")

        start = lines.index(header)
        end = len(lines)
        for i in range(start + 1, len(lines)):
            if lines[i].startswith("## "):
                end = i
                break
        sec = lines[start:end]

        target_line = next(
            (ln for ln in sec if ln.startswith("- target retrieval_components: ")),
            None,
        )
        if target_line is None:
            raise RuntimeError(f"Cannot find target retrieval components for '{ch}'.")
        target_comps = json.loads(target_line.split("`")[1].replace("'", '"'))

        marker = "**NEW component coverage (per retrieval_component):**"
        if marker not in sec:
            raise RuntimeError(f"Cannot find NEW component coverage block for '{ch}'.")
        m_idx = sec.index(marker)
        cov_lines = []
        for ln in sec[m_idx + 1:]:
            if not ln.startswith("- `"):
                break
            cov_lines.append(ln)
        if not cov_lines:
            raise RuntimeError(f"Empty NEW component coverage block for '{ch}'.")

        structural_covered = []
        for comp in target_comps:
            prefix = f"- `{comp}`:"
            line = next((ln for ln in cov_lines if ln.startswith(prefix)), None)
            if line is None:
                raise RuntimeError(
                    f"Component '{comp}' not found in NEW component coverage for '{ch}'."
                )
            if "✓" in line:
                structural_covered.append(comp)

        structural_rate = len(structural_covered) / len(target_comps)
        structural[ch] = {
            "target_components": target_comps,
            "covered_components": structural_covered,
            "rate": structural_rate,
        }
    return structural


def _candidate_pool(bank: list[dict], target_char: str, ocr_conf_min: float = 0.9) -> list[dict]:
    # Keep the exact same filter pipeline ordering as 6retrieve.py
    after_ocr = [c for c in bank if (c.get("ocr_conf") or 0) >= ocr_conf_min]
    after_self = [c for c in after_ocr if c.get("character") != target_char]
    after_unk = [
        c
        for c in after_self
        if not (
            c.get("has_unknown") is True
            and c.get("retrieval_components") == [c.get("character")]
        )
    ]
    return after_unk


def main() -> None:
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    report_text = STRUCTURAL_REPORT_PATH.read_text(encoding="utf-8")

    structural = _parse_structural_report(report_text)

    results: dict = {
        "n_seeds": N_SEEDS,
        "sample_size": SAMPLE_SIZE,
        "seeds": list(range(N_SEEDS)),
        "targets": {},
    }

    summary_lines = [
        "| target | target_comps | structural_rate | random_mean | random_std | random_max | delta(struct-mean) |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]

    for ch in TARGET_CHARS:
        target_comps = list(structural[ch]["target_components"])
        pool = _candidate_pool(bank, ch, ocr_conf_min=0.9)

        per_seed_runs: list[dict] = []
        per_comp_hit_counts: dict[str, int] = {c: 0 for c in target_comps}
        rates: list[float] = []

        for seed in range(N_SEEDS):
            rng = random.Random(seed)
            random_refs = rng.sample(pool, SAMPLE_SIZE)

            seen_components: set[str] = set()
            for ref in random_refs:
                seen_components.update(ref["retrieval_components"])

            covered = [c for c in target_comps if c in seen_components]
            uncovered = [c for c in target_comps if c not in seen_components]
            for c in covered:
                per_comp_hit_counts[c] += 1

            rate = len(covered) / len(target_comps)
            rates.append(rate)

            per_seed_runs.append({
                "seed": seed,
                "refs": [
                    {
                        "bank_id": r["bank_id"],
                        "char": r["character"],
                        "retrieval_components": r["retrieval_components"],
                        "layout": r["layout"],
                        "strokes": r["stroke_count"],
                        "wxz_path": r["wxz_path"],
                    }
                    for r in random_refs
                ],
                "covered_components": covered,
                "uncovered_components": uncovered,
                "coverage_rate": rate,
            })

        mean_rate = statistics.mean(rates)
        std_rate = statistics.pstdev(rates) if len(rates) > 1 else 0.0
        max_rate = max(rates)
        min_rate = min(rates)
        structural_rate = structural[ch]["rate"]
        per_comp_hit_prob = {c: per_comp_hit_counts[c] / N_SEEDS for c in target_comps}

        results["targets"][ch] = {
            "target_retrieval_components": target_comps,
            "pool_size": len(pool),
            "structural_rate": structural_rate,
            "structural_covered": structural[ch]["covered_components"],
            "random_rate_mean": mean_rate,
            "random_rate_std": std_rate,
            "random_rate_min": min_rate,
            "random_rate_max": max_rate,
            "per_component_hit_prob": per_comp_hit_prob,
            "per_seed_runs": per_seed_runs,
        }

        summary_lines.append(
            f"| {ch} | {target_comps} | {structural_rate:.4f} | "
            f"{mean_rate:.4f} | {std_rate:.4f} | {max_rate:.4f} | "
            f"{structural_rate - mean_rate:+.4f} |"
        )
        print(
            f"{ch}: struct={structural_rate:.4f}  "
            f"rand_mean={mean_rate:.4f}  rand_std={std_rate:.4f}  "
            f"rand_max={max_rate:.4f}  delta={structural_rate - mean_rate:+.4f}"
        )

    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    OUTPUT_MD_PATH.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(f"Random baseline JSON written to: {OUTPUT_JSON_PATH}")
    print(f"Summary markdown written to: {OUTPUT_MD_PATH}")


if __name__ == "__main__":
    main()
