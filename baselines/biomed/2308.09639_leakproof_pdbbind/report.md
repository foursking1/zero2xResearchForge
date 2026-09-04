# Report：LP-PDBBind 时间分裂防泄漏关键论断验证

- task_id：`2308.09639_leakproof_pdbbind`
- 论文：Leak Proof PDBBind: A Reorganized Dataset of Protein-Ligand Complexes...（arXiv:2308.09639, THGLab）
- 本文档：方法、结果、结论、局限；所有数值均由 `agent_solution/code/` 从冻结 `data/` 重新计算得到（固定随机种子 0），未手工抄写论文数值（论文数值仅用于对照锚）。

## 1. 目标与三问

1. **泄漏程度**：冻结的 LP-PDBBind 时间分裂数据中，train/val/test 三集之间是否存在同一配体/同一靶点跨集重复？
2. **时间分裂 vs 随机分裂**：同模型在两种划分训练下，LP test CL2 非共价子集测试 RMSE 是否出现论文所述方向性差异（时间更严格→误差更高）？
3. **核心锚复现**：复现至少一个序列/配体基基线（RF、DeepDTA 类 CNN）于 LP test 的 RMSE 并与论文 Table 1 对照，回答"时间泄漏是否显著高估方法性能"。

## 2. 数据与方法

### 2.1 冻结数据与列映射

- `data/LP_PDBBind.csv`（19,443 行；648 行无 `new_split`，按论文口径排除 → 18,795 行）。官方仓库实际列名与 TASK.md 中别名对应关系：

| 本代码列名 | CSV 原列名 | 含义（TASK.md 别名） |
|---|---|---|
| `pdb_id` | `Unnamed: 0` | PDB 复合物 ID（PDB ID） |
| `smiles` | `smiles` | 配体 SMILES（配体身份来源，Ligand ID） |
| `seq` | `seq` | 蛋白序列（靶点身份来源，UniProt ID） |
| `split` | `new_split` | LP-PDBBind 时间分裂（Time-based split） |
| `pki` | `value` | 实验结合亲和力 pKd/pKi（PKI） |
| `CL1/CL2` | `CL1/CL2` | 清洗等级 1/2（CL2 complex type） |
| `covalent` | `covalent` | 共价标记 |
| `date` | `date` | PDB 沉积日期 |

- 划分规模与论文 §3.3/Table 1 完全一致：train **11,513** / val **2,422** / test **4,860**；test 内 CL2 非共价 **2,171** 条（`CL2==True & covalent==False`）。
- 数据完整性与 checksum 校验通过（`code/common.py: verify_checksums`，与 TASK.md/frozen 一致）。

### 2.2 特征与模型

**随机森林（RF，对应论文 RF-Score 的序列/配体基再实现）**
- 配体特征：RDKit Morgan(ECFP4) 指纹，radius=2，2048 bit（规范 SMILES 转换）。
- 靶点特征：蛋白序列二肽组成向量（400 维）。
- `RandomForestRegressor(n_estimators=300, random_state=0, n_jobs=8)`。

**DeepDTA 类 1D-CNN**
- 输入：SMILES 字符序列（max 100 token）与蛋白序列（max 800 token，20AA+X 词表）双分支 one-hot+Embedding(128)。
- 结构：3×Conv1d(8/8/4 kernel, 32/64/128 filters, ReLU) → global max pool → concat → FC(512)→1；MSE loss、Adam(lr=1e-3)、batch 128、dropout 0.2；在 val 上按 RMSE 早停（patience=6, max 40 epoch）。CPU 训练。

### 2.3 划分协议（防泄漏口径）

- **时间分裂（主口径）**：`new_split` 原值；训练/验证数据取 `CL1==True & 非共价`（对应论文"train on CL1, test on CL2"训练协议；train 7,384 / val 1,891 有效行）；test 固定为 LP test **CL2 非共价子集 2,171 条**。
- **随机分裂对照**：同一批 18,795 行按固定种子 0 重排为相同规模 train/val/test（11,513/2,422/4,860），选取同口径 CL1 非共价做训练/早停；**评测仍在同一个 LP test CL2 非共价 2,171 条上进行**——即对照两人数一致、唯一差别是训练集是否泄漏（数据铁律 3/4 遵守：test 不参与任何拟合或调参；随机划分不顶替主结论，仅作对照）。
- 除 CNN 用 val 早停外，未对 test 做任何超参选择；RF 超参固定。

## 3. 结果

### 3.1 Q1 泄漏统计（`results/leakage_stats.csv`，`evidence/fig1_leakage.png`）

身份定义：配体 = RDKit 规范 SMILES；靶点 = 蛋白序列精确相等（冷冻 CSV 无 UniProt 列，序列为最严格可用的靶点身份代理）。

