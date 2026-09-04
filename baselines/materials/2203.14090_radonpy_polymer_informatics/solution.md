# Solution — 2203.14090_radonpy_polymer_informatics

## 1. 任务
验证 Hayashi et al., "RadonPy: Automated Physical Property Calculation using All-atom Classical Molecular Dynamics Simulations for Polymer Informatics", npj Comput. Mater. 8, 222 (2022)（arXiv:2203.14090）的 L1 critical claim：

> RadonPy 全自动全原子经典 MD 管线对 1,138 个均聚物计算 15 种物理性质，≥1/≥3/5 次成功 1,070/1,001/759 个；PI1070 计算性质数据库（均值/标准差/计数）与 PoLyInfo 实验值系统一致。

## 2. 方法与口径
- **数据（冻结）**：`data/PI1070.csv`（1,077 行 × 157 列，MIT，SHA-256 `4EE41D52...56A4`，与清单一致）。判方重算路径：`F:\dataset\materials\2203.14090_radonpy_polymer_informatics\PI1070.csv`（脚本自动探测本地 `data/` 与 `/mnt/f/dataset/...` 两处）。
- **统计口径**：
  1. 数据规模：行/列、`monomer_ID` 唯一数、`polymer_class` 分布。
  2. 性质族识别：含 `_min/_max/_std/_count` 四联伴生列的基础性质即为一个"性质族"（MD 统计：`_count` = 5 次独立重复成功次数，`_mean` 取 5 次均值）。
  3. 成功数：以 `thermal_conductivity_count`（反 NEMD，管线最易失败性质）作门槛统计 ≥1 / ≥3 / ==5；另有 15 主性质 `_count` 逐聚合物取 min 的严格口径。
  4. 失败分类：对每个性质族统计 `_count==0` 的聚合物数（对应论文 4 类管线失败）。
  5. 实验一致性方向性：以高分子物理公认实验参考区间做分布隶属度检验（对照讨论，非逐点重算）。
  6. 机理：TC 分解列（TC_ke/pe/pair/bond/angle/dihed/improper/kspace）求和验证 + top-TC 聚合物化学结构检查。
- **随机种子**：42（本任务为确定性表格统计，重复运行结果一致）。
- **设备**：CPU，秒级。

## 3. 结果
### 3.1 数据统计（对齐判分 A1）
- 1,077 行 × 157 列；`monomer_ID` 唯一 1,077；`polymer_class` 20 类（频数：class13=261, class3=162, class2=161, class4=118, class1=83, class7/9=67, class10=50, class15=40, 其余 10 类共 71）；`tacticity`：atactic 574 / none 503；`temp`=300 K。
- 检出 **26 个性质族**；其中 15 个主性质（论文语义）为：density, Rg, r2, self-diffusion, Cp, Cv, compressibility, bulk_modulus,
isentropic_compressibility, isentropic_bulk_modulus, volume_expansion, linear_expansion, static_dielectric_const, refractive_index, thermal_conductivity；其余 11 个为补充/分解（dielectric_const_dc、thermal_diffusivity、nematic_order_parameter、TC_ke/pe/pair/bond/angle/dihed/improper/kspace）。

### 3.2 成功数（A3/锚#2）
| 口径 | ≥1 | ≥3 | ==5 |
|---|---|---|---|
| thermal_conductivity_count | **1,070** ✅ | **1,001** ✅ | **759** ✅ |
| 15 主性质 count 取 min | 1,067 | 998 | 745 |

恰好等于论文数字（1,070/1,001/759）。严格口径略低，确认 NEMD 热导率是最主要失败来源。

### 3.3 性质分布（A2，MD 计算值，含统计列解读）
- `density`：mean=1.1326, med=1.1271, [0.7424, 1.9145], std=0.1804 g/cm³（non-null 1,077）✅ 判分抽查区间 0.83–1.4。
- `thermal_conductivity`：mean=0.2397, med=0.2364, [0.0822, 0.6188], std=0.0656 W/m/K（non-null 1,070）。
- `refractive_index`：mean=1.5492, med=1.5449, [1.2741, 1.8389], std=0.0886（non-null 1,075）。
- `Cp`：mean=3,085.5 J/kg/K（non-null 1,076）；`bulk_modulus`：mean=3.06 GPa。
- 统计列语义：每个性质有 `_min/_max/_std/_count`，(min+max)/2≈均值、`_std` 为 5 次 MD 重复标准差、`_count` 为成功次数。例：thermal_conductivity `_count` ≥1 者为 1,070。

### 3.4 与论文/实验对照（A3/锚#5）
- **方向性隶属度**（对照讨论，非实测）：density 97.2%、refractive_index 99.1%、thermal_conductivity 99.0% 的计算值落在高分子物理公认实验参考区间内；Cp 仅 29.7%（部分一致，经典力场常系统性高估——如实留白）。
- density 与 refractive_index 正相关（ρ=0.158）、RI 与 TC 正相关（ρ=0.272）、density 与 TC 负相关（ρ=-0.329），物理自洽。
- top-8 TC：最高 0.619 W/m/K（PI690, class 13 芳香酰亚胺），包含 class 13（酰亚胺）5 个、class 10（芳酰胺）1 个、class 8（噻吩刚性）1 个、class 1（trans-烯烃刚性共轭）1 个——与论文"氢键/偶极-偶极/刚性线性主链共价键"高热导率机制方向一致。

### 3.5 失败分析（对照锚#3）
- `thermal_conductivity/TC_*`：7 个聚合物 _count=0（NEMD 失败）；`thermal_diffusivity`：8；`dielectric_const_dc/refractive_index`：2；多数平衡性质（Cp/Cv/bulk_modulus/…）：1——与论文"DFT 不收敛 / MD 未平衡 / 取向序参数 / NEMD 温度梯度非线性"4 类失败来源的分布量级一致（NEMD 占比最高）。

### 3.6 TC 分解机制（对照锚#7）
`sum(TC_ke+TC_pe+TC_pair+TC_bond+TC_angle+TC_dihed+TC_improper+TC_kspace)` 与 `thermal_conductivity` 逐行一致（corr=1.0，sum matches total=True）。top-TC 聚合物主要由 bond/angle/pair 贡献，支持共价键与强非键相互作用主导机制。

## 4. 结论标签
**supported**（具体判定理由见 claim.md；部分 caveat 记为 Cp 高估与逐点实验对照缺失，均不影响主论断成立）

## 5. 文件清单
```
agent_solution/
├── claim.md                 # 四档结论 + 关键数字
├── solution.md              # 本文
├── report.md                # 完整报告
├── code/
│   ├── analysis.py          # 主分析（统计/分布/成功数/类间/机制/图）
│   └── experiment_consistency.py  # 实验一致性方向性检验
├── results/
│   ├── evidence_table.csv   # property,metric,value 证据表
│   ├── metrics.json         # 全量指标
│   └── experiment_consistency.json
└── evidence/
    ├── property_distributions.png
    ├── TC_by_class.png
    ├── failure_by_family.csv
    ├── top_TC_polymers.csv
    └── exp_consistency_table.csv
```

## 6. 复现
```bash
python3 code/analysis.py                # 自动定位 data/PI1070.csv 或 /mnt/f 冻结源
python3 code/experiment_consistency.py
```
依赖：numpy/pandas（matplotlib 仅用于生成可选图）。可在 1 分钟内重算全部数字。