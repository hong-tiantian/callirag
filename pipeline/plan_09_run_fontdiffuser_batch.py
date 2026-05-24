from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from common import EXPERIMENT_MANIFEST_PATH, GEN_OUTPUT_DIR, ROOT, load_csv, normalize_to_windows_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan A step 09: run_fontdiffuser_batch.py")
    parser.add_argument("--experiment-manifest", type=Path, default=EXPERIMENT_MANIFEST_PATH, help="experiment_manifest.csv")
    parser.add_argument(
        "--fontdiffuser-root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "baseline_clean" / "FontDiffuser",
        help="FontDiffuser repo root",
    )
    parser.add_argument("--ckpt-dir", type=Path, default=None, help="Checkpoint directory")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute FontDiffuser sampling. Default is dry-run manifest check.",
    )
    return parser.parse_args()


def _build_cmd(fontdiffuser_root: Path, ckpt_dir: Path, content: str, style: str, out: str, seed: str) -> list[str]:
    sample_py = fontdiffuser_root / "sample.py"
    return [
        "python",
        str(sample_py),
        f"--ckpt_dir={ckpt_dir.as_posix()}",
        "--save_image",
        "--device=cuda:0",
        "--algorithm_type=dpmsolver++",
        "--guidance_type=classifier-free",
        "--guidance_scale=7.5",
        "--num_inference_steps=20",
        "--method=multistep",
        f"--content_image_path={content}",
        f"--style_image_path={style}",
        f"--save_image_dir={(Path(out).parent).as_posix()}",
        f"--seed={seed}",
    ]


def _resolve_repo_path(path_value: str) -> Path | None:
    p = normalize_to_windows_path(path_value)
    if p is None:
        return None
    if p.is_absolute():
        return p
    return (ROOT.parent / p).resolve()


def main() -> None:
    args = parse_args()
    rows = load_csv(args.experiment_manifest)
    ckpt_dir = args.ckpt_dir or (args.fontdiffuser_root / "ckpt")
    GEN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cmd_log_path = GEN_OUTPUT_DIR / "run_commands.txt"
    cmd_lines = []
    run_count = 0
    skip_count = 0

    for row in rows:
        output_path_raw = (row.get("output_path") or "").strip()
        output_path = _resolve_repo_path(output_path_raw)
        if output_path is None:
            print(f"[warn] missing output_path for row: {row}")
            continue
        output_path.parent.mkdir(parents=True, exist_ok=True)
        content_path = _resolve_repo_path((row.get("content_path") or "").strip())
        style_path = _resolve_repo_path((row.get("ref_path") or "").strip())
        content = content_path.as_posix() if content_path else ""
        style = style_path.as_posix() if style_path else ""
        seed = str(row.get("generation_seed", "2026"))
        if not content_path or not content_path.exists():
            print(f"[warn] missing content image for {row.get('target_char')} {row.get('group')}: {content}")
            continue
        if not style_path or not style_path.exists():
            print(f"[warn] missing style image for {row.get('target_char')} {row.get('group')}: {style}")
            continue

        cmd = _build_cmd(args.fontdiffuser_root, ckpt_dir, content, style, output_path.as_posix(), seed)
        cmd_lines.append(" ".join(cmd))

        if output_path.exists():
            skip_count += 1
            continue
        if not args.execute:
            continue

        run_count += 1
        try:
            subprocess.run(cmd, check=True, cwd=args.fontdiffuser_root)
            produced = output_path.parent / "out_single.png"
            if produced.exists():
                shutil.copy2(produced, output_path)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] failed for {row.get('target_char')} {row.get('group')}: {exc}")

    cmd_log_path.write_text("\n".join(cmd_lines) + "\n", encoding="utf-8")
    if args.execute:
        print(f"finished execute mode. run={run_count}, skipped_existing={skip_count}")
    else:
        print("dry-run only (no inference executed).")
    print(f"command log: {cmd_log_path.as_posix()}")


if __name__ == "__main__":
    main()

