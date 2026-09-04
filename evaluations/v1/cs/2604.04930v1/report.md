# EVAL REPORT: 2604.04930v1（CoDE-Stop 置信度早停）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判）
- 评测时间: 2026-08-13

## 总分: 82 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 45 | 60 | R01 压缩率 47.0%（GPQA 子集）/ 43.5%（thr 0.75）落入 50-75% 带下沿附近；R02 部分成立（GPQA 保精度，AIME 未保）；数据仅 1 模型 3 benchmark 子集 |
| B 证据真实性 | 25 | 25 | 全部数字由脚本实算（analyze_codestop.py 实现论文 Eq.1-4）；代码可运行；多 JSON 交叉一致 |
| C 方法与报告 | 12 | 15 | solution.md 完整；诚实标注子集限制与 inconclusive 判定；报告深度略欠（无 bootstrap 区间） |

## A 核心结果达成度（45/60）

| 规则 | 锚值 | agent 值 | 判定 |
|---|---|---|---|
| R01 CR 50-75% | 50-75% | 47.0%（AIME scisolve）/ 43.5%（GPQA thr 0.75） | ⚠️ 下沿附近（GPQA 0.435 略低于 50% 下沿） |
| R02 精度保持 ≤2pp | trend | GPQA thr0.75: 0.8（基线 0.8）保持；AIME 未保持 | ⚠️ 部分 |
| R03 CR 低于全部基线 | trend | 47.0% > DEER 38.3% | ❌ 未全面优于 |
| R05 4 prompting 策略 | trend | 4 策略 accuracy 0.2-0.5 存在但无置信度序列 | ⚠️ 无法测试（inconclusive） |

→ 冻结数据仅覆盖 1 模型（Qwen3-4B）+ 3 benchmark 子集（论文用多模型），R01 部分命中、R02 部分成立；agent 诚实判定 C01=partially_supported、C02=inconclusive。约 45/60。

## B 证据真实性（25/25）

- analyze_codestop.py 实现论文 Eq.1-4（置信度动力学早停），从冻结 public_data 实算
- metrics.json 与 metrics_repro.json 交叉一致；evidence_table.csv 行级可重算
- 4 张图（fig1-4）由脚本生成，数据完整

## C 方法与报告（12/15）

- C1 方法（5/5）：CoDE-Stop 算法严格按论文公式实现；token 口径（reasoning+tokens）清晰
- C2 稳健性（4/5）：多阈值扫描（thr 0.75/0.80/0.95）；无 bootstrap 区间
- C3 报告（4/5）：solution.md 结构完整（数据源/方法/结论/限制）；诚实标注子集局限；4 策略基准确认

## 结论

- **科学结论**：`partially_supported`（C01）+ `inconclusive`（C02）——冻结数据子集（1 模型 3 benchmark）上压缩率约 43-47%（锚带下沿），精度保持仅 GPQA 成立
- agent 诚实处理数据局限，未过度声明；B 满分，A 受数据覆盖限制
