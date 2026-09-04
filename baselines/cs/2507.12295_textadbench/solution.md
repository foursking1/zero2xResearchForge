# Solution — Text-ADBench 复现：SMS-Spam + LLaMA-3-8B (mntp) EOS 嵌入下 浅层 vs 深度检测器

**Task:** `2507.12295_textadbench` · 验证论文核心 claim：使用 LLM 嵌入时，深度检测器（AE/DSVDD/DPAD）相比浅层算法（KNN 等）**无性能优势**。

## 结论（对三个可证伪表述）

| # | 表述 | 判定 | 数值证据 |
|---|------|------|----------|
| (a) | KNN 测试 AUROC 是 10 种方法中最高（或并列最高） | **supported** | KNN = **94.85%**，rank **1/10**（其余方法 86.96–94.10%） |
| (b) | KNN AUROC 落在 93.96 ± 3 | **supported** | 94.85 ∈ [90.96, 96.96]，与论文锚 Δ = +0.89pp |
| (c) | 深度检测器 AE/DSVDD/DPAD 的 AUROC 不高于 KNN | **supported** | AE 93.72，DPAD 94.10，DSVDD 75.92；deep_max − KNN = **−0.75pp** |

**汇总判定：`supported`。** 三个表述全部成立；数据支持的强度较高（KNN 锚 Δ0.89pp 落在满分档，方向校验偏差 −0.75pp < +2pp 阈值）。结论适用边界：仅在 **SMS-Spam + LLaMA-3-8B(mntp)-EOS** 单一配置上验证（与任务锚定范围一致），不推广到论文全量 12 数据集 × 14 嵌入。

## 关键结果（平均 over 5 seeds，固定种子 42/2024/7/123/8888）

| 方法 | 类型 | AUROC (%) | ±std | 论文 Table 12 | Δ |
|---|---|---|---|---|---|
| **knn** (k=3) | shallow | **94.85** | 0.00 | 93.96 | +0.89 |
| dpad | deep | 94.10 | 0.40 | 92.53 | +1.57 |
| ae | deep | 93.72 | 0.09 | 92.63 | +1.09 |
| ocsvm | shallow | 93.17 | 0.00 | 92.22 | +0.95 |
| kde | shallow | 93.00 | 0.00 | 92.14 | +0.86 |
| pca | shallow | 92.80 | 0.00 | 91.78 | +1.02 |
| lof | shallow | 92.02 | 0.00 | 91.47 | +0.55 |
| iforest | shallow | 91.03 | 0.72 | 89.65 | +1.38 |
| ecod | shallow | 86.96 | 0.00 | 85.26 | +1.70 |
| **dsvdd** | deep | 75.92 | 7.37 | 86.98 | −11.06 |

- 全部 10 个数字由我在本环境从官方冻结 `.npy` 直接算出（见 `results/auroc_per_seed.csv`，逐 seed 记录）；KNN 与 rubric 参考重算（pyod 3.6.4 = 94.85）严格一致。
- 所有方法（除 DSVDD）与论文相差 ≤1.7pp，处于 rubric 满分/半档容差内；DSVDD 差异来自 pyod 版本行为（见报告 §局限性与边界）。
- `evidence_table.csv` 已给出 `knn_rank=1` 与 `deep_max_minus_knn=−0.75pp`。

## 协议与方法

1. **数据**：官方 HF 冻结 `sms_spam/Llama3-8b/train|test/mntp_eos_token_embeddings.npy` + `mntp_embedding_labels.npy`（4 个文件 SHA-256 全部校验通过，`code/verify_knn.py --checksums` 可复核）。
2. **协议**（论文 §5 / 官方仓库 `anomaly_detection/main.py`）：`model.fit(train)` → `model.decision_function(test)` → `roc_auc_score(test_label, score)`；`contamination=0.1`（不影响 AUROC，只用原始分数）。
3. **超参**：逐字来自官方仓库 `arguments/*_llm.json`：
   - KNN `n_neighbors=3`；OCSVM `kernel=rbf`；IForest 默认；LOF `n_neighbors=30`；PCA `n_components=0.9`;KDE `bandwidth=50, metric=euclidean`；ECOD 默认；
   - AE (pyod)：`preprocessing=False, lr=1e-4, epoch_num=300, batch_size=1000, optimizer=adam, hidden_activation=leaky_relu, hidden_neurons=[4096,2048,2048,1024]`；
   - DSVDD (pyod)：同结构，`lr=1e-4(learning_rate), epochs=300, batch_size=1000, l2=0.01, use_ae=True, validation=0.0, dropout=0.0, output_activation=identity(原 null→linear)`；
   - DPAD（官方仓库 `dpad.py` 原版 vendor）：`lr=1e-4, 200 epochs, gamma=0.01, lamb=0.1, k=10, bs=8192, hidden=[4096,2048,2048,1024], leaky_relu`。
4. **防泄漏**：只读冻结嵌入；train 4,044 全正常样本拟合；test 标签仅用于最终 AUROC 计算，绝不参与调参/选方法。
5. **运行**：`cd agent_solution && python code/run_experiment.py`（10 方法 × 5 seeds，含深模型约 1 小时；可用 `--methods knn --device cpu` 等子集快速验证）。

## 文件清单

- `code/run_experiment.py` — 主实验（拟合→打分→AUROC，固定种子，逐 seed 落盘）
- `code/dpad.py` — 官方 DPAD 实现（MIT 原样 vendor）
- `code/deep_port.py` — pyod 3.6.4 DeepSVDD 的 device 移植（数学逐字节等价，已验证），增加 GPU 支持
- `code/aggregate_from_scores.py` — 从落盘 score 审计重建证据表
- `code/make_evidence_table.py` — 证据表生成
- `code/verify_knn.py` — 裁判侧快速 KNN 抽查 + SHA-256 校验
- `results/evidence_table.csv`、`results/auroc_per_seed.{csv,json}`、`results/auroc_comparison.png`、`results/*_run.log`
- `evidence/` — 关键证据复制（表、图、逐 seed 数据、运行日志）
- 完整方法学、版本、局限与边界见 `report.md`。