"""Quick diagnostics: gradient flow / logit scale / loss curve on GPU."""
import os, sys
import numpy as np
import torch
import torch.nn as nn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import N_PCA_BANDS, DATA_DIR
from models import HybridSN, CNN2D
from data_utils import preprocess
from train_utils import set_seed

device = 'cuda'
X_train, y_train, X_test, y_test, meta, _ = preprocess(DATA_DIR)
Xt = torch.from_numpy(X_train[:256]).to(device)
yt = torch.from_numpy(y_train[:256].astype(np.int64) - 1).to(device)


def run(name, model, lr, steps=40, bs=64):
    set_seed(0)
    model = model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    lossf = torch.nn.CrossEntropyLoss()
    losses, gnorms, logit_max = [], [], []
    for i in range(steps):
        si = (i * bs) % (len(Xt) - bs)
        xb, yb = Xt[si:si + bs], yt[si:si + bs]
        opt.zero_grad()
        out = model(xb)
        loss = lossf(out, yb)
        loss.backward()
        g = torch.cat([p.grad.reshape(-1) for p in model.parameters() if p.grad is not None])
        gnorms.append(g.norm().item())
        opt.step()
        losses.append(loss.item())
        logit_max.append(out.abs().max().item())
    print(f'{name}: loss_1={losses[0]:.3f} loss_{steps}={losses[-1]:.3f} '
          f'grad_norm(last)={gnorms[-1]:.1f} logit_max={max(logit_max):.1f} '
          f'loss@10={losses[10]:.3f}')
    del model, opt
    torch.cuda.empty_cache()


run('HybridSN lr5e-4', HybridSN(), 5e-4)
run('HybridSN lr1e-3', HybridSN(), 1e-3)
run('CNN2D lr5e-4', CNN2D(), 5e-4)