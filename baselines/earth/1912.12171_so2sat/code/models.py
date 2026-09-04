"""Model definitions: ResNeXt-style CNN with CBAM attention (paper: ResNeXt-CBAM)."""
import torch
import torch.nn as nn


class CBAM(nn.Module):
    """CBAM attention block (Woo et al., 2018): channel + spatial attention."""

    def __init__(self, channels, reduction=16):
        super().__init__()
        self.ch_avg = nn.Sequential(
            nn.Conv2d(channels, channels // reduction, 1, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels // reduction, channels, 1, bias=False),
        )
        self.ch_max = nn.Sequential(
            nn.Conv2d(channels, channels // reduction, 1, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels // reduction, channels, 1, bias=False),
        )
        self.sp = nn.Sequential(
            nn.Conv2d(2, 1, kernel_size=7, padding=3, bias=False),
            nn.Sigmoid(),
        )
        self.sig = nn.Sigmoid()

    def forward(self, x):
        # channel attention
        avg = torch.mean(x, dim=(2, 3), keepdim=True)
        mx = torch.amax(x, dim=(2, 3), keepdim=True)
        ca = self.sig(self.ch_avg(avg) + self.ch_max(mx))
        x = x * ca
        # spatial attention
        avg_s = torch.mean(x, dim=1, keepdim=True)
        mx_s = torch.amax(x, dim=1, keepdim=True)
        sa = self.sp(torch.cat([avg_s, mx_s], dim=1))
        x = x * sa
        return x


class ResNeXtBlock(nn.Module):
    def __init__(self, in_c, out_c, cardinality=8, stride=1):
        super().__init__()
        b = in_c // cardinality
        self.conv1 = nn.Conv2d(in_c, out_c, 1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_c)
        self.conv2 = nn.Conv2d(out_c, out_c, 3, stride, 1, groups=cardinality, bias=False)
        self.bn2 = nn.BatchNorm2d(out_c)
        self.conv3 = nn.Conv2d(out_c, out_c, 1, bias=False)
        self.bn3 = nn.BatchNorm2d(out_c)
        self.short = nn.Sequential()
        if stride != 1 or in_c != out_c:
            self.short = nn.Sequential(
                nn.Conv2d(in_c, out_c, 1, stride, bias=False),
                nn.BatchNorm2d(out_c),
            )

    def forward(self, x):
        h = torch.relu(self.bn1(self.conv1(x)))
        h = torch.relu(self.bn2(self.conv2(h)))
        h = self.bn3(self.conv3(h))
        return torch.relu(h + self.short(x))


def make_stage(in_c, out_c, n_blocks, cardinality, stride=1, use_cbam=True):
    blocks = [ResNeXtBlock(in_c, out_c, cardinality, stride)]
    blocks += [ResNeXtBlock(out_c, out_c, cardinality, 1) for _ in range(n_blocks - 1)]
    stage = nn.Sequential(*blocks)
    if use_cbam:
        return nn.Sequential(stage, CBAM(out_c))
    return stage


class ResNextCBAM(nn.Module):
    """ResNeXt backbone with CBAM attention. Input: 32x32xC, output: logits(17)."""

    def __init__(self, in_ch, nclass=17, width=64, cardinality=8, depth=3):
        super().__init__()
        w = width
        self.stem = nn.Sequential(
            nn.Conv2d(in_ch, w, 3, 1, 1, bias=False),
            nn.BatchNorm2d(w),
            nn.ReLU(inplace=True),
        )
        self.stage1 = make_stage(w, w, depth, cardinality, 1, use_cbam=True)
        self.stage2 = make_stage(w, w * 2, depth, cardinality, 2, use_cbam=True)
        self.stage3 = make_stage(w * 2, w * 4, depth, cardinality, 2, use_cbam=True)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(w * 4, nclass)

    def forward(self, x):
        h = self.stem(x)
        h = self.stage1(h)
        h = self.stage2(h)
        h = self.stage3(h)
        h = self.pool(h).flatten(1)
        return self.fc(h)


def build_model(in_ch, nclass=17, variant="l"):
    if variant == "l":
        return ResNextCBAM(in_ch, nclass, width=64, cardinality=8, depth=3)
    return ResNextCBAM(in_ch, nclass, width=32, cardinality=4, depth=2)


if __name__ == "__main__":
    m = build_model(10, variant="l")
    x = torch.randn(2, 10, 32, 32)
    print("out:", m(x).shape, "params(M):", sum(p.numel() for p in m.parameters()) / 1e6)
    m2 = build_model(18, variant="s")
    print("out(s,fusion):", m2(x[:1].repeat(1, 18, 1, 1)[:, :18]).shape,
          "params(M):", sum(p.numel() for p in m2.parameters()) / 1e6)