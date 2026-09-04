"""Vision feature extraction from cached pretrained backbones (offline).

Precomputes and caches per-image features so training runs are fast and
reproducible without any network access. Backbones available offline:
  - resnet18  (torchvision, ~47MB)
  - vit_b_16  (torchvision, ~346MB)
  - timm ViT-B/16 augreg2 in21k ft in1k (~331MB)
"""
import os

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

# --- deterministic offline weights ---
HUB = os.path.expanduser("~/.cache/torch/hub/checkpoints")
RESNET18 = os.path.join(HUB, "resnet18-f37072fd.pth")
VIT_B16 = os.path.join(HUB, "vit_b_16-c867db91.pth")

_tf = transforms.Compose([
    transforms.Resize((224, 224), interpolation=Image.BILINEAR),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def _load_resnet18():
    import torchvision.models as M

    net = M.resnet18(weights=None)
    net.load_state_dict(torch.load(RESNET18, map_location="cpu", weights_only=True))
    net.eval()
    return net


def _load_vit():
    import torchvision.models as M

    net = M.vit_b_16(weights=None)
    net.load_state_dict(torch.load(VIT_B16, map_location="cpu", weights_only=True))
    net.eval()
    return net


def extract_resnet18_conv(inputs, device="cpu", stage=4):
    """Return spatial map after conv stage `stage`. stage=3 -> (B,256,14,14),
    stage=4 -> (B,512,7,7)."""
    net = _load_resnet18().to(device).eval()
    feats = []
    with torch.no_grad():
        for i in range(0, len(inputs), 8):
            t = torch.stack([_tf(im) for im in inputs[i:i + 8]]).to(device)
            x = net.conv1(t); x = net.bn1(x); x = net.relu(x); x = net.maxpool(x)
            x = net.layer1(x); x = net.layer2(x)
            if stage >= 3:
                x = net.layer3(x)
            if stage >= 4:
                x = net.layer4(x)
            feats.append(x.cpu())
    return torch.cat(feats, 0).numpy()


def extract_resnet18_features(images, device="cpu", pool=False):
    """Return conv5 spatial map (B,512,7,7) or pooled (B,512). Uses frozen ResNet18."""
    net = _load_resnet18().to(device).eval()
    feats = []
    with torch.no_grad():
        for i in range(0, len(images), 8):
            t = torch.stack([_tf(im) for im in images[i:i + 8]]).to(device)
            x = net.conv1(t)
            x = net.bn1(x); x = net.relu(x); x = net.maxpool(x)
            x = net.layer1(x); x = net.layer2(x); x = net.layer3(x); x = net.layer4(x)
            if pool:
                x = F.adaptive_avg_pool2d(x, 1).flatten(1)
            feats.append(x.cpu())
    return torch.cat(feats, 0).numpy()


def extract_vit_features(images, device="cpu"):
    """Global tokens (B,768) from frozen ViT-B/16."""
    net = _load_vit().to(device).train(False)
    feats = []
    with torch.no_grad():
        for i in range(0, len(images), 4):
            t = torch.stack([_tf(im) for im in images[i:i + 4]]).to(device)
            out = net._process_input(t)
            n = net.hidden_dim
            out = torch.cat([net.class_token.expand(out.shape[0], -1, -1), out], dim=1)
            out = net.encoder(out)
            feats.append(out[:, 0].detach().cpu())
    return torch.cat(feats, 0).numpy()