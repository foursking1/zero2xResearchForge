# 科研任务：Point-LN「轻量非参数点云分类」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2501.14238_pointln`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Point-LN: A Lightweight Framework for Efficient Point Cloud Classification Using Non-Parametric Positional Encoding（arXiv:2501.14238v1）
- 领域：CS / 三维点云分类

## 问题（可证伪）

论文声称：仅用**非参数组件（FPS + kNN + 非学习式位置编码）+ 精简可学习线性分类器**，即可在点云分类基准上达到与 SOTA 相当的精度，同时参数量极小。请基于本包冻结数据独立实现并验证两条论断：

1. **论断 C1（ModelNet40 精度-效率）**：Point-LN 在 ModelNet40 上达到 **94.0%** 精度、仅 **0.8M** 可学习参数——与 PointMLP（94.1%，12.6M 参数）相当，但参数少约一个数量级；明显高于零参数方法 Point-NN（81.8%）与 Point-GN（85.3%）。
2. **论断 C2（ScanObjectNN 真实场景）**：在更具挑战的 ScanObjectNN 上，Point-LN 达到 OBJ-BG **92.2%** / OBJ-ONLY **92.1%** / PB-T50-RS **91.7%**（本包冻结 PB-T50-RS 子集，主锚 = **91.7%**）。

请回答：
- (a) 按方向提示实现的模型在 ModelNet40 测试集上的总体精度与可学习参数量是多少？C1 的「精度与 PointMLP 相当 + 参数大幅更少」是否成立？
- (b) 在 ScanObjectNN PB-T50-RS 测试集上的总体精度是多少？C2 是否成立？
- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`（可对 C1/C2 分别给标签）。

## 数据说明

- 数据包：`data/`（冻结，来源与许可见 `data/SOURCE.md`，SHA-256 固定于 `source_manifest.json`）
  - `modelnet40_normal_resampled.tar.gz`：ModelNet40 全部 12,311 个物体（40 类），每物体一个 `.txt`（10,000 点，xyz，normal_resampled 格式）
  - `modelnet40_train.txt` / `modelnet40_test.txt`：**官方划分清单**（9,843 / 2,468），必须使用
  - `modelnet40_shape_names.txt`：40 个类别名（与清单文件名的类别段一致）
  - `training_objectdataset_augmentedrot_scale75.h5` / `test_objectdataset_augmentedrot_scale75.h5`：ScanObjectNN **PB_T50_RS**（15 类），`data`(N,2048,3) xyz、`label`(N,) 0-14、`mask`(N,2048)（-1=背景点）

## 方向提示（协议建议，按此口径才能与论文锚对齐）

论文方法要点（§III，自行按提示实现，不给完整代码）：

1. **采样**：每个物体采样 **1,024 点**（论文遵循 PointNet++ 等惯例；ScanObjectNN 可保留 h5 的 2,048 点或采样 1,024，报告中说明）。
2. **归一化**：常用做法为平移至中心 + 单位尺度归一化（报告写明口径；统计量只能由训练集样本自身计算，禁止跨样本全局统计泄漏）。
3. **非参数特征提取管线**：
   - **FPS**（最远点采样）选出 N/2 个中心点；
   - **kNN** 分组（k 自选，报告说明）构造局部邻域；
   - 邻居坐标/特征按邻域均值-标准差归一化；
   - **位置编码**：三角位置编码 TPE（逐轴 sin/cos，尺度 α 与波长 β 控制）与/或高斯位置编码 GPE（非学习式），编码前后可各接一个线性层；
   - 多级 local_grouper（线性变换聚合局部特征），全局聚合（如平均池化）后接线性分类头。
4. **学习组件**：全部可学习参数集中在轻量线性层/分类头（**目标 ≤ ~2M 参数**，论文为 0.8M）。
5. **训练**：优化器/学习率/轮数/批大小自定，固定随机种子并写入代码；报告超参与种子。
6. **指标**：测试集总体精度（%）；可学习参数量（M）；可选推理耗时（ms/样本）。

## 输出要求（提交物）

1. **`claim.md`**：C1/C2 的判定（四档标签）、失败条件、数据支持强度、关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从 `data/` 冻结数据读取、训练、评估，重算全部指标；禁止外网下载。
3. **`results/evidence_table.csv`**：至少含列 `dataset,accuracy,params_M,seed`（每数据集×种子一行；含均值行）。
4. **`results/metrics.json`**：ModelNet40 train/test 样本数；两数据集测试精度与参数量；C1/C2 判定；对比行（PointMLP 94.1%/12.6M、Point-NN 81.8%/0M、Point-GN 85.3%/0M，标注为论文引用）。
5. **`report.md`**：方法（采样/归一化/编码/分组/分类器/训练）、结果、与论文对照、局限（实现与论文的差异说明）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止合成/模拟点云；禁止从网络下载其他点云/划分。
- ModelNet40 划分必须用包内官方清单；禁止自行随机划分。
- 归一化/采样/背景点处理等统计量不得利用测试集信息。
- 禁止把论文数字（94.0/91.7 等）当作本实验实测值；论文数值只能用于对照讨论。