"""Small 2D U-Net for multi-entity brain tumour segmentation (FLAIR input).

Output has 3 channels (per voxel, per binary tumor entity): [ET, TC, WT].
Supports optional dropout (for MC-Dropout uncertainty) --- kept as a
configuration toggle so the same architecture can be trained deterministically
(dropout applied only at inference) or with dropout active during training.
"""
import numpy as np
import torch
import torch.nn as nn


def conv_block(in_ch, out_ch, p_drop=0.0):
    layers = [
        nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
    ]
    if p_drop > 0.0 and p_drop is not None:
        layers.append(nn.Dropout2d(p_drop))
    return nn.Sequential(*layers)


class UNet2D(nn.Module):

    def __init__(self, in_ch=1, out_ch=3, base_ch=16, levels=4, p_drop=0.3,
                 mc_dropout=False):
        super().__init__()
        self.p_drop = p_drop
        self.mc_dropout = mc_dropout  # keep dropout active during inference
        self.levels = levels
        self.base_ch = base_ch

        chs = [base_ch * (2 ** i) for i in range(levels + 1)]  # e.g. 16,32,64,128,256

        self.encs = nn.ModuleList()
        self.pools = nn.ModuleList()
        self.decs = nn.ModuleList()
        self.ups = nn.ModuleList()

        self.encs.append(conv_block(in_ch, chs[0], p_drop if mc_dropout else 0.0))
        for i in range(1, levels + 1):
            self.pools.append(nn.MaxPool2d(2))
            self.encs.append(conv_block(chs[i - 1], chs[i], p_drop if mc_dropout else 0.0))

        # decoder
        for i in range(levels):
            self.ups.append(nn.ConvTranspose2d(chs[levels - i], chs[levels - i - 1], 2, stride=2))
            self.decs.append(conv_block(chs[levels - i], chs[levels - i - 1],
                                        p_drop if mc_dropout else 0.0))

        self.head = nn.Conv2d(chs[0], out_ch, 1)

    def forward(self, x):
        skips = []
        h = x
        for i, enc in enumerate(self.encs):
            h = enc(h)
            if i < self.levels:
                skips.append(h)
                h = self.pools[i](h)
        for i in range(self.levels):
            h = self.ups[i](h)
            h = torch.cat([h, skips[self.levels - 1 - i]], dim=1)
            h = self.decs[i](h)
        return self.head(h)


def count_params(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    m = UNet2D()
    x = torch.randn(2, 1, 160, 160)
    print(m(x).shape, "params", count_params(m))