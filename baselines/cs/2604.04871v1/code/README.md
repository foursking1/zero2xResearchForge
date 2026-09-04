# code/ — 运行代码

本目录包含 TASK 声明（C01–C04）分析的全部可运行代码。

## 文件

- `analyze_claims.py` — 主分析脚本。对冻结数据 `F:\dataset\24_2604.04871v1`（论文 PDF、`statsclaw_repo/` 框架源码、`data/monte_carlo_results.csv`）执行：
  1. 论文文本提取（pdftotext）与短语对照；
  2. C01：代理清点 + 信息隔离正则审计（10 项禁止 + 3 项正向对照 + isolation 技能 7 条 + Leader 派发规则）；
  3. C02：代理文件计数、论文"eight"声明、附录 A1 对照、README 计数、单会话证据；
  4. C03：planner 三规范产出、独立自足、派发隔离规则；
  5. C04：状态链、中断态、前提条件表（18 行）解析；
  6. 补充：冻结蒙特卡洛 CSV 重算（覆盖率、失败率、RMSE 衰减、MH 接受率、耗时比）。

## 运行

```bash
cd <task_root>   # D:/project/paper-bench/tasks_legacy/2604.04871v1
python agent_solution/code/analyze_claims.py
```

输出写入 `agent_solution/results/`：
- `evidence_table.csv` — 证据表
- `metrics.json` — 机器可读指标
- `paper_text.txt` — 论文提取文本（可追溯性）

## 依赖

Python ≥ 3.9，`pandas`/`numpy`（补充数值部分）；系统 `pdftotext`（论文提取；若缺失则回退读取已有 `results/paper_text.txt`）。

## 复现说明

- 只读冻结数据，未复制大文件。
- 所有数值均由脚本本次运行产生；论文数值仅以"论文引用"形式标注于 `solution.md`，未直接采用。
