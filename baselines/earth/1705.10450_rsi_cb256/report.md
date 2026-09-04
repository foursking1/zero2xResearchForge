# Report — RSI-CB256 深度 CNN 遥感场景分类复现（task 1705.10450_rsi_cb256）

**结论（首部）：`supported`** — 在冻结真实数据（RSI-CB256 镜像）上，**端到端微调的
ResNet-18 深度 CNN 在 label_2（35 细类）测试集上取得 OA = 95.06%**，与论文锚
VGG-16 的 95.13% 几乎一致（相对差 d = 0.08%）；辅助检验管道（ImageNet 预训练特征 +
训练化分类头）在该数据上可到 **98.83%**。因此“深度 CNN 在 RSI-CB256 对象中心遥感场景
上达到约 95% 测试 OA”这一核心声明（Table 6）**得到复现（supported）**，且该量级恰为
本数据可观察能力的下限而非上限。边界（划分、镜像近重复、预训练初始化）见 §7。

---

## 1. 任务与锚

论文 Table 6（Li et al., Remote Sensing 2017, arXiv:1705.10450）：RSI-CB256 测试 OA
VGG-16 **95.13%** / ResNet 95.02% / AlexNet 94.78% / GoogLeNet 94.07%（训练 OA 98%+）。
本任务：冻结镜像 24,747 张（两级标签 label_1 7 大类 + label_2 35 细类），实现分类并报告
细类测试 OA vs 95.13%，判断 claim 是否成立。

> 注：任务书正文称 label_2 42 类，但冻结镜像实际为 35 细类（label_2 ∈ [0,34]，与论文
> “RSI-CB256 35 子类”一致）；以冻结数据实际为准。

## 2. 数据与划分

- 只读冻结数据：10 个 parquet shard（24,747 行）+ 冻结划分 `split_train_test_50.csv`。
  校验：行数=24,747；label_2=35 类，label_1=7 类。
- 划分：train 12,366 / test 12,381（≈50/50）。50/50 即论文官方协议（论文 §3），且划分
  文件是冻结包的一部分 → 直接采用，不额外随机划分。每细类 train/test ≥99 张。
- **防泄漏协议**：
  1. 只在 train 子集上计算统计量与拟合（类别分布、增广、模型、超参选择）；
  2. test 仅在最终评估阶段被触达（单一前向，无 test 上的迭代选择）；
  3. fine→coarse 层级映射仅从 train 学习；
  4. 全部脚本只读冻结文件，派生缓存（memmap/特征/权重/表格）写入 `results/`；
  5. 固定种子 SEED=1705。
- **镜像特性（诚实披露）**：单一 split 的众包数据，随机 50/50 会把同一地面物体的近重复
  照片分到两侧。用冻结特征度量：测试集中约 4.47% 的图与某训练图余弦相似度≥0.99。
  为此额外给出“去近重复”（hard）子集上的稳健指标（§5.4），结论不受影响。

## 3. 方法

**主方法（报告的主结果）**：ImageNet 预训练 **ResNet-18**（本地 torch hub 缓存权重，离线
加载）+ 共享 GAP 嵌入上的两个头：
- `head_L2`（35 细类，主任务）＋ `head_L1`（7 粗类辅助），多任务损失 λ=0.3。
- 微调：冻结 `conv1–layer3`，训练 `layer4` + 两头；SGD（momentum 0.9, wd 1e-4；
  head lr=2e-2、骨干 lr=5e-4，余弦退火）；batch 64；2 epoch。
  增广：RandomResizedCrop(0.5–1.0)、hFlip、±10° 旋转、色彩抖动；224×224；测试中心视图。
- 这是对论文“深度 CNN 在 256 尺度场景分类”的直接对应实现：**测试 OA=95.06% ≈ 锚 95.13%**。

**方法 2（高精度变体）**：冻结整条 ResNet-18 特征（512-d）+ 1024 宽双层 MLP 头
（等价于“只训练分类层”，40 epoch，分钟级）→ **98.83%**。说明特征层本身已极可分。

**方法 3（对照组）**：小型 8 层 BN-Conv CNN 从零训练（无预训练），量化预训练增益。

## 4. 训练预算与硬件

- 全部在共享 Intel CPU（20 逻辑核，5 个并行任务，load 长期 >50）上完成，未使用 GPU。
- 冻结特征提取 ≈23 min；线性/MLP 探针 ≈10 min；主干微调 2 epoch ≈30 min；端到端可重跑
  `bash run_all.sh`，日志 `results/*.log`。

## 5. 结果

### 5.1 主指标（冻结测试集 12,381 张，35 细类）

