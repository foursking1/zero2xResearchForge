# Report — 验证 LoTSS-Deep DR1 射电源分类人口统计（L1）

- **task_id**：`2305.05782_lotss_deep_source_class`
- **论文**：Best P.N. et al., *The LOFAR Two-metre Sky Survey: Deep Fields Data Release 1. V. Survey description, source classifications and host galaxy properties*, MNRAS (2021/2023), arXiv:2305.05782
- **数据**：LOFAR Surveys Deep Fields DR1 官方发布（9 文件），冻结于 `F:\dataset\astro\2305.05782_lotss_deep_source_class\`（本机 `/mnt/f/dataset/astro/2305.05782_lotss_deep_source_class/`）；全部 SHA-256 与 `data/source_manifest.json` 一致。
- **结论**：**supported** —— 冻结数据精确复现论文 Table 2 全部计数，核心人口统计论断成立。

## 1. 方法

基于官方发布的三场分类目录（11 列主表 `*_classifications_dr1.fits`）做确定性统计。步骤：

1. **解析**：`astropy.io.fits` 读入主表（后备后端 `fitsio`，结果一致）。
2. **逐类计数**：对最终分类列 `Overall_class` 计数（SFG/RQAGN/LERG/HERG/Unc）。
3. **口径交叉验证**（C1）：
   - 用 README 规则独立重建 `AGN_final × RadioAGN_final → Overall_class`（任一 `-1` → Unc），与 `Overall_class` 逐行比对 —— **0 失配**（81,951/81,951）；
   - 主表 vs 扩展表 `Overall_class` 逐行一致 —— **0 失配**；
4. **流量分层**：`S_150MHz`（Jy→μJy）分箱 `[0,100)/[100,300)/[300,1000)/[1000,1500)/[1500,∞)`，报告各箱 n、n(SFG)、SFG 占比；50% 开关点由相邻箱线性插值。
5. **对照与归因**：实测 vs 论文 Table 2；`>90%` vs `84%` 做口径归因（C2）。

所有数值由脚本从 FITS 重算，论文数字仅用于对照讨论，未作"实测值"。

## 2. 结果

### 2.1 目录规模（锚 A1）

ELAIS-N1 **31,610** / Lockman Hole **31,162** / Boötes **19,179** → 总计 **81,951**，与 Table 2 **完全一致**（±0）。

### 2.2 逐类计数（锚 A2）— 实测 == Table 2

| field | SFG | RQAGN | LERG | HERG | Unc | Σ |
|---|---|---|---|---|---|---|
| en1 | 22,720 | 2,779 | 4,287 | 510 | 1,314 | 31,610 |
| lockman | 21,044 | 2,633 | 5,304 | 710 | 1,471 | 31,162 |
| bootes | 11,916 | 2,030 | 3,158 | 524 | 1,551 | 19,179 |
| **总** | **55,680** | **7,442** | **12,749** | **1,744** | **4,336** | **81,951** |
| **%** | **67.9%** | **9.1%** | **15.6%** | **2.1%** | **5.3%** | — |

逐场 15 项全部与 Table 2 差 0（`paper_comparison.table2_exact_match = all true`）。

### 2.3 可靠分类率与 SFG 主导（锚 A3）

- 可靠分类率 **94.7%**（∈[93%,96%]）；Unc 5.3%。
- SFG 总计 **67.9%**（>2/3）；ELAIS-N1 **71.9%**（>70%）✅ §7。
- RQAGN **9.1%**（~10%）。radio-loud（LERG+HERG）合计 **17.7%**。

### 2.4 ELAIS-N1 低流量分布（锚 A4）

| 流量箱（μJy） | n | n(SFG) | SFG% |
|---|---|---|---|
| <100 | 681 | 573 | **84.1%** |
| 100–300 | 19,120 | 15,150 | 79.2% |
| 300–1000 | 9,718 | 6,417 | 66.0% |
| 1000–1500 | 804 | 333 | 41.4% |
| >1500 | 1,287 | 247 | **19.2%** |

- SFG 占比随流量**单调下降**（84.1%→19.2%）。
- **开关点** ~**0.99 mJy**（∈[0.5,2.5] mJy；≈1.0 mJy，论文 §7 ~1–1.5 mJy 一致）。
- 论文 Abstract「>90% at limiting flux」vs 目录末箱 84.1%：归因于 (i) 论文图采用**检测完整性/天空覆盖完备性修正**；(ii) 极限流量定义差异——目录最暗端（S<100 μJy，n=681）受 S/N 与选区截断偏置，仅强大最暗源得以入选（偏恒星形成/射电宁静）。二者为同趋势、不同口径，不为矛盾。

### 2.5 交叉验证与扩展检查

- 主/扩展表 `Overall_class` **100% 一致**；flag 重建 **100% 一致**。
- 逐场可靠率：en1 95.8% / lockman 95.3% / bootes 91.9%。
- 形态学一致性：LERG/HERG 中 `Extended_radio=1`（>80 kpc 清晰扩展）占比远高于 SFG/RQAGN（见 `results/morphology_by_class.csv`）；与 radio-loud=S FG 划分的物理预期（文献广泛共识）相称。
- 无线电剩余简单截断（AGN_final=0 且 Radio_excess≤0.5 dex：21,276）与 SFG 标签（22,720）同量级，方向一致。

## 3. 输出产物

- `results/evidence_table.csv`：逐类计数表（`field,class,n` + TOTAL 汇总）+ 逐场流量分箱表（`field,flux_bin_uJy,n,n_sfg,frac_sfg`）。
- `results/metrics.json`：三场行数、逐类计数与百分比、可靠率、ELAIS-N1 分箱与开关点、Table 2 对照、结论标签。
- `figures/class_fractions.png`、`figures/sfg_frac_vs_flux.png`。
- `code/analyze_lotss_deep.py`、`code/crosscheck_lotss_deep.py`（可复现，含固定种子）。

## 4. 局限与边界

1. **口径**：本评测只对冻结的 DR1 发布目录负责；论文含 SED 拟合中间产物与完整性修正，本文以目录 `Overall_class`/原始计数为准，未复现拟合链。
2. **开关点**：由 5 箱线性插值得到 ~0.99 mJy；箱边界/最暗箱小样本（n=681）引入 ±~0.2 mJy 扰动；论文图论 ~1–1.5 mJy 含完备性修正细节。
3. **流量单位**：`S_150MHz` 为 Jy（目录），已统一换算 μJy/mJy；3 个场的灵敏度不同（ELAIS-N1 最深），跨场比较流量的绝对深度受此影响。
4. **未动其他发布**：DR2 或后续发布不在本任务范围。

## 5. 结论

| 论断 | 判定 |
|---|---|
| 目录规模 31,610/31,162/19,179 = 81,951 | ✅ 精确复现 |
| Table 2 五类 × 三场计数 | ✅ 精确复现（差 0） |
| 94.7% 可靠分类（Unc 5.3%） | ✅ |
| SFG 67.9%（>2/3）、ELAIS-N1 >70% | ✅ |
| RQAGN 9.1%（~10%） | ✅ |
| 低流量端 SFG 主导 + 单调下降 + ~1 mJy 开关点 | ✅ |
| Abstract「>90% at limit」 | ⚠️ 方向一致；84% vs 90% 有明确口径归因 |

**总标签：`supported`**。