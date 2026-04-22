#!/usr/bin/env python3
"""Retrieve top-k candidates from wxz_bank for 8 target failure cases.

New scheme: slot-based retrieval with Anchor + Coverage slots.
  Slot A (anchor_slots=2): reinforce the main radical.
  Slot B (coverage_slots=3): exemplars of hard/rare components.

Usage:  python 6retrieve.py
Output: retrieval_data_prepare/bank/RETRIEVAL_TEST.md
"""

# HARD RULE: scoring ONLY uses retrieval_top_level and retrieval_components.
# top_level_components / leaf_components are RAW analysis fields, NOT scored.
# Target and candidate must both go through the same retrieval-field generator.

from __future__ import annotations

import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "bank" / "wxz_bank.json"
DECOMP_PATH = ROOT / "bank" / "decomp.json"
GT_PATH = ROOT / "cases" / "wxz_gt_chars.csv"
REPORT_PATH = ROOT / "bank" / "RETRIEVAL_TEST.md"

TARGET_CHARS: List[str] = ["璨", "霆", "鳞", "彎", "瘻", "秦", "赢", "諢"]

# ---------------------------------------------------------------------------
# Import retrieval builder from 4build_retrieval.py (reuse, not rewrite)
# ---------------------------------------------------------------------------


def _load_build_retrieval_module():
    p = ROOT / "pipeline" / "4build_retrieval.py"
    spec = importlib.util.spec_from_file_location("_build_retrieval", str(p))
    if spec is None or spec.loader is None:
        print(f"ERROR: cannot load {p}", file=sys.stderr)
        sys.exit(1)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_br = _load_build_retrieval_module()
build_retrieval_for_entry = _br.build_retrieval_for_entry
load_merged_ids = _br.load_merged_ids
IDS_PATH_4 = _br.IDS_PATH

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def jaccard(a: list, b: list) -> float:
    """Set-based Jaccard: |A∩B| / |A∪B|. Returns 0 when both empty."""
    sa, sb = set(a), set(b)
    union = sa | sb
    if not union:
        return 0.0
    return len(sa & sb) / len(union)


def load_gt(path: Path) -> Dict[str, str]:
    """Load GT CSV → {character: bank_id}."""
    gt: Dict[str, str] = {}
    if not path.is_file():
        return gt
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.strip().split(",")
        if len(parts) >= 3:
            gt[parts[2]] = f"wxz_{parts[1]}"
    return gt


def build_target_fields(
    target_char: str,
    decomp: dict,
    ids_map: dict,
    raw_leaf_freq: Counter,
) -> dict:
    """Build retrieval fields for a target character using the same pipeline as bank."""
    if target_char not in decomp:
        print(
            f"ERROR: target '{target_char}' not found in decomp.json. "
            f"Cannot construct retrieval fields. Aborting.",
            file=sys.stderr,
        )
        sys.exit(1)

    d = decomp[target_char]
    entry = {
        "character": target_char,
        "bank_id": None,
        "ids": d.get("ids", "") or ids_map.get(target_char, ""),
        "top_level_components": list(d.get("top_level_components", []) or []),
        "leaf_components": list(d.get("leaf_components", []) or []),
    }
    warnings: list = []
    rtl, rc = build_retrieval_for_entry(entry, ids_map, raw_leaf_freq, warnings)
    return {
        "character": target_char,
        # raw IDS top-level (from decomp) — used to determine anchor_comp
        "top_level_components": list(d.get("top_level_components", []) or []),
        "retrieval_components": rc,
        "retrieval_top_level": rtl,
        "layout": d.get("layout", ""),
        "stroke_count": d.get("stroke_count", 0) or 0,
    }


# ---------------------------------------------------------------------------
# Bank frequency precomputation
# ---------------------------------------------------------------------------


def build_bank_freq(bank: list) -> Dict[str, int]:
    """Precompute bank_freq[comp] = # bank entries whose retrieval_components contains comp."""
    freq: Dict[str, int] = {}
    for entry in bank:
        for comp in set(entry.get("retrieval_components", []) or []):
            freq[comp] = freq.get(comp, 0) + 1
    return freq


def difficulty(comp: str, bank_freq: Dict[str, int]) -> float:
    """difficulty(comp) = 1 / log(1 + bank_freq(comp)). Higher = harder."""
    f = bank_freq.get(comp, 0)
    if f == 0:
        return float("inf")
    return 1.0 / math.log(1.0 + f)


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------


