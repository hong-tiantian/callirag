#!/usr/bin/env python3
"""
Translate raw retrieval cache into adapter dataloader cache.

IMPORTANT:
- LAYOUT_TO_OUTER_ID is a fixed, explicit mapping.
- Future new layout values must be added to this table manually.
- Dynamic layout-to-id mapping is forbidden.
"""
from __future__ import annotations

import json
import random
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


NUM_OUTER = 13
MAX_SLOTS = 3
SLOT_NONE = 39  # = NUM_OUTER * MAX_SLOTS
ROLE_ANCHOR = 0
ROLE_COVERAGE = 1
ROLE_PAD = 2
K_MAX = 5
TRUNCATION_SEED = 42

LAYOUT_TO_OUTER_ID = {
    "⿰": 0,
    "⿱": 1,
    "⿸": 2,
    "": 3,
    "⿺": 4,
    "⿳": 5,
    "⿹": 6,
    "⿵": 7,
    "⿻": 8,
    "⿲": 9,
    "⿴": 10,
    "⿷": 11,
    "⿶": 12,
}

LAYOUT_NOMINAL_SLOTS = {
    "⿰": 2,
    "⿱": 2,
    "⿸": 2,
    "⿹": 2,
    "⿺": 2,
    "⿻": 2,
    "⿵": 2,
    "⿶": 2,
    "⿷": 2,
    "⿴": 2,
    "⿲": 3,
    "⿳": 3,
    "": 0,
}


ROOT = Path(__file__).resolve().parents[1]
RAW_CACHE = ROOT / "outputs" / "train_retrieval_cache_raw.jsonl"
BANK_PATH = ROOT / "bank" / "wxz_bank.json"
OUT_CACHE = ROOT / "outputs" / "train_retrieval_cache.jsonl"
OUT_ANOMALY = ROOT / "outputs" / "decomp_anomaly.json"
OUT_STATS = ROOT / "outputs" / "translate_stats.json"


def parse_slot_name(slot_name: str) -> tuple[str | None, str | None]:
    # expected: slot_{idx}:{role}:{matched_comp}
    parts = slot_name.split(":", 2)
    if len(parts) != 3:
        return None, None
    _, role_name, matched_comp = parts
    return role_name, matched_comp


def deterministic_truncate(refs: list[dict], k_max: int, seed: int) -> list[dict]:
    if len(refs) <= k_max:
        return list(refs)
    rng = random.Random(seed)
    indexed = list(enumerate(refs))
    group = defaultdict(list)
    for idx, ref in indexed:
        group[ref.get("role_name", "")].append((idx, ref))
    anchors = group.get("anchor", [])
    coverages = group.get("coverage", [])
    others = [x for role, vals in group.items() if role not in {"anchor", "coverage"} for x in vals]
    kept: list[tuple[int, dict]] = []
    # Keep coverage first, then others, then anchors.
    for block in (coverages, others, anchors):
        if not block:
            continue
        rng.shuffle(block)
        need = k_max - len(kept)
        if need <= 0:
            break
        kept.extend(block[:need])
    kept.sort(key=lambda x: x[0])
    return [ref for _, ref in kept]


