"""Correction methods: DFR, Group DRO, P-ClArC, RR-ClArC.

Implements the paper's protocols (Section 3.2):
  * DFR        - re-train last layer on a balanced subset (8 samples/group),
                 SGD lr=0.01, select by validation AGA.
  * Group DRO  - post-hoc, updates ALL layers, SGD lr=1e-4 momentum 0.9,
                 weight-decay grid {1.0,0.5,0.1,0.05,0.01}, dynamic C
                 (Sagawa et al.), select by validation AGA.
  * P-ClArC    - CAV at layer l (SVM or PCAV), suppressive projection layer
                 inserted between l and l+1, fine-tune downstream head only.
  * RR-ClArC   - CAV at layer l, fine-tune with L = CE + lam * LRR where
                 LRR = (grad_al [m . f_dh(al)] . vc)^2.

All methods operate on the *same* ERM student and select the checkpoint with
the highest validation AGA (group-balanced) for real labels.
"""
import json
import os
import time

import numpy as np
import torch
import torch.nn as nn
from torch.nn import functional as F

from config import SEED, WORKSPACE, compute_group_metrics, set_seed
from models import get_layer, make_resnet18, hook_activation


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------
def load_split(root):
    def _load(name):
        d = torch.load(os.path.join(root, f"{name}.pt"), weights_only=False)
        out = {}
        for k, v in d.items():
            if isinstance(v, np.ndarray):
                v = torch.from_numpy(v).float() if v.dtype.kind == "f" \
                    else torch.from_numpy(v).long()
            out[k] = v
        if "group_labels" in out and "groups" not in out:
            out["groups"] = out.pop("group_labels")
        return out
    return _load("train"), _load("val"), _load("test")


def split_root(dataset, poison):
    if dataset == "squares":
        # students are trained on the reference-rendering squares (squares_ref)
        base = os.environ.get("SQUARES_DIR", os.path.join(WORKSPACE, "squares_ref"))
        return os.path.join(base, poison)
    return os.path.join(WORKSPACE, "real_tensors", f"{dataset}_{poison}")


def predict(model, x, bs=128):
    model.eval()
    preds = []
    with torch.no_grad():
        for i in range(0, x.size(0), bs):
            preds.append(model(x[i:i + bs]).argmax(1).cpu())
    return torch.cat(preds)


def group_metrics(model, x, y, g):
    pred = predict(model, x)
    return compute_group_metrics(pred.numpy(), y.numpy(), g.numpy())


def extract_features(model, x, layer, bs=128):
    """Penultimate (or layer-l) features."""
    model.eval()
    feats = []
    handle, act = hook_activation(model, layer)
    with torch.no_grad():
        for i in range(0, x.size(0), bs):
            model(x[i:i + bs])
            feats.append(act["val"].flatten(1).cpu())
    handle.remove()
    return torch.cat(feats)


# ---------------------------------------------------------------------------
# DFR
# ---------------------------------------------------------------------------
def run_dfr(model, train, val, test, n_per_group=8, epochs=100, lr=0.01):
    """Retrain the last layer on a balanced subset (n_per_group/group)."""
    model = model.cpu()
    # build balanced subset
    x_s, y_s = [], []
    gs = train["groups"].numpy()
    for g in range(4):
        idx = np.where(gs == g)[0]
        rng = np.random.default_rng(SEED)
        chosen = rng.choice(idx, size=min(n_per_group, len(idx)),
                            replace=False)
        x_s.append(train["images"][chosen])
        y_s.append(train["targets"][chosen])
    xb = torch.cat(x_s)
    yb = torch.cat(y_s)
    # freeze backbone
    for p in model.parameters():
        p.requires_grad = False
    for p in model.fc.parameters():
        p.requires_grad = True
    opt = torch.optim.SGD(model.fc.parameters(), lr=lr)
    lossf = nn.CrossEntropyLoss()
    best_aga, best_state = -1, None
    for ep in range(epochs):
        model.train()
        opt.zero_grad()
        out = model(xb)
        loss = lossf(out, yb)
        loss.backward()
        opt.step()
        if ep % 10 == 0 or ep == epochs - 1:
            emp, aga, wga, _ = group_metrics(model, val["images"],
                                             val["targets"], val["groups"])
            if aga > best_aga:
                best_aga = aga
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    return model, {"best_val_aga": best_aga}


