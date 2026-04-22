from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "bank" / "wxz_bank.json"
DECOMP_PATH = ROOT / "bank" / "decomp.json"
LEAF_FREQ_PATH = ROOT / "bank" / "leaf_freq.json"
REPORT_PATH = ROOT / "bank" / "REPORT.md"
IDS_PATH = ROOT / "assets" / "ids" / "ids.txt"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

IDC_ARITY: Dict[str, int] = {
    "\u2ff0": 2, "\u2ff1": 2, "\u2ff2": 3, "\u2ff3": 3,
    "\u2ff4": 2, "\u2ff5": 2, "\u2ff6": 2, "\u2ff7": 2,
    "\u2ff8": 2, "\u2ff9": 2, "\u2ffa": 2, "\u2ffb": 2,
}

NORM: Dict[str, str] = {
    "忄": "心", "⺗": "心", "㣺": "心",
    "扌": "手",
    "氵": "水", "氺": "水",
    "灬": "火",
    "犭": "犬",
    "礻": "示", "衤": "衣",
    "艹": "艸", "⺿": "艸",
    "⺮": "竹", "𥫗": "竹",
    "辶": "辵", "⻌": "辵", "⻍": "辵",
    "⺌": "小", "⺍": "小",
    "⺊": "卜",
    "丷": "八",
    "𠂉": "人",
    "𠂊": "刀",
    "丆": "厂",
    "𠂆": "厂",
    "コ": "彐",
}

TRAD_SIMP: Dict[str, str] = {
    "车": "車", "贝": "貝", "门": "門", "马": "馬",
    "鸟": "鳥", "鱼": "魚", "纟": "糸", "讠": "言",
    "饣": "食", "钅": "金", "页": "頁", "见": "見",
    "风": "風", "飞": "飛", "韦": "韋", "长": "長",
    "龙": "龍", "龟": "龜", "齿": "齒", "麦": "麥",
    "黄": "黃", "齐": "齊", "卤": "鹵",
}

NORM_SOURCES: Set[str] = set(NORM.keys())

STROKE_PRIMITIVES: Set[str] = set(chr(cp) for cp in range(0x31C0, 0x31F0))
STROKE_PRIMITIVES |= {"丿", "丶", "亅", "乚", "乀", "乁"}

SINGLE_CHAR_WHITELIST: Set[str] = {
    "七", "九", "乃", "也", "已", "之", "于", "五", "井", "亚",
    "云", "互", "甫", "平", "丁", "干", "壬", "丢", "丰", "乎",
    "乙", "乞", "了", "予", "事", "些", "今", "介", "从", "令",
    "以", "其", "再", "冬", "几", "凡", "凭", "出", "函", "刀",
    "刃", "分", "切", "刊", "及", "又", "口", "日", "月", "木",
    "水", "火", "土", "王", "田", "目", "耳", "手", "足", "身",
    "心", "气", "米", "竹", "衣", "车", "马", "牛", "羊", "鸟",
    "鱼", "龙", "龟", "人", "儿", "女", "子", "山", "川", "工",
    "上", "下", "中", "大", "小", "厂", "不", "亞", "垂",
}

