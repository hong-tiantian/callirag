from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from common import NON_TRIVIAL_PATH, STROKE_LEVEL_UNITS, load_json, ordered_unique, save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan A step 02: build_non_trivial_components.py")
    parser.add_argument(
        "--bank-json",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "bank" / "wxz_bank.json",
        help="wxz_bank.json path",
    )
    parser.add_argument("--out", type=Path, default=NON_TRIVIAL_PATH, help="Output json path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bank = load_json(args.bank_json)

    retrieval_counter: Counter[str] = Counter()
    leaf_counter: Counter[str] = Counter()

    for row in bank:
        retrieval = row.get("retrieval_components", []) or []
        leaves = row.get("leaf_components", []) or []
        for c in retrieval:
            if isinstance(c, str) and c:
                retrieval_counter[c] += 1
        for c in leaves:
            if isinstance(c, str) and c:
                leaf_counter[c] += 1

    components = ordered_unique(
        list(retrieval_counter.keys()) + [c for c in leaf_counter.keys() if c not in retrieval_counter]
    )

    out = []
    for comp in components:
        is_stroke = comp in STROKE_LEVEL_UNITS
        source = "retrieval_components" if comp in retrieval_counter else "leaf_components"
        out.append(
            {
                "component": comp,
                "level": "stroke" if is_stroke else "component",
                "source": source,
                "include": not is_stroke,
                "note": "leaf stroke-level unit" if is_stroke else "meaningful radical/component",
                "freq_retrieval": retrieval_counter.get(comp, 0),
                "freq_leaf": leaf_counter.get(comp, 0),
            }
        )

    save_json(args.out, out)
    n_include = sum(1 for x in out if x["include"])
    print(f"wrote {len(out)} components ({n_include} include=true): {args.out.as_posix()}")


if __name__ == "__main__":
    main()

