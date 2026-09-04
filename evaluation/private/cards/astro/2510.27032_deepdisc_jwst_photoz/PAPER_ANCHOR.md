# PAPER_ANCHOR（私有）：2510.27032 DeepDISC JWST photo-z

来源：arXiv:2510.27032v1（2026-02-02）Abstract、§4 结果（Fig. 9）；发布目录 Zenodo 17487691。数值均摘自论文。

## 锚 A1 — 数据产品规模（核心结果锚，精确可核对）

| 项 | 值 |
|---|---|
| 指标名 | 发布测光红移目录规模 |
| 论文数值 | **94,000 个 photo-z**（"produce a catalog of 94000 photo-zs in 4 minutes on a single NVIDIA A40 GPU"；"a catalog of photo-zs for all JADES DR2 photometric sources in the GOODS-S field"） |
| 出处 | Abstract；§6（目录）；Zenodo 17487691 |
| 定义口径 | JADES DR2 GOODS-S 全部测光源的 ensemble 概率式 photo-z（mode + 68/95/99% CI） |
| 容差 | 冻结目录行数必须为 94,000（已核对一致）；报告其他行数 → A1 判 0 |

## 锚 A2 — 质量指标（上下文锚，本数据不可直接复算，用于可检验性分析）

| 项 | 值 |
|---|---|
| 指标名 | photo-z 点估计质量：bias、scatter（IQR，即归一化红移差的四分位距）、outlier fraction η |
| 论文数值 | **DeepDISC（9 NIRCam）**：N=298，bias=0.0035，IQR=0.0311，η=0.0503；**EAZY（9 NIRCam 匹配滤光片）**：bias=0.0032，IQR=0.0403，η=0.1242；**EAZY（9 NIRCam + HST/JEMS 附加）**：bias=0.0023，IQR=0.0198，η=0.0705 |
| 出处 | §4，Fig. 9（左/中/右三面板标题） |
| 定义口径 | 测试集 298/330 个论文检测源；点估计=PDF 众数；归一化红移差 Δz/(1+z_spec)；IQR=σ 型 scatter；η=outlier fraction（|Δz|/(1+z)>0.15 之类，论文口径） |
| 容差 | 冻结数据（目录）不含谱红移 → 不可复算。判分用途：(a) 若 agent 额外冻结/引入谱红移源做交叉验证，须明确样本差异，不得声称精确复现；(b) 讨论"质量相当/更优"结论的可检验性（C 维度） |

## 辅助事实（论文训练/测试口径，供可检验性讨论）

- 谱红移样本：训练 1,845 + 测试 330（§4），z 覆盖至 z~11，z>6 覆盖率骤降。
- 预训练：GalaxiesML（HSC DR2 204,573 星系，Do et al. 2024）；Fig 5 显示 GML 预训练 R50：bias 0.0053 / IQR 0.0402 / η 0.0732（N=314，HSC 测试）。
- 目录生成：ensemble，单卡 A40 4 分钟。
- 判分对照：A1 精确（94,000 + CI 自洽）；A2 不可复算 → 不设数值带，只作讨论锚；B 抽查见 SCORE_RUBRIC。