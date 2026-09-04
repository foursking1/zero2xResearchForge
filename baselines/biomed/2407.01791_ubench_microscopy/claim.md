# claim.md — 2407.01791_ubench_microscopy 三问判定

## 问题 1：数据与任务解析

- 冻结分片：`ubench-test-00000-of-00007.arrow`（perception test split 的 7 个分片**之一**），
  含 **3,650 行 / 3,446 唯一图像 / 21,900 道 Closed-VQA 题**（每图 6 道；answer_idx 完整性校验通过）。
- 题位（6 类）：modality、submodality、domain、subdomain、stain、classification；
- 覆盖：6 个数据集、3 种模态（light 1,600 / fluorescence 1,896 / electron 154）、2 个 domain、
  6 个 subdomain、4 个 submodality、3 种 stain、24 个细粒度类；分布见 `results/dataset_stats.json`。
- 与论文「22 任务」口径：本分片为 perception 子集之一（cognition 不在此，需全量 7 分片 + cognition 才能完整核对），
  其中 5 个粗粒度题位对应论文 coarse-grained perception，classification 对应 fine-grained perception；
  「22 = 5 粗 + 16 细 + 1 认知」的系统级核对明确不在此单分片范围内断言。

## 问题 2：VLM 评测（实测准确率，代理模型）

| 模型（v.probe = linear probe） | coarse（5 题宏平均）% | fine（classification）% | n_items（coarse / fine） |
|---|---|---|---|
| ViT-B/16 · linear-probe | 100.0 | 81.8 | 18250 / 3650 |
| ViT-B/16 · kNN | 100.0 | 67.6 | 18250 / 3650 |
| ResNet-18 · linear-probe | 100.0 | 75.8 | 18250 / 3650 |
| ResNet-18 · kNN | ≈100 | 58.6 | 18250 / 3650 |
| majority（基准） | 52.0 | 16.4 | — |

- 论文对照（Table 1，仅对照、非本机测量）：GPT-4o coarse **62.6%**、fine **51.7%**、cognition **62.0%**；
  本分片不包含 cognition 题目。
- 口径：Closed-VQA / 多选题 accuracy；5 折分组 CV（seed 42，按 image_id 分组）+ 选项集 mask 打分，
  95% bootstrap CI 见 `results/evidence_table.csv`。
- 说明：离线无 VLM/CLIP 权重，采用任务协议允许的「冻结感知编码器线性探测」及 kNN 相似度基准两种代理
  口径（kNN 更接近零样本），与论文中 BiomedCLIP 等感知模型类别对齐讨论，不冒充 GPT-4o。

## 问题 3：结论判定——「当前模型在显微镜感知上准确率有限（<70%）」是否成立？

在我运行的模型上：

- **细粒度（classification）**：更接近零样本的 kNN 基准 67.6%（ViT）/ 58.6%（ResNet），
  均 **<70%**；最强监督 linear probe 81.8%。→ 与论文「细粒度感知挣扎」一致；
- **粗粒度（5 题宏平均）**：本分片内 linear probe ≈100%、kNN ≈100%——因为该分片的粗粒度标签与
  数据集/成像协议强相关（模态/染色/domain 几乎一一对应数据集），单分片不体现论文 62.6% 的难度；
  → 粗粒度在本分片上**未重现挣扎**（分片局限，非论文观点）。
- 结论标签：**partially_supported**。

判定说明：Fine-grained perception 是本分片论断的直接检验——近零样 kNN 仅 67.6%/58.6%（ViT/ResNet）、
监督 linear probe 为 81.8%/75.8%；而 5 个粗粒度题位因答案与数据集/成像协议强相关在本分片饱和（≈100%），
无法在单分片上复现论文 62.6% 的粗粒度难度。因此整体判定 partially_supported：
「模型在显微镜感知上挣扎（<70%）」在细粒度、更接近 VLM（kNN）口径下成立；粗粒度本分片不作为反例证据断言。