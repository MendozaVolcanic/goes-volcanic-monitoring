"""Piezas comunes de H3 (casos, carga de escenas, pareo de control por BT11, referencia empirica E)."""
import os, json
import numpy as np
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
DET = r"C:\Users\nmend\AppData\Local\Temp\claude\d6ea8719dcf88502\536a0873-47fb-4b33-9ee5-de0197c3f321\scratchpad\det"
ll = np.load(os.path.join(DET, "latlon.npz")); LAT, LON = ll["lat"], ll["lon"]
BANDS = (10, 11, 14, 15)
HUE = dict(np.load(os.path.join(HERE, "huellas_h3.npz")))
META = json.load(open(os.path.join(HERE, "huellas_h3.json")))
CAND = {1: [(2026, 10, d) for d in (26, 27, 30, 31)] + [(2026, 11, d) for d in range(1, 7)],
        3: [(2026, 11, d) for d in (1, 2, 3, 4, 5, 6, 9, 12, 13, 15)]}
CAND[2] = CAND[1]


def k(dt):
    return f"{dt:%Y%m%d_%H%M}"


def load(dt):
    p = os.path.join(CACHE, k(dt) + ".npz")
    if not os.path.exists(p):
        return None
    z = np.load(p)
    d = {b: z[f"bt{b}"].astype("float64") for b in BANDS}
    d["rad"] = {b: z[f"rad{b}"].astype("float64") for b in BANDS}
    d["co"] = {b: tuple(z[f"co{b}"]) for b in BANDS}
    return d


def positivos():
    out = []
    for kk, m in sorted(META.items()):
        dt = datetime.strptime(kk, "%Y%m%d_%H%M")
        out.append((m["caso"], dt, m))
    return out


def candidatos(caso, dt):
    return [dt.replace(year=y, month=mo, day=d) for (y, mo, d) in CAND[caso]]


def pareo(caso, dt, hv):
    """Control = dia candidato con la mediana de BT11 (C14) sobre la huella mas cercana a la del positivo."""
    s = load(dt); m0 = float(np.nanmedian(s[14][hv]))
    filas = []
    for c in candidatos(caso, dt):
        sc = load(c)
        if sc is None:
            filas.append((c, None)); continue
        filas.append((c, float(np.nanmedian(sc[14][hv])) - m0))
    ok = [(c, d) for c, d in filas if d is not None]
    best = min(ok, key=lambda x: abs(x[1])) if ok else (None, None)
    return m0, best, filas


def empirica(caso, dt):
    """E: por pixel, mediana de las 3 escenas mas tibias en BT11 (C14) entre los dias candidatos al mismo
    minuto; las cuatro bandas de esas mismas escenas. Devuelve BT por banda y n escenas usadas."""
    esc = [load(c) for c in candidatos(caso, dt)]
    esc = [e for e in esc if e is not None]
    s14 = np.stack([e[14] for e in esc]); s14 = np.where(np.isfinite(s14), s14, -1e9)
    idx = np.argsort(-s14, axis=0)[:3]
    out = {}
    for b in BANDS:
        st = np.stack([e[b] for e in esc])
        out[b] = np.median(np.take_along_axis(st, idx, axis=0), axis=0)
    return out, len(esc)
