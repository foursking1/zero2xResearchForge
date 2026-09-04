# 科研任务：医学分割「源模型迁移性估计」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2307.11958_transferability_estimation_seg`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Pick the Best Pre-trained Model: Towards Transferability Estimation for Medical Image Segmentation（arXiv:2307.11958）
- 领域：biomed / 医学影像分割 / 迁移学习

## 问题（可证伪）

论文提出 source-free 迁移性估计框架 CC-FV（类别一致性 Class Consistency + 特征多样性 Feature Variety），用于在医疗图像分割中"无训练地"从候选源模型池选出最优源模型。在 MSD（Medical Segmentation Decathlon）5 个 3D CT 任务（Liver/Lung/Pancreas/Spleen/Colon）上，核心论断：

1. **CC-FV 的估计排序与真实迁移性能高度相关**：平均 Pearson 系数 0.7003、加权 Kendall's τ 0.4986（论文 Table 1），优于所有现有 TE 算法（LogME/TransRate/LEEP/GBC 等；如 GBC Pearson 均值 0.3317）。
2. **无需目标标注与微调**：TE 分数在 source-free 条件下（只用目标数据特征、不训练）即可可靠排序源模型。

请基于冻结数据回答：

1. **数据与协议**：解析冻结的 MSD Spleen/Liver 子集（NIFTI 图像 + 分割标注），构建论文式"源模型池 × 目标任务"协议（源任务预训练 → 目标任务微调），说明子集与全量（Spleen 41 例 / Liver 131 例）的关系。
2. **迁移性估计复现**：在冻结子集上实现至少两个 TE 指标（推荐 LogME/LEEP/GBC 中的两个 + 论文 CC-FV 风格的类别一致性/特征多样性估计），对候选源模型打分，报告 TE 排序与真实微调性能（Dice）的 Pearson 与加权 Kendall's τ。
3. **选择命中**：报告"按 TE 选出的最优源模型"是否就是微调后 Dice 最高的源模型。

- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结，来源/许可/checksum 见 `data/README.md`）
  - `spleen_<id>.nii.gz`（10 例）+ `spleen_<id>_label.nii.gz`：MSD Task09 Spleen 子集（图像 + 分割标注）
  - `liver_<id>.nii.gz`（10 例）+ `liver_<id>_label.nii.gz`：MSD Task03 Liver 子集
- 来源：Medical Segmentation Decathlon（MSD，medicaldecathlon.com 官方发布）；本包为 HuggingFace 镜像 `MedOtter/msd-spleen`、`MedOtter/msd-liver` 的文件子集
- 许可：MSD 数据集官方许可 CC-BY-SA-4.0（网站声明）；HF 镜像标注 cc-by-sa-4.0
- SHA-256（固定）：见 `data/README.md`（下载完成后核对）

## 方向提示（协议建议）

1. **协议设计**：以 Spleen 为目标任务、Liver（或另一任务）为源任务池：在 Liver 子集上预训练 2-3 个不同初始化/容量的 U-Net 作为源模型池；在 Spleen 子集上微调，用 Dice 作为真实迁移性能。
2. **TE 指标**：LogME（最大似然估计）、LEEP（标签转移）、GBC（梯度），以及 CC-FV 风格指标（在源模型特征上计算类内一致性 + 特征多样性）；实现细节以论文为准或合理近似并在报告中说明。
3. **评估**：报告 TE 排序与真实 Dice 的 Pearson 相关系数与加权 Kendall's τ（论文 Table 1 口径）；命中率（top-1 选择正确与否）。
4. **规模控制**：3D 训练重——建议用 2D 切片简化（每例取轴向切片子集），或 patch 训练；固定种子与切片数以保证可复现与可跑。

## 输出要求（提交物）

1. **`claim.md`**：三问判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从 `data/` 读取并完成预训练/微调/TE 计算。
3. **`results/evidence_table.csv`**：至少含列 `source_model,te_method,te_score,ft_dice,rank`。
4. **`results/metrics.json`**：Pearson / 加权 Kendall's τ（各 TE 方法）；top-1 命中；论文锚对照；结论标签。
5. **`report.md`**：方法（协议/简化/2D 化/TE 实现）、结果、局限（子集规模、2D 近似、与论文 5 任务差异）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟图像替代。
- 禁止手工抄写论文数字作为"实测结果"；所有指标必须运行代码得到。
- 论文数值（CC-FV Pearson 0.7003 / τ 0.4986 等）只能用于对照讨论。
- 目标任务（Spleen）不得用于源模型预训练；TE 评估为 source-free（不使用目标标注训练）。