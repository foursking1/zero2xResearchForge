"""2-D U-Net used for the source-pool pretraining / target fine-tuning.

Pure PyTorch, no external segmentation framework.  Capacity is controlled by
`base_channels`; depth fixed (3 down/up blocks + bottleneck) so that all pool
members share the same architecture shape and only differ in width (and seed).
Returns both the logits (for training/evaluation) and the bottleneck feature map
(used by the transferability estimators).
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class UNet(nn.Module):
    def __init__(self, in_ch=1, out_ch=1, base=16, depth=3):
        super().__init__()
        self.in_ch = in_ch
        self.out_ch = out_ch
        self.base = base
        self.depth = depth
        self.enc = nn.ModuleList()
        self.downs = nn.ModuleList()
        ic = in_ch
        chans = []
        for d in range(depth):
            oc = base * (2 ** d)
            chans.append(oc)
            self.enc.append(_ConvBlock(ic, oc))
            self.downs.append(nn.MaxPool2d(2))
            ic = oc
        self.bot = _ConvBlock(ic, ic)
        self.up = nn.ModuleList()
        self.dec = nn.ModuleList()
        for d in range(depth - 1, -1, -1):
            oc = chans[d]
            self.up.append(nn.ConvTranspose2d(ic, oc, kernel_size=2, stride=2))
            self.dec.append(_ConvBlock(2 * oc, oc if d > 0 else base))
            ic = oc if d > 0 else base
        self.head = nn.Conv2d(base, out_ch, 1)

    def forward(self, x, want_dec=False):
        skips = []
        h = x
        for e, d in zip(self.enc, self.downs):
            h = e(h)
            skips.append(h)
            h = d(h)
        h = self.bot(h)
        feats_bn = h  # bottleneck feature map (used by CC-FV / LogME / GBC)
        for u, dec, s in zip(self.up, self.dec, reversed(skips)):
            h = u(h)
            h = torch.cat([h, s], dim=1)
            h = dec(h)
        feats_dec = h  # decoder feature map at full resolution (pre-head)
        logits = self.head(h)
        if want_dec:
            return logits, feats_bn, feats_dec
        return logits, feats_bn


class _ConvBlock(nn.Module):
    def __init__(self, cin, cout):
        super().__init__()
        self.c1 = nn.Conv2d(cin, cout, 3, padding=1)
        self.b1 = nn.BatchNorm2d(cout)
        self.c2 = nn.Conv2d(cout, cout, 3, padding=1)
        self.b2 = nn.BatchNorm2d(cout)

    def forward(self, x):
        x = F.relu(self.b1(self.c1(x)))
        x = F.relu(self.b2(self.c2(x)))
        return x


def dice_score(pred_logits, target, eps=1e-6):
    """Per-sample Dice (softmax-free, single-channel logits => binary mask)."""
    p = torch.sigmoid(pred_logits)
    p = (p > 0.5).float() if not pred_logits.requires_grad else p
    target = target.float()
    if p.dim() == 4:
        inter = (p * target).sum(dim=(2, 3))
        union = p.sum(dim=(2, 3)) + target.sum(dim=(2, 3))
        return (2 * inter + eps) / (union + eps)
    inter = (p * target).sum()
    union = p.sum() + target.sum()
    return (2 * inter + eps) / (union + eps)


def dice_loss(pred_logits, target, smooth=1.0):
    p = torch.sigmoid(pred_logits)
    t = target.float()
    inter = (p * t).sum(dim=(2, 3)) + smooth
    union = p.sum(dim=(2, 3)) + t.sum(dim=(2, 3)) + smooth
    return (1.0 - 2.0 * inter / union).mean()