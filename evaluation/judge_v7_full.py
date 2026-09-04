#!/usr/bin/env python3
"""Full eval with JUDGE_PROMPT_v7.md. cards, threaded, resumable.
Outputs: results/v7_full_results.jsonl (incremental), results/v7_full_scores.csv
Enforcement (code-level): anchor_table coverage cap; supported-downgrade."""
import csv, json, os, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge_eval105_v7 as j105

BASE = os.environ.get(
    "PAPER_BENCH_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROMPT = open(os.path.join(BASE, "evaluation", "JUDGE_PROMPT_v7.md"), encoding="utf-8").read()
OUT_JSONL = os.path.join(BASE, "results", "v7_full_results.jsonl")
OUT_CSV = os.path.join(BASE, "results", "v7_full_scores.csv")
WORKERS = int(os.environ.get("JUDGE_WORKERS", "4"))
BASELINES = os.path.join(BASE, "baselines")

def discover():
    cards = []
    with open(os.path.join(BASE, "cards.csv"), encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            d, c = row["domain"], row["card_id"]
            card_dir = os.path.join(BASE, "tasks", d, c)
            if os.path.isdir(card_dir):
                cards.append(("main", d, c, card_dir))
    return cards

NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")

def _val(s):
    if not isinstance(s, str):
        return None
    m = NUM_RE.search(s.replace(",", ""))
    return float(m.group()) if m else None

def systematic_failure(rows):
    """All numeric anchors (>=3) out of tolerance, none MISSING, and
    max relative deviation >=25% -> main result not reproduced."""
    num = [r for r in rows if r.get("within_tolerance") is not None]
    if len(num) < 3 or not all(r.get("within_tolerance") is False for r in num):
        return False
    rels = []
    for r in num:
        v, p = _val(r.get("agent_value")), _val(r.get("paper_value"))
        if v is None or p is None or p == 0:
            return False
        rels.append(abs(v - p) / abs(p))
    return max(rels) >= 0.25

def enforce(d):
    """Code-level backstops for v7 rules."""
    at = d.get("anchor_table")
    n = d.get("n_anchors")
    rows = at if isinstance(at, list) else []
    # 1) missing/incomplete anchor_table -> A2<=12, total<=70
    if not isinstance(at, list) or not rows or (isinstance(n, int) and len(rows) < n):
        d["A2"] = min(d.get("A2", 0), 12.0)
        d["enforce_note"] = "anchor_table incomplete -> A2 capped"
    # recompute totals from clamped parts
    a = round(d.get("A1", 0) + d.get("A2", 0) + d.get("A3", 0), 1)
    d["A"] = a
    total = round(a + d.get("B", 0), 1)
    if not rows or (isinstance(n, int) and len(rows) < max(n or 0, 1)):
        total = min(total, 70.0)
    # 2) supported requires all numeric anchors in tolerance
    bad = [r for r in rows if r.get("within_tolerance") is False]
    if d.get("conclusion") == "supported" and bad:
        d["conclusion"] = "partially_supported"
        d["enforce_note"] = (d.get("enforce_note") or "") + \
            f" | downgraded: {len(bad)} anchors out of tolerance"
    if d.get("conclusion") == "contradicted":
        total = min(total, 50.0)
    elif d.get("conclusion") in ("supported", "partially_supported") \
            and systematic_failure(rows):
        d["conclusion"] = "contradicted"
        total = min(total, 50.0)
        d["enforce_note"] = (d.get("enforce_note") or "") + \
            " | systematic failure: all numeric anchors out of tolerance " \
            "(>=3, no MISSING), max relative deviation >=25% -> contradicted"
    d["total"] = total
    return d

def is_empty_submission(path):
    for _root, _dirs, files in os.walk(path):
        if files:
            return False
    return True

def judge_one(card):
    src, dom, card_id, card_dir = card
    key = f"{src}/{card_id}"
    asol = os.path.join(BASELINES, dom, card_id)
    if is_empty_submission(asol):
        rec = {"key": key, "source": src, "domain": dom, "card": card_id,
               "total": 0.0, "A": 0.0, "A1": 0.0, "A2": 0.0, "A3": 0.0,
               "B": 0.0, "conclusion": "inconclusive", "n_anchors": None,
               "submission_class": "not_submitted",
               "enforce_note": "empty baseline -> not_submitted",
               "anchor_table": [], "ok": True}
        with wlock:
            with open(OUT_JSONL, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"EMPTY {key} total=0 (not_submitted)", flush=True)
        return rec
    try:
        spec = j105.collect_spec(card_dir)
        artifacts = j105.collect_artifacts(asol)
        ev = j105.scan_evidence(asol)
        user = j105.USER_TMPL.format(spec=spec, artifacts=artifacts,
                                     evidence=j105.evidence_line(ev))
        payload = {"model": j105.DEFAULT_MODEL,
                   "messages": [{"role": "system", "content": PROMPT},
                                {"role": "user", "content": user}],
                   "temperature": 0, "max_tokens": 6000}
        req = urllib_request(payload)
        out = call_with_retry(req)
        d = j105.parse_json(out, ev)
        d = enforce(d)
        rec = {"key": key, "source": src, "domain": dom, "card": card_id}
        keep = ("total","A","A1","A2","A3","B","conclusion","n_anchors",
                "submission_class","enforce_note","A_notes","B_notes","weaknesses")
        rec.update({k: d.get(k) for k in keep})
        rec["anchor_table"] = d.get("anchor_table", [])
        rec["ok"] = True
    except Exception as e:
        rec = {"key": key, "source": src, "domain": dom, "card": card_id,
               "ok": False, "error": repr(e)[:300]}
    with wlock:
        with open(OUT_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(("OK  " if rec["ok"] else "FAIL") + f" {key} total={rec.get('total')}", flush=True)
    return rec

def urllib_request(payload):
    import urllib.request, ssl
    req = urllib.request.Request(
        j105.API_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {j105.API_KEY}",
                 "Content-Type": "application/json"})
    globals()["_req"] = req
    return req

def call_with_retry(req):
    import urllib.request, ssl
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300, context=ctx) as r:
                out = json.loads(r.read().decode("utf-8", "replace"))
            return out["choices"][0]["message"]["content"]
        except Exception as e:
            last = e
            print(f"  retry {attempt+1}: {e!r}"[:160], flush=True)
            time.sleep(min(10 * (attempt + 1), 45))
            req = urllib.request.Request(
                j105.API_URL, data=req.data, headers=dict(req.headers.items()))
    raise RuntimeError(last)

wlock = threading.Lock()

def main():
    if not j105.API_KEY:
        raise SystemExit("JUDGE_API_KEY is required for LLM judging.")
    done = set()
    if os.path.exists(OUT_JSONL):
        for line in open(OUT_JSONL, encoding="utf-8"):
            try: done.add(json.loads(line)["key"])
            except Exception: pass
    cards = [c for c in discover() if f"{c[0]}/{c[2]}" not in done]
    print(f"=== v7 full eval: {len(discover())} cards, {len(done)} already done, {len(cards)} to run ===", flush=True)
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(judge_one, c) for c in cards]
        for _ in as_completed(futs): pass
    write_csv()
    print("=== done ===", flush=True)

def write_csv():
    rows = [json.loads(l) for l in open(OUT_JSONL, encoding="utf-8")]
    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["source","domain","card","total","A1","A2","A3","A","B",
                    "conclusion","n_anchors","submission_class","enforce_note","ok"])
        for r in rows:
            w.writerow([r.get("source"),r.get("domain"),r.get("card"),
                        r.get("total"),r.get("A1"),r.get("A2"),r.get("A3"),
                        r.get("A"),r.get("B"),r.get("conclusion"),
                        r.get("n_anchors"),r.get("submission_class"),
                        r.get("enforce_note",""),r.get("ok")])
    print(f"csv written: {OUT_CSV} ({len(rows)} rows)", flush=True)

if __name__ == "__main__":
    main()
