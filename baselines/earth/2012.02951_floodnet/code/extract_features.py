"""Extract frozen pretrained visual features for all VQA images.

Features (ImageNet-pretrained, frozen, CPU):
  * resnet18  - pooled global feature (512-d) + spatial feature map from
                layer4 (7x7x512) at 448x448 resolution;
  * vit_b_16  - CLS token (768-d) at 224x224.

Saves workspace/features_r18.npz and workspace/features_vit.npz keyed by
image id.
"""
import os

import numpy as np
import torch
import torch.nn.functional as F
import torchvision
from PIL import Image

import config

MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]


def load_image(path):
    with Image.open(path) as im:
        im = im.convert("RGB")
    return torch.from_numpy(np.asarray(im)).permute(2, 0, 1).float() / 255.0


class ResNet18Feats(torch.nn.Module):
    def __init__(self):
        super().__init__()
        m = torchvision.models.resnet18(weights=torchvision.models.ResNet18_Weights.IMAGENET1K_V1)
        self.conv = torch.nn.Sequential(*list(m.children())[:-2])  # up to layer4 -> 7x7x512
        self.pool = m.avgpool

    def forward(self, x):
        s = self.conv(x)                 # B,512,7,7
        g = self.pool(s).flatten(1)      # B,512
        return g, s


class ViTFeats(torch.nn.Module):
    """ViT-B/16 returning the CLS-token embedding (before the classification head)."""

    def __init__(self):
        super().__init__()
        self.m = torchvision.models.vit_b_16(weights=torchvision.models.ViT_B_16_Weights.IMAGENET1K_V1)

    def forward(self, x):
        x = self.m.conv_proj(x)
        x = x.flatten(2).transpose(1, 2)
        x = torch.cat([self.m.class_token.expand(x.shape[0], -1, -1), x], dim=1)
        x = self.m.encoder(x)
        return x[:, 0]


def extract(model, kind, size):
    img_ids = sorted({p[:-4] for p in os.listdir(config.IMG_DIR) if p.lower().endswith(".jpg")})
    if kind == "r18":
        out = np.zeros((len(img_ids), 512), dtype=np.float32)
        out_spatial = []
    else:
        out = np.zeros((len(img_ids), 768), dtype=np.float32)
        out_spatial = None

    model.eval()
    with torch.no_grad():
        batch = []
        idxs = []
        for n, img_id in enumerate(img_ids):
            t = load_image(os.path.join(config.IMG_DIR, img_id + ".JPG"))
            t = F.interpolate(t[None], size=(size, size), mode="bilinear", align_corners=False)[0]
            t = (t - torch.tensor(MEAN).view(3, 1, 1)) / torch.tensor(STD).view(3, 1, 1)
            batch.append(t)
            idxs.append(n)
            if len(batch) == config.BATCH_SIZE_FEAT or n == len(img_ids) - 1:
                x = torch.stack(batch)
                if kind == "r18":
                    g, s = model(x)
                    out[idxs] = g.numpy()
                    out_spatial.append(s.numpy())
                else:
                    out[idxs] = model(x).numpy()
                batch = []
                idxs = []
            if (n + 1) % 200 == 0:
                print(f"  {kind}: {n+1}/{len(img_ids)}")

    if out_spatial is not None:
        out_spatial = np.concatenate(out_spatial, axis=0)
    np.savez(os.path.join(config.WORKSPACE, f"features_{kind}.npz"),
             ids=img_ids, feats=out,
             spatial=out_spatial if out_spatial is not None else np.zeros(0))
    print(f"saved features_{kind}.npz shape={out.shape} spatial=", None if out_spatial is None else out_spatial.shape)


def main():
    print("extracting resnet18 ...")
    r18 = ResNet18Feats()
    extract(r18, "r18", config.IMAGE_SIZE_R18)
    print("extracting vit_b_16 ...")
    vit = ViTFeats()
    extract(vit, "vit", config.IMAGE_SIZE_VIT)


if __name__ == "__main__":
    torch.set_num_threads(20)
    main()