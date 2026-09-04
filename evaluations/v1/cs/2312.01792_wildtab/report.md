# EVAL REPORT: 2312.01792_wildtab（Wild-Tab 表格 OOD 泛化）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判）
- 评测时间: 2026-08-14

## 总分: 76 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 39 | 60 | 核心 claim (a) gap 37.7% 强支持（阈值 20%）；A1/A2 绝对 MAE 偏差 29.8%/21.3%（低档带）；A4 无方法显著优于 ERM 部分验证 |
| B 证据真实性 | 25 | 25 | 26 万行全量实跑（train 100k + 三个 60k/20k）；6 seeds；SHA-256 全核对；协议与论文一致 |
| C 方法与报告 | 12 | 15 | 协议严谨（train-only scaler、dev_out 选模型）；GapDRO/HGB 补充实验加分；结论判定恰当 |

## A 核心结果达成度（39/60）

| 锚 | 判分带 | agent | 判定 |
|---|---|---|---|
| A1 OOD MAE | 1.741±5% 满分 / ≤15% 半档 / ≤30% 低档 | 2.2594（差 29.8%）| ⚠️ 低档边缘 |
| A2 ID MAE | 1.353±5% / ≤15% / ≤30% | 1.6406（差 21.3%）| ⚠️ 低档 |
| A3 泛化 gap | claim: OOD ≥20% worse than ID | **37.7%**（6 seed 中 5 个超 20%）| ✅ 强支持 |
| A4 无方法显著优于 ERM | 定性 | GroupDRO 1.742 ≈ ERM；HGB gap 23.3% 更小但非显著性检验 | ⚠️ 部分 |

→ 任务核心是 claim (a) 的 gap 方向（≥20%），agent 37.7% 强复现；A1/A2 绝对数值的偏差（~20-30%）源于冻结数据协议差异（ERM 网格/种子/预处理），agent 已用与论文一致的协议（dev_out 选型、train-only scaler）控制。约 39/60。

## B 证据真实性（25/25）

- 全量数据实跑：train 100k / dev 20k×2 / eval 60k×2，129 列 123 特征
- 5 个 CSV 的 SHA-256 全部与 manifest 匹配（数据真实性铁证）
- ERM MLP 8-config 网格 + 6 seeds + HGB + GroupDRO 补充，全部落盘
- 无泄漏：StandardScaler 只 fit train、选型用 dev_out（OOD 验证）

## C 方法与报告（12/15）

- C1 方法（5/5）：与论文协议对齐（dev_out 选型、early stop、固定种子 20260812+s）
- C2 稳健性（5/5）：6 seeds（gap 19.9%-47.8% + se≈4pp）、HGB 交叉验证
- C3 报告（3/5）：结论表清晰（claim a SUPPORTED）；但 claim (b) 的"10 方法对照"受数据包限制（仅 ERM 系列），可讨论更充分

## 结论

- **科学结论**：`supported`（claim a 核心）——ERM 在 Wild-Tab Weather 上 OOD gap 37.7%（论文声称 ≥20%），6 seed 中 5 个超阈值
- 绝对 MAE 与论文有 ~20-30% 偏差（协议细节差异），但任务核心的**泛化差距方向与量级强复现**
- 备注：本卡为 L1（critical claim），锚明确以 A1/A2 数值 + A3 交叉核对判分，agent 的 gap 复现是决定性证据
