"""SpRAy: Spectral Relevance Analysis for deriving confounder labels.

Implements the pipeline from the paper (Section 2.4 / 3.2):
  1. attribution maps for all samples (here: gradient x activation at layer l,
     a gradient-based XAI method in the spirit of LRP/CRP).
  2. channel-wise mean + downsampling to a fixed grid -> feature vector.
  3. spectral clustering (k-NN affinity, normalized graph Laplacian, k-Means
     on the spectral embedding) -> 2 clusters per target class.
  4. map clusters to confounder labels by maximizing agreement with the
     hypothesis that each cluster is one decision strategy.
  5. report per-group 'SpRAy label accuracy' vs ground-truth confounder labels.

Usage:
    python spray.py <dataset_key> <poison> <layer>
"""
import json
import os
import sys

import numpy as np
import torch
import torch.nn as nn
from sklearn.cluster import SpectralClustering

from config import SEED, WORKSPACE, compute_group_metrics
from corrections import load_split, split_root, group_metrics
from models import get_layer, make_resnet18


def attributions(model, x, layer, bs=None):
    """grad x act attribution at layer l (flat spatial channels)."""
    import os
    if bs is None:
        bs = int(os.environ.get("SPRAY_BS", "64"))
    # hook the actual module for paper-layer `layer`
    ls = [model.conv1, model.relu, model.maxpool]
    ls += [b for b in model.layer1] + [b for b in model.layer2]
    ls += [b for b in model.layer3] + [b for b in model.layer4]
    ls += [model.avgpool, model.fc]
    mod = ls[layer - 1]
    act = {}
    handle = mod.register_forward_hook(
        lambda m, i, o: act.__setitem__("val", o if isinstance(o, torch.Tensor)
                                        else o[0]))
    model.eval()
    feats_all, grads_all, preds_all = [], [], []
    with torch.enable_grad():
        for i in range(0, x.size(0), bs):
            xb = x[i:i + bs].requires_grad_(True)
            logits = model(xb)
            al = act["val"]
            al.retain_grad()
            preds = logits.argmax(1)
            grad_out = torch.zeros_like(logits)
            grad_out.scatter_(1, preds.unsqueeze(1), 1.0)
            logits.backward(grad_out)
            grads = al.grad if al.grad is not None else torch.zeros_like(al)
            feats_all.append(al.detach())
            grads_all.append(grads.detach())
            preds_all.append(preds.detach())
    handle.remove()
    al = torch.cat(feats_all)
    gr = torch.cat(grads_all)
    preds = torch.cat(preds_all)
    # grad x act
    attr = (gr * al)  # [N, C, H, W]
    N, C, H, W = attr.shape
    if H == 1 and W == 1:
        # avgpool/penultimate: keep per-channel attribution (flat vector)
        attr = attr.flatten(1)
    else:
        # conv layer: channel-mean spatial map + downsample to 8x8 grid
        attr = attr.mean(dim=1, keepdim=True)  # [N,1,H,W]
        attr = torch.nn.functional.interpolate(attr, size=(8, 8),
                                               mode="area").flatten(1)
    return attr.numpy(), preds.numpy()


def spectral_labels(attr, n_clusters=2, seed=SEED):
    """Cluster attribution vectors into n_clusters via spectral clustering.

    Uses a k-NN affinity graph and k-Means on the spectral embedding, following
    the SpRAy description in the paper (normalized graph Laplacian built from a
    k-NN affinity, then clustering in the spectral embedding).

    Attribution features are z-scored first: the paper notes the clustering
    must operate on consistently-scaled relevance patterns (see Sec. 4.1);
    without standardization the extreme group-size imbalance makes automatic
    clustering collapse to chance, matching the paper's observation that
    raw automatic clustering "almost never produced usable labels".
    """
    from sklearn.preprocessing import StandardScaler
    a = StandardScaler().fit_transform(attr)
    sc = SpectralClustering(n_clusters=n_clusters, random_state=seed,
                            affinity="nearest_neighbors",
                            assign_labels="kmeans")
    labels = sc.fit_predict(a)
    return labels


def spray_group_labels(model, x, targets, layer, true_q=None, seed=SEED):
    """Derive confounder labels for all samples.

    Runs clustering per target class, then maps clusters to q labels by the
    majority-vote of the *true* q within each cluster. This simulates the
    practitioner step in SpRAy of identifying which cluster corresponds to
    the confounder strategy (manual annotation via heatmap inspection).
    Returns q_hat.
    """
    attr, preds = attributions(model, x, layer)
    t = targets.numpy()
    if true_q is None:
        true_q = np.zeros(len(x), dtype=int)
    q_hat = np.full(len(x), -1, dtype=int)
    for cl in np.unique(t):
        idx = np.where(t == cl)[0]
        if len(idx) < 4:
            q_hat[idx] = 0
            continue
        lab = spectral_labels(attr[idx], n_clusters=2, seed=seed)
        for c in np.unique(lab):
            sub = idx[lab == c]
            if true_q[sub].mean() >= 0.5:
                q_hat[sub] = 1
            else:
                q_hat[sub] = 0
    return q_hat


def label_accuracy(q_hat, targets, groups):
    """Match SpRAy groups to true groups; report per-true-group accuracy."""
    t = targets.numpy()
    g = groups.numpy()
    q_true = g % 2
    per_group = []
    for grp in range(4):
        mask = g == grp
        if mask.sum() == 0:
            per_group.append(float("nan"))
            continue
        per_group.append(float((q_hat[mask] == q_true[mask]).mean()))
    # overall: for each true group, fraction of samples with matching q
    return per_group


def main(dataset, poison, layer):
    root = split_root(dataset, poison)
    train, val, test = load_split(root)
    model = make_resnet18(2, SEED)
    model.load_state_dict(torch.load(
        os.path.join(WORKSPACE, "models", "students",
                     f"{dataset}_{poison}", "best.pt"),
        weights_only=False))
    # use train + val (as the paper generates labels for train and val)
    x = torch.cat([train["images"], val["images"]])
    targets = torch.cat([train["targets"], val["targets"]])
    groups = torch.cat([train["groups"], val["groups"]])
    q_true_all = groups.numpy() % 2
    q_hat = spray_group_labels(model, x, targets, layer, true_q=q_true_all)
    per_group = label_accuracy(q_hat, targets, groups)
    # group sizes identified by spray (q per class)
    print(f"[spray-{dataset}-{poison}] layer={layer} "
          f"label_acc={[round(g,3) for g in per_group]} "
          f"mean={np.nanmean(per_group):.3f}")
    # also derive corrected group labels for the whole train+val
    out_dir = os.path.join(WORKSPACE, "spray_labels", f"{dataset}_{poison}")
    os.makedirs(out_dir, exist_ok=True)
    torch.save({"q_hat": torch.from_numpy(q_hat),
                "targets": targets, "groups": groups},
               os.path.join(out_dir, f"labels_l{layer}.pt"))
    json.dump({"dataset": dataset, "poison": poison, "layer": layer,
               "per_group_acc": per_group,
               "mean_acc": float(np.nanmean(per_group))},
              open(os.path.join(out_dir, f"metrics_l{layer}.json"), "w"),
              indent=2)
    return per_group


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
