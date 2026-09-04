"""Explore C02 variants to match anchor (14910, 0.70, 0.61, 16.31)."""
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
npp14 = pd.read_csv(F(r'\files\npp_14c_all.csv'))

# 1-min Cmod and bbp merged per minute
mp = pam.merge(chl[['dt','ChlACS_mg_m3']], on='dt', how='inner')
mp = mp[np.isfinite(mp['theta_PaM']) & np.isfinite(mp['ChlACS_mg_m3']) & (mp['PAR']>0) & (mp['ChlACS_mg_m3']>0)]
mp['Cmod_1min'] = mp['theta_PaM'] * mp['ChlACS_mg_m3']
bbv = bb[np.isfinite(bb['bbp470']) & (bb['bbp470']>0)]

# daily means (cruise+date), restricted to times when PaM active (PAR>0) for Cmod
mp_d = mp.groupby(['cruise','date']).agg(Cmod_d=('Cmod_1min','mean'),
                                         theta_d=('theta_PaM','mean'),
                                         chl_d=('ChlACS_mg_m3','mean')).reset_index()
bb_d = bbv.groupby(['cruise_n','date']).agg(bbp_d=('bbp470','mean'),
                                            bbp_m=('bbp470','median'),
                                            cphyto_d=('cphyto_bbp','mean'),
                                            n=('bbp470','size')).reset_index()

# Merge variant 1: 1-min Cmod daily vs bbp daily, all matched days
m1 = mp_d.merge(bb_d, left_on=['cruise','date'], right_on=['cruise_n','date'])
r = ols(m1['bbp_d'], m1['Cmod_d'])
print(f'V1 1min-Cmod daily vs bbp daily, all: n={r["n"]} slope={r["slope"]:.1f} inter={r["inter"]:.2f} r2={r["r2"]:.3f} rmse={r["rmse"]:.2f}')

# Merge variant 2: cmod station value vs bbp daily (PAR>0)
m2 = cmod.merge(bb_d, left_on=['cruise','date'], right_on=['cruise_n','date'])
m2p = m2[m2['PAR_mean']>0]
for sub in [('all', m2), ('PAR>0', m2p)]:
    r = ols(sub[1]['bbp_d'], sub[1]['C_phyto_mod'])
    print(f'V2 cmod station vs bbp daily [{sub[0]}]: n={r["n"]} slope={r["slope"]:.1f} inter={r["inter"]:.2f} r2={r["r2"]:.3f} rmse={r["rmse"]:.2f}')

# Variant 3: Cmod_d = theta_d * chl_d (product of daily means from 1-min data) vs bbp
m3 = m1.copy()
m3['Cmod_prod'] = m3['theta_d'] * m3['chl_d']
r = ols(m3['bbp_d'], m3['Cmod_prod'])
print(f'V3 daily theta*chl vs bbp daily: n={r["n"]} slope={r["slope"]:.1f} inter={r["inter"]:.2f} r2={r["r2"]:.3f} rmse={r["rmse"]:.2f}')

# Variant 4: optically-derived C daily mean vs bbp daily (this is Fig5 dashed)
r = ols(m1['bbp_d'], m1['cphyto_d'])
print(f'V4 optical cphyto daily vs bbp daily: n={r["n"]} slope={r["slope"]:.1f} inter={r["inter"]:.2f} r2={r["r2"]:.3f} rmse={r["rmse"]:.2f}')

# Variant 5: per station-day using npp14 stations (map 4a/4b/4c->4, unknown->6), PAR>0
# Use daily Cmod (1-min) aggregated per (cruise,date) - same as V1 but intersect with cmod PAR>0 dates
cmod_p = cmod[cmod['PAR_mean']>0][['cruise','date']].drop_duplicates()
m5 = m1.merge(cmod_p, on=['cruise','date'], how='inner')
r = ols(m5['bbp_d'], m5['Cmod_d'])
print(f'V5 1min-Cmod daily, only cmod PAR>0 dates: n={r["n"]} slope={r["slope"]:.1f} inter={r["inter"]:.2f} r2={r["r2"]:.3f} rmse={r["rmse"]:.2f}')

# Variant 6: exclude low bbp outliers? and try forcing intercept
for r2_target in [False, True]:
    pass
