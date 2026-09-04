#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the final evidence table (evidence_table.csv), the machine-readable
metrics bundle (metrics.json), and supporting figures.

Inputs: metrics_scisolve.json and metrics_repro.json (produced by the two
analyze_* scripts) plus the raw scisolvebench files for DEER+Fixed-Step and
for the figures.
"""
import json
import os
import math
import csv
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PUBLIC = None
for _c in [
    "E:/scisolvebench-data/asset-data/datasets-v1/v1/2604.04930v1/public_data",
    "D:/project/paper-bench/scisolvebench-assets/datasets/v1/2604.04930v1/public_data",
]:
    if os.path.isdir(_c):
        PUBLIC = Path(_c)
        break

OUT = Path(__file__).resolve().parent.parent / "results"
FIG = OUT / "figures"
FIG.mkdir(parents=True, exist_ok=True)


def load_jsonl(p):
    rows = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def deer_fixed_step(decisions_deer, conf, max_steps):
    """DEER + Fixed-Step: stop when DEER triggers OR steps exceed max_steps."""
    toks = []
    for d in decisions_deer:
        key = (d["question_index"], d["rollout_id"])
        rec = conf[key]
        idx = rec["step_indices"]
        nsteps = d["num_steps_total"]
        full = d["num_tokens"]
        # DEER decision
        if nsteps == 0 or d["stop_step"] < 0 or not d["stopped_early"]:
            deer_tokens = full
        else:
            s = d["stop_step"]
            deer_tokens = idx[s + 1] if s + 1 < len(idx) else full
        # Fixed-step component: stop at min(max_steps, nsteps) if nsteps > max_steps
        if nsteps > max_steps:
            fs_tokens = idx[max_steps] if max_steps < len(idx) else full
            toks.append(min(deer_tokens, fs_tokens))
        else:
            toks.append(deer_tokens)
    return toks


def main():
    scis = json.load(open(OUT / "metrics_scisolve.json", encoding="utf-8"))
    repro = json.load(open(OUT / "metrics_repro.json", encoding="utf-8"))

    conf = {}
    for o in load_jsonl(PUBLIC / "confidence/qwen3_4b/aime/trajectories_with_confidence.jsonl"):
        conf[(o["question_index"], o["rollout_id"])] = o
    deer = load_jsonl(PUBLIC / "baselines/qwen3_4b/aime/DEER_decisions.jsonl")

    incorrect_keys = set(tuple(k) for k in scis["c04_incorrect_keys"])

    # ---- DEER+Fixed-Step ---------------------------------------------------
    dfs40_all = deer_fixed_step(deer, conf, 40)
    dfs40_inc = [t for d, t in zip(deer, dfs40_all)
                 if (d["question_index"], d["rollout_id"]) in incorrect_keys]
    dfs10_all = deer_fixed_step(deer, conf, 10)
    dfs10_inc = [t for d, t in zip(deer, dfs10_all)
                 if (d["question_index"], d["rollout_id"]) in incorrect_keys]

    c04_extra = {
        "DEER+FixedStep(40)_avg_all": round(sum(dfs40_all) / len(dfs40_all), 1),
        "DEER+FixedStep(40)_avg_incorrect": round(sum(dfs40_inc) / len(dfs40_inc), 1),
        "DEER+FixedStep(10)_avg_all": round(sum(dfs10_all) / len(dfs10_all), 1),
        "DEER+FixedStep(10)_avg_incorrect": round(sum(dfs10_inc) / len(dfs10_inc), 1),
        "max_steps_in_data": max(d["num_steps_total"] for d in deer),
    }

    # ---- evidence rows -----------------------------------------------------
    evidence = []

    # C01 evidence (scisolve, AIME, equal accuracy)
    vanilla = next(r for r in scis["c01_baselines"] if r["method"] == "Vanilla")
    cs = scis["c01_codestop_paper_hp"]
    evidence.append({
        "metric": "c01_scisolve_aime_vanilla_accuracy", "value": vanilla["accuracy"],
        "detail": "frozen decisions; 10 AIME rollouts; equal across methods",
    })
    evidence.append({
        "metric": "c01_scisolve_aime_vanilla_avg_tokens", "value": vanilla["avg_tokens"],
        "detail": "reconstructed full-length reasoning tokens",
    })
    evidence.append({
        "metric": "c01_scisolve_aime_codestop_avg_tokens", "value": cs["avg_tokens"],
        "detail": "CoDE-Stop paper hp (steps=5,rmin=0,rmax=0.95,tau=7.1)",
    })
    evidence.append({
        "metric": "c01_scisolve_aime_codestop_token_reduction", "value": cs["token_reduction_vs_vanilla"],
        "detail": "1 - avg_tokens_codestop/avg_tokens_vanilla",
    })
    for r in scis["c01_baselines"]:
        evidence.append({
            "metric": f"c01_scisolve_aime_{r['method']}_token_reduction",
            "value": r["token_reduction_vs_vanilla"],
            "detail": f"accuracy {r['accuracy']} (n={r['n']})",
        })

    # C01 evidence (repro GPQA sweep)
    for row in repro["gpqa"]["rows"]:
        evidence.append({
            "metric": f"c01_repro_gpqa_thr{row['confidence_threshold']:.2f}_accuracy",
            "value": row["accuracy"], "detail": f"avg_tokens={row['avg_tokens']}, n={row['n']}",
        })
        evidence.append({
            "metric": f"c01_repro_gpqa_thr{row['confidence_threshold']:.2f}_token_reduction",
            "value": row["token_reduction"], "detail": "vs baseline full-length",
        })
    evidence.append({
        "metric": "c01_repro_gpqa_baseline_accuracy", "value": repro["gpqa"]["baseline_accuracy"],
        "detail": f"avg_tokens={repro['gpqa']['baseline_avg_tokens']}",
    })
    # AIME repro
    for row in repro["aime"]["rows"]:
        evidence.append({
            "metric": f"c01_repro_aime_thr{row['confidence_threshold']:.2f}_accuracy",
            "value": row["accuracy"], "detail": f"avg_tokens={row['avg_tokens']}",
        })
        evidence.append({
            "metric": f"c01_repro_aime_thr{row['confidence_threshold']:.2f}_token_reduction",
            "value": row["token_reduction"], "detail": "",
        })
    evidence.append({
        "metric": "c01_repro_aime_baseline_accuracy", "value": repro["aime"]["baseline"]["accuracy"],
        "detail": f"avg_tokens={repro['aime']['baseline']['avg_tokens']}",
    })
    evidence.append({
        "metric": "c01_scope_models_available", "value": 1,
        "detail": "only Qwen3-4B in frozen data (paper claims 4 models)",
    })
    evidence.append({
        "metric": "c01_scope_benchmarks_available", "value": 3,
        "detail": "AIME (real questions) + curated MATH & GPQA; no MATH500/GSM8K/GPQA-Diamond",
    })

    # C02 evidence
    for r in scis["c02_prompt_strategy_base"]:
        evidence.append({
            "metric": f"c02_prompt_{r['prompt_strategy']}_base_accuracy",
            "value": r["accuracy"], "detail": f"avg_tokens={r['avg_tokens']}, n={r['n']}",
        })
    evidence.append({
        "metric": "c02_has_prompt_strategy_trajectories", "value": 4,
        "detail": "vanilla, budget-force, chain-of-draft, no-thinking present",
    })
    evidence.append({
        "metric": "c02_has_confidence_for_prompt_strategies", "value": 0,
        "detail": "no confidence sequences / CoDE-Stop decisions for prompting variants",
    })

    # C03 evidence
    cs3 = scis["c03_confidence_stats"]
    evidence.append({"metric": "c03_scisolve_correct_first_conf_mean", "value": cs3["correct"]["first_conf_mean"], "detail": "high early confidence (n=4)"})
    evidence.append({"metric": "c03_scisolve_incorrect_conf_mean", "value": cs3["incorrect"]["all_conf_mean"], "detail": "incorrect also high-confidence"})
    evidence.append({"metric": "c03_scisolve_incorrect_conf_stdev_mean", "value": cs3["incorrect"]["conf_stdev_mean"], "detail": "low variance, not fluctuating"})
    evidence.append({"metric": "c03_scisolve_correct_mean_tokens", "value": cs3["correct"]["mean_tokens"], "detail": "n=4"})
    evidence.append({"metric": "c03_scisolve_incorrect_mean_tokens", "value": cs3["incorrect"]["mean_tokens"], "detail": "n=6, all at 8192 max budget"})
    evidence.append({"metric": "c03_scisolve_incorrect_heavy_tail_ratio", "value": scis["c03_incorrect_heavy_tail_ratio"], "detail": "mean/median; truncated at max budget"})
    ac = repro["all_codestop_runs"]
    evidence.append({"metric": "c03_repro_allruns_incorrect_conf_mean", "value": ac["confidence"]["incorrect"]["mean"], "detail": f"n={ac['n_incorrect']} (higher than correct)"})
    evidence.append({"metric": "c03_repro_allruns_correct_conf_mean", "value": ac["confidence"]["correct"]["mean"], "detail": f"n={ac['n_correct']}"})
    evidence.append({"metric": "c03_repro_allruns_fulltoken_ratio_inc_over_corr", "value": ac["length_ratio_incorrect_over_correct"], "detail": "mean full tokens"})
    evidence.append({"metric": "c03_repro_gpqa_baseline_incorr_corr_token_ratio", "value": round(repro["gpqa_baseline_lengths"]["incorrect"]["mean"] / repro["gpqa_baseline_lengths"]["correct"]["mean"], 3), "detail": "GPQA baseline"})

    # C04 evidence
    irt = scis["c04_avg_tokens_on_incorrect"]
    evidence.append({"metric": "c04_scisolve_incorrect_avg_tokens_codestop", "value": scis["c04_codestop_paperhp_avg_tokens_on_incorrect"], "detail": "6 incorrect rollouts"})
    evidence.append({"metric": "c04_scisolve_incorrect_avg_tokens_deer", "value": irt["DEER"], "detail": "6 incorrect rollouts"})
    evidence.append({"metric": "c04_scisolve_incorrect_avg_tokens_deer_fixedstep40", "value": c04_extra["DEER+FixedStep(40)_avg_incorrect"], "detail": "= DEER because max steps (27) < 40"})
    evidence.append({"metric": "c04_scisolve_incorrect_avg_tokens_deer_fixedstep10", "value": c04_extra["DEER+FixedStep(10)_avg_incorrect"], "detail": "sensitivity"})
    evidence.append({"metric": "c04_scisolve_codestop_vs_deer_incorrect_reduction", "value": round(1 - scis["c04_codestop_paperhp_avg_tokens_on_incorrect"] / irt["DEER"], 4), "detail": "1 - codestop/deer on incorrect rollouts"})
    evidence.append({"metric": "c04_repro_effective_ratio_inc_over_corr", "value": ac["effective_ratio_incorrect_over_correct"], "detail": "CoDE-Stop stops incorrect rollouts earlier"})
    evidence.append({"metric": "c04_incorrect_sample_size", "value": len(incorrect_keys), "detail": "very small sample"})

    # ---- write evidence CSV ------------------------------------------------
    with open(OUT / "evidence_table.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value", "detail"])
        for e in evidence:
            w.writerow([e["metric"], e["value"], e["detail"]])
    print("evidence_table.csv written:", len(evidence), "rows")

    # ---- final metrics.json --------------------------------------------------
    metrics = {
        "paper_id": "2604.04930v1",
        "analysis_generated_by": "agent_solution/code",
        "claims": {
            "C01": {
                "verdict": "partially_supported",
                "summary": ("25-50% token reduction at comparable accuracy reproduced on the GPQA "
                            "reproduction subset; best token reduction among baselines on the AIME "
                            "scisolve subset; but only 1 of 4 models and 3 benchmarks present, and "
                            "accuracy is NOT maintained on the AIME reproduction subset."),
                "key_numbers": {
                    "scisolve_aime_codestop_token_reduction": cs["token_reduction_vs_vanilla"],
                    "scisolve_aime_deer_token_reduction": next(r["token_reduction_vs_vanilla"] for r in scis["c01_baselines"] if r["method"] == "DEER"),
                    "repro_gpqa_thr075": {"accuracy": 0.8, "token_reduction": 0.4349},
                    "repro_gpqa_thr080": {"accuracy": 1.0, "token_reduction": 0.4338},
                    "repro_gpqa_thr095": {"accuracy": 0.8, "token_reduction": 0.2812},
                    "repro_aime_thr095": {"accuracy": 0.70, "token_reduction": 0.112},
                    "models_available": 1,
                },
            },
            "C02": {
                "verdict": "inconclusive",
                "summary": ("4 prompting-strategy trajectory sets exist (vanilla, budget-force, "
                            "chain-of-draft, no-thinking) with base accuracy 0.3/0.4/0.5/0.2 but "
                            "no confidence sequences or CoDE-Stop decisions for them, so the claim "
                            "cannot be tested on frozen data."),
                "key_numbers": {r["prompt_strategy"]: {"accuracy": r["accuracy"], "avg_tokens": r["avg_tokens"]} for r in scis["c02_prompt_strategy_base"]},
            },
            "C03": {
                "verdict": "partially_supported",
                "summary": ("Correct trajectories do reach high confidence early (scisolve first-step "
                            "confidence mean 0.945). Incorrect trajectories are longer (scisolve: all 6 "
                            "at 8192 max vs correct mean 5663; repro GPQA baseline ratio 1.88). BUT "
                            "incorrect trajectories do NOT show unstable/fluctuating confidence in the "
                            "frozen data: their confidence is high and stable (mean 0.93, sd 0.009; "
                            "repro incorrect conf mean 0.774 > correct 0.709), consistent with the "
                            "paper's separate observation of overconfidence on incorrect paths."),
                "key_numbers": {
                    "scisolve_correct_first_conf": cs3["correct"]["first_conf_mean"],
                    "scisolve_incorrect_conf_mean": cs3["incorrect"]["all_conf_mean"],
                    "scisolve_incorrect_conf_sd": cs3["incorrect"]["conf_stdev_mean"],
                    "scisolve_correct_mean_tokens": cs3["correct"]["mean_tokens"],
                    "scisolve_incorrect_mean_tokens": cs3["incorrect"]["mean_tokens"],
                    "repro_correct_conf_mean": ac["confidence"]["correct"]["mean"],
                    "repro_incorrect_conf_mean": ac["confidence"]["incorrect"]["mean"],
                    "repro_fulltoken_ratio_inc_over_corr": ac["length_ratio_incorrect_over_correct"],
                },
            },
            "C04": {
                "verdict": "partially_supported",
                "summary": ("On the 6 incorrect rollouts of the AIME scisolve subset, CoDE-Stop uses "
                            "5711.8 avg tokens vs DEER 6182.0 (and DEER+Fixed-Step(40) = 6182.0, "
                            "identical to DEER because max trajectory has 27 steps < 40) at matched "
                            "accuracy 0.4. ~7.6% reduction. Small sample; DEER+Fixed-Step degenerates "
                            "to DEER on this data."),
                "key_numbers": {
                    "incorrect_rollouts": len(incorrect_keys),
                    "codestop_avg_tokens_incorrect": scis["c04_codestop_paperhp_avg_tokens_on_incorrect"],
                    "deer_avg_tokens_incorrect": irt["DEER"],
                    "deer_fixedstep40_avg_tokens_incorrect": c04_extra["DEER+FixedStep(40)_avg_incorrect"],
                    "codestop_vs_deer_reduction_on_incorrect": round(1 - scis["c04_codestop_paperhp_avg_tokens_on_incorrect"] / irt["DEER"], 4),
                    "matched_accuracy": 0.4,
                },
            },
        },
        "caveats": [
            "Frozen scisolvebench subset: 5 AIME questions x 2 rollouts = 10 trajectories (4 correct / 6 incorrect).",
            "Frozen reproduction results: Qwen3-4B only; curated (synthetic) AIME/MATH/GPQA examples.",
            "The reproduction CoDE-Stop is a post-hoc heuristic simulation (truncation at 10 checkpoints), not the paper's online answer-generation loop.",
            "Frozen confidence sequences are high/stable for both correct and incorrect trajectories, so the CoDE-Stop reconstruction triggers the confidence stop at the first reasoning step for most trajectories.",
            "DEER+Fixed-Step(40) is indistinguishable from DEER because no trajectory exceeds 40 reasoning steps.",
        ],
        "sources": {
            "scisolvebench": str(PUBLIC),
            "repro_workspace": "F:/dataset/2604.04930v1/results",
        },
    }
    with open(OUT / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, default=str)
    print("metrics.json written")

    # ---- figures --------------------------------------------------------------
    # Figure 1: accuracy vs avg tokens (scisolve AIME, all methods + CoDE-Stop)
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    for r in scis["c01_baselines"]:
        ax.scatter(r["avg_tokens"], r["accuracy"], marker="o", s=70, label=r["method"])
    ax.scatter(cs["avg_tokens"], cs["accuracy"], marker="*", s=200,
               color="crimson", label="CoDE-Stop (paper hp)")
    ax.set_xlabel("avg reasoning tokens (per rollout)")
    ax.set_ylabel("accuracy")
    ax.set_title("Accuracy vs compute - AIME subset (10 rollouts, frozen data)\nall methods at equal accuracy 0.4")
    ax.legend(fontsize=7, loc="lower right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "fig1_accuracy_vs_compute_scisolve.png", dpi=150)
    plt.close(fig)

    # Figure 2: confidence trajectories correct vs incorrect (scisolve)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    for axx, (label, want_correct) in zip(axes, [("correct", True), ("incorrect", False)]):
        for key, rec in sorted(conf.items()):
            if rec["is_correct"] != want_correct:
                continue
            cseq = rec["confidence_sequence"]
            if not cseq:
                axx.plot([0], [np.nan], alpha=0.0)
                continue
            axx.plot(np.arange(1, len(cseq) + 1), cseq, marker="o", ms=3, lw=1,
                     alpha=0.7, label=f"q{key[0]}r{key[1]}")
        axx.set_xlabel("reasoning step index")
        axx.set_ylabel("confidence")
        axx.set_title(f"{label} trajectories (n={sum(1 for k,r in conf.items() if r['is_correct']==want_correct)})")
        axx.grid(alpha=0.3)
        axx.legend(fontsize=7)
    fig.suptitle("Confidence dynamics (frozen confidence sequences)")
    fig.tight_layout()
    fig.savefig(FIG / "fig2_confidence_trajectories.png", dpi=150)
    plt.close(fig)

    # Figure 3: length distributions (scisolve + repro)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    corr_l = scis["c03_correct_lengths"]
    incorr_l = scis["c03_incorrect_lengths"]
    axes[0].hist([corr_l, incorr_l], bins=range(0, 9000, 1000),
                 label=["correct", "incorrect"], color=["tab:blue", "tab:red"])
    axes[0].set_title("scisolve AIME full-token lengths\n(n=4 correct, 6 incorrect)")
    axes[0].set_xlabel("tokens"); axes[0].legend()
    rc = ac["full_tokens"]["correct"]; ri = ac["full_tokens"]["incorrect"]
    axes[1].bar(["correct\nmean", "incorrect\nmean"], [rc["mean"], ri["mean"]],
                color=["tab:blue", "tab:red"])
    axes[1].set_title("repro all codestop runs - full tokens")
    axes[1].set_ylabel("tokens")
    fig.tight_layout()
    fig.savefig(FIG / "fig3_length_distributions.png", dpi=150)
    plt.close(fig)

    # Figure 4: GPQA & AIME reproduction accuracy-compute tradeoff
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    for axx, ds, rows, base_acc, base_tok in [
        (axes[0], "GPQA", repro["gpqa"]["rows"], repro["gpqa"]["baseline_accuracy"], repro["gpqa"]["baseline_avg_tokens"]),
        (axes[1], "AIME", repro["aime"]["rows"], repro["aime"]["baseline"]["accuracy"], repro["aime"]["baseline"]["avg_tokens"]),
    ]:
        axx.scatter(base_tok, base_acc, marker="s", s=80, color="black", label="baseline (full)")
        for r in rows:
            axx.scatter(r["avg_tokens"], r["accuracy"], marker="o", s=50, label=f"thr={r['confidence_threshold']:.2f}")
        axx.set_xlabel("avg tokens"); axx.set_ylabel("accuracy")
        axx.set_title(f"{ds} (reproduction results, Qwen3-4B)")
        axx.legend(fontsize=6)
        axx.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "fig4_repro_tradeoff.png", dpi=150)
    plt.close(fig)

    print("figures written to", FIG)


if __name__ == "__main__":
    main()
