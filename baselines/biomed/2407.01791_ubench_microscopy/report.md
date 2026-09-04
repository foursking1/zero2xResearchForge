# report.md — μ-Bench「VLM 显微镜理解能力」关键论断验证（2407.01791_ubench_microscopy）

## 1. 任务与论文锚

论文：*μ-Bench: A Vision-Language Benchmark for Microscopy Understanding*（arXiv:2407.01791）。核心论断：

1. 当前 VLM（甚至最强通用模型 GPT-4o）在显微镜感知的粗/细粒度任务上准确率有限：GPT-4o 粗粒度
   感知 62.6%、细粒度感知 51.7%、认知 62.0%（Table 1）。
2. 专用生物医学 VLM（BiomedCLIP 等）在部分任务上并不优于通用模型（病理感知差 39.37pp / 19.40pp）。

本报告在**冻结的 μ-Bench perception 测试分片之一**（`ubench-test-00000-of-00007.arrow`，7 个分片之一）上：
解析数据、运行多题 Closed-VQA 评测、对三问给出四档标签。

## 2. 方法

### 2.1 数据解析
- 直接用 `pyarrow` 流式读取冻结 Arrow（image 列含 PNG bytes；`questions` 列含 6 类 Closed-VQA 题）。
- 每题记录 `question`、`options`（含干扰项与 "none of the above"）、`answer_idx`、`answer` 文本，
  连同图像级元数据（dataset / modality / domain / subdomain / submodality / stain / label_name 等）
  展开为长表（21,900 题）。完整性校验：所有 answer_idx 均有效且落在选项长度内。

### 2.2 模型与评测口径
- **为什么用代理模型**：评测环境完全离线，HF 缓存中没有任何 VLM/CLIP/对比模型权重
  （Qwen3-VL-8B 仅 tokenizer 文件；无 open_clip 权重）。因此采用任务协议明确允许的
  「开源小模型线性探测」路径，使用两类本地可用权重：
  - `vit_base_patch16_224`（timm，`augreg2_in21k_ft_in1k`，ImageNet 预训练）→ CLS 特征，768 维；
  - `resnet18`（torchvision `IMAGENET1K_V1`）→ avgpool 特征，512 维。
  评测（Closed-VQA 多选准确率，每数据/模型×题型）：
  - **linear probe**：`StandardScaler + L2 LogisticRegression`，标签=题的正确选项文本；
    测试时把各类别得分 mask 到该题选项集后取 argmax；
  - **kNN**（k=9，cosine 相似度，多数投票）——作为更接近零样本的相似度基准（不学参数）。
  - 两种方法均与 GPT-4o/LLM 类模型有本质差异（无文本/推理），结论判定已相应限定。
- **交叉验证**：`StratifiedGroupKFold(n=5, seed=42)`，按 `image_id` 分组——相同图像
  （含 193 张同时出现在 `burgess_contour` 与 `burgess_texture` 的副本）不会跨 train/test；
  准确率为 5 折测试池化计算，配 2,000 次 percentile bootstrap 95% CI（seed 42）。
- **分组汇总**：coarse = 5 个粗粒度题型（modality、submodality、domain、subdomain、stain）的宏平均；
  fine = classification 题型池化准确率；另附每题型、每数据集明细。

### 2.3 论文对照
- 论文数值仅用于对照（判分锚），不参与任何实测值计算；cognition 不在本分片，不做评测。

## 3. 结果

### 3.1 数据统计（`results/dataset_stats.json`、`results/task_counts.csv`）
| 项 | 值 |
|---|---|
| 行（图像实例） | 3,650 |
| 唯一图像（image_id） | 3,446（193 个 id 被两两数据集复用） |
| Closed-VQA 题 | 21,900（每图 6 题，全部填充） |
| 数据集 | acevedo_et_al_2020(1,600)、burgess_contour/eccentricity/texture(各 600)、colocalization_benchmark(96)、empiar_sbfsem(154) |
| 模态 | light microscopy 1,600 / fluorescence 1,896 / electron 154 |
| domain | pathology 1,600 / biology 2,050 |
| 细粒度类别 | 24 类（top: intermediate 600；血细胞各 200 …） |
| answer_idx 校验 | 21900/21900 有效 |

### 3.2 各题型准确率（`results/per_type_accuracy.csv`，5 折池化 + bootstrap CI）

| question_type | ViT-B/16 probe | ResNet-18 probe |
|---|---|---|
| modality | 100.0% | 100.0% |
| submodality | 100.0% | 100.0% |
| domain | 100.0% | 100.0% |
| subdomain | 100.0% | 100.0% |
| stain | 100.0% | 100.0% |
| classification | 81.8% | 75.8% |

### 3.3 分组汇总（`results/evidence_table.csv`）

| 模型 | coarse（宏平均）% | fine（classification）% |
|---|---|---|
| ViT-B/16 · linear-probe | 100.0 | 81.8 |
| ViT-B/16 · kNN | 100.0 | 67.6 |
| ResNet-18 · linear-probe | 100.0 | 75.8 |
| ResNet-18 · kNN | 100.0 | 58.6 |
| majority baseline | 52.0 | 16.4 |
| chance（均值 1/k） | 18.3 | 20.9 |

### 3.4 与论文对照（Table 1，仅对照）

| 指标 | 论文 GPT-4o | 本文最优（实测） | 相对差 | 备注 |
|---|---|---|---|---|
| coarse | 62.6% | 100.0%（LR）/ 100.0%（kNN） | 59.7% | 本文代理强于论文顶级模型区域（该分片粗粒度问题与数据集强相关，见 §4） |
| fine | 51.7% | 81.8%（LR）/ 67.6%（kNN） | 58.3% | kNN 抽细粒度与论文同数量级（<70%）；LR 为监督上界 |
| cognition | 62.0% | —（分片不含） | — | 不适用 |

