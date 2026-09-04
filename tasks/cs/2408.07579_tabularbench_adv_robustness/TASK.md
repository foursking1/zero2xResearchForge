# 科研任务：TabularBench「ID 测试性能误导性」与「对抗训练有效性」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2408.07579_tabularbench_adv_robustness`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：TabularBench: Benchmarking Adversarial Robustness for Tabular Deep Learning in Real-world Use-cases（arXiv:2408.07579v1）
- 领域：CS / 表格深度学习 / 对抗鲁棒性

## 问题（可证伪）

TabularBench 在 URL 网络钓鱼检测数据集上报告（论文 Table 3）：

1. **论断 C1（测试性能误导性）**：标准训练下，5 种深度架构的 ID（干净测试）精度非常接近（92.5–94.4%），但在约束对抗攻击下的鲁棒精度差异巨大（8.9–58.0%）——即"ID 精度相近 ≠ 鲁棒性相近"。
2. **论断 C2（对抗训练有效性）**：对抗训练（AT）显著提升鲁棒精度（AT 后 56.2–91.8%），且干净精度基本保持（93.4–99.5%）——即"AT 以可忽略的干净精度代价换取大幅鲁棒提升"。

请基于冻结数据回答：
- (a) 在你训练的一组深度模型上，C1 的"ID 接近但鲁棒悬殊"模式是否成立？给出 clean/robust 精度的跨度对比。
- (b) 你的对抗训练模型相对标准训练模型的鲁棒精度提升多少？干净精度代价多大？C2 是否成立？
- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`（可对 C1/C2 分别给标签）。

## 数据说明

- 数据包：`data/`（冻结，来源见 `data/SOURCE.md`）
  - `url.csv`：URL 钓鱼检测真实数据（11,430 行；63 个数值特征 + 目标 `is_phishing`；正类率 50/50）
  - `url_metadata.csv`：特征元数据（type/mutable/min/max，min/max 为原始单位取值范围）
  - `source_manifest.json`：源 URL、许可、SHA-256（固定不可变）
- 来源：TabularBench 官方 HuggingFace 数据集仓库（serval-uni-lu/tabularbench，论文配套数据）；官方仓库 MIT License
- 许可：MIT（官方仓库）；底层数据源自 ISCX-URL2016 学术数据集

## 方向提示（协议建议，按此口径才能与论文锚对齐）

1. **数据划分（复刻官方 DefaultSplitter）**：`train_test_split(random_state=42, shuffle=True, stratify=y, test_size=0.2)` 两次（第一次分出 test 20%，第二次从 train 分出 val 20%）→ train 7,315 / val 1,829 / test 2,286。
2. **标准化**：按特征 **min-max 缩放到 [0,1]**，缩放统计量（每特征 min/max）**只用 train 划分**拟合，clip 到 [0,1]（论文 API 用 TabScaler min_max，见论文 §3.4）。
3. **模型族（至少 4 个，推荐如下）**：MLP 隐藏层宽度 [64]、[128,64]、[256,128,64]、[128,64]+dropout(0.3)；ReLU 激活，输出单 logit。
4. **训练协议**：Adam（lr=1e-3, weight_decay=1e-4），batch 256，12 epochs，BCE loss，固定随机种子（如 0）并写入代码。
   - 标准训练（standard）
   - 对抗训练（AT）：FGSM 单步（ε=0.1，L2 投影步长 α=0.1），对 batch 内样本生成对抗样本后更新（即 FGSM-AT）。
5. **评估攻击（约束 PGD-L2）**：对测试集全部样本做无目标攻击（最大化 BCE loss）：40 步；L2 预算 ε=0.25；步长 α=ε/4；每步沿梯度方向走步后**投影回以原样本为中心的 L2 球**，再 **clip 到 [0,1]**（对应特征域边界）。
   - 注：论文默认攻击为 CAA（更强），ε=0.5；本任务用 PGD-L2 ε=0.25 作为可比口径（论文 Figure 4/5 显示攻击预算曲线；PGD 在 ε=0.25 下的破坏力与论文 CAA 在 ε=0.5 下量级相当——报告中说明此口径差异）。
6. **指标**：clean accuracy（测试集干净精度）与 robust accuracy（测试集在 PGD 攻击下的精度），百分比。每个模型×每种训练各报一组。

## 输出要求（提交物）

1. **`claim.md`**：C1/C2 的判定（四档标签）、失败条件、数据支持强度、关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从 `data/url.csv` 读取并重算全部指标（含训练、AT、PGD 评估）。
3. **`results/evidence_table.csv`**：至少含列 `model,training,clean_acc,robust_acc`（每模型×每训练方式一行）。
4. **`results/metrics.json`**：test 样本数；各模型 clean/robust；std 与 AT 的 clean/robust 均值与跨度（max−min）；AT 相对 std 的平均鲁棒提升（pp）与平均干净精度变化（pp）；结论标签。
5. **`report.md`**：方法（划分/缩放/模型/AT/攻击实现细节）、结果、结论、局限（与论文口径差异：CAA vs PGD、模型族差异、ε 差异；容量-鲁棒性观察等）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代。
- 缩放统计量只能由 train 拟合；test 不得参与任何统计量估计（含 min/max、均值/标准差）。
- 攻击评估只允许使用已训练模型；禁止在测试集上训练或调参。
- 禁止手工抄写论文数字作为"实测结果"；所有指标必须运行代码得到。论文数值（Table 3）只能用于对照讨论。
