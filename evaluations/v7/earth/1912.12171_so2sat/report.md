# EVAL REPORT v7: 1912.12171_so2sat

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v7（qwen3.7-max）
- 评测时间: 2026-08-24

## 总分: 62.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A1 交付实质 | 12.0 | 12 | |
| A2 科学结论保真 | 10.0 | 33 | |
| A3 方法严谨与可复现 | 15.0 | 15 | |
| **A 合计** | **37.0** | 60 | A1: 核心交付物完整，包含metrics.json、evidence_table.csv及可运行代码，机器可读结果齐全(12分)。A2: 结论声明为supported，但实测核心指标OA(0.9747)与锚点(0.61)相对差达59.8%，严重偏离。按规则'supported但数字偏离A2≤10'，给10分。A3: 方法严谨，主动发现并量化数据集空间泄漏缺陷，训练集单独归一化，代码可复现(15分)。 |
| B 真值一致性/可验证性 | 25.0 | 40 | truth_check=diverged | agent数 0.9747 vs 锚点 0.61 (ResNeXt-CBAM OA) → 严重偏离；agent数 0.9723 vs 锚点 0.58 (Kappa) → 严重偏离；agent数 0.6748/0.8086 vs 锚点 0.54 (SVM OA) → 偏离。虽然agent准确指出了冻结validation集内部空间自相关(83.7%同标签近邻)导致协议差异和数值膨胀，科学解释合理且方向一致，但绝对数值与论文真值不匹配，属于diverged。按规则supported且truth_check≠matched时B≤25，给25分。 |

## A 核心结果达成度（37.0/60 = A1 12.0 + A2 10.0 + A3 15.0）

A1: 核心交付物完整，包含metrics.json、evidence_table.csv及可运行代码，机器可读结果齐全(12分)。A2: 结论声明为supported，但实测核心指标OA(0.9747)与锚点(0.61)相对差达59.8%，严重偏离。按规则'supported但数字偏离A2≤10'，给10分。A3: 方法严谨，主动发现并量化数据集空间泄漏缺陷，训练集单独归一化，代码可复现(15分)。

## B 真值一致性/可验证性（25.0/40）[truth_check=diverged]

agent数 0.9747 vs 锚点 0.61 (ResNeXt-CBAM OA) → 严重偏离；agent数 0.9723 vs 锚点 0.58 (Kappa) → 严重偏离；agent数 0.6748/0.8086 vs 锚点 0.54 (SVM OA) → 偏离。虽然agent准确指出了冻结validation集内部空间自相关(83.7%同标签近邻)导致协议差异和数值膨胀，科学解释合理且方向一致，但绝对数值与论文真值不匹配，属于diverged。按规则supported且truth_check≠matched时B≤25，给25分。

## 证据与重算说明

独立重算未执行。关键实测数(落盘)：ResNeXt-CBAM(S2) overall_accuracy=0.974699, kappa=0.972313；SVM(PCA S2) OA=0.6748；redundancy_nn.json显示83.7%同标签近邻。证据等级2，无claim.md真值对照文件，但metrics.json与evidence_table齐全且内部自洽。

## 结论

- **科学结论**: `supported`
- **可验证性**: `diverged`
- 亮点: 科学素养极高，主动发现并量化了冻结数据集固有的空间自相关缺陷，对数值偏离给出了无懈可击的协议差异解释，且未伪造数据迎合锚点。
- 不足: 受限于冻结数据协议，绝对数值与论文跨城市泛化真值严重偏离，无法在数值上直接复现论文锚点。