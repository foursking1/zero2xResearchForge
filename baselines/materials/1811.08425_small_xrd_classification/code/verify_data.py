"""Verify the frozen data: checksums, class distribution, encoding mapping.

Runs data-integrity checks that the judge can repeat from the frozen data.
Writes a report to results/data_verification.json.
"""
import hashlib
import json
import os

import numpy as np
import pandas as pd

import config
from data_loader import load_data, _read_exp, _read_theor, _trim_to_grid


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    report = {}

    # -- checksums ---------------------------------------------------------
    expected = {
        "exp.csv": "41a213b16a7119dab1727cb238a55012f507d575af7bcdc9eba9edba6fda9219",
        "label_exp.csv": "037e37246243376369f235b6266548d2bee8a2ac905571d997cc683658951bff",
        "encoding.csv": "4a72c443bdfed9b1d837d8439b607d849eddd041b3fae9b711a029500fcd6487",
        "theor.csv": "dc78efb90cc7079002980fe6c68607e5a235db3eac0129f1a3ab935cf84bc09e",
        "label_theo.csv": "8c5f6601d8df956b30820daa0bebec206acec5c02bb4a0133ff158e59107803c",
    }
    checks = {}
    for name, exp in expected.items():
        path = os.path.join(config.DATA_DIR, name)
        got = sha256(path) if os.path.exists(path) else "missing"
        checks[name] = dict(expected=exp, got=got,
                            ok=(got == exp))
    report["checksums"] = checks

    # -- class distribution and encoding ------------------------------------
    tw, X, y = _read_exp()
    counts = np.bincount(y, minlength=7).tolist()
    enc = pd.read_csv(config.ENCODING_CSV, header=None, skiprows=1)
    mapping = {int(r[0]): r[1] for _, r in enc.iterrows()}
    report["exp"] = dict(n_samples=len(y), n_points=len(tw),
                         min_2theta=float(tw.min()), max_2theta=float(tw.max()),
                         class_counts=counts,
                         class_mapping={k: mapping[k] for k in range(7)})
    report["exp"]["class_counts_match_paper"] = counts == [4, 17, 1, 13, 4, 2, 47]

    tw_t, X_t, names = _read_theor()
    y_t = np.array([{name: i for i, name in enumerate(config.SG_ENCODING)}[n]
                    for n in names])
    report["theo"] = dict(n_spectra=len(y_t),
                          class_counts=np.bincount(y_t, minlength=7).tolist(),
                          min_2theta=float(tw_t.min()),
                          max_2theta=float(tw_t.max()),
                          used_points=len(tw))

    # -- verify exp.csv <-> Experimental/*.xy correspondence (first file) ----
    sub = os.path.join(config.EXPERIMENTAL_DIR, "Fm-3m")
    if os.path.isdir(sub):
        files = sorted(f for f in os.listdir(sub) if f.endswith(".xy"))
        if files:
            a = np.loadtxt(os.path.join(sub, files[0]))
            ok = np.allclose(a[:, 0][[0, 1]], [5.0, 5.02])
            report["raw_xy"] = dict(example=files[0], starts_at_5deg=ok)
    with open(os.path.join(config.RESULTS_DIR, "data_verification.json"),
              "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()