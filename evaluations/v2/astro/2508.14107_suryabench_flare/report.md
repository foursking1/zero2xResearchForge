# EVAL REPORT v2: 2508.14107_suryabench_flare

- 执行 agent: Claude Code (deepseek-chat, 经 DeepSeek Anthropic 兼容网关)
- 评测裁判: SciSolveBench LLM 裁判 v2（deepseek-v4-flash）
- 评测时间: 2026-08-21

## 总分: 70.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 30.0 | 60 | 依据 SCORE_RUBRIC 的 A 维度数值带逐项核对：agent 报告的核心实测数值为 test 期 label_max TSS=0.5674441784553819（证据表与 metrics.json 落盘，report.md 亦一致）。对每个 band 做布尔判断：满分带要求 TSS∈[0.20,0.42]——0.5674 不落入；半满带要求 TSS∈[0.10,0.20)∪(0.42,0.70]——0.5674 明确落入 (0.42,0.70]；零分带要求 TSS<0.10 或 TSS>0.70——均不满足，严禁套用 >0.70 判 0 规则。该 band 的附加条件（同步报告 HSS=0.4636、base-rate 漂移分析 train 0.1211→test 0.2943、阈值敏感性包络 [0.1608,0.6172] 与 Bootstrap CI [0.560,0.574]）均满足，且证据已落盘（metrics.json/evidence_table.csv），故授予该 band 满分 30 分而非取区间下限。数据规模 128,328、四分裂之和 128,328、label_max/label_cum 100% 自洽均与锚 A1/A2 一致，并入证据核查而非重复加分。方向感知：0.5674 属 GOES 历史 persistence 型技能，与论文 SDO 影像 CNN 基线（0.261–0.359）不同源，rubric 已明确 >0.70 判 0，0.5674 不受该限制，故按半满带给 30。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示：metrics.json 存在、evidence_table.csv 存在且列完整（period,n,base_rate,threshold,tp,fp,tn,fn,tss,hss）——不属于『无实测证据』情形，B≥30 成立；且证据文件内部数值与报告散文、metrics.json 严格一致，可核对，故授予 [30,40] 满分档 40 分。关键抽查数核对：test 期 base_rate=0.2942665571975917（n=43,848，正样本 12,903）与冻结锚值 0.2943 一致；test 期 TSS=0.5674441784553819 可由证据表 TP=11,880, FP=10,932, TN=20,013, FN=1,023 精确重算（TPR=0.9207, FPR=0.3533, TSS=0.5674），与报告值相对差 <1e-6。evidence_table 各行的 TSS/HSS 均可由 TP/FP/TN/FN 重算，无抄数嫌疑。train 期 base_rate=0.12106741573033708（9,051/74,760）与锚值 0.1211 一致。无任何论文数值被伪称为实测数。 |

## A 核心结果达成度（30.0/60）

依据 SCORE_RUBRIC 的 A 维度数值带逐项核对：agent 报告的核心实测数值为 test 期 label_max TSS=0.5674441784553819（证据表与 metrics.json 落盘，report.md 亦一致）。对每个 band 做布尔判断：满分带要求 TSS∈[0.20,0.42]——0.5674 不落入；半满带要求 TSS∈[0.10,0.20)∪(0.42,0.70]——0.5674 明确落入 (0.42,0.70]；零分带要求 TSS<0.10 或 TSS>0.70——均不满足，严禁套用 >0.70 判 0 规则。该 band 的附加条件（同步报告 HSS=0.4636、base-rate 漂移分析 train 0.1211→test 0.2943、阈值敏感性包络 [0.1608,0.6172] 与 Bootstrap CI [0.560,0.574]）均满足，且证据已落盘（metrics.json/evidence_table.csv），故授予该 band 满分 30 分而非取区间下限。数据规模 128,328、四分裂之和 128,328、label_max/label_cum 100% 自洽均与锚 A1/A2 一致，并入证据核查而非重复加分。方向感知：0.5674 属 GOES 历史 persistence 型技能，与论文 SDO 影像 CNN 基线（0.261–0.359）不同源，rubric 已明确 >0.70 判 0，0.5674 不受该限制，故按半满带给 30。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示：metrics.json 存在、evidence_table.csv 存在且列完整（period,n,base_rate,threshold,tp,fp,tn,fn,tss,hss）——不属于『无实测证据』情形，B≥30 成立；且证据文件内部数值与报告散文、metrics.json 严格一致，可核对，故授予 [30,40] 满分档 40 分。关键抽查数核对：test 期 base_rate=0.2942665571975917（n=43,848，正样本 12,903）与冻结锚值 0.2943 一致；test 期 TSS=0.5674441784553819 可由证据表 TP=11,880, FP=10,932, TN=20,013, FN=1,023 精确重算（TPR=0.9207, FPR=0.3533, TSS=0.5674），与报告值相对差 <1e-6。evidence_table 各行的 TSS/HSS 均可由 TP/FP/TN/FN 重算，无抄数嫌疑。train 期 base_rate=0.12106741573033708（9,051/74,760）与锚值 0.1211 一致。无任何论文数值被伪称为实测数。

## 证据与重算说明

独立重算未执行（基于提交物静态核对与磁盘证据扫描）。关键实测数逐字引用：test n=43848、base_rate=0.2942665571975917、threshold=0.38、TP=11880、FP=10932、TN=20013、FN=1023、TSS=0.5674441784553819、HSS=0.46364597810823066；train base_rate=0.12106741573033708（9,051/74,760）；test 分年 base_rate 2020=0.0055, 2021=0.0613, 2022=0.2638, 2023=0.4435, 2024=0.6969，与 PAPER_ANCHOR 辅助事实逐项一致。metrics.json 中存在 data_checks（total_rows_full=128328、splits_sum=128328、全部 label_max/label_cum 自洽=True、concat_equals_data=True）、warmup（dropped_rows=743，全部落在 train 期）、阈值敏感性（tss_min=0.1608, tss_max=0.6172, tss_at_base_rate_threshold=0.5006）、Bootstrap 95% CI=[0.5601, 0.5741]、分年 ROC-AUC（2020: 0.750, 2021: 0.788, 2022: 0.755, 2023: 0.733, 2024: 0.792）、漂移分解（aggregate 0.5674 vs 年内均值 0.1761）及 5 个稳健性对照模型，证据链完整闭环。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 方法极其严谨：特征全部基于 shift(24)+ 严格滞后已完成窗口，泄漏参照（shift(1) TSS=0.968）被显式量化并排除；warm-up 743 行显式丢弃并报告；base-rate 漂移（0.121→0.294）与泛化归因被量化分解（聚合 TSS 0.567 vs 年内均值 0.176，分年 ROC-AUC 0.73–0.79 证明阈值无关真信号），证据表/metrics/报告三处数值严格自洽，B 维度无可挑剔。
- 不足: 受冻结数据仅含 GOES 标量序列限制，模型 TSS=0.5674 落入半满带 (0.42,0.70]，无法落入满分带 [0.20,0.42] 以复现论文 SDO 影像 CNN 基线的数值区间（0.261–0.359），故 A 维度得 30 分而封顶上限为 B+C 满分；聚合技能约 2/3 来自 base-rate 漂移捕获，固定阈值下 2020 太阳极小期 TSS≈0，需如实声明'非无漂移纯泛化'。