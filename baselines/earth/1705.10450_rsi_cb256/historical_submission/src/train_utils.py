"""Shared model definition (MultiTaskResNet) + augmentation helpers."""
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms
from torchvision.models import resnet18, ResNet18_Weights

from common import N_L1, N_L2, normalize  # noqa: E402


class MultiTaskResNet(nn.Module):
    """ResNet18 backbone with a shared GAP embedding + label_2/label_1 heads."""

    def __init__(self):
        super().__init__()
        self.backbone = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
        self.backbone.fc = nn.Identity()  # expose 512-d GAP embedding
        self.head2 = nn.Sequential(
            nn.Linear(512, 512), nn.ReLU(inplace=True), nn.Dropout(0.3),
            nn.Linear(512, N_L2))
        self.head1 = nn.Linear(512, N_L1)

    def embed_and_logits(self, x):
        f = torch.flatten(self.backbone(x), 1)
        return self.head2(f), self.head1(f), f


def make_augment():
    return transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.5, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.RandomRotation(10),
    ])


def augment_batch(x_uint8, transform):
    """Apply a torchvision PIL transform per sample; returns normalized CHW tensor."""
    out = torch.empty(x_uint8.shape[0], 3, 224, 224)
    for i in range(x_uint8.shape[0]):
        pil = transforms.ToPILImage()(x_uint8[i])  # numpy input: (H,W,C)
        pil = transform(pil)
        arr = normalize(np.asarray(pil))
        out[i] = torch.tensor(arr.transpose(2, 0, 1))
        pil.close()
    return out