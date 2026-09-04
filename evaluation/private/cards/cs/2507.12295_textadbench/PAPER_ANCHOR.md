# PAPER_ANCHOR：论文核心结果锚（私有，禁止外泄到 TASK.md 之外的公开面）

论文：F. Xiao, J. Fan, Text-ADBench: Text Anomaly Detection Benchmark based on LLMs Embedding（arXiv:2507.12295，2025）。以下数值摘自论文 Table 12（SMS-SPAM 逐嵌入 AUROC）与 §5.2 观察，禁止臆造。

## 锚 A1 — SMS-Spam + LLaMA-3-8B(mntp) EOS 下 KNN 测试 AUROC
- 数值：**93.96%**
- 出处：Table 12（Average AUROC(%) on SMS-SPAM），LLaMA-3 (mntp) EOS 行、KNN 列；该行 10 种方法中的最大值（该行 Avg=90.86）。
- 定义口径：官方冻结嵌入（train 4,044 正常样本 → fit；test 1,490 → decision_function）；pyod KNN(n_neighbors=3, contamination=0.1)；AUROC = roc_auc_score(test_label, score)。
- 复现核对（2026-08-13，pyod 3.6.4）：KNN AUROC = 94.85（Δ=+0.89pp，在容差内）。
- 容差（判分用）：绝对差 ≤3pp 满分档；≤6pp 半档；≤10pp 低档（详见 SCORE_RUBRIC.md）。

## 锚 A2 — 深度检测器 AUROC（AE / DSVDD / DPAD，同一配置）
- 数值：**AE = 92.63、DPAD = 92.53、DSVDD = 86.98**
- 出处：Table 12 同一行（LLaMA-3 (mntp) EOS 列）。
- 定义口径：AE/DSVDD 用 pyod（hidden_neurons=[4096,2048,2048,1024]、lr=1e-4、epochs=300、batch_size=1000、preprocessing=False）；DPAD 用官方仓库自定义实现（lr=1e-4、200 epochs、gamma=0.01、lamb=0.1、k=10）；均为 5 次重复平均（论文 §5）。
- 容差（判分用）：以报告的最高深度方法 AUROC 相对锚（≈92.6）绝对差 ≤4pp 满分档；≤8pp 半档；≤12pp 低档。

## 锚 A3（方向性）— 深度方法无优势
- 数值：KNN（93.96）≥ AE（92.63）/ DPAD（92.53）> DSVDD（86.98），深度方法均不高于 KNN
- 出处：Table 12 同一行；正文 §5.2 "deep learning based detectors (AE, DSVDD, DPAD) exhibit no advantage over conventional shallow algorithms (OCSVM, IForest, LOF, KNN, KDE) when using LLM-derived embeddings"。
- 用途：方向性校验（若报告某深度方法显著高于 KNN，claim 需限定）。

## 锚 A4（辅助）— 全表一致性
- 同一嵌入行其他方法：OCSVM 92.22、IForest 89.65、LOF 91.47、PCA 91.78、KDE 92.14、ECOD 85.26（Table 12）。
- 论文总体发现（§5.2/Table 6）：跨 12 数据集取 best 嵌入时 KNN 平均 AUROC 90.71 最高；mean 嵌入时 KNN 77.74 亦最高。
- 用途：辅助判断 agent 结论；若 agent 声称"深度方法显著优于浅层"，需给出证据。

## 判分一致性提醒
- 锚 A1/A2 来自同一 Table 12 行，可交叉核对（KNN ≥ AE/DPAD 必须成立）；判分以 A1（KNN）与 A2（深度最高值）为主，A3 方向性校验。
- 论文数值为 5 次重复平均；深度方法有训练随机性，rubric 带宽已考虑。
