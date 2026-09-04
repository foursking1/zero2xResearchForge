#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成统一卡片清单 cards.csv（仓库根目录）。

规则：扫描 tasks/<domain>/<card>，纳入每张具有 TASK.md 的任务卡，
并关联 l1l2_labels.csv 的难度等级。
legacy 已合并进 tasks/<domain>/<card>，无独立目录。

输出：cards.csv (card_id, domain, level)
"""
import csv
import os

ROOT = os.environ.get(
    "PAPER_BENCH_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TASKS = os.path.join(ROOT, "tasks")
L1L2 = os.path.join(ROOT, "l1l2_labels.csv")
OUT = os.path.join(ROOT, "cards.csv")


def load_levels():
    d = {}
    if os.path.exists(L1L2):
        with open(L1L2, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                d[(row["domain"].strip(), row["card"].strip())] = row["level"].strip()
    return d


def main():
    levels = load_levels()
    rows = []
    for dom in sorted(os.listdir(TASKS)):
        dd = os.path.join(TASKS, dom)
        if not os.path.isdir(dd):
            continue
        for card in sorted(os.listdir(dd)):
            cp = os.path.join(dd, card)
            if not os.path.isdir(cp):
                continue
            if not os.path.isfile(os.path.join(cp, "TASK.md")):
                continue
            rows.append((card, dom, levels.get((dom, card), "")))
    rows.sort(key=lambda r: (r[1], r[0]))
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["card_id", "domain", "level"])
        for card, dom, lv in rows:
            w.writerow([card, dom, lv])
    print(f"写出 {OUT}: {len(rows)} 张可评测卡")
    from collections import Counter
    print("  域分布:", dict(Counter(d for _, d, _ in rows)))


if __name__ == "__main__":
    main()