def _full_score(target: dict, cand: dict) -> float:
    """Full anchor scoring formula: 3*J(rc) + 2*J(rtl) + layout + stroke_sim."""
    t_rc = target["retrieval_components"]
    t_rtl = target["retrieval_top_level"]
    t_layout = target["layout"]
    t_sc = target["stroke_count"]
    return (
        3.0 * jaccard(t_rc, cand.get("retrieval_components", []) or [])
        + 2.0 * jaccard(t_rtl, cand.get("retrieval_top_level", []) or [])
        + 1.0 * (1 if t_layout == cand.get("layout", "") else 0)
        + 0.5 * max(0.0, 1.0 - abs(t_sc - (cand.get("stroke_count") or 0)) / 10.0)
    )


def _coverage_score(cand: dict, hard_comp: str, target: dict) -> float:
    """Coverage slot score: reward matching the specific hard_comp + layout + stroke."""
    t_layout = target["layout"]
    t_sc = target["stroke_count"]
    rc = cand.get("retrieval_components", []) or []
    return (
        3.0 * (1.0 if hard_comp in rc else 0.0)
        + 1.0 * (1.0 if t_layout == cand.get("layout", "") else 0.0)
        + 0.5 * max(0.0, 1.0 - abs(t_sc - (cand.get("stroke_count") or 0)) / 10.0)
    )


# ---------------------------------------------------------------------------
# Old-style full retrieval (kept for comparison in report)
# ---------------------------------------------------------------------------


def _retrieve_full_scored(
    target: dict,
    bank: list,
    ocr_conf_min: float,
) -> Tuple[dict, List[Tuple[float, dict]]]:
    """Full scoring without slot logic. Returns (filter_stats, all_scored)."""
    target_char = target["character"]
    n_total = len(bank)

    after_ocr = [c for c in bank if (c.get("ocr_conf") or 0) >= ocr_conf_min]
    n_after_ocr = len(after_ocr)

    after_self = [c for c in after_ocr if c.get("character") != target_char]
    n_after_self = len(after_self)

    after_unk = [
        c
        for c in after_self
        if not (
            c.get("has_unknown") is True
            and c.get("retrieval_components") == [c.get("character")]
        )
    ]
    n_after_unk = len(after_unk)

    scored: List[Tuple[float, dict]] = []
    for c in after_unk:
        s = _full_score(target, c)
        if s > 0:
            scored.append((s, c))

    scored.sort(key=lambda x: -x[0])

    stats = {
        "原始 bank": n_total,
        "after ocr_conf": n_after_ocr,
        "after self-exclusion": n_after_self,
        "after has_unknown sanity": n_after_unk,
        "final with score > 0": len(scored),
    }
    return stats, scored


# ---------------------------------------------------------------------------
# Slot-based retrieval (new)
# ---------------------------------------------------------------------------


