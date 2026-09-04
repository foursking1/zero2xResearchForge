# report.md — 验证报告：Fermi 4FGL 喷流 AGN 人口组成论断（arXiv:2211.03400）

## 摘要

本报告在冻结的 Fermi **4FGL-DR1** 点源目录（CDS VizieR `J/ApJS/247/33`，gzip 解压 5,065 行 × 4,104 字节定宽，
`CLASS1` 区分大小写）上，重建 Foschini et al. (2022) 的喷流 AGN 人口统计口径并与其 Abstract 对照。
结论：数据规模与"无对应体 1,336"锚点**完全复现**；人口组成在方向与量级上一致
（BLL ~37% vs 40%、FSRQ 23.0% ≈ 23%、无明确分类 ~37% vs ~30%），四档判定为
**`partially_supported`**，偏差可归因于 DR1/DR2 版本差、论文的文献光谱重分类、以及 CLASS 码覆盖有限。

## 1. 方法

### 1.1 定宽解析（唯一权威：包内 ReadMe）
- `gzip.open(..., "rt", encoding="latin-1")`；逐行校验长度恰为 4,104 字节（ReadMe `Lrecl`）；跳过末尾空行；声明 `Records=5065` 与实际行数断言一致。
- 字节区间（1-based）：`Source_Name` 1–28；`GLON` 38–47；`GLAT` 49–58；`CLASS1` 3978–3982；`CLASS2` 3984–3986；`ASSOC1` 3988–4015。
- **大小写严格处理**：`bll`(likely)/`BLL`(identified) 等按表 7 区分；统计"BLL 类"合并 `bll+BLL`。
- **文件渲染细节**：VizieR 在列间隔字节处用 `|` 渲染（等同 ReadMe 的空字节），字段内容仍在声明字节范围。
  解析正确性经三重验证：① 全 33 类 `CLASS1` 计数与 ReadMe 表 7 occurrence 逐一吻合（如 `bcu`=1310、`bll`=1109、`fsrq`=651、`PSR`=232、`unk`=92…）；
  ② 抽查源 `${GLON,GLAT}` 值对照已知 4FGL 坐标（如 `4FGL J0000.3-7355` → 307.71°, −42.73°，SMC 领域）合理；
  ③ 独立实现（`pandas.read_fwf` + colspecs）重算全部关键数一致。
- 工具：Python 3.12 + gzip/pandas；无外部数据；无随机性（`--seed 0` 仅为规范占位）；CPU 秒级。

### 1.2 筛选口径（论文"河外或未分类对应体"的目录层操作化）
- 样本 = `|GLAT| > 10` 且 `CLASS1` 非空 且 `CLASS1 ∉ {PSR,psr,spp,SNR,snr,PWN,pwn,glc,gal,sbg,SFR,sfr,hmb,HMB,lmb,LMB}`。
- 无对应体 = **`CLASS1` 空**（与 4FGL 论文"1,336"定义一致）。注意 `ASSOC1` 空 ≠ 无对应体
  （全空天 1,333、|b|>10° 654，比 CLASS1 空少 3/3 个源——3 个源有 CLASS1 码但 ASSOC1 串为空），
  用 ASSOC1 做"无对应体"是错误口径。

## 2. 结果

### 2.1 数据规模
解压 5,065 行；唯一 `Source_Name` = 5,065（字节 1–28 口径与 IAU 名 1–18 口径均 5,065）。
ReadMe `Records=5065` ✓；4FGL 论文摘要 "5064 sources above 4σ" 的 +1 为 VizieR/目录发布口径常规差异。

### 2.2 全空天 CLASS1
`CLASS1` 空（无对应体）= **1,336**（= 4FGL 论文摘要 "1,336 no counterparts" ✓）。
主要类：`bcu`1310 / `bll`1109 / `fsrq`651 / `PSR`232 / `unk`92 / `spp`78 / `FSRQ`43 / `rdg`36 /
`glc`30 / `SNR`24 / `BLL`22 / `snr`16 / `PWN`12 / `agn`10 / `sbg`7 / `psr`7 / `RDG`6 / `pwn`6 /
`HMB`5 / `nlsy1`5 / `css`5 / `NLSY1`4 / `SFR`3 / `hmb`3 / `BCU`2 / `GAL`2 / `ssrq`2 / `AGN`1 / `BIN`1 /
`LMB`1 / `NOV`1 / `gal`1 / `sey`1 / `lmb`1（全部与表 7 注释一致）。

### 2.3 |b|>10° 层（3,646 源）
- 无对应体：**657（18.0%）**。
- `bcu`（小写）1,073 + `BCU`（大写）1 = **1,074（29.5%）**；无对应体 + bcu = **1,731（47.5%）**。
- blazar 类（bll+bcu+fsrq，含大小写）= 2,799（76.8%）；剔除银河系码 123（3.4%，主要为 `PSR`91 + `glc`15 + `sbg`7）。

