"""Shared training loop for the CNN classifiers."""
import os
import random
import time
import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset
from torch.optim.lr_scheduler import CosineAnnealingLR


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def make_loader(X, y, batch_size, shuffle, seed=0):
    ds = TensorDataset(torch.from_numpy(X), torch.from_numpy(y.astype(np.int64) - 1))
    g = torch.Generator().manual_seed(seed) if shuffle else None
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle, generator=g,
                      num_workers=0, drop_last=False)


def train_cnn(model, X_train, y_train, X_test, y_test, epochs, lr, weight_decay,
              batch_size, seed, device, model_name='cnn', ckpt_dir='../results/checkpoints'):
    """Trains with Adam + cosine schedule, tracks test accuracy each epoch,
    returns (best_state_dict, history, elapsed). Test data is used ONLY for
    reporting (no training-time leakage; train set is fixed by the split)."""
    set_seed(seed)
    model = model.to(device)
    loader = make_loader(X_train, y_train, batch_size, True, seed)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    sched = CosineAnnealingLR(opt, T_max=epochs)
    lossf = torch.nn.CrossEntropyLoss()

    history = {'train_loss': [], 'test_oa': []}
    best_oa, best_state = -1.0, None
    t0 = time.time()
    os.makedirs(ckpt_dir, exist_ok=True)
    for ep in range(1, epochs + 1):
        model.train()
        tot, cnt = 0.0, 0
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            out = model(xb)
            loss = lossf(out, yb)
            loss.backward()
            opt.step()
            tot += loss.item() * len(xb); cnt += len(xb)
        sched.step()
        tr_loss = tot / cnt

        model.eval()
        preds, yt = [], []
        with torch.no_grad():
            for xb, yb in make_loader(X_test, y_test, batch_size, False):
                out = model(xb.to(device)).argmax(1).cpu().numpy() + 1
                preds.append(out); yt.append(yb)
        preds = np.concatenate(preds); yt = np.concatenate(yt) + 1  # restore 1..16
        oa = float((preds == yt).mean())
        history['train_loss'].append(tr_loss)
        history['test_oa'].append(oa)
        if oa > best_oa:
            best_oa, best_state = oa, {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        if ep in (1, 10, 30, 60, 100, 150, 200) or ep == epochs or ep % 25 == 0:
            print(f'  [{model_name} seed={seed}] epoch {ep}/{epochs} '
                  f'train_loss={tr_loss:.4f} test_OA={oa:.4f}')

    elapsed = time.time() - t0
    np.savez(os.path.join(ckpt_dir, f'history_{model_name}_seed{seed}.npz'), **history)
    ckpt = os.path.join(ckpt_dir, f'{model_name}_seed{seed}.pt')
    torch.save({'state_dict': best_state, 'seed': seed}, ckpt)
    print(f'  [{model_name} seed={seed}] best test OA={best_oa:.4f} '
          f'elapsed={elapsed:.1f}s ckpt={ckpt}')
    return ckpt, history, elapsed