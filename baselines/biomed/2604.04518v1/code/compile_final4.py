"""Assemble the final evidence table and metrics JSON consistent with solution.md.

Authoritative sources (matching the numbers cited in agent_solution/solution.md):
  C01 students:    workspace/results/students_all.json          (8 models)
  C02 corrections: workspace/results/corrections/<ds>_<poison>/*.json
                   (ground-truth confounder labels)
  C03 CFKD:        workspace/results/cfkd_final/*.json + workspace/results/cfkd/*.json
                   (deduplicated)
  C04 SpRAy:       workspace/spray_labels/<ds>_<poison>/metrics_l*.json
                   + workspace/results/corrections_spray/<ds>_<poison>/*.json
                   (corrections using SpRAy labels)

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

    # ---------------- C01 students (authoritative list) ----------------
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
        for gi, gacc in enumerate(s["test_group_accs"]):
            rows.append({"metric": "student_test_g%d" % gi, "dataset": ds,
                         "poison": p, "value": gacc,
                         "definition": "Group %d test accuracy of uncorrected "
                                       "student" % gi})

    # ---------------- C02 corrections (ground-truth labels) ----------------
    corrections = []
    for d in list_jsons(os.path.join(WORKSPACE, "results", "corrections",
                                     "*", "*.json")):
        m = d["method"]
        label = "dfr" if m == "dfr" else "gdro" if m == "gdro" \
            else "pclarc" if m in ("pclarc", "p_clarc") \
            else "rrclarc" if m in ("rrclarc", "rr_clarc") else m
        d["method_key"] = label
        corrections.append(d)
    metrics["corrections"] = corrections
    for c in corrections:
        ds, p, m = c["dataset"], c["poison"], c["method_key"]
        rows.append({"metric": f"{m}_test_aga", "dataset": ds, "poison": p,
                     "value": c["test_aga"],
                     "definition": f"AGA of {m}-corrected student on test "
                                   f"(ground-truth labels; best val AGA)"})
        rows.append({"metric": f"{m}_test_wga", "dataset": ds, "poison": p,
                     "value": c["test_wga"],
                     "definition": f"WGA of {m}-corrected student on test"})

    # ---------------- C03 CFKD (deduplicated) ----------------
    cfkd = {}
    for p in sorted(glob.glob(os.path.join(WORKSPACE, "results", "cfkd_final",
                                           "*.json"))) + \
            sorted(glob.glob(os.path.join(WORKSPACE, "results", "cfkd",
                                          "*.json"))):
        d = jload(p)
        if d is None:
            continue
        key = (d.get("dataset"), d.get("poison"))
        if key not in cfkd:          # cfkd_final takes precedence (first)
            cfkd[key] = d
    cfkd = list(cfkd.values())
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
                         "definition": "WGA of CFKD-corrected student"})

    # ---------------- C04 SpRAy labels ----------------
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

    # ---------------- Corrections with SpRAy labels (C04) ----------------
    spray_corr = []
    for d in list_jsons(os.path.join(WORKSPACE, "results", "corrections_spray",
                                     "*", "*.json")):
        m = d["method"]
        d["method_key"] = m
        spray_corr.append(d)
    metrics["corrections_spray"] = spray_corr
    for c in spray_corr:
        ds, p, m = c["dataset"], c["poison"], c["method_key"]
        rows.append({"metric": f"{m}_spray_test_aga", "dataset": ds,
                     "poison": p, "value": c["test_aga"],
                     "definition": f"AGA of {m}-corrected student on test "
                                   f"using SpRAy (auto-clustered) labels"})
        rows.append({"metric": f"{m}_spray_test_wga", "dataset": ds,
                     "poison": p, "value": c["test_wga"],
                     "definition": f"WGA of {m}-corrected student using "
                                   f"SpRAy labels"})

    json.dump(metrics, open(os.path.join(RESULTS_DIR, "metrics.json"), "w"),
              indent=2)
    with open(os.path.join(RESULTS_DIR, "evidence_table.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=["metric", "dataset", "poison",
                                          "value", "definition"])
        w.writeheader()
        w.writerows(rows)
    print(f"Compiled {len(students)} students, {len(corrections)} corrections, "
          f"{len(cfkd)} cfkd, {len(spray)} spray, {len(spray_corr)} "
          f"spray-corrections -> {RESULTS_DIR}")


if __name__ == "__main__":
    main()
