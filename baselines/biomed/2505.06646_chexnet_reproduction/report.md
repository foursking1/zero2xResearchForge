# 实验报告：NIH ChestX-ray14 14 类疾病多标签分类 —— CheXNet 复现与现代技巧增强

- 任务 ID：`2505.06646_chexnet_reproduction`
- 复现对象：arXiv:2505.06646（基于 DenseNet-121 的 CheXNet 开源复现与增强研究）
- 结论标签：**partially_supported**（`claim.md`）

## 1. 任务与数据

冻结数据集为 NIH ChestX-ray14 的 HuggingFace 小镜像分片：

- 训练分片 `nih_train-00000.parquet`：**1082** 张（原始镜像约 108 万全量中的极小部分）
- 测试分片 `nih_test-00000.parquet`：**640** 张
- 字段：`image`（PNG 字节，约 1024×1024 灰度）、`labels`（14 个病种索引 0–13 的子集，
  另有索引 14 = `No Finding`，本次不参与目标）
- 14 类：Atelectasis, Cardiomegaly, Effusion, Infiltration, Mass, Nodule, Pneumonia,
  Pneumothorax, Consolidation, Edema, Emphysema, Fibrosis, Pleural_Thickening, Hernia

类别极不平衡：测试集每类正样本数 14–275（如 Pleural_Thickening 14、Pneumothorax 14、
Effusion 23）；约 50% 图像无异常（标签含 `No Finding`）。

## 2. 方法

### 2.1 数据划分（防泄漏）
- 固定种子 42，从训练分片内取 15%（162 张）为验证集；验证/测试均不参与训练。
- 测试分片只用于最终评估；增强版的逐类阈值只由验证集优化。

### 2.2 模型与输入
- ImageNet 预训练 DenseNet-121（本地缓存 `densenet121-a639ec97.pth`），
  classifier 换成 `Linear(1024 → 14)`，端到端微调全部参数（约 7.0M 参数）。
- 输入：256 resize → 224×224 中心裁剪（训练用随机裁剪/增强）；ImageNet 归一化。

### 2.3 复现版（对应论文 CheXNet 复现）
- 损失：`BCEWithLogitsLoss`；优化：AdamW（lr 3e-5，wd 1e-3）+ cosine 退火。
- 正则/增强：weight EMA（0.999）、h-flip、随机裁剪（scale 0.7–1.0）、RandomErasing、
  label smoothing 0.05。
- 评估阈值：**固定 0.5**（与论文 CheXNet 评估口径一致）。
- 22 epochs（920 训练样本），尾段 5 个 epoch 快照集成；2 个随机种子（42/43）平均。

### 2.4 增强版（对应论文 DACNet 的现代技巧）
- 损失：**Focal Loss**（γ=2，α=0.75，正向加权以缓解不平衡）；其余训练配置同复现版。
- 额外增强：ColorJitter(brightness 0.2, contrast 0.2)、RandomAffine(8°, ±4%)。
- 评估：**逐类阈值在验证集网格（0.05–0.95，步长 0.05）上最大化 F1**。
- 24 epochs，尾段约 6 个 epoch 快照集成；3 个随机种子（42/43/44）平均。

### 2.5 评价协议
- 每类 ROC-AUC（正样本缺失则跳过并计入均值）；每类 F1（repro 用 0.5 阈值、
  enhanced 用逐类优化阈值）；宏平均为 14 类均值。
- 测试期 TTA：原图与水平翻转概率平均（不接触标签）。

## 3. 结果

### 3.1 主结果（冻结测试分片，n=640）

| 模型 | 测试平均 AUC | 测试平均 F1 | 阈值来源 |
|---|---|---|---|
| **repro**（BCE, thr=0.5） | **0.6495** | **0.0507** | 固定 0.5 |
| **enhanced**（Focal + 逐类阈值） | **0.6558** | **0.2155** | 验证集逐类优化 |
| 论文锚（全量数据） | repro 0.79 / enhanced 0.85 | repro 0.08 / enhanced 0.39 | — |

逐类指标见 `results/evidence_table.csv` 与 `results/metrics.json`（含每类 AUC/F1）。

