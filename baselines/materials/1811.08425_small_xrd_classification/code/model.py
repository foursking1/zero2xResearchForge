"""a-CNN model (paper Sec III) in PyTorch.

Architecture (all-convolutional):
  3 x Conv1D(32 filters, kernel/stride 8/5/3) + ReLU
  -> Global Average Pooling -> Dense(num_classes)
"""

import torch
import torch.nn as nn

import config


class ACNN(nn.Module):
    def __init__(self, n_features=config.NUM_CLASSES,
                 filters=config.CONV_FILTERS,
                 kernels=config.KERNELS, strides=config.STRIDES,
                 loss=config.LOSS):
        super().__init__()
        self.loss_name = loss
        layers = []
        in_ch = 1
        for k, s in zip(kernels, strides):
            layers.append(nn.Conv1d(in_ch, filters, kernel_size=k, stride=s,
                                    padding=k // 2))
            layers.append(nn.ReLU())
            in_ch = filters
        self.features = nn.Sequential(*layers)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.head = nn.Linear(filters, n_features)

    def forward(self, x, training=True):
        # x: (B, L) -> (B, 1, L)
        h = self.features(x.unsqueeze(1))
        h = self.pool(h).squeeze(-1)
        return self.head(h)

    def loss(self, logits, target):
        if self.loss_name == "bce":
            target_onehot = nn.functional.one_hot(
                target, num_classes=logits.shape[-1]).float()
            return nn.functional.binary_cross_entropy_with_logits(
                logits, target_onehot)
        return nn.functional.cross_entropy(logits, target)


def build_model():
    return ACNN()
