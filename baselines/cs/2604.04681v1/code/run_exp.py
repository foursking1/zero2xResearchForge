"""Run a single BLS CIFAR training experiment on CPU using official BLS scoring/pruning logic.

Usage:
  python run_exp.py --data cifar10 --prune_type BLS_InfoBatch --ratio 0.3 --seed 0 \
      --epochs 12 --n_train 3000 --n_test 2000 --batch_size 64 --out DIR --model resnet18
"""
import argparse, json, os, sys, time
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from torchvision import datasets, transforms

BLS_REPO = r"F:/dataset/2604.04681v1/code/BLS"
sys.path.insert(0, BLS_REPO)
sys.path.insert(0, os.path.join(BLS_REPO, "examples", "cifar"))
from BLS import prune  # noqa: E402
from model import ResNet18, ResNet50  # noqa: E402

STATS = ((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))

def load_tensor_dataset(name, n_train, n_test, seed=123):
    data_dir = os.path.join(BLS_REPO, "data", name)
    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize(*STATS)])
    if name == "cifar10":
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
    images = F.pad(images, (4, 4, 4, 4), mode="reflect")
    off_h = np.random.randint(0, 9)
    off_w = np.random.randint(0, 9)
    images = images[:, :, off_h:off_h + 32, off_w:off_w + 32]
    if np.random.rand() < 0.5:
        images = torch.flip(images, dims=[3])
    return images

class PlainDS(torch.utils.data.Dataset):
    def __init__(self, imgs, labels):
        self.imgs = imgs
        self.labels = labels
    def __len__(self):
        return len(self.labels)
    def __getitem__(self, i):
        return self.imgs[i], self.labels[i]

def run(data, prune_type, ratio, epochs, seed, n_train, n_test, batch_size, alpha,
        model_name, num_threads=12):
    torch.set_num_threads(num_threads)
    torch.manual_seed(seed)
    np.random.seed(seed)
    imgs, labels, timgs, tlabels = load_tensor_dataset(data, n_train, n_test)
    num_classes = 100 if data == "cifar100" else 10

    class Args: pass
    a = Args()
    a.prune_type = prune_type
    a.ratio = ratio
    a.num_group = 5
    a.window_scale = 0.9
    a.delta = 0.875
    a.epochs = epochs
    a.prune_ratio = ratio
    a.alpha = alpha
    ds = PlainDS(imgs, labels)
    handler = prune(ds, a)
    sampler = handler.sampler
    net = (ResNet50(num_classes=num_classes) if model_name == "resnet50" else ResNet18(num_classes=num_classes))
    crit = nn.CrossEntropyLoss(reduction="none")
    opt = torch.optim.SGD(net.parameters(), lr=0.1, momentum=0.9, weight_decay=5e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    valid_acc = []
    t0 = time.time()
    for epoch in range(epochs):
        indices = list(sampler)  # reset -> prune/no_prune each epoch
        net.train()
        for i in range(0, len(indices), batch_size):
            bidx = indices[i:i + batch_size]
            b = torch.tensor(bidx)
            handler.set_active_indices(b)
            x = augment(imgs[b])
            y = labels[b]
            opt.zero_grad()
            out = net(x)
            loss = handler.update(crit(out, y))
            loss.backward()
            opt.step()
        sched.step()
        net.eval()
        with torch.no_grad():
            pred = net(timgs).argmax(1)
        valid_acc.append(float((pred == tlabels).float().mean().item() * 100))
    return {
        "data": data, "prune_type": prune_type, "ratio": ratio, "epochs": epochs,
        "seed": seed, "model": model_name, "alpha": alpha,
        "n_train": n_train, "n_test": n_test, "batch_size": batch_size,
        "valid_acc": valid_acc, "best_acc": max(valid_acc), "final_acc": valid_acc[-1],
        "saved_ratio": handler.get_saved_ratio(),
        "pruned_count": handler.get_pruned_count(), "time_s": time.time() - t0,
    }

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="cifar10")
    p.add_argument("--prune_type", default="BLS_InfoBatch")
    p.add_argument("--ratio", type=float, default=0.3)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--epochs", type=int, default=12)
    p.add_argument("--n_train", type=int, default=3000)
    p.add_argument("--n_test", type=int, default=2000)
    p.add_argument("--batch_size", type=int, default=64)
    p.add_argument("--alpha", type=float, default=0.7)
    p.add_argument("--model", default="resnet18")
    p.add_argument("--out", default="results/cpu")
    p.add_argument("--threads", type=int, default=12)
    args = p.parse_args()
    os.makedirs(args.out, exist_ok=True)
    res = run(data=args.data, prune_type=args.prune_type, ratio=args.ratio, seed=args.seed,
              epochs=args.epochs, n_train=args.n_train, n_test=args.n_test,
              batch_size=args.batch_size, alpha=args.alpha, model_name=args.model,
              num_threads=args.threads)
    fn = f"{args.data}_{args.prune_type}_{args.ratio}_{args.seed}_{args.model}.json"
    with open(os.path.join(args.out, fn), "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: res[k] for k in ["data", "prune_type", "ratio", "seed", "model",
          "best_acc", "final_acc", "saved_ratio", "time_s"]}))
