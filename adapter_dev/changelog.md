# FontDiffuser 变更记录（当前真实状态）

本文档按当前项目进度，记录我已完成并验证过的工作。  
范围基于你这轮指令与实际执行结果，不提前记录未落地事项。

## diff 审计指南

所有 adapter 接入改动均使用 `# [ADAPTER]` / `# [ADAPTER-BEGIN]` / `# [ADAPTER-END]` 标注。  
执行 `grep -n "\[ADAPTER" -r src/` 应返回 9 行匹配；审计时按下表逐行对照，不删任何既有 marker。

| checklist | file:line | 语义 |
| --- | --- | --- |
| [ ] | `src/modules/unet.py:202` | `UNet.forward` 新增 `retrieval_inputs` 形参并标注仅路由 `up_blocks[2]` |
| [ ] | `src/modules/unet.py:279` | `up_blocks` 路由分支 BEGIN，标注仅对 `up_blocks[2]` 透传 `retrieval_inputs` |
| [ ] | `src/modules/unet.py:297` | `up_blocks` 路由分支 END，与上方 BEGIN 成对闭合 |
| [ ] | `src/modules/unet_blocks.py:1` | `Optional` 引入处 marker，标注 `retrieval_inputs` 类型提示来源 |
| [ ] | `src/modules/unet_blocks.py:518` | `self.retrieval_adapter = None` 挂载点 marker，默认关闭 |
| [ ] | `src/modules/unet_blocks.py:545` | `StyleRSIUpBlock2D.forward` 新增 `retrieval_inputs` 可选参数 marker |
| [ ] | `src/modules/unet_blocks.py:550` | delta 注入块 BEGIN，标注 one-shot inject 在 offset loop 前 |
| [ ] | `src/modules/unet_blocks.py:554` | delta 注入块 END，与上方 BEGIN 成对闭合 |
| [ ] | `src/modules/retrieval_adapter.py:49` | `retrieval_adapter` 模块内既有 marker（保留，不参与逻辑改动） |

## 已完成内容

### 1) 新增 RetrievalAdapter 模块

已新增文件：`d:/htt/FontDiffuser/src/modules/retrieval_adapter.py`

实现内容（按你给的 signature）：
- `RetrievalAdapter` 类（slot/role/struct embedding、cross-attention、mask、output projection、alpha 门控）
- `out_proj`：**选项 A** — `weight` 用 `N(0, 0.02²)`、`bias` 仍 `zeros_`；`α` 仍 `0.0`。在保持零输出/bit-exact 的同时避免 `out_proj` 与 `α` 双零造成的 adapter 侧梯度全断（double-zero gradient trap）。
- `alpha` 为可学习标量，初始化 `0.0`
- `return_gate=True` 时返回 `{"alpha": scalar, "pregate_norm": scalar}`
- 文件底部包含 `if __name__ == "__main__":` 的 smoke test

### 2) 修复 mask 双重应用（仅保留 softmax 前 additive mask）

在 `retrieval_adapter.py` 中已完成：
- 保留：`logits.masked_fill(~token_mask, -1e4)`（softmax 前）
- 删除：softmax 后 `attn * token_mask` 与手动 `denom` 归一化
- 现行为：
  - `attn = torch.softmax(logits, dim=-1)`
  - `attn = self.attn_dropout(attn)`

### 3) 新增前置不变量断言

在 `forward` 里 mask 使用前新增：
- `assert mask.any(dim=1).all()`
- 报错信息：
  - `"RetrievalAdapter requires at least one valid slot per batch item; retrieve.py anchor fallback should guarantee this invariant."`

### 4) 追加 smoke test 两个 case

在 `retrieval_adapter.py` 的 `__main__` 底部追加：
- `all_masked_assert_check`：全 False mask 应触发 `AssertionError`
- `partial_mask_zero_output_check`：部分 mask 下仍保持零输出（`alpha=0`）

---

## 实际运行结果（FontDiffuser 环境）

使用环境：`D:\htt\miniconda3\envs\FontDiffuser\python.exe`  
执行命令：

`conda run -n FontDiffuser python d:/htt/FontDiffuser/src/modules/retrieval_adapter.py`

输出结果（关键检查项）：
- `num_params: 5321985`
- `shape_check: True`
- `zero_output_check: True`
- `backward_check: True`
- `return_gate_check: True`
- `delta_h_gate_shape_check: True`
- `all_masked_assert_check: True`
- `partial_mask_zero_output_check: True`

---

## Recon（A1）已完成，A2/A3 已落地并验证

我已完成对以下文件的 recon 阅读与书面结论：
- `src/modules/unet.py`
- `src/modules/unet_blocks.py`
- `src/model.py`
- `src/build.py`
- `configs/fontdiffuser.py`

并额外做过一次“默认 config + 不加载 ckpt + 随机输入”的 UNet 前向可运行性验证（可跑通）。

后续已完成 A2/A3：
- 已把 adapter 接入 `StyleRSIUpBlock2D`（for-loop 前单次注入）与 `UNet.forward`（仅路由到 `up_blocks[2]`）。
- 已新增 `tests/test_adapter_integration.py` 并完成 bit-exact、梯度与冻结检查。
- 当前 A3 在 CPU 上可稳定跑通（exit code 0）。

