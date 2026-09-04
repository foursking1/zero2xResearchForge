#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量 agent 评测：并发 + 续跑 + CSV 追加输出。
设计在 WSL 内运行（路径用 /mnt/d/...），复用 agent_eval_deepseek.run_card。

用法：
  python3 evaluation/agent_eval_full.py                # 全量（跳过 results/agent_scores.csv 已有卡）
  LIMIT=3 python3 evaluation/agent_eval_full.py        # 仅试跑前 3 张（用于验证）
环境变量：
  WORKERS  并发数（默认 6）
  LIMIT    仅评测前 N 张（默认 0=不限）
"""
import csv, os, sys, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
# 仓库根：默认从本脚本位置推导（evaluation/ 的上一级），可用环境变量覆盖
ROOT = os.environ.get(
    "PAPER_BENCH_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VALID = os.path.join(ROOT, "cards.csv")          # 统一卡片清单（根目录）
OUT = os.path.join(ROOT, "results", "agent_scores.csv")
# 环境变量可控：并发数、轮次上限、卡基目录、卡清单文件
MAX_TURNS = int(os.environ.get("MAX_TURNS", "45") or 45)
BASE = os.environ.get("BASE", "tasks")
CARDS = os.environ.get("CARDS_CSV", VALID)
WORKERS = int(os.environ.get("WORKERS", "6") or 6)
LIMIT = int(os.environ.get("LIMIT", "0") or 0)
LOCK = threading.Lock()

sys.path.insert( 0, HERE)
from agent_eval_deepseek import run_card

CSV_FIELDS = ["card", "domain", "v7_total", "v7_conclusion",
              "A1", "A2", "A3", "B", "total", "conclusion", "reason", "model", "error"]


def scored_cards():
    """已完成 = CSV 中拥有有效 total（非空白）的卡；失败/空行不计，便于重跑失败卡。"""
    done = set()
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if (row.get("total") or "").strip():
                    done.add(row["card"])
    return done


def process(row):
    card = row["card_id"]
    domain = row["domain"]
    try:
        res = run_card(card, domain, max_turns=MAX_TURNS, base=BASE)
    except Exception as e:
        res = {"card": card, "domain": domain, "error": f"EXC:{e}"}
    ok = res.get("error") is None
    a1 = res.get("A1"); a2 = res.get("A2"); a3 = res.get("A3"); b = res.get("B")
    total = ""
    if ok and None not in (a1, a2, a3, b):
        total = (a1 or 0) + (a2 or 0) + (a3 or 0) + (b or 0)
    return {
        "card": card, "domain": domain,
        "v7_total": row.get("v7_total", ""),
        "v7_conclusion": row.get("v7_conclusion", ""),
        "A1": a1, "A2": a2, "A3": a3, "B": b, "total": total,
        "conclusion": res.get("conclusion"),
        "reason": (res.get("reason") or "")[:600],
        "model": res.get("model"),
        "error": res.get("error"),
    }


def main():
    rows = list(csv.DictReader(open(CARDS, encoding="utf-8")))
    done = scored_cards()
    todo = [r for r in rows if r["card"] not in done]
    if LIMIT:
        todo = todo[:LIMIT]
    print(f"[main] 卡清单={CARDS} 总 {len(rows)} 张，已成功 {len(done)}，"
          f"待评 {len(todo)} 张，并发 {WORKERS}，轮次上限 {MAX_TURNS}，base={BASE}",
          file=sys.stderr)
    if not todo:
        print("[main] 无需评测，已全部完成", file=sys.stderr)
        return
    write_header = not os.path.exists(OUT)
    with open(OUT, "a", encoding="utf-8", newline="") as fout:
        w = csv.DictWriter(fout, fieldnames=CSV_FIELDS)
        if write_header:
            w.writeheader()
        completed = 0
        failed = 0
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futures = {ex.submit(process, r): r for r in todo}
            for fut in as_completed(futures):
                r = futures[fut]
                try:
                    out = fut.result()
                except Exception as e:
                    out = {"card": r["card"], "domain": r["domain"],
                           "error": f"FUT_EXC:{e}"}
                with LOCK:
                    w.writerow(out)
                    fout.flush()
                    completed += 1
                    if out.get("error"):
                        failed += 1
                    el = int(time.time() - t0)
                    print(f"[progress] {completed}/{len(todo)} done "
                          f"(fail={failed}) elapsed={el}s last={out.get('card')} "
                          f"total={out.get('total')} err={out.get('error')}",
                          file=sys.stderr)
    print(f"[main] 全部完成：成功 {completed - failed}/{len(todo)}，失败 {failed}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
