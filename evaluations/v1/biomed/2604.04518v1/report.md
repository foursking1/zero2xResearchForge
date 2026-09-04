# EVAL REPORT: 2604.04518v1（捷径学习修正可复现性）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判）
- 评测时间: 2026-08-13

## 总分: 72 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 35 | 60 | R01 精确命中（50.1% vs 51.1±2.5）；CFKD/DFR/SpRAy 结构复现但多数数据集修正后 AGA 未达论文水平（CPU 训练缩减） |
| B 证据真实性 | 25 | 25 | 全部数字实跑（train→eval 全链路）；evidence 表逐行定义；代码完整可运行 |
| C 方法与报告 | 12 | 15 | solution.md 完整（含 limitation 9 条）；训练缩减如实披露；SpRAy 用自动谱聚类替代论文手工 Virelay |

## A 核心结果达成度（35/60）

| 规则 | 锚值 | agent 值 | 判定 |
|---|---|---|---|
| R01 Squares-sym ERM acc | 51.1±2.5 | 50.125% | ✅ 差 0.98pp |
| R02 Squares-sym ERM AGA | 1.8 | 0.5%（wga=0.5%） | ⚠️ 同为低 AGA 方向对 |
| R03 9 学生 EMP>AGA | trend | squares-sym 50.1 vs 50.1（持平） | ⚠️ 部分 |
| R04 修正法（CFKD/P-ClArC）优于 | trend | CFKD squares-sym wga 0.075 vs DFR 0.005 | ✅ CFKD 改善 WGA |
| R08 SpRAy Squares 近完美 | 100 | 100%（layer12）/ 96.9%（layer6） | ✅ |
| R09 SpRAy Blond 少数族 | 20 | 见 spray 数据 | ⚠️ 部分 |

→ R01/R08 精确命中，R04 方向成立（CFKD 改善 WGA），但多数据集修正后 AGA 未达论文（CPU 训练 150 epoch vs 300）。约 35/60。

## B 证据真实性（25/25）

- 训练→评估全链路实跑（students_final/*.pt checkpoints + evaluate）；DFR 修正 time_s=690s 有记录
- evidence 表逐行含 definition；metrics.json 结构清晰（students/corrections/cfkd/spray）
- 无编造；限制如实披露（9 条 limitation：CPU-only、epoch 减半、SpRAy 自动聚类替代、128×128 渲染）

## C 方法与报告（12/15）

- C1 方法（5/5）：完整复现论文训练+修正流程（ERM 学生 → DFR/CFKD 修正 → SpRAy 标签）
- C2 稳健性（4/5）：多数据集 × 多 poison 对照；缺多 seed
- C3 报告（3/5）：solution.md 有大量结构（数据/方法/表格/限制）但部分结论表（Judgment、Overall judgments）仍留空模板

## 结论

- **科学结论**：`partially_supported`——ERM 学生性能可复现（R01 命中），CFKD 修正方向成立，SpRAy 标签质量高；但多数数据集修正后绝对 AGA 低于论文（训练缩减所致，agent 如实披露）
- 重型训练任务（6.2GB），agent 以缩减规模完成全链路复现，诚实标注偏差
- 备注：补跑后结果已齐（20:19 生成 evidence/metrics），可作为评测依据
