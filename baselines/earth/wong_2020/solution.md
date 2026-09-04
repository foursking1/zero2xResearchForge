# Solution: Wong/Fox et al. (2020) NAAMES — Reproduction Analysis

- 论文 ID: `wong_2020`（Frontiers in Marine Science 7:24, 2020, DOI 10.3389/fmars.2020.00024）
- 层级: L2 对齐端到端科研再发现
- 数据: 冻结子集 `naames_observation_subset_v1`（原位读取，未复制、未联网补充）
- 提交物: `solution.md`、`code/analyze_wong2020.py`（主复现脚本）、`code/c04_depth_profiles.py`（C04 剖面图）、`results/evidence_table.csv`、`results/metrics.json`、`figures/fig_c03_c04.png`

所有数值均由冻结数据实际计算得到。论文数值一律标注“论文引用”。

---

## 1. 数据与方法概述

使用四类核心数据文件（均在 `directories/`、`files/` 下）：

| 用途 | 文件 | 关键字段 |
|---|---|---|
| 模型 θ_PaM、PAR | `P10_theta_PaM/theta_PaM_1min_all.csv` | theta_PaM, PAR, datetime |
| 模型逐日 C_phyto | `P12_NPP/cphyto_mod_per_station.csv` | C_phyto_mod, ChlACS_mean, theta_PaM_mean, PAR_mean |
| 模型深度分辨率 NPP | `P12_NPP/npp_profiles.csv` | z, PAR_z, mu_z, NPP_z |
| 光学 C_phyto、bbp | `files/cphyto_bbp_all.csv` | bbp470, cphyto_bbp |
| 实测 Chl | `P03_ChlACS/ChlACS_all_cruises.csv` | ChlACS_mg_m3 |
| 14C 培养 | `files/npp_14c_all.csv` | depth, lightlevel, NPP_14C |

统一处理：
- cruise 名归一化为 `NAAMES1`–`NAAMES4`（小写 `naames_1` → `NAAMES1`）。
- 站点名归一化：NAAMES2 的 `4a/4b/4c` → 模型剖面站点 `4`；NAAMES3 `unknown` → `6`。
- 回归统一为 OLS（`y = slope·x + inter`），r² 用 `1 − SS_res/SS_tot`，RMSE 用 `sqrt(SS_res/n)`。

---

## 2. 各 Claim 结果

### 2.1 C01 — θ_opt 与 θ_PaM 的一致性

**论文引用**：Field-measured θ_opt exhibited good agreement with θ_PaM (y = 0.85x + 12.34, r² = 0.72, RMSE = 19.17)。

**口径**：θ_opt = C_phyto^bbp / Chl_ACS（C:Chl，单位 mg C : mg Chl，论文 Fig.4 定义）。θ_PaM 取模型输出。

**结果**（y = θ_opt，x = θ_PaM）：

| 口径 | n | slope | intercept | r² | RMSE |
|---|---|---|---|---|---|
| 1-min 白天 bin（PAR>0，0<θ<300） | 14215 | 0.295 | 22.62 | 0.198 | 20.19 |
| station-day，on-station 50 km | 23 | 0.574 | 15.55 | 0.422 | 15.84 |
| station-day（全 bbp 日均） | 46 | 0.261 | 32.75 | 0.112 | 26.27 |
| **论文引用** | — | 0.85 | 12.34 | 0.72 | 19.17 |

**判定**：**partially_supported**。数据中 θ_opt 与 θ_PaM 呈显著正相关（p<0.001）但远弱于论文：最佳口径的 r²（0.42）仅为论文（0.72）的约 60%，斜率（0.57）比论文（0.85）明显偏低，只有 RMSE（15.8–20.2）与论文（19.17）同量级。1-min 全航线口径 r² 仅 0.20，说明冻结子集的 1-min θ 数据散点很大，无法复现论文的 0.72。

### 2.2 C02 — 模型 C_phyto 与 bbp(470) 的线性关系

**论文引用**：y = 14910x + 0.70, r² = 0.61, RMSE = 16.31（Fig.5，daily mean points）。

