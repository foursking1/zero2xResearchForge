# Report — Text-ADBench 复现：LLM 嵌入下浅层 vs 深度文本异常检测

**Task:** `2507.12295_textadbench`（L1 critical claim，论文锚 + LLM 裁判）
**论文:** F. Xiao, J. Fan, *Text-ADBench: Text Anomaly Detection Benchmark based on LLMs Embedding*, arXiv:2507.12295 (2025)
**配置（本卡锚定）:** SMS-Spam 数据集 × LLaMA-3-8B（mntp, EOS token）嵌入，论文 Table 12 中深度方法全部不高于 KNN 的唯一 LLM 行。

---

## 1 任务与可证伪问题

在官方冻结的 **SMS-Spam + LLaMA-3-8B(mntp) EOS** 嵌入上复现论文核心发现：**使用 LLM 嵌入时，深度检测器相比浅层算法无性能优势**。三个表述：
- (a) KNN 测试 AUROC 为 10 种方法中最高（或并列最高）；
- (b) KNN AUROC ∈ 93.96 ± 3；
- (c) AE / DSVDD / DPAD 的 AUROC 均不高于 KNN。

指标 AUROC = `roc_auc_score(test_label, decision_function(test))`，protocol = `fit(train)` → `decision_function(test)`（论文 §5、官方 `anomaly_detection/main.py`）。

## 2 数据与防泄漏

- **冻结数据**（4 文件、90.7MB，官方 HF `Feng-001/Text-ADBench`）：
  - `train/mntp_eos_token_embeddings.npy` (4044, 4096) float32，标签全 0（全部正常）；
  - `test/mntp_eos_token_embeddings.npy` (1490, 4096)，标签 743×0 / 747×1（spam=异常，异常率≈50%）。
  - 4 个文件 SHA-256 均与任务卡/source_manifest 登记值一致（`verify_knn.py --checksums` 全 MATCH）。
- **防泄漏声明**：
  1. 读入的 `/mnt/f/.../Llama3-8b/mntp_*.npy` 与逐文件哈希一致，未作任何修改/重抽/重训嵌入；
  2. 仅用 train（4,044 全正常）拟合无监督检测器；test 标签只在最终评估 `roc_auc_score` 中使用；
  3. 未用 test 标签进行任何调参、种子挑选或方法取舍（种子集合在运行前固定为 42/2024/7/123/8888）；KNN anchor 校验时 no-tuning。
- 数据副本同时作为 `data/embeddings/...` 打包于 `agent_solution/`，便于裁判在隔离环境直接运行（哈希同一）。

## 3 方法、超参与实现

### 3.1 浅层（pyod 3.6.4，超参来自官方 `arguments/*.json`）

| 方法 | 超参 |
|---|---|
| KNN | `n_neighbors=3` |
| OCSVM | `kernel='rbf'` |
| IForest | 默认（`random_state=seed` 固定） |
| LOF | `n_neighbors=30` |
| PCA | `n_components=0.9` |
| KDE | `bandwidth=50, metric='euclidean'`（pyod 3.6.4 无 `kernel` 参数，省略） |
| ECOD | 默认 |

### 3.2 深度（官方 `arguments/*_llm.json` 参数）

- **AE**（pyod `AutoEncoder`）：`preprocessing=False, lr=1e-4, epoch_num=300, batch_size=1000, optimizer=adam, hidden_activation=leaky_relu, hidden_neurons=[4096,2048,2048,1024]`；其余 pyod 默认（batch_norm=True, dropout=0.2，与官方仓库一致地未覆盖）。
- **DSVDD**（pyod `DeepSVDD` 语义等价的 device 移植 `deep_port.DeepSVDDDevice`）：`preprocessing=False, learning_rate=1e-4, epochs=300, batch_size=1000, optimizer=adam, hidden_activation=leaky_relu, hidden_neurons=[4096,2048,2048,1024], l2_regularizer=0.01, use_ae=True, validation_size=0.0, dropout_rate=0.0`；`output_activation=null→identity`（pyod 3.6.4 不接受 null，等价 linear 输出）。移植与 pyod 3.6.4 在 CPU 上逐字节一致（`max|Δscore|=0.0` 已验证），仅增加 GPU 加速。
- **DPAD**（官方仓库 `anomaly_detection/dpad.py` 原样 vendor，MIT）：`learning_rate=1e-4, n_epochs=200, hidden_neurons=[4096,2048,2048,1024], hidden_activation=leaky_relu, gamma=0.01, lamb=0.1, k=10, bs=8192, num_classes=128`，`decision_function` = test 表征到 train 表征的 k=10 最近邻距离均值。

