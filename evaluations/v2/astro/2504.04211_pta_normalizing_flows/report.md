# EVAL REPORT v2: 2504.04211_pta_normalizing_flows

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（deepseek-v4-flash）
- 评测时间: 2026-08-21

## 总分: 35.0 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 0 | 60 | 依据数值带匹配铁律：agent 报告的关键实测数值——重加权 Hellinger 均值 0.6105（PowerLaw 0.5182, SMBHB 0.3245, DW 0.9888），logZ_NF_IS 与 logZ_MCMC_HME 的 BF 排序一致（PowerLaw>SMBHB>DW），但 3 个唯一模型对中仅 1 对 |ΔlnBF|≤1（SMBHB/PL 0.998），DW/PL 为 6.70、DW/SMBHB 为 7.70。逐一带入 rubric 区间：满分带要求 Hellinger 均值 ≤0.45 且逐模型多数 ≤0.5 且 BF 排序一致且多数模型对在线性比≤3×（或 logBF 差≤1）——均值 0.6105>0.45，且逐模型多数（2/3）>0.5，故满分带不命中；半满带要求 Hellinger 均值 0.45–0.6 或仅 1–2 个模型或 BF 部分不一致——均值 0.6105>0.6 且模型数为 3，严格落入零分带『Hellinger 均值 >0.6』条件（逐模型 DW 0.9888 亦>0.6）；即使 BF 排序一致，因 rubric 零分条件为『Hellinger 均值 >0.6 或多数模型 BF 反转』，命中其一即触发零分。另注意 Hellinger 仅在 2 维 SGWB 边缘分布计算（非论文 22 维），且 learned-HME NF 证据塌缩（neff≈1–2），NF 证据改用 IS 估计，均进一步偏离锚 A1/A2 口径；A3 效率为次要锚，方向成立（~2.3×加速）但不改变 A=0。该数值有 metrics.json/evidence_table.csv 落盘支撑，故按零分带给 0 而非因证据缺失降档。 |
| B 证据真实性/实际复现 | 35.0 | 40 | 磁盘证据扫描显示：metrics.json、evidence_table.csv（results 与 results_smoke 两层）、critical_checks.json、provenance/data_facts.json、pta_data_summary.json 及多份 figure 均存在；evidence_table.csv 与 metrics.json 数值（如 PowerLaw reweighted Hellinger=0.5182、logZ_NF_IS=68975.409、MCMC=69005.556 等）与 report.md/claim.md/EVAL_REPORT 完全一致，可逐项核对；代码完整（pta_data.py/pta_likelihood.py/pta_nf.py/pta_postprocess.py 等），可读且无抄袭论文数字迹象（报告明确区分论文值 0.2611 与实测值 0.611）。按规则落入『有证据文件且数值与报告严格一致、可核对』区间，B∈[30,40]。扣 5 分：① 独立重算未执行，无法通过代码运行复核证据文件真实性；② 证据本身存在结构性弱点——Hellinger 降维至 2 维（非论文 22 维）、NF 训练缩减 40 倍且 learned-HME 证据崩溃（neff≈1）、MCMC 链长不足（autocorr τ≈121–123 已接近步数 1200），直接影响核心指标的可信度与可比性。综合给 B=35。 |

## A 核心结果达成度（0/60）

