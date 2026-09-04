# agent_solution — 2608.00352_thermosphere_density

AETHER-P3 热层密度预测论文（arXiv:2608.00352）**评测框架 Dst 锚声称**（Table 3/5）验证包。

## 结论

**`supported`** — C1–C4 全部成立：

| 声称 | 论文锚 | 冻结数据重算 | 出现时刻（UTC） |
|---|---|---|---|
| C1 安静（2024-05-24~31） | −27 nT | **−28 nT**（差 1 nT，版本/舍入归因） | 2024-05-31 19:00 |
| C2 中等（2015-02-01~28） | −69 nT | **−69 nT** | 2015-02-18 00:00 |
| C3 极端（2024-05-10~13） | −406 nT | **−406 nT** | 2024-05-11 02:00 |
| C4 主相 | 05-10 15:00 → 05-13 00:00 | −406 时刻在主相内 ✓ | — |

数据完整性：219,168 行 = 24×9132 天（2000-01-01 → 2024-12-31），无缺口、逐小时；与 `DST.mat` 交叉复算完全一致。

## 目录

```
agent_solution/
├── claim.md                  # 声称 + 结论标签
├── solution.md               # 方法说明与结果
├── report.md                 # 完整报告（≤2 页）
├── code/
│   ├── verify_claims.py      # 完整流程：完整性+交叉源+窗口 min+主相+分类+图表
│   └── recheck_key_numbers.py # 极简抽查（B 维度关键数，仅标准库）
└── results/
    ├── evidence_table.csv    # 逐窗口证据表
    ├── metrics.json          # 总体指标 + SHA-256
    └── figure.{svg,png,pdf}  # Dst 时序 + 三窗口标注图
```

## 复现（在任务根目录）

```bash
python agent_solution/code/verify_claims.py .      # 完整流程（写 results/）
python agent_solution/code/recheck_key_numbers.py  # 抽查关键数
```

依赖：Python 3.10+，`numpy` / `pandas` / `scipy` / `matplotlib`。
数据源：`data/dst_hourly.csv`（论文随附 `DST.mat` 的确定性派生，SHA-256 已核对）。

## 边界

本包仅验证论文**评测框架**（Dst 锚与主相定义）声称；卫星密度数据与模型预测不在此卡数据面内，不作任何预测技能声明。所有数字由代码从冻结数据重算，无手工抄数。