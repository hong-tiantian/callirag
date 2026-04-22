# Retrieval Test Report — Slot-Based (Anchor + Coverage)

- Bank: `wxz_bank.json` (3500 entries)
- OCR confidence threshold: 0.9
- Anchor slots: 2  |  Coverage slots: 3
- Full score formula: `3*J(rc) + 2*J(rtl) + 1*layout + 0.5*stroke_sim`
- Coverage score formula: `3*(hard_comp match) + 1*layout + 0.5*stroke_sim`
- Difficulty: `1 / log(1 + bank_freq(comp))`
- Targets: `['璨', '霆', '鳞', '彎', '瘻', '秦', '赢', '諢']`

## 璨
- target retrieval_components: `['王', '歺', '又', '米']`
- target top_level_components (raw): `['王', '粲']`
- target retrieval_top_level: `['王', '粲']`
- target layout: `⿰`
- target stroke_count: `17`
- **anchor_comp**: `王`
- **hard_comps**: `['米', '又']`

**Component difficulty (bank_freq → difficulty):**
- `米`: bank_freq=49, difficulty=0.2556
- `又`: bank_freq=64, difficulty=0.2396

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3157
- after has_unknown sanity: 3132
- final with score > 0: 2815

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 3.17 | wxz_5164 | 瑕 | ['王', '彐', '又'] | ['王', '叚'] | ⿰ | 13 | /d/htt/data/image/train/wxz/5164.jpg |
| 2 | 2.77 | wxz_0866 | 環 | ['王', '睘'] | ['王', '睘'] | ⿰ | 17 | /d/htt/data/image/train/wxz/0866.jpg |
| 3 | 2.72 | wxz_2256 | 璞 | ['王', '菐'] | ['王', '菐'] | ⿰ | 16 | /d/htt/data/image/train/wxz/2256.jpg |
| 4 | 2.67 | wxz_5794 | 璜 | ['王', '黃'] | ['王', '黃'] | ⿰ | 15 | /d/htt/data/image/test/wxz/5794.jpg |
| 5 | 2.62 | wxz_6527 | 瑪 | ['王', '馬'] | ['王', '馬'] | ⿰ | 14 | /d/htt/data/image/test/wxz/6527.jpg |

