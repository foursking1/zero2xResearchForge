# -*- coding: utf-8 -*-
"""构建部署数据包：聚合仓库评测数据 -> website/data/eval_data.json
用法: python build_data.py [--root D:\\project\\paper-bench]
"""
import csv, json, os, re, statistics, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOMAINS = {
    "earth":     {"label": "EARTH 地球科学", "color": "#059669"},
    "astro":     {"label": "ASTRO 天文",    "color": "#7c3aed"},
    "cs":        {"label": "CS 计算机",     "color": "#2563eb"},
    "biomed":    {"label": "BIO 生物医学",  "color": "#db2777"},
    "materials": {"label": "MATERIAL 材料", "color": "#d97706"},
}

def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def num(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default

def task_meta(card_dir: Path):
    title, claim = "", ""
    n_files = size_mb = None
    task_md = card_dir / "TASK.md"
    if task_md.exists():
        text = task_md.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"^#\s*TASK[:：]\s*(.+)$", text, re.M)
        title = m.group(1).strip() if m else card_dir.name
        m2 = re.search(r"^##\s*1[\.、][^\n]*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S)
        if m2:
            paras = [p.strip() for p in m2.group(1).split("\n\n") if len(p.strip()) > 60]
            if paras:
                claim = re.sub(r"\s+", " ", paras[0])[:520]
                if len(paras[0]) > 520: claim += "…"
        if not claim:
            body = re.sub(r"^#.*$", "", text, flags=re.M)
            body = re.sub(r"^\|.*\|$", "", body, flags=re.M)
            body = re.sub(r"^\s*[-*]\s+", "", body, flags=re.M)
            paras = [re.sub(r"\s+", " ", p.strip()) for p in body.split("\n\n")]
            paras = [p for p in paras if len(p) >= 80]
            if paras:
                claim = paras[0][:520] + ("…" if len(paras[0]) > 520 else "")
    manifest = card_dir / "data" / "MANIFEST.tsv"
    if manifest.exists():
        try:
            rows = [l for l in manifest.read_text(encoding="utf-8", errors="ignore").splitlines()
                    if l.strip() and not l.startswith("path")]
            n_files = len(rows)
            total = 0
            for l in rows:
                parts = l.split("\t")
                if len(parts) >= 2:
                    try: total += int(parts[1])
                    except ValueError: pass
            size_mb = round(total / 1e6, 1)
        except Exception:
            pass
    return title, claim, n_files, size_mb

def build(root: Path):
    cards_rows = read_csv(root / "cards.csv")
    l1l2 = {r["card"]: r for r in read_csv(root / "l1l2_labels.csv")}
    v7 = {r["card"]: r for r in read_csv(root / "results" / "v7_full_scores.csv")}
    try:
        agent = {r["card"]: r for r in read_csv(root / "results" / "agent_scores.csv")}
    except FileNotFoundError:
        agent = {}

    cards = []
    for row in cards_rows:
        cid, dom, level = row["card_id"], row["domain"], row["level"]
        title, claim, n_files, size_mb = task_meta(root / "tasks" / dom / cid)
        v, a, lab = v7.get(cid, {}), agent.get(cid, {}), l1l2.get(cid, {})
        cards.append({
            "id": cid, "domain": dom, "level": level, "title": title, "claim": claim,
            "target": lab.get("target_interval", ""),
            "dataFiles": n_files, "dataMB": size_mb,
            "v7": {"total": num(v.get("total")), "A1": num(v.get("A1")), "A2": num(v.get("A2")),
                   "A3": num(v.get("A3")), "A": num(v.get("A")), "B": num(v.get("B")),
                   "conclusion": v.get("conclusion", ""), "nAnchors": num(v.get("n_anchors")),
                   "subClass": v.get("submission_class", ""), "enforce": v.get("enforce_note") or ""},
            "agent": ({"total": num(a.get("total")), "conclusion": a.get("conclusion", ""),
                       "reason": (a.get("reason") or "")[:420], "model": a.get("model", "")}
                      if a.get("total") not in (None, "") else None),
        })

    def mean(vals):
        vals = [v for v in vals if v is not None]
        return round(statistics.mean(vals), 1) if vals else None

    by_domain = {}
    for dom, meta in DOMAINS.items():
        subset = [c for c in cards if c["domain"] == dom]
        l1s = [c["v7"]["total"] for c in subset if c["level"] == "L1"]
        l2s = [c["v7"]["total"] for c in subset if c["level"] == "L2"]
        by_domain[dom] = {**meta, "n": len(subset), "nL1": len(l1s), "nL2": len(l2s),
                          "mean": mean([c["v7"]["total"] for c in subset]),
                          "meanL1": mean(l1s), "meanL2": mean(l2s)}

    totals = [c["v7"]["total"] for c in cards if c["v7"]["total"] is not None]
    l1_all = [c["v7"]["total"] for c in cards if c["level"] == "L1" and c["v7"]["total"] is not None]
    l2_all = [c["v7"]["total"] for c in cards if c["level"] == "L2" and c["v7"]["total"] is not None]
    concl = {}
    for c in cards:
        k = c["v7"]["conclusion"] or "n/a"
        concl[k] = concl.get(k, 0) + 1

    hist = {"0-40": 0, "40-50": 0, "50-60": 0, "60-70": 0, "70-80": 0, "80-90": 0, "90-100": 0}
    for t in totals:
        for lo, hi in [(0,40),(40,50),(50,60),(60,70),(70,80),(80,90),(90,101)]:
            if lo <= t < hi:
                hist["0-40" if lo==0 else f"{lo}-{hi if hi<101 else 100}"] += 1
                break

    paired = [(c["v7"]["total"], c["agent"]["total"]) for c in cards
              if c["v7"]["total"] is not None and c["agent"] and c["agent"]["total"] is not None]
    stats = {
        "nMain": len(cards), "nL1": sum(1 for c in cards if c["level"] == "L1"),
        "nL2": sum(1 for c in cards if c["level"] == "L2"),
        "mean": round(statistics.mean(totals), 1),
        "meanL1": round(statistics.mean(l1_all), 1), "meanL2": round(statistics.mean(l2_all), 1),
        "geo": {"n": 12, "mean": 62.1, "note": "地热独立子集（不在仓库主集内），按原表保留并计入全量"},
        "nFull": len(cards) + 12, "conclusions": concl, "hist": hist,
        "byDomain": by_domain,
        "agentStats": {"n": len(paired), "v7Mean": mean([p[0] for p in paired]),
                       "agentMean": mean([p[1] for p in paired]),
                       "diff": round(statistics.mean(b - a for a, b in paired), 1) if paired else None},
    }
    return {"cards": cards, "stats": stats}

def main():
    root = Path(sys.argv[sys.argv.index("--root") + 1]) if "--root" in sys.argv else HERE.parent.resolve()
    out_dir = HERE / "data"
    out_dir.mkdir(exist_ok=True)
    data = build(root)
    out = out_dir / "eval_data.json"
    out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"root={root}")
    print(f"cards={len(data['cards'])} -> {out} ({out.stat().st_size//1024} KB)")

if __name__ == "__main__":
    main()
