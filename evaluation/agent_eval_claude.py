#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用 WSL 中的 Claude Code 作为 agent 评测一张 paper-bench 卡，并与 v7 分数对比。

用法（运行时注入 key，不写死在脚本里）：
  ANTHROPIC_API_KEY=sk-xxx [ANTHROPIC_BASE_URL=https://...] \
  wsl python3 /mnt/d/project/paper-bench/evaluation/agent_eval_claude.py [--cards c1,c2]

关键点：
- claude 走 --bare 模式：严格用 ANTHROPIC_API_KEY 认证，不读 OAuth/keychain。
- --dangerously-skip-permissions + --add-dir <卡目录>：让 agent 在该卡目录内读文件、跑提交代码。
- agent 真正执行提交代码并和 PAPER_ANCHOR 真值做容差比对（这是与 v7 / free single-judge 的本质区别）。
- 输出 agent_eval_results.csv + 打印与 v7 的对照。
"""
import os, sys, json, re, csv, time, subprocess, argparse
from card_material import private_card_dir

ROOT = os.environ.get(
    "PAPER_BENCH_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = f"{ROOT}/work"
CSV_V7 = f"{WORK}/v7_full_scores.csv"
MODEL = os.environ.get("CLAUDE_EVAL_MODEL", "sonnet")
MAX_BUDGET = os.environ.get("CLAUDE_EVAL_BUDGET", "0.50")

PROMPT = """You are an evaluator for a scientific reproduction benchmark (SciSolveBench / zero2xResearchForge).
Task specification directory: {card_dir}
Private evaluation-material directory: {private_dir}
Baseline directory: {baseline_dir}

Steps (use your tools to actually do them, do not just summarize):
1. Read TASK.md in the task specification directory, then PAPER_ANCHOR.md and SCORE_RUBRIC.md in the private evaluation-material directory.
2. Read the historical baseline submission in the baseline directory (final report, metrics.json, evidence tables, source code).
3. If the submission includes runnable code/scripts (e.g. run.sh, *.py, *.ipynb, Makefile), execute them in a sandbox to REGENERATE the claimed metrics. Then compare the regenerated numbers against the truth values in PAPER_ANCHOR.md with reasonable tolerance (relative ~5-10%, or as specified per anchor). Record any discrepancies.
4. Score with these dimensions and maxima:
   A1 delivery completeness (0-12): are machine-readable deliverables present (report/metrics/code/evidence)? missing key deliverables -> low.
   A2 scientific fidelity (0-33): does the method match the task spec? no unauthorized dataset/method substitution?
   A3 methodology rigor (0-15): experiment design / ablations / error handling.
   B evidence authenticity (0-40): are reported numbers consistent with PAPER_ANCHOR truth within tolerance? clear contradiction or systematic deviation -> very low B.
5. Output ONLY a JSON object, no surrounding prose:
{{"A1":<int 0-12>,"A2":<int 0-33>,"A3":<int 0-15>,"B":<int 0-40>,"total":<A1+A2+A3+B>,"conclusion":"supported|partially_supported|contradicted|unverified","reason":"<concise Chinese; cite the specific numeric checks you performed and their pass/fail>"}}

Be strict: verify numbers against the anchor table; do not trust confident narration. If you executed code, state whether regenerated metrics matched the submission's claims.
"""

def v7_scores():
    d = {}
    for r in csv.DictReader(open(CSV_V7, encoding="utf-8-sig")):
        try: d[r["card"]] = float(r["total"])
        except: pass
    return d

def resolve(card_id):
    cands = []
    for dom in ["astro","biomed","cs","earth","materials"]:
        cands.append(f"{ROOT}/tasks/{dom}/{card_id}")
    # legacy 卡已全部并入 tasks/<domain>/<card>，全库统一 2 层路径
    for c in cands:
        if os.path.isdir(c): return c
    return None

def run_claude(card_dir, api_key, base_url):
    env = dict(os.environ)
    env["ANTHROPIC_API_KEY"] = api_key
    if base_url: env["ANTHROPIC_BASE_URL"] = base_url
    domain = os.path.basename(os.path.dirname(card_dir))
    baseline_dir = os.path.join(ROOT, "baselines", domain, os.path.basename(card_dir))
    private_dir = private_card_dir(card_dir)
    prompt = PROMPT.format(card_dir=card_dir, private_dir=private_dir, baseline_dir=baseline_dir)
    cmd = ["claude", "-p", "--bare", "--dangerously-skip-permissions",
           "--add-dir", card_dir]
    if os.path.isdir(private_dir):
        cmd.extend(["--add-dir", str(private_dir)])
    if os.path.isdir(baseline_dir):
        cmd.extend(["--add-dir", baseline_dir])
    cmd.extend(["--model", MODEL, "--output-format", "json",
                "--max-budget-usd", MAX_BUDGET, prompt])
    for attempt in range(3):
        try:
            out = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=900)
            txt = out.stdout.strip()
            try:
                wrap = json.loads(txt); result = wrap.get("result", txt)
            except Exception:
                result = txt
            m = re.search(r"\{[^{}]*\"total\"[^{}]*\}", result, re.S)
            if m:
                return json.loads(m.group(0)), result
            sys.stderr.write(f"[attempt {attempt}] no JSON in output; tail={result[-300:]}\n")
        except Exception as e:
            sys.stderr.write(f"[attempt {attempt}] {e!r}\n")
        time.sleep(5 * (attempt + 1))
    return None, ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cards", default="1903.02557_dash_supernova_class,2111.10009_exominer_tess_vetting,2110.08733_loveda,1709.00029_eurosat")
    args = ap.parse_args()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    if not api_key:
        sys.exit("ERROR: set ANTHROPIC_API_KEY (and optionally ANTHROPIC_BASE_URL) in env.")
    v7 = v7_scores()
    rows = []
    for cid in [c.strip() for c in args.cards.split(",") if c.strip()]:
        d = resolve(cid)
        if not d:
            sys.stderr.write(f"[skip] {cid} not found\n"); continue
        sc, raw = run_claude(d, api_key, base_url)
        v7s = v7.get(cid)
        rec = {"card": cid, "v7_total": v7s,
               "agent_A1": sc.get("A1") if sc else "", "agent_A2": sc.get("A2") if sc else "",
               "agent_A3": sc.get("A3") if sc else "", "agent_B": sc.get("B") if sc else "",
               "agent_total": sc.get("total") if sc else None,
               "agent_conclusion": sc.get("conclusion") if sc else None,
               "agent_reason": (sc.get("reason","")[:400] if sc else raw[:300])}
        rows.append(rec)
        sys.stderr.write(f"[done] {cid}: v7={v7s} agent={rec['agent_total']} ({rec['agent_conclusion']})\n")
    with open(f"{WORK}/agent_eval_results.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("\n=== Claude Code agent vs v7 ===")
    for r in rows:
        print(f"  {r['card'][:40]:40s} v7={r['v7_total']}  agent={r['agent_total']}  {r['agent_conclusion']}")
        print(f"     reason: {r['agent_reason'][:200]}")

if __name__ == "__main__":
    main()
