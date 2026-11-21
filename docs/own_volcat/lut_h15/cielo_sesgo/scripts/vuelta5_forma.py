r"""Vuelta 5, prueba 2 y 3 (EXPLORACIÓN, cuadros 1 a 5, no decide): forma espacial y temporal del desfase implícito
del cielo despejado de C14 (vuelta 3) en nube tenue (0,05 <= ε < 0,3). Mapa por celda de 0,25°, estabilidad entre
cuadros, autocorrelación, saltos en bordes de celda GFS, correlación con SST CMC, superficie GFS, SST − superficie
GFS, BT despejada, lat/lon, distancia a nube espesa y textura de BT14. Escribe ../resultados/vuelta5_forma.txt y
vuelta5_mapa_desfase_c14.png.
"""
import os, sys
import netCDF4
import numpy as np
from scipy.ndimage import distance_transform_edt, uniform_filter
from scipy.stats import spearmanr
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vuelta3_eps11 as V3  # noqa: E402
CS = V3.CS
RESD = os.path.join(os.path.dirname(HERE), "resultados")
SST = netCDF4.Dataset(r"D:\goes_cache\volcat_test_mauna_loa\ext\mauna-loa_g17-conus_nov2022_r20260709-volcat-code-ancil\ancillary\sst\20221128120000-CMC-L4_GHRSST-SSTfnd-CMC0.1deg-GLOB-v02.0-fv03.0.nc")
sst_lat, sst_lon = SST["lat"][:].astype(float), SST["lon"][:].astype(float)
SSTA = SST["analysed_sst"][0].astype(float).filled(np.nan)
G = dict(np.load(r"D:\goes_cache\cielo_sesgo\gfs_sfc.npz"))
lin = []
P = lambda *a: lin.append(" ".join(str(x) for x in a))  # noqa: E731

mapas, PIX = {}, {k: [] for k in ("d14", "d15", "sst", "tsfc", "clr", "lat", "lon", "dist", "tex", "cellgfs", "r", "c", "fr")}
for i, h in enumerate(CS.E.ELIGE):
    c = CS.Cuadro(h)
    X = V3.por_cuadro(c)
    d = c.d
    lat = d["geocatL1__pixel_latitude"].astype(float); lon = d["geocatL1__pixel_longitude"].astype(float)
    ev = c.ev
    thin = (np.isfinite(ev) & (ev >= 0.05) & (ev < 0.3)).ravel() & np.isfinite(X["d14"])
    iy = np.clip(np.rint((lat - sst_lat[0]) / 0.1).astype(int), 0, len(sst_lat) - 1)
    ix = np.clip(np.rint((lon - sst_lon[0]) / 0.1).astype(int), 0, len(sst_lon) - 1)
    sst = SSTA[iy, ix]
    hh = int(h[:2]) + int(h[2:4]) / 60.0; w = (hh - 6) / 6
    gy = d["geocatRTM__nwp_y_index"].astype(int); gx = d["geocatRTM__nwp_x_index"].astype(int)
    tsfc = (1 - w) * G["gfs.22112718_F012.hdf|tsfc"][gy, gx] + w * G["gfs.22112800_F012.hdf|tsfc"][gy, gx]
    espesa = np.isfinite(ev) & (ev >= 0.5)
    dist = distance_transform_edt(~espesa)
    b14 = c.obs[14]
    tex = np.sqrt(np.maximum(uniform_filter(b14 ** 2, 3) - uniform_filter(b14, 3) ** 2, 0))
    rr, cc = np.indices(CS.SH)
    for k, v in (("d14", X["d14"]), ("d15", X["d15"]), ("sst", sst), ("tsfc", tsfc), ("clr", c.clr[14]), ("lat", lat),
                 ("lon", lon), ("dist", dist), ("tex", tex), ("cellgfs", gy * 1000 + gx), ("r", rr), ("c", cc),
                 ("fr", np.full(CS.SH, i))):
        PIX[k].append(np.asarray(v, float).ravel()[thin])
    # mapa por celda de 0,25°
    cy = np.floor(lat.ravel()[thin] / 0.25).astype(int); cx = np.floor(lon.ravel()[thin] / 0.25).astype(int)
    key = cy * 10000 + cx
    dd = X["d14"][thin]
    u, inv = np.unique(key, return_inverse=True)
    cnt = np.bincount(inv)
    med = np.array([np.median(dd[inv == j]) for j in range(len(u))])
    mapas[h] = {int(k): float(m) for k, m, n in zip(u, med, cnt) if n >= 20}