KANGXI_RADICALS: Set[str] = {
    "一", "丨", "丶", "丿", "乙", "亅", "二", "亠", "人", "儿",
    "入", "八", "冂", "冖", "冫", "几", "凵", "刀", "力", "勹",
    "匕", "匚", "匸", "十", "卜", "卩", "厂", "厶", "又", "口",
    "囗", "土", "士", "夂", "夊", "夕", "大", "女", "子", "宀",
    "寸", "小", "尢", "尸", "屮", "山", "巛", "工", "己", "巾",
    "干", "幺", "广", "廴", "廾", "弋", "弓", "彐", "彡", "彳",
    "心", "戈", "戶", "手", "支", "攴", "文", "斗", "斤", "方",
    "无", "日", "曰", "月", "木", "欠", "止", "歹", "殳", "毋",
    "比", "毛", "氏", "气", "水", "火", "爪", "父", "爻", "爿",
    "片", "牙", "牛", "犬", "玄", "玉", "瓜", "瓦", "甘", "生",
    "用", "田", "疋", "疒", "癶", "白", "皮", "皿", "目", "矛",
    "矢", "石", "示", "禸", "禾", "穴", "立", "竹", "米", "糸",
    "缶", "网", "羊", "羽", "老", "而", "耒", "耳", "聿", "肉",
    "臣", "自", "至", "臼", "舌", "舛", "舟", "艮", "色", "艸",
    "虍", "虫", "血", "行", "衣", "襾", "見", "角", "言", "谷",
    "豆", "豕", "豸", "貝", "赤", "走", "足", "身", "車", "辛",
    "辰", "辵", "邑", "酉", "釆", "里", "金", "長", "門", "阜",
    "隶", "隹", "雨", "青", "非", "面", "革", "韋", "韭", "音",
    "頁", "風", "飛", "食", "首", "香", "馬", "骨", "高", "髟",
    "鬥", "鬯", "鬲", "鬼", "魚", "鳥", "鹵", "鹿", "麥", "麻",
    "黃", "黍", "黑", "黹", "黽", "鼎", "鼓", "鼠", "鼻", "齊",
    "齒", "龍", "龜", "龠",
}

TARGET_CHARS: List[str] = ["璨", "霆", "鳞", "彎", "瘻", "秦", "赢", "諢"]

# ---------------------------------------------------------------------------
# IDS helpers (kept from previous version)
# ---------------------------------------------------------------------------

def _is_idc(ch: str) -> bool:
    return ch in IDC_ARITY


def _is_stroke_primitive(ch: str) -> bool:
    return ch in STROKE_PRIMITIVES


def _clean_ids(ids: str) -> str:
    out = []
    in_bracket = False
    for ch in ids or "":
        if ch == "[":
            in_bracket = True
            continue
        if ch == "]":
            in_bracket = False
            continue
        if not in_bracket:
            out.append(ch)
    return "".join(out).strip()


def load_ids_txt(path: Path) -> Dict[str, str]:
    m: Dict[str, str] = {}
    if not path.is_file():
        return m
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) >= 3 and parts[0].upper().startswith("U+"):
            ch = parts[1].strip()[:1]
            ids = _clean_ids(parts[2].strip())
            if ch:
                m[ch] = ids
    return m


def load_merged_ids(base_path: Path) -> Dict[str, str]:
    merged: Dict[str, str] = {}
    full_path = base_path.parent / "ids_full.txt"
    if full_path.is_file():
        merged.update(load_ids_txt(full_path))
    if base_path.is_file():
        merged.update(load_ids_txt(base_path))
    return merged


def parse_expr(s: str, i: int) -> Tuple[str, int]:
    if i >= len(s):
        raise ValueError("IDS ended unexpectedly")
    ch = s[i]
    if not _is_idc(ch):
        return ch, i + 1
    n = IDC_ARITY[ch]
    i += 1
    parts: List[str] = []
    for _ in range(n):
        part, i = parse_expr(s, i)
        parts.append(part)
    return ch + "".join(parts), i


def parse_children(expr: str) -> Tuple[str, List[str]]:
    expr = _clean_ids(expr)
    if not expr or not _is_idc(expr[0]):
        return "", []
    layout = expr[0]
    n = IDC_ARITY[layout]
    i = 1
    children: List[str] = []
    for _ in range(n):
        child, i = parse_expr(expr, i)
        children.append(child)
    if i != len(expr):
        raise ValueError(f"IDS has trailing content: {expr[i:]!r}")
    return layout, children


def is_unknown_numbered_component(ch: str) -> bool:
    if not ch:
        return False
    o = ord(ch)
    return 0x2460 <= o <= 0x2473


def sanitize_retrieval(comps: List[str], character: str) -> List[str]:
    # 过滤圈号未知部件 ①-⑳
    filtered = [c for c in comps if not (len(c) == 1 and "\u2460" <= c <= "\u2473")]
    # 过滤后为空则用整字兜底
    if not filtered and character:
        return [character]
    return filtered


