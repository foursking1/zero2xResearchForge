import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, os
df = pd.read_csv("results/means_table.csv")
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, ds in zip(axes, ("creditcard", "jobprofit")):
    d = df[(df.dataset == ds) & (df.setting == "with_prior")]
    d = d.sort_values("f1")
    ax.barh(d.model.str.replace("PARiskRanker", "PA-RiskRanker"), d.f1, color="#4C72B0" if "PA" in "".join(d.model) else "#DDAA33")
    for i, (f1, loss) in enumerate(zip(d.f1, d.financial_loss)):
        ax.text(f1 - 0.004, i, f"{f1:.3f}", va="center", ha="right", fontsize=8)
    ax.set_title(f"with-prior F1 — {ds}")
    ax.set_xlim(0.55, 1.0)
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    for i, (f1, loss) in enumerate(zip(d.f1, d.financial_loss)):
        ax2.text(0.0, i, f"loss={loss:,.0f}", va="center", ha="left", fontsize=7, color="#666")
plt.tight_layout()
os.makedirs("evidence", exist_ok=True)
plt.savefig("evidence/with_prior_f1_compare.png", dpi=150)
print("saved evidence/with_prior_f1_compare.png")
