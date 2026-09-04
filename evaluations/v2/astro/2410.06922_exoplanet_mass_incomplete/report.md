# EVAL REPORT v2: 2410.06922_exoplanet_mass_incomplete

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（deepseek-v4-flash）
- 评测时间: 2026-08-21

## 总分: 68.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 30.0 | 60 | 关键实测数值（逐字引用，均来自落盘 metrics.json/evidence_table.csv）：complete 子集 kNN×KDE=0.9139、kNN-Imputer=0.9557、MissForest=0.9605、MICE=1.0012、GAIN=1.9884、mBM-class=0.9637；full 全档案 MissForest=1.1913、kNN×KDE=1.3474、MICE=1.3715、kNN-Imputer=2.0428、GAIN=4.5402；extended 8 属性 kNN×KDE=1.4036（150 子集 1.2431），六属性 full=1.3474（150 子集 1.0728）。逐 rubric band 判定：（1）满分带 60 要求『全档案 kNN×KDE 最低且扩展差异<0.05 或≤6属性』：full 中 kNN×KDE(1.3474) > MissForest(1.1913)，不满足『kNN×KDE 最低』；extended 差异 Δ=1.4036-1.3474=+0.0562>0.05 且方向为损伤而非提升，不满足。故满分带不命中。（2）半满带 30 条件『排名部分反转但整体模式保持』：complete 最优组 {kNN×KDE,kNN-Imputer,MissForest} 保持且 GAIN 最差，full 中 GAIN 仍最差（4.54），整体模式保持，但 full 最优被 MissForest 反转、8 属性方向相反，故命中半满带。（3）零分带不适用（GAIN 未反转、多数数据集已完成）。三项子项（complete/full/extended）均完成且证据表齐全，按半满带取 30 分，不向上取整。注：允许快照差异导致绝对值偏离，判分以结构性方向为主。 |
| B 证据真实性/实际复现 | 38.0 | 40 | 磁盘证据扫描显示：metrics.json 存在、evidence_table.csv 存在（evidence/ 与 results/ 两处内容一致）、25 个结果 CSV/JSON、多个 distribution_*.csv、可运行 .py 代码齐全，属『有证据文件且数值与报告严格一致、可核对』层级，B 应落在 [30,40]。抽查关键实测数：complete kNN×KDE eps=0.9139026070858511、full GAIN eps=4.540157573190279，在 report.md、evidence_table.csv、metrics.json 三处严格一致，且与论文锚值（0.886、2.552）明显不同，无抄论文数字嫌疑。独立重算未执行（环境限制），按代码完整性与证据链闭环在区间内给 38 分（不取 40 满分，因未实际重算验证可运行性）。 |

## A 核心结果达成度（30.0/60）

关键实测数值（逐字引用，均来自落盘 metrics.json/evidence_table.csv）：complete 子集 kNN×KDE=0.9139、kNN-Imputer=0.9557、MissForest=0.9605、MICE=1.0012、GAIN=1.9884、mBM-class=0.9637；full 全档案 MissForest=1.1913、kNN×KDE=1.3474、MICE=1.3715、kNN-Imputer=2.0428、GAIN=4.5402；extended 8 属性 kNN×KDE=1.4036（150 子集 1.2431），六属性 full=1.3474（150 子集 1.0728）。逐 rubric band 判定：（1）满分带 60 要求『全档案 kNN×KDE 最低且扩展差异<0.05 或≤6属性』：full 中 kNN×KDE(1.3474) > MissForest(1.1913)，不满足『kNN×KDE 最低』；extended 差异 Δ=1.4036-1.3474=+0.0562>0.05 且方向为损伤而非提升，不满足。故满分带不命中。（2）半满带 30 条件『排名部分反转但整体模式保持』：complete 最优组 {kNN×KDE,kNN-Imputer,MissForest} 保持且 GAIN 最差，full 中 GAIN 仍最差（4.54），整体模式保持，但 full 最优被 MissForest 反转、8 属性方向相反，故命中半满带。（3）零分带不适用（GAIN 未反转、多数数据集已完成）。三项子项（complete/full/extended）均完成且证据表齐全，按半满带取 30 分，不向上取整。注：允许快照差异导致绝对值偏离，判分以结构性方向为主。

## B 证据真实性/实际复现（38.0/40）

磁盘证据扫描显示：metrics.json 存在、evidence_table.csv 存在（evidence/ 与 results/ 两处内容一致）、25 个结果 CSV/JSON、多个 distribution_*.csv、可运行 .py 代码齐全，属『有证据文件且数值与报告严格一致、可核对』层级，B 应落在 [30,40]。抽查关键实测数：complete kNN×KDE eps=0.9139026070858511、full GAIN eps=4.540157573190279，在 report.md、evidence_table.csv、metrics.json 三处严格一致，且与论文锚值（0.886、2.552）明显不同，无抄论文数字嫌疑。独立重算未执行（环境限制），按代码完整性与证据链闭环在区间内给 38 分（不取 40 满分，因未实际重算验证可运行性）。

## 证据与重算说明

独立重算未执行。关键实测数核对：evidence_table.csv 中 complete kNN×KDE eps=0.9139026070858511、full GAIN eps=4.540157573190279、extended kNN×KDE eps=1.4035702766524918，与 report.md 及 metrics.json 完全一致；150 子集方向（delta_150）在 metrics.json 中逐算法列出（kNN-Imputer +0.850、GAIN +2.501、kNN×KDE +0.159、MissForest +0.013、MICE +0.024），与报告叙述相符。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实且深入地分析了快照差异导致的排名反转与方向不一致，未强行拟合论文结论；证据表、JSON 与报告数值严格对齐，透明度极高。
- 不足: 全档案中 kNN×KDE 未能复现最优排名（被 MissForest 超越），且 8 属性扩展方向与论文相反，导致核心结果达成度止步于半满档。