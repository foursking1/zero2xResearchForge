# Report: QU-BraTS 不确定性评分与排名解耦 — 关键论断验证

**任务**：`2112.10074_qubrats_uncertainty_seg`（L1 critical claim）
**论文**：QU-BraTS: MICCAI BraTS 2020 Challenge on Quantifying Uncertainty in Brain Tumor Segmentation
（MELBA 2022:026, arXiv:2112.10074）
**数据**：`data/brats2021_mini.parquet`（BraTS 2021 训练集 10 例子集，冻结，CC-BY-4.0）
**结论**：`supported`

---

## 1. 任务与论断

QU-BraTS 2020 挑战（14 队）用下述分数评估肿瘤分割**预测不确定性**的质量：

> score = AUC1 + (1 − AUC2) + (1 − AUC3)，AUC1/2/3 分别为 DSC、FTP（过滤真阳性比）、
> FTN（过滤真阴性比）随不确定性阈值 τ 变化的曲线下面积（论文 §3；官方记为
> `score=(AUC1+(1−AUC2)+(1−AUC3))/3`，两种写法排序一致）。

两大核心论断：
1. **不确定性排名 ≠ 分割排名**（互补信息）：SCAN 队 QU-BraTS 第 1、BraTS 分割第 4；
   Alpaca 队分割第 1、QU-BraTS 第 7（论文 Table 2）。
2. **好的不确定性能通过阈值过滤清除错误预测**：随 τ 降低（过滤更多体素），应在保持
   真阳性的同时清掉假阳/假阴（论文 Table 1 / Figure 1 演示）。

## 2. 数据解析与基准（Q1）

`brats2021_mini.parquet` 每行 `image`/`annotations` 为 gzip 压缩的 NIFTI 字节封装。
全部 10 例均为 **FLAIR 单模态** `240×240×155`（int16），标注 `{0,1,2,4}`
（1=NCR/NET 坏死、2=ED 水肿、4=ET 增强），对应实体：
**WT = {1,2,4}，TC = {1,4}，ET = {4}**。逐例统计、脑掩码（FLAIR>0）、标签体素数见
`data_cache/raw_meta.json`（总 WT 体素 ~1.03M；00000088 仅 311 个 ET 体素、00000061
含 17 万坏死体素——病例间差异大，ET/TC 难度高）。

**与 BraTS 2020 队列的关系**：同源公开替代（BraTS 2020 为注册制数据不可离线获取）。
两代数据采用同一采集/预处理协议（颅骨剥离、SRI24 配准、1mm³）。规模上本包仅 10 例、
且为单模态；论文为 369 训练 + 125 验证 + 166 测试（多模态 4 序列）。因此本复现的
**数字不可与论文直接比较**，仅检验**方向性论断**。

**固定划分**（患者级，seed 0，`data_cache/split.json`）：
**train 6** = {00000119, 00000088, 00000106, 00000057, 00000061, 00000014}，
**val 1** = {00000055}，**test 3** = {00000116, 00000092, 00000017}。
不确定性仅只在 test 上评估，绝不接触训练。

## 3. 方法（Q2）

### 3.1 预处理与切片
- 每例 FLAIR 在脑掩码内 z-score；轴向切片以**脑质心为中心裁剪 160×160**（`crop_params.json`）。
- 有内容切片进训练集：train 799 / val 142 / test 394 片，batch 16。

### 3.2 分割模型
- 2D **U-Net**，单通道入，**3 输出通道** = ET/TC/WT 三个二值实体头；
  encoder `[16,32,64,128,256]`（~1.9M 参数）；损失 = 逐通道加权 BCE（pos-weight 由实体先验，
  ET/TC/WT 分别 ≈244/67/29）+ 0.4×soft-Dice；Adam lr 1e-3 + 余弦调度，≤35 epoch，
  依 val 均值 Dice 早停并保存最优。随机水平翻转增强。固定种子。

| 模型 | 类型 | seed | dropout | val 均值 Dice |
|---|---|---|---|---|
| mcd_s0 | MC-Dropout | 0 | p=0.3（训练+推理） | 0.151 (ET .060 / TC .062 / WT .327) |
| mcd_s1 | MC-Dropout | 1 | p=0.3 | 0.151 |
| det_s2 | 确定型 | 2 | — | 0.167 |
| det_s3 | 确定型 | 3 | — | 0.165（22 epoch 早停） |
| det_s4 | 确定型 | 4 | — | 0.161 |
| ensemble_det | Deep Ensemble（det_s2+s3+s4 软均值） | — | — | — |

### 3.3 不确定性图
- 逐体素预测概率：MC-Dropout = T=15 次随机前向（仅 Dropout 层置为 train 态、BN 保持 eval）
  sigmoid 均值；确定型 = 单次前向；Deep Ensemble = 三成员软均值。
- **不确定性 = 二值预测熵**（bits）`H(p) = -p log₂p - (1−p)log₂(1−p)`，×100 归一化到 **[0,100]**（论文口径）。
- 消融**随机不确定性基线**：同一分割 + 逐体素 uniform[0,100]（seed 0）。

