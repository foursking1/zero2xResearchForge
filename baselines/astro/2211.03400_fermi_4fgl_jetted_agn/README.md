# 2211.03400 Fermi 4FGL 喷流 AGN 人口组成 — Agent Solution

复现 Foschini et al. (2022, Universe 8, 587) 论文口径的人口统计，基于冻结 4FGL-DR1 目录
（CDS VizieR `J/ApJS/247/33`：`4fgl.dat.gz` + `ReadMe`）。

## 目录结构
```
agent_solution/
├── claim.md                 四档判定 + 逐项对照 + 定义敏感度
├── solution.md              方法与结果摘要
├── report.md                完整报告（≤2 页）
├── README.md                本文件
├── code/
│   ├── analyze_4fgl.py      主脚本：定宽解析 → 全空天/\|b\|>10°/样本 三层统计 → 证据表 + metrics
│   ├── verify_checks.py     独立实现（pandas.read_fwf）重算抽查 3 数并断言
│   └── make_figures.py      补充图（GLAT/GLON 分布、人口组成柱状图）
├── results/
│   ├── metrics.json         全部关键指标 + 论文对照 + 判定
│   ├── evidence_table.csv   全空天 CLASS1 计数 / \|b\|>10° 组成 / 重建样本组成
│   ├── all_sky_class_counts.csv        全空天逐码计数（含大小写）
│   ├── sample_composition.csv          样本内组成
│   ├── sample_vs_allsky_crosscheck.csv 三层对照（可追溯）
│   ├── sample_source_membership.csv    逐源样本成员表（可复现任何占比）
│   └── verify_checks.json   PASS 断言结果
└── evidence/
    └── figures/             fig1 / fig2（PNG）
```

## 运行（Python 3.11+，仅 gzip + pandas + matplotlib）
```bash
python3 code/analyze_4fgl.py  --data-dir /mnt/f/dataset/astro/2211.03400_fermi_4fgl_jetted_agn --outdir .
# 自动定位：不传 --data-dir 时依次尝试 $FROZEN_DATA_DIR、data/、F: 冻结目录及其 WSL 挂载
python3 code/verify_checks.py --data-dir <数据目录> --outdir .     # 抽查 3 数断言，ALL_CHECKS_PASS
python3 code/make_figures.py  --data-dir <数据目录> --outdir evidence/figures
```

## 核心结论
- 总行数 / 唯一源 = **5,065 / 5,065**；CLASS1 空（无对应体）全空天 = **1,336**；
  \|b\|>10° 无对应体 = **657（18.0%）**；\|b\|>10° bcu（大小写合计）= **1,074（29.5%）**。
- 论文口径重建样本 = **2,866**（\|b\|>10° 且 CLASS1 非空，剔除银河系码），组成：
  BLL 1,067（37.2%）、bcu 1,073（37.4%）、FSRQ 658（23.0%）、rdg 38、nlsy1 9、agn 10 …
- 判定：**partially_supported**（论文 2,980 / 40% / 23% / ~30% 差异由 DR1-vs-DR2 版本 + 文献重分类归因）。