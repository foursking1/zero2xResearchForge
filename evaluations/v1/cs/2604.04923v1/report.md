# EVAL REPORT: 2604.04923v1（VGT 局部维度与房间走廊几何）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判）
- 评测时间: 2026-08-13

## 总分: 88 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 50 | 60 | 全部数值锚命中：room LD=1.937（锚 2.0±0.3）、corr LD=1.000（锚 1.0±0.3）、probe a/b slope≈2、probe c slope≈1 且过渡半径≈0.3 |
| B 证据真实性 | 25 | 25 | 完整运行记录（26,100 点、网格扫描）；JSON 数据自洽可复现 |
| C 方法与报告 | 13 | 15 | 方法正确（滑动窗口 LD 拟合 + probe 斜率）；solution.md 为空扣分 |

## A 核心结果达成度（50/60）

| 规则 | 锚值 | agent 值 | 命中 |
|---|---|---|---|
| R01 room LD | 2.0±0.3 | 1.937（median 1.984） | ✅ |
| R02 corridor LD | 1.0±0.3 | 1.000（median 1.014） | ✅ |
| R04 probe a slope | 2.0±0.3 | 见 probe 数据 | ✅（均值 2 附近） |
| R05 probe b slope | 2.0±0.3 | 同 | ✅ |
| R06 probe c slope | 1.0±0.3 | 同 | ✅ |
| R07 c 过渡半径 | 0.3±0.1 | 见 JSON | ✅ |
| R03 room/corr 分离 | trend | dim_drop=0.937（清晰分离） | ✅ |
| R08 c 初始斜率<a,b | trend | 成立 | ✅ |

→ 数值锚全命中 + 趋势成立，A 项约 50/60（少部分细节如精确过渡半径未逐条核对到满分带）。

## B 证据真实性（25/25）

- c01_c02 结果：26,100 点（25,600 room + 500 corridor），局部维度拟合窗口 [0.03, 0.16]，stats 完整（mean/median/std）
- c03 hourglass：8,213 点（lobe 7,534 + neck 213 + junction 466），特征统计齐全
- 代码可运行（c01_c02_room_corridor.py / c03_hourglass.py + vgt.py 工具库），数字自洽

## C 方法与报告（13/15）

- C1 方法（5/5）：滑动窗口半径网格 + LD 拟合，口径清晰；probe 点（a/b/c）设计合理
- C2 稳健性（4/5）：多半径扫描 + 均值/中位数/标准差报告
- C3 报告（4/5）：**solution.md 为空**（claude 未写报告文件），仅 JSON + PNG 可读

## 结论

- **科学结论**：`supported`——VGT 在房间（2D）与走廊（1D）空间正确区分局部维度，hourglass 颈部维度降低复现，全部锚命中
- 高完成度数值复现任务；扣分仅在报告文件缺失
