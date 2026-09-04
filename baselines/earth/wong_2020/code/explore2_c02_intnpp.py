"""Explore C02 (C_phyto_mod vs bbp) variants + verify intNPP from profiles vs Table 3."""
import pandas as pd
import numpy as np

ROOT = r'E:\scisolvebench-data\asset-data\datasets-v1\v1\wong_2020\real_data_candidates\naames_observation_subset_v1'
F = lambda p: ROOT + p

def ols(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    n = len(x)
    X = np.vstack([x, np.ones_like(x)]).T
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    slope, inter = beta
    yhat = slope * x + inter
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot
    rmse = np.sqrt(ss_res / n)
    return dict(n=n, slope=slope, inter=inter, r2=r2, rmse=rmse)

cmap = {'naames_1': 'NAAMES1', 'naames_2': 'NAAMES2', 'naames_3': 'NAAMES3', 'naames_4': 'NAAMES4'}

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

# ---- intNPP from profiles vs Table 3 ----
prof = pd.read_csv(F(r'\directories\P12_NPP\npp_profiles.csv'))
prof['date'] = pd.to_datetime(prof['date']).dt.date
# euphotic depth: z where PAR_z/PAR_0 <= 0.01 (1% light). Integrate NPP to that depth.
def int_npp(g, light_frac=0.01):
    g = g.sort_values('z')
    par0 = g['PAR_z'].iloc[0]
    if par0 <= 0:
        return np.nan
    zeu = g.loc[g['PAR_z'] / par0 <= light_frac, 'z'].min()
    if not np.isfinite(zeu):
        zeu = g['z'].max()
    sub = g[g['z'] <= zeu]
    return np.trapezoid(sub['NPP_z'], sub['z']) if len(sub) > 1 else np.nan

intnpp = prof.groupby(['cruise', 'date']).apply(int_npp).reset_index(name='intNPP')
intnpp['cruise_num'] = intnpp['cruise'].str.replace('NAAMES', '').astype(int)
print('=== intNPP from npp_profiles (mg C m-2 d-1) by cruise ===')
print(intnpp.groupby('cruise_num')['intNPP'].agg(['mean', 'std', 'min', 'max', 'count']).round(1))
print('\nPaper Table 3 intNPP: N1 248+/-116 (78-550), N2 984+/-329 (593-1535), N3 1464+/-440 (1004-2296), N4 602+/-192 (297-945)')

# ---- C02 variants ----
# Daily 1-min C_phyto = theta_PaM * ChlACS, restricted to where all exist
m = pam.merge(chl[['dt', 'ChlACS_mg_m3']], on='dt', how='inner')
m = m[np.isfinite(m['theta_PaM']) & np.isfinite(m['ChlACS_mg_m3']) & (m['PAR'] > 0) & (m['ChlACS_mg_m3'] > 0)]
m['Cmod_1min'] = m['theta_PaM'] * m['ChlACS_mg_m3']
bb2 = bb[np.isfinite(bb['bbp470']) & (bb['bbp470'] > 0)]

# per cruise+date, on-station restriction: use npp14 station locations
npp14 = pd.read_csv(F(r'\files\npp_14c_all.csv'))
st_loc = npp14.drop_duplicates(['cruise', 'station', 'date'])[['cruise', 'station', 'date', 'lat', 'lon']]
# map cruise names
st_loc['cruise_n'] = st_loc['cruise'].map(cmap)
st_loc['date'] = st_loc['date'].astype(str)

# station-date mapping from cmod: cruise, station, date. npp14 stations have names like '4a','4b','4c' -> cmod station '4'
def norm_st(cruise, st):
    st = str(st)
    if cruise == 'NAAMES2' and st in ('4a', '4b', '4c'):
        return '4'
    if cruise == 'NAAMES3' and st == 'unknown':
        return '6'
    return st
st_loc['pstation'] = [norm_st(c, s) for c, s in zip(st_loc['cruise_n'], st_loc['station'])]
cmod['pstation'] = cmod['station'].astype(str)

# Build per (cruise, date) on-station location (mean of npp14 locations that day)
st_daily = st_loc.groupby(['cruise_n', 'date'])[['lat', 'lon']].mean().reset_index()
st_daily['date'] = pd.to_datetime(st_daily['date']).dt.date
cmod2 = cmod.merge(st_daily, left_on=['cruise', 'date'], right_on=['cruise_n', 'date'], how='left')

# Haversine
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1; dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return 2*R*np.arcsin(np.sqrt(a))

results = []
for radius in [None, 30, 60, 100, 150, 250]:
    rows = []
    for (cruise, date), g in bb2.groupby(['cruise_n', 'date']):
        loc = st_daily[(st_daily['cruise_n'] == cruise) & (st_daily['date'] == date)]
        if len(loc) == 0:
            continue
        if radius is not None:
            g = g[haversine(g['lat'], g['lon'], loc['lat'].iloc[0], loc['lon'].iloc[0]) <= radius]
        if len(g) == 0:
            continue
        rows.append(dict(cruise=cruise, date=date, bbp_d=float(g['bbp470'].mean()),
                         bbp_m=float(g['bbp470'].median()), n_bbp=len(g)))
    bb_d = pd.DataFrame(rows)
    cc = cmod2.merge(bb_d, left_on=['cruise', 'date'], right_on=['cruise', 'date'], how='inner')
    cc = cc[cc['PAR_mean'] > 0]
    r = ols(cc['bbp_d'], cc['C_phyto_mod'])
    print(f'C02 station-day PAR>0 radius={radius}: n={r["n"]} slope={r["slope"]:.1f} inter={r["inter"]:.2f} r2={r["r2"]:.3f} rmse={r["rmse"]:.2f}')

# Try using daily-mean 1-min Cmod instead of cmod station value
m_d = m.groupby(['cruise', 'date']).agg(Cmod_d=('Cmod_1min', 'mean')).reset_index()
m_d['date'] = m_d['date'].dt.date
for radius in [None, 100]:
    rows = []
    for (cruise, date), g in bb2.groupby(['cruise_n', 'date']):
        loc = st_daily[(st_daily['cruise_n'] == cruise) & (st_daily['date'] == date)]
        if len(loc) == 0:
            continue
        if radius is not None:
            g = g[haversine(g['lat'], g['lon'], loc['lat'].iloc[0], loc['lon'].iloc[0]) <= radius]
        if len(g) == 0:
            continue
        rows.append(dict(cruise=cruise, date=date, bbp_d=float(g['bbp470'].mean())))
    bb_d = pd.DataFrame(rows)
    cc = m_d.merge(bb_d, on=['cruise', 'date'], how='inner')
    r = ols(cc['bbp_d'], cc['Cmod_d'])
    print(f'C02 1min-Cmod daily PAR>0 radius={radius}: n={r["n"]} slope={r["slope"]:.1f} inter={r["inter"]:.2f} r2={r["r2"]:.3f} rmse={r["rmse"]:.2f}')

# Optically-derived C vs bbp (text mentions r2=0.60, y=14760x+0.72) - sanity check
bb_n = bb[np.isfinite(bb['cphyto_bbp']) & (bb['bbp470'] > 0) & (bb['cphyto_bbp'] > 0)]
r = ols(bb_n['bbp470'], bb_n['cphyto_bbp'])
print(f'\nC02sanity optically-derived cphyto vs bbp (1-min all): n={r["n"]} slope={r["slope"]:.1f} inter={r["inter"]:.2f} r2={r["r2"]:.3f}')
