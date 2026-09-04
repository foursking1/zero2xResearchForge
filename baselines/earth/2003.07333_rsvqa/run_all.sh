#!/usr/bin/env bash
# Reproduce the full pipeline end-to-end:
#   1) extract frozen CNN/ViT features (cached in results/_cache)
#   2) train the champion VQA model (CNN-LSTM fusion) on the image-level 80/20 split
#   3) evaluate + random-image ablation, write evidence_table.csv & metrics.json
#   4) produce figures and baseline analysis
#
# Offline: no network access required (all pretrained backbones are cached locally).
set -euo pipefail
cd "$(dirname "$0")"

export OMP_NUM_THREADS=8

echo "==> [1/4] feature extraction (cached)"
python3 -c "
from code.dataset import load_data, decode_image
from code.features import extract_resnet18_features, extract_resnet18_conv, extract_vit_features
import numpy as np, os
df = load_data()
uids = sorted(df['imgid'].unique())
im_by_id = {r['imgid']: decode_image(r['image']) for _, r in df.iterrows()}
ims = [im_by_id[i] for i in uids]
os.makedirs('results/_cache', exist_ok=True)
if not os.path.exists('results/_cache/resnet18_conv7.npy'):
    np.save('results/_cache/resnet18_conv7.npy', extract_resnet18_features(ims, 'cpu', False))
if not os.path.exists('results/_cache/resnet18_conv14.npy'):
    np.save('results/_cache/resnet18_conv14.npy', extract_resnet18_conv(ims, 'cpu', stage=3))
if not os.path.exists('results/_cache/vit_pool768.npy'):
    np.save('results/_cache/vit_pool768.npy', extract_vit_features(ims, 'cpu'))
print('features ready')
"

echo "==> [2/4] train champion (concat backbone, count-regression head, 20 epochs)"
python3 -m code.run --device cpu --backbone concat --count-head regress \
        --epochs 20 --final --seed 0 --save-scores

echo "==> [2b/4] finalize evidence/metrics in rubric format"
python3 -m code.finalize

echo "==> [3/4] analysis & figures"
python3 code/analysis.py

echo "==> [4/4] done. artifacts in results/: evidence_table.csv, metrics.json, figures"