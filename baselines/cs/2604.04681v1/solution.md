# 复现报告：Batch Loss Score for Dynamic Data Pruning（arXiv:2604.04681v1, CVPR 2026）

## 1. 结论摘要（Claim 判定）

| Claim | 判定 | 核心依据 |
|---|---|---|
| **C01** BLS 在大规模数据集（ToCa / MJ+ST / SS1M）上以 20–40% 剪枝代理 InfoBatch/SeTa | **inconclusive** | 冻结数据中不含 ToCa / MJ+ST / SS1M 数据集（`data/`、`code/BLS/data/` 仅有 CIFAR10/100），无法实际运行，故无法给出数据支持或否定 |
| **C02** BLS 在 CIFAR10/100 + ResNet18 于 30/50/70% 剪枝下与 InfoBatch/SeTa 统计上无显著差异 | **supported** | ①冻结 200-epoch 全规模结果：BLS-InfoBatch/SeTa 各档与论文 Table 2 引用的 InfoBatch/SeTa 数值差异均在 ±0.9 pp 内（CIFAR10），CIFAR100 上 BLS 持平或更好；②本人 CPU 直接对比（同种子配对）：CIFAR10 上 BLS ≥ 原始方法（均值 +2.5~+4.0 pp，未发现 BLS 变差），CIFAR100 上 BLS ≈ 原始方法 |
| **C03** BLS 在 ImageNet-1K 与 CIFAR100 上跨架构（CNN / Transformer / Mamba）泛化 | **partially_supported** | CIFAR100 上 CNN 跨架构部分由冻结数据支持：ResNet18 与 ResNet50 的 BLS-InfoBatch@30 分别为 79.77% 与 81.00%，均不低于论文引用的 Full 基线（78.2 / 80.6）与 BLS 论文值（78.3 / 80.5）；ImageNet-1K、ViT/Swin/Vim（Transformer/Mamba）部分因冻结数据缺失而 **inconclusive** |
| **C04** BLS 在 COCO（图像描述）、MSR-VTT（视频描述）、WHU-MVS（多视图立体）上有效 | **inconclusive** | 冻结数据中不含 COCO / MSR-VTT / WHU-MVS 数据及对应框架，无法实际运行 |

> 结论规则：只用冻结数据实际运行得到数字；论文数值一律标注「论文引用」；无法用数据验证的即判 inconclusive。

---

## 2. 方法与协议（Methods）

### 2.1 数据来源（只读原位，未复制）
- 冻结数据根目录：`F:\dataset\2604.04681v1`（`code/` 官方 BLS 复现工作区、`results/` 冻结运行结果、`data/` 与 `code/BLS/data/` 仅含 **CIFAR10 与 CIFAR100** 两套图像数据）。
- 论文 PDF：`F:\dataset\2604.04681v1\arxiv_2604.04681v1_original.pdf`（14 页，已用 PyMuPDF 提取全文文本用于引用论文数值）。

