r"""Vuelta 5, prueba 1: ¿la BT14/BT15 de geocatL1 (la que usamos y la que usa VOLCAT) sale de la radiancia L1b cruda
de NOAA del paquete, y con qué coeficientes de Planck? Ubica cada píxel de geocatL1 en la grilla fija ABI (lat/lon a
ángulos de barrido) y compara, para C14 y C15, la BT de geocatL1 con la BT de la radiancia L1b convertida con
(a) los coeficientes de la L1b y (b) los de geocatL1. También la radiancia que recuperamos de la BT de geocatL1 con
coeficientes de geocatL1 contra la radiancia L1b. Cuadros 1 a 10. Escribe ../resultados/vuelta5_l1b.json.
"""
import glob, json, os, sys
import netCDF4
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
IN = r"D:\goes_cache\volcat_test_mauna_loa\ext\mauna-loa_g17-conus_nov2022_r20260709-volcat-code-ancil\input"
ML = r"D:\goes_cache\lut_h15\ml"
HORAS = ["091600", "092100", "092600", "093100", "093600", "094100", "094600", "095100", "095600", "100130"]
STAMP = {"091600": "0916", "092100": "0921", "092600": "0926", "093100": "0931", "093600": "0936", "094100": "0941",
         "094600": "0946", "095100": "0951", "095600": "0956", "100130": "1001"}


def latlon_a_xy(lat, lon, p):
    req, rpol = p.semi_major_axis, p.semi_minor_axis
    H = p.perspective_point_height + req
    l0 = np.radians(p.longitude_of_projection_origin)
    phi, lam = np.radians(lat), np.radians(lon)
    e2 = (req ** 2 - rpol ** 2) / req ** 2
    phic = np.arctan((rpol ** 2 / req ** 2) * np.tan(phi))
    rc = rpol / np.sqrt(1 - e2 * np.cos(phic) ** 2)
    sx = H - rc * np.cos(phic) * np.cos(lam - l0)
    sy = -rc * np.cos(phic) * np.sin(lam - l0)
    sz = rc * np.sin(phic)
    n = np.sqrt(sx ** 2 + sy ** 2 + sz ** 2)
    return np.arcsin(-sy / n), np.arctan(sz / sx)


def bt(r, fk1, fk2, bc1, bc2):
    with np.errstate(all="ignore"):
        return (fk2 / np.log(fk1 / r + 1) - bc1) / bc2


def rad(t, fk1, fk2, bc1, bc2):
    return fk1 / np.expm1(fk2 / (bc1 + bc2 * t))


out = {}
for h in HORAS:
    d = np.load(os.path.join(ML, f"ml_{h}.npz"))
    lat = d["geocatL1__pixel_latitude"].astype(float); lon = d["geocatL1__pixel_longitude"].astype(float)
    r = {}
    for ch in (14, 15):
        f = glob.glob(os.path.join(IN, f"OR_ABI-L1b-RadC-M6C{ch}_G17_s2022332{STAMP[h]}*.nc"))[0]
        ds = netCDF4.Dataset(f)
        p = ds["goes_imager_projection"]
        x, y = ds["x"][:].astype(float), ds["y"][:].astype(float)
        R = ds["Rad"][:].astype(float).filled(np.nan)
        cl = [float(ds[k][:]) for k in ("planck_fk1", "planck_fk2", "planck_bc1", "planck_bc2")]
        xs, ys = latlon_a_xy(lat, lon, p)
        ix = np.rint((xs - x[0]) / (x[1] - x[0])).astype(int)
        iy = np.rint((ys - y[0]) / (y[1] - y[0])).astype(int)
        ok = np.isfinite(xs) & (ix >= 0) & (ix < len(x)) & (iy >= 0) & (iy < len(y))
        rl1b = np.full(lat.shape, np.nan)
        rl1b[ok] = R[iy[ok], ix[ok]]
        k = ch - 1
        cg = [float(d[n][k]) for n in ("fk1_planck", "fk2_planck", "bc1_planck", "bc2_planck")]
        btg = d[f"geocatL1__channel_{ch}_brightness_temperature"].astype(float)
        m = np.isfinite(btg) & np.isfinite(rl1b)
        da = bt(rl1b, *cl) - btg
        db = bt(rl1b, *cg) - btg
        dr = rad(btg, *cg) - rl1b
        r[f"C{ch}"] = {"n": int(m.sum()), "coef_L1b": cl, "coef_geocat": cg,
                      "BT(L1b, coef L1b) - BT geocatL1, p1/p50/p99": [float(v) for v in np.nanpercentile(da[m], [1, 50, 99])],
                      "BT(L1b, coef geocat) - BT geocatL1, p1/p50/p99": [float(v) for v in np.nanpercentile(db[m], [1, 50, 99])],
                      "frac |BT(L1b, coef geocat) - BT geocat| <= 0,01 K": float(np.mean(np.abs(db[m]) <= 0.01)),
                      "frac |BT(L1b, coef L1b) - BT geocat| <= 0,01 K": float(np.mean(np.abs(da[m]) <= 0.01)),
                      "rad(BT geocat, coef geocat) - rad L1b, p50 (mW)": float(np.nanmedian(dr[m]))}
    out[h] = r
    print(h, {c: (round(v["BT(L1b, coef L1b) - BT geocatL1, p1/p50/p99"][1], 3),
                  round(v["BT(L1b, coef geocat) - BT geocatL1, p1/p50/p99"][1], 3),
                  round(v["frac |BT(L1b, coef geocat) - BT geocat| <= 0,01 K"], 3)) for c, v in r.items()}, flush=True)
with open(os.path.join(os.path.dirname(HERE), "resultados", "vuelta5_l1b.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, ensure_ascii=False)
