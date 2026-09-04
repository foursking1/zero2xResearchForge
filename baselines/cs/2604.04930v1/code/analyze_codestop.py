#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analysis of the frozen data for arXiv:2604.04930v1
"Early Stopping for Large Reasoning Models via Confidence Dynamics" (CoDE-Stop)

This script analyzes TWO frozen data sources:

  A) scisolvebench public_data (paper-faithful reproduction data)
       <public_data>/baselines/qwen3_4b/aime/*_decisions.jsonl      (Vanilla, DEER, EAT,
                                                                     RCPD, AnswerConvergence,
                                                                     ThinkOrNot a0.2/a0.4)
       <public_data>/confidence/qwen3_4b/aime/trajectories_with_confidence.jsonl
       <public_data>/trajectories/qwen3_4b/aime/trajectories.jsonl  (full trajectories)
       <public_data>/trajectories/qwen3_4b/aime/{vanilla,budget-force,chain-of-draft,no-thinking}/
                                                                     (prompting-strategy runs)

  B) the reproduction workspace under F:/dataset/2604.04930v1/results/
       baseline/*.json, codestop/*.json, comparison/aggregate_summary.json

Everything is computed from the frozen files; no values are taken from the paper text.
"""
import json
import os
import re
import math
import glob
import statistics as st
from pathlib import Path

import numpy as np

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
PUBLIC = None
for _cand in [
    "E:/scisolvebench-data/asset-data/datasets-v1/v1/2604.04930v1/public_data",
    "D:/project/paper-bench/scisolvebench-assets/datasets/v1/2604.04930v1/public_data",
    "/d/project/paper-bench/scisolvebench-assets/datasets/v1/2604.04930v1/public_data",
]:
    if os.path.isdir(_cand):
        PUBLIC = Path(_cand)
        break
if PUBLIC is None:
    raise FileNotFoundError("Cannot locate scisolvebench public_data for 2604.04930v1")
REPRO  = Path("F:/dataset/2604.04930v1/results")
OUT    = Path(__file__).resolve().parent.parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------------
def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# --- (A) scisolvebench data ------------------------------------------------
def load_scisolve():
    """Return dict of structures from the scisolvebench public_data."""
    # full trajectories (top-level, used for baseline decisions)
    traj = {}
    for o in load_jsonl(PUBLIC / "trajectories/qwen3_4b/aime/trajectories.jsonl"):
        key = (o["question_index"], o["rollout_id"])
        traj[key] = o

    # confidence trajectories
    conf = {}
    for o in load_jsonl(PUBLIC / "confidence/qwen3_4b/aime/trajectories_with_confidence.jsonl"):
        key = (o["question_index"], o["rollout_id"])
        conf[key] = o

    # baseline decisions
    decisions = {}
    for p in sorted(glob.glob(str(PUBLIC / "baselines/qwen3_4b/aime/*_decisions.jsonl"))):
        name = Path(p).stem.replace("_decisions", "")
        decisions[name] = load_jsonl(p)

    # prompting-strategy trajectories
    prompts = {}
    for sub in ["vanilla", "budget-force", "chain-of-draft", "no-thinking"]:
        prompts[sub] = load_jsonl(PUBLIC / f"trajectories/qwen3_4b/aime/{sub}/trajectories.jsonl")

    return {"traj": traj, "conf": conf, "decisions": decisions, "prompts": prompts}


# ----------------------------------------------------------------------------
# Token accounting for baseline methods
# ----------------------------------------------------------------------------
def tokens_at_stop(dec, conf_key, conf):
    """
    Reconstruct the number of reasoning tokens consumed by an early-stopping
    method on a given trajectory.

    dec: a decision record (has stop_step, stopped_early, num_steps_total, num_tokens)
    conf_key: (question_index, rollout_id)
    conf: confidence record for that trajectory (has step_indices = token index
          of each reasoning-step start; num_tokens = full length)

    Rule: tokens consumed = token position of the END of the stopped step.
    The end of step s is approximated by the START of step s+1 (step_indices[s+1]).
    If the method never stops early (or the trajectory has no reasoning steps),
    the full trajectory is consumed.
    """
    nsteps = dec["num_steps_total"]
    full = dec["num_tokens"]
    if nsteps == 0 or dec["stop_step"] < 0 or not dec["stopped_early"]:
        return full
    idx = conf[conf_key]["step_indices"]
    s = dec["stop_step"]
    if s + 1 < len(idx):
        return idx[s + 1]
    return full


def method_metrics(decisions, conf):
    """Aggregate accuracy / avg-tokens / token-reduction for every baseline method."""
    vanilla_avg = None
    for name in decisions:
        if name.startswith("Vanilla"):
            vanilla_avg = st.mean([d["num_tokens"] for d in decisions[name]])
            break

    rows = []
    for name, decs in decisions.items():
        n = len(decs)
        acc = st.mean([1.0 if d["is_correct"] else 0.0 for d in decs])
        toks = []
        for d in decs:
            key = (d["question_index"], d["rollout_id"])
            toks.append(tokens_at_stop(d, key, conf))
        avg_tok = st.mean(toks)
        red = (1.0 - avg_tok / vanilla_avg) if vanilla_avg else 0.0
        rows.append({
            "method": name,
            "n": n,
            "accuracy": round(acc, 4),
            "n_correct": int(round(acc * n)),
            "avg_tokens": round(avg_tok, 1),
            "token_reduction_vs_vanilla": round(red, 4),
        })
    return rows, vanilla_avg


# ----------------------------------------------------------------------------
# CoDE-Stop implementation (paper Eq.1-4)
# ----------------------------------------------------------------------------
def codestop_stop_step(conf_seq, step_indices, num_tokens, steps, rmin, rmax, tau, delta=0.55):
    """
    Return the 0-indexed reasoning-step at which CoDE-Stop stops, or None if it
    never triggers (full trajectory consumed).

    c_k : confidence at step k  (k = 1..n)
    r_k = min(rmax, rmin + (rmax-rmin)/steps * k)               (Eq.2)
    v_k = 1(2*c_k - c_{k-1} < delta)                             (Eq.3)
    w_i = log(T_k / T_i) + 1                                     (Eq.4)
    D_k = sum_{i=1..k} w_i * v_i                                 (Eq.1)
    stop at k if c_k >= r_k  OR  D_k >= tau
    """
    n = len(conf_seq)
    if n == 0:
        return None
    v = []
    for k in range(1, n + 1):
        ck = conf_seq[k - 1]
        if k == 1:
            # no c_0 available; with high starting confidence v_1 = 0
            vk = 1.0 if ck < delta else 0.0
        else:
            vk = 1.0 if (2.0 * ck - conf_seq[k - 2]) < delta else 0.0
        v.append(vk)

        rk = min(rmax, rmin + (rmax - rmin) * k / steps)
        Tk = step_indices[k - 1]
        Dk = 0.0
        for i in range(1, k + 1):
            Ti = step_indices[i - 1]
            wi = math.log(Tk / Ti) + 1.0 if Tk > Ti else 1.0
            Dk += wi * v[i - 1]
        if ck >= rk or Dk >= tau:
            return k - 1
    return None


def codestop_tokens_at_stop(stop_step, conf_key, conf):
    """Same token accounting as baseline methods."""
    rec = conf[conf_key]
    if stop_step is None:
        return rec["num_tokens"]
    idx = rec["step_indices"]
    if stop_step + 1 < len(idx):
        return idx[stop_step + 1]
    return rec["num_tokens"]


def codestop_metrics(conf, steps, rmin, rmax, tau, delta=0.55):
    """Aggregate CoDE-Stop metrics over the 10 confidence trajectories."""
    keys = sorted(conf.keys())
    toks, accs = [], []
    for key in keys:
        rec = conf[key]
        ss = codestop_stop_step(rec["confidence_sequence"], rec["step_indices"],
                                rec["num_tokens"], steps, rmin, rmax, tau, delta)
        toks.append(codestop_tokens_at_stop(ss, key, conf))
        accs.append(1.0 if rec["is_correct"] else 0.0)
    return {
        "n": len(keys),
        "accuracy": round(st.mean(accs), 4),
        "n_correct": int(sum(accs)),
        "avg_tokens": round(st.mean(toks), 1),
        "stop_steps": [codestop_stop_step(conf[k]["confidence_sequence"],
                                          conf[k]["step_indices"],
                                          conf[k]["num_tokens"],
                                          steps, rmin, rmax, tau, delta) for k in keys],
    }


# ----------------------------------------------------------------------------
# C03: confidence dynamics & trajectory length
# ----------------------------------------------------------------------------
def confidence_stats(conf):
    """Correct vs incorrect confidence dynamics + length statistics."""
    correct, incorrect = [], []
    for key, rec in conf.items():
        item = {
            "key": key,
            "correct": rec["is_correct"],
            "n_tokens": rec["num_tokens"],
            "n_steps": len(rec["confidence_sequence"]),
            "conf_seq": rec["confidence_sequence"],
        }
        (correct if rec["is_correct"] else incorrect).append(item)

    def summarize(items):
        if not items:
            return {}
        confs = [c for it in items for c in it["conf_seq"]]
        lens = [it["n_tokens"] for it in items]
        nsteps = [it["n_steps"] for it in items]
        # per-trajectory statistics
        firsts = [it["conf_seq"][0] for it in items if it["conf_seq"]]
        lasts = [it["conf_seq"][-1] for it in items if it["conf_seq"]]
        stds = [st.pstdev(it["conf_seq"]) for it in items if len(it["conf_seq"]) > 1]
        # slope of confidence vs step (normalized x)
        slopes = []
        for it in items:
            if len(it["conf_seq"]) >= 2:
                x = np.arange(len(it["conf_seq"]))
                slopes.append(float(np.polyfit(x, it["conf_seq"], 1)[0]))
        return {
            "count": len(items),
            "mean_tokens": round(st.mean(lens), 1),
            "median_tokens": round(st.median(lens), 1),
            "max_tokens": max(lens),
            "min_tokens": min(lens),
            "stdev_tokens": round(st.pstdev(lens), 1),
            "skew_tokens": round(float(stats_skew(lens)), 3),
            "mean_steps": round(st.mean(nsteps), 2),
            "median_steps": st.median(nsteps),
            "max_steps": max(nsteps),
            "all_conf_mean": round(st.mean(confs), 4),
            "first_conf_mean": round(st.mean(firsts), 4) if firsts else None,
            "last_conf_mean": round(st.mean(lasts), 4) if lasts else None,
            "conf_stdev_mean": round(st.mean(stds), 4) if stds else None,
            "slope_mean": round(st.mean(slopes), 4) if slopes else None,
        }

    return {"correct": summarize(correct), "incorrect": summarize(incorrect)}


def stats_skew(x):
    """Pearson sample skewness (g1)."""
    n = len(x)
    if n < 2:
        return 0.0
    m = sum(x) / n
    s = math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1))
    if s == 0:
        return 0.0
    return (sum((v - m) ** 3 for v in x) / n) / (s ** 3)


def heavy_tail_ratio(x):
    """Mean/median ratio > 1 is a sign of right-heavy tail."""
    m = st.mean(x)
    med = st.median(x)
    return (m / med) if med else None


# ----------------------------------------------------------------------------
# C02: prompting strategies
# ----------------------------------------------------------------------------
def extract_boxed_number(text):
    boxed = re.findall(r"\\boxed\{([^}]+)\}", text)
    if boxed:
        nums = re.findall(r"-?\d+", boxed[-1])
        if nums:
            return nums[-1]
    return None


def prompt_strategy_metrics(prompts):
    """Evaluate base (full-length) accuracy & token usage of each prompting strategy."""
    out = []
    for name, rows in prompts.items():
        n = len(rows)
        correct = 0
        toks = []
        for r in rows:
            ans = extract_boxed_number(r["text"])
            gt = r["ground_truth"]
            ok = False
            if ans is not None and gt:
                try:
                    ok = abs(float(ans) - float(gt)) / abs(float(gt)) < 0.05
                except ValueError:
                    ok = ans.strip() == gt.strip()
            correct += 1 if ok else 0
            toks.append(r["num_tokens"])
        out.append({
            "prompt_strategy": name,
            "n": n,
            "accuracy": round(correct / n, 4),
            "n_correct": correct,
            "avg_tokens": round(st.mean(toks), 1),
        })
    return out


# ----------------------------------------------------------------------------
# C04: compute on incorrect rollouts
# ----------------------------------------------------------------------------
def incorrect_rollout_tokens(conf, decisions, codestop_conf):
    """Avg reasoning tokens spent on INCORRECT rollouts for each method."""
    incorrect_keys = [k for k, rec in conf.items() if not rec["is_correct"]]
    out = {}
    for name, decs in decisions.items():
        toks = []
        for d in decs:
            key = (d["question_index"], d["rollout_id"])
            if key in incorrect_keys:
                toks.append(tokens_at_stop(d, key, conf))
        out[name] = round(st.mean(toks), 1) if toks else None
    return out, incorrect_keys


def main():
    S = load_scisolve()
    conf = S["conf"]
    decisions = S["decisions"]

    report = {}

    # ------------------------------------------------------------------ C01
    # Baselines metrics
    base_rows, vanilla_avg = method_metrics(decisions, conf)

    # CoDE-Stop with paper's reported hyperparameters for Qwen3-4B on AIME
    # (Table 3 in paper: (steps, rmin, tau) = (5, 0.0, 7.1), rmax = 0.95)
    codestop_paper = codestop_metrics(conf, steps=5, rmin=0.0, rmax=0.95, tau=7.1)
    codestop_paper["token_reduction_vs_vanilla"] = round(
        1.0 - codestop_paper["avg_tokens"] / vanilla_avg, 4)
    codestop_paper["method"] = "CoDE-Stop (paper hp)"

    # tau sweep -> accuracy-compute tradeoff
    tau_sweep = []
    for tau in [0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.1, 8.0, 10.0, 12.0, 15.0, 20.0]:
        m = codestop_metrics(conf, steps=5, rmin=0.0, rmax=0.95, tau=tau)
        m["tau"] = tau
        m["token_reduction_vs_vanilla"] = round(1.0 - m["avg_tokens"] / vanilla_avg, 4)
        tau_sweep.append(m)

    report["c01_baselines"] = base_rows
    report["c01_vanilla_avg_tokens"] = round(vanilla_avg, 1)
    report["c01_codestop_paper_hp"] = codestop_paper
    report["c01_codestop_tau_sweep"] = tau_sweep

    # ------------------------------------------------------------------ C03
    cs = confidence_stats(conf)
    report["c03_confidence_stats"] = cs

    # Heavy-tail ratio on lengths
    def lens_by_correctness():
        corr, incorr = [], []
        for rec in conf.values():
            (corr if rec["is_correct"] else incorr).append(rec["num_tokens"])
        return corr, incorr
    corr_lens, incorr_lens = lens_by_correctness()
    report["c03_correct_lengths"] = corr_lens
    report["c03_incorrect_lengths"] = incorr_lens
    report["c03_correct_heavy_tail_ratio"] = round(heavy_tail_ratio(corr_lens), 3) if len(corr_lens) else None
    report["c03_incorrect_heavy_tail_ratio"] = round(heavy_tail_ratio(incorr_lens), 3) if len(incorr_lens) else None

    # ------------------------------------------------------------------ C02
    psm = prompt_strategy_metrics(S["prompts"])
    report["c02_prompt_strategy_base"] = psm

    # ------------------------------------------------------------------ C04
    irt, incorrect_keys = incorrect_rollout_tokens(conf, decisions, None)
    report["c04_incorrect_keys"] = [[k[0], k[1]] for k in incorrect_keys]
    report["c04_avg_tokens_on_incorrect"] = irt
    # CoDE-Stop tokens on incorrect rollouts (paper hp)
    cs_incorr = []
    for k in incorrect_keys:
        rec = conf[k]
        ss = codestop_stop_step(rec["confidence_sequence"], rec["step_indices"],
                                rec["num_tokens"], steps=5, rmin=0.0, rmax=0.95, tau=7.1)
        cs_incorr.append(codestop_tokens_at_stop(ss, k, conf))
    report["c04_codestop_paperhp_avg_tokens_on_incorrect"] = round(st.mean(cs_incorr), 1)

    # ------------------------------------------------------------------ save
    with open(OUT / "metrics_scisolve.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print("scisolve analysis written to", OUT / "metrics_scisolve.json")

    # quick console summary
    print("\n=== C01 baselines (accuracy / avg tokens / reduction) ===")
    for r in base_rows:
        print(f"  {r['method']:<24} acc={r['accuracy']:.2f}  avg_tok={r['avg_tokens']:8.1f}  red={r['token_reduction_vs_vanilla']:.3f}")
    print(f"  {'CoDE-Stop (paper hp)':<24} acc={codestop_paper['accuracy']:.2f}  avg_tok={codestop_paper['avg_tokens']:8.1f}  red={codestop_paper['token_reduction_vs_vanilla']:.3f}")


if __name__ == "__main__":
    main()