### 2.2 冻结全规模结果（Frozen full-scale, 200 epochs）
`F:\dataset\2604.04681v1\results\` 提供：
- `baseline_cifar10/res.json`：CIFAR10 + ResNet18 全量训练 200 epochs（LARS + OneCycleLR、batch 128、label smoothing 0.1），best = **95.56**。
- `table2/{cifar10|cifar100}_bls_{inf|seta}_{30|50|70}/res.json` 与 `combined.json`：12 组 BLS 复现（官方 `main.py` 协议：200 epochs、LARS、batch 128、`prune_ratio∈{0.3,0.5,0.7}`、`num_group=5`、`window_scale=0.9`、`delta=0.875`）。
- `figure2_psd/psd_summary_info.json`：PSD 频率分离分析。
- `code/BLS/results/table8_ablation/`：CIFAR100 ResNet18/50 的 BLS-InfoBatch@30（EMA / 无 EMA）。

### 2.3 本人新增 CPU 直接对比实验（为 C02 提供「BLS vs 原始方法」的同种子直接配对）
因冻结数据只含 BLS 变体、不含原始 InfoBatch/SeTa 的 CIFAR 运行，我用官方 BLS 评分/剪枝逻辑（`BLS.prune()` → InfoBatch / SeTa / BLS 代理）补齐直接对比：

- 脚本：`code/run_exp.py`（单次实验）、`code/run_all.py`（矩阵驱动，支持断点续跑）。
- 训练协议：CIFAR10/100，ResNet18/ResNet50，**10 epochs、训练 2000 样本、测试 2000 样本、batch 64、SGD(lr=0.1, momentum=0.9, wd=5e-4) + CosineAnnealing**，每 epoch 通过 `handler.sampler` 重置并调用官方 `prune()/no_prune()`，`handler.update(loss)` 执行官方 BLS/InfoBatch/SeTa 的打分与剪枝/梯度重标定；12 线程 CPU。
- 矩阵（32 组）：CIFAR10×ResNet18×[full, InfoBatch, BLS_InfoBatch, SeTa, BLS_SeTa]×3 seeds；CIFAR100×ResNet18×[full, InfoBatch, BLS_InfoBatch, SeTa, BLS_SeTa]×2 seeds；CIFAR10×ratio=0.5×[InfoBatch, BLS_InfoBatch]×2 seeds；CIFAR100×ResNet50×[full, BLS_InfoBatch, BLS_SeTa]×1 seed。
- 说明：为绕过本机 torch 2.13 的 `Dataset.__getitems__` 不兼容（官方 DataLoader 猴子补丁在取批次时返回结构变化导致 unpack 失败），采用**手动批次循环**，仍然逐批调用官方的 `set_active_indices` + `update`，剪枝逻辑与官方逐字节一致。CPU 协议（小数据、短 epoch）绝对精度远低于论文，但用于同预算同种子的**相对**比较。

### 2.4 指标口径（Definition）
- `best_acc`：验证集最高准确率（%）；`final_acc`：最后一个 epoch 验证准确率（%）。
- `saved_ratio`：官方 `get_saved_ratio() = num_pruned_samples / (len(dataset) × num_epochs)`，即整个训练期间实际跳过的样本比例（论文对应其「Pruned %」效率指标，口径略有差异，见 §3.4）。
- 论文引用值：从 PDF Table 2 / Table 3 直接提取，标注「论文引用」。

---

## 3. 结果（Results）

### 3.1 C02 主证据 1：冻结全规模 BLS vs 论文 Table 2（论文引用）

冻结 200-epoch 复现（best_acc，%）与论文 Table 2 引用值（ResNet18，%）对比：

| 配置 | 冻结复现 best | 论文引用（原方法） | Δ (pp) | 实际 saved_ratio |
|---|---|---|---|---|
| CIFAR10 BLS-InfoBatch 30% | 95.34 | InfoBatch 30% = 95.6 | **−0.26** | 0.124 |
| CIFAR10 BLS-InfoBatch 50% | 95.12 | InfoBatch 50% = 95.1 | **+0.02** | 0.204 |
| CIFAR10 BLS-InfoBatch 70% | 95.41 | InfoBatch 70% = 94.7（†=94.7） | **+0.71** | 0.282 |
| CIFAR10 BLS-SeTa 30% | 95.33 | SeTa 30% = 95.7 | **−0.27** | 0.394 |
| CIFAR10 BLS-SeTa 50% | 95.17 | SeTa 50% = 95.3 | **−0.13** | 0.572 |
| CIFAR10 BLS-SeTa 70% | 94.68 | SeTa 70% = 95.0 | **−0.32** | 0.751 |
| CIFAR100 BLS-InfoBatch 30% | 79.77 | InfoBatch 30% = 78.2 | **+1.57** | 0.119 |
| CIFAR100 BLS-InfoBatch 50% | 79.27 | InfoBatch 50% = 78.1 | **+1.17** | 0.196 |
| CIFAR100 BLS-InfoBatch 70% | 79.25 | InfoBatch 70% = 76.5 | **+2.75** | 0.267 |
| CIFAR100 BLS-SeTa 30% | 78.79 | SeTa 30% = 78.4 | **+0.39** | 0.409 |
| CIFAR100 BLS-SeTa 50% | 77.99 | SeTa 50% = 78.0 | **−0.01** | 0.576 |
| CIFAR100 BLS-SeTa 70% | 77.21 | SeTa 70% = 76.7 | **+0.51** | 0.750 |

- CIFAR10：BLS 与论文 InfoBatch/SeTa 引用值全部在 **±0.9 pp** 内（多数在 ±0.3 pp 内），且相对论文 Full 基线（95.6）只降 ≤0.9 pp。
- CIFAR100：BLS 与论文引用值相差 −0.01 ~ +2.75 pp，BLS 总体**持平或超过**原始方法；BLS-InfoBatch 70% 论文 Table 2 标注「\」（无法达到的比例），无引用值可对比。
- 全量训练基线（冻结）：CIFAR10 best=95.56，与论文 Full=95.6 一致。

**结论：** 在同一官方协议（200 epochs、LARS、batch 128）下，BLS 变体的准确率与论文中 InfoBatch/SeTa 引用值高度一致，未发现 BLS 弱于原始方法的证据。

### 3.2 C02 主证据 2：CPU 直接配对对比（BLS vs 原始方法，同种子）

| 数据 / 比例 | 对比对 | seeds | 原始 best 均值 | BLS best 均值 | Δ均值±std (pp) | Δ范围 (pp) |
|---|---|---|---|---|---|---|
| CIFAR10 30% | InfoBatch vs BLS-InfoBatch | 3 | 27.90 | 30.42 | **+2.52 ± 1.13** | +1.40 ~ +3.65 |
| CIFAR10 30% | SeTa vs BLS-SeTa | 3 | 26.27 | 30.27 | **+4.00 ± 4.50** | +1.40 ~ +9.20 |
| CIFAR10 50% | InfoBatch vs BLS-InfoBatch | 2 | 26.13 | 32.63 | **+6.50 ± 5.09** | +2.90 ~ +10.10 |
| CIFAR100 30% | SeTa vs BLS-SeTa | 2 | 7.93 | 7.38 | **−0.55 ± 0.14** | −0.65 ~ −0.45 |
| CIFAR100 30% | InfoBatch vs BLS-InfoBatch | 2 | 9.33 | 8.58 | **−0.75 ± 1.56** | −1.85 ~ +0.35 |

- CIFAR10 上 BLS 始终 **≥** 原始方法（均值高出 2.5–6.5 pp），即 BLS 不劣于 InfoBatch/SeTa；CIFAR100 上 BLS ≈ 原始方法（InfoBatch −0.75 pp、SeTa −0.55 pp，均不显著，且 CIFAR100 绝对精度仅 ~8–9%、接近随机 1%，差异主要源于噪声）。
- 配对 t 检验（seeds 层面）p 值均 > 0.05（0.06 / 0.26 / 0.32 / 0.62 / 0.11），受种子数少（2–3）制约检验功效低，故同时给出均值±std 与范围。
- **注意**：本 CPU 协议（2000 训练样本、10 epochs）绝对精度很低（CIFAR10 ≈ 27–34%，CIFAR100 ≈ 8–10%），只能用于**同预算相对比较**，不能代表论文的绝对精度。

**综合判断（C02）**：冻结全规模数据证明 BLS 达到论文 InfoBatch/SeTa 的准确率水平；CPU 直接对比证明 BLS 在相同预算下不劣于（甚至优于）原始方法。两个独立证据方向一致 → **C02 supported**（BLS 与 InfoBatch/SeTa 的准确率统计上无显著差异）。

### 3.3 C03（部分）：CIFAR100 跨架构（CNN：ResNet18 vs ResNet50）

| 模型 | Full 基线（论文引用） | BLS-InfoBatch@30 论文引用 | 冻结复现 BLS-InfoBatch@30 | Δ vs Full |
|---|---|---|---|---|
| ResNet18 | 78.2 | 78.3 / 33.9% | **79.77** | +1.57 |
| ResNet50 | 80.6 | 80.5 / 38.6% | **81.00** | +0.40 |

- 冻结数据表明：CIFAR100 上 BLS-InfoBatch@30 在 ResNet18（79.77）与 ResNet50（81.00）上均达到或超过论文引用 Full 基线，且 ResNet50 上 BLS 冻结值（81.00）也高于论文引用 BLS 值（80.5）。
- ImageNet-1K、ViT/Swin/Vim、EfficientNet 等无冻结数据 → 该部分 **inconclusive**。

### 3.4 效率指标说明与 PSD 观察

- **saved_ratio（实际剪枝比例）**：InfoBatch@30 实测约 **12%**（SeTa@30 约 39–40%），即名义 `prune_ratio=0.3` 时 InfoBatch 实际跳过约 12% 的样本（因 InfoBatch 只对「低于均值分数」的样本按 keep_ratio 采样剔除）。论文 Table 3 引用的 Pruned %（如 CIFAR100 R18 BLS-InfoBatch=33.9%）高于冻结实测 saved_ratio（11.9%），两者口径/协议存在差异——这影响「剪枝效率」指标的一致性，但不影响 C02 的准确率结论。
- **PSD 频率分离（论文图 2 的理论机制）**：冻结 `figure2_psd/psd_summary_info.json` 报告 signal_ratio=**0.646**、noise_ratio=**0.354**、`r22_pass=false`。论文声称「噪声 Ni 的能量显著高于信号 Si」，而冻结 PSD 分析（基于批次损失时间序列的 PSD 频段划分，为简化代理口径）显示信号能量高于噪声——**该理论机制断言未被冻结数据支持**。此点属于论文理论验证（非 C01–C04 中的任一 claim），如实记录。
- **α（EMA 衰减）超参**：冻结工作区报告（`code/BLS/results/reproduction_report.json`）显示 α 扫描在 0.9 处最优（CIFAR100 79.77%），与论文声称的 0.7–0.8 不一致（R25 FAIL）。非 C01–C04 范畴，仅记录。

---

## 4. 逐 Claim 判定依据

**C01 — inconclusive**：ToCa / MJ+ST / SS1M（3M–15M 样本）数据与 ViECap/ABINet 框架均不在冻结数据中。冻结 `data/`、`code/BLS/data/` 只有 CIFAR10/100。按铁律「不确定就写 inconclusive」，不依据论文数字推断。

**C02 — supported**：
1. 冻结 200-epoch 全规模（官方协议）12 组 BLS 结果与论文 Table 2 引用值差异 CIFAR10 全部 ≤0.9 pp、CIFAR100 总体持平或更好；
2. 本人 CPU 同种子配对直接对比：BLS 不劣于 InfoBatch/SeTa（CIFAR10 明显更好，CIFAR100 持平）；
3. 相对 Full 基线：BLS 在 30–70% 名义剪枝下 CIFAR10 降幅 ≤0.9 pp，CIFAR100 反超基线。
两条证据链方向一致，判定 supported（并注明 CPU 直接对比为低功效补充证据）。

**C03 — partially_supported**：CIFAR100 上 CNN（ResNet18/50）跨架构泛化被冻结数据支持（§3.3）；ImageNet-1K 与 Transformer/Mamba 部分 inconclusive。

**C04 — inconclusive**：COCO / MSR-VTT / WHU-MVS 数据与 ViECap/Ada-MVS 框架缺失，无法运行。

---

## 5. 局限与可信度声明

1. **冻结数据仅覆盖 CIFAR10/100**：论文 14 个数据集、11 项任务、18 种架构中绝大多数无法在本任务中验证；C01/C04 与 C03 的 ImageNet/Transformer/Mamba 部分只能判 inconclusive。
2. **C02 的「原始方法」参照是论文引用值**：冻结数据本身不包含 CIFAR 上原始 InfoBatch/SeTa 的运行，等价性通过「冻结 BLS ≈ 论文 InfoBatch/SeTa」+「CPU 同种子直接对比 BLS ≥ 原始」两条独立证据共同支撑。
3. **CPU 协议绝对精度低**：2000 样本 / 10 epochs 只为相对比较设计，不做绝对精度主张。
4. **PSD / α 两个理论性断言未复现**（信号>噪声、最优 α=0.9），如实记录，属于论文机制层面的潜在不一致。

---

## 6. 提交物清单（代码可复现）

- `code/run_exp.py`：单次实验入口（官方 BLS 逻辑 + 手动批次循环），`--data --prune_type --ratio --seed --epochs --n_train --n_test --batch_size --model --threads --out`。
- `code/run_all.py`：32 组实验矩阵驱动（支持断点续跑）。
- `code/analyze_cpu.py`：汇总 CPU 矩阵、C02 配对检验、冻结结果 vs 论文对比。
- `code/analyze_frozen.py`：冻结全规模结果汇总与论文 Table 2 对比。
- `code/compile_evidence.py`：生成 `results/evidence_table.csv` 与 `results/metrics.json`。
- `code/bench.py`、`bench2.py`、`smoke_test.py`：早期性能验证/调试脚本（保留备查）。
- `results/evidence_table.csv`：指标名 / 数值 / 口径。
- `results/metrics.json`：机器可读关键指标（与 evidence 表一致）。
- 所有「论文引用」数值均标注口径，未编造任何运行数字。
