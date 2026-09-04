# EVAL REPORT v2: 2104.02846_multiscene

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（deepseek-v4-flash）
- 评测时间: 2026-08-21

## 总分: 44.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 8.0 | 60 | agent 实测测试整体 mAP=0.415808（41.6%），论文锚 64.8%，绝对差 d=23.2pp。逐一带判定：d≤4（mAP≥60.8%）→不满足；4<d≤10（mAP∈[54.8,60.8)）→不满足；10<d≤20→不满足；d>20→命中，按 rubric 该带 0–11 分。因 mAP 有落盘 metrics.json/evidence_table.csv 实测支撑（非仅散文），故可在该带内给分；但方法为冻结 ResNet50 特征+逻辑回归且输入 224×224，未做端到端微调，mAP 距锚值 23.2pp 且未达失败条件阈值 55%，故取该带中低分 8 分。附加分析（mCF1/mEF1/OF1、频繁标签基线 mAP=0.12729、per-class AP）质量较高，但被大幅缺失的核心结果所限，不额外加到区间上限。结论词 contradicted 与自身 mAP 及 41.6%<55% 的失败条件一致，无矛盾扣分；未报告完整传统方法（SVM/RF）实测对比，但报告了频繁标签平凡基线，故不重复扣分。 |
| B 证据真实性/实际复现 | 36.0 | 40 | 磁盘证据扫描表明：metrics.json 存在、evidence_table.csv 存在、可运行代码存在，且日志、report.md、evidence_table.csv、metrics.json 四方数值严格一致（整体 mAP=0.415808、mCF1=0.40364、mEF1=0.568868、OF1=0.58217、频繁标签基线 mAP=0.12729、label=0 AP=0.459555、label=13 AP=0.011252、label=35 AP=0.452506），划分使用冻结 multiscene_split_50.csv（train 7000/test 7000，seed 20260813）。符合『有证据文件且数值与报告严格一致、可核对』档位，落入 B∈[30,40]。因裁判未在本环境独立重跑重算（独立重算未执行），不授予该档顶端，给 36 分。 |

## A 核心结果达成度（8.0/60）

agent 实测测试整体 mAP=0.415808（41.6%），论文锚 64.8%，绝对差 d=23.2pp。逐一带判定：d≤4（mAP≥60.8%）→不满足；4<d≤10（mAP∈[54.8,60.8)）→不满足；10<d≤20→不满足；d>20→命中，按 rubric 该带 0–11 分。因 mAP 有落盘 metrics.json/evidence_table.csv 实测支撑（非仅散文），故可在该带内给分；但方法为冻结 ResNet50 特征+逻辑回归且输入 224×224，未做端到端微调，mAP 距锚值 23.2pp 且未达失败条件阈值 55%，故取该带中低分 8 分。附加分析（mCF1/mEF1/OF1、频繁标签基线 mAP=0.12729、per-class AP）质量较高，但被大幅缺失的核心结果所限，不额外加到区间上限。结论词 contradicted 与自身 mAP 及 41.6%<55% 的失败条件一致，无矛盾扣分；未报告完整传统方法（SVM/RF）实测对比，但报告了频繁标签平凡基线，故不重复扣分。

## B 证据真实性/实际复现（36.0/40）

磁盘证据扫描表明：metrics.json 存在、evidence_table.csv 存在、可运行代码存在，且日志、report.md、evidence_table.csv、metrics.json 四方数值严格一致（整体 mAP=0.415808、mCF1=0.40364、mEF1=0.568868、OF1=0.58217、频繁标签基线 mAP=0.12729、label=0 AP=0.459555、label=13 AP=0.011252、label=35 AP=0.452506），划分使用冻结 multiscene_split_50.csv（train 7000/test 7000，seed 20260813）。符合『有证据文件且数值与报告严格一致、可核对』档位，落入 B∈[30,40]。因裁判未在本环境独立重跑重算（独立重算未执行），不授予该档顶端，给 36 分。

## 证据与重算说明

独立重算未执行。关键实测数（全部来自落盘 metrics.json/evidence_table.csv 与运行日志）：整体 mAP=0.415808、mCF1=0.40364、mEF1=0.568868、OF1=0.58217、frequent_label_baseline_mAP=0.12729；抽样类别 AP：label=0(apron)=0.459555、label=13(oil field)=0.011252、label=35(sea)=0.452506；划分核验：multi_run.log 显示 split train=7000/test=7000、merged rows=14000，与冻结 50/50 划分一致。未发现抄论文数字或测试段泄漏迹象（训练计数、测试计数、AP 均为独立计算值）。

## 结论

- **科学结论**: `contradicted`
- 亮点: 提交物规范完整（report+evidence_table+metrics.json+可重跑代码），证据文件与报告数值严格一致，防泄漏声明明确（统计/阈值仅从训练集估计），并提供了频繁标签平凡基线（mAP=12.7%）与长尾类别、多场景共现分析，工程上还有断点续传。
- 不足: 核心复现策略偏弱——仅用冻结 ImageNet ResNet50 特征+per-class 逻辑回归，输入降为 224×224，未做端到端微调，导致 mAP 41.6% 远低于论文锚 64.8%（差 23.2pp），未能验证『深度模型可达 ~65% mAP』的关键 claim，科学结论只能判 contradicted。