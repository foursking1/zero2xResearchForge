# -*- coding: utf-8 -*-
"""Run the official DASH (v06) model on the frozen 69 OzDES spectra.

arXiv:1903.02557 (Muthukrishna et al. 2019, MNRAS) claim verification.

Environment:
  - Python 3.13 (the ``envs/default`` venv), tensorflow-cpu 2.21 (TF1-compat
    graph mode via tensorflow.compat.v1), astrodash 1.0.22.
  - The frozen official model ``models_v06.zip`` is extracted into the
    astrodash package directory (models_v06/models/...).
  - numpy 2.x removed two behaviours astrodash 1.0.22 relied on:
      1) constructing a ragged object array ``np.array([[np.zeros(nw), ...]])``
      2) ``snInfos != []`` broadcasting against an array.
    We monkeypatch the two astrodash functions at runtime (the installed
    package files are left untouched) to make the official code run under
    numpy 2.x.  These are pure compatibility shims, not model changes.

Matching (paper Sec.5.2 / TASK 3.2):
  - Subtypes are collapsed to broad classes: Ia = {Ia-norm, Ia-91T, Ia-91bg,
    Ia-csm, Ia-02cx, Ia-pec}, II = {IIP, IIL, IIn}, Ibc = {Ib-norm, Ibn, IIb,
    Ib-pec, Ic-norm, Ic-broad, Ic-pec}.
  - ATel labels with ``?`` are mapped to the uncertain member of that broad
    class (still matched at broad-class level).
  - A DASH top-1 of ``Ic-broad`` is, per the paper, host contamination rather
    than a real Ic-broad; it is reported separately and NOT counted as a match.
"""
import os
import sys
import csv
import json
import time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dash_data

# ---------------------------------------------------------------------------
# numpy-2.x compatibility shims for astrodash 1.0.22 (no package files touched)
# ---------------------------------------------------------------------------
import astrodash.classify as _clf


def _patched_get_templates(snName, snAge, hostName, snTemplates, galTemplates, nw):
    snInfos = np.copy(snTemplates[snName][snAge]["snInfo"])
    snNames = np.copy(snTemplates[snName][snAge]["names"])
    if hostName != "No Host" and hostName != "":
        hostInfos = np.copy(galTemplates[hostName]["galInfo"])
        hostNames = np.copy(galTemplates[hostName]["names"])
    else:
        hostInfos = np.empty((1, 4), dtype=object)
        hostInfos[0, 0] = np.zeros(nw)
        hostInfos[0, 1] = np.zeros(nw)
        hostInfos[0, 2] = 1
        hostInfos[0, 3] = nw - 1
        hostNames = np.array(["No Host"])
    return snInfos, snNames, hostInfos, hostNames


_clf.get_templates = _patched_get_templates


def _patched_rlap_warning_label(self, bestType, inputImage, inputMinMaxIndex):
    """numpy-2.x-safe version of astrodash.classify.rlap_warning_label.

    The original compares ``snInfos != []`` which numpy 2.x refuses.  We keep
    the original semantics (``len(snInfos) > 0``) and, when rlap scoring is on,
    call the original RlapCalc code path guarded against further numpy-2 issues.
    """
    from astrodash.classify import classification_split
    from astrodash.read_binned_templates import get_templates
    host, name, age = classification_split(bestType)
    snInfos, snNames, hostInfos, hostNames = get_templates(
        name, age, host, self.snTemplates, self.galTemplates, self.nw)
    if len(snInfos) > 0:
        if self.rlapScores:
            try:
                from astrodash.false_positive_rejection import RlapCalc
                templateImages = snInfos[:, 1]
                templateMinMaxIndexes = list(zip(snInfos[:, 2], snInfos[:, 3]))
                rlapCalc = RlapCalc(inputImage, templateImages, snNames, self.wave,
                                    inputMinMaxIndex, templateMinMaxIndexes)
                rlap, rlapWarningBool = rlapCalc.rlap_label()
                if rlapWarningBool:
                    rlapLabel = "Low rlap: {0}".format(rlap)
                else:
                    rlapLabel = "Good rlap: {0}".format(rlap)
            except Exception as e:  # numpy-2 incompatibility deeper in RlapCalc
                rlapLabel = "rlap-unavailable: {0}".format(type(e).__name__)
                rlapWarningBool = "None"
        else:
            rlapLabel = "No rlap"
            rlapWarningBool = "None"
    else:
        rlapLabel = "(NO_TEMPLATES)"
        rlapWarningBool = "None"
    return rlapLabel, rlapWarningBool


