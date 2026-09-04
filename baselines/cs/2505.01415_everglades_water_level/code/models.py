"""PyTorch implementations of the task-specific forecasting models.

Categories follow the paper's Table 1 taxonomy:
  * Linear class : NLinear, DLinear   (arXiv:2205.13504, DLinear)
  * MLP class    : NBEATS            (arXiv:1905.10437)
All models map a (CONTEXT_LEN x 37) input window to a (HORIZON x 5) forecast
(mean squared error is minimized; point forecasts are the direct head outputs).
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
from common import CONTEXT_LEN, HORIZON, TARGETS

N_FEATURES = 37
N_OUTPUTS = len(TARGETS)
# column positions of the 5 target stations inside the 37-variable input matrix
# (fixed column order of final_concatenated_data.csv)
TARGET_IDX = [0] * len(TARGETS)

def init_target_idx(feat_cols) -> None:
    TARGET_IDX[:] = [feat_cols.index(t) for t in TARGETS]


# --------------------------------------------------------------------------
# Linear class
# --------------------------------------------------------------------------
class NLinear(nn.Module):
    """NLinear: linear model with last-value detrending (subtract last observation,
    apply a linear map, re-add the last value)."""

    def __init__(self, input_len: int = CONTEXT_LEN, feat: int = N_FEATURES,
                 horizon: int = HORIZON, out: int = N_OUTPUTS):
        super().__init__()
        self.linear = nn.Linear(input_len * feat, horizon * out, bias=True)
        self.input_len = input_len

    def forward(self, x: torch.Tensor) -> torch.Tensor:      # (B, C, F)
        last = x[:, -1, TARGET_IDX]                            # (B, out) last target value
        z = (x - x[:, -1:, :])                                 # detrend by last obs
        y = self.linear(z.reshape(x.size(0), -1))              # (B, H*out)
        y = y.reshape(x.size(0), -1, N_OUTPUTS).transpose(1, 2)  # (B, out, H)
        y = y + last.unsqueeze(-1)                             # re-add last target value
        return y.transpose(1, 2)                               # (B, H, out)


class DLinear(nn.Module):
    """DLinear: decomposition (moving-average seasonal + residual trend), two
    linear heads per component, summed."""

    def __init__(self, input_len: int = CONTEXT_LEN, feat: int = N_FEATURES,
                 horizon: int = HORIZON, out: int = N_OUTPUTS, kernel: int = 25):
        super().__init__()
        self.kernel = kernel
        pad = (kernel - 1) // 2
        self.avg = nn.AvgPool1d(kernel_size=kernel, stride=1, padding=pad)
        self.trend = nn.Linear(input_len * feat, horizon * out, bias=True)
        self.season = nn.Linear(input_len * feat, horizon * out, bias=True)
        self.input_len = input_len

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # (B, C, F) with F features
        x = x.transpose(1, 2)                             # (B, F, C)
        # moving average over the time dimension
        season = self.avg(x)                              # (B, F, C)
        trend = x - season                                # residual (trend) (B, F, C)
        y_trend = self.trend(trend.reshape(x.size(0), -1))
        y_season = self.season(season.reshape(x.size(0), -1))
        y = (y_trend + y_season).reshape(x.size(0), N_OUTPUTS, -1)  # (B, out, H)
        return y.transpose(1, 2)                          # (B, H, out)


# --------------------------------------------------------------------------
# MLP class
# --------------------------------------------------------------------------
class GBlock(nn.Module):
    """Generic block of nested MLPs with residual connections (NBEATS backbone)."""

    def __init__(self, units: list[int], in_dim: int, out_dim: int, activ: str = "relu"):
        super().__init__()
        net = []
        prev = in_dim
        for i, u in enumerate(units + [out_dim]):
            net.append(nn.Linear(prev, u))
            if i < len(units):  # activation only on hidden layers
                net.append(self._act(activ))
            prev = u
        self.net = nn.Sequential(*net)

    @staticmethod
    def _act(name: str) -> nn.Module:
        return {"relu": nn.ReLU(), "gelu": nn.GELU(), "tanh": nn.Tanh()}[name]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class NBEATS(nn.Module):
    """NBEATS with 2 stacks / 2 blocks per stack, shared (interpretable-free)
    setting: each block outputs (backcast, forecast); forecasts summed."""

    def __init__(self, input_len: int = CONTEXT_LEN, feat: int = N_FEATURES,
                 horizon: int = HORIZON, out: int = N_OUTPUTS,
                 n_blocks: tuple[int, int] = (2, 2),
                 mlp_units: tuple[list[int], list[int]] = ([256, 256], [256, 256]),
                 activ: str = "relu"):
        super().__init__()
        self.blocks = nn.ModuleList()
        in_dim = input_len * feat
        f_dim = horizon * out
        for n in n_blocks:
            for _ in range(n):
                self.blocks.append(
                    nn.ModuleList([
                        GBlock(mlp_units[0], in_dim, in_dim, activ),   # theta backcast
                        GBlock(mlp_units[1], in_dim, f_dim, activ),    # theta forecast
                    ])
                )
        self.in_dim = in_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # (B, C, F)
        xv = x.reshape(x.size(0), -1)
        fc: torch.Tensor = torch.zeros(x.size(0), HORIZON * N_OUTPUTS, device=x.device)
        for (phi_b, phi_f) in self.blocks:
            th_b = phi_b(xv)
            th_f = phi_f(xv)
            xv = xv - th_b                                  # residual backcast
            fc = fc + th_f
        return fc.reshape(x.size(0), N_OUTPUTS, HORIZON).transpose(1, 2)  # (B,H,out)


# --------------------------------------------------------------------------
# Shared helper: rolling forecast for a fixed model
# --------------------------------------------------------------------------
class ModelPredictor:
    """Holds a trained model + scaler; computes daily-rolling 28-step point forecasts.

    Input windows use only observations strictly before each origin.
    """

    def __init__(self, model: nn.Module, scaler, device: torch.device):
        self.model = model.eval()
        self.scaler = scaler
        self.device = device
        self.n_features = None

    def predict_window(self, ctx_scaled: np.ndarray) -> np.ndarray:
        """ctx_scaled: (CONTEXT_LEN, n_features) scaled values -> (HORIZON, out) scaled."""
        xt = torch.from_numpy(ctx_scaled.astype(np.float32)).unsqueeze(0).to(self.device)
        with torch.no_grad():
            pred = self.model(xt)[0].cpu().numpy()  # (H, out)
        return pred