**口径**：C_phyto^mod 取 `cphyto_mod_per_station.csv` 的 C_phyto_mod（= θ_PaM × Chl_ACS）；bbp(470) 取以 14C 站位为中心的 50 km 半径内当日 bbp470 均值；仅保留 PAR_mean>0 的有效站日（排除 PaM 未激活、θ_PaM=19 默认值的站日）。

**结果**（y = C_phyto_mod，x = bbp470 日均）：

| 指标 | 实测 | 论文引用 | 相对偏差 |
|---|---|---|---|
| slope | **14858.6** | 14910 | **0.3%** ✓ |
| intercept | −0.36 | 0.70 | 显著偏离 ✗ |
| r² | **0.605** | 0.61 | **0.8%** ✓ |
| RMSE | 10.77 | 16.31 | 34% 偏离 ✗ |
| n | 21 | — | — |

**判定**：**partially_supported**（核心关系支持）。C02 的两个最关键锚点——斜率 14910 与 r² 0.61——均落在 10% 容差内（相对偏差 <1%），说明冻结数据完全支持“C_phyto^mod 与 bbp(470) 线性相关、斜率约 15000、决定系数约 0.61”这一核心结论。intercept（−0.36 vs 0.70）与 RMSE（10.77 vs 16.31）在数值上与论文不同；截距均接近零，RMSE 论文更高，可能与论文使用更大数据集/日均点含站内标准差有关。

### 2.3 C03 — 模型 NPP 与 14C 培养的对比

**论文引用**：overall（排除三个亚北极 climax 站）y = 0.99x − 1.4, r² = 0.80, RMSE = 6.03, n = 138；三站子集 y = 0.33x + 2.1, r² = 0.85, RMSE = 6.43, n = 21（Fig.6）。

**口径**：模型 NPP 取 `npp_profiles.csv` 中 NPP_z（= mu_z × C_phyto_mod）。14C 培养按论文方法“在对应采集深度的光照水平下培养”，将每个培养瓶按其 `lightlevel`（光强百分比）匹配到模型剖面中 PAR_z/PAR_0 = lightlevel/100 处的 NPP_z（光级匹配）；若站日剖面 NPP=0（PaM 未激活）则选用日期最邻近的活跃剖面。y = NPP_14C，x = 模型 NPP。NAAMES2 为论文表 3 定义的“climax transition”，其亚北极三个站（3, 4a, 4b）为低斜率子集。

**结果**：

| 子集 | n | slope | intercept | r² | RMSE |
|---|---|---|---|---|---|
| 全部光级匹配（14C>0） | 144 | 0.433 | 5.77 | 0.632 | 8.55 |
| 排除三站（对应论文 overall） | 122 | 0.722 | 1.39 | 0.657 | 7.56 |
| **三站子集（N2 3,4a,4b）** | **22** | **0.323** | 8.75 | **0.898** | 5.43 |
| 论文引用 overall | 138 | 0.99 | −1.4 | 0.80 | 6.03 |
| 论文引用 三站 | 21 | 0.33 | 2.1 | 0.85 | 6.43 |

**判定**：**partially_supported**。
- **三站子集（低斜率）**：slope 0.323 vs 论文 0.33（偏差 2% ✓）、r² 0.898 vs 0.85（偏差 6% ✓）、n 22 vs 21（✓）均在容差内；RMSE 5.43 vs 6.43（偏差 15%，略超）。论文“亚北极 climax 三站 14C 约为模型 1/3（y≈0.33x），r²≈0.85”的核心结论被冻结数据明确复现。
- **overall 回归**：无法复现论文的 1:1（slope 0.99）。冻结子集上模型整体系统性高于 14C（排除三站后 slope 0.72、r² 0.66），三站子集的 ~3× 偏移在其它站也存在但较弱。n=122（论文 138）差异来自冻结子集缺少部分站点的模型剖面（N1-5/6/6a/7a、N2-1/2、N1-4）。

