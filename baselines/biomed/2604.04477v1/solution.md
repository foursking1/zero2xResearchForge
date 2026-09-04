# MVis-Fold（arXiv 2604.04477v1）科学结论复现与 Claim 判定

## 0. 摘要

基于**冻结数据**（`F:/dataset/2604.04477v1`，含训练完成的 checkpoint `checkpoints/stage1_best.pth`、参考复现源码 `src/`、参考 artifacts）**实际运行**得到本报告全部数字。检验 TASK 中 4 条论文 claim（C01–C04）。

**核心结论**：在冻结合成测试集（n=50）上，论文声称的性能指标**均未复现**。
- **C01（分割指标 Dice≥0.95 等 + 优于基线）→ contradicted**：实测 Dice=0.830（<0.95）、Sens=0.936（略低于 0.94）、Spec=0.990、Acc=0.988；且 MVis-Fold Dice 显著低于我训练的 Tier-1 基线 Simple 3D U-Net（Dice=1.0）与 TripoSR 启发式代理（Dice=0.920）。
- **C02（VD 误差<0.02 mm/mm³ 且 MD 误差<3 μm，>1000×/50× 改进）→ contradicted**：实测 VD 误差=27.0 mm/mm³（≫0.02）、MD 误差=4.10 μm（>3）；改进倍数仅 3.33× 与 0.57×（且 MD 一项 MVis 显著**差于** 2D SRUS）。
- **C03（血管密度与组织病理学金标准 Pearson r≥0.85, p<0.01）→ inconclusive**：冻结数据**不含组织病理学金标准**，论文 r=0.892 无法直接验证；最近的合成金标准代理 r=0.132（p=0.362）远低于阈值，可用证据不支持该 claim。
- **C04（内验证 Dice≥0.95）→ contradicted**：实测内验证 Dice=0.826（<0.95）。

所有实测数字均由本次运行得到（`agent_solution/code/`，结果见 `agent_solution/results/`）；论文声称值仅作对比，明确标注“论文引用”。

---

## 1. 数据与口径

### 1.1 冻结数据（原位读取，未复制大文件）
| 条目 | 说明 |
|---|---|
| `checkpoints/stage1_best.pth` | MVis-Fold small 模型权重（stage=1_diverse，epoch=174，训练时最优验证 Dice=0.8261，shape=16×32×32） |
| `checkpoints/best_model.pth` | 大模型权重（1.2 GB，未用于本次评估） |
| `src/` | 参考复现源码：`models/mvisfold.py`、`data/synthetic.py`、`evaluate/metrics.py`、`evaluate/vessel_analysis.py`、`baselines/sparseneus_wrapper.py`（含 TripoSR/OpenLRM 启发式代理与 Simple 3D U-Net 基线） |
| `artifacts/table1_segmentation.json` 等 | 参考复现 artifacts（仅作对比参考，非本次提交内容） |
| `arxiv_2604.04477v1.pdf` | 论文原文 |

**重要说明**：冻结数据的“数据”是**合成血管体模**（`src/data/synthetic.py` 生成，含精确已知的血管密度/直径金标准），而非论文所述 126 只小鼠、16,780 张 SRUS 真实图像 + 组织病理学金标准。因此本报告所有指标均标注为 *synthetic-only*。

### 1.2 评估协议（与参考复现一致，全部确定性可复现）
- 模型：`build_model(in_channels=6, use_small=True)`，加载 `stage1_best.pth`。
- 测试集：`VascularTreeGenerator(shape=(16,32,32), max_branches=15, seed=300+i)`，i=0..49（n=50）；SRUS 通道 `generate_sruse_channels(noise_level=0.1, seed=300+i+5000)`。
- 内验证集（C04）：训练协议确定性重算，`max_branches=10`、noise=0.05、n=20。
- 分割指标：Dice / Sensitivity / Specificity / Accuracy / HD95（95 百分位对称 Hausdorff），阈值固定 0.5（`src/evaluate/metrics.py`）。
- 参数误差：`src/evaluate/vessel_analysis.py` 的 `compare_parameters`，与合成金标准比较：血管密度误差（VD error，mm/mm³）、平均直径误差（MD error，μm）；2D SRUS 直接测量 = 逐 2D 层面骨架/距离变换的面积分数估计（单位不匹配，见 §4 局限）。
- 相关分析：Pearson r（模型估计值 vs 合成金标准）。
- 统计检验：Shapiro-Wilk（Dice 正态性）、Wilcoxon 符号秩（成对比较）、Cohen's d（计算并存入 metrics.json）、Bootstrap 95% CI（2000 次重采样）。

