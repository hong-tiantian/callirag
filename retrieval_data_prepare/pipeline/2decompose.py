# -*- coding: utf-8 -*-
"""
读取 CHISE/CJKVI 风格 ids.txt（每行：U+XXXX<TAB>字<TAB>IDS），
按 IDS 解析为部件序列，并对仍存在于映射中的部件递归展开到叶子。
结果缓存到 retrieval_data_prepare/bank/decomp.json。
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

RAG_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IDS = RAG_ROOT / "assets" / "ids" / "ids.txt"
DEFAULT_IDS_FULL = RAG_ROOT / "assets" / "ids" / "ids_full.txt"
DEFAULT_CACHE = RAG_ROOT / "bank" / "decomp.json"
DEFAULT_CSV = RAG_ROOT / "cases" / "wxz_gt_chars.csv"
DEFAULT_UNIHAN_STROKES = RAG_ROOT / "assets" / "unihan" / "Unihan_IRGSources.txt"
DEFAULT_UNIHAN_VARIANTS = RAG_ROOT / "assets" / "unihan" / "Unihan_Variants.txt"
UNICODE_UNIHAN_ZIP_URL = "https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip"

# Unicode IDS：二元/三元结构符及其子节点个数（U+2FF0–U+2FFB）
IDC_ARITY: Dict[str, int] = {
    "\u2ff0": 2,  # ⿰
    "\u2ff1": 2,  # ⿱
    "\u2ff2": 3,  # ⿲
    "\u2ff3": 3,  # ⿳
    "\u2ff4": 2,  # ⿴
    "\u2ff5": 2,  # ⿵
    "\u2ff6": 2,  # ⿶
    "\u2ff7": 2,  # ⿷
    "\u2ff8": 2,  # ⿸
    "\u2ff9": 2,  # ⿹
    "\u2ffa": 2,  # ⿺
    "\u2ffb": 2,  # ⿻
}

# 常见“笔画/极小部件”字符。若某字下一层包含这些，通常应在该字停止继续下钻。
STROKE_LIKE_UNITS: Set[str] = {
    "一",
    "丨",
    "丿",
    "丶",
    "乀",
    "乁",
    "乙",
    "乚",
    "亅",
    "乛",
    "𠃊",
    "𠃋",
    "𠃌",
    "𠃍",
    "𠃑",
    "𠃓",
    "𠄌",
    "𠄎",
    "𡿨",
    "㇀",
    "㇁",
    "㇂",
    "㇃",
    "㇄",
    "㇅",
    "㇆",
    "㇇",
    "㇈",
    "㇉",
    "㇊",
    "㇋",
    "㇌",
    "㇍",
    "㇎",
    "㇏",
    "㇐",
    "㇑",
    "㇒",
    "㇓",
    "㇔",
    "㇕",
    "㇖",
    "㇗",
    "㇘",
    "㇙",
    "㇚",
    "㇛",
    "㇜",
    "㇝",
    "㇞",
    "㇟",
    "㇠",
    "㇡",
    "㇢",
    "㇣",
    "亠",
    "幺",
    "小",
}

# 在“部件级”展示时，按字形体系偏好替换为常见部件形体。
TRAD_COMPONENT_PREFERRED: Dict[str, str] = {
    "糸": "糹",
}
SIMP_COMPONENT_PREFERRED: Dict[str, str] = {
    "糹": "纟",
}

LINE_RE = re.compile(
    r"^U\+([0-9A-Fa-f]+)\s+(\S)\s+(.*)$",
    re.UNICODE,
)
IDS_TAG_RE = re.compile(r"\[[^\]]*\]")
UNICODE_CODE_RE = re.compile(r"U\+([0-9A-F]{4,6})")


def _code_to_char(code: str) -> str:
    return chr(int(code, 16))


def ensure_unihan_file(local_path: Path, filename: str, auto_download: bool = False) -> None:
    if local_path.is_file() or not auto_download:
        return
    local_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp_zip = Path(tmp.name)
    try:
        urllib.request.urlretrieve(UNICODE_UNIHAN_ZIP_URL, str(tmp_zip))
        with zipfile.ZipFile(tmp_zip) as zf:
            with zf.open(filename) as src, local_path.open("wb") as dst:
                dst.write(src.read())
    finally:
        try:
            tmp_zip.unlink(missing_ok=True)
        except Exception:
            pass


def _idc_arity(ch: str) -> int:
    if ch in IDC_ARITY:
        return IDC_ARITY[ch]
    o = ord(ch)
    if 0x2FF0 <= o <= 0x2FFB:
        return 2
    raise ValueError(f"非 IDS 结构符: U+{o:04X} {ch!r}")


def _is_idc(ch: str) -> bool:
    if not ch:
        return False
    o = ord(ch)
    return ch in IDC_ARITY or (0x2FF0 <= o <= 0x2FFB)


def _clean_ids(ids: str) -> str:
    """去除 IDS 字符串中的 [GJK]/[TV] 等方括号标注。"""
    return IDS_TAG_RE.sub("", ids or "").strip()


def _is_cjk_ideograph(ch: str) -> bool:
    """粗略判断是否为 CJK 表意文字（用于区分“部件”与“笔画符号”）。"""
    if not ch:
        return False
    o = ord(ch)
    return (
        0x3400 <= o <= 0x4DBF
        or 0x4E00 <= o <= 0x9FFF
        or 0xF900 <= o <= 0xFAFF
        or 0x20000 <= o <= 0x2A6DF
        or 0x2A700 <= o <= 0x2B73F
        or 0x2B740 <= o <= 0x2B81F
        or 0x2B820 <= o <= 0x2CEAF
        or 0x2CEB0 <= o <= 0x2EBEF
        or 0x30000 <= o <= 0x3134F
    )


def _looks_like_stroke_level(leaves: List[str]) -> bool:
    """
    若一个分解叶子序列里出现大量非汉字符号（如 𠃊/丶/② 等），
    认为其已接近笔画级，应停止继续向下递归。
    """
    if not leaves:
        return False
    return any((x in STROKE_LIKE_UNITS) or (not _is_cjk_ideograph(x)) for x in leaves)


def _is_stroke_primitive(ch: str) -> bool:
    """是否为笔画级原语（含 U+31C0-U+31EF 与常见笔画符号）。"""
    if not ch:
        return False
    o = ord(ch)
    return (0x31C0 <= o <= 0x31EF) or (ch in STROKE_LIKE_UNITS)


def _is_unknown_component(ch: str) -> bool:
    """是否为未知部件编号 ①-⑳（U+2460-U+2473）。"""
    if not ch:
        return False
    o = ord(ch)
    return 0x2460 <= o <= 0x2473


def parse_ids_top_level(ids: str) -> Tuple[str, List[str]]:
    """解析 IDS 顶层结构：返回 (layout, top_level_components)。"""
    s = _clean_ids(ids)
    if not s:
        return "", []
    if not _is_idc(s[0]):
        return "", [s[0]]

    def read_expr(i: int) -> Tuple[str, int]:
        if i >= len(s):
            raise ValueError("IDS 意外结束")
        ch = s[i]
        if not _is_idc(ch):
            return ch, i + 1
        n = _idc_arity(ch)
        i += 1
        parts: List[str] = []
        for _ in range(n):
            one, i = read_expr(i)
            parts.append(one)
        return ch + "".join(parts), i

    layout = s[0]
    n = _idc_arity(layout)
    i = 1
    children: List[str] = []
    for _ in range(n):
        c, i = read_expr(i)
        children.append(c)
    if i != len(s):
        raise ValueError(f"IDS 解析后仍有残留: {s[i:]!r} (完整: {s!r})")
    return layout, children


def parse_ids_leaves(ids: str) -> List[str]:
    """将一条 IDS 字符串解析为按书写顺序展开的叶子字符列表（仅解析本串，不查表递归）。"""
    s = _clean_ids(ids)
    if not s:
        return []
    if not _is_idc(s[0]):
        return [s[0]]

    def component(i: int) -> Tuple[List[str], int]:
        if i >= len(s):
            raise ValueError("IDS 意外结束")
        ch = s[i]
        if _is_idc(ch):
            return expr(i)
        return [ch], i + 1

    def expr(i: int) -> Tuple[List[str], int]:
        if i >= len(s):
            raise ValueError("IDS 意外结束")
        ch = s[i]
        if not _is_idc(ch):
            raise ValueError(f"期望 IDS 结构符，得到 {ch!r} @ {i}")
        n = _idc_arity(ch)
        i += 1
        out: List[str] = []
        for _ in range(n):
            part, i = component(i)
            out.extend(part)
        return out, i

    leaves, end = expr(0)
    if end != len(s):
        raise ValueError(f"IDS 解析后仍有残留: {s[end:]!r} (完整: {s!r})")
    return leaves


def load_ids_txt(path: Path) -> Dict[str, str]:
    """char -> ids 字符串（不含首尾空白）。"""
    m: Dict[str, str] = {}
    if not path.is_file():
        return m
    text = path.read_text(encoding="utf-8", errors="replace")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "\t" in raw:
            parts = raw.rstrip("\n").split("\t")
            if len(parts) >= 3 and parts[0].upper().startswith("U+"):
                _, ch_field, ids = parts[0].strip(), parts[1].strip(), parts[2].strip()
                ch = ch_field[0]
                m[ch] = _clean_ids(ids)
                continue
        mo = LINE_RE.match(line)
        if mo:
            ch = mo.group(2)[0]
            ids = mo.group(3).strip()
            m[ch] = _clean_ids(ids)
    return m


def load_merged_ids(base_path: Path) -> Dict[str, str]:
    """
    读取 IDS 映射：
    - 若同目录存在 ids_full.txt，先载入全量；
    - 再用 base_path（默认 ids.txt）覆盖同字条目。
    """
    merged: Dict[str, str] = {}
    full_path = base_path.parent / "ids_full.txt"
    if full_path.is_file():
        merged.update(load_ids_txt(full_path))
    if base_path.is_file():
        merged.update(load_ids_txt(base_path))
    return merged


def load_strokes_map(path: Path) -> Dict[str, int]:
    """读取 Unihan_IRGSources.txt 的 kTotalStrokes。"""
    out: Dict[str, int] = {}
    if not path.is_file():
        return out
    text = path.read_text(encoding="utf-8", errors="replace")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        code, prop, value = parts[0], parts[1], parts[2]
        if prop != "kTotalStrokes" or not code.startswith("U+"):
            continue
        m = re.search(r"\d+", value)
        if not m:
            continue
        out[_code_to_char(code[2:])] = int(m.group(0))
    return out


def load_script_variant_maps(path: Path) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """
    返回 (simp_to_trad, trad_to_simp):
    - simp_to_trad: 简体字 -> 可能繁体列表（来自 kTraditionalVariant）
    - trad_to_simp: 繁体字 -> 可能简体列表（来自 kSimplifiedVariant）
    """
    simp_to_trad: Dict[str, List[str]] = {}
    trad_to_simp: Dict[str, List[str]] = {}
    if not path.is_file():
        return simp_to_trad, trad_to_simp

    text = path.read_text(encoding="utf-8", errors="replace")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        code, prop, value = parts[0], parts[1], parts[2]
        if not code.startswith("U+"):
            continue
        src = _code_to_char(code[2:])
        targets = [_code_to_char(m.group(1)) for m in UNICODE_CODE_RE.finditer(value)]
        if not targets:
            continue
        if prop == "kTraditionalVariant":
            simp_to_trad[src] = targets
        elif prop == "kSimplifiedVariant":
            trad_to_simp[src] = targets
    return simp_to_trad, trad_to_simp


def classify_script(ch: str, simp_to_trad: Dict[str, List[str]], trad_to_simp: Dict[str, List[str]]) -> str:
    """返回 simplified/traditional/common。"""
    has_trad = ch in simp_to_trad
    has_simp = ch in trad_to_simp
    if has_simp and not has_trad:
        return "traditional"
    if has_trad and not has_simp:
        return "simplified"
    return "common"


def normalize_component_script(
    c: str,
    script: str,
    simp_to_trad: Dict[str, List[str]],
    trad_to_simp: Dict[str, List[str]],
) -> str:
    if script == "traditional":
        if c in TRAD_COMPONENT_PREFERRED:
            return TRAD_COMPONENT_PREFERRED[c]
        alts = simp_to_trad.get(c, [])
        return alts[0] if alts else c
    if script == "simplified":
        if c in SIMP_COMPONENT_PREFERRED:
            return SIMP_COMPONENT_PREFERRED[c]
        alts = trad_to_simp.get(c, [])
        return alts[0] if alts else c
    return c


def expand_recursive(ch: str, ids_map: Dict[str, str], stack: Set[str]) -> List[str]:
    """递归展开：先解析 ch 的 IDS 叶子序列，再对每个仍存在于映射中的字符继续展开。"""
    if ch not in ids_map:
        return [ch]
    if ch in stack:
        return [ch]
    stack.add(ch)
    try:
        ids = ids_map[ch]
        try:
            seq = parse_ids_leaves(ids)
        except Exception:
            return [ch]
        out: List[str] = []
        for c in seq:
            out.extend(expand_recursive(c, ids_map, stack))
        return out
    finally:
        stack.discard(ch)


def expand_to_components(ch: str, ids_map: Dict[str, str], stack: Set[str]) -> List[str]:
    leaves, _ = expand_to_components_with_flags(ch, ids_map, stack)
    return leaves


def expand_to_components_with_flags(
    ch: str, ids_map: Dict[str, str], stack: Set[str]
) -> Tuple[List[str], bool]:
    """
    递归展开到“部件级”并携带异常标记：
    - 笔画原语视为停止符，不写入 leaves。
    - 若当前节点直接子元素全部是笔画原语，则保留当前字符作为 leaf。
    - 未知部件编号 ①-⑳ 不触发整字 fallback，执行 partial extraction，
      并在返回值中标记 has_unknown=True。
    """
    if _is_unknown_component(ch):
        return [], True
    if _is_stroke_primitive(ch):
        return [], False
    if ch not in ids_map:
        return [ch], False
    if ch in stack:
        return [ch], False

    ids = ids_map.get(ch, "")
    try:
        seq = parse_ids_leaves(ids)
    except Exception:
        return [ch], False
    if not seq:
        return [ch], False

    stack.add(ch)
    try:
        out: List[str] = []
        has_unknown = False
        total_children = 0
        stroke_children = 0

        for c in seq:
            total_children += 1
            if _is_unknown_component(c):
                has_unknown = True
                continue
            if _is_stroke_primitive(c):
                stroke_children += 1
                continue
            child_leaves, child_unknown = expand_to_components_with_flags(c, ids_map, stack)
            has_unknown = has_unknown or child_unknown
            out.extend(child_leaves)

        if out:
            return out, has_unknown
        if total_children > 0 and stroke_children == total_children:
            # 例如：七 -> ⿻㇀乚，子元素均为笔画原语时保留当前字
            return [ch], has_unknown
        return [], has_unknown
    finally:
        stack.discard(ch)


def char_stroke_count(ch: str, strokes_map: Dict[str, int]) -> Optional[int]:
    """真实笔画数（来自 Unihan kTotalStrokes）；无数据时返回 None。"""
    return strokes_map.get(ch)


def build_decomp(
    ids_map: Dict[str, str],
    chars: List[str],
    strokes_map: Dict[str, int],
    simp_to_trad: Dict[str, List[str]],
    trad_to_simp: Dict[str, List[str]],
    meta_map: Optional[Dict[str, dict]] = None,
) -> Dict[str, dict]:
    bank: Dict[str, dict] = {}
    meta_map = meta_map or {}
    for ch in chars:
        ids = ids_map.get(ch, "")
        try:
            layout, top_level_components = parse_ids_top_level(ids) if ids else ("", [])
        except Exception:
            layout, top_level_components = "", []
        script = classify_script(ch, simp_to_trad, trad_to_simp)
        leaf_components, has_unknown = (
            expand_to_components_with_flags(ch, ids_map, set()) if ch in ids_map else ([ch], False)
        )
        stroke_count = char_stroke_count(ch, strokes_map)
        meta = meta_map.get(ch, {})
        bank[ch] = {
            "character": ch,
            "id": meta.get("id"),
            "path": meta.get("path"),
            "freq": meta.get("freq", None),
            "script": script,
            "ids": ids,
            "layout": layout,
            "top_level_components": top_level_components,
            "leaf_components": leaf_components,
            "has_unknown": has_unknown,
            "stroke_count": stroke_count,
        }
    return bank


def load_cache(path: Path) -> Dict[str, dict]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(path: Path, data: Dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_gt_csv(csv_path: Path, bank: Dict[str, dict], char_col: str = "字符") -> None:
    if not csv_path.is_file():
        return
    rows: List[dict] = []
    fieldnames: List[str] | None = None
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if "分解" not in fieldnames:
            fieldnames.append("分解")
        for row in reader:
            ch = (row.get(char_col) or "").strip()
            if ch and ch in bank:
                row["分解"] = "·".join(bank[ch].get("leaf_components", []))
            else:
                row.setdefault("分解", "")
            rows.append(row)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_chars_from_csv(csv_path: Path, char_col: str = "字符") -> List[str]:
    """从标注 CSV 读取字符列，按出现顺序去重。"""
    if not csv_path.is_file():
        return []
    out: List[str] = []
    seen: Set[str] = set()
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ch = (row.get(char_col) or "").strip()
            if not ch or ch in seen:
                continue
            seen.add(ch)
            out.append(ch)
    return out


def load_char_meta_from_csv(
    csv_path: Path,
    char_col: str = "字符",
    id_col: str = "编号",
) -> Dict[str, dict]:
    """
    从 CSV 读取每个字符的元信息：
    - id: 原图编号
    - path: 相对路径（默认 retrieval_data_prepare/cases/content/{id}.jpg）
    - freq: 先固定为 None
    """
    meta: Dict[str, dict] = {}
    if not csv_path.is_file():
        return meta
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ch = (row.get(char_col) or "").strip()
            img_id = (row.get(id_col) or "").strip()
            if not ch:
                continue
            rel_path = ""
            if img_id:
                rel_path = f"retrieval_data_prepare/cases/content/{img_id}.jpg"
            # 同字符若重复出现，保留首次出现的 id/path。
            if ch not in meta:
                meta[ch] = {
                    "id": img_id or None,
                    "path": rel_path or None,
                    "freq": None,
                }
    return meta


def main() -> None:
    ap = argparse.ArgumentParser(description="IDS 递归分解并缓存")
    ap.add_argument("--ids", type=Path, default=DEFAULT_IDS, help="ids.txt 路径")
    ap.add_argument("--cache", type=Path, default=DEFAULT_CACHE, help="decomp.json 路径")
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="wxz_gt_chars.csv")
    ap.add_argument(
        "--unihan-strokes",
        type=Path,
        default=DEFAULT_UNIHAN_STROKES,
        help="Unihan_IRGSources.txt 路径（用于 kTotalStrokes）",
    )
    ap.add_argument(
        "--unihan-variants",
        type=Path,
        default=DEFAULT_UNIHAN_VARIANTS,
        help="Unihan_Variants.txt 路径（用于简繁标注与部件归一）",
    )
    ap.add_argument(
        "--download-unihan",
        action="store_true",
        help="若本地缺失，则自动下载 Unihan_IRGSources/Unihan_Variants",
    )
    ap.add_argument(
        "--chars",
        default="",
        help="要写入缓存的字符列表（逗号分隔）；为空时自动从 --csv 的“字符”列读取",
    )
    ap.add_argument("--no-csv", action="store_true", help="不写回 CSV")
    ap.add_argument(
        "--replace-cache",
        action="store_true",
        help="忽略已有 decomp.json，仅写入本次 --chars（默认会与已有缓存合并）",
    )
    args = ap.parse_args()

    ensure_unihan_file(args.unihan_strokes, "Unihan_IRGSources.txt", args.download_unihan)
    ensure_unihan_file(args.unihan_variants, "Unihan_Variants.txt", args.download_unihan)

    ids_map = load_merged_ids(args.ids)
    strokes_map = load_strokes_map(args.unihan_strokes)
    simp_to_trad, trad_to_simp = load_script_variant_maps(args.unihan_variants)
    char_meta = load_char_meta_from_csv(args.csv)
    chars = [c.strip() for c in args.chars.split(",") if c.strip()]
    if not chars:
        chars = load_chars_from_csv(args.csv)
    if not chars:
        raise SystemExit("未提供可分解字符：请传 --chars，或确保 --csv 存在且含“字符”列。")

    cache: Dict[str, dict] = {} if args.replace_cache else load_cache(args.cache)

    new_bank = build_decomp(ids_map, chars, strokes_map, simp_to_trad, trad_to_simp, char_meta)
    cache.update(new_bank)
    save_cache(args.cache, cache)

    for ch in chars:
        rec = new_bank.get(ch, {})
        print(
            f"{ch}\tid={rec.get('id', None)}\tpath={rec.get('path', None)}\tscript={rec.get('script','common')}\t"
            f"ids={rec.get('ids','')}\tlayout={rec.get('layout','')}\t"
            f"top={''.join(rec.get('top_level_components', []))}\t"
            f"leaf={''.join(rec.get('leaf_components', []))}\t"
            f"strokes={rec.get('stroke_count', None)}"
        )

    if not args.no_csv:
        update_gt_csv(args.csv, cache)


if __name__ == "__main__":
    main()
