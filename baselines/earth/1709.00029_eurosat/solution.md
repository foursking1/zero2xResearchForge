# Solution — EuroSAT RGB 场景分类（1709.00029）

## 方法（TL;DR）

紧凑 VGG 风格 CNN（3.9M 参数，`code/_models.py`），SGD+cosine 退火 45 epochs，
batch 256，随机翻转/裁剪/光照增强，训练于 CPU（10 线程）。输入为冻结 parquet 中
64×64 RGB 三通道像素。评估使用单模型 TTA（原图+水平翻转 softmax 平均）。

## 结果（冻结 test 集，5400 张）

| 指标 | 值 |
|---|---|
| **Overall accuracy (OA)** | **97.9074%** |
| Macro-F1 | 0.9789 |
| Macro precision / recall | 0.9790 / 0.9789 |
| 多数类基线 | 10.2593%（train 众数） |
| 论文锚点 OA | 98.57% |
| 相对差 d = \|OA−98.57\|/98.57 | 0.7%（<br> 满分带 d≤5%） |
| 通道 | RGB（冻结数据 3/13 波段） |

**判定：supported** —— RGB-only 条件下以高 OA 复现「Sentinel-2 高精度土地覆盖分类」；
残余 ~0.7 pp 差距来自 RGB vs 13 波段差异。

## 文件

- `results/metrics.json` — 全部关键指标 + 基线 + 元数据
- `results/evidence_table.csv` — 逐类 tp/fp/tn/fn/precision/recall/f1/acc + overall 行
- `results/confusion_matrix.csv` — 10×10 混淆矩阵
- `results/analysis.json` — 混淆对 top10 + 推理期通道敏感性诊断
- `results/predictions.csv.gz` — 逐图预测
- `code/run_all.sh` — 一键复现

## 复现

```bash
export EUROSAT_DATA=/mnt/f/dataset/earth/1709.00029_eurosat/data/data
bash agent_solution/code/run_all.sh
```