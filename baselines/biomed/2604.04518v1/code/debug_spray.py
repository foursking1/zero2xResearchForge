"""Debug SpRAy attribution/clustering quality for squares symmetric (R08)."""
import numpy as np
import torch
from sklearn.cluster import KMeans, SpectralClustering
from sklearn.metrics import accuracy_score

from config import SEED, WORKSPACE
from corrections import load_split, split_root
from models import make_resnet18
from spray import attributions

def main():
    root = split_root("squares", "symmetric")
    train, val, test = load_split(root)
    model = make_resnet18(2, SEED)
    model.load_state_dict(torch.load(
        os.path.join(WORKSPACE, "models", "students",
                     "squares_symmetric", "best.pt"), weights_only=False))
    x = torch.cat([train["images"], val["images"]])
    targets = torch.cat([train["targets"], val["targets"]])
    groups = torch.cat([train["groups"], val["groups"]])
    t = targets.numpy(); g = groups.numpy(); q_true = g % 2

    for layer in (4, 6, 8, 10, 12):
        attr, preds = attributions(model, x, layer)
        # feature norm per sample
        norms = np.linalg.norm(attr, axis=1)
        print(f"\n=== layer {layer} attr shape {attr.shape} ===")
        for grp in range(4):
            mask = g == grp
            if mask.sum() == 0:
                continue
            print(f"  grp{grp} n={mask.sum()} mean_norm={norms[mask].mean():.4f} "
                  f"std_norm={norms[mask].std():.4f} pred_acc="
                  f"{(preds[mask]==t[mask]).mean():.3f}")
        # per-class q separability
        for cl in np.unique(t):
            idx = np.where(t == cl)[0]
            a = attr[idx]
            qc = q_true[idx]
            if qc.sum() == 0 or qc.sum() == len(qc):
                continue
            # 2-means on z-scored features
            from sklearn.preprocessing import StandardScaler
            a_z = StandardScaler().fit_transform(a)
            km = KMeans(n_clusters=2, random_state=SEED, n_init=10)
            lab = km.fit_predict(a_z)
            # map clusters to q by majority
            if qc[lab == 0].mean() >= 0.5:
                acc = max((lab == 0).mean(), (lab == 1).mean())
            else:
                acc = 0
            # actually compute label accuracy as in spray
            q_hat = np.zeros_like(qc)
            for c in np.unique(lab):
                sub = lab == c
                q_hat[sub] = 1 if qc[sub].mean() >= 0.5 else 0
            print(f"  class {cl}: kmeans q-label acc = "
                  f"{accuracy_score(qc, q_hat):.3f}  cluster sizes="
                  f"{[int((lab==c).sum()) for c in np.unique(lab)]}")

if __name__ == "__main__":
    import os
    main()
