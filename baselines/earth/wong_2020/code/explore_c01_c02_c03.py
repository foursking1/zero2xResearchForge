"""Exploration script: try aggregation schemes to reproduce paper anchors."""
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
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot
    rmse = np.sqrt(ss_res / n)
    return dict(n=n, slope=slope, inter=inter, r2=r2, rmse=rmse)

def rma(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    n = len(x)
    if n < 3:
        return dict(n=n)
    sx, sy = np.std(x, ddof=1), np.std(y, ddof=1)
    r = np.corrcoef(x, y)[0, 1]
    slope = sy / sx
    inter = np.mean(y) - slope * np.mean(x)
    yhat = slope * x + inter
    rmse = np.sqrt(np.mean((y - yhat) ** 2))
    return dict(n=n, slope=slope, inter=inter, r2=r**2, rmse=rmse)

# ============ C01: theta_opt = cphyto_bbp / ChlACS vs theta_PaM ============
print('=' * 70)
print('C01: theta_opt vs theta_PaM')
print('=' * 70)
bb = pd.read_csv(F(r'\files\cphyto_bbp_all.csv'))
chl = pd.read_csv(F(r'\directories\P03_ChlACS\ChlACS_all_cruises.csv'))
pam = pd.read_csv(F(r'\directories\P10_theta_PaM\theta_PaM_1min_all.csv'))

for df in (bb, chl, pam):
    df['dt'] = pd.to_datetime(df['datetime'], utc=True)

# normalize cruise keys
cmap = {'naames_1': 'NAAMES1', 'naames_2': 'NAAMES2', 'naames_3': 'NAAMES3', 'naames_4': 'NAAMES4'}
bb['cruise_n'] = bb['cruise'].map(cmap)

# Merge cphyto_bbp with ChlACS on nearest datetime
def nearest_merge(a, b, tol='2min', suffixes=('_a', '_b')):
    a = a.sort_values('dt').copy()
    b = b.sort_values('dt').copy()
    m = pd.merge_asof(a, b, on='dt', direction='nearest',
                      tolerance=pd.Timedelta(tol), suffixes=suffixes)
    return m

m1 = nearest_merge(bb, chl)
# add theta_PaM from pam on same dt
m2 = nearest_merge(m1, pam, suffixes=('_x', '_y'))
m2 = m2[np.isfinite(m2['cphyto_bbp']) & np.isfinite(m2['ChlACS_mg_m3']) & np.isfinite(m2['theta_PaM'])]
m2 = m2[(m2['ChlACS_mg_m3'] > 0) & (m2['cphyto_bbp'] > 0)]
m2['theta_opt'] = m2['cphyto_bbp'] / m2['ChlACS_mg_m3']

print(f'\n[1-min merged, tol 2min] n={len(m2)}')
print(' theta_opt stats:', m2['theta_opt'].describe()[['mean','std','min','max']].round(2).to_dict())
for regname, reg in [('OLS', ols), ('RMA', rma)]:
    r = reg(m2['theta_PaM'], m2['theta_opt'])
    print(f' {regname}: slope={r.get("slope")}, inter={r.get("inter")}, r2={r.get("r2")}, rmse={r.get("rmse")}, n={r.get("n")}')

# Try only points with theta_PaM > 0 and reasonable
m2v = m2[(m2['theta_PaM'] > 0) & (m2['theta_PaM'] < 300) & (m2['theta_opt'] < 300)]
print(f'\n[1-min merged, filtered 0<theta<300] n={len(m2v)}')
for regname, reg in [('OLS', ols), ('RMA', rma)]:
    r = reg(m2v['theta_PaM'], m2v['theta_opt'])
    print(f' {regname}: slope={r.get("slope")}, inter={r.get("inter")}, r2={r.get("r2")}, rmse={r.get("rmse")}, n={r.get("n")}')

# Also try daily-mean per station-day (using cphyto_mod_per_station station-days)
bb['date'] = bb['dt'].dt.date
chl['date'] = chl['dt'].dt.date
pam['date'] = pd.to_datetime(pam['dt']).dt.date
# daily means per (cruise,date)
bb_d = bb.groupby(['cruise_n', 'date']).agg(bbp_mean=('bbp470', 'mean'),
                                            cphyto_mean=('cphyto_bbp', 'mean')).reset_index()
chl_d = chl.groupby(['cruise', 'date']).agg(chl_mean=('ChlACS_mg_m3', 'mean')).reset_index()
pam_d = pam.dropna(subset=['theta_PaM']).groupby(['cruise', 'date']).agg(
    theta_mean=('theta_PaM', 'mean')).reset_index()

bb_d['cruise_n'] = bb_d['cruise_n'].astype(str)
m = bb_d.merge(chl_d, left_on=['cruise_n', 'date'], right_on=['cruise', 'date'], suffixes=('', '_c'))
m = m.merge(pam_d, left_on=['cruise_n', 'date'], right_on=['cruise', 'date'], suffixes=('', '_p'))
m['theta_opt_d'] = m['cphyto_mean'] / m['chl_mean']
print(f'\n[daily-mean per date] n={len(m)}')
for regname, reg in [('OLS', ols), ('RMA', rma)]:
    r = reg(m['theta_mean'], m['theta_opt_d'])
    print(f' {regname}: slope={r.get("slope")}, inter={r.get("inter")}, r2={r.get("r2")}, rmse={r.get("rmse")}, n={r.get("n")}')

# station-day C01 using cphyto_mod_per_station station-days (PAR>0 only for valid PaM)
cmod = pd.read_csv(F(r'\directories\P12_NPP\cphyto_mod_per_station.csv'))
cmod['date'] = pd.to_datetime(cmod['date']).dt.date
mS = cmod.merge(bb_d, left_on=['cruise', 'date'], right_on=['cruise_n', 'date'])
mS = mS.merge(chl_d, left_on=['cruise', 'date'], right_on=['cruise', 'date'], suffixes=('', '_c'))
mS['theta_opt_s'] = mS['cphyto_mean'] / mS['chl_mean']
print(f'\n[station-day via cmod] n={len(mS)} (PAR>0: {(mS["PAR_mean"]>0).sum()})')
for subset_name, sub in [('all', mS), ('PAR>0', mS[mS['PAR_mean'] > 0])]:
    print(f'  subset={subset_name} n={len(sub)}')
    for regname, reg in [('OLS', ols), ('RMA', rma)]:
        r = reg(sub['theta_PaM_mean'], sub['theta_opt_s'])
        print(f'   {regname}: slope={r.get("slope")}, inter={r.get("inter")}, r2={r.get("r2")}, rmse={r.get("rmse")}, n={r.get("n")}')

# ============ C02: C_phyto_mod vs bbp(470) ============
print('\n' + '=' * 70)
print('C02: C_phyto_mod vs bbp470')
print('=' * 70)
cmod = pd.read_csv(F(r'\directories\P12_NPP\cphyto_mod_per_station.csv'))
cmod['date'] = pd.to_datetime(cmod['date']).dt.date

# station-day bbp means from cphyto_bbp_all
bb['cruise_n'] = bb['cruise'].map(cmap)
bb['date'] = bb['dt'].dt.date

# Approach A: station-day, match by cruise+date (no spatial filter), PAR>0
cmod['PAR>0'] = cmod['PAR_mean'] > 0
bb_d2 = bb.groupby(['cruise_n', 'date']).agg(bbp_mean=('bbp470', 'mean'),
                                             bbp_med=('bbp470', 'median'),
                                             n_bbp=('bbp470', 'size')).reset_index()
mA = cmod.merge(bb_d2, left_on=['cruise', 'date'], right_on=['cruise_n', 'date'])
print(f'\n[A station-day, all] n={len(mA)}')
for regname, reg in [('OLS', ols), ('RMA', rma)]:
    r = reg(mA['bbp_mean'], mA['C_phyto_mod'])
    print(f' {regname}: slope={r.get("slope")}, inter={r.get("inter")}, r2={r.get("r2")}, rmse={r.get("rmse")}, n={r.get("n")}')

mA_p = mA[mA['PAR>0']]
print(f'\n[A station-day, PAR>0] n={len(mA_p)}')
for regname, reg in [('OLS', ols), ('RMA', rma)]:
    r = reg(mA_p['bbp_mean'], mA_p['C_phyto_mod'])
    print(f' {regname}: slope={r.get("slope")}, inter={r.get("inter")}, r2={r.get("r2")}, rmse={r.get("rmse")}, n={r.get("n")}')

# Approach B: daily mean (aggregate over whole day incl all stations), PAR>0
print(f'\n[B daily-mean (same as A for single-station days)]')
# Approach C: 1-min samples: C_phyto_mod_1min = theta_PaM * ChlACS vs bbp470
m3 = nearest_merge(pam, chl, suffixes=('_p', '_c'))
m3 = m3[np.isfinite(m3['theta_PaM']) & np.isfinite(m3['ChlACS_mg_m3']) & np.isfinite(m3['bbp470'])]
m3 = m3[(m3['ChlACS_mg_m3'] > 0) & (m3['theta_PaM'] > 0) & (m3['bbp470'] > 0)]
m3['C_mod_1min'] = m3['theta_PaM'] * m3['ChlACS_mg_m3']
print(f'\n[C 1-min Cmod vs bbp] n={len(m3)}')
for regname, reg in [('OLS', ols), ('RMA', rma)]:
    r = reg(m3['bbp470'], m3['C_mod_1min'])
    print(f' {regname}: slope={r.get("slope")}, inter={r.get("inter")}, r2={r.get("r2")}, rmse={r.get("rmse")}, n={r.get("n")}')

print('\nDone.')
