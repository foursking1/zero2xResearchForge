# agent_solution — 2305.05782_lotss_deep_source_class

验证 Best et al. (2023, arXiv:2305.05782)「LoTSS-Deep DR1 射电源分类人口统计」L1 论断的完整可复现提交。

## 结论速览

**四档标签：`supported`** —— 冻结数据与论文 Table 2 逐类完全一致（81,951 源 / SFG 67.9% / RQAGN 9.1% / LERG 15.6% / HERG 2.1% / Unc 5.3%，可靠分类率 94.7%）；ELAIS-N1 中 SFG 占比随流量单调下降（84.1%→19.2%），50% 开关点 ~0.99 mJy；「Abstract >90% vs 目录 84%」差异归因于完整性修正与极限流量定义。

## 复现

```bash
# 冻结数据目录（示例为本机挂载路径）
DATA=/mnt/f/dataset/astro/2305.05782_lotss_deep_source_class
OUT=$PWD

python3 code/analyze_lotss_deep.py "$DATA" "$OUT"        # 主分析
python3 code/crosscheck_lotss_deep.py "$DATA" "$OUT"     # 交叉验证
```

依赖：Python 3.11+，`astropy`（或 `fitsio`）、`pandas`、`numpy`、`matplotlib`。
确定性：纯计数、无随机化（脚本内固定 `np.random.seed(42)`），重复运行输出逐字节一致。

## 目录

```
code/                    # 两个脚本
├── analyze_lotss_deep.py     # 解析 FITS、逐类计数、流量分箱、50% 开关点、比例图
└── crosscheck_lotss_deep.py  # 主/扩展表一致性、flag 重建、形态学、逐场可靠率
results/
├── evidence_table.csv        # 逐类计数表(field,class,n) + 流量分箱表(field,flux_bin_uJy,n,n_sfg,frac_sfg)
├── metrics.json              # 全部关键指标（行数/计数/百分比/可靠率/分箱/开关点/Table2 对照/结论）
├── per_field_summary.csv     # 每场计数 + 可靠率
├── morphology_by_class.csv   # Extended_radio 占各 class 比例
└── crosscheck_metrics.json   # 交叉验证明细
figures/
├── class_fractions.png       # 各场+总计五类占比
└── sfg_frac_vs_flux.png      # 三场 SFG 占比 vs S_150MHz
evidence/                     # 关键证据导出（README、morphology、per-field、Table2 复现表）
claim.md                      # 四档结论 + 逐场逐类对照 + 差异归因
solution.md                   # 方法说明与结果（速读）
report.md                     # 完整报告（方法/结果/局限，≤2 页）
```

## 关键可复核数字

| 校验点 | 值 |
|---|---|
| 三场行数 | 31,610 / 31,162 / 19,179 = 81,951 |
| en1 SFG | 22,720 |
| 总计 RQAGN | 7,442 |
| Table 2 对照 | 15 项全部差 0 |

（均可由代码从冻结 FITS 重算。）