# 当前实验线梳理（给新对话直接续接用）

## 1. 当前项目主线

| 项目 | 当前结论 |
|---|---|
| 研究主题 | Chinese calligraphy generation + retrieval-augmented structural support |
| 当前 baseline | **FontDiffuser**，不是 DeepCalliFont / CalliFormer |
| 当前目标 | 不是先做完整 RAG system，而是先做 **retrieval prototype / retrieval probing** |
| 当前最核心研究问题 | **什么样的 external reference 最可能修复 rare / complex characters 的 failure modes** |
| 当前最重要的 failure modes | 1) complex 字：**细微笔画缺失**；2) rare 字：**identity error** |
| 当前 scope | **single-character**, **same-style / same calligrapher**, 先看 **structural correctness** |
| 当前不做 | 不先做 full-page，不先做 style diversity，不先做自动大规模 learned retriever，不先做 component-level patch retrieval |

---

## 2. baseline 现在算做到哪一步

| 问题 | 结论 |
|---|---|
| baseline 是否已经“能用了” | **能**。已经足够作为 failure anchor，进入 retrieval prototype |
| baseline 是否已经“正式完整做完” | **还没有**。还没整理成论文里完整 baseline section |
| 已经拿到的 baseline 价值 | 已经观察到关键 failure：complex 字缺细笔画，rare 字会 identity error |
| 当前是否还需要继续深刷 baseline taxonomy | **不需要**。可以转去做 retrieval probe |
| baseline 在后续实验中的角色 | 作为 **failure confirmation / anchor**，不是研究重点本身 |

---

## 3. 现在真正要做的不是“完整 RAG”，而是什么

| 层级 | 当前该做的事 | 不该做的事 |
|---|---|---|
| 实验层 | 做 **rag_quick**：在 baseline failure cases 上测试 external structural support 是否有帮助 | 不要一上来做完整 retrieval-augmented generator |
| 方法层 | 先做 **whole-character retrieval prototype** | 不要直接跳到 component-level retrieval / full learned retrieval |
| 工程层 | 先做最小可执行的外置 retrieval support | 不要先重构整个模型 |

---

## 4. whole-character 到底是什么意思

| 概念 | 正确理解 |
|---|---|
| whole-character retrieval | **检索单位是整张字图**，返回结果也是整张字图 |
| 是否要拆部件 | **不要拆**。当前 whole-character retrieval 里不做部件裁剪、不做 patch retrieval |
| 数据库里存什么 | **整字图 + metadata** |
| metadata 可以有什么 | 字本身、路径、书法家/风格、布局类型、偏旁/部件标签（如果要用） |
| “同布局 / 同偏旁 / 同部件” 是什么 | 是 **retrieval criterion（检索依据）**，不是 retrieval unit |
| 是否与 whole-character 冲突 | **不冲突**。可以是“按同部件规则检索 whole-character 图” |

---

## 5. 关于 retrieval 策略，当前最清楚的判断

| 候选策略 | 当前判断 | 原因 |
|---|---|---|
| 同布局 | **可做，但偏粗** | 更适合粗结构稳定性，不一定能明显修复细微笔画缺失 |
| 同偏旁 | **可做，但先不要单独拉出来** | 和“同部件”在第一轮很容易重叠 |
| 同部件 | **更贴近当前 failure** | 对细微笔画缺失、identity error 更可能有帮助 |
| 视觉相似 | **第一轮不要做主实验** | 太主观，容易混入别的变量 |
| 随机 | **必须保留** | 作为对照组，判断 retrieval 是否只是“多给点图就更好” |

### 当前最合理的第一轮 retrieval strategy
- **retrieval unit**：whole character
- **retrieval criterion**：**same-component / same-radical whole-character retrieval**
- **对照组**：random whole-character retrieval

> 备注：如果后面需要更保守，可以先加一个 same-layout 组，但真正更贴近当前 failure 的，是 same-component / same-radical。

---

## 6. 为什么“直接换 style ref”不够准确