_clf.Classify.rlap_warning_label = _patched_rlap_warning_label


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------
def parse_top1(top1_string):
    """astrodash type string -> (subtype, age).  Format: 'host: name: age' or 'name: age'."""
    from astrodash.classify import classification_split
    host, name, age = classification_split(top1_string)
    return name, age, host


def main():
    spectra, stats = dash_data.build_spectrum_table()
    # order spectra the same way dash_data does (glob sorted)
    files = [s["file"] for s in spectra]
    zs = [s["redshift"] if s["redshift"] is not None else 0.0 for s in spectra]
    labels = [s["atel_type"] for s in spectra]

    print(f"[dash] classifying {len(files)} spectra with knownZ=True, smooth=6 ...")
    from astrodash import Classify
    from astrodash.classify import classification_split
    from astrodash.false_positive_rejection import combined_prob

    t_total0 = time.perf_counter()
    c = Classify(filenames=files, redshifts=zs, knownZ=True, smooth=6,
                 rlapScores=True)
    t_setup = time.perf_counter() - t_total0

    t0 = time.perf_counter()
    best_types, softmaxes, best_labels, imgs, minmax = c._input_spectra_info()
    t_class = time.perf_counter() - t0
    print(f"[dash] forward pass for {len(files)} spectra in {t_class:.2f}s "
          f"(model+setup {t_setup:.2f}s)")

    rows = []
    for i, s in enumerate(spectra):
        # top-20 match list (same structure astrodash.list_best_matches builds)
        bestMatchList = []
        for k in range(20):
            host, name, age = classification_split(best_types[i][k])
            prob = float(softmaxes[i][k])
            bestMatchList.append((host, name, age, prob))
        # Reliable flag from the paper's combined-probability logic
        try:
            bestName, bestAge, probTotal, reliableFlag = combined_prob(bestMatchList)[1:]
        except Exception as e:
            bestName, bestAge, probTotal, reliableFlag = (None, None, None,
                                                          "unavailable")

        top1 = best_types[i][0]
        subtype, age, host = parse_top1(top1)
        prob = float(softmaxes[i][0])
        # rlap diagnostic via the (patched) astrodash rlap_warning_label
        try:
            rlap_label, rlap_warn = c.rlap_warning_label(
                top1, imgs[i], minmax[i])
        except Exception as e:
            rlap_label, rlap_warn = "rlap-failed: {0}".format(type(e).__name__), "None"

        broad, unc, icb = dash_data.atel_to_broad(subtype)
        atel_broad, atel_unc, atel_icb = dash_data.atel_to_broad(s["atel_type"])

        # paper convention: Ic-broad predicted is NOT counted as a match
        if subtype == "Ic-broad":
            match = "ICBROAD_EXCLUDED"
        elif broad is not None and atel_broad is not None:
            match = "MATCH" if broad == atel_broad else "MISMATCH"
        else:
            match = "UNKNOWN"

        rows.append({
            "file": os.path.basename(s["file"]),
            "obj": s["obj"],
            "epoch": s["epoch"],
            "redshift": s["redshift"],
            "atel_type": s["atel_type"],
            "atel_broad": atel_broad,
            "atel_uncertain": s["uncertain"],
            "dash_top1": subtype,
            "dash_host": host,
            "dash_age": age,
            "dash_prob": prob,
            "dash_broad": broad,
            "dash_uncertain": unc,
            "rlap": rlap_label,
            "reliable": reliableFlag,
            "match": match,
        })

    # ---- match rates (paper Sec.5.2 convention) ----
    total = len(rows)
    counted = [r for r in rows if r["match"] in ("MATCH", "MISMATCH")]
    excluded = [r for r in rows if r["match"] == "ICBROAD_EXCLUDED"]
    n_match = sum(r["match"] == "MATCH" for r in counted)
    overall = n_match / len(counted) if counted else float("nan")

    # per broad-label type (count only spectra whose ATel label maps to a broad class)
    from collections import defaultdict
    per_type = defaultdict(lambda: {"match": 0, "count": 0, "excluded": 0})
    for r in rows:
        key = r["atel_broad"]
        if key is None:
            key = "UNKNOWN"
        if r["match"] == "ICBROAD_EXCLUDED":
            per_type[key]["excluded"] += 1
        else:
            per_type[key]["count"] += 1
            if r["match"] == "MATCH":
                per_type[key]["match"] += 1
    per_type_rates = {}
    for k, v in per_type.items():
        per_type_rates[k] = {
            "match": v["match"],
            "count": v["count"],
            "rate": (v["match"] / v["count"]) if v["count"] else float("nan"),
            "icbroad_excluded": v["excluded"],
        }

    # ---- outputs ----
    outdir = os.path.normpath(os.path.join(HERE, "..", "results"))
    os.makedirs(outdir, exist_ok=True)

    t_total = time.perf_counter() - t_total0

    with open(os.path.join(outdir, "dash_predictions.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "obj", "epoch", "redshift", "atel_type", "atel_broad",
                    "dash_top1", "dash_broad", "dash_prob", "rlap", "reliable",
                    "match"])
        for r in rows:
            w.writerow([r["file"], r["obj"], r["epoch"], r["redshift"],
                        r["atel_type"], r["atel_broad"], r["dash_top1"],
                        r["dash_broad"], f"{r['dash_prob']:.4f}",
                        r["rlap"], r["reliable"], r["match"]])

    # specific objects used in paper Table 2 / rubric B2 spot-check
    spot = {}
    for obj in ("DES16C3bq", "DES16E2aoh"):
        cands = [r for r in rows if r["obj"] == obj]
        spot[obj] = [{"epoch": r["epoch"], "dash_top1": r["dash_top1"],
                      "dash_broad": r["dash_broad"], "prob": r["dash_prob"],
                      "match": r["match"]} for r in cands]

    metrics = {
        "task": "1903.02557_dash_supernova_class",
        "n_spectra": total,
        "n_counted_match_or_mismatch": len(counted),
        "n_icbroad_excluded": len(excluded),
        "n_match": n_match,
        "overall_match_rate": overall,
        "per_type": per_type_rates,
        "spot_check": spot,
        "time_model_setup_s": t_setup,
        "time_forward_pass_s": t_class,
        "time_total_wall_s": t_total,
        "smooth": 6,
        "knownZ": True,
        "model": "v06 (zeroZ)",
        "device": "CPU",
        "python": sys.version.split()[0],
        "tensorflow": "2.21.0 (tf.compat.v1 graph mode)",
        "astrodash": "1.0.22",
        "numpy_compat_shims": ["get_templates", "rlap_warning_label"],
        "paper_table1": {
            "overall": "197/212=0.929",
            "Ia": "127/129=0.984",
            "II": "25/28=0.893",
            "Ibc": "1/1=1.0",
        },
    }
    with open(os.path.join(outdir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2, default=float)

    # console summary
    print(f"\n=== DASH match summary ===")
    print(f"overall match rate: {n_match}/{len(counted)} = {overall:.4f} "
          f"(counted; {len(excluded)} Ic-broad predictions excluded per paper)")
    for k, v in per_type_rates.items():
        print(f"  {k:5s}: {v['match']}/{v['count']} = {v['rate']:.4f} "
              f"(icbroad_excluded={v['icbroad_excluded']})")
    print(f"time: setup {t_setup:.2f}s + forward {t_class:.2f}s = "
          f"total wall {t_total:.2f}s for {total} spectra in one batch")
    print("spot-check:", json.dumps(spot, default=float))
    print("wrote dash_predictions.csv and metrics.json")


if __name__ == "__main__":
    main()
