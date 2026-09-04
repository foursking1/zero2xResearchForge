# 科研任务：高光谱异常检测基准中统计 RX 检测器可复现性与精度/速度权衡（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id: `2507.05730_had_survey`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Hyperspectral Anomaly Detection Methods: A Survey and Comparative Study（arXiv:2507.05730，2025）
- 领域：CS / 高光谱遥感 / 异常检测基准

## 问题（可证伪）

论文对 17 个高光谱异常检测（HAD）基准数据集系统评测了 10 种方法，核心发现是「深度学习方法（GT-HAD）平均检测精度最高（平均 AUC=0.9733），而统计方法 RX 在保持有竞争力精度的同时速度最快（平均 AUC=0.9390、平均 0.40s；Table 5 Avg 行）」。

本任务用冻结的 14 个高光谱数据集（论文 Table 5 评测子集）验证三个子 claim：

- **(a) RX 锚可复现性**：用标准全局 RX 检测器（马氏距离）对每个冻结数据集计算像素级 AUC，应与论文 Table 5 RX 列对应值一致（|Δ|≤0.01）在 **≥10/14** 个数据集上成立（自检 11/14 精确一致；San Diego/Gulfport/Bay Champagne 三行因版本差异允许 ±3pp 并须在报告中说明）。
- **(b) RX 竞争力下限**：全部 14 个冻结数据集的 RX AUC ≥ 0.80（论文 Table 5 RX 列最低 0.8221；自检全部 ≥0.82），且单图 100×100 量级运行时间 < 5 秒（论文报告平均 0.40s）。
- **(c) 方法族平均精度排序（论文数值参照）**：表示/深度方法平均 AUC 高于统计方法（CRD 0.9567、GT-HAD 0.9733 > RX 0.9390），即「深度最准、统计最快」；若自行实现 CRD（可选加分项），应得到 CRD > RX 的方向。

## 方向提示（非方法步骤）

- 数据加载：`scipy.io.loadmat`；`data` (H,W,B) 为光谱强度，`map` (H,W) 为 ground truth（0=背景，>0=异常像素）；像素级二分类 = 背景 vs 异常。
- RX 全局检测器：`score(x) = (x−μ)ᵀ Σ⁻¹ (x−μ)`，其中 μ、Σ 为全图像素均值与协方差（奇异协方差用伪逆 `np.linalg.pinv`）；异常分数为马氏距离。
- 指标：`roc_auc_score((gt>0).ravel(), score)`，像素级 AUC。
- San Diego 行：用 `sandiego.mat` 左上 `[:100,:100,:]` 裁剪 + `plane_gt.mat`（100×100 GT）。
- 映射表（冻结文件 ↔ 论文 Table 5 行号，含一处命名互换）：
  - `abu/abu-airport-1.mat`→8.1；`abu/abu-airport-2.mat`→8.3（本镜像机场2文件与论文 8.3 行值一致）；`abu/abu-airport-3.mat`→8.2（版本差异）
  - `abu/abu-urban-1..5.mat`→9.1..9.5；`abu/abu-beach-1.mat`→10.1；`abu/abu-beach-2.mat`→10.2（版本差异）
  - `aviris_1.mat`→6；`aviris_2.mat`→7；`hydice_urban.mat`→2；`sandiego.mat+plane_gt.mat`→1（全图版）
- 防泄漏：异常检测为无监督设定（只用背景/全图统计打分，不用 GT 拟合任何参数；GT 仅用于评估 AUC）——注意 RX 用全图统计是标准做法，但报告中须说明其对异常点污染的敏感性。

## 数据说明

- 数据包：`$PAPER_BENCH_DATA_DIR/hsi`（18 个 .mat，~97MB）。
- 内容：ABU 13 图（机场4/城市5/海滩4）+ aviris_1/2 + hydice_urban + sandiego 全图 + plane_gt；结构 `data`(H,W,B) + `map`(H,W)。
- 来源：GitHub 公开镜像（sxt1996 系列 + HSIYJND），公开遥感数据，无需注册/API key；逐文件 SHA-256 登记 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`。

## 输出要求（提交物）

1. **结论**：对 (a)(b)(c) 分别给出 `supported / partially_supported / contradicted / inconclusive`，并说明与论文 Table 5 的对照及版本差异影响。
2. **证据表**：`results/evidence_table.csv`，至少含列：`file`、`survey_id`、`n_anomaly`、`auc_rx`、`auc_paper_rx`、`delta`、`match_le_0_01`、`runtime_s`；汇总 `n_match`、`min_auc`、`mean_auc`、`mean_runtime_s`。
3. **代码**：完整可复现脚本（固定数据路径），从冻结 .mat 读取并计算 RX/AUC。
4. **报告**：`report.md`：方法（RX 定义/伪逆/裁剪）、版本差异说明（San Diego 全图、Gulfport/Bay Champagne 波段数）、与论文 17 数据集全量评测的差异、局限性（未跑 CRD/深度方法；无监督统计的敏感性）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代。
- GT 只用于最终 AUC 评估；禁止用 GT 拟合、调参或选择背景像素（除论文标准做法外不得引入泄漏）。
- 18 个 .mat 不得修改；报告中必须说明与论文全量实验（10 方法 × 17 数据集）的差异。
