#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据设计盘点脚本（只读诊断，不修改任何文件）。

对 tasks/<domain>/<card> 下每张卡分类（legacy 已合并进 tasks，无独立目录）：
  - 固化膨胀   : 卡自身数据体积过大（默认 >=500MB，数据被烤进仓库）
  - 路径可救   : 代码把数据写死在异机绝对路径(如 F:\\dataset / E:\\scisolvebench-data)，
                 但卡片本身自带可观数据(>=5MB) -> 改相对路径即可真跑
  - 数据缺失   : 代码写死异机绝对路径，但卡片极小(<5MB,只有代码+清单) -> 数据不在仓内
  - 自包含     : 无外部异机路径写死（仅有仓库自引用/相对路径）

判定规则：
  - 外部异机路径 = 绝对路径且不属于本仓库，且非本机噪声(.workbuddy/python.exe)
  - 卡片自带数据代理判据：size_MB >= 5 视为"数据在仓内"

输出：
  - 打印汇总表
  - 写 results/data_design_inventory.csv
"""
from __future__ import annotations

import csv
import os
import re
import sys

ROOT = os.environ.get(
    "PAPER_BENCH_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TASKS = os.path.join(ROOT, "tasks")
OUT_CSV = os.path.join(ROOT, "results", "data_design_inventory.csv")

BLOAT_MB = 500.0  # 超过此体积视为"固化膨胀"
CODE_EXT = (".py", ".sh", ".R", ".ipynb", ".md", ".txt", ".json", ".yaml", ".yml")

DRIVE_RE = re.compile(r"[A-Za-z]:\\[^\s\"'`]+")
POSIX_RE = re.compile(r"/(?:mnt|Users|home)/[^\s\"'`]+")


def classify_ref(ref: str) -> str:
    """把一条绝对路径归类为 noise / internal / external。"""
    r = re.sub(r"[/\\]+", "/", ref)  # 归一化反斜杠与多重斜杠
    low = r.lower()
    if ".workbuddy" in low or "python.exe" in low:
        return "noise"
    if "project/paper-bench" in low:
        return "internal"  # 本仓库自引用，不算外部
    # 异机/外部：其他盘符、/Users、/mnt、/home 等
    return "external"


def collect_files(card_dir: str):
    """返回 (全部相对文件列表, 外部异机路径集合, 内部自引用集合, 噪声集合)."""
    all_files = []
    external = set()
    internal = set()
    noise = set()
    for root, _dirs, files in os.walk(card_dir):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, card_dir).replace("\\", "/")
            all_files.append(rel)
            if f.lower().endswith(CODE_EXT):
                try:
                    with open(full, "r", encoding="utf-8", errors="ignore") as fh:
                        txt = fh.read()
                except Exception:
                    continue
                for m in DRIVE_RE.findall(txt):
                    c = classify_ref(m)
                    (noise if c == "noise" else
                     internal if c == "internal" else external).add(m.replace("\\", "/"))
                for m in POSIX_RE.findall(txt):
                    c = classify_ref(m)
                    (noise if c == "noise" else
                     internal if c == "internal" else external).add(m)
    return all_files, external, internal, noise


def card_size_mb(card_dir: str) -> float:
    total = 0
    for root, _d, files in os.walk(card_dir):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total / (1024.0 * 1024.0)


def has_manifest(card_dir: str) -> bool:
    for root, _d, files in os.walk(card_dir):
        for f in files:
            if f.upper() == "DATA_MANIFEST.md":
                return True
    return False


def main() -> int:
    if not os.path.isdir(TASKS):
        print(f"ERROR: {TASKS} 不存在", file=sys.stderr)
        return 1

    cards = []
    for dom in sorted(os.listdir(TASKS)):
        dd = os.path.join(TASKS, dom)
        if not os.path.isdir(dd):
            continue
        for c in sorted(os.listdir(dd)):
            cp = os.path.join(dd, c)
            if os.path.isdir(cp):
                cards.append((dom, c, cp))
    print(f"发现 {len(cards)} 张卡（tasks/<domain>/<card>），开始盘点...\n")

    rows = []
    for dom, card, cdir in cards:
        all_files, external, internal, noise = collect_files(cdir)
        size_mb = card_size_mb(cdir)
        manifest = has_manifest(cdir)
        has_external = len(external) > 0
        embedded = size_mb >= 5.0  # 卡片自带可观数据 -> 数据在仓内

        bloat = size_mb >= BLOAT_MB
        if bloat:
            category = "固化膨胀"
        elif has_external and embedded:
            category = "路径可救"
        elif has_external and not embedded:
            category = "数据缺失"
        else:
            category = "自包含"

        # 抽一个代表性外部路径做示例
        sample_ref = sorted(external)[0] if external else (
            sorted(internal)[0] if internal else "")

        rows.append({
            "card": card,
            "size_MB": round(size_mb, 1),
            "external_paths": len(external),
            "internal_self_paths": len(internal),
            "embedded_data": embedded,
            "has_DATA_MANIFEST": manifest,
            "category": category,
            "sample_ref": sample_ref,
        })

    # 排序：先按分类，再按体积
    cat_order = {"固化膨胀": 0, "数据缺失": 1, "路径可救": 2, "自包含": 3}
    rows.sort(key=lambda r: (cat_order.get(r["category"], 9), -r["size_MB"]))

    # 打印
    hdr = f"{'card':<22}{'size_MB':>10}  {'external':>8}  {'internal':>8}  {'manifest':>8}  category"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r['card']:<22}{r['size_MB']:>10.1f}  "
              f"{r['external_paths']:>8}  {r['internal_self_paths']:>8}  "
              f"{str(r['has_DATA_MANIFEST']):>8}  {r['category']}")
        if r["sample_ref"]:
            tag = "外部路径" if r["external_paths"] else "自引用"
            print(f"    └ {tag}示例: {r['sample_ref']}")

    # 汇总
    from collections import Counter
    cnt = Counter(r["category"] for r in rows)
    total_mb = sum(r["size_MB"] for r in rows)
    print("\n==== 汇总 ====")
    for k in ("固化膨胀", "数据缺失", "路径可救", "自包含"):
        if cnt.get(k):
            sub = [r for r in rows if r["category"] == k]
            print(f"  {k:<8}: {cnt[k]:>2} 张, 合计 {sum(s['size_MB'] for s in sub):>10.1f} MB")
    print(f"  {'总计':<8}: {len(rows):>2} 张, 合计 {total_mb:>10.1f} MB ({total_mb/1024:.2f} GB)")

    # 写 CSV
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nCSV 已写出: {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
