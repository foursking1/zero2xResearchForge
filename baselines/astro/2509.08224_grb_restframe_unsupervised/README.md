# agent_solution — 2509.08224_grb_restframe_unsupervised

在冻结 M20 GRB 目录（`tablea1.dat`，320 行 × 152 字节定宽）上验证论文
arXiv:2509.08224 的"~14% / ~86% 双族人口结构"论断。

## 目录结构
```
agent_solution/
├── claim.md              # 四档判定（supported）+ 论文逐项对照与差异归因
├── solution.md           # 方法与结果速览
├── report.md             # 完整复现报告（方法/结果/归因/局限）
├── README.md             # 本说明
├── code/
│   ├── reproduce.py      # 主分析脚本（解析/计数/中位数/短暴统计/事件查询/出图/输出 JSON）
│   └── verify_probe.py   # 独立重算脚本（rubric 3 抽查数：320 / 45 / 0.27）
├── results/
│   ├── evidence_table.csv      # 逐行解析表（grb,t90z_s,z,epz_keV,eiso_e51,type,...）
│   ├── evidence_summary.csv    # 分族汇总行（AGG:*）
│   ├── metrics.json            # 全部关键指标 + 论文锚对照 + 结论标签
│   └── figures/                # fig1 T90z 直方图 / fig2 Epz–Eiso 散点 / fig3 Eiso 直方图
├── evidence/
│   ├── events_crosscheck.csv   # 点名事件交叉验证
│   └── key_metrics.csv         # 关键指标导出
└── data/                       # 冻结数据副本（tablea1.dat + ReadMe，SHA-256 已校验）
```

## 运行
```bash
conda/py env: Python 3.10+，依赖 numpy pandas matplotlib（scikit-learn 可选，仅健全性检查用）

python3 code/reproduce.py        # → 重新生成 results/ 全部产物
python3 code/verify_probe.py     # → 打印 3 抽查数并 PASS/FAIL
```

数据定位顺序（均可）：环境变量 `GRB_DATA_DIR` → `code/data` · `../data`
（本目录下的冻结副本）→ 冻结包 `/mnt/f/dataset/astro/2509.08224_grb_restframe_unsupervised`。
主脚本每次运行都会对 `tablea1.dat` 做 SHA-256 校验（期望
`b84d3a7fa1cc3bdea722e385fc5a6cb22f3b2f142efc0b4238402e1128a40f0a`）。

## 核心数字（全部由代码产生）
- 总行 320；Type: I=34, I+EE=11, II=235, II+SNph=19, II+SNsp=21
- Type I=45（14.06%）、Type II=275（85.94%）
- Type I 中位数：T90z 0.27 s / Epz 706 keV / Eiso 0.69（×10⁵¹ erg）
- Type II 中位数：T90z 14.50 s / Epz 446 keV / Eiso 100.0
- T90,z<2 s = 64（20.0%）；Type I 短暴 42/45=93.3%；Type II 短暴 22
- 事件：060614A=I+EE、980425B=II+SNsp、171205A=II+SNsp、110402A=I+EE；200826A 不在 M20
- 结论：**supported**（M20 目录人口结构层面）

## 复现校验命令
```bash
python3 code/verify_probe.py          # 期望: 320 / 45 / 0.27 全 PASS
sha256sum data/tablea1.dat            # 期望 b84d3a7f…0f0a
awk 'length($0)>152 {print NR}' data/tablea1.dat | wc -l   # 0（行宽 ≤152）
```