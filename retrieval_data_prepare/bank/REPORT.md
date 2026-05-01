# Retrieval Components Report

## 1) 规则
- 起点: `top_level_components`（不是 IDS 根）
- 停止: 康熙部首 / 独体字白名单 / raw leaf freq>=5 / 节点在 raw_leaves / 无法再拆
- 后处理: 过滤笔画原语 → NORM → TRAD_SIMP（统一繁体）
- 硬约束: `len(retrieval_components) <= len(leaf_components)`

## 2) Bug 修复验证

### Bug 1: 硬约束检查
- 违反 `len(retrieval) <= len(raw)` 的条目数（raw_len>0）: **0**
- raw_leaves 为空的条目（raw parser 全部过滤，retrieval 退回 retrieval_top_level）: **7**
  - wxz_5467 小: retrieval=['小']
  - wxz_5482 垂: retrieval=['垂']
  - wxz_0246 之: retrieval=['之']
  - wxz_0588 亞: retrieval=['亞']
  - wxz_2167 不: retrieval=['不']
  - wxz_2646 之: retrieval=['之']
  - wxz_2741 乙: retrieval=['乙']

### Bug 2: NORM 残留检查
- retrieval_components 中 NORM 源形式总出现次数: **0**

### Bug 3: 笔画原语残留检查
- retrieval_components 中笔画原语总出现次数: **0**

### Bug 4: 繁简统一（TRAD_SIMP）
- retrieval_components 中仍含简体源形式的次数: **0**

### NORM 扩展残留检查（应全部为 0）
  - 丷: 0
  - ⺊: 0
  - 𠂉: 0
  - 𠂊: 0
  - ⺌: 0
  - 丆: 0
  - 𠂆: 0
  - コ: 0

### 安全闸触发（len 超限后 fallback 到 top_level）: 123 次
- 抽样 10 条（before_fallback -> after_fallback）:
  - wxz_5444 並: ['䒑', '业'] -> ['並']
  - wxz_5573 胚: ['月', '丕'] -> ['胚']
  - wxz_5673 夜: ['亠', '亻', '夂'] -> ['亠', '⿰亻⿴夂丶']
  - wxz_5741 天: ['一', '大'] -> ['天']
  - wxz_5753 胤: ['幺', '月'] -> ['⿱幺月']
  - wxz_5768 衰: ['亠', '口', '一', '𧘇'] -> ['衰']
  - wxz_5843 無: ['人', '卌', '一', '火'] -> ['⿳𠂉卌一', '火']
  - wxz_5871 敢: ['乛', '耳', '攵'] -> ['⿱乛耳', '攵']
  - wxz_5893 壶: ['士', '冖', '业'] -> ['壶']
  - wxz_6058 乞: ['人', '乙'] -> ['乞']

### Parser 排查说明（婁 / 軍）
- `ids.txt` 中这两个字无条目；`ids_full.txt` 中：`婁=⿱⑧女`，`軍=⿱冖車`。
- `軍` 可正常解析；`婁` 含未知编号 `⑧`，属于已知未知部件（partial extraction）。
- 本轮 target case 出现空 raw_leaves 的主要原因不是 parser 报错，而是这两个字不在当前 decomp 子集（OCR 字集驱动）中。
- 已按规则修正 raw_leaves 为空时的 fallback：改为 `retrieval_top_level`，不再退回整字。

## 3) 8 个 target case
- 璨: raw_leaves=['王', '歺', '又', '米'] | retrieval_top_level=['王', '粲'] | retrieval_components=['王', '粲']
- 霆: raw_leaves=['雨', '廴', '壬'] | retrieval_top_level=['雨', '廷'] | retrieval_components=['雨', '廷']
- 鳞: raw_leaves=['鱼', '米', '夕', '㐄'] | retrieval_top_level=['魚', '粦'] | retrieval_components=['魚', '粦']
- 彎: raw_leaves=['糹', '言', '糹', '弓'] | retrieval_top_level=['䜌', '弓'] | retrieval_components=['䜌', '弓']
- 瘻: raw_leaves=['疒', '婁'] | retrieval_top_level=['疒', '婁'] | retrieval_components=['疒', '婁']
- 秦: raw_leaves=['三', '人', '禾'] | retrieval_top_level=['𡗗', '禾'] | retrieval_components=['𡗗', '禾']
- 赢: raw_leaves=['亡', '口', '月', '贝', '凡'] | retrieval_top_level=['吂', '⿲月贝凡'] | retrieval_components=['吂', '月', '貝', '凡']
- 諢: raw_leaves=['言', '冖', '車'] | retrieval_top_level=['言', '軍'] | retrieval_components=['言', '軍']

