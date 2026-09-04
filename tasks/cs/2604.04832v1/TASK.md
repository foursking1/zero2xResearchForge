# TASK: When One Sensor Fails: Tolerating Dysfunction in Multi-Sensor Prototypes

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- **论文 ID**: `2604.04832v1`
- **出处**: arXiv:2604.04832v1, April 2026
- **层级**: L2（RCBench 对齐端到端科研再发现；轻量协议 v2.0）
- **数据**: 已就绪（F），见 `data/DATA_MANIFEST.md`

## 1. 科学问题（可证伪）

**问题 1（C01）**：FDR-based task complexity analysis predicts paper-vs-scissors is over 10x more difficult (normalized FDR 0.073) than rock-vs-paper (0.842) and rock-vs-scissors (1.000)

**问题 2（C02）**：MLP validation oracle confirms FDR predictions: paper-vs-scissors achieves MCC of 0.872 while rock-vs-paper (0.990) and rock-vs-scissors (1.000) achieve near-perfect scores

**问题 3（C03）**：Sensor ablation audit reveals task-dependent sensor importance: Sensor 2 is highly critical for 'paper' gesture, sensors 6 and 7 are consistently redundant across all gestures

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