| 问题 | 当前理解 |
|---|---|
| FontDiffuser 原始 ref 是什么 | 原本是 **style reference** |
| 把结构相关 reference 直接塞进 style ref 通道算什么 | 只能算 **proxy experiment**，不算严格的外置 RAG |
| 它能回答什么 | 模型能不能通过 style-reference 通道顺便吸收到结构帮助 |
| 它不能严格回答什么 | 独立 retrieval support 本身是否在起作用 |
| 当前更想做什么 | 一个 **小的外置 retrieval support branch**，而不是简单挪用 style ref |

---

## 7. 外置 retrieval 注入方案，已经讨论到哪里

## 7.1 之前的“实验语义层级”区分

| 方案 | 含义 |
|---|---|
| 直接替换 style ref | 最快的 proxy，不算真正独立 retrieval |
| 保留 style ref，再额外加 retrieval support | 比上面更准确，更像小外置 RAG |
| 做真正 retrieval fusion | 最正式，但也最重 |

## 7.2 技术注入方式：A 和 B 的区别（已经确认）

| 方案 | 含义 | 优点 | 缺点 | 当前判断 |
|---|---|---|---|---|
| **A. Content-path augmentation** | retrieval 先并进 content path，再生成 | 最轻，最容易先做 | retrieval 和 content 混掉，解释不够干净 | 可做 prototype，但不够像正式 RAG |
| **B. Cross-attention 新分支** | retrieval 保持独立条件，单独编码后送给 UNet cross-attention | 语义最干净，最像真正 retrieval augmentation | 更重，需要加分支 / adapter | **当前更倾向选 B** |

### 当前已确认的选择
- 你更倾向 **B**
- 原因：B 里 retrieval 是 **独立条件**，更像真正的外置 RAG
- 因此后续不该再把“多张 ref 拼成 style 图”当主要方法路线

---

## 8. 如果做 B，当前最小实现应该是什么

| 模块 | 当前建议 |
|---|---|
| content path | 保留原样 |
| style path | 保留原样 |
| retrieval branch | **新增一条独立分支** |
| retrieval encoder | 可以先**复用 content encoder 参数并冻结** |
| 注入点 | 送进 UNet 的 **cross-attention**，作为独立 keys/values |
| 训练策略 | **冻结主模型，只训很小的 adapter / projection** |
| 当前不做 | 不全量 end-to-end 重训整个模型 |

---

## 9. 训练数据要不要额外准备

| 问题 | 当前结论 |
|---|---|
| 是否需要全新“检索训练数据集” | **不需要** |
| 需要做什么 | 在现有 FontDiffuser 训练样本上，给每条样本离线挂 retrieval 结果 |
| 训练 tuple 形式 | `(content image, original style ref, retrieved refs, target image)` |
| retrieval 结果怎么来 | 从同书法家 bank 里按规则离线生成（random / same-layout / same-component） |
| 第一轮数据规模 | 先做 **1k–3k 个 target 字 / 3k–10k 个 training tuples** 就够看趋势 |
| 当前目标 | 先验证 retrieval branch 会不会被模型用起来，不是追最终 SOTA |

---

## 10. 显卡是否够

| 配置 | 当前判断 |
|---|---|
| 3080 20G + 冻结主模型 + 小 adapter 微调 | **够** |
| 3080 20G + 全量 end-to-end 重训 | **会比较紧，且不建议现在做** |
| 当前建议路线 | 冻结主模型，只训 retrieval branch / adapter |

---

## 11. 目前到底参考到哪些论文了

| 层面 | 是否已经参考到 |
|---|---|
| literature review / 文章叙事 | **已经参考到** |
| 方法启发（bank、metadata、external support、fusion precedent） | **已经参考到** |
| 代码实现 / 实验落地 | **还没有真正落进去** |

### 目前几篇论文各自的作用（已经达成的理解）

| 论文 | 当前作用 |
|---|---|
| **VQ-Font** | 最适合参考 **bank / metadata / similarity index 的组织方式** |
| **LF-Font** | 最适合参考 **external support 的 fusion precedent / injection level** |
| **DM-Font** | 最适合参考 **write-read external support 的范式**，但不适合当前第一版 whole-character prototype 直接照抄 |

### 当前最实用的判断
- **现在最值得真正落地参考的是 VQ-Font 的 bank/meta/index 思路**
- LF-Font / DM-Font 目前更适合作为 **method design precedent**，不是第一版实验模板

