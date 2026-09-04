# SCORE_RUBRIC（私有）：2504.04211_pta_normalizing_flows

- 层级：L1（critical claim）；总分 100 = A 核心结果达成度 60 + B 证据真实性 25 + C 方法与报告 15。
- 判分模型：任意强 LLM judge（Claude/GLM 均可）；跨 agent 比较用同一 judge。

## A. 核心结果达成度（60）

以 PAPER_ANCHOR A1/A2 为主锚：复现"重加权 NF 后验与 MCMC 的 Hellinger 均值 0.2611（典型 ≲0.3）"与"NF Bayes factor 与 MCMC 在不确定度内一致（Table III）"。

| 分段 | 得分 | 条件 |
|---|---|---|
| 满分 | 60 | ≥3 个 SGWB 模型：重加权 Hellinger 均值 ≤0.45 且逐模型多数 ≤0.5；NF 与 MCMC 的 BF 排序一致且多数模型对在线性比 ≤3×（或 log BF 差 ≤1）；给出逐模型证据表 |
| 半满 | 30 | 方向正确但 Hellinger 均值 0.45–0.6 或仅 1–2 个模型；或 BF 部分不一致（个别模型对反转）但整体排序保持；或缺 MCMC 参考（只用近似） |
| 零分 | 0 | Hellinger 均值 >0.6 或多数模型 BF 反转；未做 NF vs MCMC 对照；用论文数字冒充结果 |

注：NF 训练具随机性，锚取量级带而非精确值；允许缩减模型数/训练样本并明确报告；效率声明（A3）为次要加分项，不达标不扣 A 分。

## B. 证据真实性（25）

- 提交含代码+证据表；裁判抽查 2 数：某模型（如 PowerLaw）的 reweighted Hellinger 距离，与某对模型的 NF Bayes factor（运行提交代码从冻结数据重算，与报告一致；随机算法在固定种子下应可复现，容差 ≤1e-6 或按报告的标准差声明）。
- 无代码/不可运行 → 扣 8；抄论文数字（无法重算）→ 该项 0–8。

## C. 方法与报告（15）

- C1 方法合理（5）：数据提取（ENTERPRISE）、NF 架构/训练协议、HME 证据估计流程明确。
- C2 稳健性（6）：模型覆盖数、随机种子、MCMC 收敛判据、时间/硬件报告、ToA 版本差异说明。
- C3 报告边界（4）：四档结论标签、scope/limitations（10 vs 68 脉冲星、模拟训练数据口径、GPU/CPU 混杂）、不宣称已证明 SKA 规模可行性。