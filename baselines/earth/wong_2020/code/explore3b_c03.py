"""C03: build 14C vs model NPP matched dataset and find the 3 subarctic climax stations."""
import pandas as pd
import numpy as np

ROOT = r'E:\scisolvebench-data\asset-data\datasets-v1\v1\wong_2020\real_data_candidates\naames_observation_subset_v1'
F = lambda p: ROOT + p

def ols(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    n = len(x)
    if n < 3:
        return dict(n=n)
    X = np.vstack([x, np.ones_like(x)]).T
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    slope, inter = beta
    yhat = slope * x + inter
    ss_res = np.sum((y - yhat) ** 2); ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot
    rmse = np.sqrt(ss_res / n)
    return dict(n=n, slope=slope, inter=inter, r2=r2, rmse=rmse)

npp = pd.read_csv(F(r'\directories\P12_NPP\npp_profiles.csv'))
r14 = pd.read_csv(F(r'\files\npp_14c_all.csv'))

# Normalize
npp['date'] = npp['date'].astype(str)
npp['station'] = npp['station'].astype(str)
r14['dstr'] = r14['date'].astype(str)
r14['dstr'] = r14['dstr'].apply(lambda d: f'{d[:4]}-{d[4:6]}-{d[6:8]}')
r14['station'] = r14['station'].astype(str)

# station mapping for 14C -> npp_profiles
def map_st(cr, st):
    if cr == 'NAAMES2' and st in ('4a', '4b', '4c'):
        return '4'
    if cr == 'NAAMES3' and st == 'unknown':
        return '6'
    return st

r14['pstation'] = [map_st(c, s) for c, s in zip(r14['cruise'], r14['station'])]

# For each 14C row, find model NPP at nearest z from npp_profiles for (cruise, pstation, dstr)
def nearest_npp(cr, st, date, depth):
    sub = npp[(npp['cruise'] == cr) & (npp['station'] == st) & (npp['date'] == date)]
    if len(sub) == 0:
        return np.nan, np.nan, np.nan, 0
    z = sub['z'].to_numpy(float)
    i = np.argmin(np.abs(z - depth))
    return sub['NPP_z'].iloc[i], z[i], sub['C_phyto_mod'].iloc[i], len(sub)

res = []
for _, row in r14.iterrows():
    mnpp, mz, mc, nz = nearest_npp(row['cruise'], row['pstation'], row['dstr'], row['depth'])
    res.append(dict(cruise=row['cruise'], station=row['station'], pstation=row['pstation'],
                    date=row['dstr'], depth=row['depth'], lightlevel=row['lightlevel'],
                    npp14=row['NPP_14C'], npp_model=mnpp, model_z=mz, n_zprof=nz))
M = pd.DataFrame(res)
M['npp14'] = pd.to_numeric(M['npp14'], errors='coerce')

print('Total 14C rows:', len(M))
print('Matched to model (model_z finite):', np.isfinite(M['npp_model']).sum())
print('Both finite:', (np.isfinite(M['npp14']) & np.isfinite(M['npp_model'])).sum())

mm = M[np.isfinite(M['npp14']) & np.isfinite(M['npp_model'])].copy()
print('\nRatio model/14C by cruise+station (mean):')
mm['ratio'] = mm['npp_model'] / mm['npp14'].replace(0, np.nan)
agg = mm.groupby(['cruise', 'station']).agg(n=('npp14', 'size'), ratio=('ratio', 'mean'),
                                            med_ratio=('ratio', 'median')).reset_index()
print(agg.round(2).to_string())

# Full regression (y=14C, x=model)
print('\nFull matched regression (y=14C, x=model):')
r = ols(mm['npp_model'], mm['npp14'])
print(f'n={r["n"]} slope={r["slope"]:.3f} inter={r["inter"]:.2f} r2={r["r2"]:.3f} rmse={r["rmse"]:.2f}')

# Save matched dataset
mm.to_csv(r'D:\project\paper-bench\tasks_legacy\wong_2020\agent_solution\results\c03_matched_raw.csv', index=False)
