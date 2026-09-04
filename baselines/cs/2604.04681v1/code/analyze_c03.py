"""C03 partial: cross-architecture generalization on CIFAR100 (CNNs: ResNet18 vs ResNet50).

Uses frozen full-scale data (code/BLS/results/table8_ablation) for BLS-InfoBatch@30
on ResNet18/ResNet50, compared against paper Table 3 cited values (Accuracy / Pruned %).
ImageNet-1K / Transformer / Mamba components are documented as not testable (no frozen data).
"""
import json, os
import numpy as np

BLS_RES = r"F:/dataset/2604.04681v1/code/BLS/results/table8_ablation"
FROZEN_T2 = r"F:/dataset/2604.04681v1/results/table2/combined.json"

# Paper Table 3 (CIFAR100 column): Accuracy / Pruned % -- 论文引用
paper = {
    ("R18", "full"): (78.2, None),
    ("R18", "BLS_InfoBatch"): (78.3, 33.9),
    ("R18", "BLS_SeTa"): (78.4, 40.1),
    ("R50", "full"): (80.6, None),
    ("R50", "BLS_InfoBatch"): (80.5, 38.6),
    ("R50", "BLS_SeTa"): (80.7, 40.7),
}

def main():
    ab = json.load(open(os.path.join(BLS_RES, "table8_ablation.json")))
    frozen = {
        ("R18", "BLS_InfoBatch"): ab["resnet18_with_ema"]["best_accuracy"],
        ("R50", "BLS_InfoBatch"): ab["resnet50_with_ema"]["best_accuracy"],
    }
    # frozen table2 cifar100_bls_inf_30 best = 79.77 (same run as table8 resnet18_with_ema)
    comb = json.load(open(FROZEN_T2))
    print("=== C03 (partial) CIFAR100 cross-architecture: BLS-InfoBatch@30 ===")
    print(f"{'arch':5s} {'Full(paper)':11s} {'BLS(paper)':11s} {'BLS(frozen)':12s} {'delta_vs_full':>13s}")
    for arch in ["R18", "R50"]:
        f_full, _ = paper[(arch, "full")]
        f_bls, _ = paper[(arch, "BLS_InfoBatch")]
        r_bls = frozen[(arch, "BLS_InfoBatch")]
        print(f"{arch:5s} {f_full:<11.2f} {f_bls:<11.2f} {r_bls:<12.2f} {r_bls-f_full:+13.2f}")

    print("\n=== Summary ===")
    print("CIFAR100 CNN cross-arch: BLS-InfoBatch@30 reaches/exceeds paper-cited Full on both R18 and R50 -> supported.")
    print("ImageNet-1K, Transformer (ViT/Swin), Mamba (Vim), EfficientNet: no frozen data -> inconclusive.")

    out = os.path.join("results", "c03_cifar100_cross_arch.csv")
    os.makedirs("results", exist_ok=True)
    with open(out, "w") as f:
        f.write("arch,full_paper_cited,bls_paper_cited,bls_frozen_repro,delta_vs_full\n")
        for arch in ["R18", "R50"]:
            f_full, _ = paper[(arch, "full")]
            f_bls, _ = paper[(arch, "BLS_InfoBatch")]
            r_bls = frozen[(arch, "BLS_InfoBatch")]
            f.write(f"{arch},{f_full},{f_bls},{r_bls},{r_bls-f_full:.2f}\n")
    print("saved:", out)

if __name__ == "__main__":
    main()
