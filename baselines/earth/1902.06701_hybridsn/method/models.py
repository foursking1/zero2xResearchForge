"""Model definitions.

- HybridSN (3D-2D hybrid CNN): the paper's architecture, implemented in PyTorch.
  Reference: Roy et al., "HybridSN: Exploring 3-D-2-D CNN Feature Hierarchy for
  Hyperspectral Image Classification", IEEE GRSL 17(2), 2020 (arXiv:1902.06701).

  The 3D convolutions slide over BOTH spatial (25x25) and spectral (30 PCA bands)
  axes, jointly learning spatial-spectral features; then the feature map is
  unfolded to 2D and refined by a 2D spatial convolution, and classified by dense
  layers. Channel widths follow the task card (3D 32 -> 64 -> 128, 2D 64, FC 256/128):

    3DConv(8,32,3,3,3)  -> Conv3d(1, 32, k3) pad same   (spectral axis = depth)
    3DConv(32,64,3,3,3) -> Conv3d(32, 64, k3) pad same
    3DConv(64,128,3,3,3)-> Conv3d(64, 128, k3) pad valid
    2DConv(128,64,3,3)  -> Conv2d(128*28, 64, k3) pad same
    FC                  -> Dense 256 -> Dense 128 -> Dense n_classes

  Input window: 25x25.

- CNN2D: 2D-only CNN baseline on the same 25x25 patches (spectral bands as input
  channels, no joint 3D spectral-spatial convolution).
"""
import torch
import torch.nn as nn


def _init(m):
    """Keras-default 'glorot_uniform' initialization, matching the paper's Keras
    implementation (they did not override the default initializer)."""
    if isinstance(m, (nn.Conv2d, nn.Conv3d, nn.Linear)):
        nn.init.xavier_uniform_(m.weight)
        if m.bias is not None:
            nn.init.constant_(m.bias, 0)


class HybridSN(nn.Module):
    """3D-2D hybrid CNN hyperspectral classifier (HybridSN architecture)."""

    def __init__(self, n_bands=30, n_classes=16, n_filters=(32, 64, 128),
                 n_filters2d=64, fc_units=(256, 128), dropout=0.5):
        super().__init__()
        self.n_bands = n_bands
        self.conv1 = nn.Conv3d(1, n_filters[0], (3, 3, 3), padding=(1, 1, 1))
        self.conv2 = nn.Conv3d(n_filters[0], n_filters[1], (3, 3, 3), padding=(1, 1, 1))
        self.conv3 = nn.Conv3d(n_filters[1], n_filters[2], (3, 3, 3))  # valid: 30->28, 25->23

        n_spectral = n_bands - 2           # 28 channels after 3 3D-convs on depth axis
        self.spatial = 25 - 2              # 23
        self.conv2d = nn.Conv2d(n_filters[2] * n_spectral, n_filters2d, (3, 3),
                                padding=(1, 1))

        flat = n_filters2d * self.spatial * self.spatial
        self.fc1 = nn.Linear(flat, fc_units[0])
        self.fc2 = nn.Linear(fc_units[0], fc_units[1])
        self.head = nn.Linear(fc_units[1], n_classes)
        self.drop = nn.Dropout(dropout)
        self.relu = nn.ReLU(inplace=True)
        self.apply(_init)

    def forward(self, x):
        # x: (B, n_bands, 25, 25)
        x = x.unsqueeze(1)                       # (B, 1, n_bands, 25, 25)
        x = self.relu(self.conv1(x))             # (B,32,30,25,25)
        x = self.drop(x)
        x = self.relu(self.conv2(x))             # (B,64,30,25,25)
        x = self.drop(x)
        x = self.relu(self.conv3(x))             # (B,128,28,23,23)
        x = self.drop(x)
        B, C, D, H, W = x.shape
        x = x.permute(0, 2, 1, 3, 4).contiguous().view(B, C * D, H, W)  # (B,128*28,23,23)
        x = self.relu(self.conv2d(x))                                    # (B,64,23,23)
        x = self.drop(x)
        x = torch.flatten(x, 1)                  # (B, 64*23*23)
        x = self.relu(self.fc1(x))
        x = self.drop(x)
        x = self.relu(self.fc2(x))
        return self.head(x)


class CNN2D(nn.Module):
    """2D-only CNN baseline on the same 25x25 patches."""

    def __init__(self, n_bands=30, n_classes=16, dropout=0.5):
        super().__init__()
        self.conv1 = nn.Conv2d(n_bands, 32, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool = nn.MaxPool2d(2)               # 25x25 -> 12x12
        self.fc1 = nn.Linear(64 * 12 * 12, 256)
        self.fc2 = nn.Linear(256, 128)
        self.head = nn.Linear(128, n_classes)
        self.drop = nn.Dropout(dropout)
        self.relu = nn.ReLU(inplace=True)
        self.apply(_init)

    def forward(self, x):
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.drop(x)
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.drop(x)
        x = self.pool(x)
        x = torch.flatten(x, 1)
        x = self.relu(self.fc1(x))
        x = self.drop(x)
        x = self.relu(self.fc2(x))
        return self.head(x)


def count_params(model):
    return sum(p.numel() for p in model.parameters())