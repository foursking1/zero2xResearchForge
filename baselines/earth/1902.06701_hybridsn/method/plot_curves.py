"""Generate training-curve figure from whichever HybridSN history npz exists.

Preference: results/checkpoints/history_hybridsn_seed0.npz (100-epoch curve),
else results/checkpoints/history_hybridsn_r30_seed0.npz (60-epoch curve, from the
ratio sweep). Output: evidence/training_curves.png.
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RES = os.path.join(ROOT, 'results', 'checkpoints')
EVID = os.path.join(ROOT, 'evidence')
os.makedirs(EVID, exist_ok=True)

path = os.path.join(RES, 'history_hybridsn_seed0.npz')
label = 'HybridSN seed 0, 100 epochs'
if not os.path.exists(path):
    path = os.path.join(RES, 'history_hybridsn_r30_seed0.npz')
    label = 'HybridSN seed 0, 60 epochs (ratio sweep, 30%)'
if not os.path.exists(path):
    print('no history found; skipping training-curve figure'); sys.exit(0)

h = np.load(path)
fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
ax[0].plot(h['train_loss'], color='tab:blue')
ax[0].set_title('Training loss'); ax[0].set_xlabel('epoch'); ax[0].grid(alpha=0.3)
ax[1].plot(h['test_oa'], color='tab:green')
ax[1].set_title('Test OA'); ax[1].set_xlabel('epoch'); ax[1].set_ylim(0.0, 1.0)
ax[1].grid(alpha=0.3)
fig.suptitle(label, fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(EVID, 'training_curves.png'), dpi=120)
print('wrote', os.path.join(EVID, 'training_curves.png'), '|', label,
      '| final OA=%.4f' % h['test_oa'][-1])