## 4. QU-BraTS 评分（Q3, A1）

移植官方实现（RagMeh11/QU-BraTS `BraTS_Seg_Uncertainty.py`）为数组接口
`code/qub_metrics.py`：
- 阈值网格 41 点 `τ ∈ {100, 97.5, …, 0}`（`linspace(0,100,41)`，保证端点与 100/75/50/25 落在网格）；
- 每 τ：`unc_mask = (uncertainty ≤ τ)`；被过滤体素（uncertainty>τ）从分割中剔除；
- `DSC(τ)` = 仅剩体素上的 Dice（`GT·mask` vs `Pred·mask`；双空时记 1.0，同官方）；
- `FTP(τ) = (TP₍τ=100₎ − TP₍τ₎)/TP₍τ=100₎`，`FTN(τ) = (TN₍τ=100₎ − TN₍τ₎)/TN₍τ=100₎`，均限**脑掩码**内；
- `AUC1/2/3 = sklearn.auc(τ, 曲线)/100`；`score = (AUC1+(1−AUC2)+(1−AUC3))/3`（Eq.1），
  `score_sum` = 任务原文无 `/3` 写法。

在 3 个测试患者的整卷（reconstruct 回 240×240×155）上评估，逐实体输出
`results/evidence_table.csv`。

### 4.1 关键结果

| 模型 | 实体 | AUC1 | AUC2 | AUC3 | **score** | score_sum | DSC |
|---|---|---|---|---|---|---|---|
| det_s2 | WT | 0.8619 | 0.1085 | 0.1322 | **0.8737** | 2.6212 | 0.7456 |
| det_s4 | WT | 0.8403 | 0.1408 | 0.1263 | **0.8577** | 2.5732 | 0.7757 |
| mcd_s0 | WT | 0.9013 | 0.2021 | 0.2056 | **0.8312** | 2.4936 | 0.8007 |
| mcd_s1 | WT | 0.9063 | 0.2100 | 0.4768 | 0.7398 | 2.2194 | 0.6610 |
| ensemble_det | WT | 0.9359 | 0.2690 | 0.4045 | 0.7541 | 2.2623 | 0.8292 |
| det_s3 | WT | 0.9568 | 0.2849 | 0.6943 | 0.6592 | 1.9776 | 0.8266 |
| mcd_s0 | TC | 0.5791 | 0.2699 | 0.1899 | **0.7064** | 2.1193 | 0.3886 |
| det_s2 | TC | 0.4444 | 0.3084 | 0.1128 | **0.6744** | 2.0231 | 0.4099 |
| mcd_s0 | ET | 0.3791 | 0.3470 | 0.2209 | **0.6037** | 1.8111 | 0.2431 |

完整 18 行（6 模型 × 3 实体）见 `results/evidence_table.csv`；逐阈值曲线见
`results/threshold_means.csv`、`threshold_trends.csv`；图见 `results/figures/`。

### 4.2 结论①：阈值过滤提升“决策可靠性”（A2）✅

以分数最高的 WT 模型 `mcd_s0`（未过滤 DSC 0.8007）为例，随 τ 收紧：

| τ | 100 | 75 | 50 | 25 |
|---|---|---|---|---|
| DSC（剩余体素） | 0.8007 | 0.8562 | 0.8920 | **0.9491** |
| FTP（过滤真阳比） | 0.000 | 0.106 | 0.160 | 0.245 |
| FTN（过滤真阴比） | 0.000 | 0.018 | 0.053 | 0.250 |

- **DSC 单调上升**（0.80→0.95）：被过滤的确实多是不正确断言（FP/FN），剩余体素更可信
  （等价于 FPR↓ 而 TPR 基本保持：FTP 在 τ=75/50 仅 0.11/0.16）。
- `det_s2` WT 同样成立（DSC 0.746→0.906，FTP≤0.12）。低阈值 FTP/FTN 的小幅上升符合
  论文 Table 1 演示（过滤到最后必然碰到真阳/真阴）。
- 与论文一致，**FTN 惩罚能抓出“把背景标为高不确定”的病态不确定性**：
  `det_s3` 在各实体低 τ 处 FTN≈0.99（背景体素几乎全被滤），其 score 显著低于同分割精度的
  `mcd_s0`（WT 0.659 vs 0.831）——正对应论文对 Team Alpaca 式 1−softmax 置信度的批评。

### 4.3 结论②：不确定性排名 ≠ 分割精度排名（A3）✅

6 个模型在 3 个测试患者（整卷）上的「score 排名」vs「DSC 排名」（均降序取均值）：