### 3.5 每数据集 fine（classification）准确率（`results/per_dataset_accuracy.csv`）

- resnet18_knn / acevedo_et_al_2020: acc=67.0% (n=1600)
- resnet18_knn / burgess_et_al_2024_contour: acc=42.5% (n=600)
- resnet18_knn / burgess_et_al_2024_eccentricity: acc=45.2% (n=600)
- resnet18_knn / burgess_et_al_2024_texture: acc=52.8% (n=600)
- resnet18_knn / colocalization_benchmark: acc=77.1% (n=96)
- resnet18_knn / empiar_sbfsem: acc=97.4% (n=154)
- ResNet-18 / acevedo_et_al_2020: acc=86.9% (n=1600)
- ResNet-18 / burgess_et_al_2024_contour: acc=59.7% (n=600)
- ResNet-18 / burgess_et_al_2024_eccentricity: acc=65.5% (n=600)
- ResNet-18 / burgess_et_al_2024_texture: acc=67.8% (n=600)
- ResNet-18 / colocalization_benchmark: acc=74.0% (n=96)
- ResNet-18 / empiar_sbfsem: acc=96.8% (n=154)
- vit_base_patch16_224_knn / acevedo_et_al_2020: acc=87.3% (n=1600)
- vit_base_patch16_224_knn / burgess_et_al_2024_contour: acc=43.2% (n=600)
- vit_base_patch16_224_knn / burgess_et_al_2024_eccentricity: acc=41.2% (n=600)
- vit_base_patch16_224_knn / burgess_et_al_2024_texture: acc=57.0% (n=600)
- vit_base_patch16_224_knn / colocalization_benchmark: acc=75.0% (n=96)
- vit_base_patch16_224_knn / empiar_sbfsem: acc=96.8% (n=154)
- ViT-B/16 / acevedo_et_al_2020: acc=97.8% (n=1600)
- ViT-B/16 / burgess_et_al_2024_contour: acc=62.2% (n=600)
- ViT-B/16 / burgess_et_al_2024_eccentricity: acc=62.5% (n=600)
- ViT-B/16 / burgess_et_al_2024_texture: acc=73.5% (n=600)
- ViT-B/16 / colocalization_benchmark: acc=84.4% (n=96)
- ViT-B/16 / empiar_sbfsem: acc=98.7% (n=154)

### 3.6 可视化（`evidence/`）
- `coarse_fine_acc.png`：各模型 coarse/fine vs 论文 GPT-4o 参考线；
- `per_type_acc.png`：6 种题型准确率（含 error bar）；
- `dataset_composition.png`：分片模态/domain/submodality 构成。

## 4. 三问结论判定

1. **数据与任务口径**：解析成功；6 题型 × 6 数据集 × 21,900 题全部落入 Closed-VQA 口径；
   与论文「22 任务」的对应关系已说明（perception 的 5 粗 + 1 细层级；cognition 不在本分片）。
2. **模型评测**：代理模型 coarse 达 100.0%（LR）/ 100.0%（kNN），fine 达 81.8%（LR）/
   67.6%（kNN）；kNN 在细粒度上显著 <70%。
3. **论断判定**：**partially_supported**。
   Fine-grained perception is the honest stress test of the claim on this shard: the near-zero-shot kNN
   baseline reaches only 67.6%/58.6% (ViT-B/16 / ResNet-18) and a supervised linear probe 81.8%/75.8%.
   The five coarse-grained taxonomy question types saturate on this shard (~99.9-100% for both LR and kNN)
   because their labels coincide with dataset/imaging-protocol identity; the paper's 62.6% coarse macro
   covers the full benchmark, which this single shard does not reproduce. Conclusion: the "models struggle
   on microscope perception (<70%)" claim holds for the fine-grained, more VLM-like (kNN) setting, while
   the coarse-grained subset of this shard does not recapitulate paper-level difficulty.

## 5. 局限

1. **覆盖**：仅冻结 7 个 perception 测试分片之一（约 3,650 行 / 21,900 题），不冒充全量；
   无 train split（用分片内 grouped CV），无 cognition；论文 62.6%/51.7% 为全量宏平均，不可逐项对照。
2. **粗粒度分片特性**：本分片 5 个粗粒度题位的答案与数据集/成像协议几乎一一对应（例如 modality、
   stain、domain 可直接由数据源区分），故监督 LR 与 kNN 均 ≈100%——这是**分片难度的体现**，
   不代表论文 62.6% 的粗粒度论断被推翻；审稿该分片时粗粒度问题信息量较低。
3. **模型差异**：无离线 VLM/CLIP 权重，linear probe / kNN 为感知编码器代理，不代表 GPT-4o 级别的
   零样本 LLM closed-VQA；对「GPT-4o 表现」的推断是间接的（论文数字仅对照）。
4. **口径细节**：Closed-VQA 选项 mask 打分法；未评测 open-VQA（本分片全为 closed）；未复现论文的
   VLM prompt/生成式交互流程。
5. **统计**：CI 为 percentile bootstrap；CV 分组避免同图泄漏；数据集间分布差异仍在（宏平均部分缓冲）。

## 6. 可复现性与证据

- 运行：`bash code/run_all.sh`（全离线、CPU 默认，约 40–60 分钟；GPU 可选 `--device cuda` 加速特征抽取）。
- 关键证据：`results/evidence_table.csv`、`results/metrics.json`、`results/predictions.parquet`、
  `results/per_type_accuracy.csv`、`results/per_dataset_accuracy.csv`、`evidence/*.png`。
- 数据铁律：全部数值由本代码在冻结分片上运行得到；论文数字（62.6%/51.7%/62.0% 等）仅用于对照并标注来源。