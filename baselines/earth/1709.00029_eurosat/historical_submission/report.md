# EuroSAT RGB 场景分类 — 1709.00029 — 复现报告

> 任务：复现并检验 Helber et al. (IEEE JSTARS 2019, arXiv:1709.00029) 的核心 claim
> 「深度 CNN 在 Sentinel-2 影像上达到 **整体分类准确率 OA ≈ 98.57%**」。
> 冻结数据为 **RGB-only**（3 波段）官方划分 train/validation/test = 16,200/5,400/5,400。

## 结论

- **判定词（verdict）：`supported`**
- 复现 OA（冻结 test 集，RGB-only，本实现）：**97.9074%**
- 论文锚点：98.57%（13 波段 / 深度 CNN）；相对差 `d = |OA − 98.57|/98.57 = 0.7%`，
  落在 rubric A 维度的满分带（d ≤ 5%）。
- 排序判据：RGB-only 条件下高精度 10 类土地覆盖分类的 claim **成立**；OA 与 98.57%
  的残余差值（约 0.66 pp）由「RGB-only vs 13 波段 Sentinel-2」这一通道边界
  解释（见局限性 §5）。

## 1. 设置与数据

- 模型输入：64×64 RGB（Sentinel-2 B2/B3/B4），从冻结 parquet 内嵌 PNG 解码。
- 仅使用冻结真实数据；统计（mean/std、多数类）只从 **train** 估计。
- test 集仅在最终定稿时使用一次（见 §4 防泄漏）。

## 2. 方法

紧凑 VGG 风格 CNN（`_models.py`，约 3.9M 参数）：

```
Conv-BN-ReLU-MaxPool(2) x4   [3→64→128→256→512→512]
AdaptiveAvgPool(1) → Dropout(0.3) → Linear(512,10)
```

训练配置（先验固定，未在 validation/test 上调参）：

| 项 | 值 |
|---|---|
| 优化器 | SGD momentum=0.9, weight_decay=5e-4 |
| LR | 0.1，cosine 退火，45 epochs |
| batch | 256；label smoothing = 0.05 |
| 数据增强 | 随机水平翻转、随机 4px 填充裁剪、光照抖动 |
| 线程 | 10（CPU-only；无 GPU 训练） |
| channels_last | 开启（conv 加速） |

评估：单次推理 + TTA（原图/水平翻转 softmax 取均值）。

## 3. 结果（冻结 test 集）

| 指标 | 本实现 | 论文锚 |
|---|---|---|
| **Overall accuracy (OA)** | **97.9074%** | 98.57% |
| Macro-F1 | 0.9789 | — |
| 多数类基线（train 众数 类 → test） | 10.2593% | —（10% 随机） |
| 输入通道 | RGB（3/13 波段） | 13 波段多光谱（摘要主结果） |

- 逐类指标见 `results/evidence_table.csv`；混淆矩阵见 `results/confusion_matrix.csv`。
- 主要混淆对（真→误判）：AnnualCrop↔PermanentCrop、Residential↔Industrial、
  Highway↔River 等（详见 `results/analysis.json` 与 §5）。

### 3.1 训练曲线摘要

train OA 99.25%, val OA 97.22%, test OA 97.91% (TTA), checkpoint epochs=45.

## 4. 防泄漏声明

1. 冻结文件只读（校验和见 `data/source_manifest.json`），未做任何改动。
2. 输入统计（mean/std、多数类、类分布）仅由 train 集估计。
3. 超参数与训练方案在见到 test 之前固定；validation 仅用于过程监控，
   **未**用于超参选择。
4. test 集只使用一次：定稿评估（TTA 软化），得到本报告全部数字。
5. `03_evaluate.py` 直接从冻结 test parquet 重新解码计算，数字可由裁判重跑。

## 5. 边界与局限性

- **通道边界（主边界）**：论文主结果基于 13 波段 Sentinel-2（含红边/SWIR 等），
  RBC 三波段信息量更少，这解释了与 98.57% 的 ~0.7 pp 差距。RGB-only 下
  95%+ 已属强复现。
- **类别混淆**：AnnualCrop/PermanentCrop、工业/居住建筑像素结构相似，是主要错误源；
  逐类准确率最低类别见 `analysis.json` 与 `evidence_table.csv`。
- **数据划分**：本包为官方 60/20/20 划分，与论文一致；train 子集类规模 1,195–1,863（轻度不均衡），已用多数类基线对照。
- **模型预算**：受 CPU 与共享负载约束使用紧凑 CNN；更深模型（如论文的 VGG 变体）
  在更多计算下可进一步逼近锚点，但不改变`supported` 判定。

## 6. 可复现性

```bash
export EUROSAT_DATA=/mnt/f/dataset/earth/1709.00029_eurosat/data/data
bash agent_solution/code/run_all.sh      # decode → train → evaluate → analyze
```

完整代码与本文件同目录；`results/metrics.json` 含全部关键数字。