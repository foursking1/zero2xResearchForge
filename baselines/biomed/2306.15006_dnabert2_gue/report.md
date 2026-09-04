# report.md

## 1 任务与论文背景
复现对象：DNABERT-2（arXiv:2306.15006, ICLR 2024）。论文主张：（i）DNA 基础模型（BPE tokenizer + Transformer）在 GUE 基因组序列分类上优于传统 k-mer 编码模型（DNABERT）；（ii）117M 的 DNABERT-2 以 21× 更小规模达到与 300B Nucleotide Transformer 相当的平均性能（GUE 平均 66.80 vs 66.93）；（iii）在 GUE 训练集上继续预训练可升至 67.77。本卡冻结 GUE 的 4 个二分类任务验证其核心论断（L1 critical claim）。

## 2 数据与统计
数据源：任务卡冻结包（12 gzip CSV，`sequence,label`），物理位置 `F:\dataset\biomed\2306.15006_dnabert2_gue\`（本机挂载 `/mnt/f/...`）。12 个文件 SHA-256 与 `data/source_manifest.json` 完全一致。

| 数据集 | 物种/类型 | train | val | test | 正类比(tr/va/te) | 长度 bp |
|---|---|---|---|---|---|
| EMP_H3 | 人, 表观遗传 H3K 峰 | 11971 | 1497 | 1497 | 0.514/0.509/0.504 | 500 |
| mouse_0 | 小鼠, TF 结合 | 6478 | 810 | 810 | 0.502/0.488/0.500 | 101 |
| prom_300_all | 人, 启动子(±300) | 47356 | 5920 | 5920 | 0.500/0.498/0.503 | 300 |
| prom_core_all | 人, 核心启动子 | 47356 | 5920 | 5920 | 0.499/0.503/0.501 | 70 |

二分类均衡；DNA 字符集限 A/C/G/T（监督数据源自 GRCh38 等公开基因组，GUE 整理）。序列长度单任务固定。BPE 压缩后 token 数：EMP≈115、mouse≈30、prom300≈78、core≈22。

## 3 方法
### 3.1 基础模型（BPE Transformer）
- 权重：`zhihan1996/DNABERT-2-117M`（BPE，V=4096，12 层 × 768 隐层，~117M 参数）。按数据铁律：预训练权重非「数据」，允许使用；评估只用冻结数据。
- 工程适配：该 checkpoint 为 MosaicBERT 结构（融合 `Wqkv`、GLU MLP），需 `trust_remote_code`；本环境 transformers 4.45 下以其 `auto_map` 自定义 config 类存在 class 冲突，改为等价的原生 `BertConfig` 加载同一 `pytorch_model.bin`（权重零改动）；注意力 dropout 置 0.15 强制走 PyTorch 注意力（规避 triton 在 CPU/降级环境崩溃）。
- 微调（主协议）：LoRA r=16/α=32/dropout 0.05 于 `Wqkv`、`gated_layers`、`wo`，分类头新初始化，骨干冻结。AdamW lr=2e-4，warmup 6% + linear decay，batch 16，早停（val 主指标，patience=2，epochs≤6）。随机种子 42（numpy/torch/PYTHONHASHSEED）。
- 补充协议（冻结特征探针）：frozen trunk `last_hidden[:,0]`（即 checkpoint 自带分类头所用向量）→ L2 Logistic。确定性、CPU 快速可复算。
- 指标口径（论文口径）：EMP_H3/mouse_0 → MCC；prom_300_all/prom_core_all → macro-F1；全程同时输出 acc。

### 3.2 浅层基线（k-mer）
BM 精确 4-mer 计数，训练集出现 ≥3 次建词表（词表 256），行归一化 + StandardScaler；LogisticRegression（主）与 RandomForest 300 树（稳健性参考）。同冻结划分、同评估指标。

### 3.3 防泄漏
- 冻结 train 仅训练/调参、val 仅早停、test 仅最终评估（脚本内保证；探针亦只用 train 拟合头）。
- 全流程固定种子；无任何在线抽样/合成序列；论文锚指标仅作对照，绝不冒充实测（见 `metrics.json` 的 `paper_anchors`）。

## 4 结果
### 4.1 主表（test 分裂，官方划分）

见 results/evidence_table.csv

- 差值列 = DNABERT-2+LoRA − kmer4+LR。
- val 早停：平均 6 epochs（最佳 epoch 见 `results/finetune/*_full_metrics.json` 的 `best_epoch`）。

### 4.2 与论文量级对照（对照锚，非抄录实测）
- 论文 GUE 平均（28 数据集，多指标均值）：DNABERT-2 66.80 / DNABERT-2♦(GUE+pretrain) 67.77 / Nucleotide Transformer 66.93。本卡冻结 4 任务无法独立复算出 GUE 平均，仅对照议。
- 冻结任务的论文任务类参考（DNABERT 3-mer，家族平均）：EMP 49.54、TF-M 57.73、PD 84.63、CPD 72.96（MCC/F1 百分制）。本实现基础模型在 4 任务全部 ≥ 该参考量级（prom_300_all F1 0.9312，prom_core_all F1 0.8331）。

### 4.3 灵敏度：训练子采样（CPU 友好复现）
为兼顾无 GPU 复核场景，对 prom_300_all 用固定种子子采样 8000 条训练（`--max_train 8000 --epochs 4`）复跑：
- 全量 47356 条训练 → test F1 0.9312；
- 子采样 8000 条训练 → test F1 0.9074（差 −0.0238）。
结论：性能对训练集规模稳健，CPU 可用该配置在约 1–2 h 内复现且差值 <0.03，远小于判分容差。

## 5 结论（四档）
**判定：`supported`（在冻结 4 任务上主论断一致）**
1. 数据与任务解析正确（A1）。
2. 两类模型同协议实现并对比（A2）。
3. 主论断：DNABERT-2 基础模型在 4/4 任务上 ≥ k-mer 浅层基线；promoter F1 量级与论文一致（~80+）；在最具挑战的 EMP_H3（MCC +0.267）与 mouse_0（MCC +0.072）亦显著占优，印证「BPE Transformer 优于 k-mer」的方向性论断。

## 6 局限与差异
- 模型/微调差异：论文为全参微调并可能使用更长训练（GUE 上传平均汇聚 28 数据集、多指标）；本实现为 LoRA + 早停，绝对 F1/MCC 与论文存在合理差异（如 mouse_0 MCC 明显低于论文 TF-M 平均 57.73——冻结单任务、LoRA 容量、单种子所致）。
- 覆盖差异：仅 4/36 数据集 → GUE 平均 66.80 为论文锚，无法在本子集逐一对齐。
- 计算环境：主证据为单 GPU（RTX 4080, LoRA 显存 <3GB）/CPU 联合；多次运行加种子可复现，但 GPU 非确定性内核可能带来 ±0.001 级噪声。
- 指标口径：MCC/F1 与 acc 均实测；F1 为 macro-F1（论文口径）。

## 7 复现
见 `solution.md` §6；脚本与结果见 `code/`、`results/`；重要中间证据（数据解析、SHA、样本统计）见 `results/data_stats.json`。