# ---------------------------------------------------------------------------
# Normalization: 阝 position-aware → NORM → TRAD_SIMP
# ---------------------------------------------------------------------------

def _normalize_one(
    comp: str,
    parent_layout: Optional[str],
    child_index: Optional[int],
    warnings: Optional[List[dict]] = None,
    context: Optional[dict] = None,
) -> str:
    if comp == "阝":
        if parent_layout == "⿰" and child_index == 0:
            comp = "阜"
        elif parent_layout == "⿰" and child_index is not None and child_index > 0:
            comp = "邑"
        elif warnings is not None:
            warnings.append({
                "type": "unresolved_fu_yi",
                "character": (context or {}).get("character"),
                "bank_id": (context or {}).get("bank_id"),
                "ids": (context or {}).get("ids"),
                "parent_layout": parent_layout,
                "child_index": child_index,
            })
    comp = NORM.get(comp, comp)
    comp = TRAD_SIMP.get(comp, comp)
    return comp


# ---------------------------------------------------------------------------
# Core: expand from top_level_components, bounded by raw leaf granularity
# ---------------------------------------------------------------------------

def _should_stop(
    node: str,
    raw_leaves_set: Set[str],
    raw_leaf_freq: Counter,
    ids_map: Dict[str, str],
) -> bool:
    if node in KANGXI_RADICALS:
        return True
    if node in SINGLE_CHAR_WHITELIST:
        return True
    if raw_leaf_freq.get(node, 0) >= 5:
        return True
    if node in raw_leaves_set:
        return True
    if node not in ids_map:
        return True
    return False


def _expand_expr(
    expr: str,
    raw_leaves_set: Set[str],
    ids_map: Dict[str, str],
    raw_leaf_freq: Counter,
    parent_layout: Optional[str] = None,
    child_index: Optional[int] = None,
    stack: Optional[Set[str]] = None,
) -> List[Tuple[str, Optional[str], Optional[int]]]:
    """Expand an IDS (sub-)expression; returns leaves with parent-layout context."""
    if not expr:
        return []
    if _is_idc(expr[0]):
        try:
            layout, children = parse_children(expr)
        except Exception:
            return []
        out: List[Tuple[str, Optional[str], Optional[int]]] = []
        for idx, child_expr in enumerate(children):
            out.extend(_expand_expr(
                child_expr, raw_leaves_set, ids_map, raw_leaf_freq,
                parent_layout=layout, child_index=idx, stack=stack,
            ))
        return out
    node = expr if len(expr) == 1 else expr[0]
    return _expand_node(
        node, raw_leaves_set, ids_map, raw_leaf_freq,
        parent_layout, child_index, stack,
    )


def _expand_node(
    node: str,
    raw_leaves_set: Set[str],
    ids_map: Dict[str, str],
    raw_leaf_freq: Counter,
    parent_layout: Optional[str] = None,
    child_index: Optional[int] = None,
    stack: Optional[Set[str]] = None,
) -> List[Tuple[str, Optional[str], Optional[int]]]:
    """Expand a single-character node; returns leaves with parent-layout context."""
    if is_unknown_numbered_component(node):
        return []
    if _should_stop(node, raw_leaves_set, raw_leaf_freq, ids_map):
        return [(node, parent_layout, child_index)]
    if stack is None:
        stack = set()
    if node in stack:
        return [(node, parent_layout, child_index)]
    stack.add(node)
    try:
        ids = ids_map.get(node, "")
        try:
            layout, children = parse_children(ids)
        except Exception:
            return [(node, parent_layout, child_index)]
        if not children:
            return [(node, parent_layout, child_index)]
        out: List[Tuple[str, Optional[str], Optional[int]]] = []
        for idx, child_expr in enumerate(children):
            out.extend(_expand_expr(
                child_expr, raw_leaves_set, ids_map, raw_leaf_freq,
                parent_layout=layout, child_index=idx, stack=stack,
            ))
        return out if out else [(node, parent_layout, child_index)]
    finally:
        stack.discard(node)


