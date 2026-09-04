# SCORE_RUBRIC: 2401.11052_llm_materials_mining（私有）

判分模型：任意一致的 LLM 裁判（Claude / GLM 均可），固定本 rubric；证据抽查需**实际运行提交代码**从冻结数据重算。
总分 100 = A 60 + B 25 + C 15。L2 目标区间 ~30（±10）：端到端再发现，能完成核心评估并给出正确排序者得中高段，仅完成部分场景/口径者得中低段。

## A. 核心结果达成度（60 分）
按三场景关键数值与结论逐项核分（容差 = 报告 F1 与论文值差 ≤ 1.0 个百分点即该项成立）：

1. **材料 NER（SuperMat holdout，GPT-3.5-Turbo zero-shot）**：strict F1 ≈ **17.0**（micro）；formula 匹配 F1 ≈ **44.8**（micro）；formula 增益 ≈ **+28 F1（+266%）**，新增 176 匹配中错误 5 个（~2.5%）。三项中达成 ≥2 → 20 分；1 项 → 10；0 → 0。
2. **性质 NER（MeasEval）**：zero-shot 下**无 LLM 超过 grobid-quantities 基线**；few-shot 仅 GPT-4/GPT-4-Turbo 有 ~2% F1 增益；GPT-4 zero-shot soft F1 ≈ **59**（Sentence-BERT ≈ 62.5）。结论正确且至少一个数值复现 → 20 分；仅结论 → 10。
3. **关系抽取 RE（SuperMat 全量）**：fine-tuned GPT-3.5-Turbo 超规则基线 **~15% F1**（strict micro ≈ **84-86**）；GPT-4/GPT-4-Turbo few-shot 超基线但比 fine-tuned GPT-3.5-Turbo 低 **15-18%**；GPT-3.5-Turbo zero-shot 存在 shuffled 效应。达成 ≥3 → 20 分；2 → 14；1 → 7。

（若 agent 仅因无 OpenAI API 无法重跑 LLM，但用冻结原始输出完整重算指标并得出正确结论 → 不扣分；若伪造"自己跑了模型"的数值 → B 全扣。）

## B. 证据真实性（25 分）
1. 提交含可运行代码 + 证据表（5 分；缺 → 0 且按 3 处理）
2. 裁判抽查 2 个关键数（15 分）：
   - **抽查 1（8 分）**：运行提交代码，从冻结 `data/dataset/superMat/entities/` 的预测 + 期望文件重算 GPT-3.5-Turbo zero-shot strict F1（≈17.0）与 formula F1（≈44.8）；与证据表一致（±0.5）→ 8；一致但实现口径不同（±2）→ 4；无法重算/抄数值 → 0。
   - **抽查 2（7 分）**：重算 RE fine-tuned GPT-3.5-Turbo strict micro F1（≈84-86，从 `relations/results/results-fine-tuning/` 预测 + `supermat-paragraphs-all.csv` 期望）；一致（±1）→ 7；±3 → 4；否则 0。
   - 证据表数值与论文精确相同但代码无法重算 → 判抄写，B 全扣。
3. 数据铁律合规（5 分）：无伪造预测/标签、无把 id/行号当特征；违规 → 0 并 C 连带。

## C. 方法与报告（15 分）
1. 指标/匹配口径实现正确（strict/soft/formula 差异说明）（4）
2. 三个场景覆盖完整、逐 run 均值±std（4）
3. shuffled 效应与提示策略消融分析到位（3）
4. 局限性诚实（语料领域局限、LLM 输出格式/JSON 问题、微调数据规模）（4）

## 结论标签
- **supported**：A ≥ 45 且 B ≥ 20
- **partially_supported**：A 25–44 且 B ≥ 12
- **contradicted**：A < 25 且证据可靠
- **inconclusive**：代码无法运行 / 证据不足