X = {k: np.concatenate(v) for k, v in PIX.items()}
P("pixeles tenues (cuadros 1 a 5):", len(X["d14"]))
P("desfase C14 p5/50/95:", np.percentile(X["d14"], [5, 50, 95]).round(2), " C15:", np.percentile(X["d15"][np.isfinite(X["d15"])], [5, 50, 95]).round(2))
X["sst_menos_tsfc"] = X["sst"] - X["tsfc"]
P("SST CMC - T superficie GFS (en pixeles tenues) p5/50/95:", np.nanpercentile(X["sst_menos_tsfc"], [5, 50, 95]).round(2))
P("Correlacion de rangos con el desfase C14 (pixel):")
for k in ("sst", "tsfc", "sst_menos_tsfc", "clr", "lat", "lon", "dist", "tex"):
    m = np.isfinite(X[k])
    P(f"  {k:16s} {spearmanr(X['d14'][m], X[k][m]).correlation:+.3f}")
P("Desfase por distancia a nube espesa (eps >= 0,5), mediana:")
for a, b in ((0, 2), (2, 5), (5, 10), (10, 20), (20, 1e9)):
    q = (X["dist"] >= a) & (X["dist"] < b)
    if q.sum() > 200:
        P(f"  [{a},{b}) px  n={q.sum()} d14 {np.median(X['d14'][q]):+.2f}")
P("Desfase por textura de BT14 (sd 3x3), mediana:")
for a, b in ((0, .2), (.2, .5), (.5, 1), (1, 2), (2, 99)):
    q = (X["tex"] >= a) & (X["tex"] < b)
    if q.sum() > 200:
        P(f"  [{a},{b}) K  n={q.sum()} d14 {np.median(X['d14'][q]):+.2f}")
# estabilidad entre cuadros (mapas de 0,25°)
hs = CS.E.ELIGE
cors = []
for a, b in zip(hs[:-1], hs[1:]):
    kk = sorted(set(mapas[a]) & set(mapas[b]))
    if len(kk) > 10:
        cors.append((a, b, len(kk), spearmanr([mapas[a][k] for k in kk], [mapas[b][k] for k in kk]).correlation))
P("Estabilidad del mapa de 0,25° entre cuadros consecutivos (celdas >= 20 px):",
  [(a[:4], b[:4], n, round(r, 3)) for a, b, n, r in cors])
# autocorrelación espacial de celdas vecinas (cuadro 1)
m1 = mapas[hs[0]]
pares1 = [(m1[k], m1[k + 1]) for k in m1 if k + 1 in m1] + [(m1[k], m1[k + 10000]) for k in m1 if k + 10000 in m1]
pares4 = [(m1[k], m1[k + 4]) for k in m1 if k + 4 in m1] + [(m1[k], m1[k + 40000]) for k in m1 if k + 40000 in m1]
for nom, pr in (("vecina 0,25°", pares1), ("a 1°", pares4)):
    if len(pr) > 10:
        a, b = np.array(pr).T
        P(f"Autocorrelacion espacial ({nom}), cuadro 1: n={len(pr)} rho={spearmanr(a, b).correlation:+.3f}")
# saltos en bordes de celda GFS (cuadro 1, vecinos horizontales)
fr0 = X["fr"] == 0
r0, c0, d0, g0 = X["r"][fr0].astype(int), X["c"][fr0].astype(int), X["d14"][fr0], X["cellgfs"][fr0]
idx = {(a, b): i for i, (a, b) in enumerate(zip(r0, c0))}
mismo, cruza = [], []
for i, (a, b) in enumerate(zip(r0, c0)):
    j = idx.get((a, b + 1))
    if j is not None:
        (mismo if g0[i] == g0[j] else cruza).append(abs(d0[i] - d0[j]))
P(f"Vecinos horizontales, cuadro 1: misma celda GFS n={len(mismo)} |dd14| med {np.median(mismo):.3f}; "
  f"cruzan borde n={len(cruza)} |dd14| med {np.median(cruza):.3f}")
with open(os.path.join(RESD, "vuelta5_forma.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lin) + "\n")
print("\n".join(lin))
# figura: mapa de 0,25° del cuadro 1 y del 5
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
for a, h in zip(ax, (hs[0], hs[-1])):
    m = mapas[h]
    ks = np.array(list(m)); v = np.array([m[k] for k in ks])
    la = (ks // 10000) * 0.25 + 0.125; lo = (ks % 10000 - (ks % 10000 > 5000) * 10000) * 0.25 + 0.125
    sc = a.scatter(lo, la, c=v, s=18, marker="s", cmap="RdBu_r", vmin=-2.5, vmax=2.5)
    a.set_title(f"{h[:2]}:{h[2:4]} UTC"); a.set_xlabel("lon"); a.set_ylabel("lat")
fig.colorbar(sc, ax=ax, label="desfase C14 (K), mediana por celda 0,25°")
fig.suptitle("Mauna Loa, nube tenue (0,05 ≤ εtot < 0,3): cielo despejado de 11 µm que usa VOLCAT menos geocatRTM")
fig.savefig(os.path.join(RESD, "vuelta5_mapa_desfase_c14.png"), dpi=80)
