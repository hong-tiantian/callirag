# quick_eva

`quick_eva` 是按 `planA.md` 第 19 节实现的独立 11-step 实验脚本集合。

- 不依赖 `pipeline` 脚本执行逻辑；
- 读取 `callirag/bank/`、`callirag/cases/`；
- 输出落到 `callirag/outputs/layer1/`、`callirag/outputs/layer2/`；
- 当前默认兼容 `case_assets_15.csv` 的 15 个候选 target，正式实验范围由 `outputs/case_manifest.csv` 决定。

## Step 列表（Plan A）

1. `build_case_manifest.py`
2. `build_non_trivial_components.py`
3. `build_bank_enriched.py`
4. `bank_coverage_check.py`
5. `retrieve_structural.py`
6. `export_layer1_visuals.py`
7. `analyze_layer1.py`
8. `build_experiment_manifest.py`
9. `run_fontdiffuser_batch.py`
10. `build_blind_pairs.py`
11. `analyze_layer2.py`

## 用法

逐步执行（在仓库根目录）：

```bash
python callirag/quick_eva/build_case_manifest.py
python callirag/quick_eva/build_non_trivial_components.py
python callirag/quick_eva/build_bank_enriched.py
python callirag/quick_eva/bank_coverage_check.py
python callirag/quick_eva/retrieve_structural.py
python callirag/quick_eva/export_layer1_visuals.py
python callirag/quick_eva/analyze_layer1.py
python callirag/quick_eva/build_experiment_manifest.py
python callirag/quick_eva/run_fontdiffuser_batch.py
python callirag/quick_eva/build_blind_pairs.py
python callirag/quick_eva/analyze_layer2.py
```

一键顺序执行：

```bash
python callirag/quick_eva/run_all.py
```

说明：

- `analyze_layer1.py` / `analyze_layer2.py` 在缺少标注文件时会自动生成模板；
- `run_fontdiffuser_batch.py` 默认 dry-run，不实际推理；加 `--execute` 才会真正调用 FontDiffuser。

