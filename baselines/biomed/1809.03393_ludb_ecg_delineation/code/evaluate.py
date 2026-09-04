"""Evaluation under ANSI/AAMI EC57:1998 tolerance (+/-150 ms).

For each (record, lead, point_type): produce detection/reference time lists,
greedy nearest match within tolerance => TP/FP/FN, Se/PPV, and time error.
"""
import numpy as np
from common import TOL_SAMP, POINT_TYPES, FS, LEADS

# how to extract the three sub-points of each wave triple
WAVE_ATTRS = {"qrs": "qrs", "p": "p", "t": "t"}
SUB = {"onset": 0, "peak": 1, "offset": 2}


def matcher(dets, refs, tol=TOL_SAMP, lo=None, hi=None):
    """Greedy nearest-neighbour matching within tol. Returns:
    (tp, fp, fn, errors_ms_list).
    Only detections in [lo, hi] (inclusive) are counted (evaluation window).
    Each detection is matched to its closest still-unused reference within tol;
    each reference matched at most once.
    """
    if lo is not None:
        dets = [int(d) for d in dets if d >= lo and d <= hi]
    else:
        dets = list(dets)
    refs = sorted([int(r) for r in refs])
    dets = sorted([int(d) for d in dets])
    used_ref = set()
    errors = []
    for d in dets:
        best = None
        best_d = 1e9
        for j, r in enumerate(refs):
            if j in used_ref:
                continue
            dd = abs(d - r)
            if dd < best_d:
                best_d = dd
                best = j
        if best is not None and best_d <= tol:
            used_ref.add(best)
            errors.append(d - refs[best])
    tp = len(errors)
    fp = len(dets) - tp
    fn = len(refs) - tp
    return tp, fp, fn, errors


def point_lists(pack, wave, sub, lead):
    """Turn per-lead annotation pack into time lists for a sub-point.

    pack = {'qrs': [...], 'p': [...], 't': [...]} entries are triples.
    Returns list of sample times (or empty).
    """
    tris = pack.get(wave, [])
    idx = SUB[sub]
    out = [t[idx] for t in tris if t[idx] is not None]
    return out


def reference_times(waves_parsed, wave, sub):
    tris = waves_parsed.get(wave, [])
    idx = SUB[sub]
    return [t[idx] for t in tris if t[idx] is not None]


def evaluate_record(pred_pack, ref_pack, window=None):
    """Evaluate one record * all leads * all point types.

    pred_pack: {lead: {'qrs':[(on,p,off)], 'p':[], 't':[]}}
    ref_pack:  {lead: {'qrs':[(on,p,off)], 'p':[], 't':[]}}  (from annotations)
    window:    dict {(lead, wave_type): (lo, hi)} for THIS record, or None.
    Returns list of dict rows and errors accumulation.
    """
    rows = []
    errors = {}
    for pt in POINT_TYPES:
        wave, sub = pt.split("_", 1)
        tp = fp = fn = 0
        errs = []
        lead_list = [lead for lead in pred_pack if lead in ref_pack]
        for lead in lead_list:
            d = point_lists(pred_pack[lead], wave, sub, lead)
            r = reference_times(ref_pack[lead], wave, sub)
            if not r:
                # no reference annotations of this type in this lead ->
                # nothing to score; skip the lead entirely (no TP/FP/FN)
                continue
            lo, hi = window.get((lead, wave), (None, None)) if window else (None, None)
            t, f, fn_, e = matcher(d, r, lo=lo, hi=hi)
            tp += t
            fp += f
            fn += fn_
            errs.extend(e)
        errors[pt] = errs
        rows.append({"point_type": pt, "tp": tp, "fp": fp, "fn": fn,
                     "errors_ms": list(errs)})
    return rows, errors


def aggregate(rows_list):
    """Aggregate per-record rows into a summary table.

    rows_list may be a list of lists (per record) or a flat list of rows.
    """
    if rows_list and isinstance(rows_list[0], list):
        flat = [row for rec in rows_list for row in rec]
    else:
        flat = rows_list
    acc = {pt: {"tp": 0, "fp": 0, "fn": 0} for pt in POINT_TYPES}
    all_errs = {pt: [] for pt in POINT_TYPES}
    for row in flat:
        acc[row["point_type"]]["tp"] += row["tp"]
        acc[row["point_type"]]["fp"] += row["fp"]
        acc[row["point_type"]]["fn"] += row["fn"]
        all_errs[row["point_type"]].extend(row["errors_ms"])

    summary = []
    for pt in POINT_TYPES:
        tp = acc[pt]["tp"]
        fp = acc[pt]["fp"]
        fn = acc[pt]["fn"]
        se = tp / (tp + fn) * 100.0 if (tp + fn) else float("nan")
        ppv = tp / (tp + fp) * 100.0 if (tp + fp) else float("nan")
        e = np.array(all_errs[pt], dtype=float)
        m = float(np.mean(e)) if e.size else float("nan")
        sd = float(np.std(e)) if e.size else float("nan")
        summary.append({
            "point_type": pt, "se": se, "ppv": ppv,
            "mean_err_ms": m, "std_err_ms": sd,
            "tp": tp, "fp": fp, "fn": fn,
        })
    return summary