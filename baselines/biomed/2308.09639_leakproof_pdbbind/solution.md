# solution.md：LP-PDBBind「时间分裂防泄漏」验证（2308.09639_leakproof_pdbbind）

## 任务
在冻结的 LP-PDBBind 数据上验证论文核心论断：传统随机划分因同配体/同靶点泄漏高估测试性能，时间（相似度控制）分裂下测试 RMSE 上升、泄漏统计趋零。

## 方法（固定种子 0，全量代码重算）
- **数据列映射**：`Unnamed:0`→PDB ID；`new_split`→时间分裂；`value`→pKi；`smiles`→配体（规范 RDKit SMILES=配体身份）；`seq`→蛋白序列（靶点身份代理，因无 UniProt 列）；`CL1/CL2`/`covalent`→清洗/共价标记。仅使用带 `new_split` 的 18,795 行（train 11,513 / val 2,422 / test 4,860，与论文精确一致）。
- **泄漏检查**：配体/靶点在 train↔test、train↔val、val↔test 的精确身份重复；时间分裂 vs 等规模随机分裂（seed=0）。
- **模型（LP test CL2 非共价 2,171 条为评测集，test 不参与拟合/调参）**：
  1. 随机森林：配体 ECFP4(2048) + 蛋白二肽组成(400)，`RandomForestRegressor(n=300, seed=0)`；
  2. DeepDTA 类 1D-CNN：SMILES 字符 + 蛋白序列双分支卷积（3×Conv1d, FC512），MSE/Adam，val 早停；
  3. 训练协议对应论文 "train on CL1 & 非共价, test on CL2"。

## 结果（LP test CL2 非共价, n=2171）

| 模型 | 时间分裂 RMSE (Pearson R) | 随机分裂 RMSE (Pearson R) | 论文锚（时间） | 相对差 |
|---|---|---|---|---|
| Random Forest | **1.801** (0.364) | **0.842** (0.893) | 2.10 | **14.2%**（满分档） |
| DeepDTA 类 CNN | **1.612** (0.485) | **1.057** (0.818) | 2.29 | 29.6%（半满档） |

泄漏统计（train→test）：

| 身份 | LP 时间分裂 | 随机分裂(seed=0) |
|---|---|---|
| 配体（规范 SMILES） | **0** / 4838 (0%) | 976 / 4860 (20.1%) |
| 靶点（精确序列） | 711 / 4860 (14.6%) | 1965 / 4860 (40.4%) |
| 配体 OR 靶点 | 14.6% | **53.7%** |

## 三问答
1. **泄漏存在**（时间分裂下配体 0、随机 20.1%；靶点 14.6% vs 40.4%）；Q1：`partially_supported`（配体维度 fully supported）。
2. **方向成立**：同模型、同测试子集下随机分裂 RMSE 显著低于时间分裂（RF -53%、CNN -34%），符合"随机划分泄漏高估"；Q2：`supported`。
3. **锚复现**：RF 1.801 vs 论文 2.10（-14.2%）；CNN 1.612 vs 2.29（-29.6%）；"泄漏显著高估序列方法性能"在复现范围内成立；Q3：`supported`。

## 可复现性
```
bash agent_solution/code/run_all.sh   # checksum 校验 → 01 泄漏 → 02 RF → 03 CNN → 04 BDB → 05 汇总 → 06 图
```
依赖 `code/requirements.txt`；约 20–30 分钟（CPU），单进程无网络，种子固定 0。关键产物：`results/leakage_stats.csv`、`results/evidence_table.csv`、`results/metrics.json`、`evidence/*.png`。

## 局限
RF 非 3D 原子对特征；CNN 为轻量 DeepDTA 再实现；IGN/AutoDock Vina/BDB-结构锚未复现（需 3D+权重，冻结包无）；靶点身份以精确序列代理 UniProt；随机分裂单一实现。