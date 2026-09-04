import os, sys
import numpy as np, torch
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
from torch.utils.data.dataloader import _BaseDataLoaderIter
BLS_REPO = r'F:/dataset/2604.04681v1/code/BLS'
sys.path.insert(0, BLS_REPO)
from BLS import prune

print('patch active:', _BaseDataLoaderIter.__next__.__name__ if hasattr(_BaseDataLoaderIter.__next__, '__name__') else 'builtin')

class Args: pass
a=Args(); a.prune_type='BLS_InfoBatch'; a.ratio=0.3; a.num_group=5; a.window_scale=0.9; a.delta=0.875; a.epochs=2; a.prune_ratio=0.3; a.alpha=0.7
tf = transforms.ToTensor()
full = datasets.CIFAR10(root=os.path.join(BLS_REPO,'data','cifar10'), train=True, download=False, transform=tf)
idx = np.random.RandomState(0).choice(len(full), 50, replace=False)
ts = Subset(full, idx)
h = prune(ts, a)
sm = h.sampler
loader = DataLoader(h, batch_size=8, shuffle=False, sampler=sm)
it = iter(loader)
# check what __next__ returns directly
nd = it._next_data()
print('_next_data(): type', type(nd), 'len', len(nd))
for i, e in enumerate(nd):
    print('  [%d] type=%s' % (i, type(e)), getattr(e, 'shape', ''))
    if isinstance(e, list):
        print('      list len', len(e), 'first elem', type(e[0]), getattr(e[0], 'shape', None))
b = next(it)
print('next(it): type', type(b), 'len', len(b))
for i, e in enumerate(b):
    print('  [%d] type=%s' % (i, type(e)), getattr(e, 'shape', ''))