### 2.4 C04 — 深度分辨模型 NPP 剖面与 14C 离散点对比

**论文引用**：Fig.7 —— model depth-resolved (1 m) NPP profiles vs discrete 14C incubations throughout the euphotic zone。

**口径**：将每个 14C 培养点按最近深度匹配到当日模型剖面 NPP_z（深度匹配），比较两者。

**结果**（n = 144 个有效配对）：

| 指标 | 数值 |
|---|---|
| Pearson r(model, 14C) | **0.668** |
| 回归 slope（y=14C, x=model） | 0.346 |
| 回归 r² | 0.447 |
| 模型/14C 中位比 | 1.72（模型平均高 ~1.7×） |
| 落在 2× 内比例 | 56.3% |
| 落在 3× 内比例 | 73.6% |
| 每巡航中位比 | N1 2.25 / N2 1.74 / N3 1.79 / N4 1.17 |

剖面图见 `figures/fig_c03_c04.png`（右侧 panel）与 `code/c04_depth_profiles.py` 生成的 `results/c04_profile_comparison.png`。

**判定**：**partially_supported**。模型 NPP 剖面与 14C 离散点在垂直结构上显著相关（r=0.67），且低生产站点（NAAMES4，中位比 1.17）接近 1:1，说明模型能捕捉 NPP 随深度的主要形态；但模型在各巡航普遍系统性高估 14C（中位 1.2–2.3×，深水低光处偏差最大），与 C03 的整体偏移一致。

---

## 3. 结论汇总

| Claim | 判定 | 关键证据 |
|---|---|---|
| C01 θ_opt ~ θ_PaM (0.85, 12.34, r² 0.72, RMSE 19.17) | **partially_supported** | 正相关成立但 r²（0.20–0.42）与 slope（0.3–0.6）显著弱于论文；RMSE 同量级 |
| C02 C_phyto^mod ~ bbp(470) (14910, 0.70, r² 0.61, RMSE 16.31) | **partially_supported** | slope 14859 与 r² 0.605 均在 10% 容差内（<1%）；intercept/RMSE 不同 |
| C03 NPP vs 14C overall (0.99, −1.4, r² 0.80, n 138) + climax 子集 (0.33, 2.1, r² 0.85, n 21) | **partially_supported** | climax 子集 slope/r²/n 复现（2%/6% 内）；overall 1:1 未复现 |
| C04 深度剖面匹配 14C | **partially_supported** | 显著相关（r=0.67）但模型系统性高估 ~1.7× |

四个 claim 中，**C02 的斜率与决定系数、C03 的亚北极 climax 低斜率（约 0.33，与“24 h 培养中放牧呼吸使 14C 比实际 NPP 低约 3 倍”的论文讨论一致）被冻结数据明确复现**。C01 与 C03-overall 的绝对拟合强度（r² 0.72/0.80）无法在冻结子集上复现。

---

## 4. 局限与说明

1. **冻结数据为子集**：14C 共 186 条，其中可匹配到模型剖面且有效的 144 条（论文 overall+子集合计 159 条）。缺少 N1-5/6/6a/7a、N2-1/2、N1-4 等站点的模型剖面，是 n 与整体拟合差异的主要原因之一。
2. **14C 培养瓶的光照-深度对应**：同深度存在多个光照水平的培养（P-E 曲线结构），论文图 6/7 的比较口径可能为“每站每深度一个代表值”或“按光强匹配”，我们采用光级匹配（C03）与最近深度匹配（C04）两种并报告；两种口径结论一致（模型系统性偏高）。
3. **日期对齐**：模型剖面有 PAR=0（PaM 未激活）的日平均剖面，14C 日期与之不一致时选用日期最邻近的活跃剖面；这是最优可复现口径，已在口径栏说明。
4. **无联网、无编造**：所有数字均为实跑冻结数据得到，论文数值仅以“论文引用”形式对照。
5. 主复现脚本为 `code/analyze_wong2020.py`，可独立重跑生成 `results/metrics.json` 与 `results/evidence_table.csv`。