def slot_retrieve(
    target: dict,
    bank: list,
    bank_freq: Dict[str, int],
    anchor_slots: int = 2,
    coverage_slots: int = 3,
    ocr_conf_min: float = 0.9,
) -> dict:
    """Slot-based retrieval: Anchor slots + Coverage slots.

    target must include keys: character, top_level_components, retrieval_components,
    retrieval_top_level, layout, stroke_count.
    """
    target_char = target["character"]

    # Filter candidates
    candidates = [
        c for c in bank
        if (c.get("ocr_conf") or 0) >= ocr_conf_min
        and c.get("character") != target_char
        and not (
            c.get("has_unknown") is True
            and c.get("retrieval_components") == [c.get("character")]
        )
    ]

    # Anchor component = first retrieval_top_level (normalized)
    rtl = target.get("retrieval_top_level", []) or []
    anchor_comp: str = rtl[0] if rtl else ""

    # Retrieval components of target (deduplicated, order-preserving)
    t_rc_raw = target["retrieval_components"] or []
    seen: dict = {}
    t_rc_unique: List[str] = []
    for c in t_rc_raw:
        if c not in seen:
            seen[c] = True
            t_rc_unique.append(c)

    total_slots = anchor_slots + coverage_slots

    # anchor_comp is already normalized (from retrieval_top_level), no need for
    # TRAD_SIMP mapping. anchor_forms is just {anchor_comp} for downstream use.
    anchor_forms: set = {anchor_comp} if anchor_comp else set()

    # --- Determine hard_comps ---
    if len(t_rc_unique) <= 1:
        # 独体字: no hard comps, all slots become anchor slots
        hard_comps: List[str] = []
        eff_anchor_slots = total_slots
        eff_coverage_slots = 0
    else:
        non_anchor = [c for c in t_rc_unique if c not in anchor_forms]
        non_anchor_sorted = sorted(non_anchor, key=lambda c: -difficulty(c, bank_freq))
        # Dynamic sizing: take all non-anchor comps that have bank hits, up to coverage_slots.
        # This prevents dropping valid hard comps when the target has 4+ retrieval_components.
        hard_comps = [c for c in non_anchor_sorted if bank_freq.get(c, 0) > 0][:coverage_slots]
        if not hard_comps:
            # 所有非 anchor 组件均无 bank 命中（如 瘻），剩余 coverage_slots 全部 fallback 到 anchor
            eff_anchor_slots = total_slots
            eff_coverage_slots = 0
        else:
            eff_anchor_slots = anchor_slots
            eff_coverage_slots = coverage_slots

    # --- Pre-score all candidates by full formula ---
    full_scored: List[Tuple[float, dict]] = []
    for c in candidates:
        s = _full_score(target, c)
        if s > 0:
            full_scored.append((s, c))
    full_scored.sort(key=lambda x: -x[0])

    selected_chars: set = set()
    refs: List[dict] = []

    # ----------------------------------------------------------------
    # Slot A: Anchor slots
    # ----------------------------------------------------------------
    anchor_hits = [
        (s, c) for s, c in full_scored
        if anchor_comp and (
            bool(anchor_forms & set(c.get("retrieval_components", []) or []))
            or bool(anchor_forms & set(c.get("top_level_components", []) or []))
        )
    ]

    filled_anchor = 0
    for s, c in anchor_hits:
        if filled_anchor >= eff_anchor_slots:
            break
        char = c.get("character", "")
        if char in selected_chars:
            continue
        selected_chars.add(char)
        refs.append({
            "rank": len(refs) + 1,
            "char": char,
            "wxz_path": c.get("wxz_path", ""),
            "role": "anchor",
            "matched_comp": anchor_comp,
            "score": round(s, 4),
            "_entry": c,
        })
        filled_anchor += 1

    # Fallback: not enough anchor candidates → fill with highest full_score
    if filled_anchor < eff_anchor_slots:
        for s, c in full_scored:
            if filled_anchor >= eff_anchor_slots:
                break
            char = c.get("character", "")
            if char in selected_chars:
                continue
            selected_chars.add(char)
            refs.append({
                "rank": len(refs) + 1,
                "char": char,
                "wxz_path": c.get("wxz_path", ""),
                "role": "anchor",
                "matched_comp": anchor_comp,
                "score": round(s, 4),
                "_entry": c,
            })
            filled_anchor += 1

    # ----------------------------------------------------------------
    # Slot B: Coverage slots
    # ----------------------------------------------------------------
    uncovered_comps: List[str] = []
    slot_reassignments: List[dict] = []

    if eff_coverage_slots > 0 and hard_comps:
        if len(hard_comps) == 1:
            dedicated = [hard_comps[0]] * min(2, eff_coverage_slots)
        else:
            dedicated = [hard_comps[0], hard_comps[1]]
        free_count = eff_coverage_slots - len(dedicated)
        slot_plan: List[Optional[str]] = list(dedicated) + [None] * free_count

        for slot_comp in slot_plan:
            if slot_comp is not None:
                _fill_dedicated_coverage_slot(
                    slot_comp, target, full_scored, selected_chars,
                    refs, uncovered_comps, slot_reassignments,
                    t_rc_unique, hard_comps, anchor_forms, bank_freq,
                    anchor_hits, eff_anchor_slots, filled_anchor,
                )
            else:
                _fill_free_coverage_slot(
                    hard_comps, target, full_scored, selected_chars, refs,
                    anchor_hits, slot_reassignments, uncovered_comps,
                )

    # Re-number ranks
    for i, ref in enumerate(refs, 1):
        ref["rank"] = i

    # Build coverage_report.covered (all target comps that appear in at least 1 ref)
    all_ref_comps: set = set()
    for ref in refs:
        entry = ref.get("_entry", {})
        all_ref_comps.update(entry.get("retrieval_components", []) or [])

    # anchor_comp is explicitly prepended when any anchor slot filled.
    # This handles cases where anchor_comp is a simplified or complex form
    # that does not appear literally in retrieval_components (e.g. yu2 vs Yu2_trad).
    covered_in_refs: List[str] = []
    if filled_anchor > 0 and anchor_comp:
        covered_in_refs.append(anchor_comp)
    for c in t_rc_unique:
        if c in all_ref_comps and c not in covered_in_refs:
            covered_in_refs.append(c)

    return {
        "target": target_char,
        "anchor_comp": anchor_comp,
        "hard_comps": hard_comps,
        "refs": refs,
        "coverage_report": {
            "covered": covered_in_refs,
            "uncovered": uncovered_comps,
            "slot_reassignments": slot_reassignments,
        },
    }


