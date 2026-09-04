"""C04: Depth-resolved modeled NPP profiles vs discrete 14C measurements.
Generates profile comparison figures and aggregate metrics."""
import pandas as pd
import numpy as np
import os

ROOT = r'E:\scisolvebench-data\asset-data\datasets-v1\v1\wong_2020\real_data_candidates\naames_observation_subset_v1'
F = lambda p: ROOT + p
OUT = r'D:\project\paper-bench\tasks_legacy\wong_2020\agent_solution\results'

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

# Active profiles per (cruise, station): prefer exact date; else nearest active date
prof_by = {}
for (cr, st), g in npp.groupby(['cruise', 'station']):
    prof_by[(cr, st)] = g

def get_profile(cr, st, dstr):
    g = prof_by.get((cr, st))
    if g is None or len(g) == 0:
        return None, None
    dates = sorted(g['date'].unique())
    # choose active profile nearest to dstr
    best = None; best_d = 1e9
    for d in dates:
        sub = g[g['date'] == d]
        if sub['NPP_z'].max() <= 0:
            continue
        dd = abs(pd.to_datetime(d) - pd.to_datetime(dstr)).days
        if dd < best_d:
            best_d = dd; best = d
    if best is None:
        return None, None
    return g[g['date'] == best], best

# depth-match each 14C point
rows = []
for _, row in r14.iterrows():
    prof, pd_ = get_profile(row['cruise'], row['pstation'], row['dstr'])
    if prof is None:
        rows.append(dict(cruise=row['cruise'], station=row['station'], pstation=row['pstation'],
                         date=row['dstr'], depth=row['depth'], lightlevel=row['lightlevel'],
                         npp14=row['NPP_14C'], npp_model=np.nan, model_z=np.nan, prof_date=None))
        continue
    z = prof['z'].to_numpy(float)
    i = np.argmin(np.abs(z - row['depth']))
    rows.append(dict(cruise=row['cruise'], station=row['station'], pstation=row['pstation'],
                     date=row['dstr'], depth=row['depth'], lightlevel=row['lightlevel'],
                     npp14=row['NPP_14C'], npp_model=prof['NPP_z'].iloc[i],
                     model_z=prof['z'].iloc[i], prof_date=pd_))
M = pd.DataFrame(rows)
M['npp14'] = pd.to_numeric(M['npp14'], errors='coerce')

ok = np.isfinite(M['npp14']) & np.isfinite(M['npp_model']) & (M['npp_model'] > 0) & (M['npp14'] > 0)
mm = M[ok].copy()
mm['ratio'] = mm['npp_model'] / mm['npp14']

def ols(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    n = len(x)
    X = np.vstack([x, np.ones_like(x)]).T
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    slope, inter = beta
    yh = slope * x + inter
    r2 = 1 - np.sum((y - yh) ** 2) / np.sum((y - y.mean()) ** 2)
    rmse = np.sqrt(np.sum((y - yh) ** 2) / n)
    return dict(n=n, slope=slope, inter=inter, r2=r2, rmse=rmse)

print('=== C04 depth-profile comparison (y=14C, x=model NPP at nearest model depth) ===')
r = ols(mm['npp_model'], mm['npp14'])
print(f'All matched (14C>0, model>0): n={r["n"]} slope={r["slope"]:.3f} inter={r["inter"]:.2f} r2={r["r2"]:.3f} rmse={r["rmse"]:.2f}')
print(f'Median model/14C ratio: {mm["ratio"].median():.2f}, mean: {mm["ratio"].mean():.2f}')
print(f'% points within 2x (0.5<ratio<2): {(mm["ratio"].between(0.5,2).mean()*100):.1f}%')
print(f'% points within 3x (0.33<ratio<3): {(mm["ratio"].between(0.33,3).mean()*100):.1f}%')
corr = np.corrcoef(mm['npp_model'], mm['npp14'])[0,1]
print(f'Pearson r(model,14C) = {corr:.3f}')

print('\nPer-cruise:')
for cr, g in mm.groupby('cruise'):
    rr = ols(g['npp_model'], g['npp14'])
    print(f'  {cr}: n={rr["n"]} slope={rr["slope"]:.3f} r2={rr["r2"]:.3f} rmse={rr["rmse"]:.2f} med_ratio={g["ratio"].median():.2f}')

# Per-station summary for evidence
st = mm.groupby(['cruise', 'station']).agg(n=('npp14', 'size'),
                                           med_ratio=('ratio', 'median'),
                                           corr=('npp14', lambda x: np.corrcoef(mm.loc[x.index,'npp_model'], x)[0,1] if len(x)>2 else np.nan),
                                           rmse=('npp14', lambda x: np.sqrt(np.mean((mm.loc[x.index,'npp_model']-x)**2)))).reset_index()
print('\nPer-station:')
print(st.round(2).to_string())
st.to_csv(os.path.join(OUT, 'c04_per_station.csv'), index=False)
mm.to_csv(os.path.join(OUT, 'c04_matched_depth.csv'), index=False)

# ---- Generate profile comparison figures ----
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cruise_map = {'NAAMES1':'NAAMES1 (winter transition)', 'NAAMES2':'NAAMES2 (climax transition)',
                  'NAAMES3':'NAAMES3 (equilibrium phase)', 'NAAMES4':'NAAMES4 (accumulation phase)'}
    fig, axes = plt.subplots(2, 2, figsize=(14, 14))
    axes = axes.ravel()
    for idx, cr in enumerate(['NAAMES1', 'NAAMES2', 'NAAMES3', 'NAAMES4']):
        ax = axes[idx]
        profs = npp[npp['cruise'] == cr]
        # pick stations that have 14C data
        st14 = set(r14[r14['cruise'] == cr]['pstation'])
        for st_ in sorted(profs['station'].unique()):
            g = profs[profs['station'] == st_]
            for d in g['date'].unique():
                sub = g[g['date'] == d].sort_values('z')
                if sub['NPP_z'].max() <= 0:
                    continue
                lab = f'st{st_}' if st_ in st14 else None
                ax.plot(sub['NPP_z'], sub['z'], lw=1.2, color='k', alpha=0.5, label=lab if lab else None)
        m14 = mm[mm['cruise'] == cr]
        ax.scatter(m14['npp14'], m14['depth'], c='gray', s=30, zorder=5, label='14C')
        ax.set_ylim(120, 0)
        ax.set_xlabel('NPP (mg C m$^{-3}$ d$^{-1}$)')
        ax.set_ylabel('Depth (m)')
        ax.set_title(cruise_map[cr])
        if idx == 0:
            ax.legend(loc='lower right', fontsize=8)
        ax.grid(alpha=0.3)
    fig.suptitle('C04: Model NPP profiles (black) vs discrete 14C incubations (gray)')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'c04_profile_comparison.png'), dpi=120)
    print('\nSaved figure:', os.path.join(OUT, 'c04_profile_comparison.png'))
except Exception as e:
    print('Figure generation failed:', e)
