# Task: 2401.11052_llm_materials_mining（L2 端到端科研再发现）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

## 元信息
- task_id: `2401.11052_llm_materials_mining`
- 层级: L2（RCBench 三段式：input / output / scientific goal；目标论文隐藏，不提供全文）
- 领域: materials（材料科学文献信息抽取评估）

## 任务描述

### Input（输入数据）
- 两个公开标注语料（见 `data/dataset/`，已冻结）：
  - **SuperMat**（超导材料段落语料，`data/dataset/superMat/`）：`entities/` 材料实体 NER 标注（训练/验证 holdout 划分）与文本（`supermat-paragraphs-*.csv`）；`relations/` 材料-性质关系标注（全量 1,143 条期望记录）与文本；各模型逐 run 的**原始抽取输出**（`entities/results/`、`relations/results/`，含 zero-shot / few-shot / fine-tuning × run1-3 × shuffled/非 shuffled）；微调训练数据（`*/ft/`）。
  - **MeasEval**（SemEval 测量/量词语料，`data/dataset/measeval/`）：`measeval-text.csv` 文本、`measeval-expected.csv` 期望标注、`results/` 各模型原始输出（GPT-3.5-Turbo/GPT-4/GPT-4-Turbo × zero-shot/few-shot/ft + grobid-quantities 基线）。
  - **grobid-quantities 语料**（`data/dataset/quantities/`）：性质/量词 NER 微调训练数据。
- 评估脚本与指标实现：`data/scripts/`（evaluation/ner/re 的指标计算与 formula-matching 匹配实现）。
- 所有原始 LLM 输出均为**真实实验数据**（论文作者运行 OpenAI 模型所得，逐 run 保存）。

### Output（要求产出）
- 对三个抽取场景给出**完整评估表**（P/R/F1，strict / soft / formula / Sentence-BERT 匹配口径）：
  1. 材料实体 NER（SuperMat holdout）
  2. 性质/量词 NER（MeasEval）
  3. 材料→性质关系抽取 RE（SuperMat 全量）
- 模型排名、提示策略（zero-shot/few-shot/fine-tuned）消融、shuffled vs 非 shuffled 对比、formula-matching 增益分析。

### Scientific goal（科学目标）
评估 GPT-3.5-Turbo / GPT-4 / GPT-4-Turbo 从材料科学文献中抽取结构化信息（实体与关系）的能力，并与专用模型（BERT 类、规则/量词解析系统）对比，回答：
1. LLM 在**领域实体识别（NER）**上能否达到/超过专用基线？
2. LLM 在**关系抽取（RE）**上能否利用推理能力连接概念，微调/few-shot 后能否超过规则基线？
3. 不同模型代际与提示策略之间的性能排序是什么？"打乱实体顺序"效应是否存在？

（目标论文为 2024 年一篇材料文献挖掘 LLM 评测研究，数据集与其公开评测仓库即本任务数据源。）

## 数据说明
- 目录：`data/`（冻结，160 文件，约 29.5 MB）
- **来源**：论文作者公开评测仓库（GitHub，2026-08-13 抓取；论文 "Code and data availability" 声明指向该仓库）。仓库含评测脚本、SuperMat/MeasEval 数据与全部模型原始输出。
- **许可**：仓库 LICENSE = Apache-2.0（`data/LICENSE_APACHE2.txt`）。底层语料（SuperMat 超导段落、MeasEval SemEval-2021 Task 11、grobid-quantities）为公开研究语料，学术用途；**使用前请按各数据集自身条款审计**（SuperMat/MeasEval 分别在各自 GitHub 仓库发布）。
- **Checksum**：全部 160 文件 SHA-256 见 `data/CHECKSUMS_SHA256.tsv`；核心文件：
  - `dataset/measeval/measeval-text.csv` 337bfebefd5071c4eda8d228438b52abfe9b0d14a9e114d2aaf6b8b3ebad1142
  - `dataset/measeval/measeval-expected.csv` 27606835dfbbf0bbb9e480b77d9b0b29acbb584a54e805de03fa412f18cd45ad
  - `dataset/superMat/entities/supermat-paragraphs-all.csv` a026f292c2194c2d4364d0b942a292807cfffdf7e2988379cc4d7ba50aad5e73
  - `dataset/superMat/entities/supermat-expected-holdout-material.csv` 7409ce842edbc922d4582ecff7a8c4853269ae929ea955bd0cd81a2aac6362d9
  - `dataset/superMat/relations/supermat-paragraphs-all.csv` 4c824b5c7d73db2f2385254b573e293988ecf17d6c49ee96c91315d576674d9b
  - `dataset/quantities/quantities-text.csv` f140aa5b0bf53f0b2d6921b3f7a40f83e49cd8a268906e1d75cb975b49252e89
- **Schema**：语料/期望/预测均为 CSV（id, text/entity/relation 字段）；预测输出在 `results/` 下按 模型×策略×run 组织；评估脚本 `data/scripts/` 内含指标与匹配实现。

## 输出要求
1. **结论**：回答 scientific goal 的三个问题，给出明确的模型/策略排序与"LLM vs 专用基线"判断。
2. **证据表**（`results/evidence_table`）：三个场景 × 模型 × 策略的 P/R/F1（含 strict/soft/formula 口径），formula 增益，shuffled 效应，逐 run 均值±std。
3. **代码**：可运行脚本，从冻结 `data/` 直接重算出证据表中的关键数值（使用或扩展 `data/scripts/` 均可）。
4. **报告**：方法、口径差异、错误分析、局限性。

## 数据铁律提醒
- 只用本任务冻结的真实数据（语料、标注、模型原始输出）；**禁止伪造/合成抽取结果**。
- 禁止把行号、id 顺序等非物理信息当作特征。
- 数据 checksum 已固定（SHA-256）；报告中注明来源与许可（Apache-2.0 + 各语料条款）。