# ---------------------------------------------------------------------------
# Group DRO (post-hoc, all layers)
# ---------------------------------------------------------------------------
class GroupDRO:
    """Sagawa et al. group DRO applied post-hoc to an existing model."""

    def __init__(self, model, n_groups=4, lr=1e-4, momentum=0.9,
                 weight_decay=0.1, adv_lr=0.01, use_adjust_c=True,
                 c_ratio=0.1):
        self.model = model
        self.n_groups = n_groups
        self.lr = lr
        self.opt = torch.optim.SGD(model.parameters(), lr=lr,
                                   momentum=momentum,
                                   weight_decay=weight_decay)
        self.adv_probs = torch.ones(n_groups) / n_groups
        self.adv_lr = adv_lr
        self.use_adjust_c = use_adjust_c
        self.C = 1.0
        self.c_ratio = c_ratio

    def _group_losses(self, out, y, g):
        ce = F.cross_entropy(out, y, reduction="none")
        losses = []
        for grp in range(self.n_groups):
            m = g == grp
            if m.sum() == 0:
                losses.append(torch.tensor(0.0))
            else:
                losses.append(ce[m].mean())
        return torch.stack(losses)

    def step(self, x, y, g):
        self.model.train()
        self.opt.zero_grad()
        out = self.model(x)
        g = g.to(out.device)
        group_losses = self._group_losses(out, y, g)
        if self.use_adjust_c:
            gl = group_losses.detach()
            self.C = float(gl.mean() + self.c_ratio *
                           (gl.std() if gl.std().isfinite()
                            else torch.tensor(0.0)))
            self.C = max(self.C, 1e-8)
        # exponential tilting of group weights
        with torch.no_grad():
            self.adv_probs = self.adv_probs * torch.exp(
                self.adv_lr * self.C * group_losses.detach())
            self.adv_probs = self.adv_probs / self.adv_probs.sum()
        loss = torch.sum(self.adv_probs.to(out.device) * group_losses)
        loss.backward()
        self.opt.step()
        return float(loss.item())


def run_group_dro(model, train, val, test, wd_grid=(0.1, 0.5, 1.0),
                  epochs=300, bs=32):
    best_overall = (-1, None, None)
    for wd in wd_grid:
        m = make_resnet18(2, SEED)
        m.load_state_dict({k: v.clone() for k, v in model.state_dict().items()})
        dro = GroupDRO(m, weight_decay=wd)
        n = train["images"].size(0)
        rng = np.random.default_rng(SEED)
        best_aga, best_state = -1, None
        for ep in range(epochs):
            per = torch.randperm(n, generator=torch.Generator().manual_seed(ep))
            for i in range(0, n, bs):
                idx = per[i:i + bs]
                dro.step(train["images"][idx], train["targets"][idx],
                         train["groups"][idx])
            if ep % 10 == 0 or ep == epochs - 1:
                emp, aga, wga, _ = group_metrics(m, val["images"],
                                                 val["targets"], val["groups"])
                if aga > best_aga:
                    best_aga = aga
                    best_state = {k: v.clone() for k, v in m.state_dict().items()}
        if best_aga > best_overall[0]:
            best_overall = (best_aga, best_state, wd)
    m = make_resnet18(2, SEED)
    m.load_state_dict(best_overall[1])
    return m, {"best_val_aga": best_overall[0], "best_wd": best_overall[2]}


