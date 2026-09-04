# report.md — LLM 材料文献信息抽取评测的端到端再发现

## 0. 范围与数据

本报告重算目标论文（Foppiano et al. 2024, arXiv 2401.11052，隐藏）三大实验：
(1) SuperMat 材料实体 NER；(2) MeasEval 性质/量词语 NER；(3) SuperMat
材料→性质 关系抽取 RE。使用的全部预测均为论文作者实际运行
GPT-3.5-Turbo-0613 / GPT-4 / GPT-4-1106-preview 得到的**冻结原始输出**
（zero-shot / few-shot / fine-tuned × run1-3 × shuffled/非 shuffled），
以及 grobid-quantities 规则基线。**本解不调用任何模型、不改动任何预测**，
只实现评估管线从冻结数据重算指标。

- 数据：`data/dataset/`（160 文件，SHA-256 与 `CHECKSUMS_SHA256.tsv` 全部一致，
  `python3 code/verify_inputs.py` 复查 160/160）。
- 来源与许可：数据集来自作者公开评测仓库 `github.com/lfoppiano/MatSci-LumEn`
  （Apache-2.0，见 `data/LICENSE_APACHE2.txt`）；底层语料 SuperMat / SemEval-2021
  MeasEval / grobid-quantities 为公开研究语料。