## 4) 抽样 20 条 old vs new retrieval
- wxz_5395 霧: raw=['冂', '丷', '八', '龴', '𠄐', '夂', '力'] | old=['雨', '務'] → new=['雨', '務']
- wxz_5398 徨: raw=['彳', '白', '十'] | old=['彳', '皇'] → new=['彳', '皇']
- wxz_5399 别: raw=['口', '力', '刂'] | old=['另', '刂'] → new=['另', '刂']
- wxz_5405 賴: raw=['束', '𠂊', '目', '八'] | old=['束', '負'] → new=['束', '負']
- wxz_5406 完: raw=['宀', '儿'] | old=['宀', '元'] → new=['宀', '元']
- wxz_5409 褪: raw=['衤', '辶', '艮'] | old=['衣', '退'] → new=['衣', '退']
- wxz_5413 吴: raw=['口', '人'] | old=['口', '天'] → new=['口', '天']
- wxz_5415 退: raw=['辶', '艮'] | old=['辵', '艮'] → new=['辵', '艮']
- wxz_5417 救: raw=['丷', '八', '攵'] | old=['求', '攵'] → new=['求', '攵']
- wxz_5419 惠: raw=['心'] | old=['心'] → new=['心']
- wxz_5421 佣: raw=['亻', '冂', '二'] | old=['亻', '用'] → new=['亻', '用']
- wxz_5423 誰: raw=['言', '隹'] | old=['言', '隹'] → new=['言', '隹']
- wxz_5424 往: raw=['彳', '十'] | old=['彳', '主'] → new=['彳', '主']
- wxz_5426 鎬: raw=['人', '十', '丷', '口', '冂', '口'] | old=['金', '高'] → new=['金', '高']
- wxz_5428 甫: raw=['十', '月'] | old=['十', '月'] → new=['十', '月']
- wxz_5430 毁: raw=['臼', '工', '𠘧', '又'] | old=['𬛸', '殳'] → new=['𬛸', '殳']
- wxz_5434 翼: raw=['冫', '冫', '田', '十', '八'] | old=['羽', '異'] → new=['羽', '異']
- wxz_5436 臭: raw=['自', '犬'] | old=['自', '犬'] → new=['自', '犬']
- wxz_5439 平: raw=['干', '丷'] | old=['干', '八'] → new=['干', '八']
- wxz_5443 樺: raw=['木', '十'] | old=['木', '華'] → new=['木', '華']

## 5) 统计
- bank 条目数: 3500
- retrieval_components 平均长度: 1.9749
- 去重 unique retrieval_components 数: 1319
- retrieval_components 频次 top-50（归一化后）:
  - 水: 219
  - 口: 216
  - 木: 162
  - 手: 155
  - 亻: 142
  - 艸: 125
  - 心: 116
  - 月: 87
  - 言: 82
  - 火: 78
  - 土: 71
  - 虫: 70
  - 辵: 69
  - 王: 66
  - 日: 60
  - 女: 60
  - 糸: 53
  - 疒: 50
  - 石: 48
  - 竹: 47
  - 宀: 46
  - 阜: 44
  - 禾: 43
  - 𧾷: 41
  - 衣: 39
  - 目: 39
  - 山: 38
  - 犬: 35
  - 金: 34
  - 米: 34
  - 貝: 32
  - 人: 32
  - 攵: 31
  - 酉: 29
  - 邑: 29
  - 刂: 28
  - 八: 28
  - 力: 28
  - 示: 28
  - 彳: 27
  - 隹: 27
  - 巾: 27
  - 白: 26
  - 广: 26
  - 魚: 25
  - 馬: 23
  - 冫: 22
  - 雨: 21
  - 十: 21
  - 頁: 21

## 6) 人工复核清单
### 阝 无法判断左右位置: 0 条

### 频次边缘（3-5）组件 top-20:
  - 〢: 5
  - 丘: 5
  - 入: 5
  - 冘: 5
  - 及: 5
  - 彑: 5
  - 旡: 5
  - 末: 5
  - 朱: 5
  - 玄: 5
  - 隶: 5
  - 𠂎: 5
  - 久: 4
  - 兆: 4
  - 才: 4
  - 朿: 4
  - 爿: 4
  - 片: 4
  - 瓦: 4
  - 禹: 4

### 白名单未覆盖但高频（freq>=20）:
  - 丷: 378
  - 𠂊: 239
  - 氵: 229
  - 亻: 186
  - 扌: 151
  - 阝: 93
  - 𠂉: 89
  - 辶: 86
  - 攵: 72
  - 忄: 72
  - 灬: 67
  - 丆: 57
  - 刂: 55
  - コ: 54
  - ⺊: 51
  - ⺌: 50
  - 𠂆: 44
  - 龴: 43
  - 𫠠: 42
  - 纟: 42

### Normalization edge cases:
  - 月: 87
  - 阜: 44
  - 邑: 29
  - 艸: 125
  - 辵: 69
  - 糸: 53
  - 車: 18
  - 貝: 32
