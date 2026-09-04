# 科研任务：DNABERT-2「基因组基础模型效率与性能」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2306.15006_dnabert2_gue`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Zhou et al., "DNABERT-2: Efficient Foundation Model and Benchmark for Multi-Species Genomes", ICLR 2024（arXiv:2306.15006）
- 领域：biomed / 基因组学 / DNA 语言模型

## 问题（可证伪）

DNABERT-2 论文提出 GUE（Genome Understanding Evaluation）基准（36 数据集 / 9 类基因组任务）并论证：**DNA 基础模型（Transformer，BPE tokenizer）在基因组序列分类任务上优于传统 k-mer 编码模型（DNABERT），且 DNABERT-2（117M 参数）能以 21× 更小规模达到与超大模型（Nucleotide Transformer 300B 参数）相当的性能（GUE 平均 66.80 vs 66.93）**；在 GUE 训练集上额外预训练（DNABERT-2♦）可进一步提升到 67.77。

请基于冻结数据回答：

1. **数据与任务**：解析冻结的 4 个 GUE 任务（EMP_H3 表观遗传标记预测、mouse_0 小鼠转录因子结合、prom_300_all 启动子检测、prom_core_all 核心启动子检测；各含 train/val/test 的 DNA 序列 + 二分类标签），统计类别数与序列长度。
2. **两类模型对比**：实现并训练
   - **基因组基础模型**（推荐：HuggingFace DNABERT-2 或 Nucleotide Transformer，LoRA/全参数微调；或自训小型 BPE Transformer——若资源受限）；
   - **k-mer/浅层基线**（如 k-mer 频率 + RF/逻辑回归，或 1D CNN on one-hot/k-mer）。
   在官方 train/val/test 划分上评估（指标：promoter 任务用 F1，其余用 MCC，按论文口径）。
3. **验证论断**：基础模型是否在 4 个任务上 ≥ 浅层基线？性能是否与论文量级一致（DNABERT-2 平均 GUE 66.80；promoter F1 ≈ 84-85、core promoter ≈ 73）？给出对照表与四档结论。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件（gzip CSV，列 `sequence,label`）：EMP_H3、mouse_0、prom_300_all、prom_core_all 各 train/val/test。
- 来源：DNABERT-2 官方（GitHub MAGICS-LAB/DNABERT_2，GUE 数据）；许可：DNABERT-2 代码 MIT、GUE 数据基于公开基因组数据（HG38、ENCODE 等）整理，用于学术研究评测。
- 规模：~8.4MB；序列长度 70-500bp；微调基础模型需 GPU（若受限可用小模型 DNABERT-2-mini 或子集，固定种子并声明）。

## 方向提示（协议建议）

1. **读取**：`gzip.open` + csv；序列为 A/C/G/T 字符。
2. **基础模型**：`pip install transformers`，`zhihan1996/DNABERT-2-117M`（BPE tokenizer）；分类头 + LoRA 或全参微调，epochs 3-10，early stopping 按 val 指标。DNABERT-2 需 `trust_remote_code`。
3. **基线**：k-mer（3/4/5-mer 计数 + 逻辑回归/RF）或 one-hot 1D CNN；与基础模型同数据同指标。
4. **指标**：prom_300_all/prom_core_all 用 macro F1（论文口径）；EMP_H3/mouse_0 用 MCC（论文口径；可同时报 ACC）。
5. **对照**：论文 Table 3（平均 GUE：DNABERT-2 66.80、DNABERT-2♦ 67.77、Nucleotide Transformer 66.93）与 Table 4 任务均值（PD 84.63、CPD 72.96、EMP 49.54、TF-M 57.73，均为 DNABERT 3-mer 的参考值）——只能对照讨论，禁止抄为实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成训练与评估。
3. **`results/evidence_table.csv`**：至少含列 `dataset,method,metric,value`（每任务 × 每方法一行；metric 为 f1/mcc/acc）。
4. **`results/metrics.json`**：样本统计、各方法指标、基础模型 vs 基线差值、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（子集/模型/微调差异 vs 论文、指标口径）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用 GUE 在线下载的其他版本或合成 DNA。
- 预训练模型权重不算「数据」，允许下载使用；但评估只能用冻结数据。
- 禁止手工抄写论文数字作为「实测结果」。
- 测试集禁止参与训练/调参。
