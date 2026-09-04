"""Smoke test: verify BLS package imports and runs 2 training epochs on a tiny CIFAR10 subset on CPU."""
import os, sys, time, json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

# Official BLS repo path (frozen data, read-only)
BLS_REPO = r"F:/dataset/2604.04681v1/code/BLS"
sys.path.insert(0, BLS_REPO)
sys.path.insert(0, os.path.join(BLS_REPO, "examples", "cifar"))

from BLS import prune  # noqa: E402
from model import ResNet18  # noqa: E402

def main():
    torch.manual_seed(42)
    np.random.seed(42)
    device = "cpu"

    data_dir = os.path.join(BLS_REPO, "data", "cifar10")
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])
    full = datasets.CIFAR10(root=data_dir, train=True, download=False, transform=transform)
    idx = np.random.RandomState(0).choice(len(full), 300, replace=False)
    trainset = Subset(full, idx)
    testset = datasets.CIFAR10(root=data_dir, train=False, download=False, transform=transform)
    # small test subset
    tidx = np.random.RandomState(0).choice(len(testset), 300, replace=False)
    testset = Subset(testset, tidx)

    class Args:
        prune_type = "BLS_InfoBatch"
        ratio = 0.3
        num_group = 5
        window_scale = 0.9
        delta = 0.875
        epochs = 2
        prune_ratio = 0.3
        alpha = 0.7
    args = Args()

    handler = prune(trainset, args)
    sampler = handler.sampler
    loader = DataLoader(handler, batch_size=64, shuffle=False, sampler=sampler)
    net = ResNet18(num_classes=10)
    crit = nn.CrossEntropyLoss(reduction="none")
    opt = optim.SGD(net.parameters(), lr=0.1, momentum=0.9, weight_decay=5e-4)

    for epoch in range(2):
        net.train()
        n = 0
        for blobs in loader:
            inputs, targets = blobs
            opt.zero_grad()
            out = net(inputs)
            loss = crit(out, targets)
            loss = handler.update(loss)
            loss.backward()
            opt.step()
            n += len(inputs)
        # eval
        net.eval()
        correct = 0
        with torch.no_grad():
            for inputs, targets in DataLoader(testset, batch_size=64):
                correct += (net(inputs).argmax(1) == targets).sum().item()
        print(f"epoch {epoch}: train_seen={n}, test_acc={correct/len(testset)*100:.2f}%")

    print("SMOKE OK")

if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"elapsed {time.time()-t0:.1f}s")
