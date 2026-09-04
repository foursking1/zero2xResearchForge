# PAPER_ANCHOR（私有，仅裁判/编译者可见）：2607.18127_cloudens

> 用途：LLM judge 判分基准。本卡为 L1（critical claim）。数值全部摘自 arXiv:2607.18127（Doan, Islam, Miranskyy, Nguyen, Heldal, Pelliccione, "ClouDens: Operational Context-Aware Anomaly Detection for Large-scale Cloud System Monitoring", IEEE TNSM 投稿）§II/§V、Table I-IV 与 Fig 6-7，禁止臆造。

## 目标论文与协议

- 数据（§II-A，基于 Islam et al. arXiv:2411.09047 / Zenodo 10.5281/zenodo.14062900）：IBM Cloud Console 生产遥测，39,365 时点 x 117,448 特征，5 分钟间隔，约 4.5 个月；特征名编码上下文属性（位置/角色/组件/HTTP 方法/状态码/端点/聚合类型）。
- 子集（§V-B）：按 HTTP 状态码（4xx/5xx）x 聚合（count/avg/min/max）分 8 个子集；5xx 每子集 2,406 特征（99.02% 稀疏），4xx 每子集 4,085 特征（94.74% 稀疏）。
- 划分（§V-B）：训练 2024-01-26 ~ 2024-02-29（5 周，剔除标注异常窗 a1-a6）；验证 = 训练段 30%；测试 2024-03-01 ~ 2024-05-31（26,488 时点）；25 个标注异常窗中 19 个在测试期（a7-a25），覆盖 967 时点（3.65%）。
- 预处理：zero/mean/median 三插补（5xx count 最优 = zero，Table III）；min-max 仅训练段；滑窗 w=6、单步预测。
- 模型（§V-B-4）：GRU 基线 vs ClouDens（上下文感知图 + A3T-GCN），均 32 隐层、batch 32、Adam lr=1e-3、MSE，除图外一致。
- 评分（Table III/IV）：LF {W=30, W'=2, Lt=0.99975}；MD {ϵ=99.8}（5xx count 最优）；NAB Standard / LowFN（Reward Low FN）profile。
- 异常窗 ID 映射（Table I + anomaly_windows.csv 核验）：测试期 19 窗按时间 a7→0 ... a25→18；source 1=Issue Tracker（ID 3,12,13 = a10,a19,a20）、2=Instant Messenger（0,5,6,7,8,9,14,16,17 = a7,a12,a13,a14,a15,a16,a21,a23,a24）、3=Test Log（1,2,4,10,11,15,18 = a8,a9,a11,a17,a18,a22,a25）。

## 锚 A1 — NAB 分数（Table IV，"5xx count" 子集，w=6，逐点混淆矩阵总和 26,488）

| 评分 | 模型 | TP | TN | FP | FN | NAB Standard | NAB LowFN | 检出 IT | 检出 IM | 检出 TL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LF {30,2,0.99975} | GRU | 6 | 25468 | 53 | 961 | 6.58 | 13.16 | 1/3 [12] | 4/9 [6,7,8,17] | 0/7 |
| LF | ClouDens | 7 | 25469 | 52 | 960 | 11.38 | 18.11 | 1/3 [12] | 5/9 [6,7,8,9,17] | 0/7 |
| MD {99.8} | GRU | 13 | 25481 | 40 | 954 | 5.89 | 10.95 | 0/3 | 4/9 [6,8,14,17] | 0/7 |
| MD | ClouDens | 16 | 25483 | 37 | 952 | 20.94 | 26.24 | 1/3 [3] | 6/9 [6,7,8,9,14,17] | 0/7 |

- 出处：Table IV（§V-C EQ1）。ClouDens MD 两 NAB（20.94/26.24）与复现包 experimental_results/full_data_reward_fn_priority.csv 中 A3TGCN* 行一致（16/25484/37/951, 20.94/26.24）。
- 方向结论（§V-C Answer to EQ1）：上下文感知图显著提升 NAB、降低 FP、扩大异常覆盖、提前检测。

## 锚 A2 — 检测质量（Table IV 混淆矩阵 + 检出列表）

- ClouDens MD：TP 16 vs GRU 13；FP 37 vs 40；FN 952 vs 954。ClouDens 额外捕获 Anomaly 7、9（IM）与 Anomaly 3（Issue Tracker，GRU 完全漏检）。
- ClouDens LF：TP 7 vs 6、FP 52 vs 53；捕获 Anomaly 9（IM，GRU LF 漏检）。
- 判分口径：TP/FP 方向与 IM 覆盖方向（6/9 vs 4/9）。

## 锚 A3 — 评分策略互补与子集差异（§V-C EQ2）

- 5xx count 与 4xx count 为最高 NAB 子集（MD LowFN 26.24 与 18.56，Fig 6(b)）；count 子集各检出 8/19、9/19 异常（Fig 6(a)）。
- 不同策略/子集揭示不同异常：LF 下 5xx max 独检 Anomaly 4、16；4xx avg/min 检 3、10、11；MD 下 4xx count 检出跨全部三类来源的 8 个异常。
- 辅助锚（Table V，MD）：两子集 ensemble "4xx count + 5xx count" NAB LowFN = 22.28、检出 10/19（IT 2/3、IM 6/9、TL 2/7）、FP 153、2.01 alerts/day；全 8 子集 ensemble LowFN = -10.05、检出 13/19、FP 402、4.98 alerts/day。

## 判分对照速查（judge 用）

- A1 满分带：MD 两 profile ClouDens > GRU 且比值 >= 1.3（锚比值 3.56x / 2.40x）。
- A2 满分带：ClouDens MD Standard ∈ [14,28]、LowFN ∈ [18,34]（锚 20.94/26.24，约 ±33%）。
- A3：TP 升/FP 降/IM 覆盖升 三条至少两条。
- B 抽查字段：parquet 行数（39,365）、5xx count 特征数（2,406）、anomaly_windows 行数（25）/测试期 19 窗、GRU 与 ClouDens 的 MD NAB Standard 重算（与证据表绝对差 <= 2.0）。
