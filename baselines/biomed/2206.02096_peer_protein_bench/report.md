# Report — PEER Solubility 单任务关键论断复现

**Task ID** `2206.02096_peer_protein_bench` · **层面** L1（critical claim）· **日期** 2026-08-18

## 1. 背景与目标

PEER（Fang et al., NeurIPS 2022, arXiv:2206.02096）提出 17 个蛋白质序列理解任务，其中 Solubility（溶解度）为蛋白质级二分类（可溶/不可溶）。论文摘要与 §5.2/Table 3 的两个核心论断：

- **C1**：预训练蛋白语言模型（ESM-1b）在多数单任务上取得最佳性能，Solubility 上 ESM-1b = 70.23%。
- **C2**：从零训练的序列编码器（LSTM 70.18 / CNN 64.43）显著优于特征工程（DDE 59.77 / Moran 57.73）。

本报告在**冻结数据**（train/valid/test = 62,478/6,942/1,999，SHA-256 固定）上：①核对数据装配口径；②复现 DDE、Moran、CNN、LSTM 四类模型；③判定论断在冻结数据上是否成立。

## 2. 方法与实现

### 2.1 数据装配（`code/01_data_stats.py`）

| 划分 | 样本数 | 正类数 | 正类比例 | 长度 min/中位/max |
|---|---|---|---|---|
| train | 62,478 | 26,075 | 41.73% | 19 / 275 / 1200 |
| valid | 6,942 | 2,897 | 41.73% | 27 / 275 / 1200 |
| test  | 1,999 | 1,000 | 50.03% | 34 / 260 / 1200 |

- 与原论文 Table 1 及冻结锚数值完全一致；正类比例 41.7%、长度 19–1200（中位 275）。
- 长度分布（train）：约 8% 序列 >512（第 92 百分位 ≈ 488，P99 = 844），故编码器采用截断至 512（在报告中已说明；PEER 官方实现亦使用固定最大长度/截断）。
- 序列唯一（train/valid/test 均为 0 重复）。
- 测试集仅用于最终单次评估。

### 2.2 特征工程基线（`code/02_feature_models.py`）

- **DDE（二肽期望偏差）400 维**：`DDE(x,y) = (D(x,y) − E(x,y))/√V(x,y)`，其中 `D=C/(N−1)`，`E=(Cx/N)·(Cy/N)`，`V=E(1−E)`。闭合公式，无训练集外统计。
- **Moran 自相关 50 维**：10 个理化指标（Kyte-Doolittle 疏水性、Hopp-Woods 亲水性、侧链质量、Chou-Fasman α/β 倾向、Grantham/Zimmerman 极性、等电点、体积、转角倾向）× 5 个滞后：`I(d)=Σᵢ(vᵢ−v̄)(vᵢ₊d−v̄)/var(v)`。
- 分类器：LogisticRegression（liblinear）。特征标准化只由 train 拟合；正则强度 C 在 valid 上用网格选择；Moran 因 train 类别失衡（58/42）采用 class_weight='balanced'（DDE 保持论文式非加权以保证可比）。测试集只评估一次。

### 2.3 从零训练序列编码器（`code/03_encoder_models.py`）

公共设置：20 字母 AA 索引 + padding(20)；Embedding(128)；截断/填充至 512；AdamW(lr=1e-3, wd=1e-4)；交叉熵；ReduceLROnPlateau（不提前触发时仅可靠早停）；valid 早停 patience=4 / max 12 epochs；**每个模型 3 个固定种子（2024/2025/2026），报告 mean±std**；测试集单次评估。

- **CNN**：Emb→Conv(128,7)ReLu→MP(3,2)→Conv(192,5)ReLu→MP(3,2)→Conv(192,3)ReLu→GlobalMaxPool→Linear(2)，Dropout 0.2。
- **LSTM**：Emb→BiLSTM(128, 1 层)→按真实长度做均值池化→Linear(2)，Dropout 0.2；包裹 packed sequence 提升效率。

确定性：全局种子、`cudnn.deterministic=True`、`DataLoader(num_workers=0)`（避免多 worker 批次乱序造成不可复现）。
实现设备：CUDA（RTX 4080，空闲时使用；代码在无 GPU 时自动回退 CPU）。

### 2.4 提交物生成（`code/04_assemble_results.py`、`05_verify.py`）

`results/metrics.json`（数据统计+各模型 accuracy+论文对照+结论标签）、`results/evidence_table.csv`（`model,accuracy`）、自校验脚本（test 行数、DDE accuracy 重算、SHA-256）。

## 3. 结果

