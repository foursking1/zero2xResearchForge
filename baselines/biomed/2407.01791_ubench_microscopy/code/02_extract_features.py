#!/usr/bin/env python
"""Step 2: extract frozen-backbone image features for every unique image in the
frozen Arrow shard (fully offline; CPU by default, CUDA available via --device).

Models:
  - timm `vit_base_patch16_224.augreg2_in21k_ft_in1k`  (CLS token, D=768)
  - torchvision `resnet18` (IMAGENET1K_V1)              (pooled,      D=512)

Outputs: features/features_<model>.npy  (N x D, float32)
         features/image_keys_<model>.csv (image_id per row)
"""
import argparse
import os
import time
import warnings

import torch

warnings.filterwarnings("ignore", category=FutureWarning)


def build_model(name, device):
    if name == "vit_base_patch16_224":
        import timm

        model = timm.create_model(
            "vit_base_patch16_224.augreg2_in21k_ft_in1k", pretrained=True)
        model.eval()
        data_cfg = timm.data.resolve_model_data_config(model)
        transform = timm.data.create_transform(**data_cfg, is_training=False)
        feats = _vit_features
    elif name == "resnet18":
        from torchvision import models, transforms

        model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        model.eval()
        transform = transforms.Compose([
            transforms.Resize(256, interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        feats = _resnet_features
    else:
        raise ValueError(name)
    return model.to(device), transform, feats


@torch.no_grad()
def _vit_features(model, x):
    return model.forward_features(x)[:, 0]


@torch.no_grad()
def _resnet_features(model, x):
    z = model.conv1(x)
    z = model.bn1(z)
    z = model.relu(z)
    z = model.maxpool(z)
    z = model.layer1(z)
    z = model.layer2(z)
    z = model.layer3(z)
    z = model.layer4(z)
    z = model.avgpool(z)
    return z.flatten(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True,
                    choices=["vit_base_patch16_224", "resnet18"])
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--batch", type=int, default=32)
    args = ap.parse_args()

    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _common import load_arrow_questions, decode_image_bytes, FEATURES
    from PIL import Image

    df = load_arrow_questions()
    uniq = df.drop_duplicates("image_id").reset_index(drop=True)
    image_ids = uniq["image_id"].tolist()
    print(f"unique images: {len(image_ids)}")

    device = torch.device(args.device)
    if args.device == "cpu":
        torch.set_num_threads(min(20, os.cpu_count() or 4))
    model, transform, feats_fn = build_model(args.model, device)

    all_feats = []
    t0 = time.time()
    with torch.no_grad():
        for s in range(0, len(image_ids), args.batch):
            chunk = image_ids[s:s + args.batch]
            tensors = [transform(decode_image_bytes(uniq["image_bytes"].iloc[j])) for j in range(s, s + len(chunk))]
            x = torch.stack(tensors).to(device)
            f = feats_fn(model, x).cpu()
            all_feats.append(f)
            if (s // args.batch) % 10 == 0:
                print(f"  {s}/{len(image_ids)}  ({time.time()-t0:.0f}s)", flush=True)
    feat = torch.cat(all_feats, 0).numpy().astype("float32")
    out_p = os.path.join(FEATURES, f"features_{args.model}.npy")
    key_p = os.path.join(FEATURES, f"image_keys_{args.model}.csv")
    import numpy as np
    np.save(out_p, feat)
    import pandas as pd
    pd.DataFrame({"image_id": image_ids}).to_csv(key_p, index=False)
    print(f"saved {out_p} shape={feat.shape} in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()