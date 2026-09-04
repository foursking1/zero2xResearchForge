# solution.md — 完整执行记录（方法 / 步骤 / 结果 / 结论）

任务：`2606.23725_comp_refs_not_experiments`（L2，端到端科研再发现）
目标假设 H0：GNN 电压筛选器在未见 Na-ion 阴极上误差小到可驱动筛选，且计算参考电压（MP PBE+U）≈ 实验电压，常数加性偏移可校准系统误差。
本文件记录从冻结数据到结论的每一步，全部数字由实际运行代码得到（非抄写）。

---

## 0. 环境与数据完整性

- 运行环境：Windows 11 / Python 3.13.14；numpy 2.5.2、pandas 3.0.5、scipy 1.18.0、matplotlib 3.11.1。
- 输入：`data/na_cathodes_validation.csv`（7 行）、`data/li_offset_audit.csv`（4 行）。
- 完整性校验：对两个文件计算 SHA-256，与 `data/SOURCE.md` 冻结值一致（`c02e4ead…`、`1dc10206…`），运行输出 `checksum OK: …`。

## 1. 执行步骤

1. 读取两个冻结 CSV。
2. 计算逐行 `signed error = v_pred − v_lit`、`|error|`；标记规范集（`excluded_canonical=no`，n=6）与全集（n=7）。
3. 防泄漏检查：7 行 `in_training_corpus` 全为 False（全部样本外）。
4. 计算总体指标：MAE / RMSE / bias / max|err|（规范 n=6 与全 7 行）；tier A/B 分组的 MAE；化学家族均值偏差与跨度。
5. 残差结构：Pearson r(signed error, v_lit)（n=7 与 n=6）；r(v_pred, v_lit) 与 OLS 斜率。
6. 加性校准（样本外）：留一法偏移校正 → LOO 校正误差向量 → 10,000 次 bootstrap（seed 20260609）→ 95% CI（97.5 分位上界）；对照组：样本内均值偏移、朴素原始 MAE bootstrap 上界。
7. 三方误差分解（n=2，两个 NaCoPO4 多形体）：`pred−lit = (mp−lit) + (pred−mp)`。
8. 自有基准审计（Li 4 对）：δ = V_QME − V_exp 的均值与样本标准差（ddof=1），对照预注册门槛 0.30 V 给出判定。
9. 写出 `results/evidence_table.csv`、`results/metrics.json` 与 3 张图；打印控制台摘要。

运行命令：

```bash
cd agent_solution
python code/analyze.py
```

（脚本输出见 `code/analyze.py` 末尾的 `print` 段；核心数值与 `results/metrics.json` 逐字一致。）

## 2. 结果（本次实际运行得到）

### 2.1 真实误差（Q1）
- 规范 n=6：**MAE = 0.6682 V**，RMSE = 0.7670 V，bias = +0.2314 V，max|err| = 1.3064 V。
- 全 7 行：MAE = 0.6938 V，bias = +0.3194 V。
- 梯子判定：0.668 > 0.50 V → **not screening-grade**（不可用于筛选）。
- tier A MAE = 0.5899 V；tier B MAE = 0.7465 V（A 级行也不达标）。

### 2.2 残差结构（Q2）
- Pearson r(signed error, v_lit)：n=7 → **−0.9385**；n=6 → −0.9795。
- r(v_pred, v_lit) = −0.0101；OLS 斜率 ≈ −0.0037（预测与实验几乎无线性关系）。
- 结构：高压低估（NaCoPO4 4.3–4.5 V 实验 vs 3.7–3.9 V 预测）、低压高估（Na2FePO4F 2.985 V 实验 vs 4.29 V 预测）。

### 2.3 加性校准（Q3，样本外）
- 样本内均值偏差 = +0.2314 V；样本内去均值后 MAE = 0.6682 V（不变）。
- **LOO 校正后 MAE = 0.8018 V > 原始 MAE 0.6682 V**（常数偏移不转移）。
- bootstrap（10,000 次，seed 20260609）95% CI = [0.513, 1.0905] V；单侧 95% 上界 1.034 V；**97.5 分位保守上界 1.0905 V**。
- 对照：朴素原始 MAE bootstrap 95% 上界 = 0.9286 V（远低于保守口径，证明必须样本外校正）。
- 家族偏差跨度 = 1.063 V（磷酸盐 −0.222、氟磷酸盐 +0.607、层状氧化物 +0.841 V）>> 0.15 V。

### 2.4 误差分解（Q4，n=2）
| 行 | pred−lit | mp−lit | pred−mp |
|---|---|---|---|
| NaCoPO4 ABW | −0.784 | −0.539 | −0.245 |
| NaCoPO4 β | −0.434 | −0.538 | +0.104 |
| 均值 | −0.609 | **−0.538** | −0.071 |

模型相对参考平均偏离仅 −0.07 V；参考相对实验偏低 0.54 V → **误差主源 = 计算参考尺度**。

### 2.5 自有基准审计（Q5）
- δ = {+0.314, +0.484, +0.434, −0.198} V；均值 +0.2584 V；**sd(δ, ddof=1) = 0.3125 V**。
- 0.3125 ≥ 0.30 V → **FAIL：撤销本地 PBE+U 基准的绝对电压声称**。
- 核心 3 对（LiFePO4 型）共享 +0.4106 V（sd=0.0873 V），但 LiMn2O4 对为 −0.198 V，偏移不可跨化学迁移。

## 3. 结论

**标签：`contradicted`**（provisional，n<20）。

证据链：(i) MAE=0.668 V 不可筛选；(ii) 残差-电压 r=−0.939 强电压依赖；(iii) LOO 加性校正失效且保守 95% 上界 1.09 V；(iv) 计算参考偏低 0.54 V 主导误差；(v) 本地 DFT 基准 sd(δ)=0.313 V 绝对电压声称 FAIL。**H0 不成立：该 GNN 筛选器对未见 Na-ion 阴极的绝对电压筛选不可用，"计算参考≈实验 + 常数偏移可校准"被数据拒绝。**

**边界**：样本量极小（n=6/7）→ provisional；覆盖 3 个化学家族、tier A/B 为主；n=2 分解限 NaCoPO4 单化学；结论不构成对一切 ML 材料筛选的普适否定。

## 4. 产物清单

```
agent_solution/
├── claim.md                      # 可证伪声称 + 失败条件 + 结论标签
├── report.md                     # ≤2 页方法/结果/结论/边界
├── solution.md                   # 本文件
├── code/
│   └── analyze.py                # 唯一分析脚本，一切指标由冻结数据重算
└── results/
    ├── evidence_table.csv        # 逐行证据表（含单位说明列）
    ├── metrics.json              # 全部总体指标（含定义/单位/判定）
    ├── figure_error_voltage.png  # 残差 vs 实验电压（r=−0.939）
    ├── figure_decomposition.png  # 三方误差分解（n=2）
    └── figure_calibration.png    # 原始 vs LOO 校正 |err|（0.668→0.802 V）
```

## 5. 关键数字可复现性

| 指标 | 本次运行值 | 复现方式 |
|---|---|---|
| 规范 MAE | 0.6682 V | `python code/analyze.py` 输出 |
| Pearson r（n=7） | −0.9385 | 同上 |
| LOO 校正 MAE | 0.8018 V | 同上 |
| bootstrap 95% 上界 | 1.0905 V | 同上（seed 20260609） |
| mp−lit 均值（n=2） | −0.5382 V | 同上 |
| Li sd(δ) | 0.3125 V | 同上 |
