FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

# 预构建数据（若镜像内无 data/eval_data.json 且挂载了仓库，可运行时再生成）
ENV PORT=8000 PAPER_BENCH_ROOT=/repo JUDGE_MODE=demo
EXPOSE 8000

# 挂载仓库: -v /path/to/paper-bench:/repo:ro -e PAPER_BENCH_ROOT=/repo
CMD ["sh", "-c", "if [ ! -f data/eval_data.json ] && [ -f \"$PAPER_BENCH_ROOT/cards.csv\" ]; then python build_data.py --root \"$PAPER_BENCH_ROOT\"; fi; exec gunicorn -w 2 -b 0.0.0.0:${PORT} app:app"]
