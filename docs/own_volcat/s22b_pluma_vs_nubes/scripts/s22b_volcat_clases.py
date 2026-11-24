r"""S22b: clase de cada cuadro de VOLCAT (P, N u otro) con la MISMA regla de H9 (calor_rayos/scripts/analisis_calor.py
sobre el inventario de beta73/scripts/inventario.py), para los PNG guardados en D: después del 19-11.

Regla (copiada, no reinterpretada):
- píxel con ceniza = píxel que volcat_colorbar.classify_pixels asigna a la barra (saturación >= 0,2), en la zona útil
  del mapa (fuera el título, filas < 70, y las esquinas de abajo con globo y logos);
- objeto = componente conexa de 8 vecinos; anclado si toca el disco de 10 km de Chillán (-36,86, -71,38) y tiene de 4
  a 500 píxeles; manto si algún objeto pasa MAX_SECTOR_FRAC del mapa o hay uno de más de 500 píxeles a <= 50 km;
- P = barra leída, con objeto anclado y sin manto;
- N = barra leída, sin manto y sin ningún píxel de ceniza a <= 50 km, ni en ese cuadro ni en los guardados a ±60 min;
- otro = el resto.
Diferencia conocida con el inventario original: beta73 sacaba además de la zona útil los píxeles que se clasifican en
más del 20 % de los cuadros (sobreimpresos fijos); según su propio comentario, en las filas 70 a 640 del mapa no hay
ninguno. Aquí se comprueba contra frames_calor.csv en los días que están en las dos fuentes (subcomando `validar`).

Los PNG son de SSEC (licencia restringida): se leen de D:; al repo sólo va la clase por cuadro (como frames_calor.csv).
Uso: python -I s22b_volcat_clases.py validar | clasificar
"""
import csv
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "h29_pluma_0811", "scripts"))
import h29_comun as C29  # noqa: E402  (decodifica_png, proyección del PNG, hav)

PNG = r"D:\goes_notas\s22\volcat_png\Chile_Central_2_km\frames"
PNG_DIRS = [PNG, r"D:\goes_notas\s22\s22b\volcat_png\frames"]   # la segunda: desde 24-11 11:50 (s22b_volcat_bajar.py)
FRAMES_CALOR = os.path.join(OV, "calor_rayos", "resultados", "frames_calor.csv")
CHI = (-36.86, -71.38)
_rr, _cc = np.mgrid[0:755, 0:1000]
DCHI = C29.hav(C29.LAT0 - _rr * C29.DP, C29.LON0 + _cc * C29.DP, *CHI)
SEED, NEAR50 = DCHI <= 10, DCHI <= 50


def uno(fn):
    from scipy import ndimage
    vc = C29.vc
    dt = C29.dt_de(fn)
    ok, _, barra = C29.decodifica_png(fn)
    if not barra:
        return dt, dict(barra=False, manto=None, anc=[], n50=0)
    h, w = ok.shape
    lab, n = ndimage.label(ok, structure=np.ones((3, 3), int))
    tam = np.bincount(lab.ravel(), minlength=n + 1)
    tam[0] = 0
    manto = bool((tam / ok.size > vc.MAX_SECTOR_FRAC).any())
    ids = np.unique(lab[SEED[:h, :w] & ok])
    ids = ids[ids > 0]
    anc = [int(tam[i]) for i in ids if 4 <= tam[i] <= 500]
    near = np.unique(lab[NEAR50[:h, :w] & ok])
    near = near[near > 0]
    grande = bool(any(tam[i] > 500 for i in near))
    return dt, dict(barra=True, manto=bool(manto or grande), anc=anc, n50=int((ok & NEAR50[:h, :w]).sum()))


def inventario(dias):
    fs = {}
    for carpeta in PNG_DIRS:                        # el mismo nombre en las dos carpetas es el mismo cuadro
        if os.path.isdir(carpeta):
            for f in os.listdir(carpeta):
                if f.endswith(".png") and "_annot" not in f and f[:10] in dias:
                    fs.setdefault(f, os.path.join(carpeta, f))
    fs = [fs[k] for k in sorted(fs)]
    with ProcessPoolExecutor(3) as ex:
        res = list(ex.map(uno, fs, chunksize=8))
    return {dt: r for dt, r in res}


def clases(inv):
    out = {}
    for dt, r in inv.items():
        if r["barra"] and r["anc"] and not r["manto"]:
            c = "P"
        else:
            c = "N"
            if not r["barra"] or r["manto"] or r["n50"] > 0:
                c = "otro"
            else:
                for m in range(-60, 61, 10):
                    q = inv.get(dt + timedelta(minutes=m))
                    if q is not None and (q["n50"] > 0 or q["manto"]):
                        c = "otro"
                        break
        out[dt] = c
    return out


def validar():
    dias = ["2026-10-28", "2026-11-10", "2026-11-11", "2026-11-14"]
    cl = clases(inventario(set(dias)))
    ref = {}
    with open(FRAMES_CALOR, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ref[datetime.strptime(r["dt"][:16], "%Y-%m-%d %H:%M")] = r["clase"]
    comun = [t for t in cl if t in ref]
    tab = {}
    for t in comun:
        tab[(ref[t], cl[t])] = tab.get((ref[t], cl[t]), 0) + 1
    print("cuadros en las dos fuentes:", len(comun), "(PNG aquí:", len(cl), ")")
    for k in sorted(tab):
        print(f"  frames_calor {k[0]:5s} -> aquí {k[1]:5s}: {tab[k]}")
    dis = sorted(t for t in comun if ref[t] != cl[t])
    print("discrepancias:", [f"{t:%m-%d %H:%M} {ref[t]}->{cl[t]}" for t in dis][:40])


def clasificar():
    dias = {f"2026-11-{d:02d}" for d in (22, 23, 24)}
    inv = inventario(dias | {"2026-11-21"})          # el 21-11 sólo para la ventana de ±60 min de las 00:00 del 22
    cl = clases(inv)
    os.makedirs(RES, exist_ok=True)
    fn = os.path.join(RES, "volcat_clases_22a24nov.csv")
    with open(fn, "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["dt", "clase", "n_anc", "max_anc", "n50", "barra", "manto"])
        for dt in sorted(cl):
            if f"{dt:%Y-%m-%d}" not in dias:
                continue
            r = inv[dt]
            wr.writerow([f"{dt:%Y-%m-%d %H:%M}", cl[dt], len(r["anc"]), max(r["anc"]) if r["anc"] else 0, r["n50"],
                         r["barra"], r["manto"]])
    cnt = {}
    for dt, c in cl.items():
        if f"{dt:%Y-%m-%d}" in dias:
            cnt.setdefault(f"{dt:%Y-%m-%d}", {}).setdefault(c, 0)
            cnt[f"{dt:%Y-%m-%d}"][c] += 1
    print(fn)
    for d in sorted(cnt):
        print(d, cnt[d])


if __name__ == "__main__":
    {"validar": validar, "clasificar": clasificar}[sys.argv[1]]()