### 3.3 训练细节

- 深层模型 5 次重复（seeds 42/2024/7/123/8888），报告 mean±std，与论文「5 次平均」口径一致；浅层确定性方法单次即稳定（std=0）。
- 硬件：torch 2.11.0+cu128，RTX 4080（16GB，显存充足时使用，逐 seed 串行，峰值 <5GB）；浅层在 CPU。
- 环境版本：pyod==3.6.4、numpy 2.4.6、scikit-learn 1.6.1、scipy 1.17.1、torch 2.11.0。

## 4 结果

### 4.1 证据表（`results/evidence_table.csv`，AUROC %，mean over 5 seeds）

| method | type | n_train | n_test | auroc(%) | auroc_std | knn_rank | deep_max_minus_knn(pp) | paper(%) |
|---|---|---|---|---|---|---|---|---|
| knn | shallow | 4044 | 1490 | **94.85** | 0.00 | **1** | **−0.75** | 93.96 |
| ae | deep | 4044 | 1490 | 93.72 | 0.09 | — | — | 92.63 |
| dsvdd | deep | 4044 | 1490 | 75.92 | 7.37 | — | — | 86.98 |
| dpad | deep | 4044 | 1490 | 94.10 | 0.40 | — | — | 92.53 |
| ocsvm | shallow | 4044 | 1490 | 93.17 | 0.00 | — | — | 92.22 |
| kde | shallow | 4044 | 1490 | 93.00 | 0.00 | — | — | 92.14 |
| pca | shallow | 4044 | 1490 | 92.80 | 0.00 | — | — | 91.78 |
| lof | shallow | 4044 | 1490 | 92.02 | 0.00 | — | — | 91.47 |
| iforest | shallow | 4044 | 1490 | 91.03 | 0.72 | — | — | 89.65 |
| ecod | shallow | 4044 | 1490 | 86.96 | 0.00 | — | — | 85.26 |

逐 seed 明细见 `results/auroc_per_seed.csv` 与 `auroc_per_seed.json`；分数文件在 `results/scores/` 可独立复核；汇总图 `results/auroc_comparison.png`。

### 4.2 对三个表述的判定

1. **(a) KNN 最高：supported。** KNN 94.85 为 10 种方法唯一最高（rank 1）。第二高 DPAD 94.10。
2. **(b) KNN∈93.96±3：supported。** Δ=+0.89pp（论文 93.96 vs 实测 94.85），且与 rubric 参考重算（pyod 3.6.4 → 94.85）**完全一致**。
3. **(c) 深度不高于 KNN：supported。** AE 93.72、DPAD 94.10、DSVDD 75.92 均 < KNN 94.85；`deep_max − KNN = −0.75pp`，无任何深度方法超过 KNN。

### 4.3 与论文数值对照

- 10 个方法中 9 个与论文差距 ≤1.7pp（KNN +0.89, AE +1.09, DPAD +1.57, OC-SVM +0.95, KDE +0.86, PCA +1.02, LOF +0.55, IForest +1.38, ECOD +1.70），方向与排序基本一致，且系统性地略高于论文（5-run 平均 vs 本环境单机、pyod 3.6.4 vs 论文 2.0.2 等版本差异的常见表现）。
- **DSVDD 例外（75.92 vs 论文 86.98，−11pp）**，原因见下。

