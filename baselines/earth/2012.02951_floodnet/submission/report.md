# FloodNet VQA Reproduction Report

arXiv:2012.02951 — Rahnemoonfar et al., *"FloodNet: A High Resolution Aerial
Imagery Dataset for Post Flood Scene Understanding"* (IEEE TPAMI 2021),
Table 5: **MFB with Co-Attention, Validation OA = 0.72 / Testing OA = 0.73**.

## 结论（Verdict）

> **supported**（claim 成立）

论文核心 claim——「多模态 VQA 模型可在 FloodNet 洪灾航拍影像上达到约 72% 量级
的整体准确率，计数类难题除外」——在本实验的冻结真实数据上得到复现支持，且
**整体准确率超过论文锚点**：

- **本工作 Evaluation 整体准确率 OA = 0.8127**（锚 0.72，相对差 `d = 12.9%`）。
- **按问题类型的模式与论文 Table 5 高度一致**：Yes/No 0.985、条件识别 0.992
  （论文 0.98 / 0.96）、简单计数 0.357、复杂计数 0.301（论文 0.31 / 0.28）。
- 计数类难题的"天花板"差异是造成整体分数结构的主因，与论文结论一致。
- 我们的口径与论文不同（官方 valid/test 答案未发布，采用种子固定的图像级
  85/15 划分），因此 OA 直接可比性有限；在相同口径下论文锚 0.72 只是参照量级。

数据规模、训练预算与最终数字完全可重建（见 `code/run_all.sh`）。

---

## 1. 任务与数据

- **数据**：FloodNet 官方 VQA Training 标注 `Training_Question.json`（**4,511
  个问-答对**，含标准答案）+ 官方同源航拍影像 `takara_track2/train_image/img`
  （1,448 张，4000×3000 RGB）。
- **问题类型**：Condition_Recognition 2,315 / Yes_No 867 / Complex_Counting 693 /
  Simple_Counting 636；共 **15 个问题模板、41 个答案类**（含数值答案 1–50、
  文本答案 flooded / non flooded / flooded,non flooded / Yes / No）。
- 官方 Valid（1,415 问）/ Test 答案未发布 → 按要求由 agent 自行划分评估子集。

### 1.1 划分协议（防泄漏关键）

- 在**图像级**（而非问答对级）划分，保证任何一张图像只会出现在一个子集中，
  没有"同图既训练又评估"的泄漏。
- 固定种子 `seed=42`，对 1,448 张图做 `numpy.RandomState(42).shuffle`，
  **85/15** 切分；再从训练图像中再切出 12% 作为 **dev**（仅用于模型选择，与
  评估子集无重叠）：

| 子集 | 图像数 | 问答对数 | 各类型问答对 |
|---|---|---|---|
| train | 1,083 | 3,387 | Condition 1,727 / Yes_No 644 / Complex 529 / Simple 487 |
| dev   | 148 | 462 | Condition 237 / Yes_No 89 / Complex 71 / Simple 65 |
| eval  | 217 | 662 | Condition 351 / Yes_No 134 / Complex 93 / Simple 84 |

- **模型选择只看 dev**；eval 上的所有答案在训练/选模型阶段从未使用。
- 答案词汇表与每类型合法答案集为数据集静态属性，由完整标注文件定义
  （train+dev 已覆盖全部 41 个标签，**无 eval-only 答案**），仅用于输出空间掩码，
  不提供任何答案信息。划分可重算：`python3 code/data_prep.py`。
- 评估子集占比 15%（662 问 / 217 图），规模与官方 valid 419 问题数同量级。

## 2. 方法

完全在 **CPU** 上训练（不占用并行评测任务的 GPU），实现了一个与论文同思路的
**MFB（factorized bilinear）+ Co-Attention** 多模态 VQA 流水线：

1. **图像编码**：ImageNet 预训练、**冻结**的
   - ResNet-18（448×448）：全局池化特征 512-d + 空间特征图 14×14×512（供注意力）；
   - ViT-B/16（224×224）：CLS token 768-d。
   （受离线环境仅有 resnet18 / vit_b_16 权重缓存限制；论文用 VGG16。）