### 1.3 运行环境与复现
- Python 3.13.12（torch 2.13.0+cpu，numpy，scipy，scikit-image，einops，tqdm，PyYAML）。
- 数据根目录：`F:/dataset/2604.04477v1`（脚本默认值）。
- 运行命令：
  ```bash
  python agent_solution/code/analyze.py --root F:/dataset/2604.04477v1 --n-test 50 --outdir agent_solution/results   # 主评估（Table1/Table2/相关/内验证/统计/claim 判定）
  python agent_solution/code/robustness.py --root F:/dataset/2604.04477v1 --outdir agent_solution/results            # 多 seed 稳健性
  python agent_solution/code/noise_sensitivity.py --root F:/dataset/2604.04477v1 --outdir agent_solution/results     # 噪声敏感性
  python agent_solution/code/train_baseline.py --root F:/dataset/2604.04477v1 --outdir agent_solution/results        # Tier-1 基线训练+测试
  ```

---

## 2. 结果

### 2.1 Table 1 — 分割性能（冻结合成测试集，n=50）
| 方法 | Dice | Sens | Spec | Acc | HD95 (voxel) | 时间 (s/样本) |
|---|---|---|---|---|---|---|
| **MVis-Fold (small)** | **0.8297 ± 0.0808** | **0.9360 ± 0.0345** | 0.9901 ± 0.0039 | 0.9882 ± 0.0043 | 1.00 | 0.014 |
| Simple 3D U-Net（Tier-1 基线，本次训练） | 1.0000 ± 0.0000 | 1.0000 | 1.0000 | 1.0000 | 0.00 | — |
| TripoSR 代理（启发式） | 0.9198 ± 0.0522 | 0.8617 | 0.9997 | 0.9959 | 0.64 | 0.001 |
| OpenLRM 代理（启发式） | 0.7782 ± 0.1853 | 0.6935 | 0.9984 | 0.9906 | 2.22 | 0.004 |
| 论文引用（真实数据） | 0.959 ± 0.034 | 0.951 ± 0.038 | 0.957 ± 0.025 | 0.962 ± 0.053 | 3.2 ± 1.1 | 8.3 |

- MVis-Fold Dice 95% CI = [0.8082, 0.8517]（bootstrap, 2000 次）。
- **与参考 artifacts 交叉验证**：本次复现 Dice=0.8297 / Sens=0.9360 / Spec=0.9901 / Acc=0.9882，与冻结 `artifacts/table1_segmentation.json`（0.8297/0.9361/0.9901/0.9882）一致，确认评估协议无偏差。

### 2.2 Table 2 — 参数精度（对合成金标准，n=50）
| 方法 | VD 误差 (mm/mm³) | MD 误差 (μm) |
|---|---|---|
| 2D SRUS 直接测量 | 89.80 ± 17.07 | 2.33 ± 2.64 |
| **MVis-Fold (3D)** | **26.998 ± 19.06** | **4.104 ± 2.51** |
| 改进倍数（SRUS/MVis） | 3.33× | 0.57× |
| 论文引用（vs 组织病理） | 0.012 ± 0.006 | 2.16 ± 0.5 |
| 论文引用倍数 | 1353× | 55× |

