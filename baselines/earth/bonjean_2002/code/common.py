#!/usr/bin/env python3
"""Shared configuration and loading helpers for the Bonjean & Lagerloef (2002)
diagnostic-model reproduction analysis.

Data root points at the frozen reproduction workspace (read in place, never copied).
All scripts in this folder import from here so the data location is defined once.
"""
import os
import numpy as np
import netCDF4 as nc4

# Frozen data root (original location; do not copy).
DATA_ROOT = r"F:\dataset\42_bonjean_2002_mem_n\42_bonjean_2002_mem_n\reproduce"

# Physical constants from the paper / P05 report.
G = 9.8            # m/s^2
RHO_AIR = 1.22     # kg/m^3  (Large & Pond 1981)
RHO_M = 1025.0     # kg/m^3  reference seawater density
CHI_T = 3.0e-4     # K^-1    thermal expansion coefficient
R_EARTH = 6371000.0  # m
DEG2M = 111200.0   # m/deg (used by reference scripts)
H_LAYER = 70.0     # m depth scale (paper)
H_STDD = 30.0      # m layer-average depth


def path(name):
    return os.path.join(DATA_ROOT, name)


def load_ssh():
    ds = nc4.Dataset(path("topex_ssh_tropical_pacific_10day.nc"))
    ssh = ds.variables["ssh_anomaly"][:]
    time = ds.variables["time"][:]
    lat = ds.variables["latitude"][:]
    lon = ds.variables["longitude"][:]
    ds.close()
    return ssh, time, lat, lon


def load_dh():
    """Mean dynamic height (relative to 1000 dbar) on the 1-deg tropical Pacific grid."""
    ds = nc4.Dataset(path("woa94_mean_dynamic_height.nc"))
    lat = ds.variables["latitude"][:]
    lon = ds.variables["longitude"][:]
    dh = ds.variables["dh"][:]
    ds.close()
    return dh, lat, lon


def load_winds():
    ds = nc4.Dataset(path("ccmp_wind_tropical_pacific_10day.nc"))
    uw = ds.variables["uwnd"][:]
    vw = ds.variables["vwnd"][:]
    time = ds.variables["time"][:]
    lat = ds.variables["lat"][:]
    lon = ds.variables["lon"][:]
    ds.close()
    return uw, vw, time, lat, lon


def wind_stress_large_pond(uw, vw):
    """Bulk aerodynamic wind stress (m^2 s^-2) after Large & Pond (1981), as
    described in the P05 report.

    tau = rho_air * C_DN * |W| * W / rho_m
    C_DN = 1.2e-3  (|W| < 11 m/s)
    C_DN = (0.49 + 0.065*|W|) * 1e-3  (11 <= |W| <= 25 m/s)
    """
    W = np.sqrt(uw ** 2 + vw ** 2)
    cdn = np.where(W < 11.0, 1.2e-3, (0.49 + 0.065 * W) * 1e-3)
    tau_x = RHO_AIR * cdn * W * uw / RHO_M
    tau_y = RHO_AIR * cdn * W * vw / RHO_M
    return tau_x, tau_y


def load_stored_tau():
    """Stored wind stress in the frozen file (documented to be ~2*pi too weak)."""
    ds = nc4.Dataset(path("wind_stress_tropical_pacific_10day.nc"))
    tau_x = ds.variables["tau_x"][:]
    tau_y = ds.variables["tau_y"][:]
    ds.close()
    return tau_x, tau_y


def load_buoyancy_gradient_mean():
    ds = nc4.Dataset(path("sst_buoyancy_gradient_mean.nc"))
    thx = ds.variables["theta_x_mean"][:]
    thy = ds.variables["theta_y_mean"][:]
    lat = ds.variables["latitude"][:]
    lon = ds.variables["longitude"][:]
    ds.close()
    return thx, thy, lat, lon


def load_layer_velocity():
    ds = nc4.Dataset(path("layer_averaged_velocity_30m.nc"))
    u = ds.variables["u"][:]
    v = ds.variables["v"][:]
    time = ds.variables["time"][:]
    lat = ds.variables["latitude"][:]
    lon = ds.variables["longitude"][:]
    ds.close()
    return u, v, time, lat, lon


def load_mean_diagnostic_velocity():
    ds = nc4.Dataset(path("mean_diagnostic_velocity.nc"))
    u_mean = ds.variables["u_mean"][:]
    v_mean = ds.variables["v_mean"][:]
    lat = ds.variables["latitude"][:]
    lon = ds.variables["longitude"][:]
    ds.close()
    return u_mean, v_mean, lat, lon


def load_drifter_05():
    ds = nc4.Dataset(path("drifter_mean_field_05deg.nc"))
    lon = ds.variables["longitude"][:]
    lat = ds.variables["latitude"][:]
    u = ds.variables["u"][:]   # (lon, lat)
    v = ds.variables["v"][:]
    ds.close()
    return u, v, lat, lon


def zonal_grad_1d(f1d, lat_row, lon):
    """Centered zonal gradient (d/dx) of a 1-D field on a given latitude row."""
    dld = np.abs(lon[1] - lon[0]) * np.pi / 180.0
    dx = dld * R_EARTH * np.cos(lat_row * np.pi / 180.0)
    g = np.full(len(f1d), np.nan)
    g[1:-1] = (f1d[2:] - f1d[:-2]) / (2 * dx)
    g[0] = (f1d[1] - f1d[0]) / dx
    g[-1] = (f1d[-1] - f1d[-2]) / dx
    return g


def merid_grad_2d_row(field2d, idx, lat):
    """Centered meridional gradient at latitude row idx of a (lat, lon) field."""
    dlat_m = np.abs(lat[1] - lat[0]) * np.pi / 180.0 * R_EARTH
    ny = field2d.shape[0]
    if idx == 0:
        return (field2d[1] - field2d[0]) / dlat_m
    if idx == ny - 1:
        return (field2d[-1] - field2d[-2]) / dlat_m
    return (field2d[idx + 1] - field2d[idx - 1]) / (2 * dlat_m)


def equator_interp(field2d, lat):
    """Average the two rows bracketing the equator (-0.5 and +0.5) -> lat=0 value."""
    idx = int(np.argmin(np.abs(lat)))
    row_lo, row_hi = idx, idx + 1
    return 0.5 * (field2d[row_lo] + field2d[row_hi])
