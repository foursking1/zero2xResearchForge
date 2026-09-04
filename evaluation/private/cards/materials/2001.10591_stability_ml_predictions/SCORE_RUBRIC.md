# 裁判 Rubric：2001.10591_stability_ml_predictions（L1，总分 100）

## 判分模型
- Claude / GLM 等 LLM 裁判均可；证据重算由裁判运行提交代码完成。
- 判分输入：`claim.md`、`code/`、`results/`、`report.md` + 冻结数据（`F:\dataset\materials\2001.10591_stability_ml_predictions\`）。

## A. 核心结果达成度（60 分）

| 键 | 论文值（出处） | 判分规则 |
|---|---|---|
| A1 数据与协议（20） | 85,014 成分；train 59,509 / val 12,752 / test 12,753；稳定判据 ΔHd≤0 | 数据统计正确 + 划分/协议合理 → 满分；统计错误或未声明协议 → 0-10 |
| A2 双方法对照（20） | ΔHf 回归模型 vs 稳定性预测（hull 重建或 ΔHd 回归/分类），同协议 | 两类方法均实现并出对照表 → 满分；只有一类 → 0-8 |
| A3 主论断验证（20） | Ef MAE 低（≤~0.2 eV/atom 量级）而稳定性分类 acc<80% 或 F1<0.75 或 FPR>0.15；冻结参考 6 模型 ΔHd MAE 0.069–0.101 eV/atom | 方向一致 + 锚区间复现 → 满分；部分成立 → 10-14；相反且有讨论 → 5-10 |

## B. 证据真实性（25 分）
- 必须含 `code/` + `results/`；缺失 → B=0。
- 抽查字段 1：冻结 CSV 行数（脚本重算：Ef/Ed train 59,509、val 12,752、test 12,753）。
- 抽查字段 2：`results/evidence_table.csv` 中 ΔHd MAE（如 Roost ≈0.069 eV/atom，用 `Ed_allMP_Roost_ml_results.json` + `CritExam__Ed_test.csv` 重算核验，容差 ±0.01 eV/atom）。
- 可重算一致 → 25；1 项不一致（超容差）→ 12-20；无代码/抄数 → 0-10。

## C. 方法与报告（15 分）
- C1（5）：方法合理（特征/模型/hull 或分类协议说明）；C2（5）：防泄漏（划分固定、超参只由验证集选择）；C3（5）：报告含方法/结果/局限/结论标签。
