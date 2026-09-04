# EVAL REPORT v7: 2308.05572_gaia_wd_xp_class

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 100.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1: 交付物完整，包含metrics.json、evidence_table.csv和可运行代码，满足机器可读要求(12分)。A2: 核心统计数据与PAPER_ANCHOR真值及冻结数据探针完全吻合，正确识别版本漂移，科学结论保真(33分)。A3: 采用严谨的定宽字节切片解析，进行了多口径交叉验证并解释舍入差异，方法sound且可复现(15分)。 |
| B 真值一致性/可验证性 | 40 | 40 | truth_check=matched | agent数 total_rows=100886 vs 锚点 100886 → 吻合；agent数 DA high-conf=77330 vs 锚点 77330 → 吻合；agent数 n_high_conf_total=89188 vs 锚点 89188 → 吻合；agent数 n_teff_neg999=1396 vs 锚点(冻结数据实测) 1396 → 吻合；agent数 n_da_teff_gt_300000_all=68 vs 锚点(冻结数据实测) 68 → 吻合。所有关键指标均与真值及冻结数据探针精确匹配。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1: 交付物完整，包含metrics.json、evidence_table.csv和可运行代码，满足机器可读要求(12分)。A2: 核心统计数据与PAPER_ANCHOR真值及冻结数据探针完全吻合，正确识别版本漂移，科学结论保真(33分)。A3: 采用严谨的定宽字节切片解析，进行了多口径交叉验证并解释舍入差异，方法sound且可复现(15分)。

## B 真值一致性/可验证性（40/40）[truth_check=matched]

agent数 total_rows=100886 vs 锚点 100886 → 吻合；agent数 DA high-conf=77330 vs 锚点 77330 → 吻合；agent数 n_high_conf_total=89188 vs 锚点 89188 → 吻合；agent数 n_teff_neg999=1396 vs 锚点(冻结数据实测) 1396 → 吻合；agent数 n_da_teff_gt_300000_all=68 vs 锚点(冻结数据实测) 68 → 吻合。所有关键指标均与真值及冻结数据探针精确匹配。

## 证据与重算说明

独立重算未执行。关键实测数(total=100886, DA=77330, Teff=-999=1396, DA>300k=68)均有明确落盘记录(metrics.json, evidence_table.csv)且与代码逻辑自洽，无抄数嫌疑，证据链完整。

## 结论

- **科学结论**: `supported`
- **可验证性**: `matched`
- 亮点: 完美复现了论文的所有核心统计数据，代码解析逻辑严谨规范，对版本漂移和口径差异的分析极其透彻。
- 不足: 裁判未执行独立代码重算，但落盘证据与代码逻辑已充分支撑结论，提交物本身无明显弱点。