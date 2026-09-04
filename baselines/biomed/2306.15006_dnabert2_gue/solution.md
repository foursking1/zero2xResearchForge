# solution.md — DNABERT-2 GUE 冻结任务复现（方法说明与结果）

> task 2306.15006_dnabert2_gue · L1 · 验证「DNA 基础模型（BPE Transformer）优于 k-mer 浅层模型，且与论文性能量级一致」
> 完整报告见 `report.md`；判定见 `claim.md`；关键数据见 `results/`。

## 1. 复现目标
论文（DNABERT-2, ICLR 2024）主论断：基因组基础模型（BPE tokenizer + Transformer）在 GUE 多物种基因组序列分类下优于传统 k-mer 编码模型；117M 的 DNABERT-2 接近 300B Nucleotide Transformer（GUE 平均 66.80 vs 66.93）。
本任务冻结 4 个 GUE 任务：EMP_H3（表观遗传标记）、mouse_0（小鼠 TF 结合）、prom_300_all（启动子检测）、prom_core_all（核心启动子检测），用官方 train/val/test 划分验证三类问题：数据统计、两类模型对比、主论断。

## 2. 冻结数据（只使用官方冻结 gz，SHA-256 已核对）
| 数据集 | train/val/test | 正类比例 | 序列长度(bp) |
|---|---|---|---|
| EMP_H3 | 11971/1497/1497 | ≈0.51/0.51/0.50 | 500 |
| mouse_0 | 6478/810/810 | ≈0.50/0.49/0.50 | 101 |
| prom_300_all | 47356/5920/5920 | ≈0.50/0.50/0.50 | 300 |
| prom_core_all | 47356/5920/5920 | ≈0.50/0.50/0.50 | 70 |

- gzip CSV，列 `sequence,label`（{0,1}），解析脚本 `code/data_utils.py`；逐文件 SHA-256 与 `data/source_manifest.json` 一致。

## 3. 方法（两类模型，同协议：官方划分、同指标、固定种子 42）

### 3.1 基因组基础模型（BPE Transformer）
- `zhihan1996/DNABERT-2-117M`（HuggingFace，BPE tokenizer，trust_remote_code；权重为预训练，非数据，离线缓存可用）。
- 适配器：LoRA（r=16, α=32, dropout 0.05）挂在注意力 `Wqkv`、MLP `gated_layers`、`wo`；分类头新初始化；骨干冻结。可训练参数 ≈ 2.66M（约占 117M 参数量的 2.3%，骨干冻结）。
- 训练：交叉熵、AdamW (lr=2e-4)、linear schedule + warmup(6%)、batch=16、梯度裁剪 1.0、注意力 dropout 0.15（强制 PyTorch 注意力路径，规避 triton 缺陷）、验证集早停（patience=2，主指标如下）。
- 主指标口径（论文口径）：EMP_H3/mouse_0 → MCC；promoter → macro-F1。同时报 acc/f1/mcc。
- 冻结特征补充法：Frozen trunk `last_hidden[:,0]` + L2 逻辑回归头（`code/run_pretrained_probe.py`），确定性、CPU 可复跑（GPU 数分钟、CPU 较慢）。

### 3.2 k-mer / 浅层基线
- 4-mer 计数（BM 精确计数，固定词表，训练集上下 3 次出现过滤）+ 行归一化 + StandardScaler。
- 分类器：Logistic Regression（lbfgs, C=1.0, 2000 iters）为主，Random Forest（300 树）为稳健性参考。
- 同协议：同一冻结 train 训练，test 评估；不触碰 val。

## 4. 结果（全部实测）

| 任务 | 指标 | kmer4+LR | kmer4+RF | DNABERT-2+LoRA | DNABERT-2 冻结特征+LR | LoRA−LR |
|---|---|---|---|---|---|---|
| EMP_H3 | MCC | 0.4952 | 0.5000 | 0.7620 | 0.6420 | +0.267 |
| mouse_0 | MCC | 0.4520 | 0.4422 | 0.5237 | 0.1951 | +0.072 |
| prom_300_all | F1 | 0.8699 | 0.8686 | 0.9312 | 0.8735 | +0.061 |
| prom_core_all | F1 | 0.7894 | 0.7832 | 0.8331 | 0.7711 | +0.044 |

- 测速与算力：训练在 RTX 4080（16GB，LoRA 占用 <3GB），全程 CPU 亦可行（提供 `--device` 与 `--max_train`）。
- 结果文件：`results/baseline_kmer.json`、`results/baseline_rf.json`、`results/finetune/*_full_metrics.json`、`results/prmtprobe/*_probe_metrics.json`、`results/evidence_table.csv`、`results/metrics.json`。

## 5. 结论（四档）
- **`supported`**：DNABERT-2 基础模型在 4/4 冻结任务上 ≥ k-mer 基线；promoter F1 量级与论文一致（prom_300_all ≈ 0.9312，prom_core_all ≈ 0.8331，论文参考 PD 84.63/CPD 72.96）。
- 论文 GUE 平均 66.80（28 数据集，混合指标）无法在冻结 4 任务上直接复算，仅作量级对照。

## 6. 可复现
```
# 1) 数据解析与统计
python3 code/data_utils.py                      # 打印各 split 统计并核对 SHA-256
# 2) 浅层基线
python3 code/run_baseline.py --k 4 --model lr --out results/baseline_kmer.json
python3 code/run_baseline.py --k 4 --model rf --out results/baseline_rf.json
# 3) 基础模型微调（GPU 或 CPU；CPU 建议 --max_train 4000 控制时长）
python3 code/run_finetune_dnabert2.py --dataset prom_300_all --device cuda \
    --max_length 96 --epochs 6 --patience 2 --batch_size 16 --lr 2e-4 \
    --out results/finetune --run_tag full
# 4) 冻结特征探针（CPU 友好，确定性）
python3 code/run_pretrained_probe.py --dataset prom_300_all --device cpu --max_length 96 \
    --batch_size 64 --out results/prmtprobe
# 5) 汇总
python3 code/aggregate_results.py
```
（`--max_length` 为逐任务 BPE 上限：EMP 128 / mouse 64 / prom_300 96 / prom_core 32）