# PAPER_ANCHOR（私有）：2504.04211 PTA 归一化流

来源：arXiv:2504.04211v2（Lai & Li 2025, "Accelerated Bayesian Inference for Pulsar Timing Arrays: Normalizing Flows for Rapid Model Comparison Across Stochastic Gravitational-Wave Background Sources"）。全部数值摘自论文摘要、§IV–VI、Table I/III/V（论文全文：candidate-papers/astro/2504.04211.pdf）。

## 锚 A1 — NF 后验与 MCMC 的 Hellinger 距离（核心结果）

| 项 | 值 |
|---|---|
| 指标名 | Hellinger 距离（0–1，越小越接近）：直接 NF vs MCMC；重加权 NF vs MCMC |
| 论文数值 | 重加权均值 **0.2611**（直接 NF 均值 0.3665）；论文判据"H<0.3 视为对齐良好"；典型值 ≲0.3（摘要） |
| 出处 | §IV + Table I（逐模型：IGW 0.3003/0.1239；Dual(w,r) 0.3186/0.1785；Dual(Stable) 0.3555/0.1681；Dual(Dynamic) 0.2955/0.1926；SMBHB 0.5078/0.4216；PowerLaw 0.4118/0.3911；FOPT 0.3492/0.1797；DW 0.2426/0.1729；SIGW 0.4671/0.4554；CSmeta 0.4164/0.3268） |
| 定义口径 | 22 维参数（20 红噪声 + 2 SGWB）后验样本的 Hellinger 距离（定义见论文 Appendix H）；"NF/MCMC"列 = 直接 NF 采样，"Reweighted/MCMC"列 = 用似然重加权后的 NF 样本 |
| 容差 | 判分以量级带为主：重加权 Hellinger 均值 ≤0.45 且逐模型多数 ≤0.5；"重加权优于直接 NF"方向性成立 |

## 锚 A2 — NF 与 MCMC 的 Bayes factor 一致性（核心结果）

| 项 | 值 |
|---|---|
| 指标名 | 10 模型两两 Bayes factor（BF=Z(i)/Z(j)）：MCMC（Nested Sampling+KDE）vs NF（学习 HME） |
| 论文数值 | "In most cases, the NF-derived Bayes factors agree with those from MCMC, with NF values lying within the uncertainties of traditional nested-sampler estimates"（§V）；例（Dual D 行 vs SMBHB 列）：MCMC=3.3±0.6，NF=4.0±0.06；（vs DW 列）：MCMC=172.3±52.6，NF=221.8±7.6 |
| 出处 | §V + Table III |
| 定义口径 | HME 证据估计：丢弃最低 10% 似然值降方差；NF 每模型 2×10^5 训练样本 × 50 epochs；MCMC 参考 = Nested Sampling 的 KDE 证据 |
| 容差 | 判分以排序与量级为主：多数模型对 NF 与 MCMC 的 BF 在同一量级（线性比 ≤3× 或 log BF 差 ≤1）且模型排序一致 |

## 锚 A3 — 加速声明（第三发现，含混杂因素）

| 项 | 值 |
|---|---|
| 指标名 | 每模型推断+训练时间（含混杂因素说明） |
| 论文数值 | NF ~20 小时/模型（10 颗脉冲星，GPU）vs MCMC ~10 天（68 颗脉冲星，CPU）；扩展性：N_pulsars=8..15 拟合得每残差每 epoch 时间 T_per-res ≈ 0.13 s（Eq. 16） |
| 出处 | 摘要 + §VI（论文明确说明 10 vs 68 脉冲星、GPU vs CPU 为混杂因素，比较非严格对照） |
| 容差 | 效率为次要锚：报告时间+硬件即可；不要求复现 20h/10d 数值本身 |

## 辅助事实（数据定义，供判分与复现参考）

- 数据：NG15 wideband，10 颗脉冲星（Table V），4,944 个 ToA（本包 v2.1.0 为 4,954，+1/颗）；每脉冲星 2 个红噪声参数 + 全局 2 个 SGWB 参数 = 22 维。
- 10 个 SGWB 源模型：SMBHB、PowerLaw、Cosmic String（meta-stable）、Domain Wall、FOPT、SIGW、Dual nT/IGW、Dual (w,r)、Dual (Stable)、Dual (Dynamic)。
- 许可：NG15 数据 Zenodo 16051178（CC-BY-4.0）；论文 arXiv。