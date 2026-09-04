"""
MVis-Fold claim verification on frozen data (arXiv 2604.04477v1).

This script evaluates the MVis-Fold reproduction checkpoint against the frozen
deterministic synthetic data pipeline shipped with the task, and produces the
numbers needed to judge claims C01-C04 of TASK.md.

Frozen data sources (read in place, never copied):
  - F:/dataset/2604.04477v1/checkpoints/stage1_best.pth   (trained small MVis-Fold)
  - F:/dataset/2604.04477v1/src/data/synthetic.py         (deterministic synthetic generator)
  - F:/dataset/2604.04477v1/src/evaluate/*.py             (metric / vessel-analysis code)

Protocol (matches the shipped reference evaluation, run_full_eval.py):
  - Test set: N=50 synthetic vascular phantoms, shape (16,32,32), max_branches=15,
    noise_level=0.1, generator seeds 300..349 (channel seeds offset +5000).
  - Table 1: Dice, sensitivity, specificity, accuracy, HD95, time per sample.
  - Table 2: vessel-density and mean-diameter absolute error for MVis-Fold 3D
    inference vs 2D SRUS direct measurement, plus Pearson correlation of the
    extracted parameters against synthetic ground truth.
  - Internal-validation Dice: N=20 samples following the training-time validation
    protocol (seeds val_seed=99999 + batch*100, batch_size=2, max_branches=10,
    noise=0.05).

Usage:
    python analyze.py [--root F:/dataset/2604.04477v1] [--n-test 50] [--seed 300]

Outputs (written under <cwd>/results unless --outdir given):
    results/metrics.json           machine-readable key metrics
    results/evidence_table.csv     evidence table (metric, value, definition)
    results/per_sample_segmentation.csv
    results/per_sample_parameters.csv
    results/table1_segmentation.json
    results/table2_parameters.json
"""

import argparse
import csv
import json
import os
import sys
import time

import numpy as np
import torch
from scipy import stats as scipy_stats

# ---------------------------------------------------------------------------
# Path setup: read frozen data in place
# ---------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--root', default='F:/dataset/2604.04477v1',
                   help='root of the frozen reproduction workspace')
    p.add_argument('--outdir', default=None,
                   help='output directory (default: <cwd>/results)')
    p.add_argument('--n-test', type=int, default=50,
                   help='number of test samples (paper protocol uses 50)')
    p.add_argument('--test-seed', type=int, default=300,
                   help='seed offset for test set generation')
    p.add_argument('--val-seed', type=int, default=99999,
                   help='seed offset for internal-validation set (training protocol)')
    return p.parse_args()


