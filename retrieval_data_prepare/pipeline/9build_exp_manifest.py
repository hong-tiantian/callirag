import json
import os
import re
from pathlib import Path


TARGETS = ["璨", "霆", "鳞", "彎", "瘻", "秦", "赢", "諢"]
CONDITIONS = ["A", "B", "C"]

BASE_DIR = Path(__file__).resolve().parent.parent
BANK_PATH = BASE_DIR / "bank" / "wxz_bank.json"
RETRIEVAL_MD_PATH = BASE_DIR / "bank" / "RETRIEVAL_TEST.md"
RANDOM_BASELINE_PATH = BASE_DIR / "outputs" / "random_baseline_results.json"
OUTPUT_PATH = BASE_DIR / "outputs" / "exp_manifest.jsonl"

# A 组固定绝对路径：按需求写成 forward slash
A_REF_CHAR = "永"
A_REF_PATH = "D:/htt/retrieval_data_prepare/cases/style_wxz1175.jpg"
A_REF_SOURCE = "fixed_baseline"


def unix_drive_to_windows_abs(path_str: str) -> str:
    m = re.match(r"^/([a-zA-Z])/(.*)$", path_str)
    if not m:
        raise RuntimeError(f"Invalid bank wxz_path format (expect /<drive>/...): {path_str}")
    drive = m.group(1).upper()
    rest = m.group(2)
    return f"{drive}:/{rest}"


def parse_structural_top1(md_text: str, target_char: str) -> tuple[str, str]:
    section_pattern = rf"^##\s+{re.escape(target_char)}\s*$"
    section_match = re.search(section_pattern, md_text, flags=re.MULTILINE)
    if not section_match:
        raise RuntimeError(f"Target '{target_char}' not found in RETRIEVAL_TEST.md")

    next_section_match = re.search(r"^##\s+", md_text[section_match.end() :], flags=re.MULTILINE)
    section_text = (
        md_text[section_match.end() : section_match.end() + next_section_match.start()]
        if next_section_match
        else md_text[section_match.end() :]
    )

    marker = "### NEW Slot-Based Top-5"
    marker_idx = section_text.find(marker)
    if marker_idx < 0:
        raise RuntimeError(f"Target '{target_char}' missing '### NEW Slot-Based Top-5' section")

    table_text = section_text[marker_idx + len(marker) :]
    lines = [ln.strip() for ln in table_text.splitlines() if ln.strip().startswith("|")]
    data_lines = [ln for ln in lines if not re.match(r"^\|\s*-+\s*\|", ln)]

    rank1_line = None
    for line in data_lines:
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 9:
            continue
        if parts[0] == "1":
            rank1_line = parts
            break

    if rank1_line is None:
        raise RuntimeError(f"Target '{target_char}' NEW Slot-Based Top-5 missing rank-1 row")

    ref_char = rank1_line[4]
    ref_path_raw = rank1_line[8]
    return ref_char, unix_drive_to_windows_abs(ref_path_raw)


def pick_gt_record(bank_entries: list[dict], target_char: str) -> dict:
    candidates = [x for x in bank_entries if x.get("character") == target_char]
    if not candidates:
        raise RuntimeError(f"GT not found in bank for target '{target_char}'")
    return max(candidates, key=lambda x: float(x.get("ocr_conf", 0.0)))


def must_exist(path_str: str, label: str) -> None:
    if not os.path.exists(path_str):
        raise RuntimeError(f"{label} file not found: {path_str}")


def main() -> None:
    with BANK_PATH.open("r", encoding="utf-8") as f:
        bank_entries = json.load(f)
    with RANDOM_BASELINE_PATH.open("r", encoding="utf-8") as f:
        random_data = json.load(f)
    md_text = RETRIEVAL_MD_PATH.read_text(encoding="utf-8")

    # A 组固定 ref 必须存在，不能替换
    must_exist(A_REF_PATH, "A_ref")

    entries: list[dict] = []
    b_sources: list[str] = []
    c_sources: list[str] = []

    for target in TARGETS:
        gt_record = pick_gt_record(bank_entries, target)
        gt_path = unix_drive_to_windows_abs(gt_record["wxz_path"])
        must_exist(gt_path, f"GT({target})")

        # B: random seed0 top1，严格按 per_seed_runs[0].refs[0]
        if "targets" not in random_data or target not in random_data["targets"]:
            raise RuntimeError(f"random_baseline_results missing target '{target}'")
        target_block = random_data["targets"][target]
        if "per_seed_runs" not in target_block:
            raise RuntimeError(
                f"random_baseline_results target '{target}' missing key 'per_seed_runs'"
            )
        seed_runs = target_block["per_seed_runs"]
        if not seed_runs:
            raise RuntimeError(f"random_baseline_results target '{target}' has empty per_seed_runs")
        first_run = seed_runs[0]
        if "refs" not in first_run or not first_run["refs"]:
            raise RuntimeError(
                f"random_baseline_results target '{target}' missing per_seed_runs[0].refs[0]"
            )
        b_ref = first_run["refs"][0]
        b_ref_char = b_ref["char"]
        b_ref_path = unix_drive_to_windows_abs(b_ref["wxz_path"])
        must_exist(b_ref_path, f"B_ref({target})")

        # C: structural slot top1
        c_ref_char, c_ref_path = parse_structural_top1(md_text, target)
        must_exist(c_ref_path, f"C_ref({target})")

        a_entry = {
            "case_id": f"{target}_A",
            "target_char": target,
            "condition": "A",
            "ref_char": A_REF_CHAR,
            "ref_path": A_REF_PATH,
            "ref_source": A_REF_SOURCE,
            "gt_char": target,
            "gt_path": gt_path,
        }
        b_entry = {
            "case_id": f"{target}_B",
            "target_char": target,
            "condition": "B",
            "ref_char": b_ref_char,
            "ref_path": b_ref_path,
            "ref_source": "random_seed0_top1",
            "gt_char": target,
            "gt_path": gt_path,
        }
        c_entry = {
            "case_id": f"{target}_C",
            "target_char": target,
            "condition": "C",
            "ref_char": c_ref_char,
            "ref_path": c_ref_path,
            "ref_source": "structural_slot_top1",
            "gt_char": target,
            "gt_path": gt_path,
        }

        entries.extend([a_entry, b_entry, c_entry])
        b_sources.append(f"{target}→{b_ref_char}")
        c_sources.append(f"{target}→{c_ref_char}")

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for item in entries:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print("Generated 24 entries:")
    print("  A: 8 entries, all ref=永 (style_wxz1175.jpg)")
    print(f"  B: 8 entries, sources: [{', '.join(b_sources)}]")
    print(f"  C: 8 entries, sources: [{', '.join(c_sources)}]")
    print(f"Manifest written to: {OUTPUT_PATH.resolve().as_posix()}")


if __name__ == "__main__":
    main()
