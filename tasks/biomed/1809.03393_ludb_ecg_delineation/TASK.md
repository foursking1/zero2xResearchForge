# 科研任务：LUDB「多导联 ECG 波形分割提升 P/T 波检测精度」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`1809.03393_ludb_ecg_delineation`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Kalyakulina et al., "LUDB: A New Open-Access Validation Tool for Electrocardiogram Delineation Algorithms", IEEE Access 8:186181-186190, 2020（arXiv:1809.03393）
- 领域：biomed / 心电信号（ECG）/ 波形分割（delineation）

## 问题（可证伪）

LUDB 论文的核心论断：**多导联（12 导联）联合分析的 ECG 波形分割算法，在 P 波与 T 波检测上显著优于单导联方法**。论文在 LUDB 上对比了两类工具：

- Kalyakulina et al. 的小波多导联算法（逐导联检测 + 跨导联一致性校正：复合波须在 ≥8/12 导联检出、参考点跨导联取平均）——P/QRS/T 各关键点（onset/peak/offset）灵敏度 Se ≥ 97%（P onset Se 98.46%、QRS onset Se 99.61%、T offset Se 98.03%）；
- 单导联工具 ecg-kit——P 波与 T 波明显逊色（P onset Se 88.26%、P peak Se 89.64%、T peak Se 85.62%、T offset Se 85.00%）。

请基于冻结数据回答：

1. **数据与标注**：解析冻结 LUDB 数据（WFDB 格式：200 条记录，每条 12 导联 × 500 Hz × 10 秒；每导联独立参考标注，符号 `(`=波 onset、`)`=波 offset、`N`=QRS 峰、`p`=P 峰、`t`=T 峰）。统计各导联 P/QRS/T 波数量并加总，与论文总量（58,429 个波：P 16,797 / QRS 21,966 / T 19,666）核对比例关系。
2. **分割方法**：实现至少两类可运行的分割管线：
   - **多导联方法**（推荐）：先在每条导联独立检测 QRS（Pan-Tompkins 或小波），再做跨导联一致性校正（某复合波在 ≥8/12 导联检出视为存在；参考点时间跨导联取平均），再在 QRS 前后窗内检测 T 波与 P 波，输出 onset/peak/offset；
   - **单导联基线**：仅使用单一导联（如 II 导联）运行同一核心检测器（不做跨导联校正），或使用现成单导联库（如 neurokit2 的 delineate）。
3. **精度对比**：按 ANSI/AAMI EC57:1998 容差（±150 ms，即 ±75 样本 @500 Hz）判定 TP/FP/FN，计算 Se、PPV 与时间误差 m±σ，给出多导联 vs 单导联在 P/QRS/T 各关键点上的对比表，验证「多导联显著改善 P/T 波检测」论断是否成立（同时报告 QRS 是否保持同等精度）。

- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR/ludb_1.0.1`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 内容：200 条 10 秒 12 导联 ECG（`data/` 下每记录 14 个文件：`.hea` 头、`.dat` 信号、12 个导联标注 `.i/.ii/.iii/.avr/.avl/.avf/.v1-v6`）；`ludb.csv` 元数据（ID/性别/年龄/节律/电轴/诊断分类）；`RECORDS`、`ANNOTATORS`、`SHA256SUMS.txt`（官方校验和，全部 2805 项已核对一致）。
- 来源：PhysioNet LUDB v1.0.1（https://physionet.org/content/ludb/1.0.1/）；许可：ODC Attribution License（ODC-By）。
- 采样：500 Hz，10 秒 → 每导联 5000 样本；导联顺序 i, ii, iii, avr, avl, avf, v1, v2, v3, v4, v5, v6。
- 数据规模：全量 200 条（约 24.8MB）。若计算资源受限，可冻结 30-50 条子集（固定随机种子），并在报告中声明；两种方法必须使用同一子集。

## 方向提示（协议建议）

1. **读取**：`wfdb` 库 `rdsamp()` 读信号、`rdann(record, 'i')` 读标注；标注符号见上。`rdann` 的 `sample` 为样本序号（0-based），换算 ms = sample / 500 × 1000。
2. **简化口径**：可只报告 peak（N/p/t）为主口径，onset/offset 为加分项；QRS 检测优先保证正确，P/T 在 QRS 前后固定窗口（如 QRS onset 前 200-350 ms 找 P，offset 后 200-400 ms 找 T）。
3. **多导联校正**：以「某复合波被 ≥8/12 导联检出」作为存在判据；对检出导联的参考点时间取平均/中位数；评估时把多导联输出与每条导联的参考标注分别比对（逐导联评估）。
4. **评估**：容差 ±150 ms（±75 样本）；Se=TP/(TP+FN)、PPV=TP/(TP+FP)、m±σ 为时间误差均值±标准差（ms）。建议对每条记录评估后跨记录聚合。
5. **规模控制**：全量 200 条 × 12 导联 × 5000 样本（合计约 1200 万样本）CPU 可处理；如需训练深度模型，可只用 30-50 条子集。

## 输出要求（提交物）

1. **`claim.md`**：三问判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成分割与评估。
3. **`results/evidence_table.csv`**：至少含列 `method,point_type,se,ppv,mean_err_ms,std_err_ms,tp,fp,fn`（每方法 × 每关键点一行；point_type 如 p_onset/p_peak/p_offset/qrs_onset/qrs_peak/qrs_offset/t_peak/t_offset）。
4. **`results/metrics.json`**：样本统计（记录数、导联数、波计数）、两种方法各关键点 Se/PPV/m±σ、多导联 vs 单导联差值、论文锚对照、结论标签。
5. **`report.md`**：方法（预处理/检测器/多导联校正/单导联基线）、结果、局限（子集 vs 全量、实现差异 vs 论文算法、容差口径）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成 ECG 或外部心电图替代。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值（Table 6 的 Se/PPV/m±σ、58,429 个波等）只能用于对照讨论。
- 两种方法必须在同一冻结子集、同一评估协议下比较；参考标注不得参与方法训练/调参。
