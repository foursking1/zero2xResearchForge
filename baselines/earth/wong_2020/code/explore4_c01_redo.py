"""Redo C01 with correct theta_opt = cphyto_bbp / ChlACS (C:Chl) at 1-min bins."""
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
    yh = slope * x + inter
    r2 = 1 - np.sum((y - yh) ** 2) / np.sum((y - np.mean(y)) ** 2)
    rmse = np.sqrt(np.sum((y - yh) ** 2) / n)
    return dict(n=n, slope=slope, inter=inter, r2=r2, rmse=rmse)

cmap = {'naames_1':'NAAMES1','naames_2':'NAAMES2','naames_3':'NAAMES3','naames_4':'NAAMES4'}
bb = pd.read_csv(F(r'\files\cphyto_bbp_all.csv'))
bb['cruise_n'] = bb['cruise'].map(cmap)
bb['dt'] = pd.to_datetime(bb['datetime'], utc=True)
bb['dtm'] = bb['dt'].dt.floor('min')
chl = pd.read_csv(F(r'\directories\P03_ChlACS\ChlACS_all_cruises.csv'))
chl['dt'] = pd.to_datetime(chl['datetime'], utc=True)
chl['dtm'] = chl['dt'].dt.floor('min')
pam = pd.read_csv(F(r'\directories\P10_theta_PaM\theta_PaM_1min_all.csv'))
pam['dt'] = pd.to_datetime(pam['datetime'], utc=True)
pam['dtm'] = pam['dt'].dt.floor('min')

# 1-min bin means per cruise+minute
bb1 = bb.groupby(['cruise_n','dtm']).agg(bbp=('bbp470','mean'), cph=('cphyto_bbp','mean')).reset_index()
chl1 = chl.groupby(['cruise','dtm']).agg(chl=('ChlACS_mg_m3','mean')).reset_index()
pam1 = pam.groupby(['cruise','dtm']).agg(th=('theta_PaM','mean'), PAR=('PAR','mean')).reset_index()

# Merge on minute
m = bb1.merge(chl1, left_on=['cruise_n','dtm'], right_on=['cruise','dtm'])
m = m.merge(pam1, left_on=['cruise_n','dtm'], right_on=['cruise','dtm'])
m = m[(m['chl']>0) & (m['cph']>0)]
m['theta_opt'] = m['cph'] / m['chl']
m = m[np.isfinite(m['theta_opt']) & np.isfinite(m['th'])]
print(f'1-min bins merged: n={len(m)}')
print(f'theta_opt range: {m["theta_opt"].min():.1f} - {m["theta_opt"].max():.1f} (paper 10-235)')

# filter reasonable range like paper (10-235)
mf = m[(m['theta_opt']>0) & (m['theta_opt']<300) & (m['th']>0) & (m['th']<300)]
for name, sub in [('all', m), ('0<theta<300', mf), ('PAR>0', m[m['PAR']>0])]:
    r = ols(sub['th'], sub['theta_opt'])
    print(f'{name}: n={r["n"]} slope={r["slope"]:.3f} inter={r["inter"]:.2f} r2={r["r2"]:.3f} rmse={r["rmse"]:.2f}')

# Also try daytime only (PAR>0) + range filter
sub = mf[mf['PAR']>0]
r = ols(sub['th'], sub['theta_opt'])
print(f'PAR>0 & 0<theta<300: n={r["n"]} slope={r["slope"]:.3f} inter={r["inter"]:.2f} r2={r["r2"]:.3f} rmse={r["rmse"]:.2f}')

# per-cruise
print('\nPer cruise (0<theta<300):')
for cr, g in mf.groupby('cruise_n'):
    r = ols(g['th'], g['theta_opt'])
    print(f'  {cr}: n={r["n"]} slope={r["slope"]:.3f} inter={r["inter"]:.2f} r2={r["r2"]:.3f} rmse={r["rmse"]:.2f}')