合成金标准范围：GT 密度 89.83 ± 17.07 mm/mm³（远高于论文真实值 2.847 mm/mm³，因体模体积小）；GT 直径 29.11 ± 7.40 μm。

### 2.3 相关分析（对合成金标准）
| 参数 | MVis-Fold r (p) | 2D SRUS r (p) | 论文引用 r |
|---|---|---|---|
| 血管密度 | 0.1318 (p=0.362) | 0.0658 (p=0.650) | 0.892 (p<0.001，vs 组织病理) |
| 平均直径 | 0.8793 (p≈4.5e-17) | 0.8926 (p≈3e-18) | — |

### 2.4 内验证集（C04）
| 口径 | Dice |
|---|---|
| 确定性内验证块（n=20, max_branches=10, noise=0.05） | 0.8262 ± 0.0949（95% CI [0.6423, 0.9303]） |
| checkpoint 记录的训练最优验证 Dice | 0.8261 |
| 论文引用（内部验证） | 0.964 ± 0.041 |

### 2.5 稳健性
- 噪声敏感性（同 50 个测试样本，噪声 0.05/0.1/0.3）：Dice = 0.8286 / 0.8297 / 0.8275，Sens = 0.9390 / 0.9360 / 0.9211。性能随噪声平滑下降（无灾难性崩塌）。
- 多测试 seed 块（seed 100/200/300/400 × 20 样本）：Dice = 0.806 / 0.819 / 0.849 / 0.827，池化 0.825 ± 0.071（n=80）。跨 seed 稳定在 ~0.81–0.85，均 < 0.95。

### 2.6 统计检验（由逐样本数据计算）
- Shapiro-Wilk（MVis Dice）：W=0.9093，p=0.0010 → 非正态。
- Wilcoxon 符号秩（VD 误差 MVis vs 2D SRUS）：stat=1.0，p≈3.6e-15 → MVis VD 误差显著更低（支持 MVis 在 VD 上的优势）。
- Wilcoxon 符号秩（MD 误差 MVis vs 2D SRUS）：stat=225.0，p≈3.1e-5 → MVis MD 误差显著**更高**（与 C02 声称的 2D 改进方向相反）。
- Wilcoxon 符号秩（Dice MVis vs TripoSR 代理）：stat=0.0，p≈1.8e-15 → MVis 显著**低于** TripoSR 代理。

---

## 3. Claim 判定

### C01 — MVis-Fold 达到 Dice≥0.95, Sens≥0.94, Spec≥0.95, Acc≥0.95，且优于 SparseNeuS/OpenLRM/TripoSR
**判定：contradicted**
- 实测：Dice=0.830（<0.95，**关键阈值未达**），Sens=0.936（略低于 0.94），Spec=0.990（≥0.95 ✓），Acc=0.988（≥0.95 ✓）。
- “优于基线”子项：在冻结合成数据上，MVis Dice（0.830）< TripoSR 代理（0.920）< 本次训练的 Tier-1 基线 Simple 3D U-Net（1.000），仅优于 OpenLRM 代理（0.778）；Wilcoxon 检验显示 MVis 显著低于 TripoSR 代理。
- 依据：§2.1、§2.6；注：冻结数据中的基线为启发式代理与 Simple UNet（域与论文原始的 SparseNeuS/OpenLRM/TripoSR 模型不完全等价），论文 Table 1 的原始基线对比无法直接复现，但可用的可比实现均不落后于 MVis-Fold。

### C02 — VD 误差<0.02 mm/mm³ 且 MD 误差<3 μm，且较 2D SRUS 有 >1000 倍与 >50 倍改进
**判定：contradicted**
- 实测：VD 误差=27.0 mm/mm³（≫0.02），MD 误差=4.10 μm（>3 μm）；改进倍数 VD=3.33×、MD=0.57×，远低于 1000×/50×。
- MD 子项方向相反：MVis MD 误差显著高于 2D SRUS（Wilcoxon p≈3.1e-5）。
- 依据：§2.2、§2.6；注意 2D SRUS 参考为面积分数口径（单位不匹配），故 VD 改进倍数仅具方向性；论文的 1353×/55× 是对组织病理金标准测得，冻结数据无法复现。

