# Task: 1902.06701 HybridSN 高光谱图像分类（L2 端到端科研再发现）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`1902.06701_hybridsn`
- 层级：L2（RCBench 对齐：input/output/scientific goal 三段式；目标论文隐藏，仅给原始数据）
- 领域：earth / 高光谱遥感影像分类 / 3D-2D 混合卷积

## 任务描述（三段式）

### Input（给定）

- `data/Indian_pines_corrected.mat`：Indian Pines（IP）高光谱影像（AVIRIS，145×145 像素，200 个反射率波段）
- `data/Indian_pines.mat`：原始 220 波段版本（145×145×220，未做波段剔除，可选参考）
- `data/Indian_pines_gt.mat`：地面真值标签图（145×145；0=背景，1-16 共 16 类）

数据集为真实 AVIRIS 机载光谱仪采集的印第安纳州 Indian Pines 农区影像，共 10,249 个有标注像素。

### Output（必须产出）

1. **`method/`**：实现并训练一个**高光谱分类器**，至少包括：
   - 一个**3D-2D 混合 CNN**（先 3D 卷积联合提取空间-光谱特征，再 2D 卷积细化空间特征；参考 HybridSN 架构精神：3DConv(8,32,3,3,3)-3DConv(32,64,3,3,3)-3DConv(64,128,3,3,3)-2DConv(128,64,3,3)-FC，输入窗口 25×25）；
   - 至少一个**基线**（如 SVM/RBF、2D-CNN 或光谱像素级分类，自选）。
2. **`protocols/`**：实现论文口径的数据划分：**随机抽取 30% 有标注样本作为训练、其余 70% 测试**（论文：`30% and 70% of the data are randomly divided into training and testing groups`），固定种子可复现。
3. **`results/`**：`evidence_table.csv`（每类一行 + 整体行：OA/AA/Kappa、每类 accuracy）、`metrics.json`（overall_accuracy、average_accuracy、kappa、train_ratio、seed、window_size）。
4. **`report.md`**：完整科研报告（见 Scientific Goal）。

### Scientific Goal（要回答的科学问题）

针对「3D-2D 混合卷积网络能否在少量标注（30%）下取得高精度高光谱分类」这一主题，回答：

1. **Q1 复现性**：你的 3D-2D 混合 CNN 在 IP 30% 训练口径下的 OA 是多少？与论文报告的 **99.75±0.1%**（HybridSN，Table II）差多少（绝对/相对）？
2. **Q2 混合结构价值**：3D-2D 混合 CNN 相比你的基线（SVM 或 2D-CNN）在 OA/AA/Kappa 上的提升有多大？
3. **Q3 训练比例敏感性**：将训练比例改为 10% 或 70% 时 OA 如何变化？30% 是否是合理折中？
4. **Q4 结论标签**：基于证据，给出四档结论：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 冻结真实数据（来源与许可见 `data/SOURCE.md`，SHA-256 固定于 `data/source_manifest.json`）
- 禁止合成/模拟数据；禁止从网络下载其他版本 IP 数据
- 数据划分必须从冻结 `Indian_pines_gt.mat` 按固定种子完成；统计（归一化均值/方差）仅用训练子集
- 标签 0=背景像素，不参与训练/评估；类别数 16

## 数据铁律提醒

- 只用本包冻结数据；禁止合成数据替代。
- 所有关键数字必须由你的代码从本包数据算出；禁止照抄论文数字。
- 不许改动冻结文件。