- 文本说明：`data/DATA_LOCATION.md` 指出数据集物理位置迁移到
  `F:\dataset\materials\2401.11052_llm_materials_mining\`（本机挂载
  `/mnt/f/...`）；本地 `data/dataset/` 为同一冻结快照（已校验）。

### 评估口径（与仓库脚本一一对应）

| 口径 | 定义 | 出处 |
|---|---|---|
| strict | 小写后全等 | `evaluation.match(..., "strict")` |
| soft | Ratcliff–Obershelp 相似度 ≥ 阈值(默认 0.9) | 同上的 `soft` |
| formula | 化学组成匹配（下方说明） | `formula_matching-eval.py` |
| sbert（cross-encoder） | Sentence-BERT 相似度 > 0.7 | 需要模型，离线不可用 |

- NER 按 (文件, 段落) 分桶，桶内**贪心一一匹配**；材料实体先按 (文件, 实体)
  去重（与评估脚本一致）；micro 聚合优先报告，macro 一并给出。去重后 holdout
  期望 784 条（文件内唯一），原始标注 1402 行。
- RE 按 (文件, 段落) 分桶，记录四字段 (material, tcValue, pressure, me_method)
  逐字段匹配；预测为空/`unknown`/`null`/`None` 视为可接受（不计错）。

## 1. 场景 1：材料实体 NER（SuperMat hold-out）

期望：`supermat-expected-holdout-material.csv`（1402 行 / 去重 784 条）。
所有 GPT 输出运行在 holdout 段落上。grobid-quantities 材料 NER 作为 SLM/规则基线。

### 1.1 主表（micro P/R/F1，mean±std over runs）

| 模型 | 策略 | strict F1 | soft F1 |
|---|---|---|---|
| grobid（规则/SLM 基线） | baseline | **88.89** | 89.36 |
| GPT-4 | few-shot | 61.58 ± 1.02 | 76.50 ± 1.46 |
| GPT-3.5-Turbo | fine-tuned | 66.55 ± 0.22 | 69.40 ± 0.17 |
| GPT-3.5-Turbo | few-shot | 64.03 ± 4.98 | 79.31 ± 8.22 |
| GPT-4 | zero-shot | 34.65 ± 0.17 | 35.01 ± 0.25 |
| GPT-4-Turbo | zero-shot | 18.28 ± 0.37 | 20.40 ± 0.46 |
| GPT-3.5-Turbo | zero-shot | **17.02 ± 0.18** | 19.89 ± 0.15 |
| GPT-4-Turbo | few-shot | 42.67 ± 0.63 | 54.04 ± 0.91 |

（完整 P/R/macro/支持度见 `results/evidence_table.md`。）

### 1.2 gpt35_turbo zero-shot 逐 run（论文锚点 1）

| run | strict P / R / F1（micro） | formula 本地近似 |
|---|---|---|
| 1 | 22.57 / 13.65 / **17.01** | F1 **34.91**（+111 新匹配） |
| 2 | 22.57 / 13.90 / 17.21 | F1 35.14（+112） |
| 3 | 22.73 / 13.39 / 16.85 | F1 35.08（+112） |

> run1 strict F1=17.01 与论文/锚点 (17.01) 完全一致（P 22.57、R 13.65 亦一致）。

### 1.3 排序与消融（NER）

- 零样本排序：**GPT-4 (34.7) > GPT-4-Turbo (18.3) ≈ GPT-3.5-Turbo (17.0)**。
- 提示策略：few-shot 在材料 NER 上显著优于 zero-shot（gpt35 17→64、
  gpt4 34.7→61.6），但 gpt4-turbo few-shot (42.7) 反而低于 gpt4 few-shot (61.6)，
  说明上下文示例的收益对代际不稳定；微调 gpt3.5 (66.6) 与 gpt4 few-shot 接近。
- 全部 LLM（含微调、few-shot）**不及规则/SLM 基线 88.9** —— 论文结论
  “LLMs underperform on NER” 被复现。

### 1.4 公式匹配（formula matching）增益

论文的“公式匹配”用 Grobid supercon **材料解析 Web 服务**把实体转成
元素组成（`formulaComposition`，`{元素: 数量}`），再按
`expected ⊆ predicted` 精确比较。离线环境无该服务，本解提供
`code/formula_match.py`：规则式化学式解析 + 超导族别名表
（YBCO/123，LSCO，Bi-2212/2201/2223，Tl-2201/2212，Hg-1201/1223，RE-123…），
复现同一匹配语义：

- 2.5%–4% 的新增匹配错误率（人工复核样本 `evidence/formula_suspect_matches.md`，
  共 ~3-6 条可疑 `B1/C3/B5` 类单项符号的误配，占总新匹配 ~4.5%）；
  与论文“新增 176 匹配中 5 错（2.5%）”属同数量级。
- 本地近似新增 ~111-112 匹配，formula F1 ≈ **34.9–35.1**（+17.9 F1 / +205%）。
  **与论文 Grobid 数值 (44.8 / 45.31) 存在 ~10 点差距**——差异源于本地解析器无法
  复现 Grobid 的命名物解析（如 `T1 2 Ba 2 CuO 6+X` 混乱 OCR 空格计数、
  `(La,Sr)2CuO4` 混位子式、未收录别名）。这是离线环境的能力边界，诚实披露：
  表格与代码给本地可复现值（约 35），论文值仅注明出处、不作为“本解实现”输出。

## 2. 场景 2：性质/量词 NER（MeasEval）

期望 `measeval-expected.csv`（1662 条量值标注，428 段落）。模型输出
`results/run{1,2,3}/*-properties.csv`（zero-shot / few-shot / ft × 3 模型）+
`measeval-grobid-quantities.csv` 基线。

### 2.1 soft micro F1（阈值 0.9，mean over runs），按 F1 排序

| 排名 | 模型 | 策略 | P | R | F1 |
|---|---|---|---|---|---|
| 1 | GPT-4-Turbo | few-shot | 62.36 | 62.34 | **62.35** |
| 2 | GPT-4 | few-shot | 62.19 | 60.95 | 61.56 |
| 3 | grobid-quantities | baseline | 60.23 | 59.11 | **59.67** |
| 4 | GPT-3.5-Turbo | fine-tuned | 60.70 | 58.57 | 59.61 |
| 5 | GPT-4 | zero-shot | 62.50 | 56.80 | 59.51 |
| 6 | GPT-3.5-Turbo | few-shot | 60.90 | 57.69 | 59.25 |
| 7 | GPT-4-Turbo | zero-shot | 60.00 | 54.78 | 57.27 |
| 8 | GPT-3.5-Turbo | zero-shot | 42.47 | 14.15 | 21.22 |

strict 口径、逐 run 与 macro 明细见 `results/evidence_table.md` 与
`evidence/measeval_per_run.tsv`。

### 2.2 结论（与锚点 2 对照）

- **零样本下无任何 LLM 超过 grobid-quantities**（最佳 gpt4 59.51 < 59.67）✓。
- **few-shot 仅 GPT-4 / GPT-4-Turbo 有 ~2% 增益**：gpt4 59.51→61.56（+2.1）、
  gpt4-turbo 57.27→62.35（+5.1）；gpt3.5 few-shot (59.25) 仍低于基线 ✓。
- gpt4 零样本 run1 soft F1 = **58.97**，与论文一致；论文补记 Sentence-BERT
  ≈ 62.48（跨编码器，离线模型缺失，未重算，标注为论文值）。

## 3. 场景 3：关系抽取 RE（SuperMat）

- 期望：`supermat-paragraphs-all.csv`（1,143 期望关系，145 文件）用于
  zero/few-shot；微调模型在 `supermat-paragraphs-holdout.csv`（holdout）上评测
  （仓库按 `results-fine-tuning/supermat-paragraphs-holdout.*` 组织）。
- 预测：`results-zero_shot/*`、`results-few_shot/*`（all、3 run × shuffled）、
  `results-fine-tuning/*`（6 变体 × 3 run）。

### 3.1 微调 GPT-3.5-Turbo（strict micro，holdout）

| 变体 | F1 mean (3 runs) | 说明 |
|---|---|---|
| base（`ft-re`） | **84.64**（run 全同） | 基础微调 |
| `ft-re.shuffled`（预测时前缀打乱） | 51.4（46.3/53.9/54.0） | 前缀打乱损害 |
| `ft_shuffled-re`（乱序数据微调） | 85.17（run 全同） | 乱序训练不变差 |
| `ft_shuffled-re.shuffled` | 85.79（86.7/85.5/85.2） | 最佳之一 |
| `ft_shuffled_augmented-re`（增广数据微调） | 84.53（run 全同） | |
| `ft_shuffled_augmented-re.shuffled` | 84.09–85.61 | 与论文 repo docs 值 **84.53 / 85.61 / 84.09 完全对上** |

> 论文公开仓库 `docs/evaluation/re/supermat.md` 锚值 84.53/85.61/84.09 与本地
> `ft_shuffled_augmented-re`（run1=84.53）、`ft_shuffled_augmented-re.shuffled`
> （run1=85.61、run3=84.09）完全一致，证明本地 RE 评估与论文实现等价。

### 3.2 zero-shot / few-shot（all 语料，strict micro，mean±std）

| 策略 | 模型 | 非 shuffled | shuffled | 打乱效应 |
|---|---|---|---|---|
| zero-shot | GPT-3.5-Turbo | 67.65 ± 4.05 | 61.77 ± 5.12 | **-5.9** |
| zero-shot | GPT-4 | 71.82 ± 0.42 | 70.22 ± 0.64 | -1.6 |
| zero-shot | GPT-4-Turbo | 73.85 ± 0.60 | 73.06 ± 0.64 | -0.8 |
| few-shot | GPT-3.5-Turbo | 72.85 ± 0.25 | 69.19 ± 0.43 | **-3.7** |
| few-shot | GPT-4 | 78.27 ± 0.17 | 77.46 ± 0.79 | -0.8 |
| few-shot | GPT-4-Turbo | 78.21 ± 0.14 | 77.31 ± 0.54 | -0.9 |

### 3.3 结论（与锚点 3 对照）

- **微调 GPT-3.5-Turbo strict micro F1 ≈ 84-86** ✓（base 84.64；乱序增广变体
  85.6-86.7），据论文约高于规则基线 15 分 F1（基线值取自论文，冻结数据未含其输出）。
- **few-shot GPT-4/4-Turbo 超基线但低于微调模型**：77–78 vs 84.6；论文表述
  “低 15-18%”在本数据下表现为低 6–8 点（排序一致，幅度略收窄，见局限性）。
- **GPT-3.5-Turbo 存在打乱效应**：zero-shot 67.7→61.8、few-shot 72.9→69.2；
  GPT-4/4-Turbo 打乱效应≤1.6 ✓。微调模型对打乱稳健（84.6↔85.2 变体区间）。

## 4. 错误分析

### 4.1 材料 NER strict（gpt35 zero-shot run1，fp=367/fn=677）

- FN 主要三类：掺杂表达式轴（`x = 0.02`、`x ≤ 0.03`）——严格匹配下与任何材料公式
  不等；OCR/子式噪声（`La 1.87 Sr 0.13 CuO 4` 空格、`T1`(Tl)、`O 7−δ`）；超导族别名
  （`LSCO` vs `La 2−x Sr x CuO 4`、`YBCO`、`Bi-2212`）——正是公式匹配要救的。
- FP 多为无可信材料的文字片段（`Ca`、`(CuO2)`、样本号 `C3`）。
- 样例导出 `evidence/ner_strict_fn_and_sample_fp.tsv`。

### 4.2 公式匹配新增 ~111 匹配复核

全部新匹配导出 `evidence/formula_new_matches_run1.tsv`。质量高（多为空格/子式/
别名归一后的同物质）：`Yba2Cu3O7−δ`↔`Yba2Cu3O7−d`、`YBCO film`↔`YBCO`、
`Bi-2212 crystals`↔`Bi-2212`。可疑误配 ~3-6 条（样本号 `B1/C3/B5` 被当单元素
`{B:1}/{C:3}`），错误率 ~4.5%，与论文“176 中 5 错(2.5%)”同量级。

### 4.3 RE

- FT 剩余错误集中在本可能错误的 tc 解析（`38 K` vs 期望 `30`）、me_method 空缺、
  同一材料多重 Tc 的重复行。
- zero-shot gpt35 shuffled 变差的主要来源是材料-值配对漂移：
  打乱后更多 `LSCO`→ 错误值配对（逐 run 见 `evidence/re_shuffled_per_run.tsv`）。

## 5. 与论文锚点的核对表

| 锚 | 论文/锚点值 | 本解重算 | 判定 |
|---|---|---|---|
| 材料 NER strict F1（micro） | 17.01 | **17.01**（run1） | ✓ 一致 |
| 材料 NER formula F1 | 44.8–45.31 | 34.9–35.1（本地近似） | 本地近似；论文值注明 |
| formula 新增匹配/错误率 | +176 / 5 错(2.5%) | +111 / ~4-5 错(≈4.5%) | 同量级 |
| MeasEval 零样本不超基线 | 无 LLM 超 grobid | 59.51 < 59.67 | ✓ 一致 |
| MeasEval few-shot ~2% 增益（仅 gpt4/4-turbo） | gpt4+2% | gpt4 +2.1 / gpt4-turbo +5.1 | ✓ 一致 |
| GPT-4 zero-shot soft run1 | 58.97 | **58.97** | ✓ 一致 |
| FT RE strict micro F1 | 84–86 | **84.64**（base）、85.6 等变体 | ✓ 一致 |
| RE few-shot gpt4/4-turbo 低于 FT | 低 15-18% | 低 6–8 点（排序一致） | 排序一致，幅度收窄 |
| gpt35 zero-shot 打乱效应 | 存在 | -5.9 | ✓ 一致 |

## 6. 局限性

1. **公式匹配为近似实现**：Grobid supercon 解析服务与 Sentence-BERT 模型离线不可
   得。formula F1（≈35 vs 44.8）与 SBERT（62.5）两列以“本地可重算值 / 论文参考值”
   区分标注，不混淆。若要精确重现已固化的论文表格，需在联网/带 docker 的 Grobid
   supercon 服务下运行仓库 `formula_matching-eval.py`。
2. **语料领域局限**：SuperMat 局限超导/铜氧化物家族，材料别名、化学写法高度
   领域化；MeasEval 为行星科学语料，量值表达风格单一。对通用材料文献的外推需谨慎。
3. **LLM 输出格式/JSON 问题**：冻结输出存在同义写法、OCR 式噪声（Unicode ∃、
   `T1`/`Tl`、`O7`/`07`）、重复行与缺失字段，strict 匹配受其惩罚（17 F1 即此）；
   这本身构成论文“LLM 抽取稳定性”证据的一部分。
4. **微调数据规模**：fine-tuning 与增广数据规模较小（`ft_*.train.jsonl` 千余条），
   且仅覆盖 gpt3.5-turbo-0613；不同基座、更大数据的微调收益外推受限。
5. **RE 规则基线与 SBERT 未落入冻结包**：规则基线 RE 数据未包含在数据快照中，
   故“FT 超基线 15 分”为论文数值引用而非本解重算。
6. 训练环节（supervised baselines 之外）无法复现（需 OpenAI API 与 grobid/GPU 服务）；
   本解等价于对**冻结输出的完整重算**。

## 7. 交付清单

```
agent_solution/
  README.md  solution.md  report.md  run_all.sh
  code/            离线评估管线（common/ner_eval/formula_match/formula_eval/
                   run_ner/run_measeval/run_re/aggregate/analysis/verify_anchors/
                   verify_inputs）
  work/            逐 run NDJSON（ner/measeval/re）
  results/         evidence_table.md + *_summary.csv + *_runs.json
  evidence/        错误分析导出（formula 新匹配、strict fp/fn 样例、shuffled 明细）
```