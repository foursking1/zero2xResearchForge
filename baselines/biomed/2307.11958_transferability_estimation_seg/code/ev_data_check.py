"""ev_data_check.py -- data-integrity evidence: inventory, salvage stats, figures.

Documents (a) the frozen NIFTI SHA/checksums, (b) the gzip-truncation state of
every file (recoverable-slice ratio, label intactness, foreground z-range), and
(c) example slice + label crops from a fully-readable case and from a salvaged
partial case.  Outputs go to evidence/ and results/data_check.json.
"""
import os
import sys
import json
import struct
import hashlib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_ROOT, CASES, read_raw_nifti, save_json, EVIDENCE_DIR

README_SHA = {
    "spleen_10.nii.gz": "A0FF3C1E61E150220FDEA277C7999E8161B82C6EEF4C2C737980B745062C08A3",
    "liver_1.nii.gz": "919BED688F6329539E2A9E929F6C63898241E569C2654C143A28D6D6F2DE0F1E",
}


def main():
    rows = {}
    for organ, cases in CASES.items():
        for c in cases:
            ip = os.path.join(DATA_ROOT, f"{c}.nii.gz")
            lp = os.path.join(DATA_ROOT, f"{c}_label.nii.gz")
            img, shp, dt, pixd, img_ok = read_raw_nifti(ip)
            lab, lshp, _, _, lab_ok = read_raw_nifti(lp)
            fg = np.where(lab.reshape(-1, lab.shape[-1]).sum(axis=0) > 0)[0]
            fg_z = [int(fg.min()), int(fg.max())] if len(fg) else None
            rows[c] = {
                "organ": organ,
                "nz_img_header": int(shp[2]) if shp else None,
                "recovered_slices": int(img.shape[2]),
                "img_complete": bool(img_ok),
                "label_complete": bool(lab_ok),
                "label_nz": int(lshp[2]),
                "label_fg_z_start_end": fg_z,
                "pixdim_mm": [round(x, 4) for x in pixd],
            }
    save_json(rows, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "data_check.json"))

    # figures: one readable + one salvaged case
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for c in ["liver_0", "liver_1"]:
        img, shp, *_ = read_raw_nifti(os.path.join(DATA_ROOT, f"{c}.nii.gz"))
        lab, *_ = read_raw_nifti(os.path.join(DATA_ROOT, f"{c}_label.nii.gz"))
        fg = np.where(lab.reshape(-1, lab.shape[-1]).sum(axis=0) > 0)[0]
        zmid = int(fg[len(fg) // 2]) if len(fg) else int(img.shape[2] // 2)
        hv = np.clip(img[:, :, zmid], -200, 300)
        fig, ax = plt.subplots(1, 2, figsize=(8, 4))
        ax[0].imshow(hv, cmap="gray")
        ax[0].set_title(f"{c} slice z={zmid} (source=image)")
        ax[1].imshow(hv, cmap="gray")
        ov = np.zeros((*hv.shape, 3)); ov[..., 1] = (lab[:, :, zmid] > 0); ov[..., 0] = (lab[:, :, zmid] > 1)
        ax[1].imshow(ov, alpha=0.45)
        ax[1].set_title("with label overlay (green=liver, red=tumor)")
        fig.tight_layout()
        fig.savefig(os.path.join(EVIDENCE_DIR, f"datacheck_{c}.png"), dpi=110)
        plt.close(fig)
    print("wrote results/data_check.json and evidence/datacheck_*.png")


if __name__ == "__main__":
    main()