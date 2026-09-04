# 论文锚：2306.15006_dnabert2_gue

> 用途：LLM judge 判分基准（私有）。数值来自 arXiv:2306.15006v2（ICLR 2024），禁止臆造。

## 锚清单

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | DNABERT-2 规模 | 117M 参数（相对 FLOPs 1.00）；Nucleotide Transformer 300B（21× 更大） | Table 3 | 参数量 | 参照锚 |
| 2 | GUE 平均分 | DNABERT-2 66.80（top-2 8∥4）；DNABERT-2♦ 67.77（11∥10）；Nucleotide Transformer 66.93（7∥9） | Table 3 | 28 数据集平均（不同任务指标不同） | 参照锚（±5 判同量级） |
| 3 | 主论断 | DNABERT-2 以 21× 更小规模达到与 SOTA（NT）相当性能；BPE 优于 k-mer；GUE 上额外预训练提升 | Abstract / §5.3 | 方向性 | 方向 |
| 4 | 任务级参考（DNABERT 3-mer） | EMP 49.54、TF-M 57.73、PD 84.63、CPD 72.96 | Table 4 | 各任务平均 | 参照锚（本卡冻结 4 任务：EMP_H3、mouse_0、prom_300_all、prom_core_all） |
| 5 | GUE 组成 | 36 数据集 / 9 任务 / 4 物种；序列长度 70-1000（GUE）、5000-10000（GUE+） | §4.2 | 基准组成 | 参照锚 |

## 备注
- 主论断：基因组基础模型（BPE Transformer）在 GUE 上优于 k-mer 模型，且小型高效模型与超大模型性能相当。
- 判分提示：以「基础模型 ≥ k-mer 基线（多数冻结任务）+ 性能与论文量级一致」为主判据；绝对数值受模型/微调影响，不强求。
