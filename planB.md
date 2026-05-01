# Plan B — Adapter Development

## 目标

在 FontDiffuser 之上增加一个 retrieval-conditioned adapter：FontDiffuser 主体全部冻结，只训 adapter。Adapter 的职责是吃 `retrieve.py` 输出的 5-slot refs（anchor + coverage），融合成 feature-space 残差，注入到 UNet 的 offset path，让模型"看着 ref 照抄组件怎么写"。

## Scope（第一阶段）

- 单字 / 王羲之单书法家 / 繁体
- 8 个 target case（都是 rare/complex 字）
- 只验证"结构正确性"，不追求美观

## 已锁定的架构决策

### Retrieval 侧（已完成）

- 5 个 slot：2 anchor（强化主部首）+ 3 coverage（攻难组件）
- Bank 归一化后的 difficulty metric：`1 / log(1 + bank_freq)`
- 零命中退化链：widen → 换 hard_comp → 全 anchor
- 输出带 role（anchor/coverage/empty）和 matched_comp 标签

### Adapter 侧

- 模块：`RetrievalAdapter`，位于 `adapter_dev/FontDiffuser/src/modules/retrieval_adapter.py`
- Signature：
  ```python
  adapter(h_q, refs, slot_ids, role_ids, target_struct, mask, return_gate=False) -> delta_h
  ```
- Slot 编码：离散 `(outer_ids × slot_index + SLOT_NONE) = 37` tokens，role 3 tokens，target_struct 12 tokens。全部 additive bias 到 ref token 上。
- Gate：`out_proj` zero-init + learnable scalar α（init=0）。无 scheduler，无 L2。
- Mask：softmax 前 additive `-1e4`（无后处理 renormalize）
- 前置不变量：每个 batch item 至少一个 valid slot（由 retrieve.py anchor fallback 保证）

### 注入点

- 主注入点：UNet 的 `up_blocks[2]`（`StyleRSIUpBlock2D`），offset path 的**最高分辨率** block
- `style_content_feat` shape：`[B, 64, 48, 48]`
- 注入位置：`StyleRSIUpBlock2D.forward` 的 for loop 之前、`style_content_feat` 取出之后，一次性加 `delta_h`
- 复用 `content_encoder`（冻结）做 refs 的特征提取——**不碰 `style_encoder`**
  - 理由：style_encoder 是生成驱动的 single-ref summarizer，没有 style disentanglement 约束；content_encoder 天然更擅长提取"字形结构"

### 冻结策略

- FontDiffuser 所有原有参数 `requires_grad=False`
- 只有 adapter 的参数 trainable

## 执行阶段与状态

| 阶段 | 内容 | 状态 |
|---|---|---|
| A0 | RetrievalAdapter 模块实现 + smoke test | ✅ 完成（7/7 check 全绿） |
| A1 | UNet recon，定位注入点 | ✅ 完成（锁定 `up_blocks[2]`，48×48×64） |
| A2 | 最小改动集成（unet.py + unet_blocks.py） | ✅ 完成 |
| A3 | Bit-exact invariance 验证 | ⏳ 进行中（`conda run` 吞输出问题需换命令重跑） |
| A4 | 补 marker 注释 + 同步 changelog（hygiene 清理） | ⏸ A3 全绿后启动 |
| B  | Mid block 第二注入点（hidden-state residual） | ⏸ A 阶段全部完成后 |
| C  | 训练 pipeline：dataloader + ref pack + loss | ⏸ |
| D  | 评估：component-level metric + OCR confidence | ⏸ |
| E  | Rarity-tiered injection depth（按模型训练集频率） | ⏸ 实验后决策 |

## 目录约定

```
adapter_dev/
  FontDiffuser/              # 被修改的工作副本（marker 注释 + changelog 必须对齐）
  changelog.md               # 所有 FontDiffuser 源码改动的索引
baseline_clean/
  FontDiffuser/              # 原版 pristine 副本，不改，作为 diff 基准
retrieval_data_prepare/
  pipeline/                  # 1ocr → 7generate_gt_wxz
  bank/                      # bank json + OCR 结果
  cases/                     # 8 个 target case
  manifests/                 # case 产出 manifests
  outputs/                   # 暂存输出
quick_eva/                   # 快速评估脚本
PHASE2_RECON.md              # FontDiffuser 架构 recon 报告（架构决策的证据基础）
planA.md                     # Retrieval 设计 plan
planB.md                     # 本文件：Adapter 开发 plan
```

