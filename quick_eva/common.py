from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
BANK_DIR = ROOT / "bank"
OUTPUTS_DIR = ROOT / "outputs"
LAYER1_OUTPUTS_DIR = OUTPUTS_DIR / "layer1"
LAYER2_OUTPUTS_DIR = OUTPUTS_DIR / "layer2"
LEGACY_OUTPUTS_DIR = OUTPUTS_DIR / "legacy"
CASES_DIR = ROOT / "cases"

CASE_MANIFEST_PATH = OUTPUTS_DIR / "case_manifest.csv"
NON_TRIVIAL_PATH = BANK_DIR / "non_trivial_components.json"
BANK_ENRICHED_PATH = BANK_DIR / "bank_enriched.json"
BANK_COVERAGE_PATH = LAYER1_OUTPUTS_DIR / "bank_coverage.csv"
SIM_LAYER_PATH = LAYER1_OUTPUTS_DIR / "sim_layer.json"
TOPK_MANIFEST_PATH = LAYER1_OUTPUTS_DIR / "retrieval_topk_manifest.csv"
LAYER1_VIS_DIR = LAYER1_OUTPUTS_DIR / "layer1_visuals"
LAYER1_ANN_PATH = LAYER1_OUTPUTS_DIR / "layer1_annotation.csv"
LAYER1_RESULT_PATH = LAYER1_OUTPUTS_DIR / "layer1_results.csv"
EXPERIMENT_MANIFEST_PATH = LAYER2_OUTPUTS_DIR / "experiment_manifest.csv"
GEN_OUTPUT_DIR = LAYER2_OUTPUTS_DIR / "generation_outputs"
BLIND_DIR = LAYER2_OUTPUTS_DIR / "blind_images"
BLIND_PAIRS_PATH = LAYER2_OUTPUTS_DIR / "blind_eval_pairs.csv"
GROUP_MAPPING_PATH = LAYER2_OUTPUTS_DIR / "group_mapping_private.csv"
LAYER2_ANN_PATH = LAYER2_OUTPUTS_DIR / "layer2_annotation.csv"
LAYER2_RESULT_PATH = LAYER2_OUTPUTS_DIR / "layer2_results.csv"


STROKE_LEVEL_UNITS = {
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
    "𠄐",
    "𠃊",
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
}


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def repo_relative_path(*parts: str) -> str:
    return (Path(ROOT.name) / Path(*parts)).as_posix()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def is_existing_image(path_value: str | None) -> bool:
    p = normalize_to_windows_path(path_value)
    return p is not None and p.is_file()


def normalize_to_windows_path(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    raw = path_value.strip()
    if not raw:
        return None

    p = Path(raw)
    if p.is_absolute():
        return p

    # Convert "/d/foo/bar.jpg" style to "D:/foo/bar.jpg".
    if raw.startswith("/") and len(raw) > 3 and raw[2] == "/":
        drive = raw[1].upper()
        return Path(f"{drive}:/{raw[3:]}")
    return Path(raw)


def ordered_unique(items: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def stroke_similarity(target_strokes: int | None, cand_strokes: int | None) -> float:
    if target_strokes is None or cand_strokes is None:
        return 0.0
    gap = abs(target_strokes - cand_strokes)
    if gap <= 2:
        return 1.0
    if gap <= 5:
        return 0.5
    return 0.0


def stable_int(text: str, mod: int) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % mod

