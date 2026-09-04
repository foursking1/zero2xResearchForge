"""Result analysis: paired bootstrap CI, evidence table, metrics.json, claim verdict.

Reader-friendly entrypoint:
    python analyze.py                    # uses results/raw_evals.csv
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

from config import BOOTSTRAP_SEED, EVIDENCE_DIR, N_BOOTSTRAP, RESULT_DIR, SEEDS

PAPER = {
    "baseline_ood_auc": 0.9774,
    "complexity": dict(delta=+0.0060, ci=[0.0023, 0.0102]),
    "strain": dict(delta=+0.0032, ci=[0.0008, 0.0052]),
    "both": dict(delta=+0.0066, ci=[0.0038, 0.0093]),
}


def paired_bootstrap(deltas, alpha=0.05, n_resample=N_BOOTSTRAP):
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    d = np.asarray(deltas, dtype=float)
    samples = rng.choice(d, size=(n_resample, len(d)), replace=True).mean(axis=1)
    lo, hi = np.percentile(samples, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi), samples


def main(evals_csv=None):
    evals_csv = evals_csv or os.path.join(RESULT_DIR, "raw_evals.csv")
    df = pd.read_csv(evals_csv)
    df = df.sort_values(["variant", "seed"]).reset_index(drop=True)

    baselines = df[df["variant"] == "baseline"].set_index("seed")["ood_auc"]
    rows = []
    variant_stats = {}
    for v, g in df.groupby("variant"):
        for _, r in g.iterrows():
            delta = float(r["ood_auc"] - baselines[r["seed"]])
            rows.append(dict(variant=v, seed=r["seed"], ood_auc=float(r["ood_auc"]),
                             delta=delta, ci_low=np.nan, ci_high=np.nan))
        mean_auc = float(g["ood_auc"].mean())
        if v == "baseline":
            variant_stats[v] = dict(mean_ood_auc=mean_auc, delta=0.0, ci_low=0.0, ci_high=0.0,
                                    ci_excludes_zero=False)
        else:
            deltas = (g.set_index("seed")["ood_auc"] - baselines).values
            lo, hi, _ = paired_bootstrap(deltas)
            mean_d = float(np.mean(deltas))
            variant_stats[v] = dict(mean_ood_auc=mean_auc, delta=round(mean_d, 6),
                                    ci_low=round(lo, 6), ci_high=round(hi, 6),
                                    ci_excludes_zero=bool(lo > 0 or hi < 0))

    ev = pd.DataFrame(rows)
    # fill per-variant CI on each row of that variant
    for v, st in variant_stats.items():
        ev.loc[ev["variant"] == v, "ci_low"] = st["ci_low"]
        ev.loc[ev["variant"] == v, "ci_high"] = st["ci_high"]
    ev.to_csv(os.path.join(EVIDENCE_DIR, "evidence_table.csv"), index=False)
    ev.to_csv(os.path.join(RESULT_DIR, "evidence_table.csv"), index=False)

    # ---- label distribution (A3)
    label_csv = os.path.join(RESULT_DIR, "label_stats.json")
    lab = json.load(open(label_csv)) if os.path.exists(label_csv) else {}
    label_anchor = None
    if lab.get("corpus_easy_frac"):
        frac_ours = lab["corpus_easy_frac"]
        frac_paper = 53159 / 65177  # 0.8156
        label_anchor = dict(paper="53,159/12,018 (81.6% easy)", ours="%d/%d (%.1f%% easy)" %
                            (lab["total_easy"], lab["total_hard"], 100 * frac_ours),
                            ours_frac=frac_ours, paper_frac=round(frac_paper, 4),
                            rel_diff=round(abs(frac_ours - frac_paper) / frac_paper, 4),
                            within_15pct=bool(abs(frac_ours - frac_paper) / frac_paper <= 0.15))

    # ---- verdicts vs anchors
    rel_diff = abs(variant_stats["baseline"]["mean_ood_auc"] - PAPER["baseline_ood_auc"]) / PAPER["baseline_ood_auc"]
    anchor = {"baseline": dict(paper=PAPER["baseline_ood_auc"],
                               ours=round(variant_stats["baseline"]["mean_ood_auc"], 5),
                               rel_diff=round(rel_diff, 5))}
    for v, st in variant_stats.items():
        if v == "baseline":
            a_ok = rel_diff <= 0.05
            a_label = "supports (A1)" if a_ok else ("partially" if rel_diff <= 0.15 else "weak/no")
            anchor[v].update(direction=None, ci_excludes_zero=None, verdict=a_label)
            continue
        p = PAPER[v]
        direction_ok = st["delta"] > 0
        ci_ok = st["ci_excludes_zero"]
        anchor[v] = dict(paper_delta=p["delta"], paper_ci=[p["ci"][0], p["ci"][1]],
                         ours_delta=st["delta"], ours_ci=[st["ci_low"], st["ci_high"]],
                         direction_positive=direction_ok,
                         ci_excludes_zero=ci_ok,
                         matches_paper_sign=bool(np.sign(st["delta"]) == np.sign(p["delta"])))
    # overall conclusion
    a1_ok = rel_diff <= 0.05
    a2_variants = [v for v in ("complexity", "strain", "both") if v in variant_stats]
    a2_any_pos_ci = any(variant_stats[v]["ci_excludes_zero"] and variant_stats[v]["delta"] > 0
                        for v in a2_variants)
    a2_all_reported = all(variant_stats[v]["delta"] > 0 for v in a2_variants)
    if a1_ok and a2_any_pos_ci and a2_all_reported:
        conclusion = "supported"
    elif rel_diff <= 0.15 and (a2_any_pos_ci or not a2_variants):
        conclusion = "partially_supported"
    elif rel_diff > 0.15 and not a2_any_pos_ci:
        conclusion = "contradicted"
    else:
        conclusion = "inconclusive"

    meta = dict(
        corpus=lab,
        label_anchor=label_anchor,
        baseline=dict(mean_ood_auc=round(variant_stats["baseline"]["mean_ood_auc"], 5),
                      paper=0.9774, rel_diff=round(rel_diff, 5), auc_ok_5pct=bool(rel_diff <= 0.05)),
        variants={v: {**st, "paper": PAPER[v] if v != "baseline" else None}
                  for v, st in variant_stats.items()},
        anchor_comparison=anchor,
        conclusion=conclusion,
        bootstrap=dict(n_resample=N_BOOTSTRAP, alpha=0.05, units="bootstrapped mean of per-seed paired deltas"),
    )
    with open(os.path.join(RESULT_DIR, "metrics.json"), "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    print("\nConclusion:", conclusion)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--evals", default=None)
    a = ap.parse_args()
    main(a.evals)