### 2.4 论文口径重建样本（2,866 源）
| 组（大小写合并） | 数量 | 占比 |
|---|---|---|
| BLL（bll+BLL） | 1,067 | 37.2% |
| bcu（bcu+BCU） | 1,074 | 37.5% |
| FSRQ（fsrq+FSRQ） | 658 | 23.0% |
| rdg+RDG（misaligned 射电星系） | 38 | 1.3% |
| nlsy1+NLSY1 | 9 | 0.3% |
| agn+AGN | 10 | 0.35% |
| css / ssrq / NOV / GAL | 5 / 2 / 1 / 2 | 各 <0.2% |

（小写拆解：bll 1,045 / BLL 22 / bcu 1,073 / BCU 1（已在 bcu 组内）/ fsrq 619 / FSRQ 39。）

### 2.5 与论文 Abstract 对照
| 项 | 论文（4FGL-DR2 + 文献重分类） | 冻结 DR1 目录层 | 差距与归因 |
|---|---|---|---|
| 最终样本 | 2,980 | **2,866** | −3.8%；DR1/DR2 版本差 + 论文加入 4LAC/NED 与光谱重分类对应体 |
| BLL | 40% | **37.2%** | −2.8 pt；论文把部分 bcu 判为 BL Lac |
| FSRQ | 23% | **23.0%** | ≈一致（FSRQ 认定稳定） |
| misaligned AGN | 2.8% | 1.3%（+ssrq 共 1.4%） | 论文多波段归类更广 |
| NLS1+Sy+LINER | 1.9% | 0.31% | 目录只带 9 个 NLSY1 码，论文靠光谱扩充 |
| changing-look AGN | 1.1% | 不适用 | 4FGL-DR1 无此类码，目录层不可表示 |
| 无明确分类 | ~30% | bcu 37.4%（样本内）；见 2.6 敏感度 | 论文文献重分类压低 bcu 占比 |
| 无对应体 | 4FGL 1,336 | **1,336** | 数据源锚完全一致 |

### 2.6 「无明确分类」定义敏感度
| 定义 | 数量 | 占比 | 备注 |
|---|---|---|---|
| 仅无对应体（\|b\|>10° 分母） | 657 | 18.0% | 下界；论文无对应体已按设计被排除出样本 |
| 样本内 bcu（样本分母 2,866） | 1,073 | **37.4%** | 最贴近论文口径的目录代理（论文经重分类后 ~30%） |
| 无对应体 + bcu（\|b\|>10° 分母） | 1,731 | 47.5% | 上界；把论文排除的源计入"无分类" |
| 全空天无对应体 | 1,336 | 26.4% | 参照 |

结论：论文的 ~30% 落在 (下界 18.0%，目录代理 37.4%，上界 47.5%) 之间，方向一致，
"bcu 是否计入无明确分类"是把 29.5% 变成 47.5% 的关键二分——必须明示口径。

### 2.7 判定
**`partially_supported`**。判定理由见 `claim.md` 第 5 节：
数据规模/无对应体锚完全支撑；人口组成方向与量级一致可归因，非 contradicted；逐项 1:1 精确复现并非本目录层能力所及。

## 3. 局限与边界

1. **定宽解析**：以 ReadMe 字节表为唯一权威；VizieR `|` 分隔符渲染不影响数字列；若按分隔符切列会错位。
2. **大小写**：`CLASS1` 大小写语义必须保留；合并统计需显式声明（本文 bcu 默认指小写 `bcu`，组合口径单列）。
3. **筛选口径**：论文"河外或未分类对应体"在目录层用「|b|>10 ∧ CLASS1 非空 ∧ 非银河系码」近似；
   排除码集合按 TASK.md，大写 `GAL`（正常星系，2 个）若不剔除样本为 2,866，若剔除为 2,864（±10 容差内）。
   `unk` 未出现在 \|b|>10 的河外筛选中（92 个 unk 全在低纬/被排除路径），故不作为排除码。
4. **版本与过程差异**：论文基于 4FGL-DR2 + 文献光谱重分类 + 4LAC/NED 交叉；本卡片冻结 4FGL-DR1，
   无重分类步骤。2,980 vs 2,866（~4%）与 FSRQ 吻合、BLL/ambiguous 偏移均由此而来，属如实归因而非抄数。
5. **不可表示类别**：changing-look AGN、LINER、部分 Seyfert 在 DR1 CLASS 码中没有标签，目录层无法给出论文口径的相应占比。
6. 「~30%」的判定对口径（bcu 是否计入）高度敏感；本报告显式给出三档（18.0% / 37.4% / 47.5%）。
7. 全部数字可由 `results/sample_source_membership.csv`（逐源）与 `code/*.py` 从冻结文件重算复现。

## 4. 产物清单
- `claim.md`（四档判定 + 逐项对照 + 敏感度）
- `code/analyze_4fgl.py`（主解析/统计/证据表/metrics）、`code/verify_checks.py`（独立重算抽查 3 数 + 断言）、
  `code/make_figures.py`（图）
- `results/evidence_table.csv`、`results/metrics.json`、`results/all_sky_class_counts.csv`、
  `results/sample_composition.csv`、`results/sample_vs_allsky_crosscheck.csv`、
  `results/sample_source_membership.csv`、`results/verify_checks.json`
- `evidence/figures/fig1_glat_glon_distributions.png`、`evidence/figures/fig2_population_composition.png`
- `solution.md`（方法 + 复现说明）、`report.md`（本文）