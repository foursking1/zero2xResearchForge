# 实验报告：TabularBench URL 数据集鲁棒性验证

## 1. 任务与方法概要

验证 arXiv:2408.07579（TabularBench）Table 3 在 URL 网络钓鱼检测数据集上的两个关键论断：
- **C1**：标准训练下不同深度架构的 ID（干净测试）精度接近，但约束对抗攻击下的鲁棒精度悬殊。
- **C2**：对抗训练（AT）显著提升鲁棒精度，干净精度代价可忽略。

实验使用冻结数据 `data/url.csv`（11,430 行，63 个特征 + `is_phishing`），全部指标由本地运行代码得到。

## 2. 方法实现细节

### 2.1 数据划分（复刻官方 DefaultSplitter）
- 两次 `train_test_split(random_state=42, shuffle=True, stratify=y, test_size=0.2)`：第一次分出 test 20%，第二次从剩余 train 分出 val 20%。
- 结果：**train 7,315 / val 1,829 / test 2,286**；正类率 50.0%。
- val 划分仅用于记录划分口径，训练与评估均使用 train/test（与任务协议一致）。

### 2.2 标准化
- 逐特征 **min-max 缩放到 [0,1]**：`(x - min_train) / (max_train - min_train)`，再 clip 到 [0,1]。
- 缩放统计量（每特征 min/max）**只用 train 划分拟合**，test/val 不参与任何统计量估计。
- 零方差特征（span=0）设 span=1 避免除零。

### 2.3 模型
4 个 ReLU MLP，输出单 logit（BCEWithLogits）：
- `mlp64`：隐藏层 [64]
- `mlp128_64`：[128, 64]
- `mlp256_128_64`：[256, 128, 64]
- `mlp128_64_drop`：[128, 64] + Dropout(0.3)

### 2.4 训练
- 优化器 Adam（lr=1e-3, weight_decay=1e-4），batch 256，12 epochs，BCE loss。
- 固定随机种子 `seed=0`（`torch.manual_seed` + `np.random.seed` 各一次），CPU 训练。
- 两种训练方式：
  - **标准训练（standard）**：直接最小化干净样本的 BCE loss。
  - **对抗训练（FGSM-AT）**：对每个 batch 先做 FGSM 单步攻击（ε=0.1，L2 归一化步长 α=0.1，投影回 L2 球并 clip 到 [0,1]），再用对抗样本更新模型。

### 2.5 攻击评估（PGD-L2，无目标）
- 对 test 全部 2,286 样本做无目标攻击（最大化 BCE loss）。
- **L2 预算 ε=0.25**；步数 40；步长 α=ε/4=0.0625。
- 每步：沿 L2 归一化梯度方向走步 → **投影回以原样本为中心的 L2 球** → **clip 到 [0,1]**（特征域边界）。
- 评估指标：clean accuracy（干净 test 精度）、robust accuracy（攻击后 test 精度），百分比。
- 攻击评估只使用已训练模型，测试集不参与训练或调参。

## 3. 结果

### 3.1 各模型×各训练方式（表 1）

| model | training | clean_acc | robust_acc |
|---|---|---|---|
| mlp64 | standard | 91.64% | 50.87% |
| mlp128_64 | standard | 93.66% | 16.01% |
| mlp256_128_64 | standard | 94.44% | 12.42% |
| mlp128_64_drop | standard | 93.39% | 23.05% |
| mlp64 | adversarial | 89.90% | 77.78% |
| mlp128_64 | adversarial | 92.21% | 77.73% |
| mlp256_128_64 | adversarial | 92.83% | 77.78% |
| mlp128_64_drop | adversarial | 92.08% | 76.95% |

### 3.2 汇总指标

| 指标 | standard | adversarial |
|---|---|---|
| clean 均值 | 93.29% | 91.75% |
| clean 范围 | 91.64–94.44% | 89.90–92.83% |
| clean 跨度 | **2.80pp** | 2.93pp |
| robust 均值 | 25.59% | 77.56% |
| robust 范围 | 12.42–50.87% | 76.95–77.78% |
| robust 跨度 | **38.45pp** | 0.83pp |

- **AT 相对 std 平均鲁棒提升：+51.97pp**
- **AT 相对 std 平均干净精度变化：−1.53pp**
- 逐模型鲁棒提升：+26.99pp（mlp64）、+61.63pp（mlp128_64）、+65.44pp（mlp256_128_64）、+53.93pp（mlp128_64_drop）。
- 逐模型干净代价：−1.75pp、−1.44pp、−1.62pp、−1.31pp。

### 3.3 结构观察
- **标准训练下**：clean 跨度仅 2.80pp，robust 跨度高达 38.45pp。小模型 mlp64 最鲁棒（50.87%），大模型 mlp256_128_64 最脆弱（12.42%），呈现"容量越大越易受攻击"的负相关趋势（与论文 Table 10 的标准训练相关方向一致）。
- **AT 后**：各架构 robust 收敛到 76.9–77.8%（跨度 0.83pp），"AT 抹平架构差异"复现。

## 4. 结论

- **C1（ID 接近但鲁棒悬殊）：supported**。clean 跨度 2.80pp（≤5pp）且 robust 跨度 38.45pp（≥15pp），结构性模式成立。
- **C2（AT 大幅提升鲁棒且干净保持）：supported**。平均鲁棒提升 +51.97pp（≥20pp），平均干净代价 −1.53pp（≤5pp）。
- 与论文 Table 3 对照：论文 standard ID 92.5–94.4（跨度 1.9pp）、robust 8.9–58.0（跨度 49.1pp）；AT 鲁棒 56.2–91.8、干净 93.4–99.5、平均提升 ≈+45pp。本实验在 MLP+PGD-L2 ε=0.25 口径下复现了相同的结构模式（方向与量级一致），但具体绝对值因攻击与模型族不同而有差异。

## 5. 局限与口径差异

1. **攻击差异**：论文默认攻击为 CAA（ε=0.5），本实验用 PGD-L2 ε=0.25。任务协议认定两者破坏力量级相当（PGD-L2 ε=0.25 下的结果与论文 CAA ε=0.5 的曲线量级可比），但绝对鲁棒值不能与论文逐项对齐。
2. **模型族差异**：论文使用 5 种专用表格架构（TabTr/RLN/VIME/STG/TabNet），本实验为 4 个 MLP。MLP 族无法完全代表论文模型族的鲁棒性水平，但结构模式（ID 相近 vs 鲁棒悬殊；AT 提升且抹平差异）一致。
3. **训练预算**：12 epochs / Adam 属轻量训练，未使用论文的完整训练配置；绝对精度略低于论文。
4. **AT 方式**：使用单步 FGSM-AT（ε=0.1），论文的对抗训练细节可能不同；单步 AT 在大模型上提升尤其显著。
5. **容量-鲁棒性观察**：标准训练下观察到"大模型更脆弱"，AT 后该差异基本消失——该现象仅在 PGD-L2 口径下验证，未推广到 CAA。
6. **单数据集**：结论仅针对 URL 用例；TabularBench 还含其他用例，不在此处验证。

## 6. 复现

```bash
python code/run_experiment.py
```

- 读取：`data/url.csv`（冻结，SHA-256 见 `data/source_manifest.json`）。
- 输出：`results/evidence_table.csv`、`results/metrics.json`。
- 环境：Python 3.13，numpy 2.5.2，pandas 3.0.5，torch 2.13.0+cpu，scikit-learn；固定 seed=0。
- 运行时间约 2 分钟内（CPU）。