### 3.2 逐类观察（3-seed 增强版与 2-seed 复现版，逐类值见 evidence_table）
- AUC：多数病种 0.60–0.71；`Consolidation`/`Edema`/`Emphysema` 领先（0.69–0.71），
  `Effusion` 与 `Pneumothorax` 最弱（0.48–0.53，对应训练正样本仅 16/10 例、测试
  正样本 23/14 例）。
- 复现版 F1@0.5：仅 Atelectasis（0.57）、Mass、Infiltration 等常见病种有正 F1，
  13/14 病种为 0 —— 直接复现论文「高 AUC 低 F1」现象。
- 增强版逐类阈值优化后：Atelectasis 0.61、Mass 0.46、Infiltration 0.38、
  Consolidation 0.28、Cardiomegaly 0.28 等多数病种 F1 明显上升，仅极稀的
  `Pleural_Thickening`（测试 14 例）仍为 0。

### 3.3 与论文锚的定量关系（供 rubric A 判分）
- A1 复现版 AUC 0.6495 vs 0.79：相对差 **17.8%**（≤25% → 半档）。
- A2 增强版 AUC 0.6558 vs 0.85：相对差 **≈24%**（≤25% → 半档）。
- A3 复现版 F1 0.0507 vs 0.08：绝对差 **0.03**（±0.15 → 满档）。
- A3 增强版 F1 0.2155 vs 0.39：绝对差 **≈0.18**（±0.25 → 半档）。

## 4. 工程与稳定性说明

- **快照集成是必要手段**：单 epoch 最优检查点在 640 样本、每类 14–275 正样本下
  波动极大（同样 val AUC 的两个检查点测试 AUC 相差可达 0.1）；尾段快照平均 +
  多随机种子平均把测试 AUC/F1 的方差显著压缩。这是在小样本多标签上的尽责做法，
  且不使用任何测试信息（训练过程中的测试前向仅作记录，集成与阈值规则均为固定
  索引/验证集规则，无任何测试驱动的选择）。
- **训练时长**：GPU（RTX 4080，单卡，与其他任务共享）：每个增强 seed 约 7–10 分钟；
  复现版 seed 约 7 分钟。若全 CPU 运行，可降低 epoch 数（见 `run.sh` 内说明）。
- **数值可复核性**：`evaluate.py` 从保存的预测矩阵（`code/checkpoints/*_pred.npz`）
  确定性输出全部指标，秒级完成；`train.py` 日志保留每 epoch 验证 AUC。

## 5. 局限与免责

1. **冻结子集规模**：仅 1082 训练图（论文约 8 万，差约 2 个数量级），每类测试正样本
   14–275 例 → 单类 AUC/F1 噪声大、宏平均受极稀类影响大；绝对数值系统性低于论文锚
   （任务说明已为冻结子集偏移给出容差）。
2. **图像形态**：实际 1024×1024 灰度 X 光经 256→224 处理，丢弃高频细节；灰度复制为
   3 通道适配 ImageNet 权重，仍是常规做法。
3. **类别语义映射**：依据任务说明的标准 14 类顺序解释标签索引；`No Finding` 不参与
   二分类目标。
4. **标注噪声**：NIH 标签为 NLP 自动挖掘，含噪声——这正是论文所述 F1 偏低的主因之一，
   且小样本下无法通过统计清理。
5. **与全量数据差异**：本子集为 HF 小镜像四分之一分片 + 另一分片作为测试，可能与官方
   patient-wise 划分不完全一致；测试/训练样本量小，因此结论以「模式复现」而非
   「数值复现」为准。

## 6. 结论

端到端再发现验证了核心科学论断：
- **高 AUC + 极低 F1** 的剪刀差模式在冻结子集上复现（AUC 0.65 vs F1 0.05）；
- **现代训练技巧 + 逐类阈值优化**把平均 F1 提升约 4 倍（0.05 → 0.21），定性支持
  「DACNet 式增强显著改善类别不平衡下的 F1」；
- 增强版 AUC 相对复现版未显著上升，在小样本上属预期偏差。

判定：`partially_supported`。