# EVAL REPORT v2: 2112.10074_qubrats_uncertainty_seg

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1(20分): 精确实现论文Eq.1公式，evidence_table与metrics.json中AUC1/2/3及score数值完整且验算一致(如det_s2 WT score=0.8737)。A2(20分): threshold_means.csv证实随τ降低DSC单调上升(0.80->0.95)，FTP/FTN保持低位，过滤有效性趋势完全成立。A3(20分): metrics.json中ranking_decoupling详列6模型在3实体上的排名错位(如WT上det_s2 score第1但DSC第5)，排名解耦论断获充分支撑。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示metrics.json与evidence_table.csv等核心证据文件齐全。抽查字段1(evidence_table中det_s2 WT score=0.8737)与抽查字段2(threshold_means中mcd_s0 WT τ=75 dsc=0.8562)在报告、CSV与JSON中严格一致。未发现抄袭论文锚值或测试集泄漏，证据真实可信，落入最高档。 |

## A 核心结果达成度（60/60）

A1(20分): 精确实现论文Eq.1公式，evidence_table与metrics.json中AUC1/2/3及score数值完整且验算一致(如det_s2 WT score=0.8737)。A2(20分): threshold_means.csv证实随τ降低DSC单调上升(0.80->0.95)，FTP/FTN保持低位，过滤有效性趋势完全成立。A3(20分): metrics.json中ranking_decoupling详列6模型在3实体上的排名错位(如WT上det_s2 score第1但DSC第5)，排名解耦论断获充分支撑。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示metrics.json与evidence_table.csv等核心证据文件齐全。抽查字段1(evidence_table中det_s2 WT score=0.8737)与抽查字段2(threshold_means中mcd_s0 WT τ=75 dsc=0.8562)在报告、CSV与JSON中严格一致。未发现抄袭论文锚值或测试集泄漏，证据真实可信，落入最高档。

## 证据与重算说明

独立重算未执行。关键实测数抽查：det_s2 WT score=0.8737 (AUC1=0.8619, AUC2=0.1085, AUC3=0.1322)，公式验算一致；mcd_s0 WT τ=75时dsc=0.8562, ftp=0.1057, ftn=0.0182。所有数值均来自冻结数据计算，未混用论文数字。

## 结论

- **科学结论**: `supported`
- 亮点: 实验设计严谨，不仅复现了核心公式与排名解耦现象，还引入了随机不确定性消融对照以证明score度量的是信息量而非单纯精度；证据文件结构清晰，数值高度一致。
- 不足: 受限于10例单模态数据，ET/TC的绝对分割精度较低，导致部分实体的AUC绝对值偏小，但方向性结论依然稳健。