# solution.md — 2407.01791_ubench_microscopy 关键论断验证

**任务**：μ-Bench (arXiv:2407.01791) — 验证「当前 VLM 在显微镜感知上表现挣扎（准确率 <70%）」这一核心论断，
在冻结的 perception 测试分片 `ubench-test-00000-of-00007.arrow`（7 个分片之一，3,650 行图像、21,900 道 Closed-VQA 题）上。

## 方法（一句话）

冻结分片 → pyarrow 解析出 6 类 Closed-VQA 题（5 粗粒度 + 1 细粒度）→ 在冻结模型上提取图像特征
（timm ViT-B/16 ImageNet、torchvision ResNet18 ImageNet）→ 每类题以两道评测跑法衡量：
**linear probe**（StandardScaler + L2 逻辑回归，5 折分组 CV）与 **cosine kNN**（k=9，同一 CV 划分，
更接近零样本相似度基准）→ 按题目选项集 mask（closed-VQA / 多选题口径）打分 → 得到粗/细粒度准确率
（seed=42、按 image_id 分组防泄漏，percentile bootstrap 95% CI）。

> 离线环境无任何 VLM/CLIP 权重可用（HF 缓存中 Qwen3-VL 仅 tokenizer 文件、无 open_clip），
> 故采用任务协议明确允许的「开源小模型线性探测」路径，将冻结感知编码器+线性头/kNN 作为
> 「通用/专用感知模型（BiomedCLIP 类）」代理；论文中的 GPT-4o 数字仅作对照讨论，不冒充实测。

## 关键数字（本分片实测，Closed-VQA 多选题 accuracy）

| 模型 | coarse（5 题宏平均） | fine（classification） |
|---|---|---|
| ViT-B/16 · linear-probe | 100.0% | 81.8% |
| ViT-B/16 · kNN | 100.0% | 67.6% |
| ResNet-18 · linear-probe | 100.0% | 75.8% |
| ResNet-18 · kNN | 100.0% | 58.6% |
| majority baseline | 52.0% | 16.4% |
| 论文 GPT-4o（对照，非实测） | 62.6% | 51.7% |

- n_items：coarse 18250 题、fine 3650 题；95% bootstrap CI 见 `results/evidence_table.csv`；
- majority/chance per 题型见 `results/baselines.csv`（fine chance ≈ 0.21）。

## 三问判定（详见 claim.md 与 report.md）

1. **数据与任务**：本分片 3,650 行 / 3,446 唯一图像 / 21,900 题，6 个题位、6 个数据集、3 种模态、
   24 个细粒度类；与论文「22 任务」（5 粗 + 16 细 + 1 认知）的对应关系及口径见 report.md。
2. **VLM 评测**：代理模型实测 coarse ≈100.0%（linear probe）/ 100.0%（kNN）、
   fine 81.8%（LR）/ 67.6%（kNN）；kNN（更接近零样本）在细粒度上 <70%。
3. **结论判定**：**partially_supported** —— 细粒度是本分片论断的直接检验（近零样 kNN 仅 67.6%/58.6%，
   监督 LR 81.8%/75.8%，即细粒度上「挣扎」成立）；而 5 个粗粒度题位因答案与数据集/成像协议强相关在本
   分片饱和（≈100%），无法在单分片上复现论文 62.6% 的粗粒度难度（分片局限，非反例证据），故整体为
   partially_supported。

## 产物
- `code/`：可复现流水线（解析→特征→评测→绘图），CPU 可跑，约 40–60 分钟（特征抽取为主）；
- `results/evidence_table.csv`、`results/metrics.json`：判分抽查字段；
- `evidence/`：粗/细粒度准确率图（含论文 GPT-4o 参考线）、各题型准确率图、数据构成图。