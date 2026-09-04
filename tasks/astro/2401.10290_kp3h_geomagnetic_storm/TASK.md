# 科研任务：3 小时提前预测地磁暴（Kp 指数）——RF 回归关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2401.10290_kp3h_geomagnetic_storm`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Iris Yan, "Early Prediction of Geomagnetic Storms by Machine Learning Algorithms", arXiv:2401.10290 (2024)
- 领域：astro / 空间天气 / 地磁暴机器学习预测

## 问题（可证伪）

论文核心论断：**融合多源真实太阳风/地磁观测（NASA OMNIWeb 5 分钟太阳风数据、京都 WDC Dst 指数、GFZ Kp 指数），用随机森林（RF）回归 + 特征选择（保留 top-50 特征）+ 对低 Kp 多数类下采样，可以在 3 小时前预测 Kp 指数，在 2021 年测试期（10–12 月）达到 82.55% 的准确率（预测值在真实值 ±1 以内）**；且**特征重要性随历史时滞快速衰减（越近的测量越重要，6 小时前的测量几乎无信息）**，因此 3 小时提前接近实际预测极限。

请基于冻结数据回答（三小件：数据规模与质量 → 预测技能 → 论断判定）：

1. **数据复现**：解析冻结的三个真实数据集（OMNI 5-min 太阳风、GFZ Kp、京都 Dst），统计 2021 年行数、时间覆盖、缺失率；用 `aux_omni_hourly_2021.csv` 交叉验证 Kp/Dst 解析是否正确（注意 OMNI 的 kp 为十分度 ×10）。
2. **3 小时提前预测**：构造滞后特征（建议与论文同构：太阳风 7 变量 × 9 小时/5 分钟滞后 = 每变量 108 个 lag；Dst 滞后 1/2/3 小时；Kp 按 3 小时间隔滞后 3–24 小时 = 8 个 lag），训练 RF 回归（100 棵树），在 2021-10-01~12-31 测试，报告 **±1 内准确率**（Kp 单位）及 RMSE。
3. **基线与消融**：报告持久性基线（最近已知 Kp）、均值基线；特征选择 top-50 是否提升；训练期对低 Kp 样本下采样（L=2，丢弃一半）的影响。
4. **重要性衰减**：报告 RF 特征重要性随历史时滞的变化（近端 ≤15 分钟 vs 远端 ~8–9 小时的均值），判断"重要性随滞后快速衰减"是否成立。
5. **结论**：论文 82.55% 与"重要性快速衰减"论断，在冻结数据口径下判定为 `supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 冻结包物理位置：`$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md`、`data/source_manifest.json` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 主数据（3 个真实数据集，均为论文引用的官方源）：
  - `omni_hro_5min_2021\omni_5min_2021.csv`：NASA OMNI 5 分钟高分辨率太阳风，105,120 行（2021 全年 365×288）。列：`YR,MO,DY,HR,MN,F,BX_GSE,BY_GSE,BZ_GSE,flow_speed,proton_density,T`（F=磁场总强度 fma，T=质子温度 K）；原 CDF 缺失填充值 9999.9 / 9999999 已转为 NaN。
  - `kp_gfz\kp_gfz_2021.csv`：GFZ 官方 Kp/ap 指数（3 小时间隔），2,920 行（2021 全年 365×8）。列：`YR,MO,DY,HR_START,HR_MID,MJD_START,MJD_MID,Kp,ap,flag`；Kp 为 0–9 连续标度（1/3 步长）。
  - `dst_kyoto_2021\dst_kyoto_2021.csv`：京都 WDC Dst 指数（provisional，每小时），8,760 行。列：`YR,MO,DY,HR,Dst`（nT）。
  - `aux_omni_hourly_2021.csv`：NASA OMNI 官方 hourly 数据集（HuggingFace 官方镜像，CC-BY-4.0）2021 年子集，8,760 行 × 48 列（含 `kp_index`(×10)、`dst_index_nt`、7 个太阳风变量等）。**辅助交叉验证源，非必需**。
- 原始溯源文件（12 个月 5-min CDF.gz、GFZ 全历史 Kp 文本、12 个月京都 Dst 请求文件）同样冻结在包内，SHA-256 见移动日志。
- 规模：主数据 ~6MB，CPU 可完成训练。

## 方向提示（协议建议）

1. **预测网格**：建议每 3 小时一个预测点（00/03/06/…/21 UTC），目标 = t+3h 的 Kp（即 GFZ 中 `HR_START = (t+3h)` 的区间）。2021 全年约 2,916 个事件；warm-up（前 9 小时）需显式处理。
2. **防泄漏**：特征严格来自 `≤ t` 的已观测数据（最新可用 Kp 为 `[t−3h, t)` 区间值；5-min 太阳风最晚取 `t` 时刻值）；目标为 `t+3h`。禁止用 `t+3h` 及之后任何信息。
3. **缺测**：5-min 太阳风存在约 5–9% 缺失（已为 NaN）。建议前向填充后取 lag（或按训练集中位数填充），并在报告中说明；sklearn RF 不接受 NaN。
4. **指标**：accuracy = 测试集中 `|predicted Kp − actual Kp| ≤ 1`（Kp 单位）的比例；同步报告 RMSE 与 confusion（按 ±1 内/外二值）。
5. **对照**：论文数值（82.55%、top-100→top-50 提升、下采样提升）只能用于对照讨论，禁止抄为实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）、关键数字、与论文 82.55% 的差距及原因分析。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成解析、特征构造、训练与评估。
3. **`results/evidence_table.csv`**：至少含列 `time,actual_kp,predicted_kp`（测试期逐事件），并附 `period,n,base_rate,accuracy,rmse` 汇总行。
4. **`results/metrics.json`**：数据规模统计、各模型/基线指标、特征重要性衰减（近端/远端均值与比值）、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（网格/预处理/缺失处理 vs 论文差异）。

## 数据铁律提醒

- 只使用本包冻结的真实数据；禁止模拟/合成数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论。
- 预测特征与目标之间的时间顺序必须严格（无未来信息泄漏）。
