"""Assemble final evidence table and metrics JSON for the C01-C05 judgments.

Sources:
  C01 students:    workspace/results/students_all.json
  C02 corrections: workspace/results/corrections/<ds>_<poison>/*.json (GT labels)
  C03 CFKD:        workspace/results/cfkd/*.json
  C04 spray corr.: workspace/results/corrections_spray/<ds>_<poison>/*.json
  C05 spray labels: workspace/spray_labels/<ds>_<poison>/metrics_l*.json

Writes agent_solution/results/metrics.json and evidence_table.csv
(rows are atomic metrics, one per metric/dataset/poison).
"""
import csv
import glob
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.join(BASE, "..", "workspace")
RESULTS_DIR = os.path.join(BASE, "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def jload(path):
    try:
        return json.load(open(path))
    except Exception:
        return None


def list_jsons(pattern):
    out = []
    for p in sorted(glob.glob(pattern)):
        d = jload(p)
        if d is not None:
            out.append(d)
    return out


def main():
    rows = []
    metrics = {}

    # ---------------- C01 students ----------------
    students = jload(os.path.join(WORKSPACE, "results", "students_all.json")) or []
    metrics["students"] = students
    for s in students:
        ds, p = s["dataset"], s["poison"]
        rows.append({"metric": "student_test_emp_acc", "dataset": ds,
                     "poison": p, "value": s["test_emp_acc"],
                     "definition": "Empirical accuracy of uncorrected ERM "
                                   "student on balanced test split"})
        rows.append({"metric": "student_test_aga", "dataset": ds,
                     "poison": p, "value": s["test_aga"],
                     "definition": "Average Group Accuracy of uncorrected "
                                   "student on test"})
        rows.append({"metric": "student_test_wga", "dataset": ds,
                     "poison": p, "value": s["test_wga"],
                     "definition": "Worst Group Accuracy of uncorrected "
                                   "student on test"})

    # ---------------- C02/C03 corrections ----------------
    corrections = list_jsons(os.path.join(WORKSPACE, "results", "corrections",
                                          "*", "*.json"))
    metrics["corrections"] = corrections
    for c in corrections:
        ds, p, m = c["dataset"], c["poison"], c["method"]
        rows.append({"metric": f"{m}_test_aga", "dataset": ds, "poison": p,
                     "value": c["test_aga"],
                     "definition": f"AGA of {m}-corrected student on test "
                                   f"(best val AGA selected; ground-truth "
                                   f"labels)"})
        if "test_wga" in c:
            rows.append({"metric": f"{m}_test_wga", "dataset": ds,
                         "poison": p, "value": c["test_wga"],
                         "definition": f"WGA of {m}-corrected student on test "
                                       f"(ground-truth labels)"})

    # ---------------- C03 CFKD ----------------
    cfkd = list_jsons(os.path.join(WORKSPACE, "results", "cfkd", "*.json"))
    metrics["cfkd"] = cfkd
    for c in cfkd:
        ds, p = c["dataset"], c["poison"]
        rows.append({"metric": "cfkd_test_aga", "dataset": ds, "poison": p,
                     "value": c["test_aga"],
                     "definition": "AGA of CFKD-corrected student on test "
                                   "(tractable proxy: confounder-flip "
                                   "counterfactuals + perfect oracle + "
                                   "last-layer fine-tune; no group labels)"})
        if "test_wga" in c:
            rows.append({"metric": "cfkd_test_wga", "dataset": ds,
                         "poison": p, "value": c["test_wga"],
                         "definition": "WGA of CFKD-corrected student on test "
                                       "(tractable proxy)"})

    # ---------------- C04 corrections with SpRAy labels ----------------
    spray_corr = list_jsons(os.path.join(WORKSPACE, "results",
                                         "corrections_spray", "*", "*.json"))
    metrics["spray_corrections"] = spray_corr
    for c in spray_corr:
        ds, p, m = c["dataset"], c["poison"], c["method"]
        rows.append({"metric": f"spray_{m}_test_aga", "dataset": ds,
                     "poison": p, "value": c["test_aga"],
                     "definition": f"AGA of {m}-corrected student on test "
                                   f"using SpRAy-derived group labels "
                                   f"(layer {c.get('spray_layer')})"})
        if "test_wga" in c:
            rows.append({"metric": f"spray_{m}_test_wga", "dataset": ds,
                         "poison": p, "value": c["test_wga"],
                         "definition": f"WGA of {m}-corrected student using "
                                       f"SpRAy labels (layer "
                                       f"{c.get('spray_layer')})"})

    # ---------------- C05 SpRAy labels ----------------
    spray = list_jsons(os.path.join(WORKSPACE, "spray_labels", "*",
                                    "metrics_l*.json"))
    metrics["spray"] = spray
    for sp in spray:
        ds, p = sp["dataset"], sp["poison"]
        rows.append({"metric": f"spray_label_acc_mean_l{sp['layer']}",
                     "dataset": ds, "poison": p, "value": sp["mean_acc"],
                     "definition": "Mean SpRAy confounder-label accuracy over "
                                   "4 groups (layer %d)" % sp["layer"]})
        for gi, gacc in enumerate(sp["per_group_acc"]):
            rows.append({"metric": f"spray_label_acc_g{gi}_l{sp['layer']}",
                         "dataset": ds, "poison": p, "value": gacc,
                         "definition": "SpRAy confounder-label accuracy for "
                                       "group %d (layer %d)" % (gi, sp["layer"])})

    json.dump(metrics, open(os.path.join(RESULTS_DIR, "metrics.json"), "w"),
              indent=2)
    with open(os.path.join(RESULTS_DIR, "evidence_table.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=["metric", "dataset", "poison",
                                          "value", "definition"])
        w.writeheader()
        w.writerows(rows)
    print(f"Compiled {len(students)} students, {len(corrections)} corrections, "
          f"{len(cfkd)} cfkd, {len(spray_corr)} spray-corrections, "
          f"{len(spray)} spray-label sets -> {RESULTS_DIR}")


if __name__ == "__main__":
    main()
