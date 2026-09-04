# 科研任务：Wild-Tab 表格 OOD 泛化（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id: `2312.01792_wildtab`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Wild-Tab: A Benchmark For Out-Of-Distribution Generalization In Tabular Regression（arXiv:2312.01792）
- 领域：CS / 表格机器学习 / OOD 泛化

## 问题（可证伪）

在 Wild-Tab 使用的真实表格回归数据（Shifts Weather Prediction 的公开规范划分，即论文中的 "Weather" 数据集）上，验证论文的两个核心结论：

1. **泛化差距 claim**：用经验风险最小化（ERM）训练的回归模型，其分布外（OOD）测试 MAE 显著高于分布内（ID）测试 MAE。论文报告：ID 1.353 °C → OOD 1.741 °C，相对差距 28.6%。
2. **ERM 竞争力 claim**：简单 ERM 的 OOD 性能与专门设计的 OOD 泛化方法相当（论文：Weather OOD 测试 MAE 各方法落在 1.734–1.77 °C 区间，ERM 1.741 不处显著劣势）。

可证伪表述：基于冻结数据，(a) "OOD 相对 ID 显著退化（≥20%）" 是否成立；(b) "简单 ERM 不显著差于专门 OOD 方法" 是否成立。

## 方向提示（非方法步骤）

- 指标：MAE（°C），越低越好（论文主指标，§3.4 Evaluation Metrics）。
- 划分：数据包已按时间与气候划分为 train / dev_in / dev_out / eval_in / eval_out；in = 分布内，out = 分布外（气候 + 时间迁移，Shifts hybrid 协议，论文 §2.2 / Figure 1）。只用 train 训练。
- 模型：从 ERM 角度出发，带正则化的 MLP 即可；用 dev（尤其是 out-domain 部分）做模型选择。
- 防泄漏：特征标准化/归一化统计量只能由 train 拟合；eval_in / eval_out 不得参与任何选择、早停或调参。

## 数据说明

- 数据包：`data/`（冻结子集，来源见下）
  - `train.csv`：100,000 行（对官方 canonical train 3,129,592 行按种子 20260812 均匀子采样）
  - `dev_in.csv` / `dev_out.csv`：各 20,000 行（官方 50,000 行子采样）
  - `eval_in.csv` / `eval_out.csv`：各 60,000 行（官方 561,105 / 576,626 行子采样）
  - `source_manifest.json`：源 URL、许可、种子、各文件 sha256（权威 checksum 记录）
- schema：每行 = 一个观测，共 129 列；目标列 = `fact_temperature`（2 米气温，°C）；推荐输入特征 = 第 7 列起（`sun_elevation` 等 123 个数值天气特征，跳过前 6 列元数据，与 Shifts 官方 tutorial `df.iloc[:, 6:]` 一致）。
- 来源：Shifts Weather Prediction 数据集规范划分（Wild-Tab 论文 §3.1 与附录 A 使用的同一公开 canonical partition）
  - 官方下载：https://storage.yandexcloud.net/yandex-research/shifts/weather/canonical-partitioned-dataset.tar
  - 官方仓库：https://github.com/Shifts-Project/shifts （weather/ 目录）
- 许可：CC BY NC SA 4.0（Shifts 数据集官方许可；署名、非商业、相同方式共享；源 tar 内 LICENSE.md）
- checksum（sha256）：
  - train.csv: 8706cf4521a6fac16cb585b2f937632e2a89c2c7bb050e7aab5eb33f4a980d2b
  - dev_in.csv: 8be19393ca7301a78874b0ff498e24c62e51dd5a69906561f44f82127961c084
  - dev_out.csv: 09e8ca3f3a759381b7a146fc56e32564af4b0fa07364e9950ae83cb70faf556f
  - eval_in.csv: cc997881c2952a7a28687281f1bbc6ddd55341c541280fd09c1cd0962c1b67d1
  - eval_out.csv: fc1a297cc3990814266f9a5f6122a51c9786ee42288c8e95f8950dd56ae68c06

## 输出要求（提交物）

1. **结论**：对上述两个 claim 分别给出 `supported / partially_supported / contradicted / inconclusive`，并说明数据支持的强度。
2. **证据表**：`results/evidence_table.csv`（或等价表格），至少含列：`split`（eval_in / eval_out）、`n`、`mae`、`target_mean`、`target_std`；另报告 ID→OOD 相对差距 `gap_pct`。
3. **代码**：完整可复现的训练/评估脚本（含固定随机种子），从 `data/` 读取冻结数据。
4. **报告**：`report.md`：方法（模型、预处理、超参）、防泄漏说明、局限性（冻结子集与论文全量的差异、种子敏感性）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代。
- eval_in / eval_out 只用于最终评估；禁止用于训练、验证、早停、调参或特征选择。
- 标准化统计量只能由 train 拟合；禁止使用全量统计（数据泄漏）。
- 报告中必须说明本冻结子集与论文全量实验（3.1M 训练样本）的差异。