def main() -> None:
    t0 = time.time()
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    path_to_bank = {e.get("wxz_path"): e for e in bank if e.get("wxz_path")}
    char_to_bank = {}
    for e in bank:
        ch = e.get("character")
        if ch and ch not in char_to_bank:
            char_to_bank[ch] = e

    anomalies: list[dict] = []
    translated: list[dict] = []
    slot_id_dist = Counter()
    role_id_dist = Counter()
    target_struct_dist = Counter()
    slot_none_count = 0
    leaf_match_loss_chars = 0

    with RAW_CACHE.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    n_input = 0
    metadata_in = None
    if lines:
        first = json.loads(lines[0])
        if "_metadata" in first:
            metadata_in = first["_metadata"]
            data_lines = lines[1:]
        else:
            data_lines = lines
    else:
        data_lines = []

    for line in data_lines:
        n_input += 1
        try:
            row = json.loads(line)
            ch = row.get("char")
            if not ch:
                anomalies.append({"type": "missing_char", "raw": row})
                continue

            bank_entry = char_to_bank.get(ch)
            if bank_entry is None:
                anomalies.append({"type": "char_not_in_bank", "char": ch})
                continue

            layout = bank_entry.get("layout", "")
            top_levels = list(bank_entry.get("top_level_components", []) or [])
            if layout not in LAYOUT_TO_OUTER_ID:
                anomalies.append(
                    {"type": "unknown_layout", "char": ch, "layout": layout, "top_level_components": top_levels}
                )
                continue

            expected_len = LAYOUT_NOMINAL_SLOTS[layout]
            actual_len = len(top_levels)
            if actual_len != expected_len:
                anomalies.append(
                    {
                        "type": "decomp_anomaly",
                        "char": ch,
                        "layout": layout,
                        "top_level_components": top_levels,
                        "actual_len": actual_len,
                        "expected_len": expected_len,
                    }
                )
                continue

            target_struct = LAYOUT_TO_OUTER_ID[layout]
            refs_raw = row.get("refs")
            if not isinstance(refs_raw, list):
                anomalies.append({"type": "missing_refs", "char": ch, "raw": row})
                continue

            parsed_refs: list[dict] = []
            allocated = set()
            char_has_slot_none = False

            for idx, ref in enumerate(refs_raw):
                if not isinstance(ref, dict):
                    anomalies.append({"type": "invalid_ref_type", "char": ch, "index": idx, "ref": ref})
                    continue

                role_name = None
                matched_comp = None
                if isinstance(ref.get("slot_name"), str):
                    role_from_slot, comp_from_slot = parse_slot_name(ref["slot_name"])
                    role_name = role_from_slot
                    matched_comp = comp_from_slot

                if role_name is None:
                    role_name = ref.get("role_name")

                if role_name == "exemplar":
                    role_name = "coverage"

                if role_name not in {"anchor", "coverage"}:
                    anomalies.append(
                        {
                            "type": "missing_or_invalid_role",
                            "char": ch,
                            "ref_index": idx,
                            "ref": ref,
                        }
                    )
                    continue

                if matched_comp is None:
                    anomalies.append(
                        {
                            "type": "missing_matched_comp",
                            "char": ch,
                            "ref_index": idx,
                            "ref": ref,
                        }
                    )
                    continue

                indices = [i for i, c in enumerate(top_levels) if c == matched_comp]
                if indices:
                    chosen = next((i for i in indices if i not in allocated), indices[0])
                    allocated.add(chosen)
                    slot_id = target_struct * MAX_SLOTS + chosen
                else:
                    chosen = None
                    slot_id = SLOT_NONE
                    char_has_slot_none = True

                role_id = ROLE_ANCHOR if role_name == "anchor" else ROLE_COVERAGE

                wxz_path = ref.get("path")
                ref_char = None
                if wxz_path in path_to_bank:
                    ref_char = path_to_bank[wxz_path].get("character")
                else:
                    anomalies.append(
                        {
                            "type": "path_not_in_bank",
                            "char": ch,
                            "ref_index": idx,
                            "path": wxz_path,
                        }
                    )

                parsed_refs.append(
                    {
                        "slot_id": slot_id,
                        "slot_index": chosen,
                        "role_id": role_id,
                        "role_name": role_name,
                        "matched_comp": matched_comp,
                        "char": ref_char,
                        "wxz_path": wxz_path,
                    }
                )

            if not parsed_refs:
                anomalies.append({"type": "empty_refs_after_parse", "char": ch})
                continue

            truncated = deterministic_truncate(parsed_refs, K_MAX, TRUNCATION_SEED)

            if not truncated:
                anomalies.append({"type": "empty_refs_after_truncate", "char": ch})
                continue

            k_actual = len(truncated)
            ref_mask = [True] * k_actual
            refs_final = list(truncated)
            while len(refs_final) < K_MAX:
                refs_final.append(
                    {
                        "slot_id": SLOT_NONE,
                        "slot_index": None,
                        "role_id": ROLE_PAD,
                        "role_name": "pad",
                        "matched_comp": None,
                        "char": None,
                        "wxz_path": None,
                    }
                )
                ref_mask.append(False)

            if not any(ref_mask):
                anomalies.append({"type": "all_pad_after_padding", "char": ch})
                continue

            slot_ids = [r["slot_id"] for r in refs_final]
            role_ids = [r["role_id"] for r in refs_final]

            if char_has_slot_none:
                leaf_match_loss_chars += 1

            for sid in slot_ids:
                slot_id_dist[sid] += 1
                if sid == SLOT_NONE:
                    slot_none_count += 1
            for rid in role_ids:
                role_id_dist[rid] += 1
            target_struct_dist[target_struct] += 1

            translated.append(
                {
                    "char": ch,
                    "target_struct": target_struct,
                    "k_actual": k_actual,
                    "ref_mask": ref_mask,
                    "slot_ids": slot_ids,
                    "role_ids": role_ids,
                    "refs": refs_final,
                }
            )
        except Exception as e:  # noqa: BLE001
            anomalies.append({"type": "exception", "error": repr(e), "raw_line": line})

    meta_out = {
        "_metadata": {
            "num_outer": NUM_OUTER,
            "max_slots": MAX_SLOTS,
            "slot_none": SLOT_NONE,
            "k_max": K_MAX,
            "truncation_seed": TRUNCATION_SEED,
            "layout_to_outer_id": LAYOUT_TO_OUTER_ID,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_raw_cache": str(RAW_CACHE.resolve()),
            "source_bank": str(BANK_PATH.resolve()),
            "input_metadata": metadata_in,
        }
    }

    with OUT_CACHE.open("w", encoding="utf-8") as f:
        f.write(json.dumps(meta_out, ensure_ascii=False) + "\n")
        for row in translated:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    OUT_ANOMALY.write_text(json.dumps(anomalies, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    total_ref_slots = max(1, len(translated) * K_MAX)
    stats = {
        "n_input": n_input,
        "n_output": len(translated),
        "n_anomaly": len(anomalies),
        "slot_id_distribution": {str(k): v for k, v in sorted(slot_id_dist.items(), key=lambda x: x[0])},
        "role_id_distribution": {str(k): v for k, v in sorted(role_id_dist.items(), key=lambda x: x[0])},
        "target_struct_distribution": {str(k): v for k, v in sorted(target_struct_dist.items(), key=lambda x: x[0])},
        "slot_none_count": slot_none_count,
        "slot_none_ratio": round(slot_none_count / total_ref_slots, 6),
        "leaf_match_loss_chars": leaf_match_loss_chars,
    }
    OUT_STATS.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    elapsed = time.time() - t0
    print("=== Translate Cache Stats ===")
    print(f"n_input={stats['n_input']} n_output={stats['n_output']} n_anomaly={stats['n_anomaly']}")
    print(f"slot_none={stats['slot_none_count']} ratio={stats['slot_none_ratio']}")
    print(f"leaf_match_loss_chars={stats['leaf_match_loss_chars']}")
    print(f"role_id_distribution={stats['role_id_distribution']}")
    print(f"target_struct_distribution={stats['target_struct_distribution']}")
    print(f"elapsed_sec={elapsed:.2f}")
    print(f"out_cache={OUT_CACHE.resolve()}")
    print(f"out_anomaly={OUT_ANOMALY.resolve()}")
    print(f"out_stats={OUT_STATS.resolve()}")


if __name__ == "__main__":
    main()

