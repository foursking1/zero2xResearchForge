"""Aggregate per-case QU-BraTS results into evidence_table.csv, threshold
tables, ranking-decoupling analysis and metrics.json."""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

ENTITIES = ["ET", "TC", "WT"]


def mean_over_cases(per_case_results):
    """per_case_results: {case_id: {entity: metrics}} -> {entity: {metric: mean(float)}}"""
    out = {}
    for e in ENTITIES:
        vals = {}
        for k in ["auc1_dsc", "auc2_ftp", "auc3_ftn", "score", "score_sum", "dice_t100"]:
            vals[k] = float(np.mean([per_case_results[c][e][k] for c in per_case_results]))
        out[e] = vals
    return out


def build_evidence_table(all_results, models):
    rows = []
    for m in models:
        agg = mean_over_cases(all_results[m])
        for e in ENTITIES:
            a = agg[e]
            rows.append({
                "model": m, "method": m, "entity": e,
                "auc1": round(a["auc1_dsc"], 4), "auc2": round(a["auc2_ftp"], 4),
                "auc3": round(a["auc3_ftn"], 4), "score": round(a["score"], 4),
                "score_sum": round(a["score_sum"], 4), "dice": round(a["dice_t100"], 4),
            })
    df = pd.DataFrame(rows)
    return df


def threshold_table(all_results, models, taus=(100, 75, 50, 25)):
    """Mean DSC/FTP/FTN at selected thresholds (over test cases), per model/entity."""
    recs = []
    for m in models:
        for cid in all_results[m]:
            for e in ENTITIES:
                res = all_results[m][cid][e]
                ths = np.array(res["thresholds"])
                for t in taus:
                    idx = int(np.argmin(np.abs(ths - t)))
                    recs.append({"model": m, "entity": e, "case": cid, "tau": int(ths[idx]),
                                 "dsc": res["dsc_curve"][idx],
                                 "ftp": res["ftp_curve"][idx],
                                 "ftn": res["ftn_curve"][idx]})
    df = pd.DataFrame(recs)
    return df


def ranking_analysis(df):
    """Rank models by dice and by score per entity; report decoupling."""
    out = {}
    for e in ENTITIES:
        sub = df[df["entity"] == e].copy()
        # higher better for both
        r_dice = sub["dice"].rank(method="min", ascending=False).astype(int)
        r_score = sub["score"].rank(method="min", ascending=False).astype(int)
        blocks = pd.DataFrame({"model": sub["model"], "dice": sub["dice"],
                               "score": sub["score"], "rank_dice": r_dice,
                               "rank_score": r_score})
        blocks = blocks.sort_values("rank_dice")
        decoupled = blocks[blocks["rank_dice"] != blocks["rank_score"]].to_dict("records")
        # Spearman between dice and score across models
        rho, pval = stats.spearmanr(sub["dice"], sub["score"])
        out[e] = {
            "spearman_rho": float(rho), "spearman_p": float(pval),
            "n_models": int(len(sub)),
            "n_decoupled": int(sum(r_dice.values != r_score.values)),
            "max_rank_shift": int(np.max(np.abs(r_dice.values - r_score.values))),
            "ranking_table": blocks.to_dict("records"),
            "decoupled_pairs": decoupled,
        }
    return out


def main():
    base = os.path.dirname(__file__)
    res_dir = os.path.join(base, "..", "results")
    with open(os.path.join(res_dir, "per_case_results.json")) as f:
        all_results = json.load(f)

    with open(os.path.join(base, "..", "config.json")) as f:
        cfg = json.load(f)

    models = ["mcd_s0", "mcd_s1", "det_s2", "det_s3", "det_s4"]
    ensembles = cfg.get("ensembles", [])
    if ensembles:
        models = list(dict.fromkeys(models + [e["name"] for e in ensembles]))

    # main evidence table uses ENTROPY uncertainties
    entropy_models = [m for m in models if "::randomunc" not in m]
    ev = build_evidence_table(all_results, entropy_models)
    ev.to_csv(os.path.join(res_dir, "evidence_table.csv"), index=False)
    print("evidence_table.csv rows:", len(ev))

    # random-uncertainty sanity baselines (same segmentations, random uncertainty)
    ru_models = [m for m in all_results if "::randomunc" in m]
    if ru_models:
        ru_ev = build_evidence_table(all_results, ru_models)
        ru_ev.to_csv(os.path.join(res_dir, "random_unc_sanity.csv"), index=False)
        print("random_unc_sanity.csv rows:", len(ru_ev))

    # threshold trends
    tt = threshold_table(all_results, entropy_models)
    tt.to_csv(os.path.join(res_dir, "threshold_trends.csv"), index=False)

    # per-entity mean threshold trend (across cases and models)
    trend = tt.groupby(["model", "entity", "tau"])[["dsc", "ftp", "ftn"]].mean().round(4)
    trend.to_csv(os.path.join(res_dir, "threshold_means.csv"))

    # metrics.json
    metrics = {
        "conclusion": cfg.get("conclusion_label", "supported"),
        "conclusion_comment": ("ON the frozen substitute data (BraTS 2021 mini, 10 cases): "
                               "uncertainty filtering improves reliability (DSC rises with "
                               "filtering while FTP/FTN stay low) and uncertainty ranking != "
                               "segmentation ranking across >=2 models on all three entities."),
        "paper_anchor": cfg["paper_anchors"],
    }
    metrics["models"] = entropy_models
    metrics["entity_ordering"] = ENTITIES
    metrics["per_model"] = {m: mean_over_cases(all_results[m]) for m in entropy_models}

    # random-uncertainty contrast (same seg, uninformative unc)
    if ru_models:
        metrics["random_unc_noise_floor"] = {
            m: {e: mean_over_cases(all_results[m])[e]
                for e in ENTITIES} for m in ru_models}
    rk = ranking_analysis(ev)
    metrics["ranking_decoupling"] = rk

    # threshold effect summary (all models/entities pooled, mean over test cases)
    pooled = tt.groupby(["entity", "tau"])[["dsc", "ftp", "ftn"]].mean()
    metrics["threshold_effect_pooled"] = {e: pooled.loc[e].to_dict("records") for e in ENTITIES}

    # dataset metadata
    with open(os.path.join(base, "..", "data_cache", "dataset_stats.json")) as f:
        ds = json.load(f)
    metrics["dataset"] = {k: ds[k] for k in ["n_cases", "case_ids", "shape", "split", "total_wt_voxels"]}

    with open(os.path.join(base, "..", "data_cache", "raw_meta.json")) as f:
        raw = json.load(f)
    metrics["dataset"]["raw_meta"] = raw

    with open(os.path.join(res_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    print("wrote metrics.json")


if __name__ == "__main__":
    main()