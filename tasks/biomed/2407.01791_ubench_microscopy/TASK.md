# 科研任务：μ-Bench「VLM 显微镜理解能力」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2407.01791_ubench_microscopy`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：μ-Bench: A Vision-Language Benchmark for Microscopy Understanding（arXiv:2407.01791）
- 领域：biomed / 显微镜影像 / VLM 评测

## 问题（可证伪）

μ-Bench 是专家策展的显微镜视觉-语言基准（22 个生物医学任务，覆盖感知与认知两大类）。论文核心论断：

1. **当前 VLM 在所有类别上表现挣扎，即便是基础任务（如区分显微镜模态）**：最强通用模型 GPT-4o 在粗粒度感知上准确率仅 62.6%、细粒度感知 51.7%、认知任务 62.0%（论文 Table 1）。
2. **专用生物医学模型（BiomedCLIP 等）在部分任务上并不优于通用模型**；在病理特定感知上差距明显（粗粒度差 39.37pp、细粒度 19.40pp，GPT-4o vs BiomedCLIP 等）。

请基于冻结数据回答：

1. **数据与任务**：解析冻结的 μ-Bench perception 测试分片，统计任务数、题目数、模态/尺度分布，确认与论文"22 个任务"口径的对应关系。
2. **VLM 评测**：对冻结分片运行至少一个可获得的 VLM（开源模型如 CLIP/BiomedCLIP/Qwen-VL 均可，或商用 API），报告粗粒度/细粒度感知的准确率，与论文 Table 1 对照（GPT-4o 62.6%/51.7%、BiomedCLIP 等）。
3. **结论判定**：在你运行的模型上，"当前模型在显微镜感知上准确率有限（<70%）"是否成立？

- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结，来源/许可/checksum 见 `data/README.md`）
  - `ubench-test-00000-of-00007.arrow`：μ-Bench perception 数据集的测试分片之一（约 5.4 亿字节；含图像与题目/答案元数据，7 个分片之一）
  - `dataset_info.json`：数据卡 schema（字段说明）
- 来源：HuggingFace 官方仓库 `jnirschl/uBench`（论文配套数据；`perception/0.1.0/` 目录，仅 test split）
- 许可：CC-BY-SA-4.0（HF 数据卡声明）
- SHA-256（固定）：见 `data/README.md`（下载完成后核对）

## 方向提示（协议建议）

1. **解析**：Arrow 可用 `pyarrow`/`datasets` 读取；先看 `dataset_info.json` 字段（通常含 image、question、answer、task/类别等）。
2. **评测方式**：论文将任务分为 Closed VQA（accuracy）与 Open VQA（GRIT 指标）；本任务以 Closed VQA 的 accuracy 为主口径（如冻结分片含开放式题目，可仅评测可判分的子集并说明）。
3. **模型选择**：无 GPU 时可用开源小模型（如 CLIP/BiomedCLIP 零样本或线性探测）或商用 VLM API；报告中说明所用模型与论文 GPT-4o 的差异。
4. **指标**：准确率（accuracy），可加 bootstrap 置信区间；粗粒度/细粒度分组口径参照论文。

## 输出要求（提交物）

1. **`claim.md`**：三问判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本，从 `data/` 解析冻结分片并运行评测。
3. **`results/evidence_table.csv`**：至少含列 `model,task_group,accuracy,n_items`（每模型×粗/细粒度）。
4. **`results/metrics.json`**：任务数/题目数统计；各模型准确率；论文锚对照；结论标签。
5. **`report.md`**：方法（数据解析/模型/评测口径）、结果、局限（冻结分片为 7 个之一、模型差异、Open VQA 处理）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟图像替代。
- 禁止手工抄写论文数字作为"实测结果"；所有指标必须运行代码得到。
- 论文数值（GPT-4o 62.6%/51.7%/62.0% 等）只能用于对照讨论。
- 冻结分片为 7 个测试分片之一：报告时明确样本覆盖，不得把分片结果冒充全量。