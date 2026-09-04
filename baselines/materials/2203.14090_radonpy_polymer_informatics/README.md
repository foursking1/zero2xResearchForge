# Agent Solution — 2203.14090 RadonPy Polymer Informatics

**结论：`supported`**。冻结 `PI1070.csv`（1,077 行 × 157 列 × 20 类）重算，论文成功数 1,070 / 1,001 / 759 精确复现；性质分布物理合理且与实验趋势方向一致。

## 目录
```
agent_solution/
├── claim.md                     # 四档结论 + 关键数字
├── solution.md                  # 方法说明与结果（简版）
├── report.md                    # 完整报告（方法/结果/局限/结论）
├── README.md                    # 本文档
├── code/
│   ├── analysis.py              # 主分析：统计/分布/成功数/类间/TC分解/top-8/图
│   └── experiment_consistency.py# 实验一致性方向性检验（对照讨论）
├── results/
│   ├── evidence_table.csv       # property,metric,value 证据表
│   ├── metrics.json             # 全量结构化指标
│   └── experiment_consistency.json
└── evidence/
    ├── property_distributions.png   # density/TC/RI/Cp 直方图
    ├── TC_by_class.png              # 跨 polymer_class 平均热导率
    ├── failure_by_family.csv        # _count==0 失败分布
    ├── top_TC_polymers.csv          # top-8 高热导率聚合物
    └── exp_consistency_table.csv    # 实验一致性方向表
```

## 复现（判方重算用）
依赖：`numpy`, `pandas`（图需 `matplotlib`，可选）。Python ≥3.8。

```bash
# 1) 主分析（数据自动定位：任务 data/PI1070.csv 或 /mnt/f/dataset/.../PI1070.csv）
python3 code/analysis.py [PI1070.csv 可选显式路径]

# 2) 实验一致性方向性检验
python3 code/experiment_consistency.py [PI1070.csv 可选显式路径]
```

运行时间：秒级（1,077 行纯表格统计）。随机种子固定为 42，输出确定性一致。

## 关键数字速查
| 指标 | 值 | 论文/锚 |
|---|---|---|
| 行 × 列 | 1,077 × 157 | 冻结清单一致 |
| 唯一 monomer_ID | 1,077 | 1,070（成功口径差异见 report §4） |
| polymer_class | 20 | 20 |
| ≥1 / ≥3 / ==5 次成功 | **1,070 / 1,001 / 759** | 1,070 / 1,001 / 759 ✅ |
| density 均值 (g/cm³) | 1.1326 | 抽查区间 0.83–1.4 ✅ |
| thermal_conductivity 均值 (W/m/K) | 0.2397 | 无定形 0.08–0.5 量级 ✅ |
| refractive_index 均值 | 1.5492 | 无名形 1.28–1.75 量级 ✅ |
| Cp 均值 (J/kg/K) | 3085.5 | 部分偏移（经典力场高估，caveat） |

## 判定链
1. 数据统计正确（A1）→ 成功数精确一致（A3 规模核验）
2. 性质分布物理合理（A2，含 `_min/_max/_std/_count` 统计列解读）
3. 与实验趋势方向一致：97–99% 计算值落入公认实验区间、跨类 TC 走势与刚性/氢键机制吻合（A3 方向性）
4. 结论：**supported**；局限：无 PoLyInfo 实验值列，无法逐点重算 Fig.4/5。