---

## 12. rag_quick 现在真正该长什么样

| 目录 / 对象 | 作用 |
|---|---|
| `cases/` | 每个 failed 字一个子文件夹 |
| `reference_bank/` | same-style / same-calligrapher 的 whole-character bank |
| `configs/` | 每个 case 的 retrieval plan |
| `outputs/` | baseline 与 retrieval 结果 |
| `notes.csv` | 每条结果的记录表 |

### `notes.csv` 建议字段

| 字段 | 含义 |
|---|---|
| case_id | case 编号 |
| target_char | 目标字 |
| failure_type | complex 缺细笔画 / rare identity error / 其他 |
| has_gt | 是否有 ground truth |
| retrieval_type | random / same-layout / same-component |
| retrieval_chars | 实际选了哪些 reference 字 |
| improved_identity | 是否改善 identity |
| improved_stroke | 是否改善细笔画问题 |
| notes | 主观观察 |

---

## 13. 当前最该做的事情（按顺序）

| 顺序 | 任务 | 当前说明 |
|---|---|---|
| 1 | 固定 3–5 个 failed baseline cases | 每个 case 明确属于哪类 failure |
| 2 | 给每个 case 建 same-style whole-character bank | 先把 metadata 组织起来 |
| 3 | 先确定第一轮 retrieval criterion | 当前更倾向 **same-component / same-radical**，随机作对照 |
| 4 | 把 retrieval branch 的最小接口定下来 | 现在倾向 **B：独立 cross-attention branch** |
| 5 | 做最小训练版 | 冻结主模型，只训小 adapter |
| 6 | 先跑小规模结果 | 看 retrieval support 是否有明显趋势 |
| 7 | 再决定要不要扩到 same-layout 或更细粒度 | 第二阶段再说 |

---

## 14. 当前仍然存在的疑惑（必须继续讨论）

| 疑惑 | 当前状态 |
|---|---|
| 第一轮 retrieval criterion 最终到底选 **same-layout** 还是 **same-component** | 目前倾向 **same-component**，但还需要最后确认 |
| retrieval branch 在 UNet 的哪一层接入最合适 | **未定** |
| retrieval encoder 是否完全复用 content encoder，还是只复用部分 | **未定** |
| adapter 最小做到什么程度 | **未定** |
| 一个 target 对应几张 retrieval refs 最合适 | 目前偏向 **top-3** |
| 训练时 retrieval branch 的 supervision 需要额外损失吗 | **未定** |
| 第一轮实验是否只做 qualitative / case study，还是顺带做一点 quantitative | **未定** |
| ground truth 不存在的 case 怎么放进实验 | 只能做 qualitative probing，不能做 gt-based quantitative |
| 论文里如何表述“当前 prototype”与“planned full method”的区别 | 需要避免把 prototype 写成完整 RAG system |

---

## 15. 当前最关键的几句判断（给新对话直接承接）

| 主题 | 结论 |
|---|---|
| baseline 是否够了 | **够进入 retrieval prototype，但还不算完整论文 baseline section** |
| 当前最该做的是什么 | **不是继续刷 baseline，不是直接做 full RAG，而是做 small retrieval prototype** |
| whole-character 是否与同部件策略冲突 | **不冲突**。whole-character 是 retrieval unit；same-component 是 retrieval criterion |
| 当前更想要的注入方式 | **B：独立 retrieval branch + cross-attention** |
| 是否要准备全新 retrieval dataset | **不要**，在现有样本上离线挂 retrieval 结果即可 |
| 3080 20G 是否够 | **够做冻结主模型 + 小 adapter 微调的 prototype** |

---

## 16. 给下一轮对话的直接起点

下一轮最值得直接接着讨论的，不是泛泛“RAG 怎么做”，而是这四件具体事：

| 优先级 | 问题 |
|---|---|
| 1 | 第一轮 retrieval criterion 最终选 **same-component** 还是 **same-layout**？ |
| 2 | B 方案里 retrieval branch 最小怎么接到 UNet cross-attention？ |
| 3 | 训练时冻结哪些模块，只训哪些 adapter？ |
| 4 | rag_quick 的 bank / metadata 表具体怎么写？ |