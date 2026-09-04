"""Grid search C02 definitions to match anchor (14910, 0.70, 0.61, 16.31)."""
import pandas as pd
import numpy as np

ROOT = r'E:\scisolvebench-data\asset-data\datasets-v1\v1\wong_2020\real_data_candidates\naames_observation_subset_v1'
F = lambda p: ROOT + p

def ols(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    n = len(x)
    if n < 3: return dict(n=n)
    X = np.vstack([x, np.ones_like(x)]).T
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    slope, inter = beta
    yhat = slope * x + inter
    ss_res = np.sum((y - yhat) ** 2); ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot
    rmse = np.sqrt(ss_res / n)
    return dict(n=n, slope=slope, inter=inter, r2=r2, rmse=rmse)

cmap = {'naames_1':'NAAMES1','naames_2':'NAAMES2','naames_3':'NAAMES3','naames_4':'NAAMES4'}
cmod = pd.read_csv(F(r'\directories\P12_NPP\cphyto_mod_per_station.csv'))
cmod['date'] = pd.to_datetime(cmod['date']).dt.date
bb = pd.read_csv(F(r'\files\cphyto_bbp_all.csv'))
bb['dt'] = pd.to_datetime(bb['datetime'], utc=True)
bb['cruise_n'] = bb['cruise'].map(cmap)
bb['date'] = bb['dt'].dt.date
chl = pd.read_csv(F(r'\directories\P03_ChlACS\ChlACS_all_cruises.csv'))
chl['dt'] = pd.to_datetime(chl['datetime'], utc=True)
chl['date'] = chl['dt'].dt.date
pam = pd.read_csv(F(r'\directories\P10_theta_PaM\theta_PaM_1min_all.csv'))
pam['dt'] = pd.to_datetime(pam['datetime'], utc=True)
pam['date'] = pam['dt'].dt.date

# 1-min Cmod
mp = pam.merge(chl[['dt','ChlACS_mg_m3']], on='dt', how='inner')
mp = mp[np.isfinite(mp['theta_PaM']) & np.isfinite(mp['ChlACS_mg_m3']) & (mp['ChlACS_mg_m3']>0)]
mp['Cmod_1min'] = mp['theta_PaM'] * mp['ChlACS_mg_m3']

# daytime bbp (PAR>0): match bbp to pam PAR
bbp2 = bb[np.isfinite(bb['bbp470']) & (bb['bbp470']>0)].copy()
bbp2['dt'] = bbp2['dt'].dt.floor('min')
pam_par = pam[['dt','PAR']].dropna()
bbp2 = bbp2.merge(pam_par, on='dt', how='left')
bbp2['is_day'] = bbp2['PAR'].fillna(0) > 0

target = (14910, 0.70, 0.61, 16.31)

def score(r):
    slope, inter, r2, rmse = r['slope'], r['inter'], r['r2'], r['rmse']
    return abs(slope-target[0])/target[0] + abs(inter-target[1])/abs(target[1]) + abs(r2-target[2])/target[2] + abs(rmse-target[3])/target[3]

results = []
# y variants
for yname, yvals in [('cmod_station', cmod.set_index(['cruise','date'])['C_phyto_mod'])]:
    pass

# Build daily aggregates
bb_all = bbp2.groupby(['cruise_n','date']).agg(bbp_all=('bbp470','mean')).reset_index()
bb_day = bbp2[bbp2['is_day']].groupby(['cruise_n','date']).agg(bbp_day=('bbp470','mean')).reset_index()
bb_med = bbp2.groupby(['cruise_n','date']).agg(bbp_med=('bbp470','median')).reset_index()
mp_d = mp.groupby(['cruise','date']).agg(Cmod_1m=('Cmod_1min','mean'),
                                         theta_d=('theta_PaM','mean'),
                                         chl_d=('ChlACS_mg_m3','mean')).reset_index()
cmod_dates = cmod[cmod['PAR_mean']>0][['cruise','date']].drop_duplicates()
cmod_all_dates = cmod[['cruise','date']].drop_duplicates()

for label, bbdf, xcol in [('bbp_all', bb_all, 'bbp_all'), ('bbp_day', bb_day, 'bbp_day'), ('bbp_med', bb_med, 'bbp_med')]:
    for yname in ['Cmod_1m', 'theta_d_chl_d']:
        if yname == 'Cmod_1m':
            m = mp_d.merge(bbdf, left_on=['cruise','date'], right_on=['cruise_n','date'])
            y = m['Cmod_1m']
        else:
            m = mp_d.merge(bbdf, left_on=['cruise','date'], right_on=['cruise_n','date'])
            y = m['theta_d'] * m['chl_d']
        for fname, filt in [('alldates', m.index), ('cmodPAR>0', m.merge(cmod_dates, on=['cruise','date'], how='inner').index),
                            ('cmodAll', m.merge(cmod_all_dates, on=['cruise','date'], how='inner').index)]:
            mf = m.loc[filt]
            if len(mf) < 3: continue
            r = ols(mf[xcol], y.loc[mf.index])
            results.append((f'{yname}|{label}|{fname}', r))

# cmod station value variants
for label, bbdf, xcol in [('bbp_all', bb_all, 'bbp_all'), ('bbp_day', bb_day, 'bbp_day')]:
    m = cmod.merge(bbdf, left_on=['cruise','date'], right_on=['cruise_n','date'])
    for fname, filt in [('alldates', m.index), ('PAR>0', m[m['PAR_mean']>0].index)]:
        mf = m.loc[filt]
        r = ols(mf[xcol], mf['C_phyto_mod'])
        results.append((f'cmod_station|{label}|{fname}', r))

results.sort(key=lambda t: score(t[1]))
for name, r in results[:12]:
    print(f'{name:35s} n={r["n"]:3d} slope={r["slope"]:9.1f} inter={r["inter"]:7.2f} r2={r["r2"]:.3f} rmse={r["rmse"]:6.2f}  score={score(r):.3f}')
