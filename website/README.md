# zero2x ResearchForge · Benchmark Arena

科研复现评测网站（可部署）：**题目库 → 基线复现结果与打分 → 提交并打分**。

- 前端：单页（原生 HTML/CSS/JS，无构建步骤），数据由服务端注入 + REST API
- 后端：Flask（页面 + 只读 API + 提交/评分队列）
- 裁判：与仓库评测链**同一套代码**（`evaluation/judge_eval105.py` + `evaluation/JUDGE_PROMPT_v7.md` + `judge_v7_full.enforce` 钳制），默认 qwen3.7-max、temperature=0

## 功能

| 页签 | 内容 |
|---|---|
| 概览 | 全量口径 KPI（主集 125 + 地热独立子集 12 = 137）、领域×难度热力矩阵、分数直方图、结论分布、双裁判对比 |
| 题目库 | 125 张任务卡搜索/筛选；详情含关键主张、冻结数据规模、评分协议、v7 分解、agent 裁判评语、TASK.md 原文 |
| 基线结果 | 难度校准散点（目标区间 vs 实际分）、全字段可排序明细表、CSV 导出 |
| 提交打分 | 上传 solution ZIP（或粘贴报告文本）→ 异步评测流水线（5 阶段）→ 真实/模拟评分卡 + enforce 提示 + 最近提交列表 |

## 本地运行

```bash
cd website
pip install -r requirements.txt
python build_data.py        # 聚合仓库数据 -> data/eval_data.json（默认仓库根 = 上级目录）
python app.py               # 打开 http://127.0.0.1:5000
```

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `PAPER_BENCH_ROOT` | 上级目录 | paper-bench 仓库根（读 cards.csv / results/ / tasks/） |
| `PORT` | 5000 | 监听端口 |
| `JUDGE_MODE` | `demo` | `demo` = 模拟评分（联调演示）；`llm` = 真实 LLM 裁判 |
| `JUDGE_API_KEY` | — | llm 模式必需的 API key |
| `JUDGE_API_URL` | agtcloud chat-completions URL | 可选的 OpenAI-compatible chat-completions endpoint |
| `JUDGE_MODEL` | `qwen3.7-max` | 可选的裁判模型名 |

**llm 模式**：`JUDGE_MODE=llm JUDGE_API_KEY=sk-xxx JUDGE_MODEL=<model> python app.py`
提交物建议包含 `claim.md` / `metrics.json` / `report.md` / `evidence_table.csv` / 代码 —— 与 `baselines/<domain>/<card>/` 的交付结构一致，裁判按 v7 协议输出 A1/A2/A3/B + conclusion，并经 `enforce()` 代码级钳制（锚表不全 → A2≤12/总分≤70；contradicted → ≤50）。

## Docker 部署

```bash
docker build -t paperbench-arena ./website
# demo 模式（无仓库数据挂载时需先构建好 data/eval_data.json 打进镜像）
docker run -p 8000:8000 paperbench-arena
# llm 模式 + 挂载仓库数据
docker run -p 8000:8000 \
  -v /path/to/paper-bench:/repo:ro \
  -e PAPER_BENCH_ROOT=/repo \
  -e JUDGE_MODE=llm -e JUDGE_API_KEY=sk-xxx \
  paperbench-arena
```

## 裸机 / 云服务器部署

```bash
pip install -r requirements.txt
python build_data.py --root /path/to/paper-bench
JUDGE_MODE=llm JUDGE_API_KEY=sk-xxx PORT=8000 \
  gunicorn -w 2 -b 0.0.0.0:8000 app:app    # 建议 gunicorn；评分线程在 worker 内异步执行
```

## 目录结构

```
website/
  app.py               # Flask 入口：页面注入 + /api/*
  judge_service.py     # 评分服务（demo / llm，复用仓库评测链 + enforce）
  build_data.py        # 数据聚合：cards/l1l2/v7/agent/TASK.md -> data/eval_data.json
  templates/index.html # 单页前端（服务端注入数据）
  data/eval_data.json  # 构建产物
  submissions/         # 运行时提交与评分结果（每提交一个 UUID 目录）
  requirements.txt / Dockerfile / .dockerignore
```

## 安全边界（与老设计一致）

私有裁判材料（`PAPER_ANCHOR.md` / `SCORE_RUBRIC.md` / `CALIBRATION.md` / `truth/`）**永不下发浏览器**——API 不提供这些文件，仅裁判进程在服务端读取。
