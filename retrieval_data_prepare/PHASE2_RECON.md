# PHASE2 Recon: FontDiffuser 样式参考管线（只读分析）

> 说明：你给的工作目录是 `/d/htt/FontDiffuser/`，但实际被批量脚本调用的 `batch_inference.py` 位于 `d:/htt/batch_inference.py`（仓库根目录）。以下按真实执行路径追踪。

## A. Call graph（含 file:line）

```text
d:/htt/batch_inference.py
  main() [34]
    ├─ 组装单次推理参数：
    │    args.content_image_path = ... [110]
    │    args.style_image_path   = ... [111]
    │    sampling(args, pipe)    [119]
    │
    └─ 首次仅加载一次模型：
         load_fontdiffuer_pipeline(args) [92]
           └─ from sample import arg_parse, load_fontdiffuer_pipeline, sampling [88]

d:/htt/FontDiffuser/sample.py
  sampling() [126]
    ├─ image_process() [135]
    │    ├─ Image.open(args.style_image_path).convert("RGB") [65]
    │    ├─ style transforms: Resize + ToTensor + Normalize [84-88]
    │    └─ style tensor shape: [1, 3, H, W]（通过 [None, :] 加 batch 维）[90]
    └─ pipe.generate(style_images=style_image, content_images=content_image, batch_size=1) [148-151]

d:/htt/FontDiffuser/src/dpm_solver/pipeline_dpm_solver.py
  FontDiffuserDPMPipeline.generate() [42]
    ├─ cond = [content_images, style_images] [63-65]
    └─ model_wrapper(...) -> DPM_Solver.sample(...) [74-110]
       （采样过程中反复调用 model.forward）

d:/htt/FontDiffuser/src/model.py
  FontDiffuserModelDPM.forward() [77]
    ├─ style_encoder(style_images) -> style_img_feature [88]
    ├─ style_img_feature -> style_hidden_states(序列) [90-92]
    ├─ content_encoder(content_images) [94-95]
    ├─ content_encoder(style_images) 取“style 结构特征” [97-98]
    └─ unet(..., encoder_hidden_states=[style_img_feature, content_res_feats, style_hidden_states, style_content_res_feats]) [100-107]

d:/htt/FontDiffuser/src/modules/unet.py
  UNet.forward() [196]
    ├─ down_blocks（含 MCADownBlock2D）注入 style/content [242-249]
    ├─ mid_block（UNetMidMCABlock2D）注入 style/content [257-262]
    └─ up_blocks（含 StyleRSIUpBlock2D）注入 style + 结构偏移 [277-285]

关键注入子模块：
  d:/htt/FontDiffuser/src/modules/unet_blocks.py
    - MCADownBlock2D.forward() [307]
    - UNetMidMCABlock2D.forward() [194]
    - StyleRSIUpBlock2D.forward() [534]
```

## B. Style ref capacity（当前支持多少参考图）

- **当前单调用是 1 张 style 图**（硬编码路径参数）
  - `sample.py` CLI 只有 `--style_image_path`（单字符串）[37]
  - `image_process()` 只 `Image.open(args.style_image_path)` 一次 [65]
  - `sampling()` 调 `pipe.generate(..., batch_size=1)` [151]
- **`batch_inference.py` 层面**是“多 style 文件循环”，但每次循环仍是**单 style + 单 content**：
  - style 列表来自 `glob(STYLE_GLOB)` [38-40]
  - 每轮只给一个 `args.style_image_path` [111]
- **模型内部没有多 ref 聚合逻辑**：
  - `FontDiffuserModelDPM.forward()` 将 `style_images` 直接喂 `style_encoder` [88]
  - 没有 list/stack/top-k merge 的代码分支
  - 如果强行把 k 张 ref 作为 batch 维输入，等价于“生成 k 个样本并行”，不是“单样本融合 k refs”

结论：**N=1（每个样本单参考），不是 list-capable 聚合。**

## C. Injection point detail（注入位置/操作/形状）

### C1. 样式图读取与预处理（filesystem -> tensor）

- 读取函数：`sample.py::image_process()` [52]
- 读取方式：`PIL.Image.open(...).convert("RGB")` [65]
- 预处理：
  - `Resize(args.style_image_size, bilinear)` [84-86]
  - `ToTensor()`（HWC[0,255] -> CHW[0,1]）[87]
  - `Normalize([0.5], [0.5])`（将值域映射到约 [-1,1]）[88]
  - 加 batch 维：`style_image = ...[None, :]` [90]
- 通道顺序：模型张量是 `NCHW`
- 默认尺寸（配置默认）：`style_image_size=96`（来自 `configs/fontdiffuser.py` [24]）
  - 推理时 style 输入常见形状：`[1,3,96,96]`

### C2. Style encoder 输出类型

- 模块：`src/modules/style_encoder.py::StyleEncoder` [310]
- 前向返回：`return style_emd, h, residual_features` [442]
  - `style_emd`：**feature map**（用于后续 cross-attn context 源）
  - `h`：`adaptive_avg_pool2d -> flatten` 的**pooled 向量** [439-440]（在 DPM 推理路径里未用）
  - `residual_features`：多尺度残差特征列表
- DPM 路径实际使用：
  - `style_img_feature = style_emd` [model.py:88]
  - 再 reshape 成 token 序列：`[B,C,H,W] -> [B,H*W,C]` [90-92]

### C3. UNet 注入机制

