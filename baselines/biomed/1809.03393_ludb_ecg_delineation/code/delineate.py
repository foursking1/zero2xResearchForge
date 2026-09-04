"""Per-lead delineation and multi-lead cross-lead consensus correction.

Pipeline (multi-lead method, mirroring Kalyakulina et al.):
  1. For each lead independently: QRS detection (Pan-Tompkins) with R
     refinement and onset/offset from a wide-band slope method.
  2. P and T detection per beat per lead inside windows relative to that
     lead's own QRS onset (P) and offset (T).
  3. CROSS-LEAD CONSISTENCY on QRS beats:
       * detected in >= 8/12 leads -> complex exists; reference points
         (onset/peak/offset) averaged across the detecting leads;
       * detected in <= 4/12 leads -> cancel (absent);
       * detected in   5..8/12 leads -> no correction, per-lead kept.
  4. Same >=8 / 5-8 / <=4 consensus applied to P and T existence and times.
  5. Output per-lead annotation packs: {'qrs': [tri], 'p': [tri], 't': [tri]}.
"""
from itertools import groupby
import numpy as np

from common import FS, NSAMP, LEADS, NLEADS
from qrs import QRSDetector, refine_r_peak, qrs_onset_offset
from waves import detect_p_wave, detect_t_wave, per_lead_filtered

BEAT_MERGE_TOL = int(0.16 * FS)  # 160 ms max spread for same-beat identity
P_THRESH_HARD = 8                # >= 8/12 -> exists & average
P_THRESH_SOFT = NLEADS // 3      # <= 4   -> cancel


def per_lead_delineation(lead):
    """Run the core single-lead detector on ONE lead.

    Returns dict with 'beats': list of
    {'qrs': (on, peak, off), 'p': triple|None, 't': triple|None}.
    """
    x = lead.astype(float)
    det = QRSDetector(fs=FS)
    peaks = det.detect(x)
    peaks = refine_r_peak(x, peaks)
    xf = per_lead_filtered(x)

    beats = []
    for r in peaks:
        on, off = qrs_onset_offset(x, r, filter_low=1.0, filter_high=30.0)
        beats.append({"qrs": (on, int(r), off),
                      "p": None, "t": None})
    beats.sort(key=lambda b: b["qrs"][1])

    for i, b in enumerate(beats):
        qon, qpeak, qoff = b["qrs"]
        prev_qrs_off = beats[i - 1]["qrs"][2] if i > 0 else 0
        next_qrs_on = beats[i + 1]["qrs"][0] if i < len(beats) - 1 else NSAMP
        b["p"] = detect_p_wave(xf, qon, prev_qrs_off, fs=FS)
        b["t"] = detect_t_wave(xf, qoff, next_qrs_on, fs=FS)
    return {"beats": beats}


# ---------------------------------------------------------------------------
# Cross-lead consensus
# ---------------------------------------------------------------------------
def build_beats(per_lead):
    """Cluster per-lead QRS beats into cross-lead beat clusters.

    per_lead: dict lead -> {'beats':[...]} as from per_lead_delineation.
    Returns list of beat clusters, each:
      {'leadmap': {lead: beat_index}, 'peak_estimates': [peak,...],
       'on_mean','peak_mean','off_mean'}
    """
    all_events = []
    for lead in LEADS:
        for bi, b in enumerate(per_lead[lead]["beats"]):
            pk = b["qrs"][1]
            all_events.append((pk, lead, bi))
    all_events.sort(key=lambda t: t[0])

    clusters = []
    for ev in all_events:
        if not clusters:
            clusters.append([ev])
            continue
        cur = clusters[-1]
        med = np.median([e[0] for e in cur])
        if abs(ev[0] - med) <= BEAT_MERGE_TOL:
            cur.append(ev)
        else:
            clusters.append([ev])

    beats = []
    for cl in clusters:
        beat = {"leadmap": {lead: bi for pk, lead, bi in cl},
                "peaks": [pk for pk, _, _ in cl],
                "ons": [per_lead[lead]["beats"][bi]["qrs"][0] for _, lead, bi in cl],
                "offs": [per_lead[lead]["beats"][bi]["qrs"][2] for _, lead, bi in cl]}
        beat["peak_mean"] = float(np.mean(beat["peaks"]))
        beat["on_mean"] = float(np.mean(beat["ons"]))
        beat["off_mean"] = float(np.mean(beat["offs"]))
        beats.append(beat)
    beats.sort(key=lambda b: b["peak_mean"])
    return beats


