"""Extract frozen ImageNet-pretrained ResNet18 GAP features for all images.

No training happens here; purely a forward pass in eval mode. Result cached in
  results/features_resnet18_224.npz  (array 'feat' [N, 512] float32)
"""
import os
import sys
import time

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import RESULTS_DIR, SEED, normalize, set_seed  # noqa: E402

from torchvision.models import resnet18, ResNet18_Weights  # noqa: E402


def load_store():
    p = os.path.join(RESULTS_DIR, "images_224.memmap")
    arr = np.load(p, mmap_mode="r")
    labels = np.load(os.path.join(RESULTS_DIR, "labels.npz"))
    return arr, labels


@torch.inference_mode()
def main():
    set_seed()
    torch.set_num_threads(int(os.environ.get("TORCH_THREADS","10")))
    arr, labels = load_store()
    n = arr.shape[0]
    print(f"[feat] {n} images")

    w = ResNet18_Weights.IMAGENET1K_V1
    model = resnet18(weights=w)
    model.fc = torch.nn.Identity()
    model.eval()

    dl = DataLoader(TensorDataset(torch.arange(n)), shuffle=False,
                    batch_size=128, num_workers=0)
    feats = np.zeros((n, 512), dtype=np.float32)
    t0 = time.time()
    for bi, (idx,) in enumerate(dl):
        ids = idx.numpy()
        x = np.ascontiguousarray(arr[ids])  # [B,224,224,3] uint8
        xt = normalize(x).transpose(0, 3, 1, 2)
        with torch.no_grad():
            f = model(torch.from_numpy(xt)).numpy()
        feats[ids] = f
        if bi % 20 == 0:
            print(f"  batch {bi} done {time.time()-t0:.0f}s")
    np.savez_compressed(os.path.join(RESULTS_DIR, "features_resnet18_224.npz"), feat=feats)
    print(f"[feat] saved features in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()