def _fill_dedicated_coverage_slot(
    slot_comp: str,
    target: dict,
    full_scored: List[Tuple[float, dict]],
    selected_chars: set,
    refs: list,
    uncovered_comps: List[str],
    slot_reassignments: List[dict],
    t_rc_unique: List[str],
    hard_comps: List[str],
    anchor_forms: set,
    bank_freq: Dict[str, int],
    anchor_hits: List[Tuple[float, dict]],
    eff_anchor_slots: int,
    filled_anchor: int,
) -> None:
    """Fill one dedicated coverage slot for slot_comp.

    Fallback chain when slot_comp has zero bank hits:
    1. Widen: check top_level_components
    2. Reassign: next-highest-difficulty comp from t_rc_unique that has hits
    3. Extra anchor: add another anchor-matching exemplar
    """
    hits = [
        c for _, c in full_scored
        if slot_comp in (c.get("retrieval_components", []) or [])
        and c.get("character", "") not in selected_chars
    ]
    if not hits:
        hits = [
            c for _, c in full_scored
            if slot_comp in (c.get("top_level_components", []) or [])
            and c.get("character", "") not in selected_chars
        ]

    if hits:
        ranked = sorted(hits, key=lambda c: -_coverage_score(c, slot_comp, target))
        best = ranked[0]
        char = best.get("character", "")
        selected_chars.add(char)
        refs.append({
            "rank": len(refs) + 1,
            "char": char,
            "wxz_path": best.get("wxz_path", ""),
            "role": "coverage",
            "matched_comp": slot_comp,
            "score": round(_coverage_score(best, slot_comp, target), 4),
            "_entry": best,
        })
        return

    # --- Zero-hit path ---
    uncovered_comps.append(slot_comp)

    # Fallback 2: reassign to next-highest-difficulty comp not already in hard_comps
    already_used = set(hard_comps) | anchor_forms
    alt_comps = [
        c for c in t_rc_unique
        if c not in already_used and bank_freq.get(c, 0) > 0
    ]
    alt_comps.sort(key=lambda c: -difficulty(c, bank_freq))

    for alt in alt_comps:
        alt_hits = [
            c for _, c in full_scored
            if alt in (c.get("retrieval_components", []) or [])
            and c.get("character", "") not in selected_chars
        ]
        if not alt_hits:
            alt_hits = [
                c for _, c in full_scored
                if alt in (c.get("top_level_components", []) or [])
                and c.get("character", "") not in selected_chars
            ]
        if alt_hits:
            ranked = sorted(alt_hits, key=lambda c: -_coverage_score(c, alt, target))
            best = ranked[0]
            char = best.get("character", "")
            selected_chars.add(char)
            refs.append({
                "rank": len(refs) + 1,
                "char": char,
                "wxz_path": best.get("wxz_path", ""),
                "role": "coverage",
                "matched_comp": alt,
                "score": round(_coverage_score(best, alt, target), 4),
                "_entry": best,
            })
            slot_reassignments.append({
                "original_hard_comp": slot_comp,
                "reason": "zero_bank_hits",
                "replaced_with": alt + " (alt coverage)",
            })
            return

    # Fallback 3: convert to extra anchor slot
    anchor_comp_name = (target.get("retrieval_top_level") or [""])[0]
    for s, c in anchor_hits:
        char = c.get("character", "")
        if char not in selected_chars:
            selected_chars.add(char)
            refs.append({
                "rank": len(refs) + 1,
                "char": char,
                "wxz_path": c.get("wxz_path", ""),
                "role": "anchor",
                "matched_comp": anchor_comp_name,
                "score": round(s, 4),
                "_entry": c,
            })
            slot_reassignments.append({
                "original_hard_comp": slot_comp,
                "reason": "zero_bank_hits",
                "replaced_with": anchor_comp_name + " (anchor)",
            })
            return

    # Fallback 4: highest full_score candidate (last resort)
    for s, c in full_scored:
        char = c.get("character", "")
        if char not in selected_chars:
            selected_chars.add(char)
            refs.append({
                "rank": len(refs) + 1,
                "char": char,
                "wxz_path": c.get("wxz_path", ""),
                "role": "anchor",
                "matched_comp": anchor_comp_name,
                "score": round(s, 4),
                "_entry": c,
            })
            slot_reassignments.append({
                "original_hard_comp": slot_comp,
                "reason": "zero_bank_hits_no_anchor_avail",
                "replaced_with": "best_full_score",
            })
            return


