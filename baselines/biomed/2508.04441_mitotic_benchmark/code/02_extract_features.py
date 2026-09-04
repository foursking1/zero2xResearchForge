#!/usr/bin/env python3
"""Step 2 - Extract frozen-patch features with ImageNet-pretrained encoders.

Uses torchvision backbones whose weights are cached locally (offline-safe):
  - ResNet18 (512-d penultimate features after global-avg-pool)
  - ViT-B/16 (768-d CLS-token features)

For every 256x256 crop we extract features at 4 planar rotations (0/90/180/270)
so a later training stage can use rotation augmentation in the small-data
regime. Output: results/features.npz with one (N,4,D) float32 array per model.
"""
from __future__ import annotations
import argparse
import os
import os.path as osp
import sys

import numpy as np
import torch


def _trunc_cnn(net):
    return torch.nn.Sequential(*list(net.children())[:-2])


class _ViTBackend(torch.nn.Module):
    """conv_proj + class token + encoder(+final LN) mirroring VisionTransformer
    feature path; returns the 197-token sequence so the CLS token is index 0."""

    def __init__(self, net):
        super().__init__()
        self.conv_proj = net.conv_proj
        self.class_token = net.class_token
        self.encoder = net.encoder

    def forward(self, x):
        x = self.conv_proj(x)                 # (B, C, H', W')
        x = x.flatten(2).transpose(1, 2)      # (B, N, C)
        n = x.shape[0]
        tok = self.class_token.expand(n, -1, -1)
        return self.encoder(torch.cat([tok, x], dim=1))


def _trunc_vit(net):
    return _ViTBackend(net)


def build_backbone(arch: str, device: torch.device):
    from torchvision.models import resnet18, ResNet18_Weights, vit_b_16, ViT_B_16_Weights
    if arch == "resnet18":
        base = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1).to(device).eval()
        return _trunc_cnn(base), 512
    if arch == "vit_b_16":
        base = vit_b_16(weights=ViT_B_16_Weights.IMAGENET1K_V1).to(device).eval()
        return _trunc_vit(base), 768
    raise NotImplementedError(arch)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--results", default=None)
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"])
    ap.add_argument("--batch-size", type=int, default=32)
    args = ap.parse_args()

    res_dir = osp.abspath(args.results or osp.join(osp.dirname(osp.abspath(__file__)), "..", "results"))
    device = torch.device("auto" if args.device == "auto" else args.device)
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("device:", device)

    npz = np.load(osp.join(res_dir, "patches.npz"))
    X = npz["X"]
    n, h, w, c = X.shape
    print("patches:", X.shape)

    mean = torch.tensor([0.485, 0.456, 0.406], device=device).view(1, 3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225], device=device).view(1, 3, 1, 1)

    MODELS = [
        ("ResNet18-ImageNet", "resnet18"),
        ("ViT-B/16-ImageNet", "vit_b_16"),
    ]

    all_feats = {}
    tX = torch.from_numpy(X).permute(0, 3, 1, 2).float()
    if tX.shape[1] > 3:  # RGBA PNGs -> RGB
        tX = tX[:, :3]
    tX = tX.to(device)
    rots = []
    for k in range(4):
        rots.append(torch.rot90(tX, k, dims=(2, 3)))
    with torch.no_grad():
        for key, arch in MODELS:
            backbone, dim = build_backbone(arch, device)
            feats = np.zeros((n, 4, dim), dtype=np.float32)
            for r, t in enumerate(rots):
                all_ = []
                for i in range(0, n, args.batch_size):
                    batch = t[i:i + args.batch_size].contiguous()
                    batch = (batch / 255.0 - mean) / std
                    out = backbone(batch)
                    v = out.mean(dim=(-1, -2)).cpu().numpy() if out.dim() == 4 else out[:, 0].cpu().numpy()
                    all_.append(v)
                feats[:, r] = np.concatenate(all_, axis=0)
            all_feats[key] = feats
            print(f"{key}: {feats.shape}")

    np.savez(
        osp.join(res_dir, "features.npz"),
        ResNet18_ImageNet=all_feats["ResNet18-ImageNet"].astype(np.float32),
        ViT_B16_ImageNet=all_feats["ViT-B/16-ImageNet"].astype(np.float32),
        model_names=np.asarray(list(all_feats.keys()), dtype=object),
        patch_size=int(h),
    )
    print("saved ->", osp.join(res_dir, "features.npz"))


if __name__ == "__main__":
    main()