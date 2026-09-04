"""Model definitions (PyTorch) for MIMO time-series forecasting on M3 monthly."""
import torch
import torch.nn as nn


class MLP(nn.Module):
    def __init__(self, input_size, hidden_sizes, output_size):
        super().__init__()
        layers = []
        in_sz = input_size
        for h in hidden_sizes:
            layers.append(nn.Linear(in_sz, h))
            layers.append(nn.ReLU())
            in_sz = h
        layers.append(nn.Linear(in_sz, output_size))
        self.layers = nn.Sequential(*layers)

    def forward(self, x):
        return self.layers(x)


class RNN(nn.Module):
    """Gated recurrent forecaster: input (B, ph) -> GRU/LSTM over steps -> 18 out."""

    def __init__(self, cell, input_size, hidden_size, n_layers, output_size, dropout=0.0):
        super().__init__()
        self.cell = cell
        self.hidden_size = hidden_size
        self.n_layers = n_layers
        rnn_cls = nn.GRU if cell == "gru" else nn.LSTM
        self.rnn = rnn_cls(
            input_size=1,
            hidden_size=hidden_size,
            num_layers=n_layers,
            batch_first=True,
            dropout=dropout if n_layers > 1 else 0.0,
        )
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = x.unsqueeze(-1)  # (B, ph, 1)
        out, _ = self.rnn(x)  # (B, ph, H)
        return self.fc(out[:, -1, :])


class CNN(nn.Module):
    """1D CNN encoder with pooling, flattened into a 18-dim forecast head."""

    def __init__(self, input_size, channels, n_layers, kernel, output_size, pad=1):
        super().__init__()
        convs = []
        in_ch = 1
        for _ in range(n_layers):
            convs.append(nn.Conv1d(in_ch, channels, kernel, padding=pad))
            convs.append(nn.ReLU())
            convs.append(nn.AvgPool1d(2))
            in_ch = channels
        self.convs = nn.Sequential(*convs)
        self.flatten = nn.Flatten()
        # length after convs
        L = input_size
        for _ in range(n_layers):
            L = ((L + 2 * pad - kernel) // 1 + 1)
            L = L // 2
        self.fc = nn.Linear(channels * L, output_size)

    def forward(self, x):
        x = x.unsqueeze(1)  # (B,1,ph)
        h = self.convs(x)
        h = self.flatten(h)
        return self.fc(h)


class TCNBlock(nn.Module):
    def __init__(self, channels, kernel, dilation, dropout=0.0):
        super().__init__()
        self.pad = (kernel - 1) * dilation
        self.conv1 = nn.Conv1d(channels, channels, kernel, padding=self.pad, dilation=dilation)
        self.conv2 = nn.Conv1d(channels, channels, kernel, padding=self.pad, dilation=dilation)
        self.relu1 = nn.ReLU()
        self.relu2 = nn.ReLU()
        self.drop1 = nn.Dropout(dropout)
        self.drop2 = nn.Dropout(dropout)
        self.down = None
        if channels != channels:
            self.down = nn.Conv1d(channels, channels, 1)

    def forward(self, x):
        res = x
        out = self.drop1(self.relu1(self.conv1(x)))
        out = self.drop2(self.relu2(self.conv2(out)))
        if self.down is not None:
            res = self.down(res)
        if out.size(2) != res.size(2):
            out = out[:, :, : res.size(2)]
        return self.relu1(out + res)


class TCN(nn.Module):
    """Dilated causal conv network (Bai et al.) used as an encoder for MIMO."""

    def __init__(self, input_size, channels, n_blocks, kernel, output_size, dropout=0.0):
        super().__init__()
        self.head = nn.Conv1d(1, channels, 1)
        blocks = []
        dil = 1
        for _ in range(n_blocks):
            blocks.append(TCNBlock(channels, kernel, dil, dropout))
            dil *= 2
        self.blocks = nn.Sequential(*blocks)
        self.fc = nn.Linear(channels, output_size)

    def forward(self, x):
        x = x.unsqueeze(1)  # (B,1,ph)
        h = self.head(x)
        h = self.blocks(h)  # (B,C,ph)
        return self.fc(h[:, :, -1])


def build_model(kind, config):
    ph = config["past_history"]
    out = config["horizon"]
    if kind == "mlp":
        return MLP(ph, config["hidden_sizes"], out)
    if kind in ("gru", "lstm"):
        return RNN(
            kind,
            1,
            config["hidden"],
            config.get("n_layers", 1),
            out,
            dropout=config.get("dropout", 0.0),
        )
    if kind == "cnn":
        return CNN(ph, config["channels"], config["n_layers"], config.get("kernel", 3), out)
    if kind == "tcn":
        return TCN(ph, config["channels"], config["n_blocks"], config.get("kernel", 3), out, config.get("dropout", 0.0))
    raise ValueError(kind)