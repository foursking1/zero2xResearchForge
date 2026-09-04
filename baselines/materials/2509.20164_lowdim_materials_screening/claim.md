# 问题判定（claim）：2509.20164_lowdim_materials_screening

## 总体结论标签：`supported`

冻结数据（`screened_materials.json` + `2D_materials.json`，SHA-256 与清单一致）可**精确复现**论文的两项核心数量论断：
- FCDimen 低维材料发现分布 **9,139 = 1,838(0D) + 1,760(1D) + 3,057(2D) + 2,484(混合)**（由 `dim_fcdimen_c2` 直接统计得到，逐一精确匹配）；
- 可剥离 2D 新材料 **887 = 146(易剥离) + 741(可能剥离)**，全部不在已知 2D 数据库（C2DB/2DMatPedia/MC2D/NOMAD-RAE/topo/DBBs/robocrys）中（精确匹配）。

唯一的计数口径差异：冻结的 `screened_materials.json` 含 **35,689** 条，而非任务描述所称的 153,234。论文正文明确 "we screened 153,234 bulk materials … This screening finally gave us **35,689** materials"，即 35,689 是 153,234 经几何/已知性/凸包过滤后的子集；冻结文件对应的是论文的 35,689 筛选结果集。153,234 这一初始池在冻结数据中不可直接核验。

## 关键数字（全部由冻结数据实算，见 results/metrics.json 与 results/evidence_table.csv）

| 项目 | 论文锚 | 冻结数据实测 | 结论 |
|---|---|---|---|
| `screened_materials.json` 条目数 | 描述称 153,234 | **35,689** | 差异可解释（论文正文 35,689 = 过滤后筛选结果集；153,234 为初始池，不在冻结文件） |
| 动力稳定材料数 | 24,515 | **24,515** | 精确 |
| FCDimen 有效分类数（c1/c2/c3 非 None） | 24,515 | **24,515** | 精确 |
| 低维材料总数（c2，非 3D） | 9,139 | **9,139** | 精确 |
| 其中 0D / 1D / 2D / 混合 | 1,838 / 1,760 / 3,057 / 2,484 | **1,838 / 1,760 / 3,057 / 2,484** | 精确 |
| `2D_materials.json` 条目数 | —（2D 候选 3,057） | **2,988**（全部 c2=2D、全部 stable、唯一 mpid） | 2,988 ⊂ 3,057（69 条 c2=2D 未进入 2D 库） |
| 易剥离（E_exf ≤ 35） | — | **183** | 精确（论文正文 183） |
| 可能剥离（35 < E_exf < 125） | — | **953** | 精确（论文正文 953） |
| 易+可能剥离原始计数 | 1,136 | **1,136** | 精确 |
| 其中**不在已知 2D 库**（新材料） | 887 | **887** = 146 + 741 | 精确 |
| E_exf 分布（meV/Å²） | 阈值 35/125 | min 2.62 / 中位 152.6 / 均值 172.2 / max 1179.8 | 与阈值一致 |
| Larsen 几何描述符 | 低维材料被 Larsen 判为 3D | 全部 9,139 低维材料的 Larsen 主维度 = 3D | 支持「几何描述符无法识别」 |

## 逐条论断判定

1. **基准（35,689 个 MP 材料 UMLIP 力常数/声子）** → `supported`（计数精确一致；>10K 声子对照库不在冻结数据中，属不可核验部分）。
2. **大规模发现（153,234 筛选 → 9,139 低维）** → `supported`（9,139 及四类分布逐一精确复现）；153,234 初始池不在冻结文件，该具体规模数字标记为 `inconclusive`。
3. **可剥离 2D（887 个，全为已知 2D 库之外）** → `supported`（146+741=887，精确；已知性标记核验确认全部为库外新材料）。
4. **数据库发布** → `supported`（两个 JSON 均可解析、字段与 README 一致、SHA-256 与清单一致）。

## 证据指向

- 实算代码：`code/analyze.py`、`code/supplementary.py`
- 证据表：`results/evidence_table.csv`
- 汇总指标：`results/metrics.json`
- 补充交叉验证：`results/supplementary.json`、`results/c2_2d_missing_from_2d_file.csv`