依据数值带匹配铁律：agent 报告的关键实测数值——重加权 Hellinger 均值 0.6105（PowerLaw 0.5182, SMBHB 0.3245, DW 0.9888），logZ_NF_IS 与 logZ_MCMC_HME 的 BF 排序一致（PowerLaw>SMBHB>DW），但 3 个唯一模型对中仅 1 对 |ΔlnBF|≤1（SMBHB/PL 0.998），DW/PL 为 6.70、DW/SMBHB 为 7.70。逐一带入 rubric 区间：满分带要求 Hellinger 均值 ≤0.45 且逐模型多数 ≤0.5 且 BF 排序一致且多数模型对在线性比≤3×（或 logBF 差≤1）——均值 0.6105>0.45，且逐模型多数（2/3）>0.5，故满分带不命中；半满带要求 Hellinger 均值 0.45–0.6 或仅 1–2 个模型或 BF 部分不一致——均值 0.6105>0.6 且模型数为 3，严格落入零分带『Hellinger 均值 >0.6』条件（逐模型 DW 0.9888 亦>0.6）；即使 BF 排序一致，因 rubric 零分条件为『Hellinger 均值 >0.6 或多数模型 BF 反转』，命中其一即触发零分。另注意 Hellinger 仅在 2 维 SGWB 边缘分布计算（非论文 22 维），且 learned-HME NF 证据塌缩（neff≈1–2），NF 证据改用 IS 估计，均进一步偏离锚 A1/A2 口径；A3 效率为次要锚，方向成立（~2.3×加速）但不改变 A=0。该数值有 metrics.json/evidence_table.csv 落盘支撑，故按零分带给 0 而非因证据缺失降档。

## B 证据真实性/实际复现（35.0/40）

磁盘证据扫描显示：metrics.json、evidence_table.csv（results 与 results_smoke 两层）、critical_checks.json、provenance/data_facts.json、pta_data_summary.json 及多份 figure 均存在；evidence_table.csv 与 metrics.json 数值（如 PowerLaw reweighted Hellinger=0.5182、logZ_NF_IS=68975.409、MCMC=69005.556 等）与 report.md/claim.md/EVAL_REPORT 完全一致，可逐项核对；代码完整（pta_data.py/pta_likelihood.py/pta_nf.py/pta_postprocess.py 等），可读且无抄袭论文数字迹象（报告明确区分论文值 0.2611 与实测值 0.611）。按规则落入『有证据文件且数值与报告严格一致、可核对』区间，B∈[30,40]。扣 5 分：① 独立重算未执行，无法通过代码运行复核证据文件真实性；② 证据本身存在结构性弱点——Hellinger 降维至 2 维（非论文 22 维）、NF 训练缩减 40 倍且 learned-HME 证据崩溃（neff≈1）、MCMC 链长不足（autocorr τ≈121–123 已接近步数 1200），直接影响核心指标的可信度与可比性。综合给 B=35。

## 证据与重算说明

独立重算未执行（本裁判未实际运行提交代码复核数字）。已核对的关键实测数（来自 results/metrics.json 与 results/evidence_table.csv，内部一致）：重加权 Hellinger 均值 0.6105（PowerLaw 0.5182, SMBHB 0.3245, DW 0.9888）；直接 Hellinger 均值 0.7947；logZ MCMC(HME) 69005.556/68999.013/68993.136，logZ NF(IS) 68975.409/68969.864/68956.291，learned-HME NF 证据为 -156440.85/-328364.92/-979475.43（塌缩）；BF 排序 MCMC 与 NF-IS 完全一致（PowerLaw>SMBHB>DW），|ΔlnBF| 最大 7.70，仅 1/3 对 ≤1；NF 每模型 285–328s vs MCMC 684–805s，加速 ~2.1–2.8×。数据侧：10 颗脉冲星 4944 个活动 ToA（与论文 Table V 一致），T_obs=5724.3 天。

## 结论

- **科学结论**: `partially_supported`
- 亮点: 诚实报告了计算资源受限导致的 NF 欠训练、IS 塌缩与 learned-HME 崩溃，未用论文数字冒充实测；BF 模型排序与 MCMC 完全一致且证据文件与报告数值严格对应，可追溯性好。
- 不足: 核心指标重加权 Hellinger 均值 0.611 严格落入 rubric 零分带（>0.6），且 Hellinger 仅在 2 维边缘计算（非论文 22 维）、NF 训练量缩减 40 倍、MCMC 参考证据为截断调和均值且链长不足，导致论文核心声明（后验对齐、BF 不确定度内一致）在冻结数据上未被定量复现。