### C03 — 提取的血管密度与组织病理学金标准 Pearson r≥0.85 (p<0.01)
**判定：inconclusive**（论文所称与组织病理金标准的相关无法直接验证）
- 冻结数据**不含组织病理学金标准**，因此论文的 r=0.892 (p<0.001) 无法直接复现。
- 最近似的可用测试（与合成金标准相关）：VD r=0.132（p=0.362），远低于阈值 r≥0.85 且 p 未达 <0.01；可用证据不支持该 claim，但严格来说与组织病理的精确表述不可证伪/证实。
- 依据：§2.3。

### C04 — 内验证集 Dice≥0.95
**判定：contradicted**
- 实测：确定性内验证块 Dice=0.8262（95% CI [0.6423, 0.9303]）；checkpoint 记录的训练最优验证 Dice=0.8261。均 < 0.95。
- 依据：§2.4。

---

## 4. 局限性与诚实说明

1. **合成数据域差异（最大局限）**：所有指标基于合成血管体模（16×32×32），未包含真实 SRUS 成像的散斑、微泡动力学、组织散射等物理，也未包含论文的 126 只小鼠真实数据。真实数据上的性能预期更低（域间隙更大）。
2. **模型规模**：冻结 checkpoint 为 small 模型（2 层 Transformer，embed=128），论文架构超参数多数未给出（`src/` 复现为近似实现）。
3. **单位口径不匹配（C02）**：`compute_2d_sruse_estimate` 返回 2D 面积分数，直接与 3D 密度（mm/mm³）做差，单位不一致，故 VD 改进倍数仅方向性参考；MD 的比较口径一致（均为 μm），且方向相反。
4. **基线不可直接复现（C01）**：SparseNeuS/OpenLRM/TripoSR 原始模型不在冻结数据中；仅可用启发式代理与 Simple 3D U-Net。合成任务上 MVis 不优于这些可比基线，说明该合成任务的“基线对比”不能作为论文 Table 1 的等价复现。
5. **组织病理缺失（C03）**：无组织病理切片金标准，C03 的精确表述不可证伪/证实，故判 inconclusive。
6. **内验证协议（C04）**：训练时验证为随机批采样（`src/.../train.py` 中 seed 未固定），checkpoint 记录的 0.8261 与确定性重算的 0.8262 基本一致，均远低于 0.95，不影响判定。

---

## 5. 文件清单

| 文件 | 说明 |
|---|---|
| `code/analyze.py` | 主评估：加载冻结 checkpoint → 生成确定性测试集 → Table1/Table2/相关/内验证/统计检验/claim 判定 → 输出 results/*.json |
| `code/robustness.py` | 多 seed 稳健性（seed 100/200/300/400 × 20 样本） |
| `code/noise_sensitivity.py` | 噪声 0.05/0.1/0.3 敏感性 |
| `code/train_baseline.py` | 训练 Tier-1 基线（Simple 3D U-Net）并在同一测试集上评估 |
| `results/metrics.json` | 关键指标 + claim 判定 + 统计检验（机器可读） |
| `results/evidence_table.csv` | 证据表（claim_id, metric, value, definition） |
| `results/table1_segmentation.json` | 分割指标（机器可读） |
| `results/table2_parameters.json` | 参数精度（机器可读） |
| `results/internal_validation.json` | 内验证 Dice |
| `results/robustness.json` | 多 seed 稳健性 |
| `results/noise_sensitivity.json` | 噪声敏感性 |
| `results/baseline_results.json` | Tier-1 基线测试结果 |
| `results/per_sample_*.csv` | 逐样本明细 |

> 所有结果标注：**SYNTHETIC DATA ONLY — NOT VALIDATED ON BIOLOGICAL TISSUE**。论文数值仅以“论文引用”名义列出作对比，不参与任何实测指标。
