# report.md — 异构云遥测异常检测基准复现报告

> 复现目标：Islam, M. S., Miranskyy, A. (2026), *Benchmarking Anomaly Detection
> Across Heterogeneous Cloud Telemetry Datasets*（arXiv:2602.13288），
> Table III 的两个 critical claims。冻结数据：NAB（58 序列 / 7 子组）+
> Microsoft Cloud Monitoring（60 序列 / 9 域）。本报告所有的数值均由代码从
> **冻结原始数据** 算出，不直接引用论文数值作为"实测"。

---

## 1. 协议

### 1.1 数据与完整性
- 冻结数据已核对 `data/source_manifest.json`（180/180 文件 SHA-256 逐文件一致；
  `code/verify_data_facts.py`）。Microsoft 总行数 **225,445**、Label=1 **4,555**；
  NAB 58 条 CSV / combined_windows.json 58 个条目。详见 `evidence/data_facts.txt`。
- 切分、窗口、异常标签全部按 **点索引** 域处理，避免时区/日历解析歧义。

### 1.2 时间切分
- 每条序列按时间排序后：`[0, 70%)` 训练；`[70%, 100%)` 测试。
- 训练期最后 10% 划为 **验证子集**（早停 + 似然校准选择，二者均只来自训练期）。
- 这是论文 §IV-A 的协议；`mongodb-application-rps`、`service-unavailable`、
  `artificialNoAnomaly` 等测试期无异常窗口的子组因此天然得到 0.00（与 Table III
  一致），用于确定性 sanity check。

### 1.3 模型与窗口
- 每个深度模型都是**重建式自编码器**（窗口 x -> 重建 x -> 每点 Gaussian
  (mean, log-var)，异常分数 = 重建残差平方 / 随机方差高斯负对数似然）：
  - **GRU**：单层 GRU 编码-解码（bidirectional=False，hidden=32）；
  - **TCN**：扩张因果卷积（channels 24×3，dil 1/2/4）；
  - **Transformer**：单层 4 头 encoder（dim=24）；
  - **TSMixer**：2 层 MLP-Mixer（token- 与 channel-mixing，dim=48）；
  - **IsolationForest**：200 棵，在训练期滑窗向量上拟合，逐点分数 =
    平均 -decision_function（因果窗口）。
- 窗口长 L = clip(⌊n_train/10⌋, 16, 64)；训练样本每 epoch 至多 1500 个
  （确定性子采样），Adam lr=1e-3，epoch≤25，早停 patience=4（验证 NLL）。
- 每点分数使用**因果窗**（窗口终止于该点）——测试分不用任何未来/整体信息。

### 1.4 似然校准（仅训练期）
- 在**验证子集**上做小网格搜索，超参为长窗 W ∈ {max(10,·), …, 80}、
  短窗 W′ ∈ {1, 3}、阈值 θ ∈ {2.5, 3.0, 3.5, 4.0}，选择使"验证期 mini-NAB"
  最高的配置；验证期无异常窗口时退化为"少检测 + 更大 W"的节俭准则。
- 检测分数流：`z_t = (EMA_short(W′) − rolling_mean(W)) / rolling_std(W)`，
  因果计算；测试期检测 = 测试分数流 `z_t > θ`。
- **测试期任何统计量/标签均未进入训练、验证或校准**；测试标签只在最终评分
  稳定之后用来计算 NAB 分（见 §1.5）。种子固定（base seed 0；每文件子种子 =
  crc32(file_path)），重跑逐字节一致（`evidence/reproducibility_check.txt`）。

### 1.5 NAB 归一化评分
- 实现自研但忠实于 Numenta NAB 语义的评分器（`code/nab_scorer.py`）：
  - 测试期 detections 与 ground-truth 窗口均映射到测试局部索引；
  - 相邻 ≤ max(1, ⌊len/50⌋) 步的检测聚为一次事件，取簇首；
  - **每个窗口只计最早一次检测为 TP**，并根据早晚加权
    （窗口内更早 => 加分；窗口前轻微提前 => 线性衰减）；
  - 其余检测为 **FP，按距离最近窗口的时间距离加权**（靠近窗口的 FP 视为
    提前探测而折扣，远离的 FP 全额罚）；
  - 无检测的窗口 = FN；窗口外未被检测的点 = TN；
  - 每子组 = `100·(ΣS_model − ΣS_null)/(ΣS_ideal − ΣS_null)`，其中
    S = 1.0·TP − 0.11·FP + 0.22·TN − 1.0·FN（标准 NAB profile，
    FP/FN 负向进入）。多文件子组的聚合方式：**子组内全部序列的原始分求和后
    再归一**（即 NAB 对一组文件的标准做法），在 evidence 中声明。