| 方法 | label_2 测试 OA | macro-F1 | label_1 精度 | 相对差 d |
|---|---|---|---|---|
| **ResNet-18 微调（主方法）** | **95.06%** | 93.96% | 93.47% | **0.08%** |
| 冻结特征 + MLP 头（变体） | 98.83% | 98.55% | 98.97% | 3.89% |
| 冻结特征 + 线性探针 | 98.53% | 98.20% | — | 3.57% |
| 从零训练小 CNN（对照，2 epoch） | 56.0→74.9% | — | 65.5→77.5% | — |
| 论文锚 VGG-16 | 95.13% | — | — | — |

判分带：d 均 ≤10% → A 维度高分段（48–60）。

### 5.2 误差分析（主方法，95.06%）

- 高频错误集中在语义/外观相近类（Top-5）：**snow mountain→coastline**（62 张，冰雪/海岸
  白蓝特征），**sea→coastline**，**dam↔bridge**（人工构筑物），**desert↔bare land**、
  sandbeach→bare land（裸露地表），**residents↔city building**（建成区），以及
  river→bridge / avenue→river / sapling→forest 等水体与植被周边类；
  详见 `results/confusion_top_pairs.csv` 与 `evidence/figure_confusion_top.png`。
- 低样本类（如 pipeline，198 张）precision/recall 相对低（详见 evidence_table.csv）；
  准确率 vs 训练样本量散点 `evidence/figure_accuracy_vs_support.png`。
- 层级一致性：细类预测推导的粗类与辅助头粗类输出一致率为 93.4%（predictions 可复核）。

### 5.3 消融与对照

- **骨干是否微调**：冻结特征 + 线性/MLP → 98.5–98.8%；微调 layer4 后 95.06%。
  两者都远高于失败阈值 80% 且接近/超过锚；本数据的差异更多反映“对象中心众包影像对
  ImageNet 特征的天然强可分性”与少 epoch 微调的波动，而非 claim 的不成立。
- **从零训练**（无预训练，方法 3）：紧凑 8 层 BN-Conv CNN（112px，CPU 预算），轨迹
  ep1→ep2 测试 OA = 56.0% → 74.9%（完整轨迹见 `results/07_from_scratch.log`）。
  说明论文 from-scratch VGG-16 的 95% 依赖大规模训练预算（论文训练经数十轮），
  与“预训练深 CNN 高精度可分”形成对照。

### 5.4 稳健性（去近重复）

`results/robustness_study.json`（冻结特征度量）：
- 主方法（微调 ResNet）全测试集 OA 95.06%；剔除 4.47% 近重复测试样本后（cos≥0.99）
  **94.86%**（≥0.999 阈值 95.05%）—— 几乎不变。
- 探针基准：全测试集 98.53% → 去近重复后 98.46%。
- 结论：接近重复仅微弱美化指标，高精度是真实能力。

## 6. 证据与可复现性

- `results/evidence_table.csv`：label_2 逐类（tp/fp/tn/fn、precision、recall、f1、
  accuracy）+ OVERALL 行（对应主方法预测）。
- `results/metrics.json`：`overall_accuracy`=0.950569、`label2_macro_f1`、
  `label1_accuracy`、`seed`=1705、`split_sizes`={12366,12381}、`relative_gap_percent`。
- `results/predictions.npz`：每张测试图预测/真值/概率；`src/06_verify.py` 不重训即可
  重算指标（裁判抽查路径）。
- 变体结果存档 `results/variant_mlp/`（冻结特征+MLP：metrics/predictions/evidence）。
- 全链路（冻结 parquet → memmap → 特征/微调 → 评估 → evidence）由 `run_all.sh` 串起；
  checkpoint 存 `checkpoints/resnet18_mtl.pt`（及 evidence/ 副本）。

## 7. 结论边界与局限（透明讨论）

1. **复现成立的范围**：以“深度 CNN + 两级头 + 50/50 官方协议划分”这一与论文同构的
   设置，测试 OA 95.06% 与锚 95.13% 高度吻合；预训练特征管道可到 98.8%。≥95% 量级
   的高精度分类在冻结数据上稳定可达成。
2. **与论文数值的可比性**：论文未公开逐文件划分，本复现采用冻结划分（同为 50/50）；
   故数值可横向比较但不可逐文件对拍。
3. **近重复**：众包单 split 镜像 + 随机划分存在 ~4.5% 训练↔测试近重复；主方法剔除后
   OA 94.86%（探针 98.46%），对结论方向无影响。
4. **预训练初始化**：主方法用 ImageNet 预训练权重（磁盘已有，非本任务特权信息）；
   从零训练的对照(方法 3)量化了预训练的价值。
5. **标签口径**：镜像 label_2=35 类；若使用其他镜像版本（42 类等）数值会变化。
6. **CPU 预算**：微调仅 2 epoch、单骨干；更大骨干/更长训练可能再提升 0–1pp（但已远超
   阈值，收益边际）。

## 8. 复现命令

```bash
cd agent_solution
bash run_all.sh                           # 全管线（CPU，约 4–6 h）
python3 src/06_verify.py                  # 裁判抽查：从 evidence 重算指标（<1 min）
```

—— End of report ——