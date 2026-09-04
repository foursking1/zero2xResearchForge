"""Fast debug: single-pass multi-layer grad*xact attribution, check q separability.

Computes grad*act at all layers in one forward+backward per batch, then checks
whether kmeans/spectral clustering on the attribution features separates q
within each target class (R08 for squares symmetric).
"""
import os
import numpy as np
import torch
import torch.nn as nn
from sklearn.cluster import KMeans, SpectralClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

from config import SEED, WORKSPACE
from corrections import load_split, split_root
from models import make_resnet18


def all_layers_attr(model, x, bs=64):
    """Return grad*xact attribution for every layer, in one fwd+bwd per batch."""
    # build layer list (13 layers) hooking the actual modules called by forward
    ls = [model.conv1, model.relu, model.maxpool]
    ls += [b for b in model.layer1] + [b for b in model.layer2]
    ls += [b for b in model.layer3] + [b for b in model.layer4]
    ls += [model.avgpool, model.fc]
    outs = {i: [] for i in range(len(ls))}
    handles = []
    for i, mod in enumerate(ls):
        def _hook(m, i, o, idx=i):
            o = o if isinstance(o, torch.Tensor) else o[0]
            o.retain_grad()
            outs[idx].append(o)
        handles.append(mod.register_forward_hook(_hook))
    model.eval()
    all_attr = {i: [] for i in range(len(ls))}
    all_preds = []
    with torch.enable_grad():
        for b in range(0, x.size(0), bs):
            xb = x[b:b + bs].requires_grad_(True)
            for k in outs:
                outs[k] = []
            logits = model(xb)
            preds = logits.detach().argmax(1)
            grad_out = torch.zeros_like(logits)
            grad_out.scatter_(1, preds.unsqueeze(1), 1.0)
            logits.backward(grad_out)
            for i in range(len(ls)):
                acts = outs[i]
                a_cat = torch.cat(acts)
                g_list = [o.grad if o.grad is not None else torch.zeros_like(o)
                          for o in acts]
                g_cat = torch.cat(g_list)
                all_attr[i].append(g_cat * a_cat.detach())
            all_preds.append(preds)
    for h in handles:
        h.remove()
    return {i: torch.cat(v) for i, v in all_attr.items()}, torch.cat(all_preds)


def featurize(attr):
    """channel-mean + 8x8 downsampling -> flat vector (like spray.py)."""
    N, C, H, W = attr.shape
    a = attr.mean(dim=1, keepdim=True)
    a = torch.nn.functional.interpolate(a, size=(8, 8), mode="area").flatten(1)
    return a.numpy()


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
    attrs, preds = all_layers_attr(model, x)
    for layer in (4, 6, 8, 10, 12):
        attr = featurize(attrs[layer - 1])
        print(f"=== layer {layer} attr shape {attr.shape} ===", flush=True)
        norms = np.linalg.norm(attr, axis=1)
        for grp in range(4):
            mask = g == grp
            if mask.sum() == 0:
                continue
            print(f"  grp{grp} n={mask.sum()} mean_norm={norms[mask].mean():.4f} "
                  f"pred_acc={(preds[mask]==t[mask]).mean():.3f}", flush=True)
        for cl in np.unique(t):
            idx = np.where(t == cl)[0]
            a = attr[idx]
            qc = q_true[idx]
            if qc.sum() == 0 or qc.sum() == len(qc):
                print(f"  class {cl}: no q mixture", flush=True)
                continue
            a_z = StandardScaler().fit_transform(a)
            km = KMeans(n_clusters=2, random_state=SEED, n_init=10)
            lab = km.fit_predict(a_z)
            q_hat = np.zeros_like(qc)
            for c in np.unique(lab):
                sub = lab == c
                q_hat[sub] = 1 if qc[sub].mean() >= 0.5 else 0
            print(f"  class {cl}: kmeans(z) q-acc={accuracy_score(qc, q_hat):.3f} "
                  f"sizes={[int((lab==c).sum()) for c in np.unique(lab)]}", flush=True)
            sc = SpectralClustering(n_clusters=2, random_state=SEED,
                                    affinity="nearest_neighbors",
                                    assign_labels="kmeans")
            lab2 = sc.fit_predict(a_z)
            q_hat2 = np.zeros_like(qc)
            for c in np.unique(lab2):
                sub = lab2 == c
                q_hat2[sub] = 1 if qc[sub].mean() >= 0.5 else 0
            print(f"    spectral(z) q-acc={accuracy_score(qc, q_hat2):.3f} "
                  f"sizes={[int((lab2==c).sum()) for c in np.unique(lab2)]}", flush=True)

if __name__ == "__main__":
    main()
