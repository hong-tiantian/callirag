# FontDiffuser 变更记录（当前真实状态）

本文档按当前项目进度，记录我已完成并验证过的工作。  
范围基于你这轮指令与实际执行结果，不提前记录未落地事项。

## 已完成内容

### 1) 新增 RetrievalAdapter 模块

已新增文件：`d:/htt/FontDiffuser/src/modules/retrieval_adapter.py`

实现内容（按你给的 signature）：
- `RetrievalAdapter` 类（slot/role/struct embedding、cross-attention、mask、output projection、alpha 门控）
- `out_proj` 零初始化（`weight`/`bias` 均 `zeros_`）
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

## Recon（A1）已完成，A2/A3 尚未执行

我已完成对以下文件的 recon 阅读与书面结论：
- `src/modules/unet.py`
- `src/modules/unet_blocks.py`
- `src/model.py`
- `src/build.py`
- `configs/fontdiffuser.py`

并额外做过一次“默认 config + 不加载 ckpt + 随机输入”的 UNet 前向可运行性验证（可跑通）。

**注意：截至当前状态，尚未执行 A2/A3 代码接入。**  
即目前还没有做以下改动：
- 未把 adapter 接入 `StyleRSIUpBlock2D` / `UNet.forward`
- 未新增 `tests/test_adapter_integration.py`
- 未做 bit-exact integration test 的脚本化验证

---

## 未改动范围（保持不动）

按你的约束，以下在当前阶段未改：
- `d:/htt/FontDiffuser/src/model.py`
- `d:/htt/FontDiffuser/src/build.py`
- `d:/htt/FontDiffuser/sample.py`
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
- `T6` 当前状态：A1 已完成；A2/A3 尚未开始执行（未进行 UNet 接入、未新增 integration test 文件）。
