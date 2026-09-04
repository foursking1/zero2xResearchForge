# EVAL REPORT: 2604.04858v1（FairLogue 交集公平性分析工具包）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判，独立脚本重算）
- 评测时间: 2026-08-13
- 产物形态: **solution.md 缺失**（claude 输出未写入文件）；基于 results/ 全量 JSON + evidence_table.csv + metrics.json + code/ 评测

## 总分: 67 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 30 | 60 | 冻结数据为合成数据（非论文 All of Us 队列），4 claim 中 C04 supported、C02 partially_supported、C01/C03 inconclusive |
| B 证据真实性 | 25 | 25 | 独立重算全部逐位一致（模型性能 + 3 类 fairness gap + 官方管线 u-values） |
| C 方法与报告 | 12 | 15 | 方法严谨（官方 FairLogue 管线 + 双模型）；但 solution.md 缺失致报告维度扣分 |

## A 核心结果达成度（30/60）

### 关键前提：冻结数据性质

裁判独立核实：`fairselect/synthetic_glaucoma_intervention.csv`（10000 行，含 Asian 族群）、`Component3/glaucoma_synth_component3.csv`（12000 行）**均为合成数据**，而论文锚值来自 All of Us 真实队列（N=3880，DUCC 受控不可公开）。**agent 在 evidence 表中诚实标注"n/a: claim states All of Us (DUCC-controlled, not in frozen data); synthetic reproduction not directly comparable"，未编造数字硬套锚值，处理正确。**

### claim 判定

| Claim | agent 判定 | 裁判复核 | 依据 |
|---|---|---|---|
| C01 LR AUROC=0.709 / acc=0.651 | **inconclusive** | ✅ 合理 | 合成数据 fairselect 上 AUROC=0.7423、acc=0.7316，与锚差异大且数据集不可比 |
| C02 交集 fairness gaps 超单轴 | **partially_supported** | ✅ 合理 | DP=0.1628（方向对、接近 0.20）、FPR gap=0.1302（对）、TPR gap=0.0543 vs 0.33（差大）；Race 单轴 DP=0.1238 > 交集 DP 趋势未复现论文方向性 |
| C03 分组 TPR/FPR 匹配论文 | **inconclusive** | ✅ 合理 | 各交集组 TPR/FPR 与论文 Table 1 差异大（合成数据），且 n_predictors=16 vs 论文 56 |
| C04 反事实 u-values 趋零 | **supported** | ✅ 成立 | 6 个聚合指标 u-values 全 0（论文 max 0.06），aggregate stats 数量级一致 |

### A 扣分说明

- 34 条锚中可达成核对的规则有限：C04（R15-R17）实质达成，C02 部分方向性达成（DP/FPR 对、TPR 差、R06-R08 单轴对比缺失），C01/C03/C05/C09/C10 因合成数据无法对照
- C02 的"交集 gap 超过单轴 gap"论文结论（DP 0.20>0.10 等）在合成数据上**未复现**（Race 单轴 DP 0.1238 与交集 DP 0.1628 接近，TPR gap 单轴缺失）——agent 判定 partially_supported 是诚实且准确的，但方向性主张达成度有限
- agent 未对 R06-R08（交集 vs 单轴 TPR/FPR gap 对比）在 evidence 表中完整给出单轴 TPR/FPR 数据 → 部分规则无法核验

## B 证据真实性（25/25）

- **独立重算抽查 1（模型性能）**：裁判独立实现 LR（80/20 分层 split、seed=42、class_weight=balanced、threshold=0.5）于冻结 fairselect 数据 → **AUROC=0.7423、accuracy=0.7316，与 agent 逐位一致** ✅
- **独立重算抽查 2（fairness gaps）**：独立按官方口径（预测正率 max-min）重算 → 交集 **DP=0.1628 / EO-TPR=0.0543 / EO-FPR=0.1302**、单轴 **Race DP=0.1238 / Gender DP=0.0361**，各组 n/TPR/FPR（157/223/579/844）**全部逐位一致** ✅（注：裁判初稿曾误用真实标签均值得 DP=0.2602，比对官方 `_compute_group_rates` 确认官方口径为 `(yhat==1).mean()` 后修正，agent 数字正确）
- **独立重算抽查 3（u-values）**：裁判以官方 FairLogue `Model` 管线小规模重跑（R_null=20 / B=30 / LR）→ **6 个 u-values 全 0.0**，与 agent 的 R_null=100/B=200（lr）及 R_null=25/B=40（lgbm）结果**定性一致** ✅
- 代码完整可运行（run_full_analysis.py + build_evidence.py，LR/LightGBM 双变体），raw_results 三份 JSON 落盘，日志与结果一致
- 未发现抄论文数字：所有对比锚值在表中明确标注为 paper_value 列且 match 列如实标注 yes/no/n/a

## C 方法与报告（12/15）

- C1 方法合理性（5/5）：调用官方 FairLogue 管线（Component1 `evaluate_intersectional_fairness` + Component3 `Model` SR 方法），口径完整（80/20、seed 42、min_group_size=20、class balance、R_null/B 参数明确）；合成数据与论文数据不可比这一核心判断准确，无泄漏
- C2 稳健性（4/5）：LR 与 LightGBM 双模型交叉验证（u-values 一致）；但未做多 seed 敏感性（扣 1 分）
- C3 报告与边界（3/5）：**solution.md 缺失**（claude 最终报告未写入文件，同 08_tapley_2004 的产物问题）——无方法叙述、结论标签与局限说明；但 evidence_table.csv 含完整的 claim 判定/口径/note 列、metrics.json 含 claim_assessments，JSON 侧信息完整可读，故非 0 分

## 结论

- **科学结论**：C04 supported、C02 partially_supported、C01/C03 inconclusive → `partially_supported`（受合成数据限制）
- 数据真实性满分：三项独立重算（模型性能、fairness gaps、官方管线 u-values）全部逐位/定性一致
- 主要扣分在 A 达成度（合成数据无法对照论文 All of Us 锚值，且 C02 单轴 TPR/FPR 对比数据不完整）+ C 报告缺失
- 备注：solution.md 为空是执行脚本输出问题（claude 结果写入 JSON 但报告未生成），评测按现有产物进行
