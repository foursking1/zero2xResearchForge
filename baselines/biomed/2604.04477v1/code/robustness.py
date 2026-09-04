"""
Robustness / sensitivity check: Dice of the frozen MVis-Fold checkpoint across
several independently generated test sets (different seed offsets).

Output: <outdir>/robustness.json
"""
import argparse
import json
import os
import sys

import numpy as np
import torch


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--root', default='F:/dataset/2604.04477v1')
    p.add_argument('--outdir', default=None)
    p.add_argument('--seeds', default='100,200,300,400',
                   help='comma-separated test-set seed offsets')
    p.add_argument('--n-per-seed', type=int, default=20)
    return p.parse_args()


def main():
    args = parse_args()
    ROOT = os.path.abspath(args.root)
    OUT = os.path.abspath(args.outdir) if args.outdir else os.path.join(os.getcwd(), 'results')
    os.makedirs(OUT, exist_ok=True)
    sys.path.insert(0, os.path.join(ROOT, 'src'))

    from models.mvisfold import build_model
    from data.synthetic import VascularTreeGenerator, generate_sruse_channels
    from evaluate.metrics import compute_dice

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model, _, _ = build_model(in_channels=6, use_small=True, device=device)
    ckpt = torch.load(os.path.join(ROOT, 'checkpoints', 'stage1_best.pth'),
                      map_location=device, weights_only=False)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()

    seeds = [int(s) for s in args.seeds.split(',')]
    out = {'n_per_seed': args.n_per_seed, 'seeds': {}}
    all_dice = []
    for seed in seeds:
        dices = []
        with torch.no_grad():
            for i in range(args.n_per_seed):
                gen = VascularTreeGenerator(shape=(16, 32, 32), max_branches=15,
                                            seed=seed + i)
                phantom = gen.generate()
                channels = generate_sruse_channels(phantom, noise_level=0.1,
                                                   seed=seed + i + 5000)
                x = torch.from_numpy(channels).unsqueeze(0).float().to(device)
                out_m = model(x)
                dices.append(compute_dice(out_m[0, 0].cpu().numpy(), phantom.volume))
        out['seeds'][str(seed)] = {
            'dice_mean': float(np.mean(dices)),
            'dice_std': float(np.std(dices)),
        }
        all_dice.extend(dices)
        print(f'  seed={seed}: Dice {np.mean(dices):.4f} +/- {np.std(dices):.4f}')

    out['all_seeds_pooled'] = {
        'dice_mean': float(np.mean(all_dice)),
        'dice_std': float(np.std(all_dice)),
        'n': len(all_dice),
    }
    print(f"  pooled: Dice {np.mean(all_dice):.4f} +/- {np.std(all_dice):.4f} (n={len(all_dice)})")
    with open(os.path.join(OUT, 'robustness.json'), 'w') as f:
        json.dump(out, f, indent=2)
    return 0


if __name__ == '__main__':
    sys.exit(main())