# ---------------------------------------------------------------------------
# CAV computation
# ---------------------------------------------------------------------------
def compute_cav(model, train, layer, target_class=1, mode="pca", seed=SEED):
    """Compute CAV vc for concept 'confounder' using layer-l activations.

    Uses samples of target class y, split by confounder q.
    mode: 'svm' -> LinearSVC weight vector, 'pca' -> PCAV (first principal
    component of X+ after centering).
    Returns vc (unit norm, flattened vector) and zsup (mean of X-).
    """
    x = train["images"]
    t = train["targets"].numpy()
    q = train["confs"].numpy() if "confs" in train else \
        (train["groups"].numpy() % 2)
    mask = t == target_class
    a = extract_features(model, x, layer)  # [N, d]
    a = a[mask]
    qm = torch.from_numpy(q[mask])
    ap = a[qm == 1]  # confounder
    an = a[qm == 0]  # non-confounder
    zsup = an.mean(0, keepdim=True)
    if mode == "svm":
        from sklearn.svm import LinearSVC
        X = torch.cat([an, ap]).numpy()
        yv = np.array([0] * len(an) + [1] * len(ap))
        clf = LinearSVC(random_state=seed, C=1.0, max_iter=5000)
        clf.fit(X, yv)
        vc = torch.from_numpy(clf.coef_[0]).float()
    else:  # PCAV: first principal component of centered confounder act
        xc = ap - ap.mean(0, keepdim=True)
        # Reduced SVD only: U is [d, n] (not [d, d]) — first column is the
        # same principal component but avoids O(d^2) memory for high-d layers
        # (e.g. layer 6 of ResNet18 has d = 128*16*16 = 32768).
        U, S, _ = torch.linalg.svd(xc.T, full_matrices=False)
        vc = U[:, 0]
    vc = vc / (vc.norm() + 1e-12)
    return vc, zsup


class ProjectionLayer(nn.Module):
    """h(al) = (I - vc vc^T) al + vc vc^T zsup, operates on flattened al."""

    def __init__(self, vc, zsup):
        super().__init__()
        self.register_buffer("vc", vc.flatten().reshape(-1))
        self.register_buffer("zsup", zsup.flatten().reshape(-1))

    def forward(self, al):
        shape = al.shape
        flat = al.flatten(1)
        d = flat.size(1)
        vc = self.vc[:d]
        z = self.zsup[:d]
        proj = vc * ((flat - z) @ vc).unsqueeze(1)
        return (flat - proj).reshape(shape)


def _base_layers(model):
    m = model
    ls = [m.conv1, nn.Sequential(m.bn1, m.relu), m.maxpool]
    ls += [b for b in m.layer1] + [b for b in m.layer2]
    ls += [b for b in m.layer3] + [b for b in m.layer4]
    ls += [m.avgpool, nn.Flatten(), m.fc]
    return ls


# ---------------------------------------------------------------------------
# P-ClArC
# ---------------------------------------------------------------------------
class CorrectedModel(nn.Module):
    """Base model with projection layer inserted after layer l.

    Layers <= l frozen; layers > l trainable (downstream head f_dh).
    """

    def __init__(self, base, layer, proj):
        super().__init__()
        self.base = base
        self.layer = layer
        self.proj = proj
        ls = _base_layers(base)
        self.fe = nn.ModuleList(ls[:layer])   # layers 1..l
        self.head = nn.Sequential(*ls[layer:])  # layers l+1..13
        for p in self.fe.parameters():
            p.requires_grad = False
        for p in self.head.parameters():
            p.requires_grad = True

    def forward(self, x):
        h = x
        for mod in self.fe:
            h = mod(h)
        h = self.proj(h)
        return self.head(h)


