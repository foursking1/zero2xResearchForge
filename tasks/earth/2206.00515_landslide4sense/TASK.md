# Task: 2206.00515 Landslide4Sense（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：官方源 NXDOMAIN 不可达，经用户批准使用 HF 镜像冻结真实数据（详见 `data/SOURCE.md`）

## 1. 问题（可证伪）

论文核心结果（Table I）：在 Landslide4Sense 基准（四研究区 Iburi/Kodagu/Gorkha/Taiwan、14 波段 128×128 像素级二分类）上，深度学习分割模型 ResU-Net 达到 **F1=71.65%**（Precision 76.08%、Recall 67.71%），为 11 个 SOTA 模型之首；U-Net 为 69.94%，PSPNet 仅 56.39%。即「**深度学习可从多源遥感数据可靠检测滑坡，F1 达 ~70% 量级**」。

**可证伪问题**：在给定的冻结真实数据（论文 3799-patch 数据池的固定子集：240 训练 + 240 测试 patch）上，用你实现的像素级二分类方法，能否达到/逼近论文报告的 F1≈71.65%？「DL 滑坡检测高性能（F1≈70%）」这一 claim 在你的实验条件下成立吗？结论边界在哪（类别不平衡、阈值选择、数据子集规模）？

**失败条件**：方法在该冻结测试集上 F1 显著低于 71.65%（如 <50%），或仅靠「预测全为非滑坡」这类平凡基线（此时应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：HuggingFace 镜像 `ibm-nasa-geospatial/Landslide4sense`（官方源 `cloud.iarai.ac.at` 已 NXDOMAIN 失效，用户 2026-08-13 批准使用镜像；镜像内容与官方一致）。完整出处/许可/校验说明见 `data/SOURCE.md`。
- **结构**（`data/` 下）：
  - `train/img/image_1.h5 … image_240.h5`：影像 `img` 数组 (128,128,14) float64；波段=Sentinel-2 B1–B12 + ALOS PALSAR Slope(B13)+DEM(B14)，~10m 分辨率
  - `train/mask/mask_1.h5 … mask_240.h5`：掩码 `mask` 数组 (128,128) uint8，{0=非滑坡, 1=滑坡}
  - `test/img/image_3560.h5 … image_3799.h5` 与 `test/mask/…`：同 schema，240 patch
- **划分**：train=image_1..240，test=image_3560..3799（按官方文件序固定的子集；论文未公开 patch→研究区映射，故不做区域级拆分）。
- **许可**：官方仓库 MIT（代码/文档）；数据本体官方条款随官网下线无法在线审计，论文声明数据公开提供；镜像无额外 license 标签。
- **checksum**：`data/CHECKSUMS.sha256`（960 条，sha256 逐文件固定）。修改任何冻结文件将导致校验失败，属违规。
- 体积：约 850 MB。

## 3. 方向提示（关键点，不构成步骤指导）

- 类别极不平衡：论文报告训练部分滑坡像素占比约 5.5%——你的冻结子集中滑坡像素占比请自行统计并报告。
- F1 对决策阈值敏感：务必报告所用阈值（或概率校准方式）及 Precision/Recall 权衡。
- 建议报告与平凡基线（如全 0 预测）的对比，以及至少一个非深度基线（可选）与深度模型的差距。
- 防泄漏：任何数据统计（归一化均值/方差、类别先验）只能从训练集估计；不得使用测试集标签做任何调参。

## 4. 输出要求（结论 + 证据表 + 代码 + 报告）

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：用下列词汇之一给出结论并附一句理由：`supported` / `partially_supported` / `contradicted` / `inconclusive`。必须明确写出你得到的整体 F1，并与论文锚 F1=71.65% 比较（绝对差与相对差）。
2. **证据表**（`submission/results/evidence_table.csv`）：至少整体一行 + 每 patch 一行，列为 `split, patch_id, threshold, tp, fp, tn, fn, precision, recall, f1`；另附 `submission/results/metrics.json` 含整体 `base_rate`（测试集滑坡像素占比）、`precision/recall/f1`、`threshold`。
3. **代码**（`submission/`）：完整可重跑，从 `data/` 冻结文件读入并计算上述全部数字（数据路径通过参数或相对路径给出）。
4. **报告**（`submission/report.md`）：方法描述、训练预算与超参、防泄漏声明、类别不平衡与阈值敏感性分析、局限性（子集规模、未见区域泛化未验证）。

## 5. 数据铁律提醒

- 只使用 `data/` 内冻结的真实数据；**禁止**模拟、合成、手工构造数据。
- 禁止把测试集掩码用于训练/调参/阈值选择（仅允许最终评估时读取）。
- 报告的所有关键数字必须能从冻结数据 + 提交代码重算（裁判将抽查）。
- 不许改动冻结文件；`CHECKSUMS.sha256` 用于裁判核验。
