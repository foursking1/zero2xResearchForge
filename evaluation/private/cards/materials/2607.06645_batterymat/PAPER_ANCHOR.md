# PAPER_ANCHOR: 2607.06645_batterymat（私有）

论文：Lee, Campbell, Zhang, Choudhary, arXiv:2607.06645 (2026)。锚全部摘自论文正文/表格，禁臆造。

## 锚 1（主锚，A 维度）
- 指标名：DFT 验证层平均电压（凸包平衡电压；LMP 为步进均值）
- 论文数值：LFP **3.60** V、LMP **3.91** V（†步进均值）、LMO **4.08** V、LCO **4.18** V、NMC 变体 **4.40** V（边界案例）
- 出处：Sec 2.5（2.5.1 LFP "convex-hull average voltage is 3.60 V"；2.5.2-2.5.5 同理）；Sec 2.6 表（p12：V_DFT_avg vs V_exp_avg，LFP 3.60/3.45、LMP† 3.91/4.10、LMO 4.08/4.05、NMC-var 4.40/3.70、LCO 4.18/4.05）；仓库 `screening_cathode_analysis.md`（LFP hull 4 平台 3.48/3.58/3.65/3.67 加权 3.60；LMO 2 平台 4.17/4.00 加权 4.08；LCO 3 平台 4.01/4.23/4.48 加权 4.18；LMP 步进均值 3.91；NMC 5 平台 4.40）
- 定义口径：V_step = E(n−1) − E(n) + e_li（e_li 见各 energies.json：PBE −1.9031、optB88-vdW −0.9646）；凸包 = ΔE(x)=E(x)−xE(1)−(1−x)E(0) 下凸包，V=−dΔE/dx，按 Δx 加权；LMP 因全脱锂（Mn⁴⁺）未收敛无 x=0 端点 → 步进均值
- 容差：agent 重算与论文值差 ≤0.05 V 且四主体系 |V−V_exp| ≤0.3 V → A 满分（见 SCORE_RUBRIC.md）

## 锚 2（代理筛选层，佐证）
- 指标名：锂池候选筛选漏斗
- 论文数值：锂含 JARVIS-DFT 池 7,474 条（过滤后）→ 71 个候选；top 候选由聚阴离子磷酸盐/氟化物主导
- 出处：Abstract（"ranks the lithium-containing JARVIS-DFT pool into 71 candidates"）；Sec 2.9 与仓库 `cathode_candidates_ranked.csv`（71 行）
- 定义口径：电压筛选 avg 3.0–4.5 V（排名）或 1–5.5 V（Stage-2 过滤）、max_voltage ≤5.5 V、ehull ≤0.05 eV（JARVIS-DFT 元数据）、max_grav_cap >20 mAh/g
- 容差：能重现电压筛选（1<avg≤5.5 且 max≤5.5）且 71 候选子集一致 → 佐证成立

## 锚 3（Li 参考修正，佐证）
- 指标名：锂金属参考能（同基组重算）
- 论文数值：PBE e_li = −1.9031 eV/atom；optB88-vdW e_li = −0.9646 eV/atom；同基组重算消除表列参考的 ~1 V 系统偏移
- 出处：Sec 5（"recompute the reference in the same basis... removing a systematic offset of about 1 V"）；Abstract；仓库 README "Key Reference Values & Sources"；`dft_inputs/JVASP-913-Li/`
- 容差：agent 使用上述 e_li 值并量化 ~1 V 偏移（量级 0.5–1.5 V 视为正确）

## 辅助事实（裁判核查用）
- ALIGNN 蒸馏保真度（上下文，不判分）：held-out test MAE 0.17 V / R² 0.94（761 条，dataset-mean 基线 1.03 V；Sec 2.1，Fig 2）——标签集在 Zenodo（本包不含），不可重算，仅作背景。
- 容量声明（上下文）：四主体系理论体积容量 ±5%（Sec 2.6）——需松弛 CONTCAR 体积（仓库未含，gitignored），本任务不判分。