## Hygiene 规则（必须遵守）

1. **Marker 注释**：`adapter_dev/FontDiffuser/` 源码中每一处改动必须被
   ```python
   # --- CALLI-RAG BEGIN: <简短说明> ---
   ...
   # --- CALLI-RAG END ---
   ```
   包裹。新加的成员赋值、新加的 forward 参数、插入的代码块都算。
2. **Changelog 同步**：每次改动 FontDiffuser 源码必须在 `adapter_dev/changelog.md` 记一条，包含：文件路径、行号（大约）、改动性质、对应功能模块。
3. **Diff 校验手段**：用 WinMerge 或 `fc /l` 对比 `adapter_dev/FontDiffuser/<file>` 与 `baseline_clean/FontDiffuser/<file>`，所有 diff 行应在 changelog 和 marker 里能找到。找不到的 = 遗漏，补记或 revert。
4. **新增文件不用 marker**：`retrieval_adapter.py`、`test_adapter_integration.py` 等完全新增的文件不加 marker，但 changelog 标"新建"。
5. **Agent 执行纪律**：给执行 agent 的 prompt 必须明确这几条红线：不自行决定歧义、不 pip install、不改非指定文件、发现 bug 列出不修。

## 当前改动清单（A 阶段完成后需对齐到 changelog）

### 新增文件

- `adapter_dev/FontDiffuser/src/modules/retrieval_adapter.py`
- `adapter_dev/FontDiffuser/tests/test_adapter_integration.py`

### 修改文件

- `adapter_dev/FontDiffuser/src/modules/unet_blocks.py`
  - L1：新增 `from typing import Optional`
  - L518：`StyleRSIUpBlock2D.__init__` 结尾新增 `self.retrieval_adapter = None`
  - L545：`StyleRSIUpBlock2D.forward` 签名新增 `retrieval_inputs: Optional[dict] = None`
  - L552：`style_content_feat` 取出后、for loop 前插入 adapter 调用块

- `adapter_dev/FontDiffuser/src/modules/unet.py`
  - L202：`UNet.forward` 签名新增 `retrieval_inputs: Optional[dict] = None`
  - L279-L286：仅在 `i == 2 and hasattr(upsample_block, "retrieval_adapter")` 时传入

> 注：这些改动目前**可能还没全部加上 marker 注释**。A4 是紧接 A3 的清理任务。

## 未决的开放问题

1. **评估指标**：SSIM/MSE 不反映组件正确性。候选：
   - Component-level DINO similarity（切 patch 比对）
   - OCR confidence（能不能识别回正确字）
   - 人工打分（8 case 可行，scale 不行）

   当前倾向：OCR confidence 作主指标、DINO 作辅、8 case 补人工。未定。

2. **Aux loss**：V1 只用原始 diffusion loss。如果训完发现 adapter 没用上 retrieval 信号（ref ablation 生成结果基本不变），V2 加 component-patch similarity aux loss。

3. **Bank 覆盖不足**：bank 只覆盖 ~50% wxz 字集。全零命中组件（如 `瘻` 的 `婁`）目前只能 anchor fallback。没验证这种 case 能不能救。

4. **Rarity metric 二分**（**两个维度不要混**）：
   - `bank_freq` → retrieval 难度（给 coverage slot 排序）
   - 通用汉字频率 → 模型"看过没有"（给 rarity-tiered injection 用）

5. **Step B 的 mid block 注入语义**：mid block 没有 offset path，只能加 hidden-state residual。和"照抄组件"语义弱耦合，更像粗粒度结构 bias。可能需要不同的 adapter 配置（更小、更窄）。A 全绿后再设计。

## 下一步（最近的 queue）

1. **A3 bit-exact 验证**：换 `D:\htt\miniconda3\envs\FontDiffuser\python.exe` 直接跑，绕开 `conda run` 吞 stdout 的问题
2. **A4 hygiene 清理**：A3 通过后，给 unet.py / unet_blocks.py 的 4 处改动补 marker 注释，同步 `adapter_dev/changelog.md`
3. **Step B 设计评审**：mid block 注入是否值得做、adapter 配置是否需要调整
4. **Step C 准备**：训练数据 pack 结构、dataloader 接口、loss 选型

---

**更新规范**：每完成一个阶段，把表格状态更新 + 在对应章节补上产出位置。未决问题有结论时移出并入"已锁定的架构决策"。
