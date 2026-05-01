# Retrieval Test Report — Slot-Based (Anchor + Coverage)

- Bank: `wxz_bank.json` (3500 entries)
- OCR confidence threshold: 0.9
- Anchor slots: 2  |  Coverage slots: 3
- Full score formula: `3*J(rc) + 2*J(rtl) + 1*layout + 0.5*stroke_sim`
- Coverage score formula: `3*(hard_comp match) + 1*layout + 0.5*stroke_sim`
- Difficulty: `1 / log(1 + bank_freq(comp))`
- Targets: `['璨', '霆', '鳞', '彎', '瘻', '秦', '赢', '諢']`

## 璨
- target retrieval_components: `['王', '粲']`
- target top_level_components (raw): `['王', '粲']`
- target retrieval_top_level: `['王', '粲']`
- target layout: `⿰`
- target stroke_count: `17`
- **anchor_comp**: `王`
- **hard_comps**: `['粲']`

**Component difficulty (bank_freq → difficulty):**
- `粲`: bank_freq=1, difficulty=1.4427

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3157
- after has_unknown sanity: 3133
- final with score > 0: 2808

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 3.17 | wxz_0866 | 環 | ['王', '睘'] | ['王', '睘'] | ⿰ | 17 | /d/htt/data/image/train/wxz/0866.jpg |
| 2 | 3.17 | wxz_4217 | 璐 | ['王', '路'] | ['王', '路'] | ⿰ | 17 | /d/htt/data/image/train/wxz/4217.jpg |
| 3 | 3.12 | wxz_2256 | 璞 | ['王', '菐'] | ['王', '菐'] | ⿰ | 16 | /d/htt/data/image/train/wxz/2256.jpg |
| 4 | 3.07 | wxz_5794 | 璜 | ['王', '黃'] | ['王', '黃'] | ⿰ | 15 | /d/htt/data/image/test/wxz/5794.jpg |
| 5 | 3.07 | wxz_1058 | 瑾 | ['王', '堇'] | ['王', '堇'] | ⿰ | 15 | /d/htt/data/image/train/wxz/1058.jpg |