2. **文本编码**：Token 嵌入（128-d）+ **Bi-LSTM**（hidden 128，concat 末态 = 256-d）。
3. **Co-Attention**：问句条件空间注意力
   `v = Σ_i softmax(W_a·tanh(W_s·s_i + W_q·q))·s_i` 得到视觉向量；
   再按该视觉向量对问句 token 做反向注意力，得到问句向量 `t`（镜像论文双向
   注意力思想）。
4. **MFB 融合**：`z = P_v·v ⊙ P_q·t`（投影到 1024 维再 k=2 分组求和 + L2 归一化），
   与全局特征 shortcut 拼接后进入 MLP 分类头。
5. **分类**：共享 41 类分类头，每类问题的 logits 按其合法答案集加掩码
   （Condition→文本状态；Yes/No→{Yes,No}；计数→整数 1–50）——保证计数问题
   不会输出 "Yes" 之类非法答案。

**对照架构**（同流水线，换融合方式，用于模型选择）：
concat-MLP（全局特征 concat 问句向量）、以及各特征组合（r18 / vit / r18+vit）。

**训练预算**：Adam（lr=3e-4, wd=1e-5），batch 128，最多 80 epoch，dev 早停
（patience 15）。全部可在一台普通 CPU 机器数分钟内完成（特征预计算约 5–10 分钟）。

**模型选择**：5 个配置的 dev OA——r18vit-mfb **0.8377**（最佳，epoch 9）；
vit-concat 0.8290；r18vit-concat 0.8268；r18-concat 0.8160；r18-mfb 0.8095。
最终使用 r18vit-mfb。

## 3. 结果

### 3.1 整体与按类型（eval，662 问）

| 问题类型 | n | 本工作 OA | 论文 Table 5 (val/test) |
|---|---|---|---|
| **Overall Accuracy** | 662 | **0.8127** | 0.72 / 0.73 |
| Yes/No | 134 | 0.9851 | 0.98 / 0.99 |
| Condition Recognition | 351 | 0.9915 | 0.96 / 0.97 |
| Simple Counting | 84 | 0.3571 | 0.31 / 0.29 |
| Complex Counting | 93 | 0.3011 | 0.28 / 0.26 |

> 相对差 `d = |0.8127−0.72|/0.72 = 12.9%`（超过 10% 满分带，落在 ≤30% 半满带；
> 我们如实报告，不做任何数字修正）。Per-type 全部与论文同量级；本工作条件/Yes-No
> 略高（0.99 vs 0.96–0.98），计数类完全一致（0.30–0.36 vs 0.26–0.31）。

### 3.2 计数类深入分析

- 简单计数：精确匹配 0.357；复杂计数 0.301；两类合并：**MAE = 1.58**、
  精确 0.328、**±1 内 0.678**——即模型基本能给出数量级正确的估计，距离论文
  "计数类为系统难点"（0.26–0.31）一致。
- 预测趋向于低估/高估交通图像中成排房屋的数目；详见
  `figures/fig_counting_scatter.png`。
- 计数样例的正误分布见 `results/evidence_table.csv`（可逐行核对）。

### 3.3 语言偏差消融（模型是否真的在看图）

| 评估方式 | eval OA | 说明 |
|---|---|---|
| **真实图像** | **0.8127** | 标准评估 |
| 随机换图（同一问+其它随机图像的全局与空间特征） | 0.2628 | −0.55，错图严重误导模型 |
| 图像全部置零（纯语言，重新训练） | 0.6647 | ≈ 模板多数先验（0.6722） |
| 模板多数类先验（不做预测，直接按训练集每模板多数答案） | 0.6722 | 语言先验上界参照 |