**OLD component coverage:**
- `王`: ✓ (5 hits)
- `又`: ✓ (1 hits)
- `米`: ✗ MISS (0 hits)
- `歺`: ✗ MISS (0 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 王 | 3.17 | 瑕 | ['王', '彐', '又'] | ⿰ | 13 | /d/htt/data/image/train/wxz/5164.jpg |
| 2 | anchor | 王 | 2.77 | 環 | ['王', '睘'] | ⿰ | 17 | /d/htt/data/image/train/wxz/0866.jpg |
| 3 | coverage | 米 | 4.50 | 糟 | ['米', '曹'] | ⿰ | 17 | /d/htt/data/image/train/wxz/1620.jpg |
| 4 | coverage | 又 | 4.45 | 踱 | ['口', '止', '广', '廿', '又'] | ⿰ | 16 | /d/htt/data/image/test/wxz/6344.jpg |
| 5 | coverage | 米 | 4.50 | 磷 | ['石', '米', '舛'] | ⿰ | 17 | /d/htt/data/image/train/wxz/2636.jpg |

**coverage_report:**
- covered: `['王', '又', '米']`
- uncovered: `[]`

**NEW component coverage (per retrieval_component):**
- `王`: ✓ (2 hits)
- `又`: ✓ (2 hits)
- `米`: ✓ (2 hits)
- `歺`: ✗ MISS (0 hits)

### 分数分布
- score > 0 的候选数: 2815
- score > 1.0: 1664
- score > 2.0: 51
- score > 3.0: 1

## 霆
- target retrieval_components: `['雨', '廴', '壬']`
- target top_level_components (raw): `['雨', '廷']`
- target retrieval_top_level: `['雨', '廷']`
- target layout: `⿱`
- target stroke_count: `14`
- **anchor_comp**: `雨`
- **hard_comps**: `['壬', '廴']`

**Component difficulty (bank_freq → difficulty):**
- `壬`: bank_freq=7, difficulty=0.4809
- `廴`: bank_freq=9, difficulty=0.4343

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3157
- after has_unknown sanity: 3132
- final with score > 0: 3051

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 2.92 | wxz_2022 | 需 | ['雨', '而'] | ['雨', '而'] | ⿱ | 14 | /d/htt/data/image/train/wxz/2022.jpg |
| 2 | 2.87 | wxz_5623 | 零 | ['雨', '令'] | ['雨', '令'] | ⿱ | 13 | /d/htt/data/image/test/wxz/5623.jpg |
| 3 | 2.87 | wxz_1034 | 雷 | ['雨', '田'] | ['雨', '田'] | ⿱ | 13 | /d/htt/data/image/train/wxz/1034.jpg |
| 4 | 2.87 | wxz_1153 | 電 | ['雨', '日'] | ['雨', '⿻日乚'] | ⿱ | 13 | /d/htt/data/image/train/wxz/1153.jpg |
| 5 | 2.87 | wxz_2003 | 震 | ['雨', '辰'] | ['雨', '辰'] | ⿱ | 15 | /d/htt/data/image/train/wxz/2003.jpg |

**OLD component coverage:**
- `廴`: ✗ MISS (0 hits)
- `壬`: ✗ MISS (0 hits)
- `雨`: ✓ (5 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 雨 | 2.92 | 需 | ['雨', '而'] | ⿱ | 14 | /d/htt/data/image/train/wxz/2022.jpg |
| 2 | anchor | 雨 | 2.87 | 零 | ['雨', '令'] | ⿱ | 13 | /d/htt/data/image/test/wxz/5623.jpg |
| 3 | coverage | 壬 | 4.20 | 凭 | ['亻', '壬', '几'] | ⿱ | 8 | /d/htt/data/image/train/wxz/2245.jpg |
| 4 | coverage | 廴 | 3.45 | 誕 | ['言', '廴'] | ⿰ | 13 | /d/htt/data/image/train/wxz/2644.jpg |
| 5 | coverage | 壬 | 3.40 | 艇 | ['舟', '廴', '壬'] | ⿰ | 12 | /d/htt/data/image/train/wxz/1683.jpg |

**coverage_report:**
- covered: `['雨', '廴', '壬']`
- uncovered: `[]`

**NEW component coverage (per retrieval_component):**
- `廴`: ✓ (2 hits)
- `壬`: ✓ (2 hits)
- `雨`: ✓ (2 hits)

### 分数分布
- score > 0 的候选数: 3051
- score > 1.0: 739
- score > 2.0: 23
- score > 3.0: 0

## 鳞
- target retrieval_components: `['魚', '米', '舛']`
- target top_level_components (raw): `['鱼', '粦']`
- target retrieval_top_level: `['魚', '粦']`
- target layout: `⿰`
- target stroke_count: `20`
- **anchor_comp**: `魚`
- **hard_comps**: `['舛', '米']`

**Component difficulty (bank_freq → difficulty):**
- `舛`: bank_freq=10, difficulty=0.4170
- `米`: bank_freq=49, difficulty=0.2556

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3157
- after has_unknown sanity: 3132
- final with score > 0: 2443

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 3.52 | wxz_2475 | 麟 | ['鹿', '米', '舛'] | ['鹿', '粦'] | ⿰ | 23 | /d/htt/data/image/train/wxz/2475.jpg |
| 2 | 3.52 | wxz_2636 | 磷 | ['石', '米', '舛'] | ['石', '粦'] | ⿰ | 17 | /d/htt/data/image/train/wxz/2636.jpg |
| 3 | 3.42 | wxz_0915 | 憐 | ['心', '米', '舛'] | ['心', '粦'] | ⿰ | 15 | /d/htt/data/image/train/wxz/0915.jpg |
| 4 | 3.37 | wxz_3849 | 鄰 | ['米', '舛', '邑'] | ['粦', '邑'] | ⿰ | 14 | /d/htt/data/image/train/wxz/3849.jpg |
| 5 | 2.87 | wxz_3590 | 鳔 | ['魚', '票'] | ['魚', '票'] | ⿰ | 19 | /d/htt/data/image/train/wxz/3590.jpg |

**OLD component coverage:**
- `米`: ✓ (4 hits)
- `舛`: ✓ (4 hits)
- `魚`: ✓ (1 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 魚 | 2.87 | 鳔 | ['魚', '票'] | ⿰ | 19 | /d/htt/data/image/train/wxz/3590.jpg |
| 2 | anchor | 魚 | 2.72 | 鳕 | ['魚', '雨', '彐'] | ⿰ | 19 | /d/htt/data/image/train/wxz/0844.jpg |
| 3 | coverage | 舛 | 4.35 | 麟 | ['鹿', '米', '舛'] | ⿰ | 23 | /d/htt/data/image/train/wxz/2475.jpg |
| 4 | coverage | 米 | 4.50 | 糯 | ['米', '雨', '而'] | ⿰ | 20 | /d/htt/data/image/train/wxz/1588.jpg |
| 5 | coverage | 米 | 4.45 | 類 | ['米', '犬', '頁'] | ⿰ | 19 | /d/htt/data/image/train/wxz/2535.jpg |

**coverage_report:**
- covered: `['魚', '米', '舛']`
- uncovered: `[]`

**NEW component coverage (per retrieval_component):**
- `米`: ✓ (3 hits)
- `舛`: ✓ (1 hits)
- `魚`: ✓ (2 hits)

### 分数分布
- score > 0 的候选数: 2443
- score > 1.0: 1150
- score > 2.0: 32
- score > 3.0: 4

## 彎
- target retrieval_components: `['糸', '言', '糸', '弓']`
- target top_level_components (raw): `['䜌', '弓']`
- target retrieval_top_level: `['䜌', '弓']`
- target layout: `⿱`
- target stroke_count: `22`
- **anchor_comp**: `䜌`
- **hard_comps**: `['弓', '糸', '言']`

**Component difficulty (bank_freq → difficulty):**
- `弓`: bank_freq=14, difficulty=0.3693
- `糸`: bank_freq=62, difficulty=0.2414
- `言`: bank_freq=89, difficulty=0.2222

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3158
- after has_unknown sanity: 3133
- final with score > 0: 1679

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 3.62 | wxz_1249 | 變 | ['糸', '言', '糸', '攵'] | ['䜌', '攵'] | ⿱ | 23 | /d/htt/data/image/train/wxz/1249.jpg |
| 2 | 2.10 | wxz_6536 | 警 | ['敬', '言'] | ['敬', '言'] | ⿱ | 19 | /d/htt/data/image/test/wxz/6536.jpg |
| 3 | 2.00 | wxz_3350 | 系 | ['糸'] | ['糸'] | ⿱ | 7 | /d/htt/data/image/train/wxz/3350.jpg |
| 4 | 1.90 | wxz_2359 | 纂 | ['竹', '目', '大', '糸'] | ['𮅕', '糸'] | ⿱ | 20 | /d/htt/data/image/train/wxz/2359.jpg |
| 5 | 1.85 | wxz_4440 | 燮 | ['火', '言', '火', '又'] | ['⿲火言火', '又'] | ⿱ | 17 | /d/htt/data/image/train/wxz/4440.jpg |

**OLD component coverage:**
- `弓`: ✗ MISS (0 hits)
- `糸`: ✓ (3 hits)
- `言`: ✓ (3 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 䜌 | 3.62 | 變 | ['糸', '言', '糸', '攵'] | ⿱ | 23 | /d/htt/data/image/train/wxz/1249.jpg |
| 2 | anchor | 䜌 | 2.10 | 警 | ['敬', '言'] | ⿱ | 19 | /d/htt/data/image/test/wxz/6536.jpg |
| 3 | coverage | 弓 | 4.00 | 第 | ['竹', '弓', '丨'] | ⿱ | 11 | /d/htt/data/image/test/wxz/6339.jpg |
| 4 | coverage | 糸 | 4.40 | 纂 | ['竹', '目', '大', '糸'] | ⿱ | 20 | /d/htt/data/image/train/wxz/2359.jpg |
| 5 | coverage | 言 | 4.25 | 燮 | ['火', '言', '火', '又'] | ⿱ | 17 | /d/htt/data/image/train/wxz/4440.jpg |

**coverage_report:**
- covered: `['䜌', '糸', '言', '弓']`
- uncovered: `[]`

**NEW component coverage (per retrieval_component):**
- `弓`: ✓ (1 hits)
- `糸`: ✓ (2 hits)
- `言`: ✓ (3 hits)

### 分数分布
- score > 0 的候选数: 1679
- score > 1.0: 255
- score > 2.0: 2
- score > 3.0: 1

## 瘻
- target retrieval_components: `['疒', '婁']`
- target top_level_components (raw): `['疒', '婁']`
- target retrieval_top_level: `['疒', '婁']`
- target layout: `⿸`
- target stroke_count: `16`
- **anchor_comp**: `疒`
- **hard_comps**: `[]`

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3158
- after has_unknown sanity: 3133
- final with score > 0: 2798

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 3.12 | wxz_0583 | 療 | ['疒', '尞'] | ['疒', '尞'] | ⿸ | 17 | /d/htt/data/image/train/wxz/0583.jpg |
| 2 | 3.07 | wxz_0210 | 瘦 | ['疒', '叟'] | ['疒', '叟'] | ⿸ | 14 | /d/htt/data/image/train/wxz/0210.jpg |
| 3 | 3.02 | wxz_6290 | 痰 | ['疒', '火', '火'] | ['疒', '炎'] | ⿸ | 13 | /d/htt/data/image/test/wxz/6290.jpg |
| 4 | 2.97 | wxz_3655 | 痘 | ['疒', '豆'] | ['疒', '豆'] | ⿸ | 12 | /d/htt/data/image/train/wxz/3655.jpg |
| 5 | 2.97 | wxz_3676 | 痘 | ['疒', '豆'] | ['疒', '豆'] | ⿸ | 12 | /d/htt/data/image/train/wxz/3676.jpg |

**OLD component coverage:**
- `婁`: ✗ MISS (0 hits)
- `疒`: ✓ (5 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 疒 | 3.12 | 療 | ['疒', '尞'] | ⿸ | 17 | /d/htt/data/image/train/wxz/0583.jpg |
| 2 | anchor | 疒 | 3.07 | 瘦 | ['疒', '叟'] | ⿸ | 14 | /d/htt/data/image/train/wxz/0210.jpg |
| 3 | anchor | 疒 | 3.02 | 痰 | ['疒', '火', '火'] | ⿸ | 13 | /d/htt/data/image/test/wxz/6290.jpg |
| 4 | anchor | 疒 | 2.97 | 痘 | ['疒', '豆'] | ⿸ | 12 | /d/htt/data/image/train/wxz/3655.jpg |
| 5 | anchor | 疒 | 2.97 | 痨 | ['疒', '劳'] | ⿸ | 12 | /d/htt/data/image/train/wxz/5045.jpg |

**coverage_report:**
- covered: `['疒']`
- uncovered: `[]`

**NEW component coverage (per retrieval_component):**
- `婁`: ✗ MISS (0 hits)
- `疒`: ✓ (5 hits)

### 分数分布
- score > 0 的候选数: 2798
- score > 1.0: 130
- score > 2.0: 44
- score > 3.0: 3

## 秦
- target retrieval_components: `['三', '人', '禾']`
- target top_level_components (raw): `['𡗗', '禾']`
- target retrieval_top_level: `['𡗗', '禾']`
- target layout: `⿱`
- target stroke_count: `10`
- **anchor_comp**: `𡗗`
- **hard_comps**: `['三', '禾', '人']`

**Component difficulty (bank_freq → difficulty):**
- `三`: bank_freq=1, difficulty=1.4427
- `禾`: bank_freq=68, difficulty=0.2362
- `人`: bank_freq=121, difficulty=0.2082

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3157
- after has_unknown sanity: 3132
- final with score > 0: 3070

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 2.87 | wxz_3326 | 香 | ['禾', '日'] | ['禾', '日'] | ⿱ | 9 | /d/htt/data/image/train/wxz/3326.jpg |
| 2 | 2.82 | wxz_5800 | 季 | ['禾', '子'] | ['禾', '子'] | ⿱ | 8 | /d/htt/data/image/test/wxz/5800.jpg |
| 3 | 2.82 | wxz_4545 | 委 | ['禾', '女'] | ['禾', '女'] | ⿱ | 8 | /d/htt/data/image/train/wxz/4545.jpg |
| 4 | 2.77 | wxz_6341 | 秀 | ['禾', '乃'] | ['禾', '乃'] | ⿱ | 7 | /d/htt/data/image/test/wxz/6341.jpg |
| 5 | 2.45 | wxz_6671 | 黎 | ['禾', '勹', '人', '八', '八'] | ['𥝢', '⿱人氺'] | ⿱ | 15 | /d/htt/data/image/test/wxz/6671.jpg |

**OLD component coverage:**
- `三`: ✗ MISS (0 hits)
- `禾`: ✓ (5 hits)
- `人`: ✓ (1 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 𡗗 | 2.17 | 泰 | ['𡗗', '水'] | ⿱ | 10 | /d/htt/data/image/train/wxz/1537.jpg |
| 2 | anchor | 𡗗 | 2.12 | 春 | ['𡗗', '日'] | ⿱ | 9 | /d/htt/data/image/train/wxz/2624.jpg |
| 3 | coverage | 三 | 4.15 | 三 | ['三'] | ⿱ | 3 | /d/htt/data/image/train/wxz/3358.jpg |
| 4 | coverage | 禾 | 4.45 | 香 | ['禾', '日'] | ⿱ | 9 | /d/htt/data/image/train/wxz/3326.jpg |
| 5 | coverage | 人 | 4.50 | 拳 | ['八', '二', '人', '手'] | ⿱ | 10 | /d/htt/data/image/test/wxz/6652.jpg |

**coverage_report:**
- covered: `['𡗗', '三', '人', '禾']`
- uncovered: `[]`

**NEW component coverage (per retrieval_component):**
- `三`: ✓ (1 hits)
- `禾`: ✓ (1 hits)
- `人`: ✓ (1 hits)

### 分数分布
- score > 0 的候选数: 3070
- score > 1.0: 818
- score > 2.0: 20
- score > 3.0: 0

## 赢
- target retrieval_components: `['亡', '口', '月', '貝', '凡']`
- target top_level_components (raw): `['吂', '⿲月贝凡']`
- target retrieval_top_level: `['吂', '⿲月贝凡']`
- target layout: `⿱`
- target stroke_count: `17`
- **anchor_comp**: `吂`
- **hard_comps**: `['凡', '亡', '貝']`

**Component difficulty (bank_freq → difficulty):**
- `凡`: bank_freq=8, difficulty=0.4551
- `亡`: bank_freq=11, difficulty=0.4024
- `貝`: bank_freq=50, difficulty=0.2543

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3155
- after has_unknown sanity: 3130
- final with score > 0: 2772

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 2.36 | wxz_6154 | 臂 | ['尸', '口', '辛', '月'] | ['辟', '月'] | ⿱ | 17 | /d/htt/data/image/test/wxz/6154.jpg |
| 2 | 2.20 | wxz_1487 | 望 | ['亡', '月', '王'] | ['⿰亡月', '王'] | ⿱ | 11 | /d/htt/data/image/train/wxz/1487.jpg |
| 3 | 2.11 | wxz_2834 | 瀛 | ['水', '亡', '口', '月', '女', '凡'] | ['水', '嬴'] | ⿰ | 19 | /d/htt/data/image/train/wxz/2834.jpg |
| 4 | 1.90 | wxz_4497 | 質 | ['斤', '斤', '貝'] | ['斦', '貝'] | ⿱ | 15 | /d/htt/data/image/train/wxz/4497.jpg |
| 5 | 1.88 | wxz_2924 | 赞 | ['𠂒', '儿', '𠂒', '儿', '貝'] | ['兟', '貝'] | ⿱ | 16 | /d/htt/data/image/train/wxz/2924.jpg |

**OLD component coverage:**
- `月`: ✓ (3 hits)
- `口`: ✓ (2 hits)
- `貝`: ✓ (2 hits)
- `凡`: ✓ (1 hits)
- `亡`: ✓ (2 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 吂 | 2.36 | 臂 | ['尸', '口', '辛', '月'] | ⿱ | 17 | /d/htt/data/image/test/wxz/6154.jpg |
| 2 | anchor | 吂 | 2.20 | 望 | ['亡', '月', '王'] | ⿱ | 11 | /d/htt/data/image/train/wxz/1487.jpg |
| 3 | coverage | 凡 | 4.25 | 筑 | ['竹', '工', '凡'] | ⿱ | 12 | /d/htt/data/image/train/wxz/0149.jpg |
| 4 | coverage | 亡 | 4.05 | 盲 | ['亡', '目'] | ⿱ | 8 | /d/htt/data/image/train/wxz/4938.jpg |
| 5 | coverage | 貝 | 4.50 | 贅 | ['龶', '𠃌', '攵', '貝'] | ⿱ | 17 | /d/htt/data/image/train/wxz/5047.jpg |

**coverage_report:**
- covered: `['吂', '亡', '口', '月', '貝', '凡']`
- uncovered: `[]`

**NEW component coverage (per retrieval_component):**
- `月`: ✓ (2 hits)
- `口`: ✓ (1 hits)
- `貝`: ✓ (1 hits)
- `凡`: ✓ (1 hits)
- `亡`: ✓ (2 hits)

### 分数分布
- score > 0 的候选数: 2772
- score > 1.0: 653
- score > 2.0: 3
- score > 3.0: 0

## 諢
- target retrieval_components: `['言', '冖', '車']`
- target top_level_components (raw): `['言', '軍']`
- target retrieval_top_level: `['言', '軍']`
- target layout: `⿰`
- target stroke_count: `16`
- **anchor_comp**: `言`
- **hard_comps**: `['車', '冖']`

**Component difficulty (bank_freq → difficulty):**
- `車`: bank_freq=28, difficulty=0.2970
- `冖`: bank_freq=60, difficulty=0.2433

### 过滤阶段
- 原始 bank: 3500
- after ocr_conf: 3158
- after self-exclusion: 3158
- after has_unknown sanity: 3133
- final with score > 0: 2886

### OLD Top-5 (Pure Relevance, pre-refactor)
| rank | score | bank_id | char | retrieval_components | top_level | layout | strokes | wxz_path |
|------|-------|---------|------|----------------------|-----------|--------|---------|----------|
| 1 | 3.52 | wxz_4455 | 琿 | ['王', '冖', '車'] | ['王', '軍'] | ⿰ | 13 | /d/htt/data/image/train/wxz/4455.jpg |
| 2 | 3.47 | wxz_1617 | 渾 | ['水', '冖', '車'] | ['水', '軍'] | ⿰ | 12 | /d/htt/data/image/train/wxz/1617.jpg |
| 3 | 3.47 | wxz_3077 | 惲 | ['心', '冖', '車'] | ['心', '軍'] | ⿰ | 12 | /d/htt/data/image/train/wxz/3077.jpg |
| 4 | 3.47 | wxz_5088 | 揮 | ['手', '冖', '車'] | ['手', '軍'] | ⿰ | 12 | /d/htt/data/image/train/wxz/5088.jpg |
| 5 | 2.92 | wxz_5541 | 諷 | ['言', '風'] | ['言', '風'] | ⿰ | 16 | /d/htt/data/image/test/wxz/5541.jpg |

**OLD component coverage:**
- `冖`: ✓ (4 hits)
- `言`: ✓ (1 hits)
- `車`: ✓ (4 hits)

### NEW Slot-Based Top-5
| rank | role | matched_comp | score | char | retrieval_components | layout | strokes | wxz_path |
|------|------|--------------|-------|------|----------------------|--------|---------|----------|
| 1 | anchor | 言 | 2.92 | 諷 | ['言', '風'] | ⿰ | 16 | /d/htt/data/image/test/wxz/5541.jpg |
| 2 | anchor | 言 | 2.92 | 諦 | ['言', '帝'] | ⿰ | 16 | /d/htt/data/image/test/wxz/6615.jpg |
| 3 | coverage | 車 | 4.50 | 輻 | ['車', '畐'] | ⿰ | 16 | /d/htt/data/image/train/wxz/3787.jpg |
| 4 | coverage | 冖 | 4.50 | 擋 | ['手', '小', '冖', '口', '田'] | ⿰ | 16 | /d/htt/data/image/train/wxz/4364.jpg |
| 5 | coverage | 車 | 4.50 | 輯 | ['車', '口', '耳'] | ⿰ | 16 | /d/htt/data/image/train/wxz/4864.jpg |

**coverage_report:**
- covered: `['言', '冖', '車']`
- uncovered: `[]`

**NEW component coverage (per retrieval_component):**
- `冖`: ✓ (1 hits)
- `言`: ✓ (2 hits)
- `車`: ✓ (2 hits)

### 分数分布
- score > 0 的候选数: 2886
- score > 1.0: 1791
- score > 2.0: 82
- score > 3.0: 4

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
- ✅ `璨` — refs=['瑕', '環', '糟', '踱', '磷']
- ✅ `霆` — refs=['需', '零', '凭', '誕', '艇']
- ✅ `鳞` — refs=['鳔', '鳕', '麟', '糯', '類']
- ✅ `彎` — refs=['變', '警', '第', '纂', '燮']
- ✅ `瘻` — refs=['療', '瘦', '痰', '痘', '痨']
- ✅ `秦` — refs=['泰', '春', '三', '香', '拳']
- ✅ `赢` — refs=['臂', '望', '筑', '盲', '贅']
- ✅ `諢` — refs=['諷', '諦', '輻', '擋', '輯']

### 3. No duplicate characters within a target's top-5
- ✅ `璨` — chars=['瑕', '環', '糟', '踱', '磷']
- ✅ `霆` — chars=['需', '零', '凭', '誕', '艇']
- ✅ `鳞` — chars=['鳔', '鳕', '麟', '糯', '類']
- ✅ `彎` — chars=['變', '警', '第', '纂', '燮']
- ✅ `瘻` — chars=['療', '瘦', '痰', '痘', '痨']
- ✅ `秦` — chars=['泰', '春', '三', '香', '拳']
- ✅ `赢` — chars=['臂', '望', '筑', '盲', '贅']
- ✅ `諢` — chars=['諷', '諦', '輻', '擋', '輯']

### 4. coverage_report.covered contains at least anchor_comp
- ✅ `璨` — anchor='王', covered=['王', '又', '米']
- ✅ `霆` — anchor='雨', covered=['雨', '廴', '壬']
- ✅ `鳞` — anchor='魚', covered=['魚', '米', '舛']
- ✅ `彎` — anchor='䜌', covered=['䜌', '糸', '言', '弓']
- ✅ `瘻` — anchor='疒', covered=['疒']
- ✅ `秦` — anchor='𡗗', covered=['𡗗', '三', '人', '禾']
- ✅ `赢` — anchor='吂', covered=['吂', '亡', '口', '月', '貝', '凡']
- ✅ `諢` — anchor='言', covered=['言', '冖', '車']

### 5. 霆: coverage slots contain 廴/廷 and 壬
- ✅ `霆` coverage contains 廴/廷 — ✓
- ✅ `霆` coverage contains 壬 — ✓

### 6. 赢: any ref contains 月; note on 貝 coverage
- ✅ `赢` any ref contains 月 (anchor slots cover it) — found
- ✅ `赢` any ref contains 貝/贝 — found

### Summary: 36/36 checks passed

---
## GT Leakage Check

- 无泄漏（slot top-5 中无 GT wxz_id）

