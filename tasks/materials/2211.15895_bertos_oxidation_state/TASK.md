# Task: 2211.15895_bertos_oxidation_state（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

## 元信息
- task_id: `2211.15895_bertos_oxidation_state`
- 层级: L1（critical claim，可证伪）
- 论文: Fu, N., Hu, J., Feng, Y., Morrison, G., zur Loye, H.-C., Hu, J. *Composition Based Oxidation State Prediction of Materials Using Deep Learning Language Models.* arXiv:2211.15895 (2022)；正式版 Advanced Science 10, 2301011 (2023), DOI: 10.1002/advs.202301011
- 领域: materials（组成→氧化态预测）

## 问题（可证伪）
论文声称：BERTOS（BERT 式 Transformer，输入仅为化学组成）在 cleaned ICSD 数据集上的**全元素氧化态预测精度达 96.82%**，氧化物材料达 **97.61%**；在电荷中性子集（OS-ICSD-CN）上原子位点级精度 **96.27%**（190,468 原子位点）、化合物级全对比例 **PC=87.76%**，而 Pymatgen 启发式氧化态猜测仅 **4.49%** 能给出确定氧化态。

请使用本任务冻结数据（官方预训练模型 + 官方测试集）独立评估并验证该声明，回答：

1. **OS-ICSD 全元素精度**：用官方 `ICSD` 模型评估 `ICSD` 测试集，位点级精度 PS 是否 ≈**96.82%**？
2. **氧化物精度**：用官方 `ICSD_oxide` 模型评估 `ICSD_oxide` 测试集，PS 是否 ≈**97.61%**？
3. **电荷中性子集与交叉**：用 `ICSD_CN` 模型评估 `ICSD_CN` 测试集 PS 是否 ≈**96.27%**；并复现论文 Table 1 的 4×4 精度矩阵（4 训练模型 × 4 测试集，含交叉项，容差 ±2 pp）。
4. （加分）PC（化合物全对比例）是否 ≈**87.76%**；金属/非金属位点精度是否 ≈**97.12% / 96.05%**；电荷中性筛选应用（`checkCN.py`）能否工作。

## 方向提示
- **数据格式**：`data/datasets/*.zip` 解压后为 CoNLL 块格式——每行 `元素 氧化态`（如 `Sr 2`、`O -2`），**空行分隔化合物**；每个化合物 = 一个块（元素序列 + 对应氧化态标签）。标签范围 −5..+8（14 类）。
- **模型**：`data/models/*.zip` 为 HuggingFace `BertForTokenClassification` 检查点（config.json + pytorch_model.bin；12 层 hidden=120；vocab=123 元素 token）。加载后对每个元素 token 取 logits argmax，**预测类索引 − 5 = 氧化态**（与 config id2label 一致）。
- **分词**：`data/code/tokenizer/vocab.txt`（BertTokenizerFast，do_lower_case=False）；将化合物元素序列（如 `Sr Ti O O O`）编码为 `[CLS] … [SEP]`；标签对齐元素位置 1..n（去掉 [CLS]/[SEP]）。长度上限参考 `random_config/config.json`（max_position_embeddings=200，训练 max_length=100）。
- **评估口径（与论文一致）**：
  - **PS**（位点级精度）= 全部正确预测原子位点数 / 全部原子位点数（论文 "percentage of correctly predicted oxidation states of all atoms"）。
  - **PC**（化合物级）= 所有位点全部正确的化合物数 / 化合物总数。
  - 金属/非金属位点按元素类别分组统计。
- **运行**：CPU 即可（推理快）；依赖见 `data/code/requirements.txt`（torch + transformers）。评估脚本需能从 `data/` 直接运行（解压 zip、加载模型与测试集、输出精度表）。
- **口径备注**：论文报告的是训练过程中最佳 checkpoint 的精度；仓库释放的 checkpoint 与之存在 ≤0.6 pp 的合理差异。请在报告中对比论文数值并说明差异。

## 数据说明
- 目录：`data/`（冻结，22 文件 + SOURCE + CHECKSUMS，约 34 MB）
- **来源**：论文官方仓库 github.com/usccolumbia/BERTOS（main，HEAD b845c3d，2026-08-13 抓取）：`dataset/*.zip`（4 个数据集）+ `trained_models/*.zip`（4 个预训练模型）+ 代码。
- **许可**：GPL-3.0（仓库 LICENSE，`data/LICENSE_GPL3.txt`）；数据集为作者从 ICSD 清洗派生后公开发布，使用需遵守 GPL-3.0 与 ICSD 条款并引用论文。
- **Checksum**：全部文件 SHA-256 见 `data/CHECKSUMS_SHA256.tsv`；核心：`datasets/ICSD_CN.zip`、`models/ICSD_CN.zip` 等哈希见该表。
- **Schema 摘要**（详见 `data/SOURCE.md`）：
  - `datasets/ICSD.zip`=OS-ICSD（train 44,324 / test 5,215）；`ICSD_CN.zip`=OS-ICSD-CN（train 31,827 / test 3,724，与论文一致）；`ICSD_oxide.zip`=OS-ICSD-oxide（test 3,603）；`ICSD_CN_oxide.zip`=OS-ICSD-CN-oxide（test 2,420）
  - `models/<name>.zip`：与四个训练数据集一一对应的预训练 checkpoint
  - `code/`：train_BERTOS.py / getOS.py / checkCN.py / materials_*.py / tokenizer / random_config

## 输出要求
1. **结论**：对 3 个主问题（+加分项）给出明确回答（复现 / 部分复现 / 未复现），并与论文数值（96.82%、97.61%、96.27%、87.76%、97.12/96.05%）逐项对比。
2. **证据表**（`results/evidence_table`）：4 模型 × 4 测试集 PS 矩阵（对齐 Table 1）、PC、金属/非金属精度、位点数统计。
3. **代码**：可运行评估脚本，能从冻结数据 `data/` 直接重算证据表中的关键数值。
4. **报告**：评估口径（PS/PC 定义、标签映射、截断长度）、与论文数值的差异及可能原因（checkpoint 版本）、局限性。

## 数据铁律提醒
- 只用本任务冻结的真实数据与官方模型；**禁止自行训练替代模型、伪造或修改标签/数值**。
- 本任务是"冻结模型推理验证"，不是"重新训练"：结论必须来自官方预训练模型对官方测试集的评估。
- 报告数值必须能由冻结数据重算复现；数据 checksum 已固定（SHA-256），报告中注明数据来源与许可。