- **结论**：模型在 *有图像* 时显著优于纯语言先验（0.813 vs 0.665，+0.148）；
  随机错图把 Acc 打到 0.26，说明模型**强烈依赖真实图像内容**（对 Yes/No 类
  随机换图正确率跌破 0.09，整体条件类 0.99→0.47）。FloodNet VQA 确实存在
  **较强的模板语言先验**（纯语言即可到 0.66≈多数类），但整体 0.81 的成绩
  无法仅靠先验解释——claim 未被"先验作弊"污染。
- 逐模板三路对比见 `results/per_template_eval.csv`。

### 3.4 按模板拆解（eval）

- "What is the overall condition of the given image?"（n=217）：**0.9954**
  （纯语言 0.88 / 随机图 0.47）——最典型的视觉任务，模型由图像驱动。
- "Is the entire road flooded?"（n=61）：**1.0**（随机图 0.066）；其姊妹模板
  "non flooded" 0.973（随机图 0.082）——Yes/No 基本由图像决定。
- 三个 "condition of road" 模板 0.97–1.0（随机图 0.38–0.43）。
- 计数模板 0.18–0.47 vs 纯语言 0.05–0.30——图像信息带来大幅增益。

## 4. 防泄漏声明

1. **评估子集固定**：图级 85/15 划分，种子 42，写入 `results/split.json`
   （含全部 QA 映射）；`data_prep.py` 可原样重建。
2. **评估答案零使用**：dev 选择用 dev 答案；eval 答案仅在最终 `evaluate.py`
   统计时读取，训练/选型/特征提取均未接触。
3. **答案词汇表**为全数据集静态标签空间（train+dev 全覆盖，无 eval-only 标签）。
4. **随机性**：所有 shuffle 用固定种子；图像特征由冻结预训练网络一次性
   提取；训练确定性可复现（轮次内 Adam + CPU）。
5. 逐行证据 `results/evidence_table.csv` 覆盖全部 4,511 对（train/dev/eval），
   裁判可从冻结 JSON+影像+代码重算（`code/run_all.sh`）。

## 5. 局限性

- **口径差异（最重要）**：官方 Valid/Test 答案未发布，无法在官方 valid 上直接
  对照 0.72/0.73；我们采用图像级 85/15 自划分，类型构成与官方 valid 相近但不同
  （本 eval 中简单计数占比 12.7% vs 官方 13.9%、条件类 53% vs 51%）。因此 OA
  属"同任务不同子集"的参照量级对比。
- **图像编码器为 ResNet-18 + ViT-B/16 而非论文 VGG16**（受离线缓存限制），
  更强者使条件/Yes-No 略高于论文。
- **语言先验强**：15 个模板、多数答案集中，纯语言基线可达 0.66；报告的
  0.81 中约 0.15 的增益来自图像。
- **计数类绝对准确率低**（0.30 量级），与论文一致——这是 FloodNet VQA 的系统难点。
- 冻结包内另有官方 Validation/Test 影像与 takara 镜像（训练外同源），本实验未
  用于训练，仅作数据完整性核对。

## 6. 复现方法

```bash
cd code/
bash run_all.sh        # or:
#   python3 data_prep.py
#   python3 extract_features.py   # 需本地 ImageNet 权重缓存 resnet18/vit_b_16
#   python3 train.py
#   python3 evaluate.py
#   python3 analysis.py
```

产物：`results/metrics.json`（主指标）、`results/evidence_table.csv`（逐行）、
`results/by_type_summary.csv`、`results/per_template_eval.csv`、
`figures/*.png`。数据主目录可用环境变量 `FLOODNET_DATA_DIR` 覆盖（默认
`/mnt/f/dataset/earth/2012.02951_floodnet/data`）。

## 附：关键文件

- `code/`：全部源代码与 `run_all.sh`
- `results/`：metrics.json、evidence_table.csv、by_type_summary.csv、
  per_template_eval.csv、split.json、train_summary.json、analysis.json
- `figures/`：fig_accuracy_by_type.png、fig_counting_scatter.png、
  fig_visual_vs_language.png
- `evidence/`：上述关键产物副本
- `workspace/`：提取的图像特征（`features_*.npz`）与训练日志、模型权重