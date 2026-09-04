# TASK: 计算参考电压 ≠ 实验电压？——Na-ion 阴极 ML 电压筛选器的端到端验证

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- 任务 ID：`2606.23725_comp_refs_not_experiments`
- 层级：L2（端到端科研再发现；目标论文不提供，数据即全部输入）
- 领域：materials（电池材料，ML 电压筛选）
- 裁判：LLM judge（论文锚 + 证据抽查），见 `SCORE_RUBRIC.md`（私有）

---

## 1. Input（输入：冻结真实数据）

数据包位于 `data/`，全部为真实数据（官方仓库冻结，CC-BY-4.0），详见 `data/SOURCE.md`（来源、许可、逐文件 SHA-256）。

### 1.1 `data/na_cathodes_validation.csv`（7 行，Na-ion 阴极验证集）

一位研究者构建了一条"AI 电池材料筛选"流水线：一个图神经网络（GNN）电压预测器，训练数据来自 Materials Project 的**计算**平均电压（约 2814 张（充/放）晶格图，其中仅 20 张是 Na 化学；训练与预测均以计算电压为参考尺度）。本表是该研究者对 7 个**未见过的 Na-ion 阴极**（不在训练语料内）的验证数据。

| 列 | 含义 |
|---|---|
| `mp_id` / `formula` / `polymorph` | 化合物身份（Materials Project id / 化学式 / 多形体） |
| `family` | 化学家族（polyanionic_phosphate / polyanionic_fluorophosphate / layered_oxide） |
| `tier` | 实验电压的证据等级：A=文献文本明确给出平均电压；B=由作者给出的平台/区间做一次算术得到；C=从图读值（低置信） |
| `in_training_corpus` | 该化合物是否在 GNN 训练语料中（全部为 False，即全部真正样本外） |
| `v_lit_v` | **实验**文献平均电压（vs Na 金属，引文锚定，单位 V） |
| `v_pred_v` | GNN **预测**平均电压（V） |
| `v_mp_v` | Materials Project PBE+U **计算**平均电压（V；仅部分行有值，空白=该结构未出现在 MP 电池库） |
| `excluded_canonical` | `yes` 表示该行被操作者审计剔除出"规范口径"（原因见 `exclusion_reason`：maricite NaFePO4 循环中是非晶相，与预测用的晶态结构不是同一相；且 tier C 低置信）。其余行 `no` |
| `exclusion_reason` | 剔除原因（仅 maricite 行非空） |

### 1.2 `data/li_offset_audit.csv`（4 行，本地 DFT 基准审计）

同一流水线还包含一个本地 PBE+U（Quantum ESPRESSO）验证基准，用于"验证"候选电压。研究者用 4 个 Li-ion 基准对（实验平台电压公认）审计该基准的绝对电压声称：

| 列 | 含义 |
|---|---|
| `couple` / `key` | 氧化还原对名称/键 |
| `v_exp_v` | 实验平台电压（V，文献锚定） |
| `v_qme_v` | 本地 PBE+U 基准计算的平均电压（V） |
| `delta_v_qme_minus_exp` | 偏移 δ = V_QME − V_exp（V） |

---

## 2. Output（输出要求）

在你的工作目录下产出以下提交物（一个可复现的分析包）：

- `claim.md`：你检验的**可证伪声称**（一句话）+ 失败条件（何种证据会推翻它）+ 结论标签（四档之一：`supported` / `partially_supported` / `contradicted` / `inconclusive`）。
- `code/`：完整可运行的分析代码（Python/R 均可），**所有指标必须从 `data/` 冻结数据重算**，不得手工抄写任何数字。
- `results/evidence_table.csv`：逐行证据表（行级数值：误差、预测、参考等，列自定但须有列名与单位说明）。
- `results/metrics.json`：你报告的**全部总体指标**（命名自洽、注明定义与单位；含你对该系统"是否可用于筛选"的判断依据）。
- `results/figure.*`：可视化（可选，建议含误差/残差结构图）。
- `report.md`：方法、结果、结论、边界（≤2 页）。

### 科学目标（Scientific goal）

端到端检验以下假设链（这是目标论文声称的未经检验假设，论文本身不提供）：

> **H0**：该 GNN 电压筛选器在未见 Na-ion 阴极上的误差小到可以驱动材料筛选决策，且"计算参考电压（MP PBE+U）≈ 实验电压"成立——即用计算参考训练/评估的筛选器对实验也有用，系统误差可通过一个常数（加性）偏移校准修复。

请基于冻结数据回答（方向与"提示"见下）：

1. **真实误差**：筛选器相对实验文献电压的表现如何？是否达到你认为的"可筛选级"精度（给出你的阈值与依据）？
2. **残差结构**：误差与实验电压的关系是什么？这告诉你什么？
3. **加性校准**：一个常数偏移校准能否修复系统误差？请用**样本外**方式论证（估计偏移的行与评估的行不重叠），并给出你对其不确定性的**保守处理**（说明方法）。注意防止把"整体看起来像单个大偏差"误判为"可校准"。
4. **误差分解**：在能同时比较"预测、计算参考、实验"三者的行上，模型误差主要来自模型自身，还是来自它学到的计算参考尺度？用数值分解论证。
5. **自有基准审计**（次级）：本地 PBE+U 基准的绝对电压声称是否可信？给出你的判定规则与依据。

最后给出结论标签，并明确结论的**适用边界**（样本量、化学家族、证据等级、是否支持普适性否定）。

提示（不给方法步骤）：以实验值为基准；注意证据分级与样本量；误差结构（而非平均值）往往决定校准是否可行；区分"模型误差"与"参考误差"。

---

## 3. 数据铁律提醒

- **只用 `data/` 内冻结的真实数据**；禁止模拟/合成数据；禁止把文献里报告的数值当作自己从数据算出的结果。
- 所有报告数字必须能从冻结数据 + 你的代码重算；裁判会抽查 1-2 个关键数并运行你的代码复核。
- 遵守 `data/SOURCE.md` 记录的许可（CC-BY-4.0，需署名）；不得调用 Materials Project API（不需要，`v_mp` 已冻结）。
- 数据文件 SHA-256 固定（见 `data/SOURCE.md`），不得改动。