"""04_te.py -- source-free transferability estimation.

Given the pool of *source* models + the *target* slices, compute for every
candidate source model a transferability score.  Samples are the bottleneck
feature pixels of the target slices:

  * CC-FV (our implementation of the paper's Class-Consistency x Feature-Variety):
      - CLASS CONSISTENCY: classes are taken from the *source model's own*
        predictions (pseudo labels) -- NO target labels are used.  Score = area
        weighted mean cosine similarity of L2-normalised feature pixels to their
        class centroid (classes = source-model foreground / background).
      - FEATURE VARIETY: mean channel-wise Shannon entropy of the bottleneck
        activations (min-max normalised, 64 bins), normalised to [0,1].
      - CC-FV = CC * FV.  A GT-labelled variant of CC is reported as a check.
  * Baselines (may consume target labels -- their known requirement):
      - LogME (You et al., ICML 2021): maximum-evidence linear head on features;
      - LEEP (Nguyen et al., ICLR 2020): likelihood over the empirical
        class-transition matrix built from the source-model posterior;
      - GBC (gradient-based, approx.): neg. squared gradient-norm of a logistic
        probe on the features after K steps (transferable features => the probe
        converges => small residual gradient).

Nothing here trains the source model on the target task.
"""
import os
import sys
import json
import math
import argparse
import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (CKPT_DIR, RESULTS_DIR, SPLITS)
from dataset import make_loader
from train_utils import build_model, load_ckpt

CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pool_config.json")))
torch.set_num_threads(16)

MAX_CC_PX = 120_000   # budget for the pixel sample (balanced fg/bg)


def load_pool_models(source):
    models = {}
    for m in CFG["pool"]:
        tag = f"{source}_{m['id']}"
        model = build_model(m)
        ck = load_ckpt(f"{tag}_pretrained")
        model.load_state_dict(ck["state"])
        model.eval()
        models[m["id"]] = model
    return models