**OLD component coverage:**
- `王`: ✓ (5 hits)
- `粲`: ✗ MISS (0 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 王 | 3.17 | 環 | ['王', '睘'] | ⿰ | 17 | /d/htt/data/image/train/wxz/0866.jpg |
| 2 | anchor | 王 | 3.17 | 璐 | ['王', '路'] | ⿰ | 17 | /d/htt/data/image/train/wxz/4217.jpg |
| 3 | anchor | 王 | 3.12 | 璞 | ['王', '菐'] | ⿰ | 16 | /d/htt/data/image/train/wxz/2256.jpg |
| 4 | anchor | 王 | 3.07 | 璜 | ['王', '黃'] | ⿰ | 15 | /d/htt/data/image/test/wxz/5794.jpg |
| 5 | anchor | 王 | 3.07 | 瑾 | ['王', '堇'] | ⿰ | 15 | /d/htt/data/image/train/wxz/1058.jpg |

**coverage_report:**
- covered: `['王']`
- uncovered: `['粲', '粲']`
- slot_reassignments: `[{'original_hard_comp': '粲', 'reason': 'zero_bank_hits', 'replaced_with': '王 (anchor)'}, {'original_hard_comp': '粲', 'reason': 'zero_bank_hits', 'replaced_with': '王 (anchor)'}, {'original_hard_comp': 'free_slot', 'reason': 'no_hard_comp_hit_in_bank', 'replaced_with': '王 (anchor)'}]`

**NEW component coverage (per retrieval_component):**
- `王`: ✓ (5 hits)
- `粲`: ✗ MISS (0 hits)

### 分数分布
- score > 0 的候选数: 2808
- score > 1.0: 1660
- score > 2.0: 50
- score > 3.0: 13

## 霆
- target retrieval_components: `['雨', '廷']`
- target top_level_components (raw): `['雨', '廷']`
- target retrieval_top_level: `['雨', '廷']`
- target layout: `⿱`
- target stroke_count: `14`
- **anchor_comp**: `雨`
- **hard_comps**: `['廷']`

**Component difficulty (bank_freq → difficulty):**
- `廷`: bank_freq=5, difficulty=0.5581

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3157
- after has_unknown sanity: 3133
- final with score > 0: 3051

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 3.17 | wxz_2022 | 需 | ['雨', '而'] | ['雨', '而'] | ⿱ | 14 | /d/htt/data/image/train/wxz/2022.jpg |
| 2 | 3.12 | wxz_5623 | 零 | ['雨', '令'] | ['雨', '令'] | ⿱ | 13 | /d/htt/data/image/test/wxz/5623.jpg |
| 3 | 3.12 | wxz_6027 | 霉 | ['雨', '每'] | ['雨', '每'] | ⿱ | 15 | /d/htt/data/image/test/wxz/6027.jpg |
| 4 | 3.12 | wxz_1034 | 雷 | ['雨', '田'] | ['雨', '田'] | ⿱ | 13 | /d/htt/data/image/train/wxz/1034.jpg |
| 5 | 3.12 | wxz_1153 | 電 | ['雨', '日'] | ['雨', '⿻日乚'] | ⿱ | 13 | /d/htt/data/image/train/wxz/1153.jpg |

**OLD component coverage:**
- `廷`: ✗ MISS (0 hits)
- `雨`: ✓ (5 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 雨 | 3.17 | 需 | ['雨', '而'] | ⿱ | 14 | /d/htt/data/image/train/wxz/2022.jpg |
| 2 | anchor | 雨 | 3.12 | 零 | ['雨', '令'] | ⿱ | 13 | /d/htt/data/image/test/wxz/5623.jpg |
| 3 | coverage | 廷 | 3.40 | 艇 | ['舟', '廷'] | ⿰ | 12 | /d/htt/data/image/train/wxz/1683.jpg |
| 4 | coverage | 廷 | 3.40 | 蜓 | ['虫', '廷'] | ⿰ | 12 | /d/htt/data/image/train/wxz/3582.jpg |
| 5 | coverage | 廷 | 3.25 | 挺 | ['手', '廷'] | ⿰ | 9 | /d/htt/data/image/test/wxz/5664.jpg |

**coverage_report:**
- covered: `['雨', '廷']`
- uncovered: `[]`

**NEW component coverage (per retrieval_component):**
- `廷`: ✓ (3 hits)
- `雨`: ✓ (2 hits)

### 分数分布
- score > 0 的候选数: 3051
- score > 1.0: 738
- score > 2.0: 21
- score > 3.0: 15

## 鳞
- target retrieval_components: `['魚', '粦']`
- target top_level_components (raw): `['鱼', '粦']`
- target retrieval_top_level: `['魚', '粦']`
- target layout: `⿰`
- target stroke_count: `20`
- **anchor_comp**: `魚`
- **hard_comps**: `['粦']`

**Component difficulty (bank_freq → difficulty):**
- `粦`: bank_freq=7, difficulty=0.4809

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3157
- after has_unknown sanity: 3133
- final with score > 0: 2440

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 3.17 | wxz_2290 | 鳝 | ['魚', '善'] | ['魚', '善'] | ⿰ | 20 | /d/htt/data/image/train/wxz/2290.jpg |
| 2 | 3.12 | wxz_0844 | 鳕 | ['魚', '雪'] | ['魚', '雪'] | ⿰ | 19 | /d/htt/data/image/train/wxz/0844.jpg |
| 3 | 3.12 | wxz_3590 | 鳔 | ['魚', '票'] | ['魚', '票'] | ⿰ | 19 | /d/htt/data/image/train/wxz/3590.jpg |
| 4 | 3.07 | wxz_1344 | 鳎 | ['魚', '𦐇'] | ['魚', '𦐇'] | ⿰ | 18 | /d/htt/data/image/train/wxz/1344.jpg |
| 5 | 3.07 | wxz_2870 | 鳍 | ['魚', '耆'] | ['魚', '耆'] | ⿰ | 18 | /d/htt/data/image/train/wxz/2870.jpg |

**OLD component coverage:**
- `魚`: ✓ (5 hits)
- `粦`: ✗ MISS (0 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 魚 | 3.17 | 鳝 | ['魚', '善'] | ⿰ | 20 | /d/htt/data/image/train/wxz/2290.jpg |
| 2 | anchor | 魚 | 3.12 | 鳕 | ['魚', '雪'] | ⿰ | 19 | /d/htt/data/image/train/wxz/0844.jpg |
| 3 | coverage | 粦 | 4.35 | 麟 | ['鹿', '粦'] | ⿰ | 23 | /d/htt/data/image/train/wxz/2475.jpg |
| 4 | coverage | 粦 | 4.35 | 磷 | ['石', '粦'] | ⿰ | 17 | /d/htt/data/image/train/wxz/2636.jpg |
| 5 | coverage | 粦 | 4.25 | 憐 | ['心', '粦'] | ⿰ | 15 | /d/htt/data/image/train/wxz/0915.jpg |

**coverage_report:**
- covered: `['魚', '粦']`
- uncovered: `[]`

**NEW component coverage (per retrieval_component):**
- `魚`: ✓ (2 hits)
- `粦`: ✓ (3 hits)

### 分数分布
- score > 0 的候选数: 2440
- score > 1.0: 1147
- score > 2.0: 26
- score > 3.0: 10

## 彎
- target retrieval_components: `['䜌', '弓']`
- target top_level_components (raw): `['䜌', '弓']`
- target retrieval_top_level: `['䜌', '弓']`
- target layout: `⿱`
- target stroke_count: `22`
- **anchor_comp**: `䜌`
- **hard_comps**: `['弓']`

**Component difficulty (bank_freq → difficulty):**
- `弓`: bank_freq=10, difficulty=0.4170

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3158
- after has_unknown sanity: 3134
- final with score > 0: 1626

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 3.12 | wxz_1249 | 變 | ['䜌', '攵'] | ['䜌', '攵'] | ⿱ | 23 | /d/htt/data/image/train/wxz/1249.jpg |
| 2 | 1.82 | wxz_2363 | 彈 | ['弓', '單'] | ['弓', '單'] | ⿰ | 15 | /d/htt/data/image/train/wxz/2363.jpg |
| 3 | 1.82 | wxz_4099 | 彈 | ['弓', '單'] | ['弓', '單'] | ⿰ | 15 | /d/htt/data/image/train/wxz/4099.jpg |
| 4 | 1.67 | wxz_1163 | 粥 | ['弓', '米', '弓'] | ['弓', '米', '弓'] | ⿲ | 12 | /d/htt/data/image/train/wxz/1163.jpg |
| 5 | 1.67 | wxz_2532 | 粥 | ['弓', '米', '弓'] | ['弓', '米', '弓'] | ⿲ | 12 | /d/htt/data/image/train/wxz/2532.jpg |

**OLD component coverage:**
- `弓`: ✓ (4 hits)
- `䜌`: ✓ (1 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 䜌 | 3.12 | 變 | ['䜌', '攵'] | ⿱ | 23 | /d/htt/data/image/train/wxz/1249.jpg |
| 2 | anchor | 䜌 | 1.82 | 彈 | ['弓', '單'] | ⿰ | 15 | /d/htt/data/image/train/wxz/2363.jpg |
| 3 | coverage | 弓 | 3.35 | 疆 | ['弓', '土', '畺'] | ⿰ | 19 | /d/htt/data/image/train/wxz/1334.jpg |
| 4 | coverage | 弓 | 3.00 | 粥 | ['弓', '米', '弓'] | ⿲ | 12 | /d/htt/data/image/train/wxz/1163.jpg |
| 5 | coverage | 弓 | 3.00 | 弘 | ['弓', '厶'] | ⿰ | 5 | /d/htt/data/image/train/wxz/3270.jpg |

**coverage_report:**
- covered: `['䜌', '弓']`
- uncovered: `[]`

**NEW component coverage (per retrieval_component):**
- `弓`: ✓ (4 hits)
- `䜌`: ✓ (1 hits)

### 分数分布
- score > 0 的候选数: 1626
- score > 1.0: 239
- score > 2.0: 1
- score > 3.0: 1

## 瘻
- target retrieval_components: `['疒', '婁']`
- target top_level_components (raw): `['疒', '婁']`
- target retrieval_top_level: `['疒', '婁']`
- target layout: `⿸`
- target stroke_count: `16`
- **anchor_comp**: `疒`
- **hard_comps**: `['婁']`

**Component difficulty (bank_freq → difficulty):**
- `婁`: bank_freq=2, difficulty=0.9102

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3158
- after has_unknown sanity: 3134
- final with score > 0: 2799

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 3.17 | wxz_1779 | 瘴 | ['疒', '章'] | ['疒', '章'] | ⿸ | 16 | /d/htt/data/image/train/wxz/1779.jpg |
| 2 | 3.12 | wxz_6658 | 瘠 | ['疒', '脊'] | ['疒', '脊'] | ⿸ | 15 | /d/htt/data/image/test/wxz/6658.jpg |
| 3 | 3.12 | wxz_0583 | 療 | ['疒', '尞'] | ['疒', '尞'] | ⿸ | 17 | /d/htt/data/image/train/wxz/0583.jpg |
| 4 | 3.12 | wxz_1852 | 癌 | ['疒', '嵒'] | ['疒', '嵒'] | ⿸ | 17 | /d/htt/data/image/train/wxz/1852.jpg |
| 5 | 3.12 | wxz_5170 | 瘤 | ['疒', '留'] | ['疒', '留'] | ⿸ | 15 | /d/htt/data/image/train/wxz/5170.jpg |

**OLD component coverage:**
- `婁`: ✗ MISS (0 hits)
- `疒`: ✓ (5 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 疒 | 3.17 | 瘴 | ['疒', '章'] | ⿸ | 16 | /d/htt/data/image/train/wxz/1779.jpg |
| 2 | anchor | 疒 | 3.12 | 瘠 | ['疒', '脊'] | ⿸ | 15 | /d/htt/data/image/test/wxz/6658.jpg |
| 3 | anchor | 疒 | 3.12 | 療 | ['疒', '尞'] | ⿸ | 17 | /d/htt/data/image/train/wxz/0583.jpg |
| 4 | anchor | 疒 | 3.12 | 癌 | ['疒', '嵒'] | ⿸ | 17 | /d/htt/data/image/train/wxz/1852.jpg |
| 5 | anchor | 疒 | 3.12 | 瘤 | ['疒', '留'] | ⿸ | 15 | /d/htt/data/image/train/wxz/5170.jpg |

**coverage_report:**
- covered: `['疒']`
- uncovered: `['婁', '婁']`
- slot_reassignments: `[{'original_hard_comp': '婁', 'reason': 'zero_bank_hits', 'replaced_with': '疒 (anchor)'}, {'original_hard_comp': '婁', 'reason': 'zero_bank_hits', 'replaced_with': '疒 (anchor)'}, {'original_hard_comp': 'free_slot', 'reason': 'no_hard_comp_hit_in_bank', 'replaced_with': '疒 (anchor)'}]`

**NEW component coverage (per retrieval_component):**
- `婁`: ✗ MISS (0 hits)
- `疒`: ✓ (5 hits)

### 分数分布
- score > 0 的候选数: 2799
- score > 1.0: 130
- score > 2.0: 44
- score > 3.0: 13

## 秦
- target retrieval_components: `['𡗗', '禾']`
- target top_level_components (raw): `['𡗗', '禾']`
- target retrieval_top_level: `['𡗗', '禾']`
- target layout: `⿱`
- target stroke_count: `10`
- **anchor_comp**: `𡗗`
- **hard_comps**: `['禾']`

**Component difficulty (bank_freq → difficulty):**
- `禾`: bank_freq=43, difficulty=0.2643

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3157
- after has_unknown sanity: 3133
- final with score > 0: 3067

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 3.17 | wxz_1537 | 泰 | ['𡗗', '水'] | ['𡗗', '水'] | ⿱ | 10 | /d/htt/data/image/train/wxz/1537.jpg |
| 2 | 3.12 | wxz_2624 | 春 | ['𡗗', '日'] | ['𡗗', '日'] | ⿱ | 9 | /d/htt/data/image/train/wxz/2624.jpg |
| 3 | 3.12 | wxz_3191 | 奏 | ['𡗗', '天'] | ['𡗗', '天'] | ⿱ | 9 | /d/htt/data/image/train/wxz/3191.jpg |
| 4 | 3.12 | wxz_3326 | 香 | ['禾', '日'] | ['禾', '日'] | ⿱ | 9 | /d/htt/data/image/train/wxz/3326.jpg |
| 5 | 3.12 | wxz_5113 | 春 | ['𡗗', '日'] | ['𡗗', '日'] | ⿱ | 9 | /d/htt/data/image/train/wxz/5113.jpg |

**OLD component coverage:**
- `禾`: ✓ (1 hits)
- `𡗗`: ✓ (4 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 𡗗 | 3.17 | 泰 | ['𡗗', '水'] | ⿱ | 10 | /d/htt/data/image/train/wxz/1537.jpg |
| 2 | anchor | 𡗗 | 3.12 | 春 | ['𡗗', '日'] | ⿱ | 9 | /d/htt/data/image/train/wxz/2624.jpg |
| 3 | coverage | 禾 | 4.45 | 香 | ['禾', '日'] | ⿱ | 9 | /d/htt/data/image/train/wxz/3326.jpg |
| 4 | coverage | 禾 | 4.40 | 季 | ['禾', '子'] | ⿱ | 8 | /d/htt/data/image/test/wxz/5800.jpg |
| 5 | coverage | 禾 | 4.40 | 委 | ['禾', '女'] | ⿱ | 8 | /d/htt/data/image/train/wxz/4545.jpg |

**coverage_report:**
- covered: `['𡗗', '禾']`
- uncovered: `[]`

**NEW component coverage (per retrieval_component):**
- `禾`: ✓ (3 hits)
- `𡗗`: ✓ (2 hits)

### 分数分布
- score > 0 的候选数: 3067
- score > 1.0: 787
- score > 2.0: 31
- score > 3.0: 8

## 赢
- target retrieval_components: `['吂', '月', '貝', '凡']`
- target top_level_components (raw): `['吂', '⿲月贝凡']`
- target retrieval_top_level: `['吂', '⿲月贝凡']`
- target layout: `⿱`
- target stroke_count: `17`
- **anchor_comp**: `吂`
- **hard_comps**: `['凡', '貝', '月']`

**Component difficulty (bank_freq → difficulty):**
- `凡`: bank_freq=5, difficulty=0.5581
- `貝`: bank_freq=32, difficulty=0.2860
- `月`: bank_freq=86, difficulty=0.2239

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3155
- after has_unknown sanity: 3131
- final with score > 0: 2728

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 2.10 | wxz_6154 | 臂 | ['辟', '月'] | ['辟', '月'] | ⿱ | 17 | /d/htt/data/image/test/wxz/6154.jpg |
| 2 | 2.10 | wxz_2995 | 賽 | ['𡨄', '貝'] | ['𡨄', '貝'] | ⿱ | 17 | /d/htt/data/image/train/wxz/2995.jpg |
| 3 | 2.10 | wxz_5047 | 贅 | ['敖', '貝'] | ['敖', '貝'] | ⿱ | 17 | /d/htt/data/image/train/wxz/5047.jpg |
| 4 | 2.05 | wxz_2924 | 赞 | ['兟', '貝'] | ['兟', '貝'] | ⿱ | 16 | /d/htt/data/image/train/wxz/2924.jpg |
| 5 | 2.00 | wxz_5464 | 賢 | ['臤', '貝'] | ['臤', '貝'] | ⿱ | 15 | /d/htt/data/image/test/wxz/5464.jpg |

**OLD component coverage:**
- `貝`: ✓ (4 hits)
- `吂`: ✗ MISS (0 hits)
- `凡`: ✗ MISS (0 hits)
- `月`: ✓ (1 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 吂 | 2.10 | 臂 | ['辟', '月'] | ⿱ | 17 | /d/htt/data/image/test/wxz/6154.jpg |
| 2 | anchor | 吂 | 2.10 | 賽 | ['𡨄', '貝'] | ⿱ | 17 | /d/htt/data/image/train/wxz/2995.jpg |
| 3 | coverage | 凡 | 4.20 | 梵 | ['林', '凡'] | ⿱ | 11 | /d/htt/data/image/train/wxz/1685.jpg |
| 4 | coverage | 貝 | 4.50 | 贅 | ['敖', '貝'] | ⿱ | 17 | /d/htt/data/image/train/wxz/5047.jpg |
| 5 | coverage | 貝 | 4.45 | 赞 | ['兟', '貝'] | ⿱ | 16 | /d/htt/data/image/train/wxz/2924.jpg |

**coverage_report:**
- covered: `['吂', '月', '貝', '凡']`
- uncovered: `[]`

**NEW component coverage (per retrieval_component):**
- `貝`: ✓ (3 hits)
- `吂`: ✗ MISS (0 hits)
- `凡`: ✓ (1 hits)
- `月`: ✓ (1 hits)

### 分数分布
- score > 0 的候选数: 2728
- score > 1.0: 616
- score > 2.0: 4
- score > 3.0: 0

## 諢
- target retrieval_components: `['言', '軍']`
- target top_level_components (raw): `['言', '軍']`
- target retrieval_top_level: `['言', '軍']`
- target layout: `⿰`
- target stroke_count: `16`
- **anchor_comp**: `言`
- **hard_comps**: `['軍']`

**Component difficulty (bank_freq → difficulty):**
- `軍`: bank_freq=7, difficulty=0.4809

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3158
- after has_unknown sanity: 3134
- final with score > 0: 2886

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 3.17 | wxz_5541 | 諷 | ['言', '風'] | ['言', '風'] | ⿰ | 16 | /d/htt/data/image/test/wxz/5541.jpg |
| 2 | 3.17 | wxz_5735 | 謎 | ['言', '迷'] | ['言', '迷'] | ⿰ | 16 | /d/htt/data/image/test/wxz/5735.jpg |
| 3 | 3.17 | wxz_6615 | 諦 | ['言', '帝'] | ['言', '帝'] | ⿰ | 16 | /d/htt/data/image/test/wxz/6615.jpg |
| 4 | 3.17 | wxz_1666 | 謀 | ['言', '某'] | ['言', '某'] | ⿰ | 16 | /d/htt/data/image/train/wxz/1666.jpg |
| 5 | 3.17 | wxz_1728 | 謊 | ['言', '荒'] | ['言', '荒'] | ⿰ | 16 | /d/htt/data/image/train/wxz/1728.jpg |

**OLD component coverage:**
- `軍`: ✗ MISS (0 hits)
- `言`: ✓ (5 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 言 | 3.17 | 諷 | ['言', '風'] | ⿰ | 16 | /d/htt/data/image/test/wxz/5541.jpg |
| 2 | anchor | 言 | 3.17 | 謎 | ['言', '迷'] | ⿰ | 16 | /d/htt/data/image/test/wxz/5735.jpg |
| 3 | coverage | 軍 | 4.45 | 輝 | ['光', '軍'] | ⿰ | 15 | /d/htt/data/image/test/wxz/5650.jpg |
| 4 | coverage | 軍 | 4.35 | 琿 | ['王', '軍'] | ⿰ | 13 | /d/htt/data/image/train/wxz/4455.jpg |
| 5 | coverage | 軍 | 4.30 | 渾 | ['水', '軍'] | ⿰ | 12 | /d/htt/data/image/train/wxz/1617.jpg |

**coverage_report:**
- covered: `['言', '軍']`
- uncovered: `[]`

**NEW component coverage (per retrieval_component):**
- `軍`: ✓ (3 hits)
- `言`: ✓ (2 hits)

### 分数分布
- score > 0 的候选数: 2886
- score > 1.0: 1790
- score > 2.0: 73
- score > 3.0: 42

---
## Verification Checklist

### 1. anchor_comp == first retrieval_top_level (normalized)
- ✅ `璨` — anchor='王', first_rtl='王'
- ✅ `霆` — anchor='雨', first_rtl='雨'
- ✅ `鳞` — anchor='魚', first_rtl='魚'
- ✅ `彎` — anchor='䜌', first_rtl='䜌'
- ✅ `瘻` — anchor='疒', first_rtl='疒'
- ✅ `秦` — anchor='𡗗', first_rtl='𡗗'
- ✅ `赢` — anchor='吂', first_rtl='吂'
- ✅ `諢` — anchor='言', first_rtl='言'

### 2. Target character not in its own results
- ✅ `璨` — refs=['環', '璐', '璞', '璜', '瑾']
- ✅ `霆` — refs=['需', '零', '艇', '蜓', '挺']
- ✅ `鳞` — refs=['鳝', '鳕', '麟', '磷', '憐']
- ✅ `彎` — refs=['變', '彈', '疆', '粥', '弘']
- ✅ `瘻` — refs=['瘴', '瘠', '療', '癌', '瘤']
- ✅ `秦` — refs=['泰', '春', '香', '季', '委']
- ✅ `赢` — refs=['臂', '賽', '梵', '贅', '赞']
- ✅ `諢` — refs=['諷', '謎', '輝', '琿', '渾']

### 3. No duplicate characters within a target's top-5
- ✅ `璨` — chars=['環', '璐', '璞', '璜', '瑾']
- ✅ `霆` — chars=['需', '零', '艇', '蜓', '挺']
- ✅ `鳞` — chars=['鳝', '鳕', '麟', '磷', '憐']
- ✅ `彎` — chars=['變', '彈', '疆', '粥', '弘']
- ✅ `瘻` — chars=['瘴', '瘠', '療', '癌', '瘤']
- ✅ `秦` — chars=['泰', '春', '香', '季', '委']
- ✅ `赢` — chars=['臂', '賽', '梵', '贅', '赞']
- ✅ `諢` — chars=['諷', '謎', '輝', '琿', '渾']

### 4. coverage_report.covered contains at least anchor_comp
- ✅ `璨` — anchor='王', covered=['王']
- ✅ `霆` — anchor='雨', covered=['雨', '廷']
- ✅ `鳞` — anchor='魚', covered=['魚', '粦']
- ✅ `彎` — anchor='䜌', covered=['䜌', '弓']
- ✅ `瘻` — anchor='疒', covered=['疒']
- ✅ `秦` — anchor='𡗗', covered=['𡗗', '禾']
- ✅ `赢` — anchor='吂', covered=['吂', '月', '貝', '凡']
- ✅ `諢` — anchor='言', covered=['言', '軍']

### 5. 霆: coverage slots contain 廴/廷 and 壬
- ✅ `霆` coverage contains 廴/廷 — ✓
- ❌ `霆` coverage contains 壬 — ✗ (uncovered: [])

### 6. 赢: any ref contains 月; note on 貝 coverage
- ✅ `赢` any ref contains 月 (anchor slots cover it) — found
- ✅ `赢` any ref contains 貝/贝 — found

### Summary: 35/36 checks passed

---
## GT Leakage Check

- 无泄漏（slot top-5 中无 GT wxz_id）

