"""Build the final evidence table (evidence_table.csv) and machine-readable metrics.json.

This script re-runs the underlying analyses (datasets, reproduction results, rewards) and
merges them with the *paper-reported* values (labelled 论文引用) into a single evidence table.

Columns of evidence_table.csv:
  metric    - stable metric key
  value     - numeric value (str for qualitative cells)
  unit      - unit / denominator of the value
  claim_id  - which TASK.md claim the metric bears on
  source    - "computed_local" (recomputed from frozen data) or "paper_reported" (论文引用)
  note      - caveats / exact definition
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import analyze_datasets
import analyze_reproduction
import analyze_rewards
from common import output_dir

PAPER = {
    "table1": {
        # avg@3 grade (%), std in parentheses, Gemini-3-Pro judge
        "QED-Nano": {"IMO-ProofBench": "40.0 (0.6)", "ProofBench": "44.9 (3.4)", "IMO-AnswerBench": "67.5"},
        "QED-Nano+RSA": {"IMO-ProofBench": "56.9 (5.9)", "ProofBench": "62.6 (4.0)", "IMO-AnswerBench": "76.5"},
        "Qwen3-4B-Thinking-2507": {"IMO-ProofBench": "20.4 (2.6)", "ProofBench": "19.5 (0.9)", "IMO-AnswerBench": "55.8"},
        "DeepSeek-Math-V2(685B)": {"IMO-ProofBench": "57.9 (2.0)", "ProofBench": "60.6 (0.1)", "IMO-AnswerBench": "75.8"},
        "Gemini-3-Pro": {"IMO-ProofBench": "58.7 (2.9)", "ProofBench": "66.7 (3.1)", "IMO-AnswerBench": "83.2"},
    },
    "table2": {  # scaffolds on IMO-ProofBench
        "Single Turn": {"grade": "40.0", "tokens": 93690, "ratio": "1.00x"},
        "Reasoning Cache": {"grade": "44.0", "tokens": 237379, "ratio": "2.53x"},
        "DeepSeek Math": {"grade": "54.0", "tokens": 1605879, "ratio": "17.14x"},
        "RSA": {"grade": "56.9", "tokens": 2045764, "ratio": "21.84x"},
    },
    "fig3": "RL training curves (reward vs step up to ~350) and eval grade vs step - not part of frozen data.",
}


def _g(d: dict, group: str, exp: str) -> dict:
    return d[group][exp]


def main() -> None:
    # ---- regenerate all intermediate analyses ----
    analyze_datasets.main()
    analyze_reproduction.main()
    analyze_rewards.main()

    out_dir = output_dir()
    ds = json.loads((out_dir / "dataset_overview.json").read_text(encoding="utf-8"))
    rep = json.loads((out_dir / "reproduction_metrics.json").read_text(encoding="utf-8"))
    rw = json.loads((out_dir / "fineproofs_rewards.json").read_text(encoding="utf-8"))
    tests = json.loads((out_dir / "reproduction_tests.json").read_text(encoding="utf-8"))

    imo = rep["imo_30shot"]
    cross = rep["cross_dataset"]
    dsm = rep["dsm_wiring_test"]["qed_nano_dsm"]

    # token ratios relative to direct (computed locally)
    direct_tok = imo["qed_nano_direct"]["mean_total_tokens"]
    rc_tok = imo["qed_nano_rc"]["mean_total_tokens"]
    dsm_tok = dsm["mean_total_tokens"]

    rows: list[dict] = []

    def add(metric, value, unit, claim_id, source, note=""):
        rows.append({
            "metric": metric,
            "value": value,
            "unit": unit,
            "claim_id": claim_id,
            "source": source,
            "note": note,
        })

    # ---------------- Datasets ----------------
    add("dataset.imo_proofbench.n_problems", ds["IMOProofBench"]["n_problems"], "count", "C01", "computed_local",
        "Frozen IMOProofBench full set (60 problems)")
    add("dataset.proofbench.n_problems", ds["ProofBench"]["n_all"], "count", "C01", "computed_local",
        "Frozen ProofBench full set (all split)")
    add("dataset.proofbench.n_24_25", ds["ProofBench"]["n_24_25"], "count", "C01", "computed_local")
    add("dataset.proofbench.n_other", ds["ProofBench"]["n_other"], "count", "C01", "computed_local")
    add("dataset.fineproofs_sft.n_examples", ds["FineProofs-SFT"]["n_examples"], "count", "C04", "computed_local")
    add("dataset.fineproofs_rl.n_rows", ds["FineProofs-RL"]["n_rows"], "count", "C04", "computed_local")
    add("dataset.fineproofs_rl.total_rollout_rewards", rw["FineProofs-RL"]["total_rollout_rewards"], "count", "C04",
        "computed_local")

    # ---------------- C01: QED-Nano base (no scaffold) ----------------
    add("C01.imo_proofbench.paper_grade_pct", PAPER["table1"]["QED-Nano"]["IMO-ProofBench"], "avg@3 grade % (std)",
        "C01", "paper_reported", "论文 Table 1, Gemini-3-Pro judge")
    add("C01.proofbench.paper_grade_pct", PAPER["table1"]["QED-Nano"]["ProofBench"], "avg@3 grade % (std)",
        "C01", "paper_reported", "论文 Table 1")
    add("C01.imo_answerbench.paper_grade_pct", PAPER["table1"]["QED-Nano"]["IMO-AnswerBench"], "grade %",
        "C01", "paper_reported", "论文 Table 1; IMOAnswerBench dataset NOT in frozen snapshot")
    # local reproduction
    add("C01.imo_proofbench.local_mean_score", f"{imo['qed_nano_direct']['mean_score']:.3f}",
        "score / 7 (local Qwen2.5-1.5B judge)", "C01", "computed_local",
        "IMOProofBench first 30 problems x3 seeds (n=90); completion capped at 1024 tokens")
    add("C01.proofbench.local_mean_score", f"{cross['qed_nano_direct']['mean_score']:.3f}",
        "score / 7 (local judge)", "C01", "computed_local",
        "ProofBench first 15 problems x3 seeds (n=45)")
    add("C01.imo_answerbench.local_mean_score", "NA", "score / 7", "C01", "computed_local",
        "IMOAnswerBench not present in frozen snapshot")

    # ---------------- C02: QED-Nano + RSA scaffold ----------------
    add("C02.imo_proofbench.paper_grade_pct", PAPER["table1"]["QED-Nano+RSA"]["IMO-ProofBench"],
        "avg@3 grade % (std)", "C02", "paper_reported", "论文 Table 1 (RSA scaffold)")
    add("C02.proofbench.paper_grade_pct", PAPER["table1"]["QED-Nano+RSA"]["ProofBench"],
        "avg@3 grade % (std)", "C02", "paper_reported")
    add("C02.imo_answerbench.paper_grade_pct", PAPER["table1"]["QED-Nano+RSA"]["IMO-AnswerBench"],
        "grade %", "C02", "paper_reported")
    add("C02.imo_proofbench.local_rc_proxy_mean_score", f"{imo['qed_nano_rc']['mean_score']:.3f}",
        "score / 7 (local judge)", "C02", "computed_local",
        "RSA scaffold NOT implemented; Reasoning-Cache used as closest proxy")
    add("C02.imo_proofbench.local_rc_proxy_mean_tokens", f"{rc_tok:.1f}", "tokens/problem", "C02", "computed_local")

    # ---------------- C03: scaffold comparison ----------------
    for name in ("Single Turn", "Reasoning Cache", "DeepSeek Math", "RSA"):
        v = PAPER["table2"][name]
        add(f"C03.{name}.paper_grade_pct", v["grade"], "avg grade %", "C03", "paper_reported",
            "论文 Table 2 (IMO-ProofBench)")
        add(f"C03.{name}.paper_avg_tokens", v["tokens"], "tokens/problem", "C03", "paper_reported")
        add(f"C03.{name}.paper_token_ratio", v["ratio"], "x single turn", "C03", "paper_reported")
    # local computed scaffold comparison
    local_scaffolds = [
        ("Single Turn (direct)", imo["qed_nano_direct"]["mean_score"], direct_tok, 1.0),
        ("Reasoning Cache (RC)", imo["qed_nano_rc"]["mean_score"], rc_tok, rc_tok / direct_tok),
        ("DeepSeek Math (DSM)", dsm["mean_score"], dsm_tok, dsm_tok / direct_tok),
    ]
    for name, score, tok, ratio in local_scaffolds:
        add(f"C03.local.{name}.mean_score", f"{score:.3f}", "score / 7", "C03", "computed_local",
            "IMOProofBench, local judge; DSM is a 1-example wiring test")
        add(f"C03.local.{name}.mean_tokens", f"{tok:,.1f}", "tokens/problem", "C03", "computed_local")
        add(f"C03.local.{name}.token_ratio", f"{ratio:.2f}x", "x direct", "C03", "computed_local")

    # ---------------- C04: RL training reward ----------------
    add("C04.rl.reward_mean_distribution", (
        f"mean={rw['FineProofs-RL']['per_problem_reward_mean_distribution']['mean']:.4f}, "
        f"median={rw['FineProofs-RL']['per_problem_reward_mean_distribution']['median']:.4f}"),
        "reward units", "C04", "computed_local",
        "FineProofs-RL per-problem mean rollout reward (rubric-based, n=128 rollouts/prob)")
    add("C04.rl.frac_problems_positive_reward",
        f"{rw['FineProofs-RL']['frac_problems_with_positive_mean_reward']:.4f}",
        "fraction", "C04", "computed_local")
    add("C04.rl.rubric_present", rw["FineProofs-RL"]["rubric_coverage"], "bool", "C04", "computed_local",
        "All FineProofs-RL rows carry a generated rubric")
    add("C04.training_curve.available", rw["temporal_training_curve"]["available_in_frozen_data"],
        "bool", "C04", "computed_local",
        "No step-level training log in frozen data; paper Fig.3 curve not reproducible")
    add("C04.sft.grade7_fraction", f"{ds['FineProofs-SFT']['grade_7_fraction']:.3f}", "fraction", "C04",
        "computed_local", "FineProofs-SFT mostly high-grade reference proofs (Gemini-3-Pro grade)")

    # ---------------- Relative ordering (QED-Nano vs Qwen3-4B) ----------------
    add("REL.imo_proofbench.qwen3_vs_qednano.diff",
        f"{tests['imo_30shot']['tests'][0]['mean_diff_a_minus_b']:+.4f}",
        "points (qwen3 - qednano)", "C01", "computed_local",
        "Positive = Qwen3 higher on local judge; paired t-test p=%.4f" %
        tests["imo_30shot"]["tests"][0]["paired_ttest_p"])
    add("REL.proofbench.qwen3_vs_qednano.diff",
        f"{tests['cross_dataset']['tests'][0]['mean_diff_a_minus_b']:+.4f}",
        "points (qwen3 - qednano)", "C01", "computed_local")
    # tests[2] = (qed_nano_direct, qed_nano_rc), diff = direct - rc; we want rc - direct
    rc_direct_diff = -tests["imo_30shot"]["tests"][2]["mean_diff_a_minus_b"]
    rc_direct_p = tests["imo_30shot"]["tests"][2]["paired_ttest_p"]
    add("REL.imo_proofbench.rc_vs_direct.diff",
        f"{rc_direct_diff:+.4f}",
        "points (rc - direct)", "C03", "computed_local",
        "Positive = RC higher; paired t-test p=%.4f" % rc_direct_p)

    # ---------------- write CSV ----------------
    import csv
    out_csv = out_dir / "evidence_table.csv"
    with out_csv.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=["metric", "value", "unit", "claim_id", "source", "note"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # ---------------- write metrics.json ----------------
    metrics = {"paper_id": "2604.04898v1", "task_claims": {"C01": {}, "C02": {}, "C03": {}, "C04": {}}}
    for r in rows:
        claim = r["claim_id"]
        if claim in metrics["task_claims"]:
            metrics["task_claims"][claim][r["metric"]] = {
                "value": r["value"],
                "unit": r["unit"],
                "source": r["source"],
                "note": r["note"],
            }
    # also include the aggregated reproduction stats and test results
    metrics["reproduction_metrics"] = rep
    metrics["reproduction_tests"] = tests
    metrics["dataset_overview"] = ds
    metrics["fineproofs_rewards"] = rw
    out_json = out_dir / "metrics.json"
    out_json.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote {out_csv} ({len(rows)} rows)")
    print(f"Wrote {out_json}")
    print("\nEvidence rows:")
    for r in rows:
        print(f"  [{r['claim_id']:>3}|{r['source'][:5]:>5}] {r['metric']:<55} = {r['value']}")


if __name__ == "__main__":
    main()
