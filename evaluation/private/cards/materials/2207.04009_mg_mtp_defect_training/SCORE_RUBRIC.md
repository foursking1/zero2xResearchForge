# 裁判 Rubric：2207.04009_mg_mtp_defect_training（L1，总分 100）

## 判分模型
- Claude / GLM 等 LLM 裁判均可；证据重算由裁判运行提交代码完成。
- 判分输入：`claim.md`、`code/`、`results/`、`report.md` + 冻结数据（`F:\dataset\materials\2207.04009_mg_mtp_defect_training\`）。

## A. 核心结果达成度（60 分）

| 键 | 论文值（出处） | 判分规则 |
|---|---|---|
| A1 数据与协议（20） | Edmond 7 文件；Everything/Everything±Shear 两套；job/subjob 类别可统计 | 数据统计正确（构型数/类别）+ 协议说明 → 满分；统计错误或未声明 → 0-10 |
| A2 参考数据质量（20） | DFT 收敛：能量 0.6 meV/atom（均值）/6.4 meV/atom（最大）；PBE/550 eV | 从冻结数据抽查收敛参数或如实报告无法复算 → 10-20；未涉及 → 0-8 |
| A3 主论断验证（20） | 训练集无缺陷结构而势可迁移至缺陷；MTP RMSE 优于经典势 1–2 个数量级 | 方向一致（拟合或引用 frozen 数据佐证）+ 讨论 → 满分；部分成立 → 10-14；相反且有讨论 → 5-10 |

## B. 证据真实性（25 分）
- 必须含 `code/` + `results/`；缺失 → B=0。
- 抽查字段 1：`fit_packed.csv` 行数（47）与 `structures_packed.csv` 行数（10）；tar.gz members 数（fit 280 / structures 11）。
- 抽查字段 2：从 tar.gz 内抽查 ≥1 个构型的 DFT 能量/力可被解析（或如实说明 AiiDA 解析限制），并与索引行对应。
- 可重算一致 → 25；1 项不一致 → 12-20；无代码/抄数 → 0-10。

## C. 方法与报告（15 分）
- C1（5）：方法合理（解析/统计/拟合说明）；C2（5）：避免误报（区分可复算与不可复算部分）；C3（5）：报告含方法/结果/局限/结论标签。
