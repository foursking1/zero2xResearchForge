"""QU-BraTS uncertainty evaluation metrics -- faithful, array-based port of the
official challenge code (https://github.com/RagMeh11/QU-BraTS, file
BraTS_Seg_Uncertainty.py, and paper Equation 1).

Per patient/volume and per tumor entity (WT/TC/ET):
  * uncertainty maps normalised to [0, 100]
  * thresholds tau in {100, 100-dt, ..., 0}; voxels with uncertainty > tau are
    "filtered" (treated as removed)
  * DSC(tau)  : Dice on the remaining (unfiltered) voxels only
  * FTP(tau)  : ratio of filtered TRUE POSITIVES  = (TP_tau=100 - TP_tau)/TP_tau=100
  * FTN(tau)  : ratio of filtered TRUE NEGATIVES  = (TN_tau=100 - TN_tau)/TN_tau=100
  * AUC1 = auc(DSC vs tau)/100,  AUC2 = auc(FTP vs tau)/100, AUC3 = auc(FTN vs tau)/100
  * score_entity = (AUC1 + (1 - AUC2) + (1 - AUC3)) / 3    (paper Eq. 1)
"""
import numpy as np
from sklearn.metrics import auc

EPS = np.finfo(np.float32).eps


def dice_metric(ground_truth, predictions):
    ground_truth = ground_truth.astype(np.float32)
    predictions = predictions.astype(np.float32)
    intersection = np.sum(predictions * ground_truth)
    union = np.sum(predictions) + np.sum(ground_truth)
    if intersection == 0.0 and union == 0.0:
        return 1.0
    return float((2.0 * intersection) / union)


def ftp_ratio_metric(ground_truth, predictions, unc_mask, brain_mask):
    ground_truth = ground_truth.astype(np.float32)
    predictions = predictions.astype(np.float32)
    unc_mask = unc_mask.astype(np.float32)
    brain_mask = brain_mask.astype(np.float32)
    TP = (predictions * ground_truth) * brain_mask
    tp_before = TP.sum()
    tp_after = (TP * unc_mask).sum()
    return float((tp_before - tp_after) / (tp_before + EPS))


def ftn_ratio_metric(ground_truth, predictions, unc_mask, brain_mask):
    ground_truth = ground_truth.astype(np.float32)
    predictions = predictions.astype(np.float32)
    unc_mask = unc_mask.astype(np.float32)
    brain_mask = brain_mask.astype(np.float32)
    TN = ((1 - predictions) * (1 - ground_truth)) * brain_mask
    tn_before = TN.sum()
    tn_after = (TN * unc_mask).sum()
    return float((tn_before - tn_after) / (tn_before + EPS))


def make(ground_truth, predictions, uncertainties, brain_mask, thresholds):
    """Evaluate one binary-entity volume across uncertainty thresholds.

    Returns (dsc, ftp, ftn) lists aligned with `thresholds` (descending).
    """
    dsc, ftp, ftn = [], [], []
    for th in thresholds:
        unc_mask = np.ones_like(uncertainties, dtype=np.float32)
        unc_mask[uncertainties > th] = 0.0
        gt_f = ground_truth.astype(np.float32) * unc_mask
        pred_f = predictions.astype(np.float32) * unc_mask
        dsc.append(dice_metric(gt_f, pred_f))
        ftp.append(ftp_ratio_metric(ground_truth, predictions, unc_mask, brain_mask))
        ftn.append(ftn_ratio_metric(ground_truth, predictions, unc_mask, brain_mask))
    return np.array(dsc), np.array(ftp), np.array(ftn)


def make_uncertainty_thresholds(num_points=41):
    # linspace guarantees the endpoints 100 and 0 are included (trapezoid AUC
    # over the full [0,100] interval), matching the paper's threshold values.
    pts = np.linspace(0.0, 100.0, num_points)
    return np.array(pts)[::-1]


def evaluate_volume(gt, pred, uncertainties, brain_mask, num_points=41):
    """Evaluate one volume for one binary entity.

    gt/un:            binary GT and prediction (bool or {0,1}) [H,W,D]
    uncertainties:    float uncertainty map normalized to [0,100] [H,W,D]
    brain_mask:       binary brain mask (1=brain) [H,W,D]
    Returns dict with curves and AUCs.
    """
    thresholds = make_uncertainty_thresholds(num_points)
    dsc, ftp, ftn = make(gt, pred, uncertainties, brain_mask, thresholds)
    auc1 = auc(thresholds, dsc) / 100.0
    auc2 = auc(thresholds, ftp) / 100.0
    auc3 = auc(thresholds, ftn) / 100.0
    score = (auc1 + (1 - auc2) + (1 - auc3)) / 3.0
    return {
        "thresholds": thresholds,
        "dsc_curve": dsc,
        "ftp_curve": ftp,
        "ftn_curve": ftn,
        "auc1_dsc": float(auc1),
        "auc2_ftp": float(auc2),
        "auc3_ftn": float(auc3),
        "score": float(score),                      # paper Eq.1 (normalized)
        "score_sum": float(auc1 + (1 - auc2) + (1 - auc3)),  # task formulation
        "dice_t100": float(dice_metric(gt, pred)),  # DSC at tau=100 == full DSC
    }


def brain_mask_from_image(img):
    """Derive a brain mask from a (skull-stripped) anatomical image, as in the
    official evaluation script (0-intensity background)."""
    bm = (img > 0).astype(np.uint8)
    return bm


def entropy_binary(p, eps=1e-8):
    """Predictive entropy (bits) of a binary probability map, in [0,1]."""
    p = np.clip(p, eps, 1 - eps)
    h = -(p * np.log2(p) + (1 - p) * np.log2(1 - p))
    return h


def normalize_unc_0_100(unc):
    cmin = float(np.min(unc))
    cmax = float(np.max(unc))
    if cmax - cmin < 1e-12:
        return np.zeros_like(unc)
    return 100.0 * (unc - cmin) / (cmax - cmin)