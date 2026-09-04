"""Shared model definition for the EuroSAT compact CNN."""
import torch.nn as nn

CLASS_NAMES = [
    "AnnualCrop", "Forest", "HerbaceousVegetation", "Highway", "IndustrialBuildings",
    "Pasture", "PermanentCrop", "ResidentialBuildings", "River", "SeaLake",
]


def _blk(i, o, pool=True):
    layers = [nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(inplace=True)]
    if pool:
        layers.append(nn.MaxPool2d(2))
    return nn.Sequential(*layers)


def make_model(n_classes=10):
    return nn.Sequential(
        _blk(3, 64, True),     # 32x32
        _blk(64, 128, True),   # 16x16
        _blk(128, 256, True),  # 8x8
        _blk(256, 512, True),  # 4x4
        _blk(512, 512, False),
        nn.AdaptiveAvgPool2d(1),
        nn.Flatten(),
        nn.Dropout(0.3),
        nn.Linear(512, n_classes),
    )


def count_params(m):
    return sum(p.numel() for p in m.parameters() if p.requires_grad)