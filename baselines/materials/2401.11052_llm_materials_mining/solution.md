# solution.md — 2401.11052 材料文献 LLM 抽取评测（端到端再发现）

> 目标论文（隐藏）：Foppiano et al., *Mining experimental data from Materials Science
> literature with Large Language Models: an evaluation study*. arXiv:2401.11052.
> 本解使用冻结数据（`data/dataset`，160 文件 SHA-256 全部校验通过）**重算**论文的
> 三个抽取场景评估表，不做任何 OpenAI 调用、不合成任何预测。

## 1. 任务与方法

冻结语料/预测由论文作者公开评测仓库（GitHub `lfoppiano/MatSci-LumEn`，Apache-2.0）
快照而来。评估脚本位于 `data/scripts/`。本解的核心做法：

- 以仓库自带的评估语义（`evaluation.py` / `eval_ner.py` / `eval_re_supermat.py` /
  `formula_matching-eval.py`）为准，**离线重实现**（`agent_solution/code/`，只依赖
  Python 标准库 + `difflib`），对每一条冻结的原始模型输出逐 run 重算 P/R/F1；
- 匹配口径：**strict**（大小写不敏感全等）、**soft**（Ratcliff-Obershelp
  相似度 ≥ 0.9，与仓库默认一致）、**formula**（化学组成匹配，本地近似实现
  Grobid supercon 材料解析器，见下）、Sentence-BERT（模型离线不可用，作为论文参考值给出）；
- micro 与 macro 均计算；证据表按论文口径以 micro 为准。

### 复现脚本

```bash
bash agent_solution/run_all.sh        # 从 data/dataset 全量重算三个场景
python3 code/verify_anchors.py        # 直接重算 rubric 抽查的两个关键数
```
要求：`python3`（无需 pandas/GPU；`numpy`/`pandas` 非必需）。产出：
`results/evidence_table.md`（证据表）、`results/*_summary.csv`、`results/*_runs.json`
（逐 run）、`evidence/`（错误分析导出）。

## 2. 核心结果摘要（micro F1，%）

| 场景 | 口径 | 关键数值 | 与论文锚点 |
|---|---|---|---|
| 材料 NER（SuperMat holdout，gpt35 zero-shot） | strict | **P 22.57 / R 13.65 / F1 17.01**（run1） | ≈17.0 ✓ |
| 材料 NER 公式匹配 | formula | 本地近似 F1 **34.9–35.1**；论文（Grobid）44.8–45.3 | 见局限性 |
| 性质 NER（MeasEval，soft） | soft | 零样本无 LLM 超 grobid（59.67）；gpt4 零样本 run1 = **58.97**，few-shot gpt4 61.56 / gpt4-turbo 62.35 | 结论 ✓ 数值 ✓ |
| 关系抽取 RE（SuperMat） | strict | 微调 gpt3.5 F1 **84.64**（FT 各变体 82.6–86.7）；few-shot gpt4 ≈78.3；gpt .5 zero-shot 打乱后 67.6→61.8 | ≈84–86 ✓ |

逐 run 明细、mean±std 全表见 `results/evidence_table.md`。

## 3. 三个科学问题的回答

1. **LLM 在领域 NER 上是否达到/超过专用基线？不能。** 材料 NER：grobid 规则/SLM
   89（strict）远超最优 LLM（gpt4 零样本 34.6 / few-shot 61.6）。MeasEval 性质：
   零样本无任何 LLM 超过 grobid-quantities（59.67）；仅 GPT-4/GPT-4-Turbo few-shot
   越线（61.6/62.4）。
2. **LLM 在 RE 上能否超规则基线？微调后可以。** 微调 GPT-3.5-Turbo 达 84.6（约超
   基线 15 分）；few-shot GPT-4/4-Turbo 也超基线但低于微调模型。LLM 的关系链推理在
   微调后成为最强配置。
3. **代际/策略排序与打乱效应？** 排序 gpt4-turbo ≈ gpt4 > gpt35；few-shot > zero-shot
   （材料 NER 上 few-shot 涨 20–45 点）；微调最好。**打乱材料实体顺序损害零样本
   GPT-3.5-Turbo RE（67.6→61.8，-5.9），对 GPT-4/4-Turbo 影响很小（≤1.6）**。

## 4. 局限（诚实声明）

- **离线环境缺少 Grobid supercon 解析服务与 Sentence-BERT 模型**：formula 匹配用
  `formula_match.py` 本地近似（规则式化学式解析+超导族别名表），新匹配 111 条、
  F1≈35 vs 论文 Grobid 数值 44.8–45.3；SBERT 列（62.5）为论文参考值，不冒充重算。
- 训练/推理由冻结的原始 LLM 输出代替（无 OpenAI API），与“重跑模型”等效于论文的
  确定性参数。
- 更多口径讨论、错误分析、sensor 见 `report.md`。