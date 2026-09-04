"""Verify manual-batching harness works with official BLS InfoBatch/BLS/SeTa logic."""
import os, sys, time
import numpy as np, torch, torch.nn as nn
from torchvision import datasets, transforms
from torch.utils.data import Subset
BLS_REPO = r'F:/dataset/2604.04681v1/code/BLS'
sys.path.insert(0, BLS_REPO)
sys.path.insert(0, os.path.join(BLS_REPO, 'examples', 'cifar'))
from BLS import prune
from model import ResNet18

def make_handler(dataset, prune_type, epochs, ratio, alpha=0.7, num_group=5, window_scale=0.9, delta=0.875):
    class Args: pass
    a = Args()
    a.prune_type = prune_type
    a.ratio = ratio
    a.num_group = num_group
    a.window_scale = window_scale
    a.delta = delta
    a.epochs = epochs
    a.prune_ratio = ratio
    a.alpha = alpha
    return prune(dataset, a)

def train_and_eval(dataset, testset, prune_type, ratio, epochs, seed, num_classes, device='cpu', batch_size=64, alpha=0.7):
    torch.manual_seed(seed)
    np.random.seed(seed)
    handler = make_handler(dataset, prune_type, epochs, ratio, alpha=alpha)
    sampler = handler.sampler
    net = ResNet18(num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss(reduction='none').to(device)
    optimizer = torch.optim.SGD(net.parameters(), lr=0.1, momentum=0.9, weight_decay=5e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    valid_acc = []
    for epoch in range(epochs):
        indices = list(sampler)  # triggers reset -> prune/no_prune
        net.train()
        for i in range(0, len(indices), batch_size):
            batch_idx = indices[i:i+batch_size]
            batch = [handler[j] for j in batch_idx]
            imgs = torch.stack([b[1][0] for b in batch])
            tgts = torch.tensor([int(b[1][1]) for b in batch])
            handler.set_active_indices(torch.tensor(batch_idx))
            optimizer.zero_grad()
            out = net(imgs)
            loss = handler.update(criterion(out, tgts))
            loss.backward()
            optimizer.step()
        sched.step()
        net.eval()
        correct = 0
        with torch.no_grad():
            for i in range(0, len(testset), 256):
                batch = [testset[j] for j in range(i, min(i+256, len(testset)))]
                imgs = torch.stack([b[0] for b in batch])
                tgts = torch.tensor([int(b[1]) for b in batch])
                correct += (net(imgs).argmax(1) == tgts).sum().item()
        valid_acc.append(100.0 * correct / len(testset))
    return {'valid_acc': valid_acc, 'saved_ratio': handler.get_saved_ratio(),
            'best_acc': max(valid_acc), 'final_acc': valid_acc[-1], 'epochs': epochs}

def main():
    BLS_DATA = os.path.join(BLS_REPO, 'data', 'cifar10')
    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.4914,0.4822,0.4465),(0.2023,0.1994,0.2010))])
    full = datasets.CIFAR10(root=BLS_DATA, train=True, download=False, transform=tf)
    rng = np.random.RandomState(123)
    sub_idx = rng.choice(len(full), 600, replace=False)
    dataset = Subset(full, sub_idx)
    testset = datasets.CIFAR10(root=BLS_DATA, train=False, download=False, transform=tf)
    tidx = np.random.RandomState(0).choice(len(testset), 600, replace=False)
    testset = Subset(testset, tidx)
    for t in ['BLS_InfoBatch', 'InfoBatch', 'BLS_SeTa', 'SeTa', 'full']:
        t0 = time.time()
        res = train_and_eval(dataset, testset, t, 0.3, 3, seed=0, num_classes=10, batch_size=64)
        print(t, 'best=%.2f' % res['best_acc'], 'final=%.2f' % res['final_acc'],
              'saved_ratio=%.3f' % res['saved_ratio'], 'time=%.1fs' % (time.time()-t0))

if __name__ == '__main__':
    main()
