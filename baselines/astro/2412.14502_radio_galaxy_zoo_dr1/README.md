# RGZ DR1 验证产物 — README

验证论文 *Radio Galaxy Zoo Data Release 1* (Wong+ 2024, arXiv:2412.14502) 的 L1 关键声称。
冻结数据位于 `F:\dataset\astro\2412.14502_radio_galaxy_zoo_dr1\`（Linux 下
`/mnt/f/dataset/astro/2412.14502_radio_galaxy_zoo_dr1/`；4 个 CSV 的 SHA-256 已校验一致）。

## 内容

- `solution.md` — 方法说明与结果（简明版）
- `report.md`（= REPORT.md，NTFS 大小写不敏感）— 完整报告与方法/结果/差异归因/局限
- `code/` — 全部可运行代码
- `results/` — `metrics.json`（5 问数值）、`evidence_table.csv`（100,185 逐源行 + 汇总行）、
  `probe_numbers.json`、`summary_table.csv`、`cl_distribution.csv`、`nvotes_distribution.csv`、
  `files_verified.csv`、`robustness_checks.json`
- `evidence/` — 图：`cl_distribution.png`、`multicomponent_comparison.png`

## 运行（Python ≥3.10，只需 pandas/numpy/matplotlib）

```bash
cd agent_solution
python3 code/run_analysis.py             # 从冻结 CSV 重算全部指标并生成结果
python3 code/reproduce_three_numbers.py  # 裁判抽查 3 数（99,602 / 99,146 / 0.65 / 行级 16,531）
python3 code/__verify__.py               # 全量交叉复核（重算 vs 存盘产物）→ ALL CHECKS PASSED
python3 code/robustness_checks.py --out-dir results
```

数据目录可用 `--data-dir <dir>` 或环境变量 `RGZ_DATA_DIR` 覆盖。

## 关键数字（实测）

- 行数 99,602 + 583 = 100,185；唯一源 99,146 + 583；重复源 414 / 多余行 456。
- CL：min 0.65 / Q1 0.92 / median 1.0 / mean 0.9416 / CL<1 占 30.1%，全部 ≥0.65。
- 多分量：行级 N_comp>1 = 16,531；唯一源级 16,334（vs 论文 16,354）；N_peaks>1 = 34,741。
- ATLAS：583 行，N_comp>1 = 1。
- 四档判定：**supported**。