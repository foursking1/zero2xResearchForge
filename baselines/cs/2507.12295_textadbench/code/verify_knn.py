#!/usr/bin/env python3
"""Fast judge-facing spot-check: reproduce KNN AUROC from the frozen .npy.

Equivalent to SCORE_RUBRIC's reference recompute
    KNN(n_neighbors=3).fit(train) -> decision_function(test)
    roc_auc_score(test_label, score)   # pyod 3.6.4 => 94.85%

Logs env versions and (optionally) checks the four SHA-256 checksums.
Run it the same way the full pipeline is run:
    cd agent_solution && python code/verify_knn.py
"""
import hashlib
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

EXPECTED = {
    "train/mntp_eos_token_embeddings.npy": "7A746410CD7A35C3029A9D0B753751DD1920A0385364CB698E2F59CCF888C19E",
    "train/mntp_embedding_labels.npy": "4946B0ABDC4F88B200F2D5BFC7B57D9500CDB79E644DB9F7B30852A9EE993502",
    "test/mntp_eos_token_embeddings.npy": "854FBA8CBCF3DBBDD08898FD5DACEAB1393D50A596286EC9F3973FEF9AED7282",
    "test/mntp_embedding_labels.npy": "BE40D255B5046F738F7F7F12F74FE81884B7CB681B8C6A314062FDA831BD8C55",
}

CANDIDATES = [
    os.environ.get("TEXTAD_DATA_DIR", ""),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data",
                 "embeddings", "sms_spam", "Llama3-8b"),
    "F:/dataset/cs/2507.12295_textadbench/embeddings/sms_spam/Llama3-8b",
    "/mnt/f/dataset/cs/2507.12295_textadbench/embeddings/sms_spam/Llama3-8b",
]


def hexu(s):
    return s.upper().replace("-", "")


def main():
    import pyod
    from pyod.models.knn import KNN
    from sklearn.metrics import roc_auc_score

    print(f"pyod={pyod.__version__}")

    data_dir = next((c for c in CANDIDATES if c and os.path.isfile(
        os.path.join(c, "test", "mntp_embedding_labels.npy"))), None)
    if data_dir is None:
        raise SystemExit("frozen data not found")
    print(f"data dir : {data_dir}")

    if "--checksums" in sys.argv:
        ok = True
        for rel, want in EXPECTED.items():
            got = hexu(hashlib.sha256(open(os.path.join(data_dir, rel), "rb").read()).hexdigest())
            ok &= got == want
            print(f"  {rel:42s} {'MATCH' if got == want else 'MISMATCH'}")
        print("checksums:", "all OK" if ok else "FAILED")

    Xtr = np.load(os.path.join(data_dir, "train", "mntp_eos_token_embeddings.npy"), allow_pickle=True)
    Xte = np.load(os.path.join(data_dir, "test", "mntp_eos_token_embeddings.npy"), allow_pickle=True)
    yte = np.asarray(np.load(os.path.join(data_dir, "test", "mntp_embedding_labels.npy"), allow_pickle=True)).ravel()
    print(f"train {Xtr.shape} (all-normal) | test {Xte.shape} | #anomaly={(yte==1).sum()}")

    knn = KNN(n_neighbors=3, contamination=0.1)
    knn.fit(Xtr)
    score = knn.decision_function(Xte)
    auroc = roc_auc_score(yte, score) * 100.0
    print(f"KNN(n_neighbors=3) test AUROC = {auroc:.2f}%   (reference 94.85%)")
    assert abs(auroc - 94.85) < 0.2, "deviation from reference exceeds 0.2pp"


if __name__ == "__main__":
    main()