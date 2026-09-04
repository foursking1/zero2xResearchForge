# solution.md — 方法与结果速览

## 任务
在**冻结 M20 官方目录**（`tablea1.dat`，320 行 × 152 字节定宽，latin-1）层面验证论文
**arXiv:2509.08224**（A&A 2025，基于 rest-frame T90,z/Ep,z/Eiso 的无监督 GRB 双族分类）的核心
论断：**GRB 可按 rest-frame 参数分为 ~14% / ~86% 两族，且两族参数中位数显著分离**。

## 方法（全部由代码执行，无手工抄数）
1. 按 `ReadMe` 字节级表定宽切片解析（`GRB` 1–7、`T90i` 11–17、`z` 19–25、`Eiso` 40–50、
   `Epi` 74–80、`Type` 99–105、`EH` 134–138 等；行按 152 补齐）。
2. Type 归并：`I`/`I+EE` → Type I；`II`/`II+SNph`/`II+SNsp` → Type II。
3. 单位：`Eiso` 表值（10⁴⁴ J）数值即 ×10⁵¹ erg；`T90i`/`Epi` 即 rest-frame 的 T90,z/Ep,z。
4. 输出逐行证据表、汇总行、`metrics.json`、3 张图；独立脚本重算 3 个抽查数。
5. 论文数值仅作对照讨论，从不定为实测。

## 关键结果（实测）
| 指标 | 实测 | 论文对照 |
|---|---|---|
| 总行数 | **320** | 320（M20 全表） |
| Type I（`I`+`I+EE`） | **45（14.06%）** | GRBs-I 14.59%（t-SNE）/ 14.32%（UMAP） |
| Type II | **275（85.94%）** | GRBs-II ~86% |
| Type I 中位 T90z / Epz / Eiso | **0.27 s / 706 keV / 0.69** | 0.31 s / 523.83 keV / 0.28 |
| Type II 中位 T90z / Epz / Eiso | **14.50 s / 446 keV / 100.0** | 13.84 s / 407.94 keV / 75.19 |
| T90,z < 2 s | **64（20.0%）**；Type I 短暴 42/45=93.3%；**Type II 短暴 22** | 论文"仅靠 T90 不可靠"动机 |
| 060614A / 980425B / 171205A / 110402A | **I+EE / II+SNsp / II+SNsp / I+EE**（110402A: 2.8 s, 1924 keV → 边界案例） | 与论文 GRBs-I/II 归属一致 |
| 200826A | 不在 M20（2020，论文 Table A.1） | 如实说明 |

原始 Type 计数：`I` 34、`I+EE` 11、`II` 235、`II+SNph` 19、`II+SNsp` 21（合 320），
与 M20 ReadMe "45 type I and 275 type II" 一致。
辅助交叉验证：EHDtype/EHtype 与 Type 一致率 99.1% / 95.9%；Type I 中 80% EH>3.3、
Type II 中 98.5% EH<3.3。
诚实披露：320 样本 k-means(k=2) 健全性检查得小簇 31.9%（≠论文 14%），归因于样本与方法差异
（论文 370 样本 + t-SNE/UMAP），不作为判定依据。

## 结论
**`supported`**（M20 目录口径）：Type I/II = 45/275（14.06% / 85.94%），与论文 GRBs-I 占比
14.32–14.59% 一致；两族 T90z / Eiso 中位数分离显著（~54× / ~145×），点名事件归属全部吻合，
短暴与 Type 类别重叠（22 个"短 T90 的 Type II"）支持"仅靠 T90 不可靠"。差异（占比 ≤0.53pt、
Epz ~35% 绝对差）归因于样本组成（320 全表 vs 300+70）与分族方法（目录 Type 标签 vs
t-SNE/UMAP 聚类归属）。

## 运行
```bash
cd agent_solution
python3 code/reproduce.py        # 完整分析 → results/（evidence_table.csv, metrics.json, figures/）
python3 code/verify_probe.py     # 独立重算 320 / 45 / 0.27，全 PASS
```
数据定位：`$GRB_DATA_DIR` → `agent_solution/data`（冻结副本，SHA-256 已校验）→ 冻结包
`/mnt/f/dataset/astro/2509.08224_grb_restframe_unsupervised`。纯 CPU，秒级。

## 产出清单
- `claim.md`（四档判定 + 逐项对比）
- `report.md`（完整方法与局限）
- `code/reproduce.py`、`code/verify_probe.py`
- `results/evidence_table.csv`、`results/evidence_summary.csv`、`results/metrics.json`
- `results/figures/{fig1_t90z_histogram,fig2_epz_eiso_scatter,fig3_eiso_histogram}.png`
- `evidence/events_crosscheck.csv`、`evidence/key_metrics.csv`
- `data/`（`tablea1.dat` + `ReadMe` 冻结副本）