def build_retrieval_for_entry(
    entry: dict,
    ids_map: Dict[str, str],
    raw_leaf_freq: Counter,
    warnings: List[dict],
) -> Tuple[List[str], List[str]]:
    """Build retrieval_top_level and retrieval_components for one bank entry.

    Algorithm:
    1. Start from top_level_components (NOT IDS root).
    2. Expand each top-level node until a stop condition.
    3. Post-process: filter strokes → NORM → TRAD_SIMP.
    4. Hard constraint: len(result) <= len(leaf_components).
    """
    ch = entry.get("character", "")
    top_level = list(entry.get("top_level_components", []) or [])
    raw_leaves = list(entry.get("leaf_components", []) or [])
    raw_leaves_set = set(raw_leaves)
    ids_str = entry.get("ids", "") or ids_map.get(ch, "")
    context = {
        "character": ch,
        "bank_id": entry.get("bank_id"),
        "ids": ids_str,
    }

    top_layout: Optional[str] = None
    try:
        parsed_layout, _ = parse_children(ids_str)
        if parsed_layout:
            top_layout = parsed_layout
    except Exception:
        pass

    # --- retrieval_top_level: normalize top_level directly ---
    retrieval_top_level: List[str] = []
    for idx, t in enumerate(top_level):
        c = _normalize_one(t, top_layout, idx, warnings, context)
        if not _is_stroke_primitive(c):
            retrieval_top_level.append(c)
    if not retrieval_top_level and ch:
        retrieval_top_level = [_normalize_one(ch, None, None, warnings, context)]

    # --- retrieval_components: expand from top_level ---
    tracked: List[Tuple[str, Optional[str], Optional[int]]] = []
    for idx, t in enumerate(top_level):
        if t and _is_idc(t[0]):
            expanded = _expand_expr(
                t, raw_leaves_set, ids_map, raw_leaf_freq,
                parent_layout=top_layout, child_index=idx,
            )
        else:
            expanded = _expand_node(
                t, raw_leaves_set, ids_map, raw_leaf_freq,
                parent_layout=top_layout, child_index=idx,
            )
        tracked.extend(expanded)

    # Post-process pipeline: filter strokes → normalize → trad_simp
    result: List[str] = []
    for comp, pl, ci in tracked:
        if _is_stroke_primitive(comp):
            continue
        c = _normalize_one(comp, pl, ci, warnings, context)
        result.append(c)

    if not result and ch:
        result = [_normalize_one(ch, None, None, warnings, context)]

    # If raw_leaves is empty (raw parser filtered everything), fallback to retrieval_top_level.
    # This avoids collapsing to whole-character token and keeps retrieval useful.
    if not raw_leaves:
        if ch in SINGLE_CHAR_WHITELIST and ch:
            return retrieval_top_level, sanitize_retrieval(
                [_normalize_one(ch, None, None, warnings, context)], ch
            )
        result = list(retrieval_top_level)
        if not result and ch:
            result = [_normalize_one(ch, None, None, warnings, context)]
        return retrieval_top_level, sanitize_retrieval(result, ch)

    # Hard constraint: retrieval must never be more granular than raw
    if raw_leaves and len(result) > len(raw_leaves):
        warnings.append({
            "type": "length_violation_fallback",
            "character": ch,
            "bank_id": entry.get("bank_id"),
            "raw_len": len(raw_leaves),
            "retrieval_before_fallback": list(result),
        })
        # Fallback 1: use normalized top_level
        result = list(retrieval_top_level)
        # Fallback 2: still too long → collapse to single character
        if len(result) > len(raw_leaves):
            result = [_normalize_one(ch, None, None, warnings, context)]

    return retrieval_top_level, sanitize_retrieval(result, ch)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    decomp = json.loads(DECOMP_PATH.read_text(encoding="utf-8"))
    ids_map = load_merged_ids(IDS_PATH)

    # Global raw leaf frequency
    raw_leaf_freq: Counter = Counter()
    for row in bank:
        for comp in row.get("leaf_components", []) or []:
            raw_leaf_freq[comp] += 1

    leaf_freq_top100 = [
        {"component": c, "freq": f} for c, f in raw_leaf_freq.most_common(100)
    ]
    LEAF_FREQ_PATH.write_text(
        json.dumps(
            {"total_unique_raw_leaf_components": len(raw_leaf_freq), "top_100": leaf_freq_top100},
            ensure_ascii=False, indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    # Save old retrieval for comparison in report
    old_retrieval_map: Dict[str, List[str]] = {}
    for row in bank:
        bid = row.get("bank_id", "")
        old_retrieval_map[bid] = list(row.get("retrieval_components", []) or [])

    # Build retrieval
    warnings: List[dict] = []
    for row in bank:
        rtl, rc = build_retrieval_for_entry(row, ids_map, raw_leaf_freq, warnings)
        row["retrieval_top_level"] = rtl
        row["retrieval_components"] = rc

    BANK_PATH.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 8 target cases (may or may not be in bank)
    target_results: Dict[str, dict] = {}
    for ch in TARGET_CHARS:
        top_level_raw: List[str] = []
        raw_leaves: List[str] = []
        if ch in decomp:
            top_level_raw = decomp[ch].get("top_level_components", []) or []
            raw_leaves = decomp[ch].get("leaf_components", []) or []
        elif ch in ids_map:
            try:
                _, top_level_raw = parse_children(ids_map[ch])
            except Exception:
                pass
        fake_entry = {
            "character": ch,
            "bank_id": None,
            "ids": ids_map.get(ch, ""),
            "top_level_components": top_level_raw,
            "leaf_components": raw_leaves,
        }
        rtl, rc = build_retrieval_for_entry(fake_entry, ids_map, raw_leaf_freq, warnings)
        target_results[ch] = {
            "retrieval_top_level": rtl,
            "retrieval_components": rc,
            "raw_leaves": raw_leaves,
        }

    # ---------- Validation ----------

    # V1: hard constraint violations
    length_violations = []
    raw_empty_entries = []
    for row in bank:
        rl = len(row.get("retrieval_components", []) or [])
        ll = len(row.get("leaf_components", []) or [])
        if ll == 0:
            raw_empty_entries.append({
                "bank_id": row.get("bank_id"),
                "character": row.get("character"),
                "retrieval": row.get("retrieval_components", []),
            })
        elif rl > ll:
            length_violations.append({
                "bank_id": row.get("bank_id"),
                "character": row.get("character"),
                "raw_len": ll,
                "retrieval_len": rl,
            })

    # V2: NORM source residuals in retrieval_components
    norm_residuals: Counter = Counter()
    for row in bank:
        for c in row.get("retrieval_components", []) or []:
            if c in NORM_SOURCES:
                norm_residuals[c] += 1

    # V3: stroke primitive residuals in retrieval_components
    stroke_residuals: Counter = Counter()
    for row in bank:
        for c in row.get("retrieval_components", []) or []:
            if _is_stroke_primitive(c):
                stroke_residuals[c] += 1

    # Sample 20
    sample_rows = []
    for row in bank[:20]:
        bid = row.get("bank_id", "")
        sample_rows.append({
            "bank_id": bid,
            "character": row.get("character"),
            "raw_leaves": row.get("leaf_components", []),
            "old_retrieval": old_retrieval_map.get(bid, []),
            "new_retrieval": row.get("retrieval_components", []),
        })

    # Stats
    retrieval_lengths = [len(row.get("retrieval_components", []) or []) for row in bank]
    avg_retrieval_len = sum(retrieval_lengths) / len(retrieval_lengths) if retrieval_lengths else 0.0

    retrieval_freq: Counter = Counter()
    unique_retrieval_set: Set[str] = set()
    for row in bank:
        for c in row.get("retrieval_components", []) or []:
            retrieval_freq[c] += 1
            unique_retrieval_set.add(c)
    retrieval_top50 = retrieval_freq.most_common(50)

    # 阝 unresolved warnings
    fuyi_warnings = [w for w in warnings if w.get("type") == "unresolved_fu_yi"]
    fallback_warnings = [w for w in warnings if w.get("type") == "length_violation_fallback"]
    bank_by_id = {row.get("bank_id"): row for row in bank}
    fallback_samples = []
    for w in fallback_warnings[:10]:
        bid = w.get("bank_id")
        row = bank_by_id.get(bid, {})
        fallback_samples.append({
            "bank_id": bid,
            "character": w.get("character"),
            "before_fallback": w.get("retrieval_before_fallback", []),
            "after_fallback": row.get("retrieval_components", []),
        })

    # Required residual check after NORM extension
    must_disappear = ["丷", "⺊", "𠂉", "𠂊", "⺌", "丆", "𠂆", "コ"]
    disappear_residuals = {c: retrieval_freq.get(c, 0) for c in must_disappear}

    # Edge freq (3-5)
    edge_components = sorted(
        [{"component": c, "freq": f} for c, f in raw_leaf_freq.items() if 3 <= f <= 5],
        key=lambda x: (-x["freq"], x["component"]),
    )[:20]

    # Missing whitelist high-freq
    missing_wl = []
    for c, f in raw_leaf_freq.most_common():
        if f < 20:
            break
        if c not in SINGLE_CHAR_WHITELIST and c not in KANGXI_RADICALS:
            missing_wl.append({"component": c, "freq": f})
    missing_wl = missing_wl[:20]

    # Normalization edge cases
    norm_edge = []
    for c in ["月", "阝", "阜", "邑", "艸", "辵", "糸", "車", "车", "貝", "贝"]:
        if c in retrieval_freq:
            norm_edge.append({"component": c, "retrieval_freq": retrieval_freq[c]})

    # ---------- Report ----------
    L: List[str] = []
    L.append("# Retrieval Components Report")
    L.append("")
    L.append("## 1) 规则")
    L.append("- 起点: `top_level_components`（不是 IDS 根）")
    L.append("- 停止: 康熙部首 / 独体字白名单 / raw leaf freq>=5 / 节点在 raw_leaves / 无法再拆")
    L.append("- 后处理: 过滤笔画原语 → NORM → TRAD_SIMP（统一繁体）")
    L.append("- 硬约束: `len(retrieval_components) <= len(leaf_components)`")
    L.append("")

    L.append("## 2) Bug 修复验证")
    L.append("")
    L.append("### Bug 1: 硬约束检查")
    L.append(f"- 违反 `len(retrieval) <= len(raw)` 的条目数（raw_len>0）: **{len(length_violations)}**")
    if length_violations:
        for v in length_violations[:20]:
            L.append(f"  - {v['bank_id']} {v['character']}: raw={v['raw_len']} retrieval={v['retrieval_len']}")
    L.append(f"- raw_leaves 为空的条目（raw parser 全部过滤，retrieval 退回 retrieval_top_level）: **{len(raw_empty_entries)}**")
    if raw_empty_entries:
        for e in raw_empty_entries[:10]:
            L.append(f"  - {e['bank_id']} {e['character']}: retrieval={e['retrieval']}")
    L.append("")

    L.append("### Bug 2: NORM 残留检查")
    L.append(f"- retrieval_components 中 NORM 源形式总出现次数: **{sum(norm_residuals.values())}**")
    if norm_residuals:
        for c, n in norm_residuals.most_common():
            L.append(f"  - {c}: {n}")
    L.append("")

    L.append("### Bug 3: 笔画原语残留检查")
    L.append(f"- retrieval_components 中笔画原语总出现次数: **{sum(stroke_residuals.values())}**")
    if stroke_residuals:
        for c, n in stroke_residuals.most_common():
            L.append(f"  - {c}: {n}")
    L.append("")

    L.append("### Bug 4: 繁简统一（TRAD_SIMP）")
    trad_simp_residuals: Counter = Counter()
    for row in bank:
        for c in row.get("retrieval_components", []) or []:
            if c in TRAD_SIMP:
                trad_simp_residuals[c] += 1
    L.append(f"- retrieval_components 中仍含简体源形式的次数: **{sum(trad_simp_residuals.values())}**")
    if trad_simp_residuals:
        for c, n in trad_simp_residuals.most_common():
            L.append(f"  - {c}: {n}")
    L.append("")

    L.append("### NORM 扩展残留检查（应全部为 0）")
    for c in ["丷", "⺊", "𠂉", "𠂊", "⺌", "丆", "𠂆", "コ"]:
        L.append(f"  - {c}: {disappear_residuals.get(c, 0)}")
    L.append("")

    L.append(f"### 安全闸触发（len 超限后 fallback 到 top_level）: {len(fallback_warnings)} 次")
    if fallback_samples:
        L.append("- 抽样 10 条（before_fallback -> after_fallback）:")
        for w in fallback_samples:
            L.append(
                f"  - {w.get('bank_id')} {w.get('character')}: "
                f"{w.get('before_fallback')} -> {w.get('after_fallback')}"
            )
    L.append("")

    L.append("### Parser 排查说明（婁 / 軍）")
    L.append("- `ids.txt` 中这两个字无条目；`ids_full.txt` 中：`婁=⿱⑧女`，`軍=⿱冖車`。")
    L.append("- `軍` 可正常解析；`婁` 含未知编号 `⑧`，属于已知未知部件（partial extraction）。")
    L.append("- 本轮 target case 出现空 raw_leaves 的主要原因不是 parser 报错，而是这两个字不在当前 decomp 子集（OCR 字集驱动）中。")
    L.append("- 已按规则修正 raw_leaves 为空时的 fallback：改为 `retrieval_top_level`，不再退回整字。")
    L.append("")

    L.append("## 3) 8 个 target case")
    for ch in TARGET_CHARS:
        rec = target_results[ch]
        L.append(
            f"- {ch}: raw_leaves={rec['raw_leaves']} | "
            f"retrieval_top_level={rec['retrieval_top_level']} | "
            f"retrieval_components={rec['retrieval_components']}"
        )
    L.append("")

    L.append("## 4) 抽样 20 条 old vs new retrieval")
    for row in sample_rows:
        L.append(
            f"- {row['bank_id']} {row['character']}: "
            f"raw={row['raw_leaves']} | "
            f"old={row['old_retrieval']} → new={row['new_retrieval']}"
        )
    L.append("")

    L.append("## 5) 统计")
    L.append(f"- bank 条目数: {len(bank)}")
    L.append(f"- retrieval_components 平均长度: {avg_retrieval_len:.4f}")
    L.append(f"- 去重 unique retrieval_components 数: {len(unique_retrieval_set)}")
    L.append("- retrieval_components 频次 top-50（归一化后）:")
    for c, f in retrieval_top50:
        L.append(f"  - {c}: {f}")
    L.append("")

    L.append("## 6) 人工复核清单")
    L.append(f"### 阝 无法判断左右位置: {len(fuyi_warnings)} 条")
    for w in fuyi_warnings[:30]:
        L.append(
            f"  - char={w.get('character')}, bank_id={w.get('bank_id')}, "
            f"layout={w.get('parent_layout')}, idx={w.get('child_index')}, ids={w.get('ids')}"
        )
    L.append("")
    L.append("### 频次边缘（3-5）组件 top-20:")
    for item in edge_components:
        L.append(f"  - {item['component']}: {item['freq']}")
    L.append("")
    L.append("### 白名单未覆盖但高频（freq>=20）:")
    for item in missing_wl:
        L.append(f"  - {item['component']}: {item['freq']}")
    L.append("")
    L.append("### Normalization edge cases:")
    for item in norm_edge:
        L.append(f"  - {item['component']}: {item['retrieval_freq']}")

    REPORT_PATH.write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"updated bank: {BANK_PATH}")
    print(f"wrote leaf freq: {LEAF_FREQ_PATH}")
    print(f"wrote report: {REPORT_PATH}")
    print(f"unresolved 阝: {len(fuyi_warnings)}")
    print(f"length constraint violations: {len(length_violations)}")
    print(f"fallback triggers: {len(fallback_warnings)}")
    print(f"NORM residuals: {sum(norm_residuals.values())}")
    print(f"stroke residuals: {sum(stroke_residuals.values())}")


if __name__ == "__main__":
    main()
