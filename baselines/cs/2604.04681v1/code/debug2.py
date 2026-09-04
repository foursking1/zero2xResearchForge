import os, sys
import numpy as np, torch
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
BLS_REPO = r'F:/dataset/2604.04681v1/code/BLS'
sys.path.insert(0, BLS_REPO)
from BLS import prune

def dbg_collate(batch):
    print('=== dbg_collate called, len(batch)=', len(batch))
    for i, b in enumerate(batch[:3]):
        print(f'batch[{i}] type={type(b)} len={len(b)}')
        for j, part in enumerate(b):
            print(f'  part[{j}] type={type(part)} shape={getattr(part,"shape",None)} val={part if not hasattr(part,"shape") else ""}')
    return batch

class Args: pass
a=Args(); a.prune_type='BLS_InfoBatch'; a.ratio=0.3; a.num_group=5; a.window_scale=0.9; a.delta=0.875; a.epochs=2; a.prune_ratio=0.3; a.alpha=0.7
tf = transforms.ToTensor()
full = datasets.CIFAR10(root=os.path.join(BLS_REPO,'data','cifar10'), train=True, download=False, transform=tf)
idx = np.random.RandomState(0).choice(len(full), 50, replace=False)
ts = Subset(full, idx)
h = prune(ts, a)
sm = h.sampler
loader = DataLoader(h, batch_size=8, shuffle=False, sampler=sm, collate_fn=dbg_collate)
it = iter(loader)
b = next(it)
print('iter returned type', type(b), 'len', len(b) if hasattr(b, '__len__') else '?')
