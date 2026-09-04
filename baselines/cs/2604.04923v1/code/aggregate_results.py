"""Aggregate per-claim result JSONs into the final deliverables.

Reads results/c01_c02_room_corridor.json, c03_hourglass.json,
c03b_embeddings_vgtdot.json, c04_drl_agent.json and writes:

  * results/evidence_table.csv  - columns: metric, value, definition
  * results/metrics.json        - machine-readable {metric: {value, definition}}

Values are read directly from the computed JSONs (no transcription); only the
definitions are authored here.  Paper-cited values are labelled "论文引用".
"""
import os
import json
import csv

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(HERE), "results")


def load(name):
    with open(os.path.join(OUT_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


c12 = load("c01_c02_room_corridor.json")
c3 = load("c03_hourglass.json")
c3b = load("c03b_embeddings_vgtdot.json")
c4 = load("c04_drl_agent.json")

# Each row: (metric, value, definition)
M = []


def add(metric, value, definition):
    # round floats to a stable 6-dp display (ints/bools/strings untouched)
    if isinstance(value, float):
        value = round(value, 6)
    elif isinstance(value, list) and value and all(isinstance(x, float) for x in value):
        value = [round(x, 6) for x in value]
    M.append((metric, value, definition))


# ---------------- C01 : VGT local dimension room vs corridor ----------------
ld = c12["local_dim"]
add("c01_room_ld_mean", ld["room_ld_mean"],
    "VGT local intrinsic dimension (OLS slope of log-volume vs log-radius over r in [0.03,0.16]) averaged over room points; paper Fig.5 predicts ~2")
add("c01_corridor_ld_mean", ld["corr_ld_mean"],
    "Same VGT local dimension averaged over corridor points; paper Fig.5 predicts ~1")
add("c01_dim_drop", ld["dim_drop"],
    "room_ld_mean - corridor_ld_mean (2D->1D drop)")
add("c01_room_ld_median", ld["room_ld_median"], "median local dim, room points")
add("c01_corridor_ld_median", ld["corr_ld_median"], "median local dim, corridor points")
add("c01_ld_fit_window_lo", 0.03, "lower radius of the local-dim fit window")
add("c01_ld_fit_window_hi", 0.16, "upper radius of the local-dim fit window")
add("c01_paper_room_dim", 2, "论文引用: paper Fig.5 room stratum intrinsic dimension ~2")
add("c01_paper_corridor_dim", 1, "论文引用: paper Fig.5 corridor stratum intrinsic dimension ~1")

# ---------------- C02 : VGT probe curves ----------------
pr = c12["probe"]
add("c02_slope_small_a", pr["slopes_small"]["a"],
    "small-radius VGT curve slope at probe point a (room-corridor junction); paper ~2")
add("c02_slope_small_b", pr["slopes_small"]["b"],
    "small-radius VGT curve slope at probe point b (room centre); paper ~2")
add("c02_slope_small_c", pr["slopes_small"]["c"],
    "small-radius VGT curve slope at probe point c (corridor middle minimum); paper ~1")
add("c02_transition_radius_c", pr["transition_radius_c"],
    "radius (geometric mean of log-grid segment) at which probe c's segment slope exceeds 1.5, i.e. the 1D->2D transition; paper ~0.3")
add("c02_paper_transition_radius", 0.3, "论文引用: paper states transition radius r ~ 0.3 for corridor point c")

# ---------------- C03 : hourglass DIC / VGT-dot / HADES ----------------
had = c3["hades"]
add("c03_hades_f1", had["f1"], "best binary F1 of HADES-inspired singularity score vs junction ground truth (threshold swept)")
add("c03_hades_precision", had["precision"], "precision at best-F1 threshold")
add("c03_hades_recall", had["recall"], "recall at best-F1 threshold")
add("c03_hades_best_threshold", had["best_threshold"], "score threshold giving best F1")
add("c03_hades_n_flagged", had["n_flagged"], "points flagged by HADES at best threshold")
add("c03_hades_n_true_junction", had["n_true_junction"], "ground-truth junction points")
add("c03_hades_score_junction_mean", had["score_junction_mean"], "mean HADES score over junction points")
add("c03_hades_score_lobe_mean", had["score_lobe_mean"], "mean HADES score over lobe points")
add("c03_hades_score_neck_mean", had["score_neck_mean"], "mean HADES score over neck points")
add("c03_hades_junction_over_lobe_ratio",
    had["score_junction_mean"] / had["score_lobe_mean"],
    "junction mean score / lobe mean score (multiscale dimension-change signature)")
add("c03_dic_junction_ld_mean", c3["feature_summary"]["junction"]["dic_mean"],
    "DIC local-dim feature at junction points (small-scale VGT slope)")
add("c03_dic_neck_ld_mean", c3["feature_summary"]["neck"]["dic_mean"],
    "DIC local-dim feature at neck points")
add("c03_dic_junction_f1_3clusters", c3["dic_3clusters"]["junction_f1"],
    "DIC k=3: F1 of the cluster containing most junction points (junction absorbed into neck)")
add("c03_dic_ari_3clusters", c3["dic_3clusters"]["ari_vs_3group_gt"],
    "DIC k=3: adjusted rand index vs 3-group ground truth")
add("c03_vgtdot_ari_2clusters", c3["vgt_dot_2clusters"]["ari_vs_3group_gt"],
    "VGT-dot curve k=2: ARI vs 3-group ground truth (lobe vs neck separation)")
add("c03_vgtdot_ari_3clusters", c3["vgt_dot_3clusters"]["ari_vs_3group_gt"],
    "VGT-dot curve k=3: ARI vs 3-group ground truth")
add("c03_vgtdot_junction_f1_3clusters", c3["vgt_dot_3clusters"]["junction_f1"],
    "VGT-dot curve k=3: F1 of the cluster containing most junction points")

# ---------------- C03b : real token embeddings ----------------
add("c03b_n_embeddings", c3b["n_embeddings"], "number of token embeddings analysed")
add("c03b_embedding_dim", c3b["embedding_dim"], "token embedding dimension (paper: 256)")
add("c03b_embedding_shape", f"{c3b['n_embeddings']}x{c3b['embedding_dim']}",
    "actual embedding matrix shape")
add("c03b_paper_embedding_shape", "~48500x256",
    "论文引用: paper/claim spec C10 expects 250 trajectories x 194 steps = ~48500 256-d embeddings")
add("c03b_scalar_vgtdot_std", c3b["scalar_vgt_dot"]["std"],
    "std of the frozen scalar VGT-dot feature (mean derivative); near-constant -> not discriminative")
add("c03b_scalar_vgtdot_mean", c3b["scalar_vgt_dot"]["mean"], "mean of the frozen scalar VGT-dot feature")
add("c03b_local_dim_global_mean", c3b["local_dim_global_mean"],
    "mean VGT local intrinsic dimension over all embeddings (corrected VGT)")
add("c03b_vgtdot_ari_vs_frozen", c3b["ari_vs_frozen_clusters"],
    "ARI between corrected VGT-dot curve k-means and frozen cluster labels")
add("c03b_early_cluster_jaccard", c3b["early_cluster_overlap"]["jaccard"],
    "Jaccard overlap of the corrected VGT-dot early-time cluster with frozen cluster 1 (n=60, t<=9)")

# ---------------- C04 : trained DRL agent ----------------
ck = c4["checkpoint"]
ev = c4["evaluation"]
ad = c4["action_distribution"]
add("c04_model_params", ck["n_model_params"], "number of parameters in the PPOActorCritic model")
add("c04_config_model_params", ck["config_model_params"], "model_params recorded in results/config.json")
add("c04_params_match_config", ck["params_match_config"], "model parameter count matches config")
add("c04_checkpoint_valid", ck["exists"], "checkpoint_final.pt loads and matches architecture")
add("c04_training_steps", c4["training_stats_reported"]["total_steps"],
    "actual training steps in reproduction (config total_steps)")
add("c04_training_episodes", c4["training_stats_reported"]["total_episodes"],
    "episodes completed in the reproduction run")
add("c04_paper_training_steps", 500000,
    "论文引用: paper / claim spec C03 targets ~500000 training steps")
add("c04_reported_avg_reward", c4["training_stats_reported"]["avg_reward"],
    "reported avg reward in training_stats.json (= terminal STL robustness, see next row)")
add("c04_reported_avg_stl", c4["training_stats_reported"]["avg_stl_robustness"],
    "reported avg STL robustness in training_stats.json")
add("c04_checkpoint_rewards_equal_stl", ck["episode_rewards_identical_to_episode_stl"],
    "checkpoint episode_rewards list is identical to episode_stl_robustness (logged reward == terminal STL)")
add("c04_saved_episode_stl_mean", ck["saved_episode_stl_mean"],
    "mean of per-episode STL robustness saved in checkpoint (range [0.4,1.0])")
add("c04_trained_greedy_stl", ev["trained_greedy"]["mean_stl_robustness"],
    "mean terminal STL robustness, trained policy greedy, 100 episodes shared starts")
add("c04_trained_sampling_stl", ev["trained_sampling"]["mean_stl_robustness"],
    "mean terminal STL robustness, trained policy sampling, 100 episodes shared starts")
add("c04_random_stl", ev["random_policy"]["mean_stl_robustness"],
    "mean terminal STL robustness, random policy, 100 episodes shared starts")
add("c04_trained_vs_random_stl_gap", ev["trained_greedy_vs_random_stl_gap"],
    "trained greedy mean STL - random mean STL (negative = trained worse)")
add("c04_trained_greedy_success_ge095", ev["trained_greedy"]["success_rate_ge095"],
    "fraction of trained-greedy episodes with STL robustness >= 0.95")
add("c04_random_success_ge095", ev["random_policy"]["success_rate_ge095"],
    "fraction of random-policy episodes with STL robustness >= 0.95")
add("c04_trained_greedy_shaped_reward", ev["trained_greedy"]["mean_shaped_reward"],
    "mean per-step shaped distance reward, trained greedy")
add("c04_random_shaped_reward", ev["random_policy"]["mean_shaped_reward"],
    "mean per-step shaped distance reward, random")
add("c04_trained_vs_random_shaped_gap", ev["trained_greedy_vs_random_shaped_gap"],
    "trained greedy shaped reward - random shaped reward")
add("c04_action_entropy_mean", ad["mean_entropy"],
    "mean action-distribution entropy of trained policy over 300 random observations (max log(9)=2.197)")
add("c04_action_argmax_dominant", ad["argmax_dominant_action"],
    "action with the most argmax selections (near-deterministic policy, e.g. single-axis walking)")
add("c04_mean_action_probs", ad["mean_action_probs"],
    "mean action probability vector of the trained policy over 300 random observations")

# ---------------- write files ----------------
# CSV
csv_path = os.path.join(OUT_DIR, "evidence_table.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["metric", "value", "definition"])
    for metric, value, definition in M:
        if isinstance(value, (list, dict)):
            vstr = json.dumps(value)
        elif isinstance(value, bool):
            vstr = "true" if value else "false"
        elif value is None:
            vstr = ""
        else:
            vstr = str(value)
        w.writerow([metric, vstr, definition])
print("wrote", csv_path)

# JSON (machine-readable, keys == CSV metric names)
metrics_json = {}
for metric, value, definition in M:
    metrics_json[metric] = {"value": value, "definition": definition}
json_path = os.path.join(OUT_DIR, "metrics.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(metrics_json, f, indent=2)
print("wrote", json_path)
print("total metrics:", len(M))
