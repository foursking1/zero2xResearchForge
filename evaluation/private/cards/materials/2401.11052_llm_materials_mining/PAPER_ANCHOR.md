# PAPER_ANCHOR: 2401.11052_llm_materials_mining（私有）

目标论文（隐藏）：Foppiano, Lambard, Amagasa, Ishii. *Mining experimental data from Materials Science literature with Large Language Models: an evaluation study.* arXiv:2401.11052 (2024)；正式版 Sci. Technol. Adv. Mater. Methods (2024), DOI 10.1080/27660400.2024.2356506。锚全部摘自论文正文/附录表格与公开评测仓库聚合文档，禁臆造。

## 锚 1（材料 NER，SuperMat holdout）
- 指标：GPT-3.5-Turbo zero-shot 材料实体 NER F1（micro）
- 论文数值：strict F1 = **17.01**（P 22.57 / R 13.65）；formula 匹配 F1 = **45.31**（P 61.12 / R 36.00）——repo run1 为 44.83；F1 增益 **+28.3（+266%）**；新增 176 匹配中人工复核 5 个错误（错误率 **2.5%**）
- 出处：Sec 3.2（公式匹配评估，"P: 22.5%, R: 13.64%, F1: 17.01%... additional 176 matches (P: 61.12%, R: 36.00%, F1: 45.31%)... total gain in F1-score of 28.3 (+266%)... error rate of 2.5%"）；Appendix Table A（各 run）
- 口径：SuperMat holdout（32 文件，期望 1402 记录），strict/soft/formula/Sentence-BERT 匹配
- 容差：±1.0 F1 点

## 锚 2（性质 NER，MeasEval）
- 指标：性质/量词 NER F1（soft 匹配）
- 论文数值：zero-shot 下**无 LLM 超过 grobid-quantities 基线**；few-shot 仅 GPT-4/GPT-4-Turbo 增益 **~2%**；GPT-4 zero-shot soft F1 ≈ **58.97**（run1）vs Sentence-BERT **62.48**
- 出处：Sec 3.3（"none of the models outperformed grobid-quantities in zero-shot prompting... few-shot... marginal improvement... only for GPT-4 and GPT-4-Turbo, resulting in an F1-score gain ranging around 2%"）；Appendix Table A2（GPT-4 zero-shot properties）
- 口径：MeasEval 全量；soft 匹配
- 容差：±1.5 F1 点

## 锚 3（RE，SuperMat 全量）
- 指标：材料→性质关系抽取 F1（strict micro）
- 论文数值：fine-tuned GPT-3.5-Turbo 超规则基线 **约 15% F1**；FT 模型 strict micro F1 ≈ **84.5–85.6**（FT.base/augmented，shuffled/非 shuffled）；GPT-4/GPT-4-Turbo few-shot 超基线但比 fine-tuned GPT-3.5-Turbo 低 **15–18%**；GPT-3.5-Turbo zero-shot/few-shot 存在 shuffled 差异
- 出处：Sec 3.5（"the fine-tuned GPT-3.5-Turbo model outperforms the baseline by approximately 15% F1-score and does not show relevant differences... under shuffling"；"GPT-4 and GPT-4-Turbo... achieving an F1-score of around 15-18% lower than fine-tuned GPT-3.5-Turbo"）；公开仓库 `docs/evaluation/re/supermat.md`（FT strict micro 84.53/85.61/84.09 等）
- 口径：SuperMat 全量（期望 1,143 关系）；strict 匹配
- 容差：±2 F1 点

## 总结论锚（qualitative）
- Q1：LLM 在 NER 上显著低于 SLM（材料/性质抽取）→ "LLMs underperform significantly on NER tasks than SLMs"（Sec 5）
- Q2：微调 GPT-3.5-Turbo 与 few-shot GPT-4/4-Turbo 在 RE 上超过规则基线 → "specialised models are currently a better choice for tasks requiring extracting complex domain-specific entities like materials"（Abstract/Sec 5）
- 出处：Abstract；Sec 5 Conclusion
