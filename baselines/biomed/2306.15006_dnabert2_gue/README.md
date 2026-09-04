# agent_solution — task 2306.15006_dnabert2_gue

验证 DNABERT-2（arXiv:2306.15006, ICLR 2024）关键论断：**基因组基础模型（BPE Transformer）在 GUE 序列分类上优于 k-mer 浅层模型，且启动子等任务性能与论文量级一致**。

## 提交物索引
| 文件 | 说明 |
|---|---|
| `claim.md` | **结论判定**（四档标签 + 关键数字）：`supported` |
| `solution.md` | 方法说明 + 结果表 + 复现命令（简明版） |
| `report.md` | 完整报告：方法 / 结果 / 与论文对照 / 局限 / 防泄漏 |
| `results/evidence_table.csv` | 判分证据表（`dataset,method,metric,value`） |
| `results/metrics.json` | 汇总 JSON：统计 / 各方法指标 / 差值 / 论文锚 / 判定 |
| `results/data_stats.json` | 冻结数据逐 split 统计 |
| `results/baseline_kmer.json` / `baseline_rf.json` | k-mer 浅层基线结果 |
| `results/finetune/*_full_metrics.json` | DNABERT-2-117M+LoRA 微调结果（实测） |
| `results/prmtprobe/*.json` | DNABERT-2 冻结特征探针结果（补充） |
| `results/models/<task>/best_lora_state.pt` | LoRA 最佳 checkpoint（用于精确复现） |
| `evidence/` | 冻结数据 SHA-256 校验、行数/标签核查、指标对比图 |
| `code/` | 全部可复现脚本（固定种子 42） |

## 一句结论
DNABERT-2-117M（LoRA r=16，2.66M 可训练参数）在冻结的 **4/4** 个 GUE 任务上优于 k-mer(4-mer)+LR 基线：EMP_H3 MCC 0.7620 vs 0.4952、mouse_0 MCC 0.5237 vs 0.4520、prom_300_all F1 0.9312 vs 0.8699、prom_core_all F1 0.8331 vs 0.7894；启动子 F1 均 ≥ 论文家族参考（PD 84.63 / CPD 72.96），判定 **`supported`**。

## 快速复现
```bash
# 数据 → 基线 → 微调 → 探针 → 汇总（见 solution.md §6 的完整命令）
python3 code/aggregate_results.py            # 重生成 evidence_table.csv / metrics.json
python3 code/eval_checkpoint.py --dataset prom_300_all --device cpu   # 用保存的 checkpoint 精确复算测试集指标
```

- **精确复现（20 s~数 min）**：`eval_checkpoint.py` 从 `results/models/<task>/best_lora_state.pt` 恢复 LoRA 最佳 checkpoint 并在冻结 test 上重算，结果与 `evidence_table.csv` 完全一致（prom_300_all F1=0.9312 已验证）。
- **从头复现（有 GPU，~2.5 h）**：`code/run_finetune_dnabert2.py`，见 driver`code/driver_findatune.sh`；固定种子 42，逐任务早停。
- **CPU 从头复现（~1-2 h）**：同脚本加 `--max_train`（如 `--max_train 8000 --epochs 4`），F1 与全量结果差 <0.02（见 report.md 灵敏度小节）。

环境：Python 3.12，torch>=2.6，transformers 4.45.x，peft>=0.14，scikit-learn>=1.6，matplotlib（图）。模型权重为预训练公共权重（非数据），评估仅使用冻结数据。