# 科研任务：LLM 嵌入下文本异常检测 浅层 vs 深度方法（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id: `2507.12295_textadbench`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Text-ADBench: Text Anomaly Detection Benchmark based on LLMs Embedding（arXiv:2507.12295）
- 领域：CS / 文本异常检测 / LLM 嵌入 / 基准测试

## 问题（可证伪）

在论文发布的 Text-ADBench 基准（官方 HuggingFace 冻结数据）的 **SMS-Spam + LLaMA-3-8B(mntp) EOS 嵌入** 配置上，验证论文的核心发现之一：

**深度检测器无优势 claim**：使用 LLM 嵌入时，深度检测器（AE、DSVDD、DPAD）相比传统浅层算法（KNN、IForest、OCSVM 等）**没有性能优势**。论文报告（Table 12，LLaMA-3 (mntp) EOS 行，AUROC%）：**KNN = 93.96 为该行 10 种方法最高**，AE = 92.63、DPAD = 92.53、DSVDD = 86.98，均不高于 KNN。

可证伪表述：基于冻结数据，(a) "KNN 的测试 AUROC 是 10 种方法中最高（或并列最高）" 是否成立；(b) "KNN AUROC 落在 93.96 ± 3" 是否成立；(c) "深度检测器 AE/DSVDD/DPAD 的 AUROC 不高于 KNN" 是否成立。

## 方向提示（非方法步骤）

- 指标：AUROC（测试集，越高越好），论文主指标（§4.3 Evaluation）；计算方式 = `roc_auc_score(test_label, anomaly_score)`。
- 协议：用 train 嵌入（4,044 条，全为正常样本）拟合无监督检测器，对 test 嵌入（1,490 条，743 正常 + 747 异常）输出异常分数，与 test 标签比较（论文 §5 / 官方仓库 `anomaly_detection/main.py`：`model.fit(train_data)` → `model.decision_function(test_data)`）。
- 方法：KNN（`n_neighbors=3`，pyod）；AE / DSVDD（pyod，`hidden_neurons=[4096,2048,2048,1024]`、lr=1e-4、epochs=300、batch_size=1000、preprocessing=False）；DPAD（官方仓库 `anomaly_detection/dpad.py`，lr=1e-4、200 epochs、gamma=0.01、lamb=0.1、k=10）；contamination=0.1（不影响 AUROC）。官方参数见仓库 `arguments/*_llm.json`。
- 可选补充方法（浅层对照）：IForest、OCSVM、LOF、PCA、KDE、ECOD（pyod 默认即可）。
- 防泄漏：嵌入与标签为论文官方冻结产物；不得重新抽取/重训嵌入，不得用 test 标签调参。

## 数据说明

- 数据包：`$PAPER_BENCH_DATA_DIR/embeddings/sms_spam/Llama3-8b`（4 个 .npy 文件，共约 90.7MB，官方 HF 冻结）
  - `train/mntp_eos_token_embeddings.npy`：float32 (4044, 4096)——LLaMA-3-8B mntp EOS 训练嵌入
  - `train/mntp_embedding_labels.npy`：4,044 个标签（全 0 = 正常）
  - `test/mntp_eos_token_embeddings.npy`：float32 (1490, 4096)——测试嵌入
  - `test/mntp_embedding_labels.npy`：1,490 个标签（743×0 正常 / 747×1 异常，spam=异常）
- 来源：HuggingFace `Feng-001/Text-ADBench`（论文官方发布；text-embeddings/sms_spam-text-embeddings.zip 内 `sms_spam/Llama3-8b/train|test/mntp_eos_token_embeddings.npy` 及 `mntp_embedding_labels.npy`）。
- 代码：官方仓库 https://github.com/jicongfan/Text-Anomaly-Detection-Benchmark （MIT 许可）。
- checksum（sha256）：
  - `train/mntp_eos_token_embeddings.npy` = `7A746410CD7A35C3029A9D0B753751DD1920A0385364CB698E2F59CCF888C19E`
  - `train/mntp_embedding_labels.npy` = `4946B0ABDC4F88B200F2D5BFC7B57D9500CDB79E644DB9F7B30852A9EE993502`
  - `test/mntp_eos_token_embeddings.npy` = `854FBA8CBCF3DBBDD08898FD5DACEAB1393D50A596286EC9F3973FEF9AED7282`
  - `test/mntp_embedding_labels.npy` = `BE40D255B5046F738F7F7F12F74FE81884B7CB681B8C6A314062FDA831BD8C55`
- 逐文件 SHA-256 登记：`$PAPER_BENCH_DATA_ROOT/checksums.sha256`。

## 输出要求（提交物）

1. **结论**：对上述三个 claim 分别给出 `supported / partially_supported / contradicted / inconclusive`，并说明数据支持的强度。
2. **证据表**：`results/evidence_table.csv`（或等价表格），至少含列：`method`（knn / ae / dsvdd / dpad / iforest / ocsvm 等）、`n_train`、`n_test`、`auroc`（%）；另报告 `knn_rank`（KNN 在报告方法中的 AUROC 排名）与 `deep_max_minus_knn`。
3. **代码**：完整可复现的检测/评估脚本（含固定随机种子），从冻结 .npy 读取数据。
4. **报告**：`report.md`：方法（模型与超参、pyod/仓库版本）、防泄漏说明、局限性（单一嵌入-数据集配置 vs 论文 12 数据集全量、GPU 依赖）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代。
- 禁止用 test 标签进行任何调参/选择；嵌入文件为官方冻结产物，不得修改。
- 报告中必须说明与论文全量实验（14 个 Text-AD 数据集 × 14 种嵌入）的差异。
