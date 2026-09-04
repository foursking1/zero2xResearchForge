# TASK: PTA 随机引力波背景模型比较的归一化流加速——L1 critical claim

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- 任务 ID：`2504.04211_pta_normalizing_flows`
- 层级：L1（critical claim；卡标 L2 → 按新映射造 L1 题）
- 领域：astro（脉冲星计时阵列 / SGWB 贝叶斯推断）
- 裁判：LLM judge（论文锚 + 证据抽查），见 `SCORE_RUBRIC.md`（私有）

## 1. Input（输入：冻结真实数据）

数据包位于 `data/`，为**真实公开数据**（NANOGrav 15-Year Data Set v2.1.0 官方发布，Zenodo 16051178，CC-BY-4.0），详见 `data/SOURCE.md`（来源、许可、逐文件 SHA-256）。

### 1.1 `data/ng15_wideband_10pulsars/`（20 个文件 = 10 颗脉冲星 × {tim, par}）

论文 Table V 的 10 颗脉冲星宽波段计时数据（J0030+0451、J0613-0200、J1600-3053、J1744-1134、J1909-3744、J1910+1256、J1918-0642、J1944+0907、J2043+1711、J2317+1439），含 ToA、测量不确定度、白噪声与天体测量参数：

| 脉冲星 | 本包 ToA 数（v2.1.0） | 论文 Table V |
|---|---|---|
| J0030+0451 | 725 | 724 |
| J0613-0200 | 424 | 423 |
| J1600-3053 | 482 | 481 |
| J1744-1134 | 434 | 433 |
| J1909-3744 | 834 | 833 |
| J1910+1256 | 217 | 216 |
| J1918-0642 | 488 | 487 |
| J1944+0907 | 181 | 180 |
| J2043+1711 | 460 | 459 |
| J2317+1439 | 709 | 708 |
| 合计 | **4,954** | **4,944** |

> 版本说明：v2.1.0 每颗比论文多 1 个 ToA（官方 2025-07 版本更新），须在报告中显式说明。

## 2. Output（输出要求）

在你的工作目录下产出以下提交物：

- `claim.md`：你检验的**可证伪科学声称**（一句话）+ 失败条件 + 结论标签（`supported`/`partially_supported`/`contradicted`/`inconclusive`）。
- `code/`：完整可运行的分析代码（Python/R 均可），**所有指标必须从 `data/` 冻结数据重算**，不得手工抄写任何数字。
- `results/evidence_table.csv`：逐模型证据表（至少含：SGWB 模型、Hellinger(NF/MCMC)、Hellinger(reweighted/MCMC)、log10 证据或 Bayes factor（NF 与 MCMC 各一列）、运行时间）。
- `results/metrics.json`：总体指标（Hellinger 均值/各模型值、BF 一致性度量、时间对比）。
- `results/figure.svg`（或 png/pdf）：至少一张关键图（如 NF vs MCMC 后验叠加图，或 Hellinger/BF 对照散点图）。
- `report.md`：方法、结果、结论、边界（≤2 页）。

### 科学目标（Scientific goal）

端到端评估目标论文（不提供全文）的核心结果在冻结数据上的可复现性：

> **核心论断**：归一化流（NF）框架在 NANOGrav 15 年数据（10 颗脉冲星）上可完成 10 类 SGWB 源模型的贝叶斯推断与模型比较：重加权后验与 MCMC 的 Hellinger 距离均值 0.2611（典型 ≲0.3，判为"对齐良好"）；NF 学习调和均值估计器得到的 Bayes factor 在多数模型上与 MCMC（Nested Sampling）在不确定度内一致；每模型运行时间 ~20 小时（含训练）vs MCMC ~10 天（68 颗脉冲星）。

请基于冻结数据回答：

1. **后验一致性**：对 ≥3 个 SGWB 源模型（如 PowerLaw、SMBHB、SIGW），用 NF（条件自回归流，22 维：20 红噪声 + 2 SGWB 参数）推断后验，并与 MCMC/嵌套抽样参考比较。你的 Hellinger 距离（直接 NF 与重加权 NF）与论文 Table I 的差距多大？"重加权使后验更接近 MCMC"是否成立？
2. **模型比较**：用学习调和均值估计器（或等价证据估计）计算各模型证据与 Bayes factor，与 MCMC 参考对照（Table III）。NF 与 MCMC 的模型排序是否一致？差异是否在不确定度内？
3. **效率**：报告每模型的训练+推断时间（注明硬件）。论文的"~20h vs ~10d"在什么口径下可比较？10 颗 vs 68 颗脉冲星、GPU vs CPU 的混杂因素如何影响该比较？
4. **数据口径**：说明本包 ToA 数与论文 Table V 的差异（+1/颗）对结果的影响边界。
5. **结论**：给出四档结论标签与适用边界。

提示（不给方法步骤）：数据提取用公开的 ENTERPRISE/enterprise_extensions（`.par`/`.tim` → 残差与噪声模型）；NF 训练用论文协议（正向模拟残差 + 条件流，2×10^5 样本 × 50 epochs，丢弃最低 10% 似然的 HME 方差削减）；Hellinger 距离定义见论文 Appendix H（0–1 尺度，H<0.3 为经验"对齐良好"判据）；MCMC 参考可用 PTMCMCSampler/嵌套抽样，须报告收敛判据；计算资源受限时允许缩减模型数/样本数并明确报告。

## 3. 数据铁律提醒

- **只用 `data/` 内冻结的真实数据**；NF 训练用的**正向模拟残差是论文协议的一部分**（可引用并说明），但冻结数据必须是本包的真实 NG15 计时数据；禁止用合成数据冒充输入数据。
- 所有报告数字必须能从冻结数据 + 你的代码重算；裁判会抽查 1-2 个关键数并运行你的代码复核。
- 遵守 `data/SOURCE.md` 记录的许可（CC-BY-4.0，引用 Agazie et al. 2023）；数据文件 SHA-256 固定，不得改动。
- v2.1.0 与论文所用 v1.x 的 ToA 差异是**数据事实**，须在报告中显式说明，不得隐藏或"修正"。