def run_pclarc(model, train, val, test, layer, target_class, cav_mode,
               epochs=100, lr=1e-3, bs=32):
    vc, zsup = compute_cav(model, train, layer, target_class, cav_mode)
    # need zsup in the flattened feature dim of layer l
    cm = CorrectedModel(model, layer, ProjectionLayer(vc, zsup))
    # freeze params before layer l by only training head
    opt = torch.optim.SGD(cm.head.parameters(), lr=lr, momentum=0.9)
    lossf = nn.CrossEntropyLoss()
    best_aga, best_state = -1, None
    n = train["images"].size(0)
    for ep in range(epochs):
        cm.train()
        per = torch.randperm(n, generator=torch.Generator().manual_seed(ep))
        for i in range(0, n, bs):
            idx = per[i:i + bs]
            opt.zero_grad()
            out = cm(train["images"][idx])
            loss = lossf(out, train["targets"][idx])
            loss.backward()
            opt.step()
        emp, aga, wga, _ = group_metrics(cm, val["images"], val["targets"],
                                         val["groups"])
        if aga > best_aga:
            best_aga = aga
            best_state = {k: v.clone() for k, v in cm.state_dict().items()}
    cm.load_state_dict(best_state)
    return cm, {"best_val_aga": best_aga}


# ---------------------------------------------------------------------------
# RR-ClArC
# ---------------------------------------------------------------------------
class RRModel(nn.Module):
    def __init__(self, base, layer, vc):
        super().__init__()
        self.base = base
        self.layer = layer
        self.register_buffer("vc", vc)
        self._fl = None

    def forward(self, x):
        h = x
        layers = _base_layers(self.base)
        for i, mod in enumerate(layers):
            h = mod(h)
            if i == self.layer - 1:  # capture output of layer `layer`
                self._fl = h
        return h


def run_rrclarc(model, train, val, test, layer, target_class, cav_mode,
                lam=1.0, epochs=100, lr=1e-3, bs=32, loss_fn="sq"):
    # RR-ClArC fine-tunes ALL layers (L = CE + lam*LRR); re-enable grads in
    # case a prior method (e.g. run_dfr) froze the backbone in-place.
    for p in model.parameters():
        p.requires_grad = True
    vc, zsup = compute_cav(model, train, layer, target_class, cav_mode)
    rm = RRModel(model, layer, vc)
    opt = torch.optim.SGD(rm.parameters(), lr=lr, momentum=0.9)
    lossf = nn.CrossEntropyLoss()
    best_aga, best_state = -1, None
    n = train["images"].size(0)
    m_reg = torch.randint(0, 2, (2,)).float() * 2 - 1  # +/-1 per class
    for ep in range(epochs):
        rm.train()
        per = torch.randperm(n, generator=torch.Generator().manual_seed(ep))
        for i in range(0, n, bs):
            idx = per[i:i + bs]
            xb, yb = train["images"][idx], train["targets"][idx]
            opt.zero_grad()
            out = rm(xb)
            ce = lossf(out, yb)
            # right-reason loss
            al_raw = rm._fl                       # [B, C, H, W]
            al = al_raw.flatten(1)
            d = al.size(1)
            vcv = vc[:d]
            # gradient of m_t * logit_t w.r.t. al (raw, spatial)
            mvec = m_reg.to(out.device)
            target_lin = torch.sum(mvec[None, :] * out, dim=1)
            grads_raw = torch.autograd.grad(target_lin.sum(), al_raw,
                                            create_graph=True)[0]
            grads = grads_raw.flatten(1)
            sens = grads @ vcv.to(al.device)
            if loss_fn == "sq":
                lrr = (sens ** 2).mean()
            else:  # cosine
                lrr = (sens.abs() / (grads.norm(dim=1) * vcv.norm() + 1e-12)
                       ).mean()
            loss = ce + lam * lrr
            loss.backward()
            opt.step()
        emp, aga, wga, _ = group_metrics(rm, val["images"], val["targets"],
                                         val["groups"])
        if aga > best_aga:
            best_aga = aga
            best_state = {k: v.clone() for k, v in rm.state_dict().items()}
    rm.load_state_dict(best_state)
    return rm, {"best_val_aga": best_aga}
