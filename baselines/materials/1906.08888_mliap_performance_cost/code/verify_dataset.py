"""Independent check of the frozen data (rubric evidence field B):
  - recompute frozen-JSON configuration counts (Mo train=194, test=23;
    Cu train=262, test=31; all six elements);
  - random-sample one JSON record and cross-check energy/forces / num_atoms
    round-trip through our parser against the raw JSON fields.

Writes a human-readable transcript and an evidence CSV.
"""
import json
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from io_data import load_configs, load_mo930, config_targets, structure_to_arrays

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
ELEMENTS = ["Li", "Mo", "Cu", "Ni", "Si", "Ge"]
EXPECTED_TRAIN = {"Li": 241, "Mo": 194, "Cu": 262, "Ni": 263, "Si": 214, "Ge": 228}
EXPECTED_TEST = {"Li": 29, "Mo": 23, "Cu": 31, "Ni": 31, "Si": 25, "Ge": 25}


def main():
    random.seed(0)
    lines = []
    lines.append("Frozen-data verification transcript")
    lines.append("=" * 60)
    ok = True
    for el in ELEMENTS:
        tr = load_configs(el, "train")
        te = load_configs(el, "test")
        c_tr, c_te = len(tr), len(te)
        stat_tr = (c_tr == EXPECTED_TRAIN[el])
        stat_te = (c_te == EXPECTED_TEST[el])
        ok &= stat_tr and stat_te
        lines.append(f"{el:2s} train={c_tr} (expected {EXPECTED_TRAIN[el]}) {'OK' if stat_tr else 'MISMATCH'}  "
                     f"test={c_te} (expected {EXPECTED_TEST[el]}) {'OK' if stat_te else 'MISMATCH'}")
    mo930 = load_mo930()
    lines.append(f"Mo930 = {len(mo930)} (expected 930) {'OK' if len(mo930) == 930 else 'MISMATCH'}")
    ok &= (len(mo930) == 930)
    lines.append("")
    lines.append("Random-record cross-check (raw JSON vs our parser):")
    checks = []
    for el in ["Cu", "Mo", "Si"]:
        cfg = load_configs(el, "train")[random.randrange(0, 180)]
        E, F = config_targets(cfg)
        lat, frac, cart, names = structure_to_arrays(cfg)
        rawE = cfg["outputs"]["energy"]
        rawF = np.asarray(cfg["outputs"]["forces"])
        n_raw = cfg["num_atoms"]
        lines.append(f"  {el}: num_atoms raw={n_raw} parsed={len(cart)}  |E_unparsed-E_parsed|<1e-10 "
                     f"{(abs(rawE - E) < 1e-10)}  |F matrix equal| {np.allclose(rawF, F)}  "
                     f"|site names| {all(names[i] == cfg['structure']['sites'][i]['species'][0]['element'] for i in range(len(names)))}")
        checks.append((el, n_raw, float(rawE), float(np.abs(rawF).mean())))
        ok &= (n_raw == len(cart)) and (abs(rawE - E) < 1e-10) and np.allclose(rawF, F)
    lines.append("")
    lines.append("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    lines.append("")
    transcript = "\n".join(lines)
    print(transcript)

    with open(os.path.join(RESULTS_DIR, "verify_transcript.txt"), "w") as f:
        f.write(transcript + "\n")
    with open(os.path.join(RESULTS_DIR, "verify_evidence.csv"), "w") as f:
        f.write("element,energy_eV,mean_abs_force_eV_ang,n_atoms\n")
        for el, n, e, fm in checks:
            f.write(f"{el},{e},{fm:.6f},{n}\n")

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()