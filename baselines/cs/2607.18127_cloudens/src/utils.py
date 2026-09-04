"""Shared helpers: seed control, NAB result assembly."""
import json
import random

import numpy as np
import pandas as pd

import torch

from nab_scoring import calculate_nab_score


def set_random_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def detection_dict_to_columns(counters):
    """Flatten detection_counters into EvidenceTable columns."""
    return {"issue": counters["issue"]["count"], "issue_ids": counters["issue"]["ids"],
            "im": counters["im"]["count"], "im_ids": counters["im"]["ids"],
            "testlog": counters["testlog"]["count"], "testlog_ids": counters["testlog"]["ids"]}


def get_full_nab_result(alarms, true_labels, test_index, anomaly_windows_test):
    """Compute NAB (both profiles) + confusion + detection counters."""
    df = pd.DataFrame({"true_anomaly": true_labels, "predicted_anomaly": alarms,
                       "likelihood": alarms.astype(float)}, index=test_index)
    df.index = pd.to_datetime(df.index)
    out = {}
    for profile in ("standard", "reward_fn"):
        r = calculate_nab_score(df, anomaly_windows_test, profile)
        out[profile] = r
    return out


def fmt_id_list(ids):
    return json.dumps(sorted(int(i) for i in ids)) if isinstance(ids, (list, tuple, np.ndarray)) else str(ids)