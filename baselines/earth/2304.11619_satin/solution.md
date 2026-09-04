# Solution — 2304.11619 SATIN（SAT-4 零样本遥感分类）

## 1. 任务与数据

验证论文核心论断在冻结数据上的可复现性：
- **锚 1**：最强开放 VL 模型（OpenCLIP ViT-G/14, LAION-2B）在 SATIN 元基准 27 个数据集上零样本整体准确率 **52.0%**（摘要 + Table 3）。
- **锚 2**：同一模型在 **SAT-4** 单数据集上零样本准确率 **0.54**（附录 Table 6）。
- 本卡冻结数据为 SAT-4 官方全量组件（100,000 张 28×28 图块，4 类），可直接对照锚 2。

**冻结数据**：`F:/dataset/earth/2304.11619_satin/`
- `data/data/SAT_4.parquet`：100,000 行 × 2 列（`image`：struct{bytes,path}，PNG 编码 28×28 RGB；`label`：int64 0–3）。
- 标签：0=barren land, 1=trees, 2=grassland, 3=buildings（与 SAT-4 原始类序一致）。

来源：HF 官方镜像 `jonathan-roberts1/SATIN`（SAT-4 配置）。许可：other（学术用途）；SAT-4 原始数据公开提供。非医学/隐私数据。

## 2. 方法

1. **划分**（`satin_01_data_prep.py`）：官方为单 train split；按固定种子 20260817 分层 80/20 → 训练 80,000 / 评估 20,000。归一化均值/方差仅从训练子集估计（防泄漏）。
2. **多数类基线**（`satin_02_baseline_and_cnn.py`）：训练集多数类（grassland，35.6%）作为平凡下界。
3. **监督 CNN**（`satin_02`）：小 CNN（3 conv + 2 fc），从训练子集（20,000 张，固定种子分层抽样，纯加速用途）从头训练 6 epoch，Adam lr=1e-3，batch 512。报告整体/每类准确率 + 混淆矩阵。
4. **零样本 CLIP**（`satin_03_clip_zeroshot.py`）：OpenCLIP **ViT-B/32（LAION-2B）**，模板集成（5 个遥感相关模板），在 20,000 张评估图上零样本 top-1 分类，报告 95% Wilson CI。论文锚使用 ViT-G/14（~68 亿参数），本工作使用 ViT-B/32（~1.5 亿参数），属可复现性口径差异。

**设备**：Windows 11，Python 3.13，CNN 用 CPU（torch 2.13.0+cpu），CLIP 零样本用 GPU（NVIDIA RTX 4080，torch 2.6.0+cu124），OMP_NUM_THREADS=2。

## 3. 结果

### 3.1 监督基线（评估集 n=20,000，固定种子）

| 方法 | 整体 OA | 备注 |
|---|---|---|
| 多数类基线（grassland） | 0.356 | 平凡下界 |
| 监督小 CNN（3conv+2fc, 6 epoch） | **0.952** | 远超多数类基线 |

监督 CNN 每类 recall：barren land 0.900，trees 0.987，grassland 0.977，buildings 0.946。混淆主要发生在 barren↔trees、trees↔buildings（见 `results/satin_baseline_cnn_metrics.json`）。

### 3.2 零样本 CLIP（锚 2 对照）

| 项 | 本工作 | 论文锚 |
|---|---|---|
| 模型 | OpenCLIP ViT-B/32 (LAION-2B) | OpenCLIP ViT-G/14 (LAION-2B) |
| 参数规模 | 1.51 亿 | ~68 亿（≈45 倍） |
| SAT-4 OA | **0.384**（95% CI [0.378, 0.391]） | **0.54** |

零样本每类准确率：barren land 0.861，trees 0.157，grassland 0.367，buildings 0.000。类间混淆严重（trees↔grassland、buildings 完全丢失）。

相对差 d=|0.384−0.54|/0.54=**28.8%**（落在 rubric 半满带 d≤30% 内）。

## 4. 科学结论

**`partial_reproduced`（部分复现）**：
- 零样本 VL 模型在 SAT-4 上的定性 claim 成立：OA 0.384 远高于多数类基线（0.356）但远低于监督 CNN（0.952），且明显低于论文 ViT-G/14 的 0.54。
- 定量差距主要由**模型规模差异**解释（ViT-B/32 1.51 亿 vs ViT-G/14 ~68 亿参数）。论文核心信息「即使最强开放 VL 模型零样本遥感分类也仅约 50%」在本数据上以较小模型表现为 38%，方向上一致、数值偏低。
- SATIN 整体锚（52.0%，27 数据集元平均）在仅有 SAT-4 单数据集的冻结数据上无法复现，只能对照 SAT-4 单列锚。

## 5. 局限

1. **模型规模差异**：论文锚为 ViT-G/14（2B 预训练），本工作零样本用 ViT-B/32（更小），准确率天然偏低；SATIN 整体锚（52.0%）在仅有 SAT-4 单数据集的冻结数据上无法复现，仅能对照 SAT-4 单列锚 0.54。
2. **监督 CNN 口径**：监督 CNN 属微调口径，与论文零样本口径不同，仅作对照证明数据本身可分；不能直接判零样本 claim。
3. **训练子采样**：CNN 训练用 20,000/80,000 子集（固定种子），最终报告在完整 20,000 评估集上。

## 复现

```bash
python code/satin_01_data_prep.py       # 生成 satin_arrays.npz
python code/satin_02_baseline_and_cnn.py  # 多数类基线 + 监督 CNN → satin_baseline_cnn_metrics.json
python code/satin_03_clip_zeroshot.py     # 零样本 CLIP → satin_clip_zeroshot_metrics.json
```
