# EVAL REPORT v2: 2509.08224_grb_restframe_unsupervised

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | 逐项核对：(i)总行数320（命中）；(ii)Type I=45，Type II=275，占比14.06%（命中）；(iii)Type I中位数T90z=0.27s、Eiso=0.69，Type II中位数T90z=14.5s、Eiso=100.0（均落入满分带区间）；(iv)T90z<2s共64个，Type I短暴占比93.3%，Type II短暴22个（命中）；(v)对M20目录与论文370样本的差异及聚类方法差异进行了充分归因讨论；(vi)给出四档结论supported。所有数值均有metrics.json和evidence_table落盘支撑，A给满分60。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示metrics.json、evidence_table.csv、evidence_summary.csv等实测证据文件齐全。metrics.json中total_rows=320、typeI_total=45、typeI_median_t90z=0.27等关键数值与报告及evidence表严格一致，且代码逻辑清晰，无抄写论文数字嫌疑（如Epz实测706与论文523.83明确区分）。证据真实可靠，B给满分40。 |

## A 核心结果达成度（60/60）

逐项核对：(i)总行数320（命中）；(ii)Type I=45，Type II=275，占比14.06%（命中）；(iii)Type I中位数T90z=0.27s、Eiso=0.69，Type II中位数T90z=14.5s、Eiso=100.0（均落入满分带区间）；(iv)T90z<2s共64个，Type I短暴占比93.3%，Type II短暴22个（命中）；(v)对M20目录与论文370样本的差异及聚类方法差异进行了充分归因讨论；(vi)给出四档结论supported。所有数值均有metrics.json和evidence_table落盘支撑，A给满分60。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示metrics.json、evidence_table.csv、evidence_summary.csv等实测证据文件齐全。metrics.json中total_rows=320、typeI_total=45、typeI_median_t90z=0.27等关键数值与报告及evidence表严格一致，且代码逻辑清晰，无抄写论文数字嫌疑（如Epz实测706与论文523.83明确区分）。证据真实可靠，B给满分40。

## 证据与重算说明

独立重算未执行（基于提交物核查）。关键实测数：总行数320，Type I计数45，Type I T90z中位数0.27s，Type II T90z中位数14.5s，均在metrics.json和evidence_table.csv中有完整落盘且与报告散文严格一致。

## 结论

- **科学结论**: `supported`
- 亮点: 数据解析严谨，完美覆盖所有核心指标与边界条件；对论文样本与冻结目录的差异归因深入且诚实，补充了k-means健全性检查以佐证方法边界。
- 不足: 无明显弱点，提交物规范且详实。