关键结果（最近一次 A3）：
- `device: cpu`
- `bit_exact_check: True`（等价于 `bit_exact_noise=True` 且 `bit_exact_offset=True`）
- `adapter_grad_nonzero_check: True`
- `trainable_params: 28545`
- `adapter_params: 28545`
- `freeze_check: True`

---

## 未改动范围（保持不动）

按你的约束，以下在当前阶段未改：
- `d:/htt/adapter_dev/FontDiffuser/src/model.py`
- `d:/htt/adapter_dev/FontDiffuser/src/build.py`
- `d:/htt/adapter_dev/FontDiffuser/sample.py`
- `d:/htt/batch_inference.py`
- pipeline 相关文件

另外没有安装任何新依赖（未 `pip install`）。

---

## 时间线（按任务轮次）

- `T0` 初始化阶段：在 `d:/htt/FontDiffuser/src/modules/retrieval_adapter.py` 新建 `RetrievalAdapter`，并加入基础 smoke test（shape/zero/backward/return_gate）。
- `T1` 环境核验阶段：定位可用环境为 `FontDiffuser` conda 环境，确认可 `import torch` 并拿到版本。
- `T2` 自查阶段：完成 4 点代码审查（mask 路径、零输出性质、embedding 广播维度、target_struct 广播安全性），输出证据与结论。
- `T3` 修正阶段：按指令删除 softmax 后二次 mask+renorm，仅保留 softmax 前 additive mask；新增“每个 batch item 至少一个有效 slot”的 assert。
- `T4` 补测阶段：在 `__main__` 追加 2 条 case（全 False mask 触发断言、部分 mask 下零输出仍成立），并在 `FontDiffuser` 环境实跑通过。
- `T5` Recon 阶段（Step A1）：完成 `unet.py / unet_blocks.py / model.py / build.py / configs/fontdiffuser.py` 阅读，给出 up block 顺序、offset path 注入位置、shape 推导和“不加载 ckpt 可随机前向”验证结论。
- `T6` 集成阶段：完成 A2 接入（`StyleRSIUpBlock2D` 注入 + `UNet.forward` 路由 `up_blocks[2]`）与 A3 测试文件创建。
- `T7` 排障阶段：定位并复现过 Windows 下的 segfault / WinError 1455（环境状态波动相关），后续在页面文件调整后恢复可运行。
- `T8` 选项 A 阶段：将 `out_proj.weight` 改为 `N(0, 0.02²)`、`alpha=0` 保持不变；A3 增加 bit-exact 与 grad 的硬断言，CPU 下运行通过。

## Marker 审计条目（adapter_dev vs baseline_clean）

- `FontDiffuser/src/modules/unet_blocks.py:L1 | ~ | 为 Optional[dict] 类型提示添加 ADAPTER 标识，便于定位 retrieval_inputs 引入点 | retrieval_adapter is None 时 bit-exact == baseline`
- `FontDiffuser/src/modules/unet_blocks.py:L518 | ~ | 为 retrieval_adapter 挂载点添加 ADAPTER 标识，明确默认关闭语义 | retrieval_adapter is None 时 bit-exact == baseline`
- `FontDiffuser/src/modules/unet_blocks.py:L545 | ~ | 为 forward 新增 retrieval_inputs 形参加 ADAPTER 标识，强调可选条件输入 | retrieval_inputs is None 时 bit-exact == baseline`
- `FontDiffuser/src/modules/unet_blocks.py:L550-L554 | ~ | 用 ADAPTER-BEGIN/END 包裹单次 delta 注入块，限定注入发生在 offset-path loop 前 | retrieval_adapter is None 或 retrieval_inputs is None 时 bit-exact == baseline`
- `FontDiffuser/src/modules/unet.py:L202 | ~ | 为 UNet.forward 的 retrieval_inputs 路由形参加 ADAPTER 标识，说明仅传递给 up_blocks[2] | retrieval_inputs is None 时 bit-exact == baseline`
- `FontDiffuser/src/modules/unet.py:L279-L297 | ~ | 用 ADAPTER-BEGIN/END 包裹 up_blocks 路由分支，仅在 i==2 且存在 retrieval_adapter 时传 retrieval_inputs | 所有 adapter 参数在 freeze_check 下属于 adapter_params 子集`

---

## A4 收尾更新（本轮对话新增）

- 审计口径修正：`diff 审计指南` 从“6 处匹配点”更新为“`grep -n "\[ADAPTER" -r src/` 返回 9 行匹配”，并新增 9 行逐项 checklist（含 `src/modules/retrieval_adapter.py:49` 既有 marker，保留不删）。
- 标注策略确认：按约束不删除任何 marker；当前 9 行 grep 输出作为正确审计基线。
- A3 复跑命令（非 `conda run`）：`"D:/htt/miniconda3/envs/FontDiffuser/python.exe" d:/htt/adapter_dev/FontDiffuser/tests/test_adapter_integration.py`
- A3 复跑结果：`bit_exact_check: True`、`adapter_grad_nonzero_check: True`、`freeze_check: True`、`exit code: 0`，确认 marker 注释未破坏现有逻辑与测试。

## 时间线追加

- `T9` A4 修正与收官：根据“9 行匹配”为准更新 `diff 审计指南` 与 checklist；在 `FontDiffuser` 环境按指定 python 路径复跑 A3，结果全绿（bit-exact / grad / freeze 均通过，退出码 0）。
