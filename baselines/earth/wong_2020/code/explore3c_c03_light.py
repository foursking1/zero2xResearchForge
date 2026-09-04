"""C03 light-level matching: map each 14C incubation to model depth where PAR_z/PAR0 = lightlevel/100."""
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
npp['date'] = npp['date'].astype(str)
npp['station'] = npp['station'].astype(str)
r14['dstr'] = r14['date'].astype(str).apply(lambda d: f'{d[:4]}-{d[4:6]}-{d[6:8]}')
r14['station'] = r14['station'].astype(str)

def map_st(cr, st):
    if cr == 'NAAMES2' and st in ('4a', '4b', '4c'):
        return '4'
    if cr == 'NAAMES3' and st == 'unknown':
        return '6'
    return st

r14['pstation'] = [map_st(c, s) for c, s in zip(r14['cruise'], r14['station'])]

# Build per (cruise, station) list of profiles (date, z, PAR_z, NPP_z)
prof_by = {}
for (cr, st), g in npp.groupby(['cruise', 'station']):
    prof_by[(cr, st)] = g

def match_light(cr, st, dstr, lightlevel, use_light=True, depth=None):
    """Find model NPP for this 14C incubation. If use_light, match by light level;
    else match by nearest depth."""
    g = prof_by.get((cr, st))
    if g is None:
        return np.nan, np.nan, 0
    # choose profile date: exact match preferred, else the one with max NPP_z max (active)
    dates = sorted(g['date'].unique())
    if dstr in dates:
        pd_ = dstr
    else:
        # pick date closest to dstr among active profiles
        best = None; best_d = 1e9
        for d in dates:
            sub = g[g['date'] == d]
            if sub['NPP_z'].max() <= 0:
                continue
            dd = abs(pd.to_datetime(d) - pd.to_datetime(dstr)).days
            if dd < best_d:
                best_d = dd; best = d
        if best is None:
            return np.nan, np.nan, 0
        pd_ = best
    sub = g[g['date'] == pd_].sort_values('z')
    z = sub['z'].to_numpy(float)
    if use_light:
        par0 = sub['PAR_z'].iloc[0]
        if not np.isfinite(par0) or par0 <= 0:
            return np.nan, np.nan, 0
        lf = sub['PAR_z'].to_numpy(float) / par0
        target = lightlevel / 100.0
        i = np.argmin(np.abs(lf - target))
    else:
        if depth is None:
            return np.nan, np.nan, 0
        i = np.argmin(np.abs(z - depth))
    return sub['NPP_z'].iloc[i], sub['z'].iloc[i], len(sub)

rows = []
for _, row in r14.iterrows():
    for use_light, tag in [(True, 'light'), (False, 'depth')]:
        mnpp, mz, nz = match_light(row['cruise'], row['pstation'], row['dstr'],
                                   row['lightlevel'], use_light=use_light, depth=row['depth'])
        rows.append(dict(cruise=row['cruise'], station=row['station'], pstation=row['pstation'],
                         date=row['dstr'], depth=row['depth'], lightlevel=row['lightlevel'],
                         npp14=row['NPP_14C'], npp_model=mnpp, model_z=mz, tag=tag))
M = pd.DataFrame(rows)
M['npp14'] = pd.to_numeric(M['npp14'], errors='coerce')

for tag in ['light', 'depth']:
    mm = M[M['tag'] == tag]
    ok = np.isfinite(mm['npp14']) & np.isfinite(mm['npp_model']) & (mm['npp_model'] > 0)
    mm = mm[ok]
    print(f'=== {tag}-matched: n={len(mm)} ===')
    r = ols(mm['npp_model'], mm['npp14'])
    print(f'  y=14C, x=model: n={r["n"]} slope={r["slope"]:.3f} inter={r["inter"]:.2f} r2={r["r2"]:.3f} rmse={r["rmse"]:.2f}')
    mm['ratio'] = mm['npp_model'] / mm['npp14'].replace(0, np.nan)
    # save
    mm2 = mm.copy()
    mm2 = mm2[['cruise','station','date','depth','lightlevel','npp14','npp_model','model_z','ratio']]
    mm2.to_csv(rf'D:\project\paper-bench\tasks_legacy\wong_2020\agent_solution\results\c03_matched_{tag}.csv', index=False)
    print(mm2.groupby(['cruise','station']).agg(n=('npp14','size'), med_r=('ratio','median')).round(2).to_string())
    print()
