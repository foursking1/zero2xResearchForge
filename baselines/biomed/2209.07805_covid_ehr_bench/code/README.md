# code/ — 可复现代码

端到端复现 TJH COVID-19 早期死亡预测基准（arXiv:2209.07805）。

## 运行

```bash
python -m pip install -r requirements.txt   # 一次性
python run_experiment.py                    # 全流程（CPU，约 40–60s）
```

数据自动定位：`../data/`（任务目录）→ 物理冻结路径。二次运行结果应与
`results/` 字节级一致（固定种子）。

## 脚本清单

| 文件 | 用途 |
|---|---|
| `common.py` | 数据加载、路径解析、患者分块、窗口/缺失率工具 |
| `preprocess.py` | 聚合特征（ML）与分箱时序+掩码（GRU），训练集拟合插补/缩放 |
| `models_ml.py` | LightGBM / RandomForest / 临床式 logistic 基线 |
| `models_seq.py` | GRU 与 GRU-TA（时间感知损失）序列模型 |
| `run_experiment.py` | 编排：装配统计→训练→评测→证据表/metrics/图 |
| `requirements.txt` | 依赖（版本见标注） |

## 输出产物

- `../results/evidence_table.csv`：`model,ta,auroc,auprc`（+pct 版本）
- `../results/metrics.json`：数据统计、各模型 AUROC/AUPRC、论文锚、TA 对比、结论标签
- `../results/predictions.csv`：各模型逐患者得分
- `../results/window_sensitivity.csv`、`feature_importance_top25.csv`
- `../evidence/figures/`：ROC/PR 曲线、特征重要性图

## 防泄漏要点

- 插补均值/中位数、StandardScaler、GRU 通道标准化统计量：仅训练集拟合
- GRU 验证集：训练集内 20%（按患者），与测试集无关
- 随机种子固定（ML=42；GRU seeds=0–4）；测试集仅用于一次评分

## 口径说明

- 任务：入院后**前 72h** 测量预测院内死亡（`outcome`）；3 项共享特征
  （LDH、hsCRP、淋巴细胞%），因为冻结测试文件仅含这 3 项。
- 测试集：110 例（13 例死亡）。训练 375 例中 14 例为空占位行，剔除 → 361。