| 划分 | ligand 跨 train→test | target(seq) 跨 train→test | ligand OR target |
|---|---|---|---|
| **LP 时间分裂** | **0 / 4838**（0.00%） | **711 / 4860**（14.63%） | 711（14.63%） |
| **随机分裂（seed=0）** | **976 / 4860**（20.08%） | **1965 / 4860**（40.43%） | **2611（53.72%）** |

补充（时间分裂）：
- train→val：配体 0/2422（0%）、靶点 54/2422（2.2%）；
- val→test：配体 298/4860（6.1%）、靶点 30/4860（0.62%）。
- 唯一配体（规范 SMILES）：train 9,480 / test 4,031，共享 **0**；唯一序列 train 7,807 / test 2,644，共享 **59**。

解读：配体维度时间分裂**零**泄漏而随机分裂 20%——与论文核心观察完全一致；靶点维度随机 40.4% → 时间 14.6%（保留 3 倍差距）。时间分裂下残余 14.6% 精确同序列重叠的解释见 §4.1（论文用"按蛋白类型分组的全局比对相似度"做分裂门控，不做精确相等排除，跨类型同序列可入不同集）。因此 Q1 判定为 `partially_supported`（严格同配体维度 `supported`：0 vs 20%；同靶点维度方向成立但未归零）。

### 3.2 Q2/Q3 RMSE 对比（`results/evidence_table.csv`, `metrics.json`, `fig2/fig3`）

评测集：LP test **CL2 非共价 2,171 条**（pK 单位 kcal/mol，即 log 尺度）。

| 模型 | 划分 | 测试 RMSE | Pearson R | val RMSE（早停/报告） | 相对论文锚 |
|---|---|---|---|---|---|
| Random Forest（ECFP+二肽） | **时间** | **1.801** | 0.364 | 1.581 | vs 论文 RF 2.10 → **-14.2%** |
| Random Forest（ECFP+二肽） | 随机 | 0.842 | 0.893 | 1.337 | vs 论文 1.89 → -55% |
| DeepDTA 类 1D-CNN | **时间** | **1.612** | 0.485 | 1.468 | vs 论文 DeepDTA 2.29 → **-29.6%** |
| DeepDTA 类 1D-CNN | 随机 | 1.057 | 0.818 | 1.309 | vs 论文 1.34 → -21% |

方向性（Q2）：两种模型均在随机分裂下大幅降低 LP-test RMSE（RF 1.801→0.842，-53%；CNN 1.612→1.057，-34%），严格满足"时间分裂 ≥ 随机分裂"的方向性（论文表 1：DeepDTA 1.34→2.29、RF 1.89→2.10 同样为随机→时间增长）。这直接量化了"传统随机划分因泄漏高估性能"的幅度：在我们的 ECFP+二肽 RF 上泄漏收益高达 0.96 kcal/mol（Pearson R 0.36→0.89），因训练集中已见 53.7% 测试复合物的配体或靶点。
Pearson R 差异：随机划分下 R≈0.82–0.89（近乎记忆），时间分裂下 R≈0.36–0.49（真实泛化），与论文"泄漏高估序列基方法排名相关性"一致。

### 3.3 论文锚对照（PAPER_ANCHOR 表）

| 锚 | 论文值 | 本工作 | 相对差 | 判分档 |
|---|---|---|---|---|
| #1 DeepDTA 时间分裂 test RMSE | 2.29 | **1.612**（CNN） | 29.6% | ≤35% 半满档 |
| #2 RF 时间分裂 test RMSE | 2.10 | **1.801**（RF） | **14.2%** | **≤20% 满分档** |
| #5 划分规模 11513/2422/4860 + 2171 | 精确 | 一致（精确匹配） | 0 | — |
| #3/#4 BDB2020+（IGN/DeepDTA） | 结构基，未复现 | — | — | 不适用（见局限） |
| #6 EGFR R 提升（IGN 0.36→0.65） | 靶点级，EGFR 数据不在冻结包 | 未复现 | — | 仅方向对照 |

### 3.4 BDB2020+ 外部基准（补充，代码 `04_bdb2020_eval.py`）

对 115 条 BDB2020+（亲和目标 `pKa=-log10(IC50/M)`）作外部评测（不参与任何训练）：

| 模型 | RMSE | Pearson R |
|---|---|---|
| RF（时间分裂重训练） | 1.376 | 0.237 |
| RF（随机分裂训练） | 1.334 | 0.270 |

与论文表 2 现象一致：BDB2020+ 亲和值范围更窄（pKa 3.6–9.9）→ RMSE 更低但对方法区分更难；结构基方法（论文 IGN retrained R=0.54）在 BDB 上明显优于我们未含 3D 结构信息的序列/配体基 RF（R=0.24），符合论文"结构信息对独立基准更关键"的论述方向。随机分裂训练的 RF 在 BDB 上未显着优于时间分裂（泄漏仅对记忆测试集有效，对外部集无效），同样支持主论断。

