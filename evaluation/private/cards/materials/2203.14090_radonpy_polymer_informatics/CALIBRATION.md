# 难度校准：2203.14090_radonpy_polymer_informatics（L1）

## 设计目标区间
- L1 目标：**40-50**（满分 100，可接受 30-60）。

## 校准杠杆
- 提示粒度：给出 CSV 结构、推荐性质列（density/thermal_conductivity/refractive_index/Cp）、统计口径；无需重跑 MD。
- 锚容差：A3 方向性 + 分布量级。
- 证据抽查：B 抽查行/列数 + density 均值重算。
- 数据规模：~1.5MB，秒级。

## 自测执行
- **自测执行：待评测阶段执行（本批次跳过）。** 按用户指令（2026-08-13）本批次不跑自测/评测实验；不产生 agent_solution/EVAL_REPORT。

## rubric 定锚
- A：60（数据与协议 20 / 性质分布 20 / 主论断 20）；B：25（2 字段抽查）；C：15（方法/解读/报告）。
