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
    imgs = torch.stack([ds[i][0] for i in idx]); labels = torch.tensor([ds[i][1] for i in idx])
    tidx = rng.choice(len(te), n_test, replace=False)
    timgs = torch.stack([te[i][0] for i in tidx]); tlabels = torch.tensor([te[i][1] for i in tidx])
    return imgs, labels, timgs, tlabels

def augment(images):
    images = F.pad(images, (4,4,4,4), mode='reflect')
    off_h = np.random.randint(0, 9); off_w = np.random.randint(0, 9)
    images = images[:, :, off_h:off_h+32, off_w:off_w+32]
    if np.random.rand() < 0.5:
        images = torch.flip(images, dims=[3])
    return images

torch.set_num_threads(12)
imgs, labels, timgs, tlabels = load_tensor_dataset('cifar10', 3000, 2000)
class PlainDS(torch.utils.data.Dataset):
    def __init__(s, imgs, labels): s.imgs=imgs; s.labels=labels
    def __len__(s): return len(s.labels)
    def __getitem__(s, i): return s.imgs[i], s.labels[i]
ds = PlainDS(imgs, labels)
class Args: pass
a=Args(); a.prune_type='full'; a.ratio=0.3; a.num_group=5; a.window_scale=0.9; a.delta=0.875; a.epochs=15; a.prune_ratio=0.3; a.alpha=0.7
handler = prune(ds, a)
sampler = handler.sampler
net = ResNet18(num_classes=10)
crit = nn.CrossEntropyLoss(reduction='none')
opt = torch.optim.SGD(net.parameters(), lr=0.1, momentum=0.9, weight_decay=5e-4)
indices = list(sampler)
print('n_train_batches for epoch:', (len(indices)+63)//64, 'len indices', len(indices))
# time 2 epochs
for ep in range(2):
    t0 = time.time()
    net.train()
    for i in range(0, len(indices), 64):
        bidx = indices[i:i+64]
        b = torch.tensor(bidx)
        handler.set_active_indices(b)
        x = augment(imgs[b]); y = labels[b]
        opt.zero_grad(); out = net(x); loss = handler.update(crit(out, y)); loss.backward(); opt.step()
    print('epoch', ep, 'time', time.time()-t0)
    indices = list(sampler)
