# EVAL REPORT: 2401.11052_llm_materials_mining

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-20

## 总分: 80.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 44.0 | 60 | A1: agent 报告 strict F1=17.01，落入≈17.0区间（达成）；formula F1=34.9（未达成44.8）；增益+17.9（未达成+28）。达成1项，得10分。A2: agent 报告 zero-shot 无 LLM 超 grobid，few-shot GPT-4 增益+2.1，GPT-4 zero-shot soft F1=58.97。结论与数值均复现，得20分。A3: agent 报告 FT GPT-3.5 strict F1=84.64（落入84-86区间，达成）；few-shot GPT-4 低于 FT 6-8点（未达成15-18%区间）；zero-shot shuffled 效应 -5.9（达成）。达成2项，得14分。A总分 = 10+20+14 = 44。 |
| B 证据真实性 | 22.0 | 25 | 提交物齐全，含可运行代码与证据表（5分）。抽查1：strict F1=17.01完全一致，formula F1=34.9因离线口径差异未达44.8，给5分。抽查2：RE FT strict F1=84.64/84.53等与锚值完全一致（7分）。数据铁律合规，无伪造（5分）。B总分22分。 |
| C 方法与报告 | 14.0 | 15 | 指标口径说明清晰，诚实披露formula近似局限（3分）；三场景覆盖完整且含mean±std（4分）；shuffled与消融分析到位（3分）；局限性声明非常诚实详尽（4分）。C总分14分。 |

## A 核心结果达成度（44.0/60）

A1: agent 报告 strict F1=17.01，落入≈17.0区间（达成）；formula F1=34.9（未达成44.8）；增益+17.9（未达成+28）。达成1项，得10分。A2: agent 报告 zero-shot 无 LLM 超 grobid，few-shot GPT-4 增益+2.1，GPT-4 zero-shot soft F1=58.97。结论与数值均复现，得20分。A3: agent 报告 FT GPT-3.5 strict F1=84.64（落入84-86区间，达成）；few-shot GPT-4 低于 FT 6-8点（未达成15-18%区间）；zero-shot shuffled 效应 -5.9（达成）。达成2项，得14分。A总分 = 10+20+14 = 44。

## B 证据真实性（22.0/25）

提交物齐全，含可运行代码与证据表（5分）。抽查1：strict F1=17.01完全一致，formula F1=34.9因离线口径差异未达44.8，给5分。抽查2：RE FT strict F1=84.64/84.53等与锚值完全一致（7分）。数据铁律合规，无伪造（5分）。B总分22分。

## C 方法与报告（14.0/15）

指标口径说明清晰，诚实披露formula近似局限（3分）；三场景覆盖完整且含mean±std（4分）；shuffled与消融分析到位（3分）；局限性声明非常诚实详尽（4分）。C总分14分。

## 证据与重算说明

独立重算未执行。抽查关键实测数：材料NER strict F1=17.01，formula F1=34.91；MeasEval GPT-4 zero-shot soft F1=58.97；RE FT GPT-3.5 strict F1=84.64。数值与证据表内部一致，且与论文锚值高度吻合（除formula因离线限制外）。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实且严谨地处理了离线环境限制，明确区分了本地近似重算值与论文参考值，未伪造数据；证据表结构完整，逐run明细与均值标准差齐备。
- 不足: 受限于离线环境，formula matching 未能调用 Grobid 服务导致 F1 与增益数值与论文存在较大差距；RE 场景中 few-shot 与 FT 的性能差距未完全复现论文的 15-18% 幅度。