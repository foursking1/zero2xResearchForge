# Task: 1810.08468 OSCD（L1 critical claim，变化检测）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：HuggingFace blanchon/OSCD_RGB 镜像（真实数据，详见 `data/SOURCE.md`，数据本体在 `$PAPER_BENCH_DATA_DIR`）

## 1. 问题（可证伪）

论文（Daudt et al., "Urban Change Detection for Multispectral Earth Observation Using Convolutional Neural Networks", IGARSS 2018）核心结果：在 Onera Satellite Change Detection（OSCD）基准（24 对 Sentinel-2 双时相影像，14 对训练 / 10 对测试，二值变化掩码）上，**CNN 变化检测方法优于经典差值影像方法**：RGB（3 通道）下 Early Fusion（EF）整体精度 83.63%、变化类精度 82.14%；13 通道（全多光谱）EF 整体 88.15%、变化类 84.69%（Table 1）；而经典方法（Img diff / Log-ratio / GLRT）整体精度仅 76.12–76.93%、变化类 59.68–63.42%。论文结论：CNN 方法（尤其早融合）显著优于差值影像方法。

**可证伪问题**：在给定的冻结真实数据（完整 OSCD RGB：14 对训练 / 10 对测试双时相影像 + 二值变化掩码）上，用你实现的 CNN 变化检测方法能否达到/逼近论文报告的 ~84% 整体精度（3 通道 EF，Table 1）？「CNN（EF/Siamese）在变化类精度上比经典差值方法高 ~20pp」这一 claim 在你的实验条件下成立吗？

**失败条件**：测试整体精度显著低于论文量级（如 <78%），或仅靠"全部无变化"先验等平凡基线（此时应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：HuggingFace `blanchon/OSCD_RGB`（OSCD RGB 版镜像，非 gated；官方数据集由 Onera/ONERA 发布，Sentinel-2 影像）。完整出处/许可/校验见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR/data/data`）：
  - `train-00000-of-00001.parquet`：14 行，列 `image1`（T1 影像，582×522 RGB）、`image2`（T2 影像）、`mask`（二值变化掩码 582×522，1=变化）；
  - `test-00000-of-00001.parquet`：10 行，同结构（测试时 mask 为评测真值，可用于计算精度但不用于训练）。
- 每行一对已配准的 Sentinel-2 RGB 影像（10 m/像素，已裁切缩放到 582×522），变化类别为城市变化（新建建筑/道路等）。
- **校验**：4 个冻结文件 SHA-256 登记于 `$PAPER_BENCH_DATA_ROOT/checksums.sha256` 与 `data/source_manifest.json`。
- 体积：约 40 MB。

## 3. 方向提示（关键点，不构成步骤指导）

- 论文在 582×522 尺度上训练 CNN（EF/Siamese 架构）；3 通道 RGB 对应 Table 1 的 "3 ch." 行（EF 83.63/82.14/83.71，Siamese 84.13/78.57/84.43）。
- 类别极不平衡（无变化像素远多于变化像素，论文用反比加权损失）；建议报告整体精度 + 变化类精度 + 无变化类精度三项（与 Table 1 逐项对照）。
- 建议对比经典差值基线（Img diff / Log-ratio / GLRT ~76% 整体）以验证「CNN 优于差值方法」的 claim。
- 防泄漏：只允许从训练 14 对估计统计/阈值；不得用测试掩码调参。

## 4. 输出要求（结论 + 证据表 + 代码 + 报告）

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：用 `supported` / `partially_supported` / `contradicted` / `inconclusive` 给出结论并附一句理由；明确写出测试整体精度，并与论文锚 83.63%（Table 1，3 ch. EF 整体精度）比较（绝对差与相对差）。
2. **证据表**（`submission/results/evidence_table.csv`）：按 10 对测试影像逐对汇总，列为 `pair_id, n_change_px, n_correct, accuracy, change_acc, nochange_acc` + 整体行；另附 `submission/results/metrics.json` 含整体/变化/无变化精度、混淆矩阵（2×2）、每对明细。
3. **代码**（`submission/`）：完整可重跑，从冻结 parquet 读入并计算上述全部数字。
4. **报告**（`submission/report.md`）：方法描述（架构/是否预训练/损失/阈值）、训练预算与超参、经典差值基线对照、防泄漏声明、失败样例分析、局限性说明。

## 5. 数据铁律提醒

- 只使用冻结的真实数据；**禁止**模拟/合成/手工构造数据，禁止从外部下载替代数据。
- 禁止用测试掩码做任何训练/调参。
- 所有关键数字必须能从冻结数据 + 提交代码重算（裁判将抽查）。
- 不许改动冻结文件；SHA-256 见 `data/source_manifest.json`。
