# Task: 2506.07080 FLAIR-HUB（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

> 编译状态：**compiled（自测分：待评测）** ｜ 2026-08-13 ｜ 领域：earth ｜ 建议层级 L2 → 产出 L1 题
> 数据：官方 HuggingFace `IGNF/FLAIR-HUB` 真实数据冻结子集（详见 `data/SOURCE.md`，数据本体在 `$PAPER_BENCH_DATA_DIR`）

## 1. 问题（可证伪）

论文（Garioud et al., "FLAIR-HUB: Large-scale Multimodal Dataset for Land Cover and Crop Mapping", arXiv:2506.07080）核心结果：在 FLAIR-HUB 土地覆盖基准（74 个时空域、2,528 km²、241,100 张 512×512@0.2 m 影像、15 类 COSIA 语义分割标注，官方 split `split_flairhub`：train 152,225 / valid 38,175 / test 50,700 patch）上，**仅用航空影像（AERIAL RGBI）** 即可取得：

- **mIoU 51.5% / OA 72.6%**（Table IX，ResNet-50 + U-Net，aerial-only）；
- 更强的 aerial-only 基线 **mIoU 64.1% / OA 77.5%**（Table IX Swin-Base+UPerNet；Table X 配置 LC-A UPerFuse）；
- 且加入全部其余模态（LC-L）仅带来 **OA +0.9%、mIoU +1.7%** 的边际提升（Table X，LC-A vs LC-L）。

**可证伪问题**：在给定的冻结真实数据（论文数据池的固定子集：D005-2018 + D091-2021 两个训练域 400 train / 100 valid patch，D015-2020 未见测试域 100 test patch）上，用你实现的像素级语义分割方法（仅航空 RGBI 输入），能否达到/逼近论文报告的性能量级（mIoU≈51.5–64.1%、OA≈72.6–77.5%）？「仅航空影像即可支撑 ~50–64 mIoU 的 15 类土地覆盖分割」这一 claim 在你的实验条件下成立吗？训练域（山地/雪/裸土为主）到未见测试域（农业/落叶林为主）的跨域性能衰减有多大？

**失败条件**：模型在冻结测试集上 mIoU 显著低于论文量级（如 <20%），或仅靠「预测多数类」这类平凡基线（此时应判定 claim 未复现并给出证据）。

## 2. 数据说明

- **来源**：HuggingFace 官方仓库 `IGNF/FLAIR-HUB`（数据与代码的官方发布渠道，论文链接 https://ignf.github.io/FLAIR/FLAIR-HUB/flairhub）。完整出处/许可/校验见 `data/SOURCE.md`。
- **结构**（数据本体在 `$PAPER_BENCH_DATA_DIR`，路径见 `data/DATA_LOCATION.md`）：
  - `frozen/train/img/*.tif`（400）、`frozen/val/img/*.tif`（100）、`frozen/test/img/*.tif`（100）：航空影像 512×512×4，uint8，波段顺序 **R(0), G(1), B(2), NIR(3)**，20 cm 分辨率；论文实验使用 **IR/R/G 三通道**（即波段 3,0,1）。
  - `frozen/<split>/label/*.tif`：COSIA 土地覆盖标注 512×512 uint8，值域 0–18；**0–14 为论文评测的 15 类**（building/greenhouse/swimming_pool/impervious/pervious/bare_soil/water/snow/herbaceous/agricultural/plowed/vineyard/deciduous/coniferous/brushwood，见 `PAPER_ANCHOR.md` 锚 4 完整图例）；**15–18 为弱标签类，论文评测中排除**（评估时忽略；训练时建议 ignore_index，自行说明）。
  - `frozen_manifest.csv`：600 行，字段 `patch_id, split, roi, img, label`，patch_id 与官方 `GLOBAL_ALL_MTD_SPLIT` 一致。
  - `raw/*.zip`：官方原始 zip（D005/D091/D015 的 AERIAL_RGBI + AERIAL_LABEL-COSIA + GLOBAL_ALL_MTD），共 7 个，供溯源/扩展。
- **划分**：train/valid/test 严格取自官方 `split_flairhub`（`GLOBAL_ALL_MTD_SPLIT.gpkg`）：train=D005+D091 的 train 子集按 patch_id 排序等距抽 250+150；valid=D005+D091 的 valid 子集抽 60+40；test=D015 的 test 子集抽 100。官方 split 中 D005/D091 无 test patch、D015 无 train/valid patch，故三域天然跨域。
- **许可**：`etalab-2.0`（Etalab Open License 2.0，法国家公开数据开放许可，允许研究/再分发并注明出处）。
- **校验**：全部 1,208 个文件（7 raw zip + 600 img + 600 label + manifest）SHA-256 已登记于 `$PAPER_BENCH_DATA_ROOT/checksums.sha256` 与 `data/source_manifest.json`。修改任何冻结文件将导致校验失败，属违规。
- 体积：冻结子集约 0.62 GB（raw 全量约 10.6 GB）。

## 3. 方向提示（关键点，不构成步骤指导）

- 15 类高度不平衡（如训练子集中 bare_soil≈28%、snow≈15%，而 greenhouse/pool/vineyard 近乎为 0；测试域分布显著不同）——报告类别频率与每类 IoU，分析不平衡与跨域影响。
- 输入口径：论文实验用 IR/R/G 三通道并做均一化（均值和方差从 TRAIN+VALID 统计，Table VIII）；你只能从 **train 集**估计归一化统计（防泄漏），三通道或四通道均可，须报告所用口径。
- 评估口径：mIoU/OA 在类 0–14 上计算；真实标签 ≥15 的像素不计入混淆矩阵（与论文排除弱标签类一致）。
- 建议对比平凡基线（如预测训练集多数类）与至少一个简单模型（如小 U-Net），并报告 valid/test 差距（跨域衰减）。
- 防泄漏：任何统计（归一化、类别先验、阈值）只能从 train（可选 valid）估计；禁止用 test 标签调参。

## 4. 输出要求（结论 + 证据表 + 代码 + 报告）

请在工作目录生成 `submission/`：

1. **结论**（`submission/report.md` 首部）：用下列词汇之一给出结论并附一句理由：`supported` / `partially_supported` / `contradicted` / `inconclusive`。必须明确写出你在冻结测试集上得到的整体 mIoU 与 OA，并与论文锚 mIoU=51.5%（ResNet-50+U-Net, Table IX）及 aerial-only 性能带 51.5–64.1% 比较（绝对差与相对差）。
2. **证据表**（`submission/results/evidence_table.csv`）：至少整体一行 + 每 patch 一行，列为 `split, patch_id, n_pixels_0123_14, tp, fp, tn, fn, iou, precision, recall, f1`（可含每类一行）；另附 `submission/results/metrics.json` 含整体 `mIoU`, `OA`, 每类 IoU、测试集类别频率 `class_freq`。
3. **代码**（`submission/`）：完整可重跑，从 `$PAPER_BENCH_DATA_DIR/frozen`（或 TASK.md 说明的 data 路径）读入并计算上述全部数字。
4. **报告**（`submission/report.md`）：方法描述、训练预算与超参、输入波段口径、防泄漏声明、类别不平衡与跨域分析、局限性说明。

## 5. 数据铁律提醒

- 只使用冻结的真实数据；**禁止**模拟、合成、手工构造数据，禁止从外部下载其他版本数据替代。
- 禁止把 test 标签用于训练/调参/阈值选择（仅允许最终评估时读取）。
- 报告的所有关键数字必须能从冻结数据 + 提交代码重算（裁判将抽查）。
- 不许改动冻结文件；SHA-256 见 `data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`。
