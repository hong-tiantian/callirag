from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


STEP_SCRIPTS = [
    "build_case_manifest.py",
    "build_non_trivial_components.py",
    "build_bank_enriched.py",
    "bank_coverage_check.py",
    "retrieve_structural.py",
    "export_layer1_visuals.py",
    "analyze_layer1.py",
    "build_experiment_manifest.py",
    "run_fontdiffuser_batch.py",
    "build_blind_pairs.py",
    "analyze_layer2.py",
]


def _load(script_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"quick_eva_{script_path.stem}", str(script_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script: {script_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    for idx, script_name in enumerate(STEP_SCRIPTS, start=1):
        script = base_dir / script_name
        print(f"[quick_eva] step {idx}: {script_name}")
        mod = _load(script)
        if not hasattr(mod, "main"):
            raise RuntimeError(f"Script missing main(): {script_name}")
        mod.main()
    print("[quick_eva] all steps completed.")


if __name__ == "__main__":
    main()

