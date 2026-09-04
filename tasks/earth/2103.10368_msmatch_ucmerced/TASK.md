# Task: 2103.10368 MSMatch 少标注半监督遥感场景分类（L2 端到端科研再发现）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2103.10368_msmatch_ucmerced`
- 层级：L2（RCBench 对齐：input/output/scientific goal 三段式；目标论文隐藏，仅给原始数据）
- 领域：earth / 遥感场景分类 / 半监督学习（每类仅 5 个标注样本）

## 任务描述（三段式）

### Input（给定）

- `data/uc_merced.parquet`：UC Merced Land Use 数据集（2,100 张 256×256 遥感影像，21 类 × 每类 100 张；列：image（JPEG）、label（0-20））。类别：agricultural、airplane、baseballdiamond、beach、buildings、chaparral、denseresidential、forest、freeway、golfcourse、harbor、intersection、mediumresidential、mobilehomepark、overpass、parkinglot、river、runway、sparseresidential、storagetanks、tenniscourt。

数据集为真实 USGS 国家地图影像（UC Merced 公开数据集）。

### Output（必须产出）

1. **`method/`**：实现并训练一个**半监督分类器**，使用**每类仅 5 个标注样本（共 105 个）** + 其余未标注样本（2,100−105=1,995 个）：
   - 至少一个**一致性正则/伪标签类半监督方法**（如 FixMatch 精神：强弱增强一致性 + 高置信度伪标签；参考 MSMatch 的置信度掩码 + 多视角），框架不限；
   - 至少一个**有监督基线**（仅用 105 个标注样本训练的普通 CNN）。
2. **`protocols/`**：实现论文口径：每类随机选 5 个作为标注集（固定种子可复现），其余作为未标注池；报告标注集/未标注池的划分文件。
3. **`results/`**：`evidence_table.csv`（每类一行 + 整体行：accuracy/precision/recall/f1）、`metrics.json`（overall_accuracy、per_class_accuracy、labeled_per_class=5、seed、method）。
4. **`report.md`**：完整科研报告（见 Scientific Goal）。

### Scientific Goal（要回答的科学问题）

针对「半监督方法能否在每类仅 5 个标注样本的极端少标注下达到高精度遥感场景分类」这一主题，回答：

1. **Q1 复现性**：你的半监督方法在 UC Merced 每类 5 标注口径下的 OA 是多少？与论文报告的 **90.71%**（MSMatch，摘要）差多少（绝对/相对）？
2. **Q2 半监督增益**：相比仅用 105 个标注样本的有监督基线，半监督方法提升多少 pp？伪标签/一致性正则是否有效？
3. **Q3 标注敏感性**：标注样本数从 5→10→20 每类变化时 OA 如何变化？半监督在哪个区间增益最大？
4. **Q4 结论标签**：基于证据，给出四档结论：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 冻结真实数据（来源与许可见 `data/SOURCE.md`，SHA-256 固定于 `data/source_manifest.json`）
- 禁止合成/模拟数据；禁止使用 ImageNet 预训练权重之外的任何外部标注（若用预训练须声明）
- 标注集选择必须从冻结 parquet 按固定种子完成；未标注池不得泄露标签信息（评估时才用标签）
- 防泄漏：测试集划分与标注集选择互斥

## 数据铁律提醒

- 只用本包冻结数据；禁止合成数据替代。
- 所有关键数字必须由你的代码从本包数据算出；禁止照抄论文数字。
- 不许改动冻结文件。