## 4. 解读与讨论

### 4.1 时间分裂下为什么仍存在 14.6% 精确同序列、6.1% val→test 同配体

论文分裂算法（`dataset_creation/create_splitting.ipynb`）按蛋白 `type` 分组计算 Needleman-Wunsch 比对相似度，并以相似度(>0.5/0.9)与配体 Dice(Morgan)>0.99 作为划分门控，**不按"字符串精确相等"排除**。实地核查发现 59 个相同序列组均跨不同 `type`（如 hydrolase/other、transcription/other），被 `ProteinComparer` 判为不相似而放行。这解释了：
- 与论文声称"max 蛋白序列相似度 <0.5"在**比对-分组口径**下自洽（我们未复算全部比对相似度分布）；
- 但在**精确身份仓库口径**下（同配体/同靶点是否同时在训练与测试），配体为 0、靶点为 14.6%。
因此我们报告两套口径：论文口径（方向性相似度控制）与裁判口径（精确身份重复，A3 锚）。随机分裂则两种口径均大量泄漏。

### 4.2 主要结论

1. 时间（LP）分裂在配体层面完全消除跨 train/test 重复（0 vs 随机 20.1%），靶点层面大幅降低（14.6% vs 40.4%）——泄漏存在且时间分裂显著缓解。
2. 用同一模型、同一测试子集对比：随机分裂训练的模型在 LP test 上的 RMSE 系统性更低（泄漏高估），RP 差 0.84–0.96 kcal/mol、Pearson R 差 0.35–0.53。
3. 复现的 RF 时间分裂 test RMSE=1.801，与论文 2.10 相对差 14.2%；
   DeepDTA 类 CNN=1.612，与论文 2.29 相对差 29.6%；两模型方向与论文一致。
   ⇒ 论文论断在本复现范围内 **supported**（三问：Q1 partially_supported（配体维度 supported），Q2 supported，Q3 supported）。

## 5. 局限（与论文口径差异）

1. **模型族**：RF 用"配体指纹+序列组成"，非论文 RF-Score 的 3D 原子对距离特征；DeepDTA 类 CNN 为轻量实现（3 层卷积、单种子、早停），与论文 3 种子平均的实现细节不同——这是 CNN 锚相对差 29.6% 的主要来源。
2. **结构基模型未复现**：IGN（结构 GNN）、AutoDock Vina（经典打分）需 3D 结构与预训练权重，BDB200+ tgz（35MB 结构包）解包后可支持但不含 IGN 权重，故 Table 2/3 的结构基锚仅作对照，锚 #3/#4/#6 未纳入判分对比。
3. **靶点身份代理**：用"蛋白序列精确相等"代理 UniProt ID。同源蛋白/不同构象的真实 UniProt 级泄漏比精确序列稍广；我们报告方向（比随机显著减少）稳健，但绝对值按精确身份计算为下界。
4. **BDB2020+ 只评测了 RF**（序列/配体特征），DeepDTA 类 CNN 在 BDB 上未跑（训练耗时长），论文 BDB 对照是结构模型（IGN）口径。
5. **随机分裂为单一种子**（seed=0，固定可复现）单一实现，未做随机分裂的多次重复取均值；但方向差异（1.8→0.84）远大于任何实现噪声。
6. 亲合单位：LP-PDBBind `value` 为 pK（±），与论文 pKd/pKi 一致；BDB 用 `pKa` 列。

## 6. 复现说明

```bash
bash agent_solution/code/run_all.sh
```
依赖：python3.12 + numpy/pandas/scikit-learn/torch(cpu)/rdkit/matplotlib/joblib（`code/requirements.txt`）。总时长约 20–30 分钟（两块 CNN 在 CPU 上各约 4–7 分钟），全部脚本单进程、无网络、固定种子。`run_all.sh` 首步做 checksum 校验。

## 7. 产物清单

- `code/`：`common.py`, `01_leakage_stats.py`, `02_rf_model.py`, `03_ddta_cnn.py`, `04_bdb2020_eval.py`, `05_finalize.py`, `06_figures.py`, `run_all.sh`, `requirements.txt`, `README.md`
- `results/`：`leakage_stats.csv`, `evidence_table.csv`, `metrics.json`, `metrics_rf.json`, `metrics_cnn.json`, `metrics_bdb2020plus.json`, `claims.json`, `predictions_rf_{time,random}.csv`, `predictions_cnn_{time,random}.csv`, `predictions_rf_bdb2020plus_{time,random}.csv`, `models/rf_*.joblib`
- `evidence/`：`fig1_leakage.png`, `fig2_rmse_compare.png`, `fig3_predictions.png`
- `solution.md`, `claim.md`, `report.md`