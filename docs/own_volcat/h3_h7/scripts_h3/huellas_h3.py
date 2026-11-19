"""H3, paso 2a: huellas VOLCAT de los cuadros positivos de los tres casos, en la grilla ABI de la ventana.

Decodificacion = la de pruebaA_28oct.py (misma que paso3_objetos / huellas.py): pixel con ceniza = pixel que
volcat_colorbar.classify_pixels asigna a un bloque de la barra Ash_Height (saturacion >= 0,2), dentro de la
zona util del mapa (VALIDO) y a <= 50 km del crater; llevado a la grilla ABI por vecino mas cercano. Sin
dilatar. Cuadros con < 3 px de huella en la ventana: descartados antes de medir.
Salida: h3/huellas_h3.npz (clave YYYYMMDD_HHMM) y h3/huellas_h3.json (conteos, alturas, archivo PNG).
"""
import os, sys, json
import numpy as np
import pandas as pd
from PIL import Image
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
PR = r"C:\Users\nmend\AppData\Local\Temp\claude\3960f3d64983ed82\91527e04-4416-4efd-b41a-e8b2d704158c\scratchpad\pruebas"
sys.path.insert(0, PR)
import paso3_objetos as p  # noqa: E402  (fija LAT0, LON0, dp, VALIDO, hav, CHI; importa volcat_colorbar del repo)
from paso3_objetos import vc  # noqa: E402

DET = r"C:\Users\nmend\AppData\Local\Temp\claude\d6ea8719dcf88502\536a0873-47fb-4b33-9ee5-de0197c3f321\scratchpad\det"
PNG_OCT = r"C:\Users\nmend\AppData\Local\Temp\claude\3960f3d64983ed82\91527e04-4416-4efd-b41a-e8b2d704158c\scratchpad\volcat_extra\png"
PNG_NOV = r"C:\Users\nmend\AppData\Local\Temp\claude\58c6c65788fdfd96\9c58fda3-6424-4269-8b61-4905a4c1d033\scratchpad\volcat_chillan_10min\png"
ll = np.load(os.path.join(DET, "latlon.npz")); LAT, LON = ll["lat"], ll["lon"]
RR = np.rint((p.LAT0 - LAT) / p.dp).astype(int); CC = np.rint((LON - p.LON0) / p.dp).astype(int)
rr, cc = np.mgrid[0:755, 0:1000]
NEAR50 = p.hav(p.LAT0 - rr * p.dp, p.LON0 + cc * p.dp, *p.CHI) <= 50


def casos():
    c = {1: [datetime(2026, 10, 28, 22, 40), datetime(2026, 10, 28, 23, 0), datetime(2026, 10, 28, 23, 20),
             datetime(2026, 10, 28, 23, 40)],
         2: [datetime(2026, 10, 29, 1, 0), datetime(2026, 10, 29, 1, 10), datetime(2026, 10, 29, 1, 20)]}
    t = pd.read_csv(os.path.join(DET, "volcat", "cuadros_10min.csv"))
    pos = t[(t.toca_crater_10km == 1) & t.slot_utc.str.startswith("2026-11-14")].slot_utc
    c[3] = [datetime.strptime(s, "%Y-%m-%d %H:%M") for s in pos]
    return c


def png_for(dt):
    tag = f"GOES-19.ABI.{dt:%Y-%m-%d}.{dt:%H-%M}-"
    for d in (PNG_OCT, PNG_NOV):
        if not os.path.isdir(d):
            continue
        hits = [f for f in os.listdir(d) if f.startswith(tag) and "Ash_Height" in f]
        if hits:
            return os.path.join(d, sorted(hits)[0])
    return None


def huella(fn):
    a = np.asarray(Image.open(fn).convert("RGB"), dtype="float64"); hmap = int(vc.MAP_FRAC * a.shape[0])
    bins = vc.palette_bins(a[hmap:])
    if bins is None:
        return None, None
    m = a[:hmap]; cm = vc._saturation(m) >= 0.2
    ok = np.zeros(cm.shape, bool); mid = np.full(cm.shape, np.nan)
    if cm.any():
        c = vc.classify_pixels(m[cm], bins); ok[cm] = c["ok"]
        mid[cm] = (np.asarray(c["lo_km"]) + np.asarray(c["hi_km"])) / 2
    ok &= p.VALIDO[:hmap] & NEAR50[:hmap]
    hv = np.zeros(LAT.shape, bool); hh = np.full(LAT.shape, np.nan)
    ins = (RR >= 0) & (RR < hmap) & (CC >= 0) & (CC < a.shape[1])
    hv[ins] = ok[RR[ins], CC[ins]]; hh[ins] = np.where(ok[RR[ins], CC[ins]], mid[RR[ins], CC[ins]], np.nan)
    return hv, hh


if __name__ == "__main__":
    out, meta = {}, {}
    for caso, dts in casos().items():
        for dt in dts:
            k = f"{dt:%Y%m%d_%H%M}"; fn = png_for(dt)
            if fn is None:
                meta[k] = {"caso": caso, "estado": "sin_png"}; print(k, "sin_png"); continue
            hv, hh = huella(fn)
            if hv is None:
                meta[k] = {"caso": caso, "estado": "sin_barra", "png": fn}; print(k, "sin barra"); continue
            n = int(hv.sum())
            est = "ok" if n >= 3 else "descartado_<3px"
            meta[k] = {"caso": caso, "estado": est, "n_px": n, "png": os.path.basename(fn),
                       "altura_med_km": float(np.nanmedian(hh[hv])) if n else None}
            out[k] = hv
            print(k, caso, est, n, meta[k]["altura_med_km"])
    np.savez_compressed(os.path.join(HERE, "huellas_h3.npz"), **out)
    json.dump(meta, open(os.path.join(HERE, "huellas_h3.json"), "w"), indent=1)
