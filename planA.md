VQ-Font-style 分层 bank + 双层验证
核心改动：把轻版实验从"只换 style ref"升级为"先验证 retrieval 质量，再验证 injection 必要性"——两层独立评估，不依赖同一个指标。

Layer 1：Retrieval-level 验证（不过模型）
VQ-Font 的分层思路直接用：

bank_layer：图像 + wxz_path（你已有）
meta_layer：ids / layout / leaf_components / stroke_count（你已有）
sim_layer：离线算好的 {target_char → [(bank_id, score, reason)]} 字典
然后不跑 FontDiffuser，直接评估 retrieval 本身：

对 8-12 个 rare/complex target，structural retrieval vs random retrieval 的 top-5 给人看
人工标：retrieved chars 是否包含 target 的关键 component？是否 layout 一致？
产出：一张表，structural retrieval 的 component-hit rate vs random 的 hit rate
这一层能独立成立，和模型好不好无关。VQ-Font 的 character similarity dict 就是这种东西。这也是最容易写进 report 的部分。

Layer 2：Generation-level 验证（过 FontDiffuser）
只跑上次设计的 A/B/C 三组 12 case。但结果预期要重新定义：

如果 C > B > A：retrieval 有效 + 结构化有效（好结果，直接写）
如果 C ≈ B > A：retrieval 通道打开了，但 style channel 信息瓶颈限制了结构信号传递（这就是 adapter 线的 motivation）
如果 C ≈ B ≈ A：style ref swap 通道根本不 carry 结构信息（同上，更强证据）
后两种都是可写的 negative result，配合 Layer 1 的正向 retrieval 质量证据，report 的论证链是：

"结构化 retrieval 本身能稳定召回 component-relevant exemplars（Layer 1 证明），但通过 global style channel 注入无法把这种结构信号传到输出（Layer 2 证明）→ 需要在 offset-path 做 localized fusion（LF-Font/DM-Font 支持的范式）→ future work: adapter。"

这是一个完整的论文级别论证，而不是"我做了个实验结果不好"。

工程量
Layer 1：1 个脚本（读 retrieve.py 输出 + 人工标 CSV），0 模型改动
Layer 2：上次说的 manifest + batch_inference + 人工打分，0 模型改动
总计：两个新脚本，bank/cases/manifests 原样用
红线（给你和未来 agent）
不训练，不改 FontDiffuser UNet，不动 adapter 代码
bank schema 不重构，只在上面加 sim_layer 这一个离线字典文件
retrieve.py 不改，如果要新 ranking 逻辑单开 retrieve_v2.py
Layer 1 和 Layer 2 分别产 CSV，不合并（避免互相污染结论）
课程 DDL 前只做 12 case，不扩