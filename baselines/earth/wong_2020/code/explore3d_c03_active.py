"""C03 with active-profile date selection + light-level matching. Identify the 3 subarctic climax stations."""
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

# active profiles per station
prof_by = {}
for (cr, st), g in npp.groupby(['cruise', 'station']):
    act = g[g.groupby('date')['NPP_z'].transform('max') > 0] if len(g) else g
    if len(act) == 0:
        act = g
    prof_by[(cr, st)] = act

def match_light(cr, st, dstr, lightlevel, mode):
    g = prof_by.get((cr, st))
    if g is None or len(g) == 0:
        return np.nan, np.nan, 0
    dates = sorted(g['date'].unique())
    # choose date: exact if active, else nearest active, else exact
    if dstr in dates:
        sub = g[g['date'] == dstr]
        if sub['NPP_z'].max() > 0:
            pd_ = dstr
        else:
            pd_ = min(dates, key=lambda d: abs(pd.to_datetime(d) - pd.to_datetime(dstr)))
    else:
        pd_ = min(dates, key=lambda d: abs(pd.to_datetime(d) - pd.to_datetime(dstr)))
    sub = g[g['date'] == pd_].sort_values('z')
    z = sub['z'].to_numpy(float)
    par0 = sub['PAR_z'].iloc[0]
    if mode == 'light':
        if not np.isfinite(par0) or par0 <= 0:
            return np.nan, np.nan, 0
        lf = sub['PAR_z'].to_numpy(float) / par0
        target = lightlevel / 100.0
        i = np.argmin(np.abs(lf - target))
    else:
        i = np.argmin(np.abs(z - lightlevel))  # lightlevel is actually depth in mode=depth
    return sub['NPP_z'].iloc[i], sub['z'].iloc[i], len(sub)

rows = []
for _, row in r14.iterrows():
    for mode, arg in [('light', row['lightlevel']), ('depth', row['depth'])]:
        mnpp, mz, nz = match_light(row['cruise'], row['pstation'], row['dstr'], arg, mode)
        rows.append(dict(cruise=row['cruise'], station=row['station'], pstation=row['pstation'],
                         date=row['dstr'], depth=row['depth'], lightlevel=row['lightlevel'],
                         npp14=row['NPP_14C'], npp_model=mnpp, model_z=mz, tag=mode, lat=row['lat'], lon=row['lon']))
M = pd.DataFrame(rows)
M['npp14'] = pd.to_numeric(M['npp14'], errors='coerce')

for tag in ['light', 'depth']:
    mm = M[M['tag'] == tag]
    ok = np.isfinite(mm['npp14']) & np.isfinite(mm['npp_model']) & (mm['npp_model'] > 0)
    mm = mm[ok]
    mm['ratio'] = mm['npp_model'] / mm['npp14'].replace(0, np.nan)
    print(f'=== {tag}-matched: n={len(mm)} ===')
    r = ols(mm['npp_model'], mm['npp14'])
    print(f'  ALL  y=14C x=model: n={r["n"]} slope={r["slope"]:.3f} inter={r["inter"]:.2f} r2={r["r2"]:.3f} rmse={r["rmse"]:.2f}')
    # by-station median ratio
    st = mm.groupby(['cruise', 'station']).agg(n=('npp14', 'size'), med_r=('ratio', 'median'),
                                               lat=('lat', 'first')).reset_index()
    print(st.round(2).to_string())
    # save
    mm.to_csv(rf'D:\project\paper-bench\tasks_legacy\wong_2020\agent_solution\results\c03_matched_{tag}_active.csv', index=False)
    print()
