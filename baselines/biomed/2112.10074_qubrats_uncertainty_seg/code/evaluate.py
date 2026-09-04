"""Reconstruct full-volume predictions + uncertainties on the TEST cases and
compute QU-BraTS metrics (AUC1/AUC2/AUC3 + score) per model, per entity (ET/TC/WT).

    python evaluate.py --device cuda:0 --mc-samples 15
"""
import argparse
import json
import os
import time

import numpy as np
import torch
import torch.nn.functional as F

from model import UNet2D
import qub_metrics as qm

ENTITIES = ["ET", "TC", "WT"]


def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def load_case(cache_dir, cid):
    z = np.load(os.path.join(cache_dir, "raw", f"{cid}.npz"))
    return (z["image"], z["brain"], z["seg"], z["entities"])


def load_crop(cache_dir, cid):
    with open(os.path.join(cache_dir, "crop_params.json")) as f:
        cp = json.load(f)
    y0, y1, x0, x1 = cp[cid]
    return y0, y1, x0, x1


def predict_volume(model, image, crop, device, mc_samples, n_entities=3):
    """Full-volume per-entity foreground probabilities [E,H,W,D]."""
    y0, y1, x0, x1 = crop
    D = image.shape[-1]
    prob = np.zeros((n_entities, image.shape[0], image.shape[1], D),
                    dtype=np.float32)
    W = y1 - y0
    model.to(device)
    org_mode = None
    # MC: keep dropout active but BatchNorm in eval mode
    if mc_samples > 1:
        model.eval()
        for m in model.modules():
            if isinstance(m, torch.nn.Dropout2d):
                m.train()
    else:
        model.eval()

    slices = np.transpose(image[:, :, :], (2, 0, 1))[:, y0:y1, x0:x1]  # D x W x W
    slices = slices[:, None, :, :]  # D x 1 x W x W
    pts = torch.from_numpy(slices.astype(np.float32))
    with torch.no_grad():
        for s in range(0, len(pts), 64):
            xb = pts[s:s + 64].to(device)
            acc = []
            for _ in range(mc_samples):
                logits = model(xb)
                acc.append(torch.sigmoid(logits))
            p = torch.stack(acc).mean(dim=0).cpu().numpy()  # B x 3 x W x W
            for j, (a, b) in enumerate(zip(range(s, min(s + 64, len(pts))), range(p.shape[0]))):
                prob[:, y0:y1, x0:x1, s + j] = p[b]
    return prob


def entropy_binary_map(p):
    return np.clip(qm.entropy_binary(p) * 100.0, 0.0, 100.0)  # [0,100]


def evaluate_case(model, image, brain, seg, crop, device, mc_samples):
    prob = predict_volume(model, image, crop, device, mc_samples)
    labels = seg.astype(np.int16)
    gt = {  # per-entity binary GT
        "ET": (labels == 4).astype(np.float32),
        "TC": np.isin(labels, [1, 4]).astype(np.float32),
        "WT": (labels > 0).astype(np.float32),
    }
    results = {}
    for e, gt_bin in gt.items():
        p = prob[ENTITIES.index(e)]
        pred = (p >= 0.5).astype(np.float32)
        unc = entropy_binary_map(p)
        res = qm.evaluate_volume(gt_bin, pred, unc, brain, num_points=41)
        res["entity"] = e
        res["thresholds"] = res["thresholds"].tolist()
        res["dsc_curve"] = res["dsc_curve"].tolist()
        res["ftp_curve"] = res["ftp_curve"].tolist()
        res["ftn_curve"] = res["ftn_curve"].tolist()
        res["auc1_dsc"] = float(res["auc1_dsc"])
        res["auc2_ftp"] = float(res["auc2_ftp"])
        res["auc3_ftn"] = float(res["auc3_ftn"])
        res["score"] = float(res["score"])
        res["score_sum"] = float(res["score_sum"])
        res["dice_t100"] = float(res["dice_t100"])
        results[e] = res
    return results, prob


def predict_volume_ensemble(models, image, crop, device, n_entities=3):
    """Mean-softmax ensemble prediction over several (deterministic) models."""
    y0, y1, x0, x1 = crop
    D = image.shape[-1]
    prob = np.zeros((n_entities, image.shape[0], image.shape[1], D),
                    dtype=np.float32)
    W = y1 - y0
    slices = np.transpose(image[:, :, :], (2, 0, 1))[:, y0:y1, x0:x1][:, None, :, :]
    pts = torch.from_numpy(slices.astype(np.float32))
    with torch.no_grad():
        for s in range(0, len(pts), 64):
            xb = pts[s:s + 64].to(device)
            acc = [torch.sigmoid(m(xb)) for m in models]
            p = torch.stack(acc).mean(dim=0).cpu().numpy()
            e = min(s + 64, len(pts))
            for j in range(e - s):
                prob[:, y0:y1, x0:x1, s + j] = p[j]
    return prob


def build_ensemble(members, models_dir, device):
    models = []
    for name in members:
        ckpt = torch.load(os.path.join(models_dir, f"{name}.pt"),
                          map_location="cpu")
        cfg = ckpt["config"]
        m = UNet2D(in_ch=1, out_ch=3, base_ch=cfg["base_ch"],
                   levels=cfg["levels"], p_drop=0.0, mc_dropout=False)
        m.load_state_dict(ckpt["state_dict"])
        m.to(device)
        m.eval()
        models.append(m)
    return models