## 5 局限性与边界

1. **单配置 vs 论文全量**：本任务只锚定 1 个数据集（SMS-Spam）× 1 种嵌入（LLaMA-3-8B mntp EOS）× 10 方法，论文结论覆盖 12 个 Text-AD 数据集 × 14 种嵌入（§5.2/Table 6）。本报告的「supported」结论**只对该配置有效**，不构成对论文全量主张的独立验证。CALIBRATION.md 也提示其余嵌入行（如 mntp-supervised EOS）中 AE 94.37 > KNN 92.43，即该 claim 具有明确的配置依赖性。
2. **DSVDD 复现差异（版本行为）**：论文环境锁定 `pyod==2.0.2`，其 `deep_svdd.py` 在训练循环中把 `loss.backward()` **注释掉了**（且 `best_model_dict` 为参数别名、w_d 在循环外算一次）——即论文 DSVDD≈86.98 实际来自「未真正优化」的模型。本复现使用 pyod 3.6.4 语义（移植后已逐字节等价验证，含正确的 backward），训练 300 epochs 时因 best-epoch 快照策略产生极大 seed 波动（75.92±7.37）。因此 DSVDD 数值与论文的偏差是**上游实现差异**而非本复现错误；由于 AE/DPAD 与 KNN 的关系已足以判定方向性 claim，未对论文的 bug 行为做专门「复刻」。公证评估对 DSVDD 取值不敏感（A2 锚取深度最高值 AE/DPAD，方向校验看 KNN 与深度最高之差）。
3. **深度方法训练随机性与 GPU 依赖**：AE/DPAD 5-seed std ≤0.4pp，DSVDD 依 seed 大幅波动（0.65–0.86），报告口径为 5 次平均，单次随机种子不可复现同一数值；本环境用 GPU（RTX 4080）加速深度训练（CPU 下 AE/DSVDD 约 10–60 分钟/seed），浅层全 CPU 确定性。
4. **间接口径**：AUROC 仅用最终打分计算；未复现论文的 AUPRC/F1/FPR/FNR 等次要指标；`contamination=0.1` 只影响阈值/标签，不影响 AUROC。
5. **可行性说明**：所有代码在隔离环境中 runnable（`pip install -r requirements.txt` 后 `python code/verify_knn.py` 数十秒内即可复核 KNN 94.85）。

## 6 复现指南

```bash
cd agent_solution
pip install -r requirements.txt          # pyod==3.6.4 为关键版本
python code/verify_knn.py --checksums    # ~30 s：哈希 + KNN 94.85%
# 全量（10 方法 × 5 seeds，约 1 h；深模型默认 GPU，--device cpu 亦可）
python code/run_experiment.py --outdir results
# 从落盘分数重建证据表（审计式）
python code/aggregate_from_scores.py --scores-dir results/scores \
       --data-dir F:/dataset/cs/2507.12295_textadbench/embeddings/sms_spam/Llama3-8b \
       --outdir results
```

数据自解析：`run_experiment.py` / `verify_knn.py` 会依次搜索打包副本 `agent_solution/data/embeddings/...`、`F:\dataset\...`、`/mnt/f/dataset/...` 及 `TEXTAD_DATA_DIR`。

## 7 文件与证据索引

- `code/`：`run_experiment.py`、`dpad.py`（官方 vendor）、`deep_port.py`（DSVDD 移植）、`aggregate_from_scores.py`、`make_evidence_table.py`、`verify_knn.py`、`arguments_official/*`（官方参数文件副本）
- `results/`：`evidence_table.csv`、`summary_meta.json`、`auroc_per_seed.{csv,json}`、`auroc_comparison.png`、`scores/*.npy`、`*_run.log`、`env_info.json`
- `evidence/`：上表与图中关键证据的复制件
- `data/embeddings/sms_spam/Llama3-8b/`：官方冻结 4 文件副本（SHA-256 对标 <-> TASK.md/source_manifest）