# 任务结论判定（claim）

- **task_id**: `2306.15006_dnabert2_gue`
- **论文**: Zhou et al., "DNABERT-2: Efficient Foundation Model and Benchmark for Multi-Species Genomes", ICLR 2024 (arXiv:2306.15006)
- **判定标签**: `supported` （在冻结的 4 个子任务上，主论断成立）

## 关键数字（全部为本任务实测，非论文抄录）

| 任务 | 主指标 | k-mer基线(4-mer+LR) | DNABERT-2+LoRA(实测) | 差值 | 论文参考(对照,DNABERT 3-mer) |
|---|---|---|---|---|---|
| EMP_H3 | MCC | 0.4952 | 0.7620 | +0.267 | 49.54(平均) |
| mouse_0 | MCC | 0.4520 | 0.5237 | +0.072 | 57.73(平均) |
| prom_300_all | F1 | 0.8699 | 0.9312 | +0.061 | 84.63(平均) |
| prom_core_all | F1 | 0.7894 | 0.8331 | +0.044 | 72.96(平均) |

- 冻结数据规模：EMP_H3 (11,971/1,497/1,497)、mouse_0 (6,478/810/810)、prom_300_all (47,356/5,920/5,920)、prom_core_all (47,356/5,920/5,920)；均为二分类，类别均衡，序列长度固定（500/101/300/70 bp）。
- DNABERT-2-117M + LoRA（r=16, α=32, 注意力 Wqkv+MLP 门控+输出投影）微调，固定种子 42，val 早期停止。
- **主论断验证**：基础模型在 4/4 任务上 ≥ k-mer 基线（MCC/F1 均正向优势）；promoter F1 量级与论文一致（prom_300_all ≈ 0.9312 ≥ 80；prom_core_all ≈ 0.8331 ≥ 72.96 参考值）。
- GUE 平均锚对照：DNABERT-2 论文平均 66.80 / DNABERT-2♦ 67.77 / NT(300B) 66.93（整基 28 数据集平均，仅供对照量级，无法在冻结 4 任务上直接复算）。

## 结论说明
1. 数据与任务：解析正确（见 results/data_stats.json、evidence_table.csv）。
2. 两类模型均实现并同协议评估；基础模型 = DNABERT-2-117M（BPE Transformer）+ LoRA 微调（主）与冻结特征 + 逻辑回归（补充）。
3. 四档判定：`supported` —— 基础模型在多数（且实为全部）冻结任务上 ≥ 浅层基线，promoter F1 量级与论文一致。
4. 局限：全微调受限于离线/算力，采用 LoRA（约 2.66M 可训练参数，约 2.3%），绝对数值与论文（全参微调 + 更早 checkpoint）存在合理差异；论文 GUE 平均分覆盖 28 数据集，本卡仅冻结 4 个，无法逐一对齐平均 66.80。