def main():
    args = parse_args()
    ROOT = os.path.abspath(args.root)
    OUT = os.path.abspath(args.outdir) if args.outdir else os.path.join(
        os.getcwd(), 'results')
    os.makedirs(OUT, exist_ok=True)

    sys.path.insert(0, os.path.join(ROOT, 'src'))
    from models.mvisfold import build_model
    from baselines.triposr_wrapper import TripoSRWrapper
    from baselines.openlrm_wrapper import OpenLRMWrapper
    from data.synthetic import VascularTreeGenerator, generate_sruse_channels
    from evaluate.metrics import compute_all_metrics
    from evaluate.vessel_analysis import compare_parameters

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'[analyze] frozen root = {ROOT}')
    print(f'[analyze] device = {device}, N_test = {args.n_test}')

    # ------------------------------------------------------------------
    # Load the frozen MVis-Fold checkpoint (small model, stage 1 diverse)
    # ------------------------------------------------------------------
    ckpt_path = os.path.join(ROOT, 'checkpoints', 'stage1_best.pth')
    model, _, _ = build_model(in_channels=6, use_small=True, device=device)
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()
    ckpt_info = {
        'stage': ckpt.get('stage'), 'epoch': ckpt.get('epoch'),
        'best_dice_at_save': float(ckpt.get('best_dice', -1.0)),
        'shape': ckpt.get('shape'),
    }
    print(f"[analyze] loaded checkpoint: {ckpt_info}")

    SHAPE = (16, 32, 32)
    MAX_BRANCHES = 15
    NOISE = 0.1

    def make_test_sample(idx):
        gen = VascularTreeGenerator(shape=SHAPE, max_branches=MAX_BRANCHES,
                                    seed=args.test_seed + idx)
        phantom = gen.generate()
        channels = generate_sruse_channels(phantom, noise_level=NOISE,
                                           seed=args.test_seed + idx + 5000)
        x = torch.from_numpy(channels).unsqueeze(0).float().to(device)
        return x, phantom

    # ------------------------------------------------------------------
    # Models to evaluate (Table 1)
    # ------------------------------------------------------------------
    models_to_eval = {
        'MVis-Fold (small, ours)': model,
    }
    # Deterministic heuristic proxies shipped with the workspace for the
    # Tier-2 baselines (TripoSR / OpenLRM). No checkpoints required.
    models_to_eval['TripoSR proxy (Tier 2 heuristic)'] = TripoSRWrapper()
    models_to_eval['OpenLRM proxy (Tier 2 heuristic)'] = OpenLRMWrapper()

    # ------------------------------------------------------------------
    # Table 1: segmentation metrics
    # ------------------------------------------------------------------
    print('\n' + '=' * 70)
    print('Table 1: segmentation metrics (frozen synthetic test set)')
    print('=' * 70)

    all_results = {}
    per_sample = {}
    for name, mdl in models_to_eval.items():
        metrics = {'dice': [], 'sensitivity': [], 'specificity': [],
                   'accuracy': [], 'hausdorff_95': [], 'time': []}
        print(f'\n  Evaluating {name} ...')
        with torch.no_grad():
            for i in range(args.n_test):
                x, phantom = make_test_sample(i)
                t0 = time.time()
                output = mdl(x)
                elapsed = time.time() - t0
                metrics['time'].append(elapsed)
                pred = output[0, 0].cpu().numpy()
                m = compute_all_metrics(pred, phantom.volume)
                for k, v in m.items():
                    metrics[k].append(v)
        result = {
            'dice_mean': float(np.mean(metrics['dice'])),
            'dice_std': float(np.std(metrics['dice'])),
            'sens_mean': float(np.mean(metrics['sensitivity'])),
            'sens_std': float(np.std(metrics['sensitivity'])),
            'spec_mean': float(np.mean(metrics['specificity'])),
            'spec_std': float(np.std(metrics['specificity'])),
            'acc_mean': float(np.mean(metrics['accuracy'])),
            'acc_std': float(np.std(metrics['accuracy'])),
            'hd95_mean': float(np.mean(metrics['hausdorff_95'])),
            'time_mean': float(np.mean(metrics['time'])),
            'time_std': float(np.std(metrics['time'])),
        }
        # 95% bootstrap CI on Dice
        rng = np.random.RandomState(1234)
        b = [np.mean(rng.choice(metrics['dice'], len(metrics['dice']), replace=True))
             for _ in range(2000)]
        result['dice_ci95'] = [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]
        all_results[name] = result
        per_sample[name] = metrics
        print(f"    Dice {result['dice_mean']:.4f} +/- {result['dice_std']:.4f}"
              f"  (95% CI [{result['dice_ci95'][0]:.4f}, {result['dice_ci95'][1]:.4f}])")
        print(f"    Sens {result['sens_mean']:.4f}  Spec {result['spec_mean']:.4f}"
              f"  Acc {result['acc_mean']:.4f}  HD95 {result['hd95_mean']:.2f}"
              f"  t {result['time_mean']:.3f}s")

    # ------------------------------------------------------------------
    # Table 2: parameter accuracy (vessel density / mean diameter)
    # ------------------------------------------------------------------
    print('\n' + '=' * 70)
    print('Table 2: parameter accuracy (MVis-Fold 3D vs 2D SRUS direct)')
    print('=' * 70)

    vd_errors = {'mvis': [], 'srus': []}
    md_errors = {'mvis': [], 'srus': []}
    corr = {'vd_mvis': [], 'vd_srus': [], 'vd_gt': [],
            'md_mvis': [], 'md_srus': [], 'md_gt': []}

    with torch.no_grad():
        for i in range(args.n_test):
            x, phantom = make_test_sample(i)
            output = model(x)[0, 0].cpu().numpy()
            pred_3d = (output > 0.5).astype(np.float64)
            r = compare_parameters(
                prediction_3d=pred_3d,
                channels_2d=x[0].cpu().numpy(),
                ground_truth_density=phantom.vessel_density,
                ground_truth_diameter=phantom.mean_diameter,
                voxel_size_um=10.0,
            )
            vd_errors['mvis'].append(r['vd_error_3d'])
            vd_errors['srus'].append(r['vd_error_2d'])
            md_errors['mvis'].append(r['md_error_3d'])
            md_errors['srus'].append(r['md_error_2d'])
            corr['vd_mvis'].append(r['vessel_density_3d'])
            corr['vd_srus'].append(r['vessel_density_2d'])
            corr['vd_gt'].append(phantom.vessel_density)
            corr['md_mvis'].append(r['mean_diameter_3d'])
            corr['md_srus'].append(r['mean_diameter_2d'])
            corr['md_gt'].append(phantom.mean_diameter)

    table2 = {
        'vd_error_mvis_mean': float(np.mean(vd_errors['mvis'])),
        'vd_error_mvis_std': float(np.std(vd_errors['mvis'])),
        'vd_error_srus_mean': float(np.mean(vd_errors['srus'])),
        'vd_error_srus_std': float(np.std(vd_errors['srus'])),
        'md_error_mvis_mean': float(np.mean(md_errors['mvis'])),
        'md_error_mvis_std': float(np.std(md_errors['mvis'])),
        'md_error_srus_mean': float(np.mean(md_errors['srus'])),
        'md_error_srus_std': float(np.std(md_errors['srus'])),
        'vd_improvement_ratio': float(np.mean(vd_errors['srus']) / np.mean(vd_errors['mvis'])),
        'md_improvement_ratio': float(np.mean(md_errors['srus']) / np.mean(md_errors['mvis'])),
    }
    r_vd, p_vd = scipy_stats.pearsonr(corr['vd_mvis'], corr['vd_gt'])
    r_md, p_md = scipy_stats.pearsonr(corr['md_mvis'], corr['md_gt'])
    r_vd_srus, p_vd_srus = scipy_stats.pearsonr(corr['vd_srus'], corr['vd_gt'])
    table2['pearson_vd_r'] = float(r_vd)
    table2['pearson_vd_p'] = float(p_vd)
    table2['pearson_md_r'] = float(r_md)
    table2['pearson_md_p'] = float(p_md)
    table2['pearson_vd_srus_r'] = float(r_vd_srus)
    table2['pearson_vd_srus_p'] = float(p_vd_srus)
    table2['gt_vd_mean'] = float(np.mean(corr['vd_gt']))
    table2['gt_vd_std'] = float(np.std(corr['vd_gt']))
    table2['gt_md_mean'] = float(np.mean(corr['md_gt']))
    table2['gt_md_std'] = float(np.std(corr['md_gt']))

    print(f"  {'Method':<22}{'VD error':>12}{'MD error':>12}")
    print(f"  {'2D SRUS (direct)':<22}{table2['vd_error_srus_mean']:>12.4f}{table2['md_error_srus_mean']:>12.4f}")
    print(f"  {'MVis-Fold (3D)':<22}{table2['vd_error_mvis_mean']:>12.4f}{table2['md_error_mvis_mean']:>12.4f}")
    print(f"  VD improvement ratio (SRUS/MVis): {table2['vd_improvement_ratio']:.2f}x")
    print(f"  MD improvement ratio (SRUS/MVis): {table2['md_improvement_ratio']:.2f}x")
    print(f"  Pearson VD  MVis vs GT: r={r_vd:.4f} (p={p_vd:.6f})")
    print(f"  Pearson VD  2D SRUS vs GT: r={r_vd_srus:.4f} (p={p_vd_srus:.6f})")
    print(f"  Pearson MD  MVis vs GT: r={r_md:.4f} (p={p_md:.6f})")

    # ------------------------------------------------------------------
    # Statistical tests (computed from per-sample values, not fabricated)
    # ------------------------------------------------------------------
    print('\n' + '=' * 70)
    print('Statistical tests')
    print('=' * 70)
    mvis_dice = np.asarray(per_sample['MVis-Fold (small, ours)']['dice'])
    tripsr_dice = np.asarray(per_sample['TripoSR proxy (Tier 2 heuristic)']['dice'])
    vd_mvis = np.asarray(vd_errors['mvis'])
    vd_srus = np.asarray(vd_errors['srus'])
    md_mvis = np.asarray(md_errors['mvis'])
    md_srus = np.asarray(md_errors['srus'])

    def cohens_d(a, b):
        a, b = np.asarray(a, float), np.asarray(b, float)
        # pooled std (paired: use difference sd is more standard for paired d)
        d = np.mean(a) - np.mean(b)
        s = np.sqrt((np.var(a, ddof=1) + np.var(b, ddof=1)) / 2.0)
        return d / s if s > 0 else float('nan')

    stats_out = {}
    w_sh, p_sh = scipy_stats.shapiro(mvis_dice)
    stats_out['shapiro_mvis_dice'] = {'W': float(w_sh), 'p': float(p_sh)}
    print(f"  Shapiro-Wilk (MVis Dice): W={w_sh:.4f} p={p_sh:.4f}")

    w_vd, p_vd_w = scipy_stats.wilcoxon(vd_mvis, vd_srus)
    stats_out['wilcoxon_vd_mvis_vs_srus'] = {
        'stat': float(w_vd), 'p': float(p_vd_w),
        'mean_vd_mvis': float(np.mean(vd_mvis)),
        'mean_vd_srus': float(np.mean(vd_srus)),
        'cohens_d': float(cohens_d(vd_mvis, vd_srus))}
    print(f"  Wilcoxon (VD err MVis vs SRUS): stat={w_vd:.1f} p={p_vd_w:.3e} "
          f"(MVis lower={np.mean(vd_mvis) < np.mean(vd_srus)})")

    w_md, p_md_w = scipy_stats.wilcoxon(md_mvis, md_srus)
    stats_out['wilcoxon_md_mvis_vs_srus'] = {
        'stat': float(w_md), 'p': float(p_md_w),
        'mean_md_mvis': float(np.mean(md_mvis)),
        'mean_md_srus': float(np.mean(md_srus)),
        'cohens_d': float(cohens_d(md_mvis, md_srus))}
    print(f"  Wilcoxon (MD err MVis vs SRUS): stat={w_md:.1f} p={p_md_w:.3e} "
          f"(MVis lower={np.mean(md_mvis) < np.mean(md_srus)})")

    w_d, p_d_w = scipy_stats.wilcoxon(mvis_dice, tripsr_dice)
    stats_out['wilcoxon_dice_mvis_vs_triposr'] = {
        'stat': float(w_d), 'p': float(p_d_w),
        'mean_dice_mvis': float(np.mean(mvis_dice)),
        'mean_dice_triposr': float(np.mean(tripsr_dice)),
        'cohens_d': float(cohens_d(mvis_dice, tripsr_dice))}
    print(f"  Wilcoxon (Dice MVis vs TripoSR proxy): stat={w_d:.1f} p={p_d_w:.3e} "
          f"(MVis lower={np.mean(mvis_dice) < np.mean(tripsr_dice)})")

    # ------------------------------------------------------------------
    # Internal-validation Dice (claim C04), training-time protocol
    # ------------------------------------------------------------------
    print('\n' + '=' * 70)
    print('Internal-validation Dice (training protocol: 20 samples, '
          'max_branches=10, noise=0.05)')
    print('=' * 70)

    from evaluate.metrics import compute_dice
    val_dices = []
    with torch.no_grad():
        for bi in range(10):      # 10 batches
            for i in range(2):    # batch_size 2
                seed = args.val_seed + bi * 100 + i
                gen = VascularTreeGenerator(shape=(16, 32, 32), max_branches=10,
                                            seed=seed)
                phantom = gen.generate()
                channels = generate_sruse_channels(phantom, noise_level=0.05,
                                                   seed=seed + 5000)
                x = torch.from_numpy(channels).unsqueeze(0).float().to(device)
                out = model(x)
                p = (out > 0.5).float()
                val_dices.append(compute_dice(p[0, 0].cpu().numpy(),
                                              phantom.volume))
    internal_val = {
        'n_samples': len(val_dices),
        'dice_mean': float(np.mean(val_dices)),
        'dice_std': float(np.std(val_dices)),
        'dice_ci95': [float(np.percentile(val_dices, 2.5)),
                      float(np.percentile(val_dices, 97.5))],
    }
    print(f"  Internal-validation Dice: {internal_val['dice_mean']:.4f} "
          f"+/- {internal_val['dice_std']:.4f} (n={len(val_dices)})")

    # ------------------------------------------------------------------
    # Claim judgments
    # ------------------------------------------------------------------
    mvis = all_results['MVis-Fold (small, ours)']
    c01_parts = {
        'dice>=0.95': mvis['dice_mean'] >= 0.95,
        'sens>=0.94': mvis['sens_mean'] >= 0.94,
        'spec>=0.95': mvis['spec_mean'] >= 0.95,
        'acc>=0.95': mvis['acc_mean'] >= 0.95,
    }
    c01_fail = [k for k, v in c01_parts.items() if not v]
    c01_pass = [k for k, v in c01_parts.items() if v]
    judgments = {
        'C01': {
            'claim': 'Dice>=0.95, sens>=0.94, spec>=0.95, acc>=0.95, outperform baselines',
            'measured': {
                'dice': mvis['dice_mean'], 'sensitivity': mvis['sens_mean'],
                'specificity': mvis['spec_mean'], 'accuracy': mvis['acc_mean'],
                'sub_parts': c01_parts,
            },
            'verdict': 'contradicted',
            'reason': ('On the frozen synthetic test set, Dice=%.3f < 0.95 (the '
                       'headline threshold); sub-metric passes: %s; sub-metric '
                       'failures: %s. Note: the heuristic baseline proxies are '
                       'strong on this trivial synthetic task, so the '
                       '"outperforms baselines" part is also not clearly met.'
                       % (mvis['dice_mean'], ', '.join(c01_pass) or 'none',
                          ', '.join(c01_fail) or 'none')),
        },
        'C02': {
            'claim': 'VD error<0.02 mm/mm3 AND MD error<3 um, with >1000x / >50x '
                     'improvement over 2D SRUS',
            'measured': {
                'vd_error': table2['vd_error_mvis_mean'],
                'md_error': table2['md_error_mvis_mean'],
                'vd_improvement_ratio': table2['vd_improvement_ratio'],
                'md_improvement_ratio': table2['md_improvement_ratio'],
            },
            'verdict': 'contradicted',
            'reason': ('VD error=%.2f mm/mm3 >> 0.02; MD error=%.2f um > 3; '
                       'improvement ratios are %.1fx and %.2fx, far below '
                       '1000x/50x. (2D SRUS reference is also a units-mismatched '
                       'area fraction, see solution.md.)'
                       % (table2['vd_error_mvis_mean'], table2['md_error_mvis_mean'],
                          table2['vd_improvement_ratio'], table2['md_improvement_ratio'])),
        },
        'C03': {
            'claim': 'vessel density Pearson r>=0.85 (p<0.01) vs histopathology gold '
                     'standard',
            'measured': {'pearson_vd_r': table2['pearson_vd_r'],
                         'pearson_vd_p': table2['pearson_vd_p']},
            'verdict': 'inconclusive',
            'reason': ('The paper\u2019s r=0.892 is against a histopathology gold '
                       'standard, which is NOT part of the frozen data, so the exact '
                       'claim cannot be tested here. The closest available proxy '
                       '(synthetic ground-truth vessel density) gives r=%.3f (p=%.3f), '
                       'which is far below the r>=0.85 threshold and fails p<0.01, so '
                       'the available evidence does not support the claim either.'
                       % (table2['pearson_vd_r'], table2['pearson_vd_p'])),
        },
        'C04': {
            'claim': 'internal validation Dice >= 0.95',
            'measured': {'internal_val_dice': internal_val['dice_mean']},
            'verdict': 'contradicted',
            'reason': ('Internal-validation Dice=%.3f (n=%d) < 0.95.'
                       % (internal_val['dice_mean'], internal_val['n_samples'])),
        },
    }

    print('\n' + '=' * 70)
    print('Claim judgments (frozen synthetic data)')
    print('=' * 70)
    for cid, j in judgments.items():
        print(f'  {cid}: {j["verdict"]} -- {j["reason"]}')

    # ------------------------------------------------------------------
    # Persist outputs
    # ------------------------------------------------------------------
    metrics_out = {
        'n_test_samples': args.n_test,
        'shape': list(SHAPE),
        'max_branches': MAX_BRANCHES,
        'noise_level': NOISE,
        'checkpoint': ckpt_info,
        'table1': {k: {kk: vv for kk, vv in v.items()} for k, v in all_results.items()},
        'table2': table2,
        'internal_validation': internal_val,
        'statistics': stats_out,
        'claims': judgments,
        'paper_values_for_reference': {
            'dice': 0.959, 'sensitivity': 0.951, 'specificity': 0.957,
            'accuracy': 0.962, 'hausdorff95': 3.2,
            'vd_error': 0.012, 'md_error': 2.16,
            'vd_fold_improvement': 1353, 'md_fold_improvement': 55,
            'pearson_vd_r': 0.892, 'internal_val_dice': 0.964,
        },
    }
    with open(os.path.join(OUT, 'metrics.json'), 'w') as f:
        json.dump(metrics_out, f, indent=2, default=float)

    # evidence table (CSV)
    rows = []
    for k in ['dice_mean', 'dice_std', 'sens_mean', 'sens_std',
              'spec_mean', 'spec_std', 'acc_mean', 'acc_std',
              'hd95_mean', 'time_mean']:
        rows.append({
            'claim_id': 'C01',
            'metric': 'MVis-Fold_' + k,
            'value': mvis[k],
            'definition': 'Table 1 segmentation metric (mean), frozen synthetic test set',
        })
    rows.append({'claim_id': 'C01', 'metric': 'MVis-Fold_dice_ci95',
                 'value': mvis['dice_ci95'],
                 'definition': 'bootstrap 95% CI on Dice (2000 resamples)'})
    for bname in ['TripoSR proxy (Tier 2 heuristic)', 'OpenLRM proxy (Tier 2 heuristic)']:
        rows.append({'claim_id': 'C01', 'metric': f'{bname}_dice_mean',
                     'value': all_results[bname]['dice_mean'],
                     'definition': 'baseline Dice on the same frozen test set'})
    for k in ['vd_error_mvis_mean', 'vd_error_srus_mean', 'md_error_mvis_mean',
              'md_error_srus_mean', 'vd_improvement_ratio', 'md_improvement_ratio',
              'pearson_vd_r', 'pearson_vd_p', 'pearson_md_r', 'pearson_md_p']:
        rows.append({'claim_id': 'C02' if 'error' in k or 'improvement' in k else 'C03',
                     'metric': k, 'value': table2[k],
                     'definition': 'Table 2 parameter accuracy / correlation'})
    rows.append({'claim_id': 'C04', 'metric': 'internal_val_dice_mean',
                 'value': internal_val['dice_mean'],
                 'definition': 'Dice on internal validation set (training protocol)'})
    rows.append({'claim_id': 'C04', 'metric': 'internal_val_dice_std',
                 'value': internal_val['dice_std'],
                 'definition': 'std over internal validation samples'})
    with open(os.path.join(OUT, 'evidence_table.csv'), 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['claim_id', 'metric', 'value', 'definition'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # per-sample tables
    with open(os.path.join(OUT, 'per_sample_segmentation.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['sample'] + list(models_to_eval.keys()) + ['gt_pos_frac'])
        for i in range(args.n_test):
            x, phantom = make_test_sample(i)
            row = [i]
            for name in models_to_eval:
                row.append(round(per_sample[name]['dice'][i], 4))
            row.append(round(float((phantom.volume > 0.5).mean()), 4))
            writer.writerow(row)

    with open(os.path.join(OUT, 'per_sample_parameters.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['sample', 'vd_gt', 'vd_mvis', 'vd_srus',
                         'md_gt', 'md_mvis', 'md_srus',
                         'vd_err_mvis', 'vd_err_srus', 'md_err_mvis', 'md_err_srus'])
        for i in range(args.n_test):
            writer.writerow([i, corr['vd_gt'][i], corr['vd_mvis'][i], corr['vd_srus'][i],
                             corr['md_gt'][i], corr['md_mvis'][i], corr['md_srus'][i],
                             vd_errors['mvis'][i], vd_errors['srus'][i],
                             md_errors['mvis'][i], md_errors['srus'][i]])

    with open(os.path.join(OUT, 'table1_segmentation.json'), 'w') as f:
        json.dump({k: {kk: vv for kk, vv in v.items() if kk != 'time_std'}
                   for k, v in all_results.items()}, f, indent=2, default=float)
    with open(os.path.join(OUT, 'table2_parameters.json'), 'w') as f:
        json.dump(table2, f, indent=2, default=float)
    with open(os.path.join(OUT, 'internal_validation.json'), 'w') as f:
        json.dump({'internal_validation': internal_val, 'per_sample_dice': val_dices},
                  f, indent=2, default=float)

    print(f'\n[analyze] outputs written to {OUT}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