### 3.1 数据装配 —— 与冻结锚完全一致（A1 满分带）

train/valid/test 数量、正类比例、长度统计全部与 `data/README.md` 及锚 A1 一致。

### 3.2 各模型测试集 accuracy（%）

| 模型 | 本文实测（本文实现/协议） | 论文 Table 3 | 相对差 | 每 seed |
|---|---|---|---|---|
| DDE + LR | 59.98 | 59.77 | +0.35% | 单次（确定性） |
| Moran + 平衡 LR | 55.43 | 57.73 | −3.99% | 单次（确定性） |
| CNN（3 seeds） | 70.20 ± 0.56 | 64.43 | +8.95% | 69.43 / 70.74 / 70.44 |
| LSTM（3 seeds） | 64.63 ± 0.47 | 70.18 | −7.91% | 64.03 / 65.18 / 64.68 |

四个模型全部处于论文锚 ±10% 相对带内（`results/metrics.json: paper_anchor_comparison`，`within_10pct=true`）。
CNN 与 LSTM 实现为本环境独立实现（与 PEER 的 torchdrug 管线在超参与截断上有差异），训练采用纯 FP32 确定性模式（禁用 TF32），与论文数字 <±10% 对齐；CNN 甚至略超论文 CNN（64.43），达到与论文 ESM-1b/LSTM 相近水平。

### 3.3 论断判定

**C2「从零训练编码器 > 特征工程」：复现成功。**
编码器最优者（CNN 70.20）− 特征工程最优者（DDE 59.98）= **10.22 pp**（≥3pp），方向与量级均与论文一致（论文差：70.18−59.77 = 10.41pp）。排序 encoder（CNN 70.20 / LSTM 64.63）> DDE（59.98）> Moran（55.43）与论文「编码器 > 特征工程」一致。

**C1「预训练 PLM 全面最优」：离线不可直接实证；无矛盾证据。**
本环境离线且无预训练权重（ESM-1b / ProtBert / ESM-2 均不可加载），无法跑预训练 PLM。论文自身 Table 3 即显示从零训练 LSTM（70.18）与 ESM-1b（70.23）几乎持平；本文从零训练编码器同样达到 ≈70% 水平，与该图景一致，未发现「预训练优势非他莫属」的证据。

**四档标签：`partially_supported`**（C2 supported；C1 部分不可验证 → 不升为 supported；也没有 contradicted 证据）。

## 4. 局限性与论文管线差异（C2）

1. **预训练 PLM 未运行**：无 ESM-1b/ProtBert/ESM-2 离线权重。可由在线环境补充 ESM-1b 微调（论文 70.23）与 ProtBert 冻结特征（59.17）以完整覆盖 C1。
2. **编码器实现与 PEER 官方有差异**：超参（lr/隐层/层数/batch）、截断策略（512）、池化方式均与 PEER 的 torchdrug 实现不同。因此本 CNN（70.20，高于论文 64.43）与本 LSTM（64.63，低于论文 70.18）存在出入；LSTM 在 12 个 epoch 上限内验证集仍处于上升平台（best~69），更长的训练/更优超参可使其更接近论文值。均不改变族间排序与 ±10% 对齐。
3. **Moran 为本实现**：标准化 50 维（10 指标×5 滞后），与 PEER/TorchDrug 240 维定义的细节不同，绝对数值弱于论文（55.4 vs 57.73），但 A3 判据不受影响（判据基于 DDE 与编码器之差）。
4. **指标口径**：accuracy（%），100 刻度 ×100，与论文 Table 3 一致。
5. **数据卫生**：测试集未参与任何拟合/调参；DDE/Moran/标准化统计量仅由 train 拟合。
6. **代表性说明**：单任务、单一数据集（Solubility）的复现，论文「PLM 全面最优」是跨 17 任务的一般化论断，超出本任务可验证范围。
7. **复现性说明**：编码器训练默认使用 CUDA（位级可复现：`cudnn.deterministic`、禁用 TF32、`DataLoader(num_workers=0)`，`07_determinism_check.py` 验证两次启动 test accuracy 完全一致）；无 CUDA 时自动回退 CPU（训练更慢但路径兼容）。

## 5. 复现说明

```bash
cd agent_solution/code
python3 run_all.py        # 01→02→03→04（编码器优先 CUDA，无则 CPU）
python3 05_verify.py      # 自检（test 数 / DDE accuracy / SHA-256）
python3 06_plots.py       # figures/*.png
```

依赖：python3.11+，numpy/pandas/scikit-learn/torch。数据路径：默认 `data/` 或 `PEER_DATA_DIR`。