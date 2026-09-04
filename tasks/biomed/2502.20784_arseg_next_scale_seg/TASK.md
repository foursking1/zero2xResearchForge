# 科研任务：AR-Seg「自回归下尺度掩码预测分割」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2502.20784_arseg_next_scale_seg`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Autoregressive Medical Image Segmentation via Next-Scale Mask Prediction（arXiv:2502.20784）
- 领域：biomed / 医学影像分割 / 自回归模型

## 问题（可证伪）

论文提出 AR-Seg：将分割掩码量化为多尺度 token 图，用"下尺度掩码预测"的自回归机制显式建模跨尺度依赖，并用共识聚合（consensus aggregation）提高稳健性。在两个基准上的核心论断：

1. **LIDC-IDRI（结节分割，放射科医生间差异大）**：AR-Seg 达 GED 0.232（↓）、HM-IoU 0.616（↑）、Soft-Dice 0.658（↑），优于 BerDiff（0.238/0.596/0.644）等 SOTA（论文 Table 1）。
2. **BraTS 2021（多类脑肿瘤分割）**：AR-Seg Dice 86.97，优于 nnU-Net 84.57、BerDiff 85.42、HiDiff 85.80 等（论文 Table 2）。

请基于冻结数据回答：

1. **数据与协议**：解析冻结数据（LIDC-IDRI 结节 patch 集 与/或 BraTS 2021 mini），构建分割训练/测试协议，说明子集与全量（LIDC 1,018 例 / BraTS 2021 全量）的关系。
2. **分割基线复现**：在冻结子集上训练至少一个分割模型（U-Net 或 nnU-Net 风格），报告 Dice（BraTS 口径）或 Soft-Dice/HM-IoU（LIDC 口径）。
3. **AR-Seg 核心机制（可简化）**：实现论文风格的"多尺度掩码 + 下尺度预测"（或近似：级联/深监督 + 多尺度），与单尺度基线对比，验证"显式跨尺度依赖带来提升"；如资源受限，报告基线 + 说明 AR-Seg 机制设计的可行性分析。

- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结，来源/许可/checksum 见 `data/README.md`）
  - `lidc_train.parquet`：LIDC-IDRI 结节 patch 数据集（HF 镜像 `ykeselman/lidc-idri-patches`；约 374MB；字段含 `image`/像素间距、结节标注（bbox/恶性度等）、患者/扫描 ID）
  - （共享）`../2112.10074_qubrats_uncertainty_seg/data/brats2021_mini.parquet`：BraTS 2021 mini（10 例 NIFTI 多模态 + 分割标注）——如需使用请复制到本卡 data/ 并记录 checksum
- 来源：LIDC-IDRI（TCIA 公开数据）镜像 + BraTS 2021（zenodo，CC-BY-4.0）
- 许可：LIDC-IDRI 为 TCIA 公开数据（研究用途，CC-BY 系条款）；BraTS 2021 为 CC-BY-4.0
- SHA-256（固定）：见 `data/README.md`（下载完成后核对）

## 方向提示（协议建议）

1. **LIDC 口径**：冻结 patch 集含结节图像与标注框（xmin/ymin/xmax/ymax）与 z 层；可转换为结节/背景二分类分割（将 bbox 区域作伪掩码，说明限制），或以 patch 内分割为任务。
2. **BraTS 口径**：3D 多模态输入；建议 2D 轴向切片简化，WT 二类或 ET/TC/WT 三类；报告 Dice。
3. **AR-Seg 简化**：多尺度掩码 + 下尺度自回归可用 2D U-Net 多尺度头近似（encoder 各层输出监督），共识聚合可用多次采样平均近似；实现不了完整 AR-Seg 时如实说明并给出机制分析。
4. **指标**：BraTS 用 Dice；LIDC 用 Soft-Dice / HM-IoU / GED（以实际可计算为准）。
5. **资源控制**：固定种子；切片抽样；epoch 数适中；报告训练时长与资源。

## 输出要求（提交物）

1. **`claim.md`**：三问判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从 `data/` 读取并训练/评估。
3. **`results/evidence_table.csv`**：至少含列 `model,dataset,metric,value`（基线 + AR-Seg 风格模型）。
4. **`results/metrics.json`**：样本统计；各模型指标；论文锚对照（绝对差/相对）；结论标签。
5. **`report.md`**：方法（协议/简化/模型）、结果、局限（子集规模、2D 近似、未完整复现 AR-Seg 的说明）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟图像替代。
- 禁止手工抄写论文数字作为"实测结果"；所有指标必须运行代码得到。
- 论文数值（AR-Seg LIDC Soft-Dice 0.658 / BraTS Dice 86.97 等）只能用于对照讨论。
- 测试划分固定；禁止在测试集上训练或调参。