def _fill_free_coverage_slot(
    hard_comps: List[str],
    target: dict,
    full_scored: List[Tuple[float, dict]],
    selected_chars: set,
    refs: list,
    anchor_hits: List[Tuple[float, dict]],
    slot_reassignments: List[dict],
    uncovered_comps: List[str],
) -> None:
    """Fill one free coverage slot: highest coverage_score over all hard_comps.

    If no candidate actually contains any hard_comp (coverage_score lacks the
    3.0 component-match bonus, so score <= 1.5), convert to an anchor slot
    instead of injecting noise.
    """
    best_s = -1.0
    best_c: Optional[dict] = None
    best_hc = ""
    for _, c in full_scored:
        if c.get("character", "") in selected_chars:
            continue
        for hc in hard_comps:
            s = _coverage_score(c, hc, target)
            if s > best_s:
                best_s = s
                best_c = c
                best_hc = hc

    if best_c is not None and best_s > 1.5:
        char = best_c.get("character", "")
        selected_chars.add(char)
        refs.append({
            "rank": len(refs) + 1,
            "char": char,
            "wxz_path": best_c.get("wxz_path", ""),
            "role": "coverage",
            "matched_comp": best_hc,
            "score": round(best_s, 4),
            "_entry": best_c,
        })
        return

    anchor_comp_name = (target.get("retrieval_top_level") or [""])[0]
    for s, c in anchor_hits:
        char = c.get("character", "")
        if char not in selected_chars:
            selected_chars.add(char)
            refs.append({
                "rank": len(refs) + 1,
                "char": char,
                "wxz_path": c.get("wxz_path", ""),
                "role": "anchor",
                "matched_comp": anchor_comp_name,
                "score": round(s, 4),
                "_entry": c,
            })
            slot_reassignments.append({
                "original_hard_comp": "free_slot",
                "reason": "no_hard_comp_hit_in_bank",
                "replaced_with": anchor_comp_name + " (anchor)",
            })
            return

    for s, c in full_scored:
        char = c.get("character", "")
        if char not in selected_chars:
            selected_chars.add(char)
            refs.append({
                "rank": len(refs) + 1,
                "char": char,
                "wxz_path": c.get("wxz_path", ""),
                "role": "anchor",
                "matched_comp": anchor_comp_name,
                "score": round(s, 4),
                "_entry": c,
            })
            slot_reassignments.append({
                "original_hard_comp": "free_slot",
                "reason": "no_viable_coverage_or_anchor",
                "replaced_with": "best_full_score",
            })
            return



# ---------------------------------------------------------------------------
# Legacy MMR (kept for backward compatibility with retrieve() API)
# ---------------------------------------------------------------------------


def mmr_rerank(
    scored: List[Tuple[float, dict]],
    top_k: int = 5,
    lam: float = 0.7,
    pool_size: int = 50,
) -> List[Tuple[float, float, dict]]:
    """MMR greedy reranking over a relevance-sorted pool."""
    pool = scored[:pool_size]
    if not pool:
        return []

    max_rel = pool[0][0]
    if max_rel <= 0:
        return []

    selected: List[Tuple[float, float, dict]] = []
    remaining = list(range(len(pool)))

    for _ in range(min(top_k, len(pool))):
        best_idx_in_remaining = -1
        best_mmr = -float("inf")

        for ri, pi in enumerate(remaining):
            rel, entry = pool[pi]
            norm_rel = rel / max_rel

            if not selected:
                max_sim = 0.0
            else:
                c_comps = entry.get("retrieval_components", [])
                max_sim = max(
                    jaccard(c_comps, se.get("retrieval_components", []))
                    for _, _, se in selected
                )

            mmr = lam * norm_rel - (1 - lam) * max_sim
            if mmr > best_mmr:
                best_mmr = mmr
                best_idx_in_remaining = ri

        pi = remaining.pop(best_idx_in_remaining)
        rel, entry = pool[pi]
        selected.append((best_mmr, rel, entry))

    return selected


def component_coverage(
    target_comps: list, selected_entries: list,
) -> Dict[str, List[str]]:
    """For each target component, list which selected bank_ids cover it."""
    coverage: Dict[str, List[str]] = {c: [] for c in set(target_comps)}
    for entry in selected_entries:
        c_set = set(entry.get("retrieval_components", []))
        for tc in coverage:
            if tc in c_set:
                coverage[tc].append(entry.get("bank_id", "?"))
    return coverage


def retrieve(
    target_char: str,
    bank: list,
    top_k: int = 3,
    ocr_conf_min: float = 0.88,
    mmr: bool = True,
    lam: float = 0.7,
) -> list:
    """返回 [(score, bank_entry), ...]，按 score 降序（mmr=True 时按 MMR 排序）"""
    decomp = json.loads(DECOMP_PATH.read_text(encoding="utf-8"))
    ids_map = load_merged_ids(IDS_PATH_4)
    raw_leaf_freq: Counter = Counter()
    for row in bank:
        for comp in row.get("leaf_components", []) or []:
            raw_leaf_freq[comp] += 1

    target = build_target_fields(target_char, decomp, ids_map, raw_leaf_freq)
    _, scored = _retrieve_full_scored(target, bank, ocr_conf_min)
    if mmr:
        reranked = mmr_rerank(scored, top_k=top_k, lam=lam)
        return [(rel, entry) for _, rel, entry in reranked]
    return scored[:top_k]


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

