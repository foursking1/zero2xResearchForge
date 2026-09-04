"""Evaluation helpers: OA / AA / Kappa / per-class accuracy + result serialization."""
import json
import os
import numpy as np


def kappa_from_cm(cm):
    n = cm.sum()
    p0 = np.trace(cm) / n
    pe = (cm.sum(axis=0) * cm.sum(axis=1)).sum() / (n * n)
    return (p0 - pe) / (1 - pe + 1e-12)


def compute_metrics(y_true, y_pred, n_classes=16):
    """y_true/y_pred: integer labels in [1..n_classes]. Returns dict."""
    yt = np.asarray(y_true).astype(int)
    yp = np.asarray(y_pred).astype(int)
    n = len(yt)

    cm = np.zeros((n_classes, n_classes), dtype=np.int64)
    for t, p in zip(yt - 1, yp - 1):
        cm[t, p] += 1

    per_class = {}
    for c in range(1, n_classes + 1):
        tp = cm[c - 1, c - 1]
        total = cm[c - 1].sum()
        per_class[str(c)] = {
            'accuracy': float(tp / total) if total else None,
            'n_test': int(total),
        }
    oa = float(np.trace(cm) / n)
    per_class_recall = np.array([per_class[str(c)]['accuracy']
                                 for c in range(1, n_classes + 1)
                                 if per_class[str(c)]['accuracy'] is not None])
    aa = float(per_class_recall.mean())
    k = float(kappa_from_cm(cm))
    return {
        'n_test': n, 'correct': int(np.trace(cm)),
        'overall_accuracy': oa, 'average_accuracy': aa, 'kappa': k,
        'confusion_matrix': cm.tolist(), 'per_class': per_class,
    }


def save_metrics(method_name, metrics, extra=None, out_dir='../results'):
    os.makedirs(out_dir, exist_ok=True)
    tag = method_name.lower().replace(' ', '_')
    path = os.path.join(out_dir, f'metrics_{tag}.json')
    payload = {'method': method_name, **metrics}
    if extra:
        payload.update(extra)
    with open(path, 'w') as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    return path


def build_evidence_table(results):
    """results: list of dicts (method seeds or per ratio). Returns CSV text."""
    rows = []
    for r in results:
        pc = r.get('per_class', {})
        for c in sorted(pc, key=lambda x: int(x)):
            rows.append({
                'method': r.get('method', ''), 'seed': r.get('seed', ''),
                'train_ratio': r.get('train_ratio', ''), 'class': c,
                'n_test': pc[c]['n_test'], 'accuracy': pc[c]['accuracy'],
            })
    return rows