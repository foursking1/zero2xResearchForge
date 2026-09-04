"""Explore C03: modeled NPP vs 14C incubations. Match npp_profiles NPP_z to 14C depths.
Paper anchors: overall (excl 3 subarctic climax stations) y=0.99x-1.4, r2=0.80, RMSE=6.03, n=138
               3-station subset y=0.33x+2.1, r2=0.85, RMSE=6.43, n=21
"""
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
print('npp_profiles columns:', list(npp.columns))
print(npp[['cruise','station','date']].drop_duplicates().head(10))
print('dates sample:', npp['date'].unique()[:5])

r14 = pd.read_csv(F(r'\files\npp_14c_all.csv'))
print('\nnpp_14c columns:', list(r14.columns))
print(r14.head(3))
print('14C stations:', r14.groupby(['cruise','station_num']).size().head(30))
print('date dtype sample:', r14['date'].head(3), r14['date'].dtype)
