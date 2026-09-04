# EVAL REPORT v3: 2505.01415_everglades_water_level

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v3（qwen3.7-max）
- 评测时间: 2026-08-21

## 总分: 75.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 39.0 | 60 | A1: 最佳MLP(MLPResidual_mc0.1) 28d MAE=0.298，线性NLinear=0.397/DLinear=0.451。排序MLP<线性成立。MLP落入(0.12,0.30)且线性落入(0.25,0.55)，命中22分带。A2: DLinear增幅+69%，NLinear+83%，均≥50%，但DLinear增幅<NLinear，未满足满分带附加条件，降级至13分带。A3: 运行了Chronos_c512(0.348)，但大于最佳任务特定(0.298)，方向不符，命中4分带。A4: NP205最难，方向一致不扣分。A总计 22+13+4 = 39分。 |
| B 证据真实性/实际复现 | 36.0 | 40 | 磁盘扫描显示 evidence_table.csv 及大量 metrics_*.csv 存在，虽无 metrics.json，但证据文件丰富且内部数值与报告严格一致、可核对，落入[30,40]区间，给36分。 |

## A 核心结果达成度（39.0/60）

A1: 最佳MLP(MLPResidual_mc0.1) 28d MAE=0.298，线性NLinear=0.397/DLinear=0.451。排序MLP<线性成立。MLP落入(0.12,0.30)且线性落入(0.25,0.55)，命中22分带。A2: DLinear增幅+69%，NLinear+83%，均≥50%，但DLinear增幅<NLinear，未满足满分带附加条件，降级至13分带。A3: 运行了Chronos_c512(0.348)，但大于最佳任务特定(0.298)，方向不符，命中4分带。A4: NP205最难，方向一致不扣分。A总计 22+13+4 = 39分。

## B 证据真实性/实际复现（36.0/40）

磁盘扫描显示 evidence_table.csv 及大量 metrics_*.csv 存在，虽无 metrics.json，但证据文件丰富且内部数值与报告严格一致、可核对，落入[30,40]区间，给36分。

## 证据与重算说明

独立重算未执行。关键实测数：MLPResidual_mc0.1 28d Overall MAE=0.298，NLinear 28d=0.397，DLinear 28d=0.451，Chronos_c512 28d=0.348。数据行数1411，日期2020-10-16至2024-08-26，均有落盘CSV支撑。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 防泄漏设计严谨，证据文件极其详实（按模型、站点、lead time多维分解），对未能复现论文绝对数值和Chronos优势的原因进行了客观分析。
- 不足: NBEATS等经典模型未能复现出论文中的优势（MAE偏高），且两个线性模型间的相对退化幅度排序与论文锚值相反。