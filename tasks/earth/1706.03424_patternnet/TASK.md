# Task: 1706.03424 PatternNet 遥感图像检索（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：PatternNet 镜像（30,400 图，38 类，每类 800）

## 1. 问题（可证伪）

论文核心结果（Table 4/5）：在 **PatternNet**（38 类 × 800 张 = 30,400 张高分辨率遥感图像）图像检索基准上，基于 CNN 特征（AlexNet_Fc1）达到 **mAP 0.6003、P@5 0.9545**；VGGF 特征 mAP 0.6195。即「**深度 CNN 特征可在 PatternNet 上实现高精度内容检索（mAP≈0.60–0.62、P@5>0.95）**」。

**可证伪问题**：在给定的冻结真实数据（PatternNet 30,400 张，38 类，每类 800）上，用你实现的内容检索方法（每张图作为 query，从全库检索同类，mAP/P@k 评估），能否达到/逼近论文报告的 mAP≈0.60–0.62？「CNN 特征在 PatternNet 检索上 mAP≈0.60」这一 claim 成立吗？结论边界在哪（特征/检索距离、库规模、类别相似度）？

**失败条件**：方法在冻结数据上 mAP 显著低于 0.60（如 <0.40），或仅靠随机检索（应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：PatternNet HF 镜像（3 个 parquet shard，共 30,400 行，38 类单标签）。完整出处/许可见 `data/SOURCE.md`。
- **结构**（`$PAPER_BENCH_DATA_DIR`）：`data/data/train-00000-of-00003.parquet`（10,134 行）+ `train-00001-of-00003.parquet`（10,133）+ `train-00002-of-00003.parquet`（10,133）；列：image struct + label 0-37。
- **标签**：38 类（airplane, baseball field, basketball court, beach, bridge, cemetery, chaparral, christmas tree farm, closed road, coastal mansion, crosswalk, dense residential, ferry terminal, football field, forest, freeway, golf course, harbor, intersection, mobile home park, nursing home, oil gas field, oil well, overpass, parking lot, …）。
- **划分**：论文检索设置为「每张图作 query、全库检索（排除自身）」；无需显式划分，但 agent 可选用固定子集提高可计算性（须报告口径）。
- **许可**：镜像许可以 README 为准（PatternNet 数据公开研究用途）。非医学/隐私。
- **checksum**：逐文件 SHA-256 见 `data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`。
- 体积：约 1.42 GB。

## 3. 方向提示

- 检索协议：对每张 query 图，在全库中按特征相似度排序，计算 mAP（同类为正例）与 P@5/P@10。可先抽样 query（如每类 50 张）以控制计算量，但须报告并保持固定种子。
- 特征：CNN 特征（论文用 AlexNet/VGG 预训练特征）或自训练特征均可；距离用余弦相似度。
- 38 类中部分类别视觉相似（forest/chaparral、beach/coastal mansion 等），是主要检索错误来源。
- 防泄漏：特征提取器训练若用有监督标签，须仅用训练子集；检索评估在固定 query/gallery 上进行。

## 4. 输出要求

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：`supported` / `partially_supported` / `contradicted` / `inconclusive` + 理由。写出整体 mAP 与 P@5，与论文锚 mAP 0.6003/0.6195 比较。
2. **证据表**（`submission/results/evidence_table.csv`）：每类一行 + 整体行，列 `split, class_id, class_name, queries, retrieved, relevant, mAP, p_at_5, p_at_10`；`submission/results/metrics.json` 含 `mAP`、`p_at_5`、`p_at_10`、`num_queries`、`gallery_size`、`feature`、`seed`。
3. **代码**（`submission/`）：完整可重跑，从冻结 parquet 读入计算。
4. **报告**（`submission/report.md`）：方法（特征+距离）、检索协议、防泄漏声明、类别难度分析、局限性。

## 5. 数据铁律提醒

- 只使用冻结真实数据；禁止模拟/合成。
- 关键数字必须能从冻结数据 + 代码重算。
- 不许改动冻结文件。
