"""
Noise sensitivity of the frozen MVis-Fold small checkpoint.

The same deterministic 50-sample synthetic test set (max_branches=15,
generator seeds 300..349, channel seeds offset +5000) is evaluated at three
SRUS channel noise levels (0.05, 0.1, 0.3) to confirm the frozen model is
smoothly robust to imaging noise (no catastrophic collapse).

Frozen data read in place from --root (default F:/dataset/2604.04477v1).
Output: <outdir>/noise_sensitivity.json
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
    p.add_argument('--noise-levels', default='0.05,0.1,0.3',
                   help='comma-separated noise levels')
    p.add_argument('--n-test', type=int, default=50)
    p.add_argument('--test-seed', type=int, default=300)
    return p.parse_args()


def main():
    args = parse_args()
    ROOT = os.path.abspath(args.root)
    OUT = os.path.abspath(args.outdir) if args.outdir else os.path.join(
        os.getcwd(), 'results')
    os.makedirs(OUT, exist_ok=True)
    sys.path.insert(0, os.path.join(ROOT, 'src'))

    from models.mvisfold import build_model
    from data.synthetic import VascularTreeGenerator, generate_sruse_channels
    from evaluate.metrics import compute_all_metrics

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    shape = (16, 32, 32)
    model, _, _ = build_model(in_channels=6, use_small=True, device=device)
    ckpt = torch.load(os.path.join(ROOT, 'checkpoints', 'stage1_best.pth'),
                      map_location=device, weights_only=False)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()
    print(f'[noise] root={ROOT} device={device} n_test={args.n_test}')

    noise_levels = [float(x) for x in args.noise_levels.split(',')]
    out = {'n_test': args.n_test, 'noise_levels': {}}
    for noise in noise_levels:
        dice, sens, spec, acc = [], [], [], []
        with torch.no_grad():
            for i in range(args.n_test):
                gen = VascularTreeGenerator(shape=shape, max_branches=15,
                                            seed=args.test_seed + i)
                phantom = gen.generate()
                channels = generate_sruse_channels(phantom, noise_level=noise,
                                                   seed=args.test_seed + i + 5000)
                x = torch.from_numpy(channels).unsqueeze(0).float().to(device)
                out_m = model(x)
                m = compute_all_metrics(out_m[0, 0].cpu().numpy(), phantom.volume)
                dice.append(m['dice']); sens.append(m['sensitivity'])
                spec.append(m['specificity']); acc.append(m['accuracy'])
        out['noise_levels'][str(noise)] = {
            'dice_mean': float(np.mean(dice)),
            'sens_mean': float(np.mean(sens)),
            'spec_mean': float(np.mean(spec)),
            'acc_mean': float(np.mean(acc)),
        }
        print(f'  noise={noise}: Dice {np.mean(dice):.4f}  Sens {np.mean(sens):.4f}  '
              f'Spec {np.mean(spec):.4f}  Acc {np.mean(acc):.4f}')

    with open(os.path.join(OUT, 'noise_sensitivity.json'), 'w') as f:
        json.dump(out, f, indent=2)
    print(f'[noise] wrote {os.path.join(OUT, "noise_sensitivity.json")}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
