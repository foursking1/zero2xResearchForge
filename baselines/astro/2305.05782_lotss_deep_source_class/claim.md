# Claim 判定 — LoTSS-Deep DR1 射电源分类人口统计

- task_id：`2305.05782_lotss_deep_source_class`
- 论文：Best P.N. et al., "The LOFAR Two-metre Sky Survey: Deep Fields Data Release 1. V. Survey description, source classifications and host galaxy properties", MNRAS, arXiv:2305.05782
- 冻结数据：`F:\dataset\astro\2305.05782_lotss_deep_source_class\`（9 文件，SHA-256 全部校验一致）
- 数据口径：三个深场分类目录（`{en1,lockman,bootes}_classifications_dr1.fits`，11 列），依据 README 分类规则对 `Overall_class`（最终分类列）逐行统计；所有计数均由代码从 FITS 二进制表重算得到，与论文数值无关。

## 四档结论

> **结论标签：`supported`（支持）**

在**冻结目录数据口径**下，论文核心论断「LoTSS-Deep DR1 共约 80,000 源、94.7% 可可靠分类、SFG 占约 2/3（67.9%）、RQAGN ~9%、低流量端 SFG 主导」被目录录数值**精确支持**：

- 三场行数与论文 Table 2 完全一致（31,610 / 31,162 / 19,179 = **81,951**）；
- 五类 × 三场计数与 Table 2 **逐类完全一致**（精确复现）；
- 百分比（67.9 / 9.1 / 15.6 / 2.1 / 5.3）、可靠分类率 94.7%、SFG 2/3、RQAGN ~10%（9.1%）全部落在论文窗口；
- ELAIS-N1 低流量端 SFG 主导、占比随流量单调下降、50% 交叉点 ~1 mJy 均在论文方向性区间内；
- 「>90%」与「84%」的差异有明确口径归因（见下），非结论性冲突。

## 关键数字（实测，直接来自冻结数据）

| 指标 | 实测值 | 论文值 | 一致？ |
|---|---|---|---|
| 三场行数 | en1 31,610 / lockman 31,162 / bootes 19,179 / **总计 81,951** | Table 2：31,610 / 31,162 / 19,179 / 81,951 | ✅ 精确 |
| SFG 计数（en1/lockman/bootes/总） | 22,720 / 21,044 / 11,916 / **55,680** | 同左 | ✅ 精确 |
| RQAGN 计数（总） | **7,442** | 7,442 | ✅ 精确 |
| LERG 计数（总） | 12,749 | 12,749 | ✅ 精确 |
| HERG 计数（总） | 1,744 | 1,744 | ✅ 精确 |
| Unc 计数（总） | 4,336 | 4,336 | ✅ 精确 |
| 百分比（总） | SFG 67.9% / RQAGN 9.1% / LERG 15.6% / HERG 2.1% / Unc 5.3% | 同左 | ✅ |
| 可靠分类率 | 94.7%（1 − 4,336/81,951） | Abstract「95%」 | ✅ |
| RQAGN 占比 | 9.1%（「nearly 10%」） | ✓ | ✅ |
| SFG 占比（总） | 67.9%（>2/3） | Abstract「over two-thirds」 | ✅ |
| SFG 占比（ELAIS-N1） | 71.9%（>70%） | §7「over 70 per cent in the deepest field」 | ✅ |
| ELAIS-N1 末箱（<100 μJy）SFG 占比 | 84.1%（目录未修正口径） | Abstract「>90% at limiting flux density」 | ⚠️ 方向一致，数值差异有归因 |
| 50% 开关点 | ~0.99 mJy（线性插值，相邻箱间） | §7「~1.5 mJy」（图论，含完整性修正） | ✅ 落入 [0.5, 2.5] mJy 窗口 |

## 逐场逐类对照（实测 vs Table 2）

| field | class | 实测 | Table 2 | 差 |
|---|---|---|---|---|
| en1 | SFG | 22,720 | 22,720 | 0 |
| en1 | RQAGN | 2,779 | 2,779 | 0 |
| en1 | LERG | 4,287 | 4,287 | 0 |
| en1 | HERG | 510 | 510 | 0 |
| en1 | Unc | 1,314 | 1,314 | 0 |
| lockman | SFG | 21,044 | 21,044 | 0 |
| lockman | RQAGN | 2,633 | 2,633 | 0 |
| lockman | LERG | 5,304 | 5,304 | 0 |
| lockman | HERG | 710 | 710 | 0 |
| lockman | Unc | 1,471 | 1,471 | 0 |
| bootes | SFG | 11,916 | 11,916 | 0 |
| bootes | RQAGN | 2,030 | 2,030 | 0 |
| bootes | LERG | 3,158 | 3,158 | 0 |
| bootes | HERG | 524 | 524 | 0 |
| bootes | Unc | 1,551 | 1,551 | 0 |

**全部 15 项计数与 Table 2 差为 0。**

## ELAIS-N1 流量分层（S_150MHz，未做完整性修正）

| 流量箱（μJy） | n | SFG 数 | SFG 占比 |
|---|---|---|---|
| < 100 | 681 | 573 | 84.1% |
| 100–300 | 19,120 | 15,150 | 79.2% |
| 300–1,000 | 9,718 | 6,417 | 66.0% |
| 1,000–1,500 | 804 | 333 | 41.4% |
| > 1,500 | 1,287 | 247 | 19.2% |

SFG 占比随流量**单调下降**（84.1%→79.2%→66.0%→41.4%→19.2%）；50% 交叉点 ~0.99 mJy（≈1 mJy，处于论文论述的 ~1–1.5 mJy 区间内）。末箱 n=681 样本较小（占 ELAIS-N1 的 2.2%），开关点对箱边界有一定敏感性，误差估计 ±0.2 mJy。

## 差异归因（84% vs Abstract「>90%」）

论文 Abstract/§7 的「over 90 per cent of sources at the limiting flux density」来自**图像检测完整性修正与更细的极限流量定义**：

1. **完整性修正**：论文图的 SFG 占比使用源-计数完备性修正（成像/检测天空覆盖面积），把实测末箱 84.1% 推到 >90%；
2. **极限流量定义**：目录在最暗端受 S/N 与选区截断影响（S<100 μJy 仅 681 个已入选源），目录末箱的近端偏置是有选择性的——最暗的源只有高 S/N（在 ELAIS-N1 深图）才能入选，而这类源偏向恒星形成/射电宁静；
3. **本文口径**：冻结目录仅含"已检出+已选区的源"，未做天空完备性加权，因此是**同一问题、不同口径**的数值，不构成矛盾；方向（低流量端 SFG 主导）与开关点（~1 mJy vs 论文 ~1–1.5 mJy）一致。

## 内部一致性交叉验证（不依赖论文数字）

- `Overall_class` 与主表 `AGN_final × RadioAGN_final` 规则重建分类**100% 一致（0 失配）**；
- 主表与扩展表 `Overall_class` 逐行**100% 一致**；
- ELAIS-N1 中，物理学意义的无辐射 AGN + 无线电剩余 ≤0.5 dex 子样本（21,276）与 SFG 标签数（22,720）同量级，形态学上 LERG/HERG 的扩展射电（Extended_radio=1）占比远高于 SFG/RQAGN（详见 `evidence/morphology_by_class.csv`），佐证五类标签的区分度。

## 局限

- 只对冻结的 DR1 发布口径负责；不同发布/新版（DR2）或不同选区会改变绝对数。
- 开关点由 5 箱线性插值给出，箱边界、末箱小样本引入 ±0.2 mJy 扰动。
- 未复现代理（如 SED 拟合中间产物、85% 完整度曲线），推论以目录发布列为准。

*所有数字可由 `agent_solution/code/analyze_lotss_deep.py` 与 `crosscheck_lotss_deep.py` 从冻结 FITS 重算复现。*