_OCR_CONF_REPORT = 0.9
_TOP_K_REPORT = 5
_ANCHOR_SLOTS = 2
_COVERAGE_SLOTS = 3

_TABLE_HEADER = (
    "| rank | score | bank_id | char | retrieval_components "
    "| top_level | layout | strokes | wxz_path |"
)
_TABLE_SEP = (
    "|------|-------|---------|------|----------------------"
    "|-----------|--------|---------|----------|"
)

_SLOT_TABLE_HEADER = (
    "| rank | role | matched_comp | score | char | retrieval_components "
    "| layout | strokes | wxz_path |"
)
_SLOT_TABLE_SEP = (
    "|------|------|--------------|-------|------|----------------------"
    "|--------|---------|----------|"
)


def _fmt_row_old(rank: int, score: float, entry: dict) -> str:
    return (
        f"| {rank} | {score:.2f} | {entry.get('bank_id', '')} "
        f"| {entry.get('character', '')} "
        f"| {entry.get('retrieval_components', [])} "
        f"| {entry.get('retrieval_top_level', [])} "
        f"| {entry.get('layout', '')} "
        f"| {entry.get('stroke_count', '')} "
        f"| {entry.get('wxz_path', '')} |"
    )


def _fmt_row_slot(ref: dict) -> str:
    e = ref.get("_entry", {})
    return (
        f"| {ref['rank']} | {ref['role']} | {ref['matched_comp']} "
        f"| {ref['score']:.2f} | {ref['char']} "
        f"| {e.get('retrieval_components', [])} "
        f"| {e.get('layout', '')} "
        f"| {e.get('stroke_count', '')} "
        f"| {ref['wxz_path']} |"
    )


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    decomp = json.loads(DECOMP_PATH.read_text(encoding="utf-8"))
    ids_map = load_merged_ids(IDS_PATH_4)
    gt = load_gt(GT_PATH)

    raw_leaf_freq: Counter = Counter()
    for row in bank:
        for comp in row.get("leaf_components", []) or []:
            raw_leaf_freq[comp] += 1

    # Precompute bank_freq for difficulty scoring
    bank_freq = build_bank_freq(bank)

    missing = [ch for ch in TARGET_CHARS if ch not in decomp]
    if missing:
        print(
            f"ERROR: targets not in decomp.json: {missing}\n"
            f"Cannot construct retrieval fields. Aborting.",
            file=sys.stderr,
        )
        sys.exit(1)
    active_chars = list(TARGET_CHARS)

    # Build target fields for all chars
    targets: Dict[str, dict] = {}
    for ch in active_chars:
        targets[ch] = build_target_fields(ch, decomp, ids_map, raw_leaf_freq)

    # Run old full retrieval (for comparison)
    old_results: Dict[str, Tuple[dict, List[Tuple[float, dict]]]] = {}
    for ch in active_chars:
        stats, scored = _retrieve_full_scored(targets[ch], bank, _OCR_CONF_REPORT)
        old_results[ch] = (stats, scored)

    # Run new slot-based retrieval
    slot_results: Dict[str, dict] = {}
    for ch in active_chars:
        slot_results[ch] = slot_retrieve(
            targets[ch], bank, bank_freq,
            anchor_slots=_ANCHOR_SLOTS,
            coverage_slots=_COVERAGE_SLOTS,
            ocr_conf_min=_OCR_CONF_REPORT,
        )

    # ---- Build report ----
    L: List[str] = []
    L.append("# Retrieval Test Report — Slot-Based (Anchor + Coverage)")
    L.append("")
    L.append(f"- Bank: `{BANK_PATH.name}` ({len(bank)} entries)")
    L.append(f"- OCR confidence threshold: {_OCR_CONF_REPORT}")
    L.append(f"- Anchor slots: {_ANCHOR_SLOTS}  |  Coverage slots: {_COVERAGE_SLOTS}")
    L.append(f"- Full score formula: `3*J(rc) + 2*J(rtl) + 1*layout + 0.5*stroke_sim`")
    L.append(f"- Coverage score formula: `3*(hard_comp match) + 1*layout + 0.5*stroke_sim`")
    L.append(f"- Difficulty: `1 / log(1 + bank_freq(comp))`")
    L.append(f"- Targets: `{TARGET_CHARS}`")
    L.append("")

    for ch in active_chars:
        t = targets[ch]
        stats, old_scored = old_results[ch]
        sr = slot_results[ch]

        L.append(f"## {ch}")
        L.append(f"- target retrieval_components: `{t['retrieval_components']}`")
        L.append(f"- target top_level_components (raw): `{t['top_level_components']}`")
        L.append(f"- target retrieval_top_level: `{t['retrieval_top_level']}`")
        L.append(f"- target layout: `{t['layout']}`")
        L.append(f"- target stroke_count: `{t['stroke_count']}`")
        L.append(f"- **anchor_comp**: `{sr['anchor_comp']}`")
        L.append(f"- **hard_comps**: `{sr['hard_comps']}`")
        L.append("")

        # Show hard_comp difficulty
        if sr["hard_comps"]:
            L.append("**Component difficulty (bank_freq → difficulty):**")
            for hc in sr["hard_comps"]:
                bf = bank_freq.get(hc, 0)
                d = difficulty(hc, bank_freq)
                d_str = f"{d:.4f}" if d != float("inf") else "∞"
                L.append(f"- `{hc}`: bank_freq={bf}, difficulty={d_str}")
            L.append("")

        # --- Filter stats ---
        L.append("### 过滤阶段")
        for label, count in stats.items():
            L.append(f"- {label}: {count}")
        L.append("")

        # --- OLD top-5 (pure relevance) ---
        L.append("### OLD Top-5 (Pure Relevance, pre-refactor)")
        L.append(_TABLE_HEADER)
        L.append(_TABLE_SEP)
        for i, (s, c) in enumerate(old_scored[:_TOP_K_REPORT], 1):
            L.append(_fmt_row_old(i, s, c))
        L.append("")

        old_cov = component_coverage(
            t["retrieval_components"],
            [c for _, c in old_scored[:_TOP_K_REPORT]],
        )
        L.append("**OLD component coverage:**")
        for comp, hits in old_cov.items():
            mark = "✓" if hits else "✗ MISS"
            L.append(f"- `{comp}`: {mark} ({len(hits)} hits)")
        L.append("")

        # --- NEW slot-based top-5 ---
        L.append("### NEW Slot-Based Top-5")
        L.append(_SLOT_TABLE_HEADER)
        L.append(_SLOT_TABLE_SEP)
        for ref in sr["refs"]:
            L.append(_fmt_row_slot(ref))
        L.append("")

        # Coverage report
        cov_rep = sr["coverage_report"]
        L.append("**coverage_report:**")
        L.append(f"- covered: `{cov_rep['covered']}`")
        L.append(f"- uncovered: `{cov_rep['uncovered']}`")
        reassign = sr["coverage_report"].get("slot_reassignments", [])
        if reassign:
            L.append(f"- slot_reassignments: `{reassign}`")
        L.append("")

        # Component-level coverage for new results
        new_entries = [ref["_entry"] for ref in sr["refs"]]
        new_cov = component_coverage(t["retrieval_components"], new_entries)
        L.append("**NEW component coverage (per retrieval_component):**")
        for comp, hits in new_cov.items():
            mark = "✓" if hits else "✗ MISS"
            L.append(f"- `{comp}`: {mark} ({len(hits)} hits)")
        L.append("")

        # Score distribution
        L.append("### 分数分布")
        L.append(f"- score > 0 的候选数: {len(old_scored)}")
        L.append(f"- score > 1.0: {sum(1 for s, _ in old_scored if s > 1.0)}")
        L.append(f"- score > 2.0: {sum(1 for s, _ in old_scored if s > 2.0)}")
        L.append(f"- score > 3.0: {sum(1 for s, _ in old_scored if s > 3.0)}")
        L.append("")

    # ---- Verification Checklist ----
    L.append("---")
    L.append("## Verification Checklist")
    L.append("")

    checks_passed = 0
    checks_total = 0

    def check(label: str, ok: bool, detail: str = "") -> None:
        nonlocal checks_passed, checks_total
        checks_total += 1
        if ok:
            checks_passed += 1
        status = "✅" if ok else "❌"
        line = f"- {status} {label}"
        if detail:
            line += f" — {detail}"
        L.append(line)

    L.append("### 1. anchor_comp == first retrieval_top_level (normalized)")
    for ch in active_chars:
        t = targets[ch]
        sr = slot_results[ch]
        expected = t["retrieval_top_level"][0] if t["retrieval_top_level"] else ""
        ok = sr["anchor_comp"] == expected
        check(f"`{ch}`", ok, f"anchor={sr['anchor_comp']!r}, first_rtl={expected!r}")
    L.append("")

    L.append("### 2. Target character not in its own results")
    for ch in active_chars:
        sr = slot_results[ch]
        chars_in_refs = [ref["char"] for ref in sr["refs"]]
        ok = ch not in chars_in_refs
        check(f"`{ch}`", ok, f"refs={chars_in_refs}")
    L.append("")

    L.append("### 3. No duplicate characters within a target's top-5")
    for ch in active_chars:
        sr = slot_results[ch]
        chars_in_refs = [ref["char"] for ref in sr["refs"]]
        ok = len(chars_in_refs) == len(set(chars_in_refs))
        check(f"`{ch}`", ok, f"chars={chars_in_refs}")
    L.append("")

    L.append("### 4. coverage_report.covered contains at least anchor_comp")
    for ch in active_chars:
        sr = slot_results[ch]
        anchor = sr["anchor_comp"]
        covered = sr["coverage_report"]["covered"]
        ok = anchor in covered if anchor else True
        check(f"`{ch}`", ok, f"anchor={anchor!r}, covered={covered}")
    L.append("")

    L.append("### 5. 霆: coverage slots contain 廴/廷 and 壬")
    ch = "霆"
    if ch in slot_results:
        sr = slot_results[ch]
        cov_refs = [ref for ref in sr["refs"] if ref["role"] == "coverage"]
        cov_entries = [ref["_entry"] for ref in cov_refs]
        has_di = any(
            "廴" in (e.get("retrieval_components", []) or [])
            or "廷" in (e.get("retrieval_components", []) or [])
            or "廷" in (e.get("top_level_components", []) or [])
            for e in cov_entries
        )
        has_ren = any(
            "壬" in (e.get("retrieval_components", []) or [])
            for e in cov_entries
        )
        uncov = sr["coverage_report"]["uncovered"]
        di_detail = "✓" if has_di else f"✗ (uncovered: {uncov})"
        ren_detail = "✓" if has_ren else f"✗ (uncovered: {uncov})"
        check(f"`霆` coverage contains 廴/廷", has_di, di_detail)
        check(f"`霆` coverage contains 壬", has_ren, ren_detail)
    L.append("")

    L.append("### 6. 赢: any ref contains 月; note on 貝 coverage")
    ch = "赢"
    if ch in slot_results:
        sr = slot_results[ch]
        all_entries = [ref["_entry"] for ref in sr["refs"]]
        cov_entries = [ref["_entry"] for ref in sr["refs"] if ref["role"] == "coverage"]
        # 月 is expected in anchor slots (臂/望 both contain 月); check all refs
        has_yue_all = any(
            "月" in (e.get("retrieval_components", []) or [])
            for e in all_entries
        )
        # 貝: check all refs; hard_comps ranked by difficulty may not include 貝
        has_bei_any = any(
            "貝" in (e.get("retrieval_components", []) or [])
            or "贝" in (e.get("retrieval_components", []) or [])
            for e in all_entries
        )
        hard = sr["hard_comps"]
        check(f"`赢` any ref contains 月 (anchor slots cover it)", has_yue_all,
              "found" if has_yue_all else "MISS")
        check(f"`赢` any ref contains 貝/贝", has_bei_any,
              "found" if has_bei_any else
              f"not covered -- 貝 has lower difficulty than hard_comps={hard}")
    L.append("")

    L.append(f"### Summary: {checks_passed}/{checks_total} checks passed")
    L.append("")

    # ---- GT Leakage check ----
    L.append("---")
    L.append("## GT Leakage Check")
    L.append("")
    if not gt:
        L.append("- GT 文件未找到或为空，跳过")
    else:
        found_leak = False
        for ch in active_chars:
            gt_id = gt.get(ch)
            if not gt_id:
                L.append(f"- {ch}: 无 GT 记录，跳过")
                continue
            sr = slot_results[ch]
            for ref in sr["refs"]:
                if ref["_entry"].get("bank_id") == gt_id:
                    L.append(
                        f"- **LEAKAGE** `{ch}` rank {ref['rank']} bank_id={gt_id}"
                    )
                    found_leak = True
        if not found_leak:
            L.append("- 无泄漏（slot top-5 中无 GT wxz_id）")
    L.append("")

    report = "\n".join(L) + "\n"
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Report written to: {REPORT_PATH}")

    # Console summary
    for ch in active_chars:
        sr = slot_results[ch]
        cov_rep = sr["coverage_report"]
        cov_str = f"covered={cov_rep['covered']}"
        if cov_rep["uncovered"]:
            cov_str += f" UNCOVERED={cov_rep['uncovered']}"
        anchor = sr["anchor_comp"]
        hards = sr["hard_comps"]
        print(f"  {ch}: anchor={anchor!r} hard={hards} {cov_str}")


if __name__ == "__main__":
    main()
