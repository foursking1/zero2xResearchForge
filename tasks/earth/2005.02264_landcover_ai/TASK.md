# Task: 2005.02264 LandCover.ai 土地覆盖语义分割（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：LandCover.ai v1 官方完整包（42 张 5000×5000 影像+掩码 + 官方 train/val/test patch 清单）

## 1. 问题（可证伪）

论文核心结果（§4）：在 **LandCover.ai**（航拍土地覆盖分割，5 类：building、woodland、water、road、other）上，**DeepLabv3+（输出步长 OS=4）达到 mIoU 85.56%**；OS=16 基线为 81.81%，缩小输出步长提升 1.47pp。即「**SOTA 分割网络可在 LandCover.ai 上达到约 85.6% mIoU 的土地覆盖分割**」。

**可证伪问题**：在给定的冻结真实数据（LandCover.ai v1 官方包：42 张 5000×5000 航空影像 + 对应掩码，官方 train/val/test 512×512 patch 清单）上，用你实现的分割方法，能否达到/逼近论文报告的 DeepLabv3+ OS4 mIoU≈85.56%（test）？「高精度土地覆盖分割（~85% mIoU）」这一 claim 成立吗？结论边界在哪（模型容量、输出步长、patch 大小、类别不平衡）？

**失败条件**：方法在冻结 test patch 上 mIoU 显著低于 85.56%（如 <70%），或仅靠多数类基线（应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：LandCover.ai v1 官方发布（zip 完整包）。完整出处/许可见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR/data/landcover.ai.v1.zip`，解压后）：
  - `images/`：42 张 TIF（约 5000×5000，RGB 0.25m/px 航拍正射影像）
  - `masks/`：42 张对应掩码 TIF（5 类：0=other, 1=building, 2=woodland, 3=water, 4=road）
  - `train.txt`（7,470 patch）、`val.txt`（1,602）、`test.txt`（1,602）：官方 512×512 patch 级划分（patch 名 `{tile}_{i}`）
  - `split.py`：官方切 patch 脚本
- **划分**：官方划分以 patch 清单为准（train/val/test 已固定）；禁止重新随机划分后把 val/test 混入训练。
- **许可**：LandCover.ai 公开研究用途（CC BY 4.0，官方声明）。非医学/隐私。
- **checksum**：zip 的 SHA-256 见 `data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`。
- 体积：约 1.5 GB（zip）。

## 3. 方向提示

- 先按 `split.py` 口径把 42 张大图切成 512×512 patch（带重叠可选），再按 txt 清单分 train/val/test。
- 论文最佳：DeepLabv3+（ResNet 骨架）输出步长 4；可对比 OS16 与 OS4、以及 UNet/PSPNet 等。
- 5 类中 road/building 像素占比低，类别不平衡是主要挑战；报告每类 IoU。
- 防泄漏：只从 train patch 估计统计；val/test 只做最终评估。

## 4. 输出要求

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：`supported` / `partially_supported` / `contradicted` / `inconclusive` + 理由。写出 test mIoU，与论文锚 85.56% 比较。
2. **证据表**（`submission/results/evidence_table.csv`）：每类一行 + 整体行，列 `split, class_id, class_name, iou, precision, recall, f1, pixels`；`submission/results/metrics.json` 含 `mean_iou`、`class_iou`、`model`、`output_stride`、`patch_size`。
3. **代码**（`submission/`）：完整可重跑，从冻结 zip 解压/切 patch/训练/评估。
4. **报告**（`submission/report.md`）：方法、训练预算、防泄漏声明、每类错误分析、OS 对比、局限性。

## 5. 数据铁律提醒

- 只使用冻结真实数据；禁止模拟/合成。
- 关键数字必须能从冻结数据 + 代码重算（裁判将抽查）。
- 不许改动冻结文件。
