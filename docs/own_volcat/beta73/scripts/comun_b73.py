"""beta73: piezas comunes (positivos, estratos, candidatos de control, carga de escenas).

Criterio: docs/own_volcat/beta73/criterio_beta73_2026-11-19.md. Reutiliza el formato de escena de H3
(npz por scan con rad, bt y coeficientes Planck de cada NetCDF L1b, bandas C10, C11, C14, C15) y lee
primero el cache de H3, despues el propio.
"""
import os, json
import numpy as np
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # .../b73
CACHE = os.path.join(HERE, "cache"); os.makedirs(CACHE, exist_ok=True)
H3 = r"C:\Users\nmend\AppData\Local\Temp\claude\caac88451b34493f\bd33fd70-a478-403d-be84-fcf2fda5792e\scratchpad\h3"
CACHE_H3 = os.path.join(H3, "cache")
DET = r"C:\Users\nmend\AppData\Local\Temp\claude\d6ea8719dcf88502\536a0873-47fb-4b33-9ee5-de0197c3f321\scratchpad\det"
PNG_DIRS = [r"C:\Users\nmend\AppData\Local\Temp\claude\58c6c65788fdfd96\9c58fda3-6424-4269-8b61-4905a4c1d033\scratchpad\volcat_chillan_10min\png",
            r"C:\Users\nmend\AppData\Local\Temp\claude\3960f3d64983ed82\91527e04-4416-4efd-b41a-e8b2d704158c\scratchpad\volcat_extra\png",
            os.path.join(HERE, "png_new")]
BANDS = (10, 11, 14, 15)
EXCL_DIAS = {"2026-10-28", "2026-10-29"}
DIA0, DIA1 = datetime(2026, 10, 20), datetime(2026, 11, 19)


def k(dt):
    return f"{dt:%Y%m%d_%H%M}"


def _inv():
    res = json.load(open(os.path.join(HERE, "inv_local.json"))) + json.load(open(os.path.join(HERE, "inv_new.json")))
    out = {}
    for r in res:
        dt = datetime.fromisoformat(r["t"]).replace(tzinfo=None, second=0)
        out[dt] = r
    return out


INV = _inv()


def png(dt):
    fn = INV[dt]["fn"]
    for d in PNG_DIRS:
        p = os.path.join(d, fn)
        if os.path.exists(p):
            return p
    return None


def es_positivo(r):
    return bool(r["barra"]) and bool(r["anc"]) and not r["manto"]


def positivos():
    """(dt, estrato) de los cuadros positivos fuera de 28 y 29-10. Estrato N si cenit >= 80, D si no."""
    out = []
    for dt, r in sorted(INV.items()):
        if f"{dt:%Y-%m-%d}" in EXCL_DIAS or not es_positivo(r):
            continue
        out.append((dt, "N" if r["sza"] >= 80 else "D"))
    return out


def _limpio(dt):
    r = INV.get(dt)
    if r is None or not r["barra"] or r["manto"] or r["n50"] > 0:
        return False
    for m in range(-60, 61, 10):
        q = INV.get(dt + timedelta(minutes=m))
        if q is not None and (q["n50"] > 0 or q["manto"]):
            return False
    return True


def candidatos(dt):
    out = []
    for dd in range(-10, 11):
        if dd == 0:
            continue
        c = dt + timedelta(days=dd)
        if not (DIA0 <= c.replace(hour=0, minute=0) <= DIA1) or f"{c:%Y-%m-%d}" in EXCL_DIAS:
            continue
        if _limpio(c):
            out.append(c)
    return out


def path(dt):
    for d in (CACHE_H3, CACHE):
        p = os.path.join(d, k(dt) + ".npz")
        if os.path.exists(p):
            return p
    return None


def load(dt):
    p = path(dt)
    if p is None:
        return None
    z = np.load(p)
    d = {b: z[f"bt{b}"].astype("float64") for b in BANDS}
    d["rad"] = {b: z[f"rad{b}"].astype("float64") for b in BANDS}
    d["co"] = {b: tuple(z[f"co{b}"]) for b in BANDS}
    return d


def empirica(dt):
    """E: por pixel, mediana de las 3 escenas mas tibias en BT11 (C14) entre los candidatos del mismo minuto;
    cuatro bandas de esas mismas escenas. Misma regla que comun_h3.empirica. Devuelve (dict, n_escenas)."""
    esc = [load(c) for c in candidatos(dt)]
    esc = [e for e in esc if e is not None]
    if len(esc) < 5:
        return None, len(esc)
    s14 = np.stack([e[14] for e in esc]); s14 = np.where(np.isfinite(s14), s14, -1e9)
    idx = np.argsort(-s14, axis=0)[:3]
    out = {}
    for b in BANDS:
        st = np.stack([e[b] for e in esc])
        out[b] = np.median(np.take_along_axis(st, idx, axis=0), axis=0)
    return out, len(esc)


if __name__ == "__main__":
    pos = positivos(); need = set()
    for dt, e in pos:
        c = candidatos(dt)
        print(k(dt), e, "candidatos", len(c))
        need.add(dt); need.update(c)
    falt = sorted(d for d in need if path(d) is None)
    print("positivos", len(pos), "N", sum(e == "N" for _, e in pos), "| escenas necesarias", len(need), "faltan", len(falt))
    open(os.path.join(HERE, "escenas_faltan.txt"), "w").write("\n".join(k(d) for d in falt))
