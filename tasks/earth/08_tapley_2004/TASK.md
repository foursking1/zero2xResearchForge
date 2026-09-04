# TASK: GRACE Measurements of Mass Variability in the Earth System

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- **论文 ID**: `08_tapley_2004`
- **出处**: Science 305, 503–505 (23 July 2004); DOI: 10.1126/science.1099192
- **层级**: L2（RCBench 对齐端到端科研再发现；轻量协议 v2.0）
- **数据**: 已就绪（F），见 `data/DATA_MANIFEST.md`

## 1. 科学问题（可证伪）

**问题 1（C01）**：Annual variation in geoid height from GRACE compared with GLDAS hydrology model using 400 km Gaussian smoothing and excluding degree-2 coefficients, with GRACE cosine ranging -7.2 to +3.0 mm (RMS 0.9 mm), GRACE sine ranging -6.4 to +8.9 mm (RMS 1.3 mm), GLDAS cosine ranging -2.3 to +3.2 mm (RMS 0.4 mm), and GLDAS sine ranging -4.0 to +6.7 mm (RMS 1.0 mm).

**问题 2（C02）**：Month-to-month geoid variability for equatorial South America during 2003 shows an Amazon basin local maximum of +14.0 mm in April 2003 and a local minimum of -7.7 mm in October 2003 relative to the 14-month mean, with clear separation between Amazon and Orinoco watersheds.

**问题 3（C03）**：Observed geoid height differences for April 2002 (1000 km smoothing) and April 2003 (600 km smoothing) relative to the mean geoid show spatial patterns and amplitudes distinctly above random error realizations from calibrated covariance at matching smoothing levels.

**问题 4（C04）**：GRACE monthly gravity field estimates have geoid height accuracy of 2 to 3 mm at spatial resolution as small as 400 km; 2002 solutions resolve ~1000 km scales; 2003 solutions resolve 400-600 km scales.

请针对上述 claim(s) 设计并执行分析：使用提供的冻结数据重现论文关键结果，判断 claim 是否成立（supported / partially_supported / contradicted / inconclusive），并给出证据。

## 2. 输入与数据

- 数据位置：`$PAPER_BENCH_DATA_DIR`（原位读取，**不要复制**）。
- 内容：复现工作区含 `code/`（参考复现脚本）、`data/`（冻结数据）、`artifacts/`、`EVIDENCE_REPORT.md`（**仅裁判参考，不得直接作为你的提交内容**）。
- 论文 PDF：数据目录内（arxiv_<id>.pdf 或 <id>.pdf）。

## 3. 输出要求

提交物（写入成员提交目录 `submissions/<domain>/<card_id>/`）：

1. `solution.md` — 方法（步骤、口径、参数）、结果（关键数值表）、结论（claim 判定 + 依据）。
2. `code/` — 完整可运行代码（裁判会实跑抽查）。
3. `results/evidence_table.csv` — 证据表（指标列：指标名、数值、口径）。
4. `results/metrics.json` — 关键指标机器可读（键名自定但需与 evidence 表一致）。

## 4. 铁律

- **只用冻结数据**，不得从互联网下载或补充数据（除非 TASK 明确允许）。
- **禁止编造数字**：所有指标必须实际运行得到；引用论文数值须明确标注"论文引用"。
- 结论必须有数据支撑；不确定就写 inconclusive。
