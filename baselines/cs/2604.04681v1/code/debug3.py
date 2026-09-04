import os, sys
import numpy as np, torch
from torch.utils.data import DataLoader, Subset, _utils
from torch.utils.data.dataloader import _BaseDataLoaderIter, _SingleProcessDataLoaderIter
from torchvision import datasets, transforms
BLS_REPO = r'F:/dataset/2604.04681v1/code/BLS'
sys.path.insert(0, BLS_REPO)
from BLS import prune, InfoBatch

class Args: pass
a=Args(); a.prune_type='BLS_InfoBatch'; a.ratio=0.3; a.num_group=5; a.window_scale=0.9; a.delta=0.875; a.epochs=2; a.prune_ratio=0.3; a.alpha=0.7
tf = transforms.ToTensor()
full = datasets.CIFAR10(root=os.path.join(BLS_REPO,'data','cifar10'), train=True, download=False, transform=tf)
idx = np.random.RandomState(0).choice(len(full), 50, replace=False)
ts = Subset(full, idx)
h = prune(ts, a)
sm = h.sampler
print('h type:', type(h))
print('h is InfoBatch?', isinstance(h, InfoBatch))
print('h[0]:', [type(x) for x in h[0]], h[0][0] if not hasattr(h[0][0],'shape') else 'tensor')
print('mro of type(h):', [c.__name__ for c in type(h).__mro__])
# manual fetch
sm.reset()
indices = list(sm)[:8]
print('sampled indices:', indices)
dataset = h
samples = [dataset[i] for i in indices]
print('len samples:', len(samples))
print('sample[0] type:', type(samples[0]), 'len:', len(samples[0]))
if isinstance(samples[0], tuple):
    print('sample[0][0]:', type(samples[0][0]), getattr(samples[0][0],'shape',None))
    print('sample[0][1]:', type(samples[0][1]))
# Now check what the iterator's _dataset is
loader = DataLoader(h, batch_size=8, shuffle=False, sampler=sm)
it = iter(loader)
print('iter dataset type:', type(it._dataset))
print('is InfoBatch:', isinstance(it._dataset, InfoBatch))
print('_next_data result structure:')
try:
    nd = it._next_data()
    print('  next_data type:', type(nd), 'len:', len(nd))
except Exception as e:
    print('  ERROR:', e)