@torch.no_grad()
def collect_pixel_features(model, loader, max_px=MAX_CC_PX, scale="bn"):
    r"""Pixel-level sample of model features, aligned with (a) down-sampled GT
    labels and (b) the source model's own predictions (pseudo labels).
    scale \in {"bn", "dec"} selects bottleneck vs decoder (full-res) features."""
    rng = np.random.RandomState(7)
    feats, ygt, ypseudo, srcp, sids = [], [], [], [], []
    with torch.no_grad():
        for x, y in loader:
            logits, bn, dec = model(x, want_dec=True)          # (B,C,H,W)
            ft = dec if scale == "dec" else bn
            B, C, H, W = ft.shape
            src = torch.sigmoid(logits)
            pred = (src > 0.5).float()
            lab = (y > 0.5).float()
            gy = (F.adaptive_avg_pool2d(lab, (H, W)) > 0.5)   # (B,1,H,W)
            py = (F.adaptive_avg_pool2d(pred, (H, W)) > 0.5)
            sy = F.adaptive_avg_pool2d(src, (H, W))
            for k in range(B):
                f = ft[k].reshape(C, H * W)
                g = gy[k].reshape(-1).numpy()
                p = py[k].reshape(-1).numpy()
                s = sy[k].reshape(-1).numpy()
                fg = np.where(g)[0]; bg = np.where(~g)[0]
                nf = len(fg); nb = len(bg)
                if nf == 0:
                    feats.append(f.T); ygt.append(g); ypseudo.append(p); srcp.append(s)
                    sids.append(np.full(f.shape[1], len(sids), dtype=np.int32))
                    continue
                cap = max_px // 8
                if nf > cap:
                    fg = rng.choice(fg, cap, replace=False); nf = cap
                if nb > cap:
                    bg = rng.choice(bg, cap, replace=False); nb = cap
                pick = np.concatenate([fg, bg])
                sid_here = len(sids)
                feats.append(f[:, pick].T)
                ygt.append(g[pick]); ypseudo.append(p[pick]); srcp.append(s[pick])
                sids.append(np.full(len(pick), sid_here, dtype=np.int32))
    X = np.concatenate(feats).astype(np.float32)
    G = np.concatenate(ygt).astype(np.uint8)
    Y = np.concatenate(ypseudo).astype(np.uint8)
    S = np.concatenate(srcp).astype(np.float32)
    SID = np.concatenate(sids).astype(np.int32)
    # final balanced cap
    if len(X) > max_px:
        fg = np.where(G == 1)[0]; bg = np.where(G == 0)[0]
        n_fg = min(len(fg), max_px // 2); n_bg = min(len(bg), max_px - n_fg)
        pick = np.concatenate([rng.choice(fg, n_fg, replace=False),
                               rng.choice(bg, n_bg, replace=False)])
        X, G, Y, S, SID = X[pick], G[pick], Y[pick], S[pick], SID[pick]
    return {"X": X, "gt": G, "pseudo": Y, "srcp": S, "sid": SID,
            "n_fg": int((G == 1).sum()), "n_bg": int((G == 0).sum())}


# ---------- LogME (You et al. 2021) ----------------------------------------
def _logme(feat, labels, n_iter=150, tol=1e-4):
    n, d = feat.shape
    y = np.zeros((n, 2)); y[np.arange(n), labels.astype(int)] = 1.0
    k = 2
    alpha, beta = np.ones(1), np.ones(1)
    mu = np.zeros((d, k))
    ftf = feat.T @ feat
    fty = feat.T @ y
    A = np.eye(d)
    for _ in range(n_iter):
        A = beta[0] * ftf + alpha[0] * np.eye(d)
        for c in range(k):
            mu[:, c] = np.linalg.solve(A, beta[0] * fty[:, c])
        resid = ((y - feat @ mu) ** 2).sum()
        beta[0] = (n * k) / max(resid, 1e-10)
        trace = (mu * mu).sum()
        alpha[0] = min(d * k / max(trace, 1e-10), 1e8)
    sign, logdetA = np.linalg.slogdet(A)
    logdetA = logdetA if sign > 0 else -logdetA
    logw = 0.5 * (k * d * math.log(alpha[0]) + k * n * math.log(beta[0])) \
        - 0.5 * logdetA
    return float(logw)


def logme_score(cf):
    return _logme(cf["X"], cf["gt"])


# ---------- LEEP (Nguyen et al. 2020) ----------------------------------------
def leep_score(cf):
    src = np.clip(cf["srcp"], 1e-9, 1 - 1e-9)
    priors = np.stack([1 - src, src], axis=1)          # source classes {bg,fg}
    N = len(cf["gt"])
    trans = np.zeros((2, 2))
    for i in range(N):
        trans[cf["gt"][i]] += priors[i]
    trans /= trans.sum(1, keepdims=True) + 1e-9
    s = 0.0
    for i in range(N):
        c = cf["gt"][i]
        s += math.log(trans[c, 0] * priors[i, 0] + trans[c, 1] * priors[i, 1] + 1e-9)
    return s / N


# ---------- GBC (gradient-based probe) ---------------------------------------
def gbc_score(cf, steps=20, lr=1.0):
    X = cf["X"].astype(np.float64)
    X = (X - X.mean(0)) / (X.std(0) + 1e-5)
    y = cf["gt"].astype(np.float64)
    n, d = X.shape
    w, b = np.zeros(d), 0.0
    gss = []
    for s in range(steps):
        p = 1.0 / (1.0 + np.exp(-(X @ w + b)))
        gw = X.T @ (p - y) / n
        w -= lr * gw
        b -= lr * float((p - y).mean())
        if s >= 1:  # skip the initial (class-balance dominated) gradient
            gss.append(float(gw @ gw))
    return -float(np.mean(gss))


# ---------- CC-FV (paper-style, source-free) ----------------------------------
def _channel_entropy(mat, nbins=64, max_px=200_000):
    C, P = mat.shape
    if P > max_px:
        mat = mat[:, np.random.RandomState(0).choice(P, max_px, replace=False)]
    fmin = mat.min(1, keepdims=True); fmax = mat.max(1, keepdims=True)
    q = ((mat - fmin) / (fmax - fmin + 1e-6) * (nbins - 1)).astype(int).clip(0, nbins - 1)
    ents = 0.0
    for c in range(C):
        hist = np.bincount(q[c], minlength=nbins).astype(np.float64)
        prob = hist / hist.sum()
        ent = -(prob[prob > 0] * np.log2(prob[prob > 0])).sum()
        ents += ent / np.log2(nbins)
    return ents / C


def class_consistency(mat, labels):
    """Centroid-cosine (within-class) consistency for a given labelling."""
    C, P = mat.shape
    total = 0.0
    for c in (0, 1):
        sel = labels == c
        npx = int(sel.sum())
        if npx < 8:
            continue
        v = mat[:, sel]
        norm = np.linalg.norm(v, axis=0) + 1e-8
        vn = v / norm
        centroid = vn.mean(1)
        centroid /= np.linalg.norm(centroid) + 1e-8
        cos = (vn * centroid[:, None]).sum(0)
        total += npx / P * float(cos.mean())
    return total


def class_consistency_cross_slice(mat, labels, sid, max_slices=64, max_px=4):
    """Cross-slice class consistency (paper-style): within a predicted class,
    feature segments should align ACROSS different target slices.  For each
    class we take up to `max_slices` slices, build a normalised per-slice class
    centroid from up to `max_px` pixels, and average the cross-slice cosine
    similarity.  Random networks show low cross-slice consistency (this avoids
    the "random-net inflation" of the within-slice centroid version)."""
    rng = np.random.RandomState(3)
    C, P = mat.shape
    total = 0.0
    for c in (0, 1):
        sel = labels == c
        npx = int(sel.sum())
        if npx < 8:
            continue
        pix_sid = sid[sel]
        pix = mat[:, sel]
        slices = np.unique(pix_sid)
        if len(slices) < 2:
            continue
        if len(slices) > max_slices:
            slices = rng.choice(slices, max_slices, replace=False)
        vecs = []
        for s in slices:
            idx = np.where(pix_sid == s)[0]
            take = min(len(idx), max_px)
            if take == 0:
                continue
            pick = rng.choice(len(idx), take, replace=False)
            v = pix[:, idx[pick]]
            norm = np.linalg.norm(v, axis=0) + 1e-8
            vn = v / norm
            cent = vn.mean(1)
            cent /= np.linalg.norm(cent) + 1e-8
            vecs.append(cent)
        if len(vecs) < 2:
            continue
        vecs = np.asarray(vecs)
        cos = vecs @ vecs.T
        iu = np.triu_indices(len(vecs), 1)
        total += npx / P * float(cos[iu].mean())
    return total


def ccfv_score(cf):
    mat = cf["X"].T                                  # (C,P)
    cc_pseudo = class_consistency(mat, cf["pseudo"])
    cc_gt = class_consistency(mat, cf["gt"])
    cc_cross_pseudo = class_consistency_cross_slice(mat, cf["pseudo"], cf["sid"])
    cc_cross_gt = class_consistency_cross_slice(mat, cf["gt"], cf["sid"])
    fv = _channel_entropy(mat)
    return {"CC": cc_pseudo, "CC_gt": cc_gt, "CC_cross": cc_cross_pseudo,
            "CC_cross_gt": cc_cross_gt, "FV": fv, "score": cc_cross_pseudo * fv}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["liver", "spleen"])
    ap.add_argument("--target", choices=["spleen", "liver"])
    ap.add_argument("--cases", default=None, help="comma-list overriding target train cases")
    ap.add_argument("--scale", choices=["bn", "dec"], default="bn")
    a = ap.parse_args()

    if a.cases:
        cases = [x for x in a.cases.split(",") if x]
    else:
        cases = SPLITS[a.target][0]
    models = load_pool_models(a.source)
    rows = []
    for mid, model in models.items():
        mcfg = [m for m in CFG["pool"] if m["id"] == mid][0]
        loader = make_loader(a.target, cases, batch_size=16, shuffle=False,
                             seed=mcfg["seed"],
                             max_slices=CFG["finetune"]["max_slices_per_case"],
                             augment=False, size=CFG["finetune"]["size"])
        cf = collect_pixel_features(model, loader, scale=a.scale)
        cc = ccfv_score(cf)
        lkm = logme_score(cf)
        leep = leep_score(cf)
        gbc = gbc_score(cf)
        print(f"[te] {a.source}/{mid}: CC-FV={cc['score']:.4f} (CC_x={cc['CC_cross']:.4f} CC_xgt={cc['CC_cross_gt']:.4f} "
              f"CC={cc['CC']:.4f} FV={cc['FV']:.4f})  LogME={lkm:.2f}  LEEP={leep:.4f}  GBC={gbc:.4f}")
        rows.append({"source_organ": a.source, "target_organ": a.target,
                     "source_model": f"{a.source}_{mid}",
                     "feature_scale": a.scale, "target_train_cases": list(cases),
                     "ccfv": cc["score"], "cc": cc["CC"], "cc_gt": cc["CC_gt"],
                     "cc_cross": cc["CC_cross"], "cc_cross_gt": cc["CC_cross_gt"],
                     "fv": cc["FV"],
                     "logme": lkm, "leep": leep, "gbc": gbc,
                     "n_pixels": int(len(cf["gt"])), "px_fg": cf["n_fg"], "px_bg": cf["n_bg"]})
    out = os.path.join(RESULTS_DIR, f"te_{a.source}2{a.target}.json")
    json.dump(rows, open(out, "w"), indent=2)
    print("saved", out)


if __name__ == "__main__":
    main()