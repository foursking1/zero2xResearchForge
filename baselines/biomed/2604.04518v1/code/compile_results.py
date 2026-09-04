"""Compile all run results into metrics.json and evidence_table.csv.

Reads:
  * workspace/models/students/*/metrics.json            (C01 students)
  * workspace/results/corrections/*/*.json              (C02/C03 corrections)
  * workspace/results/cfkd/*.json                       (C03 CFKD proxy)
  * workspace/spray_labels/*/metrics_l*.json            (C04 SpRAy quality)

Writes:
  * agent_solution/results/metrics.json
  * agent_solution/results/evidence_table.csv
"""
import csv
import glob
import json
import os

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "results")


def load_jsons(pattern):
    out = []
    for p in sorted(glob.glob(pattern)):
        try:
            out.append(json.load(open(p)))
        except Exception:
            pass
    return out


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    students = load_jsons(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "workspace", "models", "students", "*",
                     "metrics.json"))
    corrections = load_jsons(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "workspace", "results", "corrections", "*",
                     "*.json"))
    cfkd = load_jsons(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "workspace", "results", "cfkd", "*.json"))
    spray = load_jsons(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "workspace", "spray_labels", "*",
                     "metrics_l*.json"))

    metrics = {
        "students": students,
        "corrections": corrections,
        "cfkd": cfkd,
        "spray": spray,
    }
    json.dump(metrics, open(os.path.join(RESULTS_DIR, "metrics.json"), "w"),
              indent=2)

    # evidence table
    rows = []
    for s in students:
        rows.append({
            "metric": "student_test_emp_acc",
            "dataset": s["dataset"], "poison": s["poison"],
            "value": s["test_emp_acc"],
            "definition": "Empirical accuracy of uncorrected ERM student on "
                          "the (balanced) test split",
        })
        rows.append({
            "metric": "student_test_aga",
            "dataset": s["dataset"], "poison": s["poison"],
            "value": s["test_aga"],
            "definition": "Average Group Accuracy (mean of 4 group "
                          "accuracies) of uncorrected student on test",
        })
        rows.append({
            "metric": "student_test_wga",
            "dataset": s["dataset"], "poison": s["poison"],
            "value": s["test_wga"],
            "definition": "Worst Group Accuracy (min of 4 group accuracies) "
                          "of uncorrected student on test",
        })
    for c in corrections:
        rows.append({
            "metric": f"{c['method']}_test_aga",
            "dataset": c["dataset"], "poison": c["poison"],
            "value": c["test_aga"],
            "definition": f"AGA of {c['method']}-corrected model on test "
                          f"(best validation AGA selected)",
        })
        rows.append({
            "metric": f"{c['method']}_test_wga",
            "dataset": c["dataset"], "poison": c["poison"],
            "value": c["test_wga"],
            "definition": f"WGA of {c['method']}-corrected model on test",
        })
    for c in cfkd:
        rows.append({
            "metric": "cfkd_test_aga",
            "dataset": c["dataset"], "poison": c["poison"],
            "value": c["test_aga"],
            "definition": "AGA of CFKD-corrected student on test (tractable "
                          "proxy: confounder-flip counterfactuals + perfect "
                          "oracle + last-layer fine-tune)",
        })
    for sp in spray:
        rows.append({
            "metric": "spray_label_accuracy_mean",
            "dataset": sp["dataset"], "poison": sp["poison"],
            "value": sp["mean_acc"],
            "definition": f"Mean SpRAy confounder-label accuracy over 4 "
                          f"groups (layer {sp['layer']})",
        })
        for gi, gacc in enumerate(sp["per_group_acc"]):
            rows.append({
                "metric": f"spray_label_accuracy_group{gi}",
                "dataset": sp["dataset"], "poison": sp["poison"],
                "value": gacc,
                "definition": f"SpRAy confounder-label accuracy for group "
                              f"{gi} (layer {sp['layer']})",
            })

    with open(os.path.join(RESULTS_DIR, "evidence_table.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=["metric", "dataset", "poison",
                                          "value", "definition"])
        w.writeheader()
        w.writerows(rows)
    print(f"Compiled {len(rows)} evidence rows -> {RESULTS_DIR}")


if __name__ == "__main__":
    main()
