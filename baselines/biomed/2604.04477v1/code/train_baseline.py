"""
Train the Tier-1 baseline (Simple 3D U-Net, the SparseNeuS stand-in shipped in
the workspace) on the same frozen synthetic distribution, then evaluate it on
the same test set used for MVis-Fold.

This gives a functional (non-random) Tier-1 baseline so the C01
"outperforms baselines" part of the claim can be assessed.

Frozen data read in place from --root (default F:/dataset/2604.04477v1).
Output: <outdir>/baseline_results.json
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import torch

ROOT_DEFAULT = 'F:/dataset/2604.04477v1'
sys.path.insert(0, os.path.join(ROOT_DEFAULT, 'src'))
from baselines.sparseneus_wrapper import SimpleBaseline3D  # noqa: E402
from data.synthetic import VascularTreeGenerator, generate_sruse_channels  # noqa: E402
from evaluate.metrics import compute_all_metrics, compute_dice  # noqa: E402

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--root', default='F:/dataset/2604.04477v1')
    p.add_argument('--outdir', default=None)
    p.add_argument('--epochs', type=int, default=40)
    p.add_argument('--n-batches', type=int, default=25,
                   help='training batches per epoch')
    p.add_argument('--n-val-batches', type=int, default=10)
    p.add_argument('--batch-size', type=int, default=2)
    p.add_argument('--test-seed', type=int, default=300)
    p.add_argument('--n-test', type=int, default=50)
    return p.parse_args()


def make_batch(gen, noise, batch_size, seed):
    images, targets = [], []
    for i in range(batch_size):
        s = seed + i
        phantom = gen.generate()
        channels = generate_sruse_channels(phantom, noise_level=noise, seed=s + 5000)
        images.append(channels)
        targets.append(phantom.volume)
    x = torch.from_numpy(np.stack(images)).float()
    y = torch.from_numpy(np.stack(targets)).unsqueeze(1).float()
    return x, y


def main():
    args = parse_args()
    ROOT = os.path.abspath(args.root)
    OUT = os.path.abspath(args.outdir) if args.outdir else os.path.join(os.getcwd(), 'results')
    os.makedirs(OUT, exist_ok=True)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'[baseline] root={ROOT} device={device}')

    shape = (16, 32, 32)
    noise = 0.1
    model = SimpleBaseline3D(in_channels=6).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-5)
    loss_fn = torch.nn.BCEWithLogitsLoss()

    train_gen = VascularTreeGenerator(shape=shape, max_branches=15, seed=42)
    val_gen = VascularTreeGenerator(shape=shape, max_branches=15, seed=100)

    best_val = 0.0
    t0 = time.time()
    for epoch in range(args.epochs):
        model.train()
        total = 0.0
        for bi in range(args.n_batches):
            x, y = make_batch(train_gen, noise, args.batch_size, bi * 1000)
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            out = model(x)
            loss = loss_fn(out, y)
            loss.backward()
            opt.step()
            total += loss.item()
        # validation every 5 epochs
        if (epoch + 1) % 5 == 0 or epoch == 0:
            model.eval()
            dices = []
            with torch.no_grad():
                for bi in range(args.n_val_batches):
                    x, y = make_batch(val_gen, noise, args.batch_size, 10000 + bi * 1000)
                    x, y = x.to(device), y.to(device)
                    out = (model(x) > 0.5).float()
                    for i in range(x.shape[0]):
                        dices.append(compute_dice(out[i, 0].cpu().numpy(),
                                                  y[i, 0].cpu().numpy()))
            val = float(np.mean(dices))
            if val > best_val:
                best_val = val
            print(f'  epoch {epoch+1} loss={total/args.n_batches:.4f} val_dice={val:.4f}')

    print(f'[baseline] training done in {time.time()-t0:.0f}s, best val Dice={best_val:.4f}')

    # Evaluate on the same frozen test set as MVis-Fold
    model.eval()
    metrics = {'dice': [], 'sensitivity': [], 'specificity': [], 'accuracy': [],
               'hausdorff_95': []}
    with torch.no_grad():
        for i in range(args.n_test):
            gen = VascularTreeGenerator(shape=shape, max_branches=15,
                                        seed=args.test_seed + i)
            phantom = gen.generate()
            channels = generate_sruse_channels(phantom, noise_level=noise,
                                               seed=args.test_seed + i + 5000)
            x = torch.from_numpy(channels).unsqueeze(0).float().to(device)
            out = model(x)
            m = compute_all_metrics(out[0, 0].cpu().numpy(), phantom.volume)
            for k, v in m.items():
                metrics[k].append(v)

    res = {
        'name': 'Simple 3D U-Net (Tier 1, SparseNeuS stand-in)',
        'best_val_dice': best_val,
        'test_dice_mean': float(np.mean(metrics['dice'])),
        'test_dice_std': float(np.std(metrics['dice'])),
        'test_sens_mean': float(np.mean(metrics['sensitivity'])),
        'test_spec_mean': float(np.mean(metrics['specificity'])),
        'test_acc_mean': float(np.mean(metrics['accuracy'])),
        'test_hd95_mean': float(np.mean(metrics['hausdorff_95'])),
        'n_test': args.n_test,
        'epochs': args.epochs,
    }
    print(json.dumps(res, indent=2))
    with open(os.path.join(OUT, 'baseline_results.json'), 'w') as f:
        json.dump(res, f, indent=2)
    return 0


if __name__ == '__main__':
    sys.exit(main())