def evaluate_ensemble(members, models_dir, image, brain, seg, crop, device):
    models = build_ensemble(members, models_dir, device)
    prob = predict_volume_ensemble(models, image, crop, device)
    labels = seg.astype(np.int16)
    gt = {
        "ET": (labels == 4).astype(np.float32),
        "TC": np.isin(labels, [1, 4]).astype(np.float32),
        "WT": (labels > 0).astype(np.float32),
    }
    results = {}
    for e, gt_bin in gt.items():
        p = prob[ENTITIES.index(e)]
        pred = (p >= 0.5).astype(np.float32)
        unc = entropy_binary_map(p)
        res = qm.evaluate_volume(gt_bin, pred, unc, brain, num_points=41)
        res["entity"] = e
        for k in ["thresholds", "dsc_curve", "ftp_curve", "ftn_curve"]:
            res[k] = res[k].tolist()
        for k in ["auc1_dsc", "auc2_ftp", "auc3_ftn", "score", "score_sum",
                  "dice_t100"]:
            res[k] = float(res[k])
        results[e] = res
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True,
                    help="model names in MODELS_DIR")
    ap.add_argument("--ensemble-members", action="append", nargs="+", default=[],
                    metavar="NAME MEMBER1 MEMBER2 ...",
                    help="define an ensemble model, e.g. --ensemble-members ens_det det_s2 det_s3 det_s4")
    ap.add_argument("--mc-samples", type=int, default=15)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--random-unc", action="store_true",
                    help="also add a random-uncertainty ablation per model")
    ap.add_argument("--cache", default=os.path.join(os.path.dirname(__file__), "..", "data_cache"))
    ap.add_argument("--models-dir", default=os.path.join(os.path.dirname(__file__), "..", "models"))
    ap.add_argument("--outdir", default=os.path.join(os.path.dirname(__file__), "..", "results"))
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    set_seed(0)

    with open(os.path.join(args.cache, "split.json")) as f:
        split = json.load(f)
    test_ids = split["test"]

    all_results = {}
    ensembles = {m[0]: m[1:] for m in args.ensemble_members}
    for name in args.models + list(ensembles.keys()):
        if name in ensembles:
            t0 = time.time()
            per_case = {}
            for cid in test_ids:
                image, brain, seg, _ = load_case(args.cache, cid)
                crop = load_crop(args.cache, cid)
                per_case[cid] = evaluate_ensemble(ensembles[name], args.models_dir,
                                                  image, brain, seg, crop,
                                                  args.device)
                print(f"[{name}] case {cid} done ({time.time() - t0:.0f}s)", flush=True)
            all_results[name] = per_case
            continue
        ckpt = torch.load(os.path.join(args.models_dir, f"{name}.pt"),
                          map_location="cpu")
        cfg = ckpt["config"]
        model = UNet2D(in_ch=1, out_ch=3, base_ch=cfg["base_ch"],
                       levels=cfg["levels"], p_drop=cfg["p_drop"],
                       mc_dropout=cfg["mc_dropout"])
        model.load_state_dict(ckpt["state_dict"])
        mc_samples = args.mc_samples if cfg["mc_dropout"] else 1
        t0 = time.time()
        per_case = {}
        pred_masks = {}
        for cid in test_ids:
            image, brain, seg, _ = load_case(args.cache, cid)
            crop = load_crop(args.cache, cid)
            res, prob = evaluate_case(model, image, brain, seg, crop,
                                      args.device, mc_samples)
            per_case[cid] = res
            pred_masks[cid] = {e: (prob[ENTITIES.index(e)] >= 0.5) for e in ENTITIES}
            print(f"[{name}] case {cid} done ({time.time() - t0:.0f}s)", flush=True)

        if args.random_unc:
            # seeded random uncertainty baseline on the SAME segmentation
            rng = np.random.default_rng(0)
            for cid in test_ids:
                image, brain, seg, _ = load_case(args.cache, cid)
                labels = seg.astype(np.int16)
                gt = {"ET": (labels == 4).astype(np.float32),
                      "TC": np.isin(labels, [1, 4]).astype(np.float32),
                      "WT": (labels > 0).astype(np.float32)}
                key = f"{name}::randomunc"
                rc = {}
                for e in ENTITIES:
                    rnd_unc = rng.uniform(0, 100, size=brain.shape).astype(np.float32)
                    res = qm.evaluate_volume(gt[e], pred_masks[cid][e].astype(np.float32),
                                             rnd_unc, brain, num_points=41)
                    res["entity"] = e
                    res["thresholds"] = res["thresholds"].tolist()
                    res["dsc_curve"] = res["dsc_curve"].tolist()
                    res["ftp_curve"] = res["ftp_curve"].tolist()
                    res["ftn_curve"] = res["ftn_curve"].tolist()
                    for k in ["auc1_dsc", "auc2_ftp", "auc3_ftn", "score",
                              "score_sum", "dice_t100"]:
                        res[k] = float(res[k])
                    rc[e] = res
                if key not in all_results:
                    all_results[key] = {}
                all_results[key][cid] = rc

        all_results[name] = per_case

    with open(os.path.join(args.outdir, "per_case_results.json"), "w") as f:
        json.dump(all_results, f, indent=2)
    print("saved", os.path.join(args.outdir, "per_case_results.json"))


if __name__ == "__main__":
    main()