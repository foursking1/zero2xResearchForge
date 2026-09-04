#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Global RX (Mahalanobis) anomaly detector on the frozen 14-dataset subset
of the HAD survey paper (arXiv:2507.05730, Table 5 / Table 4).

Usage:
    python run_rx.py                          # auto-detect data dir
    python run_rx.py --data_dir <path>        # explicit path to the hsi/ folder
    python run_rx.py --out_dir <path>         # override output dir (default: package results/)

The script ONLY reads the frozen .mat files; it never modifies them. It
computes a per-pixel global-RX anomaly score and the pixel-level
ROC-AUC against the supplied ground truth. Ground truth is used for
evaluation only -- no training / parameter fitting uses the GT.

Outputs (in out_dir):
    evidence_table.csv    -> 14-row evidence table + summary rows
    summary.json          -> machine-readable summary
    sha256_report.tsv     -> SHA-256 integrity verification of all used files

Reference values (paper Table 5, RX column) are stored here only for the
comparison columns (auc_paper_rx, delta); they are not used to fit anything.
"""

import argparse
import hashlib
import json
import os
import time
import sys

import numpy as np

try:
    import scipy.io as sio
except ImportError:
    sio = None

# ---- Frozen dataset mapping (file -> survey Table 5 row) -------------------
# survey_id matches Table 5 dataset IDs (Table 4); the ABU naming swap
# (airport-2 <-> 8.3) is from TASK.md / PAPER_ANCHOR.md.
DATASETS = [
    # (file, survey_id, paper_table5_rx_auc, note)
    ("abu/abu-airport-1.mat", "8.1", 0.8221, ""),
    ("abu/abu-airport-2.mat", "8.3", 0.8404, "naming swap: mirror airport-2 == paper row 8.3 (LA-2)"),
    ("abu/abu-airport-3.mat", "8.2", 0.9526, "version diff: 205 bands vs paper 191 (Gulfport)"),
    ("abu/abu-urban-1.mat", "9.1", 0.9907, ""),
    ("abu/abu-urban-2.mat", "9.2", 0.9946, ""),
    ("abu/abu-urban-3.mat", "9.3", 0.9513, ""),
    ("abu/abu-urban-4.mat", "9.4", 0.9887, ""),
    ("abu/abu-urban-5.mat", "9.5", 0.9692, ""),
    ("abu/abu-beach-1.mat", "10.1", 0.9807, ""),
    ("abu/abu-beach-2.mat", "10.2", 0.9999, "version diff: 193 bands vs paper 188 (Bay Champagne)"),
    ("aviris_1.mat", "6", 0.8866, ""),
    ("aviris_2.mat", "7", 0.9181, ""),
    ("hydice_urban.mat", "2", 0.9857, ""),
    ("sandiego.mat+plane_gt.mat", "1", 0.9403,
     "version diff: paper uses 100x100x186 crop, frozen package is full-band 100x100x224 crop (top-left 100x100 + plane_gt)"),
]

REQUIRED_TOL = 0.01  # |Δ| <= 0.01 counts as a match (claim a)

VERIFY_SHA = {
    # expected sha256 for the files actually evaluated (from source_manifest.json)
    "abu/abu-airport-1.mat": "0705395C9922948083BDD60A2889300C30D17D901648849705B4F35157B8C780",
    "abu/abu-airport-2.mat": "7121476E700001E76191D6EE6BC6F2D5F680C0FE49186B61A57F10FCAC7718B9",
    "abu/abu-airport-3.mat": "97B574BE2DE8C1AE3158B60B4AA34676C59A218398FC096C0DCDF125A6C74495",
    "abu/abu-urban-1.mat": "951D8D9C405D7AE200634DFD5244586545C01A561B1028F0E65E09E562523942",
    "abu/abu-urban-2.mat": "ED900CBDE844582DD51943F920EAC47C3A4E7F4CF3E0AE7612FDFB80B7EE7807",
    "abu/abu-urban-3.mat": "A4E4EF3C512B72510F5852300A5050E9E544F80ABB021D79EE04921C2070598B",
    "abu/abu-urban-4.mat": "6D6B81C9688F883A9CA59FF99EBC8053C5BE1A14099960C460BA420D8507E676",
    "abu/abu-urban-5.mat": "16A50CFCA9D6C4783ADFD663E9D1E5E948DDAAD950912B58577A604C86EB64C5",
    "abu/abu-beach-1.mat": "B1FA88474FBC06F2E654E4452D8F7F98757C199197E2B7FEC1977A5C5753FCB0",
    "abu/abu-beach-2.mat": "3EC5F0C5C36B2F98A41F9D9E69946E9F3E6FDBEEE0F42B3E402485A4EFD9BB80",
    "aviris_1.mat": "C72401FD1A36C01A7EBD1EA9BC502B1A7CA25F059E2BABC5BFFA4BEBF9BFA62C",
    "aviris_2.mat": "18280633067EB196DF877A7721D4EB567D9590ECCCC311F546A9B34658AAF85B",
    "hydice_urban.mat": "A998766A7180BCACAF5D2163D57857726D80B42F64B490083DE85F072B593F4B",
    "sandiego.mat": "563799CE06AE6EFEC3B8C3EFBB39816C7722624D51736BC8E127DB0CD916FAFC",
    "plane_gt.mat": "2E97D8B4F78A8C295C2D2A7F68442B7632AD10A397ABBF07D8F38694AC17D24D",
}

# ---- data loading ----------------------------------------------------------

def _first(d, *keys):
    for k in keys:
        if k in d:
            return d[k]
    raise KeyError(f"none of {keys} in .mat (keys={[k for k in d if not k.startswith('__')]})")


def load_dataset(data_dir, file):
    """Load (data, gt_mask) for one frozen dataset file path."""
    if file.startswith("sandiego"):
        imp = sio.loadmat(os.path.join(data_dir, "sandiego.mat"))
        gt = sio.loadmat(os.path.join(data_dir, "plane_gt.mat"))
        im = _first(imp, "Sandiego", "data")
        gtm = _first(gt, "PlaneGT", "map")
        data = im[:100, :100, :]
        gtmap = gtm[:100, :100]
        return np.asarray(data), np.asarray(gtmap)
    p = os.path.join(data_dir, file)
    d = sio.loadmat(p)
    # Full 400x400x224 image; the frozen GT (plane_gt.mat) matches the
    # top-left 100x100 crop (both from HSIYJND mirror). Paper used a
    # 100x100x186 (band-reduced) crop of the same scene -> version diff.
    imp = _first(d, "data")
    gtmap = _first(d, "map")
    return imp, gtmap


def global_rx_score(data, batch=4096):
    """Global RX: Mahalanobis score (x-mu).T Sigma^+ (x-mu) over all pixels.

    mu = global mean, Sigma = global covariance (np.cov, ddof=1), Sigma^+ the
    Moore-Penrose pseudo-inverse (handles rank-deficient / colinear bands).
    Batched in column-parallel fashion to keep memory bounded.
    """
    X = data.reshape(-1, data.shape[-1]).astype(np.float64)
    mu = X.mean(axis=0)
    Xc = X - mu
    S = np.cov(Xc, rowvar=False)              # (B,B)
    Sinv = np.linalg.pinv(S)                  # pseudo-inverse
    n = X.shape[0]
    score = np.empty(n, dtype=np.float64)
    for i0 in range(0, n, batch):
        i1 = min(i0 + batch, n)
        z = Xc[i0:i1] @ Sinv                   # (m,B)
        score[i0:i1] = np.einsum("ij,ij->i", z, Xc[i0:i1])
    return score.reshape(data.shape[:2])


def pixel_auc(gt, score):
    from sklearn.metrics import roc_auc_score
    y = (np.asarray(gt) > 0).ravel()
    s = np.asarray(score).ravel()
    return float(roc_auc_score(y, s))


# ---- sha verification ------------------------------------------------------

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


# ---- main ------------------------------------------------------------------

def resolve_data_dir(cli_value):
    if cli_value:
        p = os.path.abspath(cli_value)
        if os.path.isdir(p):
            return p
        raise SystemExit(f"data dir not found: {p}")
    candidates = [
        os.environ.get("HAD_HSI_DIR"),
        r"F:\dataset\cs\2507.05730_had_survey\hsi",
        "/mnt/f/dataset/cs/2507.05730_had_survey/hsi",
        os.path.join(os.path.dirname(__file__), "..", "data", "hsi"),
        "data/hsi",
    ]
    for p in candidates:
        if p and os.path.isdir(p) and (os.path.exists(os.path.join(p, "sandiego.mat")) or os.path.exists(os.path.join(p, "abu"))):
            return p
    raise SystemExit("Could not locate the frozen hsi/ data dir. Pass --data_dir.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--data_dir", default=None, help="folder containing the frozen .mat files (incl. abu/)")
    ap.add_argument("--out_dir", default=None, help="output directory (default: <script dir>/../results)")
    args = ap.parse_args()

    if sio is None:
        raise SystemExit("scipy is required (pip install scipy)")

    data_dir = resolve_data_dir(args.data_dir)
    out_dir = os.path.abspath(args.out_dir or os.path.join(os.path.dirname(__file__), "..", "results"))
    os.makedirs(out_dir, exist_ok=True)
    print(f"[rx] data_dir = {data_dir}")
    print(f"[rx] out_dir  = {out_dir}")

    # integrity check first
    sha_rows = []
    checked = set()
    for rel, exp in VERIFY_SHA.items():
        p = os.path.join(data_dir, rel)
        got = sha256_file(p) if os.path.exists(p) else "MISSING"
        ok = got == exp
        sha_rows.append((rel, got, exp, "OK" if ok else "MISMATCH/MISSING"))
        assert ok, f"SHA-256 mismatch for {rel}"
    with open(os.path.join(out_dir, "sha256_report.tsv"), "w") as f:
        f.write("file\tsha256_actual\tsha256_expected\tstatus\n")
        for r in sha_rows:
            f.write("\t".join(r) + "\n")
    print(f"[rx] sha-256 verified {len(sha_rows)} files OK")

    rows = []
    for rel, sid, paper_auc, note in DATASETS:
        t0 = time.perf_counter()
        data, gt = load_dataset(data_dir, rel)
        score = global_rx_score(data)
        auc = pixel_auc(gt, score)
        dt = time.perf_counter() - t0

        n_pix = int(np.prod(data.shape[:2]))
        n_anom = int((np.asarray(gt) > 0).sum())
        delta = auc - paper_auc
        match = bool(abs(delta) <= REQUIRED_TOL)
        rows.append({
            "file": rel,
            "survey_id": sid,
            "n_anomaly": n_anom,
            "auc_rx": round(auc, 4),
            "auc_paper_rx": paper_auc,
            "delta": round(delta, 4),
            "match_le_0_01": match,
            "runtime_s": round(dt, 4),
            "note": note,
            "row_type": "data",
        })
        print(f"  {rel:>30s}  id={sid:<5s} auc={auc:.4f} paper={paper_auc:.4f} "
              f"delta={delta:+.4f} match={match}  {dt:.3f}s")

    n_match = sum(r["match_le_0_01"] for r in rows)
    aucs = [r["auc_rx"] for r in rows]
    rt = [r["runtime_s"] for r in rows]
    summary = {
        "n_cases": len(rows),
        "n_match_le_0_01": n_match,
        "min_auc": round(float(min(aucs)), 4),
        "max_auc": round(float(max(aucs)), 4),
        "mean_auc": round(float(np.mean(aucs)), 4),
        "mean_runtime_s": round(float(np.mean(rt)), 4),
        "max_runtime_s": round(float(max(rt)), 4),
        "tol": REQUIRED_TOL,
        "all_auc_ge_0_80": bool(min(aucs) >= 0.80),
        "data_dir": data_dir,
    }
    print("\n[rx] SUMMARY:", json.dumps(summary, indent=2))

    # CSV
    import csv
    cols = ["row_type", "file", "survey_id", "n_anomaly", "auc_rx", "auc_paper_rx",
            "delta", "match_le_0_01", "runtime_s", "note"]
    with open(os.path.join(out_dir, "evidence_table.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
        w.writerow({"file": "SUMMARY",
                    "survey_id": f"n_match={int(n_match)}",
                    "n_anomaly": f"min_auc={min(aucs):.4f}",
                    "auc_rx": f"mean_auc={np.mean(aucs):.4f}",
                    "auc_paper_rx": f"max_auc={max(aucs):.4f}",
                    "delta": f"mean_runtime_s={np.mean(rt):.4f}",
                    "match_le_0_01": f"max_runtime_s={max(rt):.4f}",
                    "runtime_s": "",
                    "note": f"all_auc_ge_0_80={bool(min(aucs) >= 0.80)}; tol={REQUIRED_TOL}",
                    "row_type": "summary"})
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("[rx] wrote", os.path.join(out_dir, "evidence_table.csv"))
    print("[rx] wrote", os.path.join(out_dir, "summary.json"))


if __name__ == "__main__":
    sys.exit(main())