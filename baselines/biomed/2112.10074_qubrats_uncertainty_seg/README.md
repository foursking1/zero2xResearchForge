# 2112.10074 QU-BraTS 不确定性量化评分与分割排名解耦 — 可验证复现包

**结论**：`supported`（在冻结的 BraTS 2021 mini 10 例替代数据上与论文两大方向性论断一致）。

## 内容

| 路径 | 说明 |
|---|---|
| `claim.md` | 三问判定 + 四档结论标签 + 关键数字（提交物 1） |
| `report.md` | 完整报告：方法/结果/局限/结论（提交物 5） |
| `solution.md` | 方案概述 + 关键结果 + 复现说明 |
| `code/` | 全部分析代码（提交物 2），含 `code/README.md`、`code/verify.py`、`code/run_all.sh` |
| `results/` | `evidence_table.csv`（提交物 3）、`metrics.json`（提交物 4）、阈值表、曲线、图 |
| `evidence/` | 关键证据导出（略去 10 例原始体积与 checkpoint） |
| `models/` | 5 个训练好的 checkpoint（可重新生成） |
| `data_cache/` | 解析后的数据 + 患者级固定划分（可重新生成） |

## 复现

```bash
cd agent_solution
bash code/run_all.sh cuda:0        # 端到端（prepare → train → evaluate → aggregate → plots → verify）
# 或进阶（不重训、只复核数字）：
python3 code/verify.py            # 独立重算全部 AUC/score/均值并比对 evidence_table.csv
```

## 核心结论速览（3 测试患者均值）

- **分数实现（论文 Eq.1）**：`score = (AUC1 + (1−AUC2) + (1−AUC3))/3`；
  最优 `det_s2` WT：AUC1=0.8619, AUC2=0.1085, AUC3=0.1322, **score=0.8737**, DSC=0.7456。
- **过滤有效性**：`mcd_s0` WT 随 τ=100→25，DSC 0.80→0.95（单调升），FTP/FTN 仅 0→0.25。
- **排名解耦**：6 模型 × 3 实体均出现 score 排名 ≠ DSC 排名（WT 5/6、TC/ET 6/6 错位）。
- **分数是“不确定性信息量”**：同分割配随机 uncertainty，score −0.23~−0.29。