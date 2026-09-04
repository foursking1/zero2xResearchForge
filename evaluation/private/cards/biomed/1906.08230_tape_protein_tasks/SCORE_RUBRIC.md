# 裁判 Rubric：1906.08230_tape_protein_tasks（L1，总分 100）

## 判分模型
- Claude / GLM 等 LLM 裁判均可；证据重算由裁判运行提交代码完成。
- 判分输入：`claim.md`、`code/`、`results/`、`report.md` + 冻结数据（F:\dataset\biomed\1906.08230_tape_protein_tasks\）。

## A. 核心结果达成度（60 分）

| 锚 | 论文值（出处） | 判分规则 |
|---|---|---|
| A1 数据与任务（20） | Fluorescence 51,715 / Stability 68,977 条；train/test 结构与论文一致（荧光：近邻训练远邻测试） | 数据统计正确 + 任务/划分理解正确 → 满分；错误 → 0-10 |
| A2 双表示对比（20） | 预训练/可学习表示 vs one-hot 基线，同协议 | 两类均实现 → 满分；只有一类 → 0-8 |
| A3 主论断验证（20） | 预训练 ρ ≥ one-hot（Fluorescence 与 Stability） | 两任务方向一致 → 满分；仅一个任务成立 → 10-14；相反且有讨论 → 5-10 |

## B. 证据真实性（25 分）
- 必须含 `code/` + `results/`；缺失 → B=0。
- 抽查字段 1：冻结 CSV 行数与 train/test 计数（脚本重算）。
- 抽查字段 2：`results/evidence_table.csv` 中 Fluorescence 预训练表示的 ρ（运行代码重算核对）。
- 可重算一致 → 25；1 个不一致（ρ 差 >0.05）→ 12-20；无代码/抄数 → 0-10。

## C. 方法与报告（15 分）
- C1（5）方法合理（嵌入/回归头/基线说明）；C2（5）防泄漏（train/test 不混、早停只用训练内验证）；C3（5）报告含方法/结果/局限/结论标签。
