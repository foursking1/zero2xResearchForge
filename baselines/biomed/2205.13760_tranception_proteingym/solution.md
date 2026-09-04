# solution.md — 方法说明与结果速览

## 任务
验证 ProteinGym / Tranception（Notin et al., ICML 2022, arXiv:2205.13760）主论断：
**蛋白质语言模型零样本突变效应预测有效，且在多数 assay 上优于简单 site-independent 基线**。

## 方法
- **数据**：冻结的 6 个替换 DMS assay（71,625 变异；`mutant,DMS_score,DMS_score_bin`），一并使用 `ProteinGym_reference_file_substitutions.csv` 的 UniProt/物种/MSA 深度元数据。位置映射核验 100% 一致；方向「更高 = 更高适应度」核验通过。
- **评分器**（全部零样本，无训练）：
  1. **LM（主）**：ESM-2 650M（+8M 容量消融）掩码边际（masked-marginal）log-odds：
     `score = Σ_i [log P(mut_i) − log P(wt_i)]`，softmax 在 20 AA 上重整化，一次前向/位置建表（`01_score_lm.py`）。
  2. **基线**：BLOSUM62 site-independent 替换分（主基线）、BLOSUM62 按位置 z 标准化、固定种子 null（下限）。
  3. **GFP 校验**：joint masked-marginal（多点同时掩码，46,942 mask，650M）。
- **评估**：每个 assay 内 Spearman ρ（scipy）。

## 结果
| | ESM-2 650M | ESM-2 8M | BLOSUM62 | null |
|---|---|---|---|---|
| 平均 ρ（6 assay） | **0.463** | 0.227 | 0.245 | −0.001 |
| 胜出 assay 数 vs 基线 | **5/6** | 2/6 | — | — |

逐 assay（LM vs BLOSUM62）：GAL4 0.667 vs 0.145 | BLAT 0.528 vs 0.306 | BRCA1 0.520 vs 0.270 |
ADRB2 0.492 vs 0.191 | PTEN 0.465 vs 0.217 | **GFP 0.108 vs 0.339（唯一反例，多为多点 + 极浅 MSA）**。

## 结论
`supported`：零样本 LM 预测有效，且在多数 assay 上系统性优于简单基线（平均 Δρ=+0.219），与论文方向一致。

## 产物
- `code/`（00 数据核验 → 01/02 打分 → 03 Spearman/summary → 04 图）
- `results/evidence_table.csv`、`results/metrics.json`、`results/lm_scores/**`、`results/baseline_scores/**`、`results/figures/*.png`
- `claim.md`（结论+关键数字）、`report.md`（方法/结果/局限完整版）、`README.md`（复现说明）