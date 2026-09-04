# agent_solution — 2401.11052 材料文献 LLM 抽取评测（重算）

端到端重算论文 Foppiano et al. 2024（arXiv 2401.11052）的三场景评估表，
只读冻结数据，不调用模型、不生成预测。

## 快速复现

```bash
bash agent_solution/run_all.sh        # 全量：NER + MeasEval + RE + 证据表
python3 agent_solution/code/verify_anchors.py   # rubric 抽查的两个关键数字
python3 agent_solution/code/verify_inputs.py    # 输入完整性（160/160 SHA-256）
```

- 输入：`data/dataset/`（冻结快照；物理位置见 `data/DATA_LOCATION.md`
  = `F:\dataset\materials\2401.11052_llm_materials_mining\`，已挂载于
  `/mnt/f/...`，本地副本校验一致）。
- 依赖：python3（标准库；无需 GPU/网络/pandas）。
- 产出：`results/evidence_table.md`（证据表），`results/*_summary.csv`
  （mean±std 表），`results/*_runs.json`（逐 run），`work/`（中间 NDJSON），
  `evidence/`（错误分析）。

## 结构与说明

| 文件 | 内容 |
|---|---|
| `solution.md` | 方法 + 结论（精简） |
| `report.md` | 完整报告：口径、三场景全表、错误分析、局限 |
| `code/*.py` | 离线评估管线（严格/软/公式匹配的重实现） |
| `results/` | 证据表与汇总 CSV |
| `evidence/` | 关键证据导出（新公式匹配、strict 误配样例、shuffled 明细） |

## 关键数字（详见 report.md）

- 材料 NER zero-shot strict F1（gpt35, run1）= **17.01**（= 论文 17.01）
- 性质 NER 零样本无 LLM 超 grobid（soft 59.67）；gpt4 zero-shot run1 soft =
  **58.97**；few-shot gpt4/4-turbo +2.1/+5.1
- RE 微调 gpt35 strict micro = **84.64**（≥3 变体与论文 repo 合并值 84.53/85.61/84.09 对上）
- 打乱效应：gpt35 zero-shot RE 67.7→61.8（-5.9），gpt4/4-turbo ≤1.6

## 已知局限

离线/无白名单外依赖：公式匹配用 `code/formula_match.py` 本地近似（约 35 F1 而非
论文 Grobid 的 44.8）；Sentence-BERT 列为论文参考值；RE 规则基线为论文引用。
详见 `report.md` §6。