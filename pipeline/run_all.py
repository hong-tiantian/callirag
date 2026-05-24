from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


PLAN_A_SCRIPTS = [
    "plan_01_build_case_manifest.py",
    "plan_02_build_non_trivial_components.py",
    "plan_03_build_bank_enriched.py",
    "plan_04_bank_coverage_check.py",
    "plan_05_retrieve_structural.py",
    "plan_06_export_layer1_visuals.py",
    "plan_07_analyze_layer1.py",
    "plan_08_build_experiment_manifest.py",
    "plan_09_run_fontdiffuser_batch.py",
    "plan_10_build_blind_pairs.py",
    "plan_11_analyze_layer2.py",
]


def _load(script_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"pipeline_{script_path.stem}", str(script_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script: {script_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    for idx, script_name in enumerate(PLAN_A_SCRIPTS, start=1):
        script = base_dir / script_name
        print(f"[plan_a step {idx:02d}] {script_name}")
        mod = _load(script)
        if not hasattr(mod, "main"):
            raise RuntimeError(f"Script missing main(): {script_name}")
        mod.main()
    print("[plan_a] all 11 steps completed.")


if __name__ == "__main__":
    main()
