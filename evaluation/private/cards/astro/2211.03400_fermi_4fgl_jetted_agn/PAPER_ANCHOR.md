# PAPER_ANCHOR（私有，仅裁判/编译者可见）— 2211.03400_fermi_4fgl_jetted_agn

> 用途：LLM judge 的判分基准。禁止向作答 agent 暴露本文件与 SCORE_RUBRIC.md。
> 所有论文数值均从 arXiv:2211.03400（Universe 8, 587, 2022）Abstract/正文与 4FGL 目录 ReadMe 抽取，禁止臆造。
> 编译器探针数值基于本卡冻结数据（F:\dataset\astro\2211.03400_fermi_4fgl_jetted_agn\），仅供判分校准。

## 锚 A1 — 数据规模与无对应体（口径锚，判 A 维度）

| 项 | 值 |
|---|---|
| 指标名 | 4FGL 目录规模 / 无对应体源数 |
| 论文数值 | 4FGL 论文（ApJS 247, 33, Abstract）：**5,064** sources above 4σ；**1,336** sources without plausible counterparts（"For 1336 sources, we have not found plausible counterparts at other wavelengths"） |
| 出处 | J/ApJS/247/33 ReadMe Abstract；ReadMe File Summary Records=5065 |
| 冻结数据对应 | 4fgl.dat.gz 解压 5,065 行，唯一 Source_Name 5,065；CLASS1 空 = **1,336**（编译器实测，与 4FGL 论文一致；文件行数比官方源数多 1 为 VizieR 常规尾行/源表版本差异，需 agent 指出并讨论） |

## 锚 A2 — 核心结果：论文人口组成（核心结果锚，判 A 维度）

| 项 | 值 |
|---|---|
| 指标名 | 喷流 AGN 最终样本人口组成 |
| 论文数值 | 样本 **2,980** 个伽马射线点源；**BLL 40%**、**FSRQ 23%**、misaligned AGN 2.8%、NLS1+Sy+LINER 1.9%、changing-look AGN 1.1%、**~30% 仍无明确分类或完全没有分类** |
| 出处 | Abstract："Our final list is composed of 2980 gamma-ray point sources. Our final list of gamma-ray emitting jetted AGN is composed of BL Lac Objects (40%), flat-spectrum radio quasars (23%), misaligned AGN (2.8%), narrow-line Seyfert 1, Seyfert, and low-ionization nuclear emission-line region galaxies (1.9%)... About 30% of gamma-ray sources still have an ambiguous classification or lack one altogether." |
| 定义口径 | 选取 |b|>10°、河外或未分类对应体（排除星暴/正常星系）；论文基于 4FGL-DR2 + 文献光谱重分类（本卡冻结 4FGL-DR1，无光谱重分类步骤） |
| 冻结数据对应 | 论文口径目录层重建 = 2,866 源（差异 ~4%，源于 DR1 vs DR2 + 无重分类）；bcu 1,073（37.4%）、bll+BLL 1,067（37.2%）、fsrq+FSRQ 658（23.0%）、rdg+RDG 38（1.3%）、nlsy1 9（0.3%） |
| 容差（判分用） | 满分带：重建样本 2,866±10；bcu 1,073±20；bll+BLL 1,067±20；fsrq+FSRQ 658±15（见 SCORE_RUBRIC A） |

## 锚 A3 — 子论断：|b|>10° 无对应体比例（可证伪子论断）

| 项 | 值 |
|---|---|
| 指标名 | |b|>10° 伽马射线源中无对应体（CLASS1 空）比例 |
| 论文数值 | 论文未直接给出该数；由「~30% 无明确分类」推断无对应体 + bcu 合计应在 30% 量级（论文样本排除了无低频对应体的源） |
| 冻结数据对应 | |b|>10° 共 **3,646** 源，无对应体 **657（18.0%）**；bcu 1,074（29.5%）；bcu+无对应体合计 1,731（47.5%）（编译器实测） |
| 容差（判分用） | 该锚用于 B 抽查重算与 C2 定义敏感度讨论；A 维度满分带按冻结数据数值卡分 |

## 编译器探针（冻结数据，2026-08-13）

- rows=5,065；unique Source_Name=5,065
- CLASS1 全空天计数（大小写保留，与 ReadMe Table 7 occurrence 完全一致）：'' 1336 / bcu 1310 / bll 1109 / fsrq 651 / PSR 232 / unk 92 / spp 78 / FSRQ 43 / rdg 36 / glc 30 / SNR 24 / BLL 22 / snr 16 / PWN 12 / agn 10 / sbg 7 / psr 7 / RDG 6 / pwn 6 / HMB 5 / nlsy1 5 / css 5 / NLSY1 4 ...
- |b|>10°：total 3,646；CLASS1 空 657（18.02%）；bcu 1,074（29.46%）；bcu+空 1,731（47.48%）；blazar 类（bll+bcu+fsrq，含大小写）2,799（76.77%）
- 论文口径重建（|b|>10 且 CLASS1 非空，排除 PSR/psr/spp/SNR/snr/PWN/pwn/glc/gal/sbg/SFR/sfr/hmb/lmb）：**2,866** 源；bcu 1,073（37.4%）/ bll+BLL 1,067（37.2%）/ fsrq+FSRQ 658（23.0%）/ rdg+RDG 38 / nlsy1+NLSY1 9 / agn+AGN 10 / css 5 / ssrq 2 / BCU 1 / NOV 1
- 与论文 Abstract 对照：BLL 37.2% vs 40%（接近，Δ≈3pt）；FSRQ 23.0% vs 23%（一致）；bcu 37.4% 为「无明确分类」的目录层代理，论文重分类后 ~30%（Δ≈7pt，方向一致但需归因）

> 论文内部一致性提示：论文样本 2,980 来自 4FGL-DR2 选择 + 文献重分类；本卡冻结 4FGL-DR1 的 2,866 属「目录层」最接近可复现口径，agent 若指出 DR1/DR2 版本差异与重分类步骤缺失并如实归因，判分时视为正确做法。
