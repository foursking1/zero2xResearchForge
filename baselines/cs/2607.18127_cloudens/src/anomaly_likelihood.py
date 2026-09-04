"""Anomaly likelihood score (Numenta-style) used by the LF scoring strategy.

Matches src/anomaly_likelihood.py of the official ClouDens reproduction
package so the reported LF numbers are directly comparable.
"""
import numpy as np
from scipy.stats import norm


def compute_anomaly_likelihood(historical_recon_error, long_window_length, short_window_length):
    """Likelihood in (0, 1); 0.5 when the history is shorter than long window."""
    if len(historical_recon_error) <= long_window_length:
        return 0.5
    wide = historical_recon_error[-long_window_length:]
    narrow = historical_recon_error[-short_window_length:]
    mean_wide = np.mean(wide)
    std_wide = np.std(wide)
    epsilon = 1e-10
    z = (np.mean(narrow) - mean_wide) / (std_wide + epsilon)
    return 0.5 + 0.5 * (1.0 - norm.sf(z))