# EVAL REPORT v2: 2303.08092_solar_energetic_particle_ensemble

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（deepseek-v4-flash）
- 评测时间: 2026-08-21

## 总分: 66.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 34.0 | 60 | A1（14/20）：evidence_table.csv 与 metrics.json 证实 4 方法均有 10 次切分、完整指标及中位数±MAD；清洗后 24570/74 与任务预期一致。但 base epochs 缩为 150（论文 500），且 RH v1/v2 的 epochs 按 12/n_sel 缩放后实际为 450/300，与论文 500 基准不符；无 submission/run.sh 实体文件，切分与清洗正确但协议偏离，故扣分后取 14。A2（11/25）：判据1 成立（RH_v2 中位 TSS 0.868 ≥ CoNN 0.807）给 10；判据2 部分成立（RH_v1 MAD 0.026、RH_v2 MAD 0.032 均 < CoNN MAD 0.055，HSS 0.109≥0.051，但 Committee MAD 0.067 未更低）给 1；判据3 部分成立（RH_v2 TSS 0.868≥Committee 0.833、HSS 0.109≥0.064，但 RH_v2 TSS 0.868<RH_v1 0.882）给 0。各子项按部分命中带下限计。A3（9/15）：报告了与论文 Table2 的绝对差（CoNN ΔTSS=-0.099、Committee -0.093、RH_v1 -0.033、RH_v2 -0.076），除 RH_v1 外均超出 ±0.05 容差，且说明数据版本与 epochs 缩减影响，给 4；结论 partially_supported 且依据清晰，给 5。 |
| B 证据真实性/实际复现 | 32.0 | 40 | 磁盘扫描显示 metrics.json、evidence_table.csv、critical_checks.json、uncertainty.json 等实测证据文件齐全；evidence_table.csv 含 4 方法×10 切分的逐次 TSS/HSS/混淆矩阵/AUC，metrics.json 的汇总中位数与各 split 原始数据可核对一致（如 CoNN 中位 TSS 0.807、RH_v2 0.868），清洗行数 24570/74 与报告严格一致。按三级分层，属『有证据文件且数值与报告严格一致、可核对』，落 [30,40] 区间。但独立重算未执行（未实际运行代码验证绝对差≤0.02），故取区间中值偏低 32。 |

## A 核心结果达成度（34.0/60）

A1（14/20）：evidence_table.csv 与 metrics.json 证实 4 方法均有 10 次切分、完整指标及中位数±MAD；清洗后 24570/74 与任务预期一致。但 base epochs 缩为 150（论文 500），且 RH v1/v2 的 epochs 按 12/n_sel 缩放后实际为 450/300，与论文 500 基准不符；无 submission/run.sh 实体文件，切分与清洗正确但协议偏离，故扣分后取 14。A2（11/25）：判据1 成立（RH_v2 中位 TSS 0.868 ≥ CoNN 0.807）给 10；判据2 部分成立（RH_v1 MAD 0.026、RH_v2 MAD 0.032 均 < CoNN MAD 0.055，HSS 0.109≥0.051，但 Committee MAD 0.067 未更低）给 1；判据3 部分成立（RH_v2 TSS 0.868≥Committee 0.833、HSS 0.109≥0.064，但 RH_v2 TSS 0.868<RH_v1 0.882）给 0。各子项按部分命中带下限计。A3（9/15）：报告了与论文 Table2 的绝对差（CoNN ΔTSS=-0.099、Committee -0.093、RH_v1 -0.033、RH_v2 -0.076），除 RH_v1 外均超出 ±0.05 容差，且说明数据版本与 epochs 缩减影响，给 4；结论 partially_supported 且依据清晰，给 5。

## B 证据真实性/实际复现（32.0/40）

磁盘扫描显示 metrics.json、evidence_table.csv、critical_checks.json、uncertainty.json 等实测证据文件齐全；evidence_table.csv 含 4 方法×10 切分的逐次 TSS/HSS/混淆矩阵/AUC，metrics.json 的汇总中位数与各 split 原始数据可核对一致（如 CoNN 中位 TSS 0.807、RH_v2 0.868），清洗行数 24570/74 与报告严格一致。按三级分层，属『有证据文件且数值与报告严格一致、可核对』，落 [30,40] 区间。但独立重算未执行（未实际运行代码验证绝对差≤0.02），故取区间中值偏低 32。

## 证据与重算说明

独立重算未执行。关键实测数（来自 evidence_table.csv/metrics.json）：清洗后数据 24,570 行/74 SEP；CoNN 中位 TSS=0.807±0.055；RH_v2 中位 TSS=0.868±0.032；Committee 中位 TSS=0.833±0.067；RH_v1 中位 TSS=0.882±0.026；RH_v2 中位 HSS=0.109；清洗行数与逐次 TSS 数值在证据文件中自洽，未见抄论文数字或测试段泄漏痕迹。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 证据链完整：evidence_table.csv 与 metrics.json 数值严格自洽，数据清洗结果与任务预期一致；相对锚点的判定（RH_v2≥CoNN、RH 离散度更低）成立并有落盘数据支撑，结论 partially_supported 诚实、归因清晰。
- 不足: 训练预算与论文规格不符（base epochs 150 vs 500），导致绝对 TSS/HSS 偏离论文锚值超出 ±0.05 容差；缺失独立 run.sh 与依赖版本固定，且 RH_v2 未能在 TSS 上超越 RH_v1、Committee 离散度未低于 CoNN，核心主张仅部分成立。