"""Prueba A (paralaje) sobre el episodio del 28-10. Criterio: criterio_pruebaA_28oct_2026-11-18.md."""
import os, sys, json, numpy as np
from datetime import datetime
from PIL import Image
import paso3_objetos as p
from paso3_objetos import vc
DET = r"C:\Users\nmend\AppData\Local\Temp\claude\d6ea8719dcf88502\536a0873-47fb-4b33-9ee5-de0197c3f321\scratchpad\det"
sys.path.insert(0, DET)
import comun as C
from variantes_mascara import referencia
PNG = r"C:\Users\nmend\AppData\Local\Temp\claude\3960f3d64983ed82\91527e04-4416-4efd-b41a-e8b2d704158c\scratchpad\volcat_extra\png"
ll = np.load(os.path.join(DET, "latlon.npz")); LAT, LON = ll["lat"], ll["lon"]
RR = np.rint((p.LAT0 - LAT) / p.dp).astype(int); CC = np.rint((LON - p.LON0) / p.dp).astype(int)
rr, cc = np.mgrid[0:755, 0:1000]
NEAR50 = p.hav(p.LAT0 - rr * p.dp, p.LON0 + cc * p.dp, *p.CHI) <= 50
res = {r[1][:16]: r for r in json.load(open("paso4_res.json"))}
S = 5
fr = {"btd": [], "dT": []}; alturas = []
for hh in ("22:40", "23:00", "23:20", "23:40"):
    fn = res["2026-10-28T" + hh][0]
    a = np.asarray(Image.open(os.path.join(PNG, fn)).convert("RGB"), dtype="float64"); hmap = int(vc.MAP_FRAC * a.shape[0])
    bins = vc.palette_bins(a[hmap:]); m = a[:hmap]; cm = vc._saturation(m) >= 0.2
    ok = np.zeros(cm.shape, bool); mid = np.full(cm.shape, np.nan)
    c = vc.classify_pixels(m[cm], bins); ok[cm] = c["ok"]; mid[cm] = (np.asarray(c["lo_km"]) + np.asarray(c["hi_km"])) / 2
    ok &= p.VALIDO[:hmap] & NEAR50[:hmap]
    h = float(np.nanmedian(mid[ok])); alturas.append(h)
    hv = np.zeros(LAT.shape, bool); ins = (RR >= 0) & (RR < hmap) & (CC >= 0) & (CC < 1000); hv[ins] = ok[RR[ins], CC[ins]]
    dt = datetime(2026, 10, 28, int(hh[:2]), int(hh[3:]))
    sc = C.load(dt); r = referencia(dt, 10, 3)
    btd = sc["b14"] - sc["b15"]; dT = sc["b14"] - r["b14"]
    gb = np.full((2 * S + 1, 2 * S + 1), np.nan); gt = gb.copy()
    ys, xs = np.nonzero(hv)
    for iy, dy in enumerate(range(-S, S + 1)):
        for ix, dx in enumerate(range(-S, S + 1)):
            y2, x2 = ys + dy, xs + dx; k = (y2 >= 0) & (y2 < hv.shape[0]) & (x2 >= 0) & (x2 < hv.shape[1])
            if k.sum() == 0: continue
            gb[iy, ix] = np.mean(btd[y2[k], x2[k]] < -1); gt[iy, ix] = np.mean(dT[y2[k], x2[k]] < -2)
    fr["btd"].append(gb); fr["dT"].append(gt)
    print(hh, "px huella", int(hv.sum()), "altura VOLCAT mediana %.1f km" % h, "frac(0,0) btd %.2f dT %.2f" % (gb[S, S], gt[S, S]))
H = float(np.median(alturas)); dy_esp = 0.93 * H / 2.84
print("altura mediana %.1f km -> dy esperado %.1f filas al sur" % (H, dy_esp))
np.set_printoptions(precision=2, suppress=True, linewidth=200)
for k, nombre in (("btd", "BTD < -1 K"), ("dT", "dBT11 < -2 K")):
    g = np.nanmean(np.stack(fr[k]), 0)
    iy, ix = np.unravel_index(np.nanargmax(g), g.shape); dy, dx = iy - S, ix - S
    print(f"\n{nombre}: filas dy -5 (N) .. +5 (S), columnas dx -5 (O) .. +5 (E)\n", g)
    mx, c0 = g[iy, ix], g[S, S]
    print(f" maximo {mx:.2f} en dy={dy} dx={dx}; en (0,0) {c0:.2f}")
    fuerte = mx >= 0.30 and mx >= 2 * c0
    if not fuerte: v = "FALSA H4 en este episodio"
    elif dy >= 1 and abs(dx) <= 2 and abs(dy - dy_esp) <= 1: v = "REABRE H4 solo para este episodio"
    else: v = "corrimiento no explicado por paralaje"
    print(" veredicto:", v)
