import csv
import json
import random
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "retrieval_data_prepare" / "outputs" / "exp_manifest.jsonl"
GT_CSV_PATH = ROOT / "retrieval_data_prepare" / "cases" / "wxz_gt_chars.csv"
CONTENT_DIR = ROOT / "retrieval_data_prepare" / "cases" / "content"
COMPARISON_DIR = ROOT / "retrieval_data_prepare" / "outputs" / "comparison"
BLIND_DIR = ROOT / "retrieval_data_prepare" / "outputs" / "blind"
FONTDIFFUSER_ROOT = ROOT / "baseline_clean" / "FontDiffuser"
CKPT_DIR = FONTDIFFUSER_ROOT / "ckpt"


def load_manifest(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    if len(rows) != 24:
        raise RuntimeError(f"Manifest entry count must be 24, got {len(rows)}")
    return rows


def load_target_to_content_id(path: Path) -> dict[str, str]:
    mapping = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping[row["字符"]] = str(row["编号"]).zfill(4)
    return mapping


def infer_all(rows: list[dict], target_to_id: dict[str, str]) -> list[dict]:
    argv_backup = list(sys.argv)
    cwd_backup = Path.cwd()
    sys.path.insert(0, str(FONTDIFFUSER_ROOT))
    try:
        import os

        os.chdir(FONTDIFFUSER_ROOT)
        sys.argv = [
            str(FONTDIFFUSER_ROOT / "sample.py"),
            f"--ckpt_dir={CKPT_DIR}",
            "--save_image",
            "--device=cuda:0",
            "--algorithm_type=dpmsolver++",
            "--guidance_type=classifier-free",
            "--guidance_scale=7.5",
            "--num_inference_steps=20",
            "--method=multistep",
            "--content_image_path=__dummy__.jpg",
            "--style_image_path=__dummy__.jpg",
            "--save_image_dir=__dummy_out__",
        ]
        from sample import arg_parse, load_fontdiffuer_pipeline, sampling

        args = arg_parse()
        pipe = load_fontdiffuer_pipeline(args=args)
        outputs = []

        for row in rows:
            target_char = row["target_char"]
            if target_char not in target_to_id:
                raise RuntimeError(f"Missing content id for target {target_char}")
            content_path = CONTENT_DIR / f"{target_to_id[target_char]}.jpg"
            if not content_path.exists():
                raise RuntimeError(f"Content image not found: {content_path.as_posix()}")

            style_path = Path(row["ref_path"])
            if not style_path.exists():
                raise RuntimeError(f"Style image not found: {style_path.as_posix()}")

            condition = row["condition"]
            case_id = row["case_id"]
            out_dir = COMPARISON_DIR / condition / case_id
            out_dir.mkdir(parents=True, exist_ok=True)

            args.content_image_path = content_path.as_posix()
            args.style_image_path = style_path.as_posix()
            args.save_image_dir = out_dir.as_posix()
            sampling(args=args, pipe=pipe)

            produced = out_dir / "out_single.png"
            if not produced.exists():
                raise RuntimeError(f"Inference failed, missing output: {produced.as_posix()}")

            final_png = COMPARISON_DIR / condition / f"{case_id}.png"
            shutil.copy2(produced, final_png)
            outputs.append(
                {
                    "case_id": case_id,
                    "condition": condition,
                    "target_char": target_char,
                    "path": final_png,
                }
            )
        return outputs
    finally:
        sys.argv = argv_backup
        sys.path = [p for p in sys.path if p != str(FONTDIFFUSER_ROOT)]
        import os

        os.chdir(cwd_backup)


def build_blind(outputs: list[dict]) -> tuple[Path, Path]:
    BLIND_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)
    shuffled = list(outputs)
    rng.shuffle(shuffled)

    mapping_rows = []
    template_rows = []
    for i, item in enumerate(shuffled):
        blind_name = f"img_{i:02d}.png"
        blind_path = BLIND_DIR / blind_name
        shutil.copy2(item["path"], blind_path)
        mapping_rows.append(
            {
                "blind_name": blind_name,
                "case_id": item["case_id"],
                "condition": item["condition"],
                "target_char": item["target_char"],
            }
        )
        template_rows.append(
            {
                "blind_name": blind_name,
                "identity_ok(0/1)": "",
                "component_ok(0/1)": "",
                "stroke_ok(0/1)": "",
                "overall(1/2/3)": "",
                "note": "",
            }
        )

    mapping_csv = BLIND_DIR / "mapping.csv"
    with mapping_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["blind_name", "case_id", "condition", "target_char"]
        )
        writer.writeheader()
        writer.writerows(mapping_rows)

    template_csv = BLIND_DIR / "scoring_template.csv"
    with template_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "blind_name",
                "identity_ok(0/1)",
                "component_ok(0/1)",
                "stroke_ok(0/1)",
                "overall(1/2/3)",
                "note",
            ],
        )
        writer.writeheader()
        writer.writerows(template_rows)

    return mapping_csv, template_csv


def main() -> None:
    rows = load_manifest(MANIFEST_PATH)
    target_to_id = load_target_to_content_id(GT_CSV_PATH)
    outputs = infer_all(rows, target_to_id)
    mapping_csv, template_csv = build_blind(outputs)

    print("Generated comparison images:")
    for condition in ["A", "B", "C"]:
        cond_paths = [x["path"].as_posix() for x in outputs if x["condition"] == condition]
        print(f"{condition}:")
        for p in cond_paths:
            print(f"  {p}")
    print(f"mapping_csv: {mapping_csv.as_posix()}")
    print(f"scoring_template_csv: {template_csv.as_posix()}")


if __name__ == "__main__":
    main()
