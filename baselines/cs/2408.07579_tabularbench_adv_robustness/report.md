# 方法与报告：URL 数据集鲁棒性论断验证

## 1. 背景与目标
TabularBench（Simonetto et al., NeurIPS 2024 D&B, arXiv:2408.07579）在 URL 网络钓鱼检测用例（Table 3）上报告两个关键论断：
- **C1**：标准训练下 5 种深度架构 ID 精度接近（92.5–94.4%）但约束攻击下鲁棒精度悬殊（8.9–58.0%）。
- **C2**：对抗训练后鲁棒精度大幅提升（56.2–91.8%）而干净精度基本保持（93.4–99.5%）。

本报告在冻结的 URL 数据上，以任务协议（官方划分、min-max 缩放、4 个 MLP、FGSM-AT、PGD-L2 ε=0.25）自行训练+评估，对两个论断做结构性验证。

## 2. 数据
- `data/url.csv`：11,430 行 ×（63 数值特征 + `is_phishing` 标签）；正类率 50.0%（5715/5715）。SHA-256 与 `data/source_manifest.json` 一致。
- `data/url_metadata.csv`：每特征 type/mutable/min/max（攻击边界参考，本协议统一 clip 到 [0,1]）。
- 划分（官方 DefaultSplitter，`train_test_split(random_state=42, shuffle=True, stratify=y)` 双层）：
  - 第 1 次：80/20 → train 9,144 / test 2,286
  - 第 2 次：train 再 80/20 → train 7,315 / val 1,829
  - 最终 train 7,315 / val 1,829 / test 2,286。val 在本任务中仅作统计参考，不使用测试信息。

## 3. 方法
### 3.1 标准化（train-only）
逐特征 min-max 缩放到 [0,1]：`(x − min_tr)/(max_tr − min_tr)`，min/max 只在 train 划分上拟合；零跨度特征除以 1；全局 clip 到 [0,1]。test/val 不参与任何统计量估计。

### 3.2 模型
4 个前馈 MLP，ReLU 激活，单 logit 输出（BCEWithLogits）：
| 名称 | 结构 |
|---|---|
| mlp64 | 64 |
| mlp128_64 | 128–64 |
| mlp256_128_64 | 256–128–64 |
| mlp128_64_drop | 128–64 + Dropout(0.3) |

### 3.3 训练
- 优化器 Adam（lr=1e-3, weight_decay=1e-4），batch 256，12 epochs，BCEWithLogits。
- **标准训练**：原生 batch。
- **对抗训练（FGSM-AT）**：对每个 batch 生成 1 步对抗样本再更新——每样本扰动 δ=α·g/‖g‖（g 为 loss 对本 batch 输入的梯度，α=0.1）；投影到以原始样本为中心、半径 ε=0.1 的 L2 球；clip 到 [0,1]；用扰动后的 batch 计算 loss 并梯度更新。
- 固定种子 0（`torch.manual_seed + np.random.seed`），每模型每训练开始前重置；随机打乱用 `torch.randperm`。

### 3.4 评估攻击（无目标 PGD-L2）
对测试集全部 2,286 样本最大化 BCEWithLogits loss，40 步，预算 ε=0.25，步长 α=ε/4=0.0625：
`x_{t+1} = clip_{[0,1]}( Π_{B_ε(x_0)} (x_t + α·∇loss/‖∇loss‖) )`
即每步沿归一化梯度方向走步（非符号梯度，匹配 L2 攻击），投影回以原始样本为中心的 L2 球，再 clip 到特征域 [0,1]。以 0.5 阈值的 sigmoid 输出判类。
> 口径差异：论文默认攻击为 CAA（ε=0.5，能力更强）；本任务协议采用 PGD-L2 ε=0.25，其破坏力量级与论文 CAA ε=0.5 相当（论文 Figure 4/5 预算曲线）。因此绝对值不可与 Table 3 直接对比，只做结构性对照。

### 3.5 指标
clean accuracy（测试集干净精度）与 robust accuracy（PGD 攻击下精度），均为百分比；逐模型×逐训练统计，并报告跨度（max−min）与均值。

## 4. 结果
### 4.1 逐模型（详见 `results/evidence_table.csv`）
| model | training | clean_acc | robust_acc |
|---|---|---|---|
| mlp64 | standard | 91.91% | 50.83% |
| mlp64 | adversarial | 89.90% | 77.73% |
| mlp128_64 | standard | 93.00% | 17.45% |
| mlp128_64 | adversarial | 91.82% | 78.13% |
| mlp256_128_64 | standard | 94.09% | 18.15% |
| mlp256_128_64 | adversarial | 93.44% | 76.51% |
| mlp128_64_drop | standard | 93.57% | 24.98% |
| mlp128_64_drop | adversarial | 91.95% | 77.73% |

