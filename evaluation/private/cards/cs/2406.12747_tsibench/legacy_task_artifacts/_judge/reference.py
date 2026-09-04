import numpy as np, pandas as pd, json
WINDOW = 48
RATE = 0.1
SEED = 42
feat_cols = ['HUFL','HULL','MUFL','MULL','LUFL','LULL','OT']
df = pd.read_csv('ETT-h1.csv')
df['date'] = pd.to_datetime(df['date'])
tr = (df['date'] < pd.Timestamp('2017-09-01')).to_numpy()
va = ((df['date'] >= pd.Timestamp('2017-09-01')) & (df['date'] < pd.Timestamp('2018-02-01'))).to_numpy()
te = (df['date'] >= pd.Timestamp('2018-02-01')).to_numpy()
X = df[feat_cols].to_numpy(dtype=float)
mu = X[tr].mean(axis=0)
sd = X[tr].std(axis=0)
Z = (X - mu) / sd
def count_windows(idx):
    return int(len(np.where(idx)[0]) // WINDOW)
n_tr, n_va, n_te = count_windows(tr), count_windows(va), count_windows(te)
def windows(arr, start_idx, n_win):
    return np.stack([arr[start_idx + i*WINDOW : start_idx + (i+1)*WINDOW] for i in range(n_win)])
tr_w = windows(Z, 0, n_tr)
va_w = windows(Z, n_tr*WINDOW, n_va)
te_w = windows(Z, (n_tr+n_va)*WINDOW, n_te)
rng = np.random.default_rng(SEED)
masks = []
for n_win in (n_tr, n_va, n_te):
    ms = np.stack([rng.random((WINDOW, len(feat_cols))) < RATE for _ in range(n_win)])
    masks.append(ms)
M_tr, M_va, M_te = masks
def mae(imp, truth, mask):
    return float(np.abs(imp[mask]-truth[mask]).mean())
def mse(imp, truth, mask):
    return float(((imp[mask]-truth[mask])**2).mean())
def linear_impute(Win, M):
    out = Win.copy()
    for w in range(Win.shape[0]):
        for f in range(Win.shape[2]):
            col = out[w, :, f].copy()
            col[M[w, :, f]] = np.nan
            out[w, :, f] = pd.Series(col).interpolate(method='linear', limit_direction='both').to_numpy()
    return out
def locf_impute(Win, M):
    out = Win.copy()
    for w in range(Win.shape[0]):
        for f in range(Win.shape[2]):
            col = out[w, :, f].copy()
            col[M[w, :, f]] = np.nan
            out[w, :, f] = pd.Series(col).ffill().bfill().to_numpy()
    return out
train_obs = Z[:n_tr*WINDOW]
fmean = train_obs.mean(axis=0)
fmed = np.median(train_obs, axis=0)
def const_impute(Win, M, val):
    out = Win.copy()
    for w in range(Win.shape[0]):
        for f in range(Win.shape[2]):
            out[w, M[w, :, f], f] = val[f]
    return out
res = {}
for name, fn in [('Linear', linear_impute), ('LOCF', locf_impute), ('Mean', const_impute)]:
    if name == 'Mean':
        imp = const_impute(te_w, M_te, fmean)
    else:
        imp = fn(te_w, M_te)
    res[name] = {'mae': mae(imp, te_w, M_te), 'mse': mse(imp, te_w, M_te)}
imp = const_impute(te_w, M_te, fmed)
res['Median'] = {'mae': mae(imp, te_w, M_te), 'mse': mse(imp, te_w, M_te)}
out = {'test': res, 'n_test_windows': n_te, 'n_test_masked': int(M_te.sum()), 'windows': {'train': n_tr, 'val': n_va, 'test': n_te}, 'train_mean': fmean.tolist(), 'train_std': sd.tolist()}
print(json.dumps(out, indent=2))