def _consensus(triples, n_leads_detected):
    """Given per-lead triples (each may be None) for a wave, apply the
    >=8 / 5-8 / <=4 rule. Returns (mode, payload):
      mode 'absent', mode 'keep' (per-lead {lead:tri}), mode 'mean' => tri.
    """
    detected = [t for t in triples.values() if t is not None]
    n = len(detected)
    if n <= P_THRESH_SOFT:
        return ("absent", None)
    if n < P_THRESH_HARD:
        return ("keep", {lead: tri for lead, tri in triples.items() if tri is not None})
    # >= 8
    on = [t[0] for t in detected if t[0] is not None]
    pk = [t[1] for t in detected if t[1] is not None]
    off = [t[2] for t in detected if t[2] is not None]
    m_on = float(np.mean(on)) if on else None
    m_pk = float(np.mean(pk)) if pk else None
    m_off = float(np.mean(off)) if off else None
    tri = (int(round(m_on)) if m_on is not None else None,
           int(round(m_pk)) if m_pk is not None else None,
           int(round(m_off)) if m_off is not None else None)
    return ("mean", tri)


def delineate_record_multilead(sig):
    """Full multi-lead pipeline for one 12-lead record.

    Returns {lead: {'qrs':[tri...], 'p':[tri..], 't':[tri..]}}.
    """
    per_lead = {}
    for li, lead in enumerate(LEADS):
        per_lead[lead] = per_lead_delineation(sig[:, li])

    beats = build_beats(per_lead)

    # decide QRS existence / corrected times
    qrs_decision = []  # per beat: ('absent'|('keep',{lead:tri})|('mean',tri))
    for beat in beats:
        n = len(beat["leadmap"])
        triples = {lead: per_lead[lead]["beats"][bi]["qrs"]
                   for lead, bi in beat["leadmap"].items()}
        qrs_decision.append(_consensus(triples, n))

    # P / T consensus per beat using per-lead detections within the beat
    p_decision = []
    t_decision = []
    for beat in beats:
        ptri = {}
        ttri = {}
        for lead, bi in beat["leadmap"].items():
            ptri[lead] = per_lead[lead]["beats"][bi]["p"]
            ttri[lead] = per_lead[lead]["beats"][bi]["t"]
        p_decision.append(_consensus(ptri, len(beat["leadmap"])))
        t_decision.append(_consensus(ttri, len(beat["leadmap"])))

    out = {lead: {"qrs": [], "p": [], "t": []} for lead in LEADS}
    for beat, qd, pd, td in zip(beats, qrs_decision, p_decision, t_decision):
        # ---- QRS ----
        if qd[0] == "absent":
            continue
        if qd[0] == "keep":
            for lead, tri in qd[1].items():
                out[lead]["qrs"].append(tri)
        else:
            tri = qd[1]
            for lead in LEADS:
                out[lead]["qrs"].append(tri)

        # ---- P ----
        if pd[0] == "absent":
            pass
        elif pd[0] == "keep":
            for lead, tri in pd[1].items():
                out[lead]["p"].append(tri)
        else:
            tri = pd[1]
            for lead in LEADS:
                out[lead]["p"].append(tri)

        # ---- T ----
        if td[0] == "absent":
            pass
        elif td[0] == "keep":
            for lead, tri in td[1].items():
                out[lead]["t"].append(tri)
        else:
            tri = td[1]
            for lead in LEADS:
                out[lead]["t"].append(tri)

    for lead in LEADS:
        for k in ("qrs", "p", "t"):
            out[lead][k].sort(key=lambda t: t[1] if t[1] is not None else 0)
    return out


def delineate_single_lead(sig, lead_index=1):
    """Single-lead baseline: same core detector on ONE lead (lead II by
    default), NO cross-lead correction."""
    x = sig[:, lead_index].astype(float)
    res = per_lead_delineation(x)
    lead = LEADS[lead_index]
    out = {lead: {"qrs": [], "p": [], "t": []}}
    for b in res["beats"]:
        out[lead]["qrs"].append(b["qrs"])
        if b["p"] is not None:
            out[lead]["p"].append(b["p"])
        if b["t"] is not None:
            out[lead]["t"].append(b["t"])
    return out