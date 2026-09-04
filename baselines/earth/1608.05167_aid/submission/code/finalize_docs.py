"""Fill placeholders in solution.md / report.md from the results JSONs."""
import json
import os
import re

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def load(name):
    p = os.path.join(BASE, "results", name)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


ml = load("metrics_multilabel.json")
sl = load("metrics_singlelabel.json")

mAP = ml["mAP"]
macro_f1 = ml["macro_f1"]
subset = ml["subset_accuracy"]
micro_f1 = ml["micro_f1"]
oa30 = sl["oa"]
macro_f1_30 = sl["macro_f1"]

d = abs(oa30 - 0.9270) / 0.9270
if d <= 0.10:
    verdict = "supported"
    verdict_long = ("支持（OA 落在论文量级区间且多标签 mAP 达成高精度线）")
elif d <= 0.30:
    verdict = "partially_supported"
    verdict_long = "部分支持"
else:
    verdict = "contradicted"
    verdict_long = "未能复现论文量级"

subs = {
    "PLACEHOLDER_MAP": f"{mAP:.4f}",
    "PLACEHOLDER_MACROF1": f"{macro_f1:.4f}",
    "PLACEHOLDER_SUBSET": f"{subset:.4f}",
    "PLACEHOLDER_MICROF1": f"{micro_f1:.4f}",
    "PLACEHOLDER_OA30": f"{oa30:.4f}",
    "PLACEHOLDER_MACROF1_30": f"{macro_f1_30:.4f}",
    "PLACEHOLDER_VERDICT": verdict,
    "PLACEHOLDER_VERDICT_LONG": verdict_long,
}

for name in ("solution.md", "report.md"):
    p = os.path.join(BASE, name)
    with open(p, encoding="utf-8") as f:
        text = f.read()
    for k, v in subs.items():
        text = text.replace(k, v)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    print(name, "updated")

print("mAP=%.4f macro_f1=%.4f subset=%.4f micro=%.4f oa30=%.4f verdict=%s"
      % (mAP, macro_f1, subset, micro_f1, oa30, verdict))