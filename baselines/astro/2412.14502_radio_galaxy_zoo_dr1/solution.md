# RGZ DR1 关键声称验证 — 方法说明与结果 (solution.md)

**任务**：验证 *Wong+ 2024 (arXiv:2412.14502)* 关于 Radio Galaxy Zoo DR1 的 L1 关键声称。所有数字均从冻结官方目录（Zenodo 10.5281/zenodo.10656393，4 个 CSV，SHA-256 已校验）由提交代码重算。

## 快速结论：四档判定 = `supported`（支持）

## 关键结果表

| 声称 | 论文 | 实测（冻结数据） | 判定 |
|---|---|---|---|
| FIRST 分类条目 | 99,602 | **99,602** | ✓ 一致 |
| ATLAS 分类条目 | 583 | **583** | ✓ 一致 |
| 分类总数 | 100,185 | **100,185** | ✓ 一致 |
| FIRST 唯一源 | 99,146 | **99,146**（重复源 414，多余行 456） | ✓ 一致 |
| consensus ≥ 0.65 | 全部 | min **0.65**，全部 100,185 行 ≥0.65，0 行低于 | ✓ 验证 |
| CL 分布 | — | Q1 0.92 / median **1.0** / mean **0.9416** / CL<1 占 **30.1%** | ✓ |
| 平均 reliability | 0.83 | **不可从本包重算**（需论文 §3.3.1 专家标定子集；CSV 无 reliability 列） | 如实说明 |
| FIRST 多分量 (§5.1) | 16,354 | 行级 **16,531** / 唯一源级 **16,334**（~16.5%） | Δ=+177 / Δ=−20（版本+口径差） |
| ATLAS 多分量 | 1 | **1** | ✓ 一致 |

> 唯一源级 16,334 与论文 16,354 的 20 个源之差，集中在 **65 个重复 RGZID 在同一源多条行上 `N_comp` 不一致**（例如 `RGZ_J001419.7+085402` 两行 CL=1.0/N_comp=1 与 CL=0.88/N_comp=2）；不同去重顺序下唯一源级在 16,315–16,349 之间。归因：Zenodo v1 目录与论文内部发布版本的微小版本差 + 口径定义差，非核心声称矛盾。

## 方法与可复现性

- 口径：`pandas.read_csv` 直读；唯一源 = `drop_duplicates(subset="RGZID", keep="first")`；多分量两口径（行级 / 唯一源级 `N_comp>1`）+ `N_peaks>1`。
- 代码（`code/`）+ 证据表（`results/evidence_table.csv`，100,185 逐源行 + 17 条汇总行）+ `results/metrics.json`（全部 5 问数值）+ `results/probe_numbers.json` + `results/files_verified.csv`。

```bash
python3 code/run_analysis.py            # 生成全部结果
python3 code/reproduce_three_numbers.py # 裁判抽查：99,602 / 99,146 / 0.65 / 16,531（PASS）
python3 code/__verify__.py              # 全量复核：从原始 CSV 重算并核对所有产物（ALL CHECKS PASSED）
```

数据目录解析顺序：`--data-dir` 参数 → `$RGZ_DATA_DIR` → 默认 `/mnt/f/dataset/astro/2412.14502_radio_galaxy_zoo_dr1`。

## 局限
- 冻结数据为 Zenodo v1 正式发布版，与论文内部发布版存在微小版本差（集中体现于 65 个重复源）。
- reliability 0.83 需要未随包发布的专家标定数据，不在可验证范围。
- 详细分析见 `report.md`（= REPORT.md，报告正文）。