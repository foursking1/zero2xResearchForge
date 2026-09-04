import numpy as np, pandas as pd, torch, torch.nn as nn, json, time
from sklearn.model_selection import train_test_split

SEED = 0
torch.manual_seed(SEED); np.random.seed(SEED)
EPOCHS = 10
BATCH = 256
LR = 1e-3
MODELS = ['mlp64', 'mlp256_128_64']

df = pd.read_csv('data/url.csv')
feat_cols = [c for c in df.columns if c != 'is_phishing']
y = df['is_phishing'].to_numpy()
X = df[feat_cols].to_numpy(dtype=float)
i = np.arange(len(y))
i_train, i_test = train_test_split(i, random_state=42, shuffle=True, stratify=y[i], test_size=0.2)
i_train, i_val = train_test_split(i_train, random_state=42, shuffle=True, stratify=y[i_train], test_size=0.2)
lo = X[i_train].min(0); hi = X[i_train].max(0)
span = hi - lo; span[span == 0] = 1.0
Xm = np.clip((X - lo) / span, 0.0, 1.0)
Xtr, ytr = Xm[i_train], y[i_train]
Xte, yte = Xm[i_test], y[i_test]

def to_t(x): return torch.tensor(x, dtype=torch.float32)
class MLP(nn.Module):
    def __init__(self, sizes, dropout=0.0):
        super().__init__()
        layers = []; prev = len(feat_cols)
        for h in sizes:
            layers += [nn.Linear(prev, h), nn.ReLU()]
            if dropout > 0: layers.append(nn.Dropout(dropout))
            prev = h
        layers.append(nn.Linear(prev, 1))
        self.net = nn.Sequential(*layers)
    def forward(self, x): return self.net(x).squeeze(-1)
def make_model(name):
    if name == 'mlp64': return MLP([64])
    if name == 'mlp256_128_64': return MLP([256, 128, 64])
    raise ValueError

Xt_full = to_t(Xtr); yt_full = to_t(ytr).float()

def train_model(name, at_eps, at_steps, at_alpha):
    model = make_model(name)
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
    lossf = nn.BCEWithLogitsLoss()
    n = len(Xtr)
    for ep in range(EPOCHS):
        perm = torch.randperm(n)
        for b in range(0, n, BATCH):
            idx = perm[b:b+BATCH]
            xb, yb = Xt_full[idx], yt_full[idx]
            if at_eps > 0:
                xadv = xb.clone().detach()
                for _ in range(at_steps):
                    xadv.requires_grad_(True)
                    loss = lossf(model(xadv), yb)
                    grad = torch.autograd.grad(loss, xadv)[0]
                    norm = grad.norm(dim=1, keepdim=True).clamp_min(1e-12)
                    xadv = (xadv + at_alpha * grad / norm).detach()
                    delta = xadv - xb
                    dn = delta.norm(dim=1, keepdim=True).clamp_min(1e-12)
                    xadv = xb + delta * (torch.clamp(dn, max=at_eps) / dn)
                    xadv = torch.clamp(xadv, 0.0, 1.0)
                opt.zero_grad(); loss = lossf(model(xadv), yb); loss.backward(); opt.step()
            else:
                opt.zero_grad(); loss = lossf(model(xb), yb); loss.backward(); opt.step()
    return model

def evaluate(model, Xe, ye, eps, steps=40, alpha=None):
    model.eval()
    Xt = to_t(Xe); yt = to_t(ye).float()
    with torch.no_grad():
        clean = ((torch.sigmoid(model(Xt)) > 0.5).float() == yt).float().mean().item()
    if alpha is None: alpha = eps / 4.0
    xadv = Xt.clone()
    for _ in range(steps):
        xadv.requires_grad_(True)
        loss = nn.functional.binary_cross_entropy_with_logits(model(xadv), yt)
        grad = torch.autograd.grad(loss, xadv)[0]
        norm = grad.norm(dim=1, keepdim=True).clamp_min(1e-12)
        xadv = (xadv + alpha * grad / norm).detach()
        delta = xadv - Xt
        dn = delta.norm(dim=1, keepdim=True).clamp_min(1e-12)
        xadv = Xt + delta * (torch.clamp(dn, max=eps) / dn)
        xadv = torch.clamp(xadv, 0.0, 1.0)
    with torch.no_grad():
        robust = ((torch.sigmoid(model(xadv)) > 0.5).float() == yt).float().mean().item()
    return clean, robust

configs = [('std', 0.0, 0, 0.0), ('at01_1', 0.1, 1, 0.1), ('at02_2', 0.2, 2, 0.1), ('at03_3', 0.3, 3, 0.1)]
results = {}
for name in MODELS:
    results[name] = {}
    for cfg, at_eps, at_steps, at_alpha in configs:
        m = train_model(name, at_eps, at_steps, at_alpha)
        row = {}
        for eval_eps in [0.25, 0.5]:
            c, r = evaluate(m, Xte, yte, eval_eps)
            row['e' + str(eval_eps)] = {'clean': c, 'robust': r}
        results[name][cfg] = row
        print(name, cfg, row, flush=True)
print(json.dumps(results, indent=2))