1) **Down block 注入（MCADownBlock2D）**
- 位置：`unet_blocks.py::MCADownBlock2D.forward()` [307]
- 操作：
  - content 注入：`ChannelAttnBlock`，把当前 `hidden_states` 与 content encoder 对应尺度特征 `concat` [319-320, 398]
  - style 注入：`SpatialTransformer(..., context=current_style_feature)` [326-329]
- 类型：**通道注意力融合 + cross-attention**

2) **Mid block 注入（UNetMidMCABlock2D）**
- 位置：`unet_blocks.py::UNetMidMCABlock2D.forward()` [194]
- 操作与 down 类似：
  - content: `ChannelAttnBlock` [205-206]
  - style: `SpatialTransformer(..., context=current_style_feature)` [212-215]
- 类型：**通道注意力融合 + cross-attention**

3) **Up block 注入（StyleRSIUpBlock2D）**
- 位置：`unet_blocks.py::StyleRSIUpBlock2D.forward()` [534]
- 双路径：
  - 样式 token cross-attn：`attn(hidden_states, context=encoder_hidden_states)` [579]
    - `encoder_hidden_states` 在 `UNet.forward()` 里来自 `encoder_hidden_states[2]`（即 `style_hidden_states`）[283]
  - 结构偏移注入：`OffsetRefStrucInter` 预测 deformable conv offset，再 `DeformConv2d` 作用于 skip feature [554-562]
    - style 结构特征来自 `style_structure_features`（即 style 图经 content encoder 的多尺度特征）[282, 545]
- 类型：**cross-attention + DCN offset-based 结构注入**

### C4. 关键形状（按默认分辨率 96 推断）

- style 输入：`[1,3,96,96]`
- style encoder 主输出 `style_img_feature`：约 `[1,1024,3,3]`（由 5 次下采样和通道倍率推导）
- style token（给 cross-attn context）：`[1,9,1024]`
- UNet cross-attention `context_dim`：`args.style_start_channel * 16`，默认是 `1024`（`build.py` [30], `fontdiffuser.py` [31]）

> 备注：上面形状是按默认 parser 参数静态推断；真实 ckpt 训练时超参若不同，通道数会随配置变化。

## D. 最小改动注入策略（按改动量排序）

### 1) Top-1 直连（最小改动）
- **改什么**
  - 在 RAG 侧只取 top-1，继续喂现有 `--style_image_path`
  - `batch_inference.py` / `sample.py` / 模型都不改
- **不改什么**
  - 现有推理流程、ckpt 兼容、UNet 注入机制全部不变
- **风险**
  - 丢失 top-2/3 信息，多参考收益无法利用

### 2) 输入端做“像素级融合后单图喂入”（小改动）
- **改什么**
  - 在进入 FontDiffuser 前，把 top-k refs 做外部融合（如 resize 后均值/加权均值/拼贴再缩放）生成一张 proxy style 图
  - 仍走 `--style_image_path` 单图接口
- **不改什么**
  - FontDiffuser 内部代码可完全不动
- **风险**
  - 融合会抹平风格细节；拼贴方案可能引入空间伪影，影响 style encoder 表征

### 3) 编码后特征平均（中等改动，模型内最小侵入）
- **改什么**
  - 让 `sample.py` 支持多 style path（list）
  - 在 `model.py` 中对每个 ref 跑 `style_encoder`，对 `style_img_feature` / `style_hidden_states`（以及必要时 style-content 结构特征）做均值或加权均值，再送 UNet
- **不改什么**
  - UNet 主结构与 checkpoint 权重基本不变（只改前向聚合逻辑）
- **风险**
  - 简单平均会破坏组件级别互补关系；若连 style-content 结构分支一起平均，结构偏移质量可能下降

> 若目标是“最稳+最省事”：先做方案 1；若希望低成本试验多参考收益：先做方案 2；若希望模型内整合且保持接口清晰：做方案 3。

## E. Open questions（仅靠读代码无法确定）

- 当前线上/本地实际使用的 ckpt 训练超参是否与 `configs/fontdiffuser.py` 默认值一致（尤其 `content_start_channel`、`style_start_channel`）？
- `StyleRSIUpBlock2D` 中 `style_feat_in_channels` 与 style-content 多尺度特征通道是否在实际运行配置下严格匹配？
- 多参考场景下，结构分支（offset + deform conv）该使用：
  - 单一参考（比如 top-1）？
  - 还是融合后的结构特征？
  - 这会直接影响字形结构稳定性，需要实测。
- RAG top-k 的相似度分数是否可作为加权系数（而不是均值）带来更稳定收益？

## 已阅读文件清单（完整）

1. `d:/htt/batch_inference.py`
2. `d:/htt/FontDiffuser/sample.py`
3. `d:/htt/FontDiffuser/configs/fontdiffuser.py`
4. `d:/htt/FontDiffuser/src/__init__.py`
5. `d:/htt/FontDiffuser/src/build.py`
6. `d:/htt/FontDiffuser/src/model.py`
7. `d:/htt/FontDiffuser/src/dpm_solver/pipeline_dpm_solver.py`
8. `d:/htt/FontDiffuser/src/modules/__init__.py`
9. `d:/htt/FontDiffuser/src/modules/style_encoder.py`
10. `d:/htt/FontDiffuser/src/modules/content_encoder.py`
11. `d:/htt/FontDiffuser/src/modules/unet.py`
12. `d:/htt/FontDiffuser/src/modules/unet_blocks.py`
13. `d:/htt/FontDiffuser/src/modules/attention.py`
