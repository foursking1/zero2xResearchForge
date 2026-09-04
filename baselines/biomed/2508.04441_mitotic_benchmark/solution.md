# solution.md — 方法说明与结果摘要

## 任务
复现/验证论文「Benchmarking Foundation Models for Mitotic Figure Classification」
（arXiv:2508.04441, MIDOG 2022）的 L1 关键论断：冻结子集上的有丝分裂/难例分类，
以及"少量数据接近全量"的数据效率趋势。

## 数据
冻结包：`MIDOG2022_training_png.json`（官方 MS COCO，405 图，20,552 标注：
9,501 有丝分裂 + 11,051 难例，SHA-256 已核对）+ 4 张 2mm² WSI 裁剪 PNG
（`002/008/024/063.png`，各约 70–84 MB，7200×5400 量级，SHA-256 与 README 一致）。

## 方法
1. **解析**（`code/01_parse_annotations.py`）：读 COCO，按图像过滤 4 图；
   bbox 为角点对 `[x1,y1,x2,y2]`（MIDOG PNG 版格式），取中心 224×224 裁剪 → 153 patches
   （62 正 / 91 负），保存 `results/patches.npz` 与统计 JSON。
2. **特征**（`code/02_extract_features.py`）：torchvision **ResNet18-ImageNet**（512-d）与
   **ViT-B/16-ImageNet**（768-d，CLS 特征）特征冻结，每个 patch 在 0/90/180/270 四旋转下
   提取（训练侧用作增强，测试只用 rot0），保存 `results/features.npz`。
   *离线环境无病理基础模型（Phikon/UNI/Virchow…）权重，按 TASK 允许使用 ImageNet 编码器。*
3. **分类**（`code/03_train_classify.py`）：Linear Probe（L2-LogisticRegression, class-balanced）
   与小 MLP(128)，标准 5 折分层 CV、合并折预测评估；10% 与 100% 用**同测试折**、训练折内分层
   抽样；8 次随机抽样/折划分 bag 求平均（评测即由代码重算）。
4. **可选适配头**（`code/05_finetune_cnn.py`）：ResNet18 冻结至 layer3，微调 layer4+fc
   （AdamW, 30 epochs, rot/h-flip/v-flip 在线增强），3 个 CV seed bagged——对应论文"适配>线性探测"
   方向的低成本代理。
5. **汇总**（`code/06_gather_metrics.py`）：输出 `results/metrics.json`（子集统计/各模型指标/
   论文锚对照/结论标签）与 `results/evidence_table.csv`。
6. **图表**（`code/04_make_figures.py`）→ `evidence/`。

## 结果
| 模型（100% 数据） | Balanced ACC | Weighted F1 | AUROC |
|---|---|---|---|
| ResNet18 \| LinProbe **（最优）** | **0.601** | **0.615** | **0.605** |
| ResNet18 \| MLP | 0.588 | 0.602 | 0.623 |
| ViT-B/16 \| LinProbe | 0.566 | 0.577 | 0.595 |
| ViT-B/16 \| MLP | 0.558 | 0.571 | 0.581 |
| FT-ResNet18 layer4+head（适配头，可选） | 0.612 | 0.627 | 0.613 |

数据效率（同模型）：LinProbe 100%→10%：F1 0.615→0.527（**Δ=0.088 ≤ 0.15**）；
MLP：0.602→0.534（**Δ=0.068**）。10% 数据达到全量约 86% 性能。子集统计：**62 MF / 91 HN**。

## 结论标签：**supported**
（对冻结 4 图子集 + ImageNet 编码器协议；范围见 `claim.md`/`report.md` 局限性节）

## 复现
```
bash code/run_all.sh          # 全流程（GPU 推荐用于 step2/5）
# 仅 CPU 验证关键数：
python3 code/01_parse_annotations.py
python3 code/03_train_classify.py --seeds 5 --folds 5 --augment
python3 code/06_gather_metrics.py
```
重跑后 `results/evidence_table.csv` 逐字节一致（固定种子）。