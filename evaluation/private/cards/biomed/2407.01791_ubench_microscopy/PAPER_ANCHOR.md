# 论文锚：2407.01791_ubench_microscopy

## 锚清单（全部来自论文，禁止臆造）

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | GPT-4o 粗粒度感知准确率 | 62.6% | Table 1（Macro-average accuracy，Coarse-Grained Perception） | μ-Bench perception Closed VQA 粗粒度任务宏平均准确率（含 bootstrap CI） | 相对差 ≤25% 满分档 |
| 2 | GPT-4o 细粒度感知准确率 | 51.7% | Table 1（Fine-Grained Perception） | 同上口径细粒度任务 | 相对差 ≤25% 满分档 |
| 3 | GPT-4o 认知任务准确率 | 62.0% | Table 1（Cognition） | μ-Bench cognition 任务准确率 | 参照锚 |
| 4 | 通用 vs 专用模型差距 | 病理特定感知：GPT-4o 超 BiomedCLIP 39.37pp（粗粒度）/ 19.40pp（细粒度） | §4（Table 1 讨论） | 通用自回归模型 vs 专用对比模型的病理任务差距 | 方向性锚 |

## 备注
- 主论断：当前 VLM（含最强 GPT-4o）在显微镜感知/认知上错误率高；专用模型并非总优于通用模型。
- 论文出处：arXiv:2407.01791，Table 1 与 §4；数值以论文 PDF 为准。冻结数据为 perception 7 个测试分片之一。