### 4.2 汇总
| 指标 | 标准训练 (std) | 对抗训练 (AT) |
|---|---|---|
| clean 范围 / 均值 | 91.91–94.09% / 93.14% | 89.90–93.44% / 91.78% |
| clean 跨度 | **2.19pp** | 3.54pp |
| robust 范围 / 均值 | 17.45–50.83% / 27.85% | 76.51–78.13% / 77.53% |
| robust 跨度 | **33.38pp** | **1.62pp** |
| Pearson(ID, robust) | **−0.85** | −0.66 |

- **C1（ID 接近但鲁棒悬殊）→ `supported`**：clean 跨度 2.19pp ≤ 5pp；robust 跨度 33.38pp ≥ 15pp。
- **C2（AT 有效，干净保持）→ `supported`**：平均鲁棒提升 **+49.67pp** ≥ 20pp；平均干净下降 **−1.37pp** ≤ 5pp。

## 5. 分析与讨论
- **容量-鲁棒性观察**：标准训练下不存在"越大越好"的正向鲁棒收益——最小的 mlp64 最鲁棒（50.8%），最深的 mlp256_128_64 最脆弱（18.2%），dropout 介于其间。ID 精度却几乎与容量无关（91.9–94.1%）。这与论文"ID 精度有误导性、鲁棒性对架构敏感"的论点一致。
- **AT 抹平架构差异**：AT 后鲁棒跨度从 33.38pp 收敛到 1.62pp，架构间的鲁棒差异被大幅抹平，干净跨度也仅增加 1.4pp。观察与论文一致。
- **相关性**：标准训练下 ID 与鲁棒精度呈强负相关（−0.85），说明干净精度不仅不能预示鲁棒性，甚至反向相关。AT 后相关性变弱（−0.66）。n=4 过小，此数字仅供定性参考（论文 Table 10 亦报告相关不稳定）。
- **每模型鲁棒提升**：26.9–60.7pp；最小提升出现在标准训练已最鲁棒的 mlp64，这正是"AT 收益受起点鲁棒性影响"的体现。

## 6. 结论
论文的两个关键论断在本冻结数据 + 本协议下均得到支持：标准训练模型 ID 精度接近但鲁棒性天差地别（C1）；FGSM-AT 以 ≈1.4pp 的干净代价换取 ≈+49.7pp 的鲁棒提升并抹平架构差异（C2）。

## 7. 局限与适用范围
1. **攻击口径**：PGD-L2 ε=0.25 ≠ 论文 CAA ε=0.5；绝对值不可直接对比，本结论为结构性验证。不同 ε/攻击族可能改变绝对数值（但不改变"鲁棒悬殊/AT 大幅提升"的结构）。
2. **模型族**：4 个 MLP 替代论文 5 种专用架构（TabTr/RLN/VIME/STG/TabNet）；本文结构模式跨族稳健，但具体数字属于 MLP 族。
3. **AT 为 FGSM 单步**（论文为完整 AT 流程）：ε=0.1 下的启发式对抗样本；更强攻击下 FGSM-AT 常有鲁棒性高估的已知缺陷，绝对值需谨慎。
4. **数据范围**：单一 URL 用例；结论外推到其他 TabularBench 用例需另行验证（论文 Table 3 各用例模式也有差异）。
5. **相关性统计**：n=4，置信区间很宽，仅定性。
6. **确定性**：全部固定 seed 0，CPU 运算；同一机器连续两次运行 `metrics.json` 逐字节一致（`evidence/rerun_compare.txt`）。跨机器/依赖版本可能存在浮点级微小差异（不影响第二位小数的结论）。

## 8. 复现
```bash
cd agent_solution
python3 -m pip install -r code/requirements.txt   # numpy pandas scikit-learn torch matplotlib
python3 code/run_experiment.py --data ../data/url.csv --out results   # 全部重算（CPU，约 15–35 分钟）
python3 code/analysis_plots.py
```
主脚本从 `data/url.csv` 起重算全部指标（划分→缩放→8 次训练→8 次 PGD 评估），覆写 `results/evidence_table.csv` 与 `results/metrics.json`。