| 实体 | score 第 1 ↔ dice 第 1 | 排名错位数 | Spearman ρ (p) | 最典型错位 |
|---|---|---|---|---|
| WT | det_s2 (dice#5) ↔ ensemble_det (#4) | 5/6 | −0.31 (0.54) | det_s3 dice#2→score#6；det_s2 dice#5→score#1 |
| TC | mcd_s0 (dice#5) ↔ det_s4 (#1) | 6/6 | −0.20 (0.70) | det_s3 dice#2→score#6 |
| ET | mcd_s0 (dice#3) ↔ det_s3 (#1) | 6/6 | −0.49 (0.33) | det_s3 dice#1→score#6 |

- 无任一实体排名完全一致；WT 上最高分模型 `det_s2` 恰是 DSC 倒数第二的模型；
  最高 DSC 模型 `ensemble_det` 分数仅列第 4。—— 与论文“分割与不确定性提供互补信息”方向一致。
- 论文侧锚（Table 2）：SCAN QU-BraTS #1 / 分割 #4；Alpaca 分割 #1 / QU-BraTS #7。

### 4.4 分数有效性侧证：随机不确定性对照（A1）

同一分割（不变 DSC）替换为随机 uncertainty：

| | entropy | random-unc | Δscore |
|---|---|---|---|
| det_s2 WT | 0.8737 | 0.5829 | −0.291 |
| mcd_s0 WT | 0.8312 | 0.6006 | −0.231 |

随机不确定性 FTP/FTN AUC≈0.5（无信息），分数大幅下降 → 证明 score 度量的是
“不确定性信息”，而非分割准确率本身（`results/random_unc_sanity.csv`）。

## 5. 防泄漏

- 患者级固定划分（seed 0），切片不跨折。
- 阈值过滤、FTP/FTN、score 全部仅在 3 个 held-out 测试患者上计算；不确定性图仅由在
  train 上训练过的模型在 test 上推理生成，任何阈值常量/网格均不参与训练。
- 复现：`bash code/run_all.sh cuda:0`，或分部运行（见 `code/README.md`）。

## 6. 证据复核（B 抽查）

- **抽查 1（score 组成）**：`results/evidence_table.csv` 最优模型 `det_s2` WT：
  `auc1=0.8619, auc2=0.1085, auc3=0.1322, score=0.8737, dice=0.7456`；
  验证：`(0.8619+(1−0.1085)+(1−0.1322))/3 = 0.8737`（`score_sum=2.6211` 与任务式一致）。
- **抽查 2（阈值指标）**：`results/metrics.json` → `threshold_effect_pooled`，
  或 `threshold_means.csv`：`mcd_s0` WT τ=75：dsc=0.8562, ftp=0.1057, ftn=0.0182；
  τ=50：dsc=0.8920, ftp=0.1601, ftn=0.0525。
- `code/verify.py` 从 `per_case_results.json` 独立重算全部 AUC/score/均值并比对，
  **通过（exit 0）**。

## 7. 局限

1. **数据规模/口径**：BraTS 2021 mini 10 例、FLAIR 单模态、2D 切片训练/整卷评估，
   与 BraTS 2020（369 训练 + 166 测试、4 模态、3D）规模与难度差距大；数字不可直接对比论文。
2. **分割精度**：test 患者 WT DSC 0.66–0.83、TC 0.28–0.48、ET 0.18–0.28，远低于
   78 队分割榜（WT≈0.9）。ET/TC 尤其差（FLAIR 不增强高亮增强核心）；低分区绝对 score 偏噪声。
3. **实验对照**：MC-Dropout 与确定性、Deep Ensemble 各取 1–3 个种子/成员，|Δscore| 未做
   显著性检验（论文使用 10 万次置换检验）。
4. **评分细节**：论文默认阈值网格为 40 点（2.5 步）；本复现用 41 点 linspace，端点与
   100/75/50/25 精确对齐，与论文方向一致的 AUC 近似。
5. **NRS/挑战级排名**：论文以 166 例 × 3 实体 = 498 个体排名构造 NRS；本复现仅 3 测试患者，
   以均值 score/DSC 排名展示解耦，未复现 NRS/置换检验统计。

## 8. 结论

- **Q1 数据与基准**：✅ 解析 10 例 BraTS 2021 mini（FLAIR 单模态，{ET,TC,WT} 实体掩码），
  与 BraTS 2020 队列同源对照说明完整。
- **Q2 不确定性方法**：✅ 实现 MC-Dropout、Deep Ensemble、确定型熵不确定性并输出
  [0,100] 逐体素不确定性图。
- **Q3 核心论断**：✅
  1. 阈值过滤使剩余体素 DSC 0.80→0.95（FPR 降、TPR 保持），不确定性过滤有效；
  2. 6 模型 × 3 实体均出现「score 排名 ≠ DSC 排名」（WT 5/6，TC/ET 6/6），
     与论文 Table 2（SCAN #1/#4、Alpaca #7/#1）方向一致；
  3. 分数对“无信息不确定性”敏感（随机对照 score −0.23~−0.29），证实其衡量的正是
     不确定性信息量（互补信息）而非分割精度。

**结论标签：`supported`。**（在冻结替代数据上与论文两大方向性论断一致；受 10 例子集
规模限制，绝对数值不构成对论文 2020 榜单的复现。）

本报告的每个数字均可由 `code/` 从 `data/` 重算（`bash code/run_all.sh` → `code/verify.py`）。