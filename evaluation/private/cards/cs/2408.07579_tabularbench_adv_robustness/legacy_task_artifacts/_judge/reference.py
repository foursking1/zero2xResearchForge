import numpy as np, pandas as pd, torch, torch.nn as nn, json, time
from sklearn.model_selection import train_test_split

SEED = 0
torch.manual_seed(SEED); np.random.seed(SEED)
EVAL_EPS = 0.25
PGD_STEPS = 40
PGD_ALPHA = EVAL_EPS / 4.0
AT_EPS = 0.1
AT_STEPS = 1
AT_ALPHA = 0.1
EPOCHS = 12
BATCH = 256
LR = 1e-3
MODELS = ['mlp64', 'mlp128_64', 'mlp256_128_64', 'mlp128_64_drop']

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
print('train/val/test:', len(i_train), len(i_val), len(i_test), 'pos rate:', round(y.mean(), 3), flush=True)

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
    if name == 'mlp128_64': return MLP([128, 64])
    if name == 'mlp256_128_64': return MLP([256, 128, 64])
    if name == 'mlp128_64_drop': return MLP([128, 64], dropout=0.3)
    raise ValueError(name)

Xt_full = to_t(Xtr); yt_full = to_t(ytr).float()

def train_model(name, at=False):
    model = make_model(name)
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
    lossf = nn.BCEWithLogitsLoss()
    n = len(Xtr)
    for ep in range(EPOCHS):
        perm = torch.randperm(n)
        for b in range(0, n, BATCH):
            idx = perm[b:b+BATCH]
            xb, yb = Xt_full[idx], yt_full[idx]
            if at:
                xadv = xb.clone().detach()
                for _ in range(AT_STEPS):
                    xadv.requires_grad_(True)
                    loss = lossf(model(xadv), yb)
                    grad = torch.autograd.grad(loss, xadv)[0]
                    norm = grad.norm(dim=1, keepdim=True).clamp_min(1e-12)
                    xadv = (xadv + AT_ALPHA * grad / norm).detach()
                    delta = xadv - xb
                    dn = delta.norm(dim=1, keepdim=True).clamp_min(1e-12)
                    xadv = xb + delta * (torch.clamp(dn, max=AT_EPS) / dn)
                    xadv = torch.clamp(xadv, 0.0, 1.0)
                opt.zero_grad(); loss = lossf(model(xadv), yb); loss.backward(); opt.step()
            else:
                opt.zero_grad(); loss = lossf(model(xb), yb); loss.backward(); opt.step()
    return model

def evaluate(model, Xe, ye, attack=True):
    model.eval()
    Xt = to_t(Xe); yt = to_t(ye).float()
    with torch.no_grad():
        clean = ((torch.sigmoid(model(Xt)) > 0.5).float() == yt).float().mean().item()
    if not attack:
        return clean, None
    xadv = Xt.clone()
    for _ in range(PGD_STEPS):
        xadv.requires_grad_(True)
        loss = nn.functional.binary_cross_entropy_with_logits(model(xadv), yt)
        grad = torch.autograd.grad(loss, xadv)[0]
        norm = grad.norm(dim=1, keepdim=True).clamp_min(1e-12)
        xadv = (xadv + PGD_ALPHA * grad / norm).detach()
        delta = xadv - Xt
        dn = delta.norm(dim=1, keepdim=True).clamp_min(1e-12)
        xadv = Xt + delta * (torch.clamp(dn, max=EVAL_EPS) / dn)
        xadv = torch.clamp(xadv, 0.0, 1.0)
    with torch.no_grad():
        robust = ((torch.sigmoid(model(xadv)) > 0.5).float() == yt).float().mean().item()
    return clean, robust

res = {}
t0 = time.time()
for name in MODELS:
    m_std = train_model(name, at=False)
    c_s, r_s = evaluate(m_std, Xte, yte)
    m_at = train_model(name, at=True)
    c_a, r_a = evaluate(m_at, Xte, yte)
    res[name] = {'std': {'clean': c_s, 'robust': r_s}, 'at': {'clean': c_a, 'robust': r_a}}
    print(name, res[name], 'elapsed', round(time.time()-t0, 1), flush=True)

def pearson(a, b): return float(np.corrcoef(a, b)[0, 1])
std_clean = [res[k]['std']['clean'] for k in res]
std_rob = [res[k]['std']['robust'] for k in res]
at_clean = [res[k]['at']['clean'] for k in res]
at_rob = [res[k]['at']['robust'] for k in res]
summary = {
    'n_train': int(len(i_train)), 'n_val': int(len(i_val)), 'n_test': int(len(i_test)),
    'eval_eps': EVAL_EPS, 'at_eps': AT_EPS,
    'std': {'clean_range': [min(std_clean), max(std_clean)], 'robust_range': [min(std_rob), max(std_rob)],
            'clean_mean': float(np.mean(std_clean)), 'robust_mean': float(np.mean(std_rob)),
            'clean_spread': float(max(std_clean)-min(std_clean)), 'robust_spread': float(max(std_rob)-min(std_rob)),
            'pearson_id_robust': pearson(std_clean, std_rob)},
    'at': {'clean_range': [min(at_clean), max(at_clean)], 'robust_range': [min(at_rob), max(at_rob)],
           'clean_mean': float(np.mean(at_clean)), 'robust_mean': float(np.mean(at_rob)),
           'clean_spread': float(max(at_clean)-min(at_clean)), 'robust_spread': float(max(at_rob)-min(at_rob)),
           'pearson_id_robust': pearson(at_clean, at_rob),
           'robust_improvement_mean': float(np.mean(at_rob)-np.mean(std_rob))},
    'per_model': res,
}
with open('_judge/reference_results.json', 'w') as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