- Microsoft 的逐点 Label 先按"相邻 ≤2 步的标记点合并为一个异常窗口"，
  窗口再与测试期求交。

## 2. 结果

### 2.1 冻结数据事实（B 维度 self-check）
`evidence/data_facts.txt`：NAB 58 序列 / 7 子组；Microsoft 60 序列 / 9 域；
总行数 225,445；Label=1 4,555；combined_windows.json 58 条目；180/180 哈希一致。
与 TASK.md 锚值**完全一致**。

### 2.2 claim (a) — Microsoft 各子组 × 模型 NAB 分（种子 0）

| 子组（域） | GRU | TCN | Transformer | TSMixer | IF |
|---|---|---|---|---|---|
| application-crash-rate-1 | **30.74** | 30.44 | 21.36 | 20.87 | 26.48 |
| application-crash-rate-2 | **56.82** | 47.67 | 60.30 | 53.09 | 47.54 |
| consumer-purchase-rate | **84.43** | 53.87 | −24.88 | 42.01 | 17.12 |
| data-ingress-rate | −126.8 | −101.8 | −109.8 | −95.5 | −22.3 |
| ecommerce-api-incoming-rps | 31.87 | 14.39 | 34.96 | 15.20 | 35.19 |
| middle-tier-api-dependency-latency | 34.39 | 54.11 | 60.05 | 50.52 | 65.99 |
| mongodb-application-rps | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mongodb-machine-rps | **26.10** | 15.56 | 4.36 | 4.41 | −1.16 |
| service-unavailable | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

**判定**：GRU 在 5 个含异常子组全部 > 0（30.74 / 56.82 / 84.43 / 31.87 /
26.10）。但 **TCN 与 TSMixer 同样全正**（mongodb-machine-rps 上分别 +15.56、
+4.41，Transformer +4.36 亦接近 0 界），因此 *GRU 唯一全正*在本复现协议下
**未成立**。两个附加种子（seed 7、更严 θ∈{3.5,…,5.0}）均确认：GRU 全正
稳健，且至少 TSMixer 在两种变体下仍全正 → 结论对校准/种子不敏感。
→ **claim (a) 判定：`partially_supported`**（支持"GRU 全正"，不支持"唯一"）。

### 2.3 claim (b) — NAB 各子组 × 模型 NAB 分（种子 0）

| 子组 | GRU | TCN | Transformer | TSMixer | IF | 最高分归属 |
|---|---|---|---|---|---|---|
| artificialWithAnomaly | −12.57 | −0.52 | **36.92** | −3.14 | 16.95 | Transformer |
| realAdExchange | 60.96 | 66.15 | **66.79** | 63.08 | 33.19 | Transformer |
| realAWSCloudwatch | 11.21 | −6.21 | −19.82 | 15.49 | **16.34** | IF |
| realKnownCause | 19.71 | **47.14** | 44.87 | 24.05 | 19.86 | TCN |
| realTraffic | 32.70 | 32.72 | 10.77 | 10.40 | **56.12** | IF |
| realTweets | −33.08 | −38.41 | −8.56 | −23.22 | **51.06** | IF |
| artificialNoAnomaly | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | — |

- 最高分归属 = {Transformer, IF, TCN} → **3 种架构**（种子 7 = {IF, TCN,
  GRU, Transformer} → 4 种）。两个种子下均 ≥3，**无单一架构主导**。
- 与论文对照：realKnownCause 论文最佳为 TSMixer（本复现 TCN）、realTraffic
  论文最佳为 GRU（本复现 IF，种子 7 下回归 GRU）；种子 7 中 GRU 拿到
  realAWSCloudwatch、realTraffic 两子组最高分（论文也正是 GRU）。
