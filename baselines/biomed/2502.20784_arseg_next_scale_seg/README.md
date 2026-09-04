# agent_solution — 2502.20784 AR-Seg critical-claim verification

| file | content |
|---|---|
| `claim.md` | 三问判定：四档标签 `partially_supported` + 关键数字 |
| `solution.md` | 方法 + 结果速览 |
| `report.md` | 完整报告（协议/模型/结果/机制分析/局限） |
| `code/` | 全部可复现脚本（01–09 + `common.py`/`trainer.py`/`run_all.sh`），固定 seed 0 |
| `results/evidence_table.csv` | `model,dataset,metric,value`（44 行，含基线+AR 模型） |
| `results/metrics.json` | 样本统计、逐模型指标、论文锚对照、机制消融、结论 |
| `evidence/` | 共识聚合曲线、下尺度条件化消融、示例分割图 |

## 核心结果
- LIDC：基线 Soft-Dice **0.9594** → AR-Seg 风格 **0.9664**（同设置 +0.0070）。
- BraTS mini WT：基线 hard-Dice **78.14** → AR-Seg 风格 **78.98**（+0.84 pts）。
- 机制：简化 AR-Seg（多尺度掩码头 + coarse→fine 下尺度条件化 + MC-dropout 共识聚合）
  在双数据集上均 ≥ 同设置基线，方向与论文一致；绝对数值因冻结子集/2D/伪掩码而与
  论文（0.658 / 86.97）不可对标 → `partially_supported`。

## 复现
```bash
bash code/run_all.sh cuda   # 或 cpu（慢）；完整从头训练+分析 ~35-45 min (GPU)
# 快速校验（不动训练，直接用固定缓存 + 已存 checkpoint 重算两个抽查指标）：
ARSEG_DEVICE=cuda python3 code/09_verify.py
```
依赖：torch≥2.0, numpy, pandas, pyarrow, scipy, scikit-image, Pillow, nibabel, matplotlib。

## 数据
- LIDC：冻结 `data/` 上级仓库 F: 盘 `lidc_train.parquet`（SHA-256 `BDF49DA0…F45B`）。
- BraTS mini：已按任务说明复制至 `data/brats2021_mini.parquet`（SHA-256 `B95F221D…46F8`）。
- 脚本自动在本地 `data/` 与文档化物理位置之间解析路径。