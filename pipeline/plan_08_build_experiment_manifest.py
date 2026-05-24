from __future__ import annotations

import argparse
import random
from pathlib import Path

from common import (
    BANK_ENRICHED_PATH,
    CASE_MANIFEST_PATH,
    EXPERIMENT_MANIFEST_PATH,
    SIM_LAYER_PATH,
    load_csv,
    load_json,
    repo_relative_path,
    save_csv,
    stable_int,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan A step 08: build_experiment_manifest.py")
    parser.add_argument("--case-manifest", type=Path, default=CASE_MANIFEST_PATH, help="case_manifest.csv")
    parser.add_argument("--sim-layer", type=Path, default=SIM_LAYER_PATH, help="sim_layer.json")
    parser.add_argument("--bank-enriched", type=Path, default=BANK_ENRICHED_PATH, help="bank_enriched.json")
    parser.add_argument(
        "--fixed-ref-path",
        type=str,
        default="",
        help="Fixed baseline style ref path for group A. Empty means auto pick from bank.",
    )
    parser.add_argument("--fixed-ref-char", type=str, default="永", help="Fixed baseline style ref character label")
    parser.add_argument("--out", type=Path, default=EXPERIMENT_MANIFEST_PATH, help="experiment_manifest.csv")
    return parser.parse_args()


def _pick_fixed_ref(args: argparse.Namespace, bank_valid: list[dict]) -> tuple[str, str]:
    if args.fixed_ref_path:
        return args.fixed_ref_char, args.fixed_ref_path
    # fallback: first valid bank item
    for x in bank_valid:
        if x.get("wxz_path"):
            return x.get("character") or args.fixed_ref_char, x["wxz_path"]
    return args.fixed_ref_char, ""


def main() -> None:
    args = parse_args()
    case_rows = load_csv(args.case_manifest)
    sim = load_json(args.sim_layer)
    bank = load_json(args.bank_enriched)
    bank_valid = [x for x in bank if x.get("valid_for_retrieval") is True]

    fixed_char, fixed_path = _pick_fixed_ref(args, bank_valid)
    out_rows: list[dict] = []

    for case in case_rows:
        target = case.get("target_char", "")
        if not target:
            continue
        case_id = case.get("case_id", target)
        content_path = (case.get("content_path") or "").strip()
        if not content_path:
            content_path = repo_relative_path("cases", "content", f"{case_id}.jpg")
        generation_seed = 2026 + stable_int(target, 10000)

        # Group A: fixed baseline
        out_rows.append(
            {
                "target_char": target,
                "group": "A",
                "ref_char": fixed_char,
                "ref_path": fixed_path,
                "retrieval_rank": "",
                "ref_selection_seed": "",
                "generation_seed": generation_seed,
                "content_path": content_path,
                "output_path": repo_relative_path("outputs", "layer2", "generation_outputs", f"{target}_A.png"),
                "note": "fixed_baseline",
            }
        )

        # Group B: uniform random, 5 seeds
        pool = [x for x in bank_valid if x.get("character") != target]
        for seed in [0, 1, 2, 3, 4]:
            rng = random.Random(2026 + seed + stable_int(target, 1000))
            if pool:
                picked = rng.choice(pool)
                ref_char = picked.get("character", "")
                ref_path = picked.get("wxz_path", "")
            else:
                ref_char = ""
                ref_path = ""
            out_rows.append(
                {
                    "target_char": target,
                    "group": "B",
                    "ref_char": ref_char,
                    "ref_path": ref_path,
                    "retrieval_rank": "",
                    "ref_selection_seed": seed,
                    "generation_seed": generation_seed,
                    "content_path": content_path,
                    "output_path": repo_relative_path("outputs", "layer2", "generation_outputs", f"{target}_B_seed{seed}.png"),
                    "note": "uniform_random",
                }
            )

        # Group C: structural rank1
        sim_list = sim.get(target, []) or []
        rank_map = {int(x.get("rank")): x for x in sim_list if str(x.get("rank", "")).isdigit()}
        r1 = rank_map.get(1)
        if r1:
            out_rows.append(
                {
                    "target_char": target,
                    "group": "C",
                    "ref_char": r1.get("character", ""),
                    "ref_path": r1.get("wxz_path", ""),
                    "retrieval_rank": 1,
                    "ref_selection_seed": "",
                    "generation_seed": generation_seed,
                    "content_path": content_path,
                    "output_path": repo_relative_path("outputs", "layer2", "generation_outputs", f"{target}_C_rank1.png"),
                    "note": "structural_top1",
                }
            )

        # Group D: rank3 and rank5
        for rk in [3, 5]:
            item = rank_map.get(rk)
            if not item:
                continue
            out_rows.append(
                {
                    "target_char": target,
                    "group": "D",
                    "ref_char": item.get("character", ""),
                    "ref_path": item.get("wxz_path", ""),
                    "retrieval_rank": rk,
                    "ref_selection_seed": "",
                    "generation_seed": generation_seed,
                    "content_path": content_path,
                    "output_path": repo_relative_path("outputs", "layer2", "generation_outputs", f"{target}_D_rank{rk}.png"),
                    "note": "rank_ablation",
                }
            )

    save_csv(
        args.out,
        out_rows,
        [
            "target_char",
            "group",
            "ref_char",
            "ref_path",
            "retrieval_rank",
            "ref_selection_seed",
            "generation_seed",
            "content_path",
            "output_path",
            "note",
        ],
    )
    print(f"wrote experiment manifest rows={len(out_rows)}: {args.out.as_posix()}")


if __name__ == "__main__":
    main()

