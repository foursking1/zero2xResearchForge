# EVAL REPORT v7: 2507.05730_had_survey

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 100.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 33.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **60.0** | 60 | A1：交付了完整的evidence_table.csv、summary.json及可运行代码，机器可读结果完整，得12分。A2：11/14数据集RX AUC与锚点自检值精确匹配，3个版本差异行被正确归因且数值与自检真值一致，min_auc=0.8221，完美支持论文claim，得33分。A3：全局RX实现严谨（伪逆处理共线性），GT仅用于评估无泄漏，附带SHA-256校验，方法sound且可复现，得15分。 |
| B 真值一致性/可验证性 | 40 | 40 | truth_check=matched | agent数与PAPER_ANCHOR自检真值逐条比对：agent abu-airport-1 auc_rx=0.8221 vs 锚点 0.8221 → 吻合；agent aviris_1 auc_rx=0.8866 vs 锚点 0.8866 → 吻合；agent hydice_urban auc_rx=0.9857 vs 锚点 0.9857 → 吻合；agent sandiego auc_rx=0.9219 vs 锚点自检 0.9219（论文表值0.9403） → 吻合（正确复现了版本差异导致的自检值，未抄袭论文原表数字）；agent n_match=11 vs 锚点 11/14 → 吻合。所有关键指标均在容差内精确匹配。 |

## A 核心结果达成度（60.0/60 = A1 12.0 + A2 33.0 + A3 15.0）

A1：交付了完整的evidence_table.csv、summary.json及可运行代码，机器可读结果完整，得12分。A2：11/14数据集RX AUC与锚点自检值精确匹配，3个版本差异行被正确归因且数值与自检真值一致，min_auc=0.8221，完美支持论文claim，得33分。A3：全局RX实现严谨（伪逆处理共线性），GT仅用于评估无泄漏，附带SHA-256校验，方法sound且可复现，得15分。

## B 真值一致性/可验证性（40/40）[truth_check=matched]

agent数与PAPER_ANCHOR自检真值逐条比对：agent abu-airport-1 auc_rx=0.8221 vs 锚点 0.8221 → 吻合；agent aviris_1 auc_rx=0.8866 vs 锚点 0.8866 → 吻合；agent hydice_urban auc_rx=0.9857 vs 锚点 0.9857 → 吻合；agent sandiego auc_rx=0.9219 vs 锚点自检 0.9219（论文表值0.9403） → 吻合（正确复现了版本差异导致的自检值，未抄袭论文原表数字）；agent n_match=11 vs 锚点 11/14 → 吻合。所有关键指标均在容差内精确匹配。

## 证据与重算说明

独立重算未执行。关键实测数：abu-airport-1 auc_rx=0.8221，aviris_1 auc_rx=0.8866，hydice_urban auc_rx=0.9857，sandiego auc_rx=0.9219，min_auc=0.8221，n_match=11，均与落盘evidence_table.csv及summary.json严格一致，且与PAPER_ANCHOR自检真值完全吻合，未发现抄论文数字或测试段泄漏现象。

## 结论

- **科学结论**: `supported`
- **可验证性**: `matched`
- 亮点: 复现工作极其严谨，完美复现11个精确一致的数据集并正确归因3个版本差异，额外实现CRD算法验证方法族排序方向，代码包含SHA-256完整性校验，证据链非常完整。
- 不足: 运行时间受环境负载影响略高于论文标称的0.40s（实测均值约1.3s），但仍在任务允许的5s范围内，无明显实质性弱点。