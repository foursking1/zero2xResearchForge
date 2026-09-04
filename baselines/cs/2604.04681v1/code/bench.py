"""Benchmark tensor-based fast training loop with official BLS logic."""
import os, sys, time
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from torchvision import datasets, transforms
BLS_REPO = r'F:/dataset/2604.04681v1/code/BLS'
sys.path.insert(0, BLS_REPO)
sys.path.insert(0, os.path.join(BLS_REPO, 'examples', 'cifar'))
from BLS import prune
from model import ResNet18

def load_tensor_dataset(name, n_train, n_test, seed=123):
    data_dir = os.path.join(BLS_REPO, 'data', name)
    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.4914,0.4822,0.4465),(0.2023,0.1994,0.2010))])
    if name == 'cifar10':
        ds = datasets.CIFAR10(root=data_dir, train=True, download=False, transform=tf)
        te = datasets.CIFAR10(root=data_dir, train=False, download=False, transform=tf)
    else:
        ds = datasets.CIFAR100(root=data_dir, train=True, download=False, transform=tf)
        te = datasets.CIFAR100(root=data_dir, train=False, download=False, transform=tf)
    rng = np.random.RandomState(seed)
    idx = rng.choice(len(ds), n_train, replace=False)
    imgs = torch.stack([ds[i][0] for i in idx])
    labels = torch.tensor([ds[i][1] for i in idx])
    tidx = rng.choice(len(te), n_test, replace=False)
    timgs = torch.stack([te[i][0] for i in tidx])
    tlabels = torch.tensor([te[i][1] for i in tidx])
    return imgs, labels, timgs, tlabels

def augment(images):
    images = F.pad(images, (4,4,4,4), mode='reflect')
    off_h = np.random.randint(0, 9)
    off_w = np.random.randint(0, 9)
    images = images[:, :, off_h:off_h+32, off_w:off_w+32]
    if np.random.rand() < 0.5:
        images = torch.flip(images, dims=[3])
    return images

def run(name, prune_type, ratio, epochs, seed, n_train=3000, n_test=2000, batch_size=64, alpha=0.7, num_classes=10, model_fn=ResNet18):
    torch.manual_seed(seed); np.random.seed(seed)
    imgs, labels, timgs, tlabels = load_tensor_dataset(name, n_train, n_test)
    if name == 'cifar100':
        num_classes = 100
    class Args: pass
    a = Args(); a.prune_type=prune_type; a.ratio=ratio; a.num_group=5; a.window_scale=0.9; a.delta=0.875
    a.epochs=epochs; a.prune_ratio=ratio; a.alpha=alpha
    # wrap a plain dataset object so InfoBatch.__getitem__ works (returns index, data) -- but we bypass with tensor indexing
    class PlainDS(torch.utils.data.Dataset):
        def __init__(self, imgs, labels): self.imgs=imgs; self.labels=labels
        def __len__(self): return len(self.labels)
        def __getitem__(self, i): return self.imgs[i], self.labels[i]
    ds = PlainDS(imgs, labels)
    handler = prune(ds, a)
    sampler = handler.sampler
    net = model_fn(num_classes=num_classes)
    crit = nn.CrossEntropyLoss(reduction='none')
    opt = torch.optim.SGD(net.parameters(), lr=0.1, momentum=0.9, weight_decay=5e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    valid_acc = []
    t0 = time.time()
    for epoch in range(epochs):
        indices = list(sampler)
        net.train()
        for i in range(0, len(indices), batch_size):
            bidx = indices[i:i+batch_size]
            b = torch.tensor(bidx)
            handler.set_active_indices(b)
            x = augment(imgs[b])
            y = labels[b]
            opt.zero_grad()
            out = net(x)
            loss = handler.update(crit(out, y))
            loss.backward(); opt.step()
        sched.step()
        net.eval()
        with torch.no_grad():
            pred = net(timgs).argmax(1)
        acc = (pred == tlabels).float().mean().item() * 100
        valid_acc.append(acc)
    return {'valid_acc': valid_acc, 'saved_ratio': handler.get_saved_ratio(),
            'best_acc': max(valid_acc), 'final_acc': valid_acc[-1], 'time_s': time.time()-t0}

if __name__ == '__main__':
    for t in ['full', 'InfoBatch', 'BLS_InfoBatch', 'SeTa', 'BLS_SeTa']:
        t0 = time.time()
        r = run('cifar10', t, 0.3, 15, seed=0, n_train=3000, n_test=2000)
        print(t, 'best=%.2f final=%.2f saved=%.3f time=%.1fs' % (r['best_acc'], r['final_acc'], r['saved_ratio'], time.time()-t0))