- NAB 分数对似然窗口/校准高度敏感（论文未开源结果存档）；判分以正负号与
  **归属/排序** 为主，属容差内。
→ **claim (b) 判定：`supported`**。

### 2.4 与论文 Table III 的快速对照（正负号/相对量级）
- Microsoft 5 含异常子组：本复现 GRU 全部 >0，方向一致；量级与论文同数量级
  （如 acr-1 GRU 30.7 vs 31.8；acr-2 56.8 vs 35.7；cpr 84.4 vs 48.2；
  ecom 31.9 vs 36.8；mm-rps 26.1 vs 18.0）。
- 非含异常子组：mongodb-application-rps、service-unavailable 全模型 0.00，
  与 Table III 完全一致。data-ingress-rate 本复现为负（FP 偏多），而论文为
  0.00 —— 反映校准敏感性差异，详述于 §4。
- NAB：artificialWithAnomaly 中论文仅 GRU 唯一正（11.06），本复现 Transformer
  与 IF 更敏（36.92 / 16.95）而 GRU 负 —— 属容忍范围内的归属差异，不改变
  "无主导架构"结论；realKnownCause 论文最佳 2.30（TSMixer），本复现最佳 47.14
  （TCN）——量级更高，方向（模型可检测）一致。
- 详见 `results/paper_comparison_table.csv`（30 个非零论文值中 26 个正负号一致）。

## 3. 防泄漏声明
1. 训练/早停/校准只使用训练期（含验证子集）数据与标签窗口。
2. 测试期分数使用冻结模型 + 因果平滑；测试标签仅用于最后评分中的窗口匹配。
3. 报告中的任何 NAB 分都由 `run_series.py` 从冻结 CSV 算出（固定种子）；
   `evidence/reproducibility_check.txt` 给出"重跑逐字节一致"的证据。
4. 无测试期统计量参与任何超参选择。文档透明，供复核。

## 4. 局限性与边界
- **NAB 分对似然窗口/阈值的敏感性**：θ∈[2.5,5] 网格 vs 更严 [3.5,5] 网格在
  mongodb-machine-rps 上几乎不变（TCN 15.6 / TSMixer 4.4），说明"贴零"边界的
  归属并不由 θ 严格性主导，而是模型重建质量差异；但 data-ingress /
  realTweets 等"FP 型"子组在两种网格下都保持负值。
- **种子敏感性**：单独的 per-subgroup 数值在 seed0/seed7 间有 ±10~20 分抖动
  （如 realAWSCloudwatch GRU 11 vs −3）；两个 claim 的方向性结论不变
  （`results/seed_sensitivity_table.csv`、`results/nab_best_attribution.csv`）。
- **论文数值不可直接对照**：论文未开源逐模型结果存档，且其 100 次贝叶斯校准
  与本文小网格不同；判分以正负号 + 归属为主。
- 未实现的细节：论文还可能使用 per-point 平滑核 / 更大模型容量 / 更长训练；
  Exathlon（合成注入）与 IBM（超高维）被排除（任务硬约束）。
- **GRU 唯一性未复现的诚实陈述**：论文锚值给出 mongodb-machine-rps 上
  TSMixer/Transformer/TCN = 0.00 而 GRU = 18.01；本复现在该子组上所有深度模型
  均为正（GRU 26.10 / TCN 15.56 / TSMixer 4.41 / Transformer 4.36），差异来自
  校准与重建能力的综合影响，无法用冻结数据+本协议进一步拉开。

## 5. 如何复现
```bash
cd code
python3 verify_data_facts.py            # 冻结数据事实
python3 run_series.py --datasets nab,microsoft --jobs 8 --seed 0
python3 analyze.py                      # claim 判定 + 图表
python3 run_series.py --datasets microsoft --seed 0 --th-grid 3.5,4.0,4.5,5.0 \
    --outdir ../results_strict         # （可选）严格阈值灵敏度
```
主要产物均位于 `results/`（`evidence_table.csv`、`metrics.json`、
`series_raw.csv`、`claim_summary.json`、图与对照表）。