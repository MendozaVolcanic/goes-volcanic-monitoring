"""H11: piezas comunes (rutas, pares, huellas, escenas, perfiles GFS, cielo empirico para la prueba de nube).

Criterio: docs/own_volcat/reproducir_volcat/criterio_H11_2026-11-19.md. Reutiliza sin editarlos los caches y
el modelo radiativo de H3 (rt.py, LUT, MT_CKD) y de beta73; todo de solo lectura.
"""
import os, sys, json
import numpy as np
from datetime import datetime, timedelta
from scipy import ndimage

# Los scratchpads originales se borraron el 20-11; la copia rescatada se elige con H11_H3, H11_B73 y H11_TRABAJO
# (ver LEEME_rescate_2026-11-20.md en la carpeta de notas h12_datos).
H3 = os.environ.get("H11_H3", r"C:\Users\nmend\AppData\Local\Temp\claude\caac88451b34493f\bd33fd70-a478-403d-be84-fcf2fda5792e\scratchpad\h3")
B73 = os.environ.get("H11_B73", r"C:\Users\nmend\AppData\Local\Temp\claude\f4710304fa6a9a5b\6cc950d4-5fd7-4e45-a0af-882008093b90\scratchpad\b73")
TRABAJO = os.environ.get("H11_TRABAJO", r"C:\Users\nmend\AppData\Local\Temp\claude\a2570b18d9d77a03\d3ce10df-b230-48d8-900a-293980f29716\scratchpad\rv")
RTDIR = os.path.join(TRABAJO, "rt_h11"); os.makedirs(RTDIR, exist_ok=True)
# Modelo radiativo (C2, 21-11-2026): el codigo sale del repo (h3_h7/scripts_h3, identico a la copia que habia en H3)
# y sus insumos de H3_RT_LBL (tabla de coeficientes) y H3_RT_DL (MT_CKD y SRF). Sin esas variables se buscan dentro
# de H3, igual que antes. Con la copia rescatada, que no trae dl: H3_RT_DL=D:\goes_cache\rt (ver README de own_volcat).
os.environ.setdefault("H3_RT_LBL", os.path.join(H3, "lbl"))
os.environ.setdefault("H3_RT_DL", os.path.join(H3, "dl"))
sys.path.insert(0, H3)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "h3_h7", "scripts_h3"))
import rt  # noqa: E402  (modelo de H3: capas, tau, Planck, cenit satelital)

_ll = np.load(os.path.join(TRABAJO, "latlon.npz")); LAT, LON = _ll["lat"], _ll["lon"]
SEC = 1.0 / np.cos(np.radians(rt.cenit_satelital(LAT, LON)))
BANDS = (10, 11, 14, 15)
CRATER = (-36.863, -71.377)   # Nevados de Chillan (GVP), solo para el estrato y la descripcion


def k(dt):
    return f"{dt:%Y%m%d_%H%M}"


def dtk(s):
    return datetime.strptime(s, "%Y%m%d_%H%M")


# ------------------------------------------------------------------ escenas y perfiles
def path_escena(dt):
    for d in (os.path.join(H3, "cache"), os.path.join(B73, "cache")):
        p = os.path.join(d, k(dt) + ".npz")
        if os.path.exists(p):
            return p
    return None


def load(dt):
    p = path_escena(dt)
    if p is None:
        return None
    z = np.load(p)
    d = {b: z[f"bt{b}"].astype("float64") for b in BANDS}
    d["rad"] = {b: z[f"rad{b}"].astype("float64") for b in BANDS}
    d["co"] = {b: tuple(float(c) for c in z[f"co{b}"]) for b in BANDS}
    return d


def hora_gfs(dt):
    return (dt + timedelta(minutes=30)).replace(minute=0, second=0, microsecond=0)


def path_gfs(dt):
    h = hora_gfs(dt)
    for d in (os.path.join(H3, "gfs"), os.path.join(B73, "gfs"), os.path.join(TRABAJO, "gfs_e2")):
        p = os.path.join(d, f"gfs_{h:%Y%m%d%H}.npz")
        if os.path.exists(p):
            return p
    return None


# ------------------------------------------------------------------ pares y huellas
_HU3 = dict(np.load(os.path.join(H3, "huellas_h3.npz")))
_HUB = dict(np.load(os.path.join(B73, "huellas_b73.npz")))
_P3 = json.load(open(os.path.join(H3, "pareo.json")))
_PB = json.load(open(os.path.join(B73, "pareo_b73.json")))
_INV = {}
for _r in json.load(open(os.path.join(B73, "inv_local.json"))) + json.load(open(os.path.join(B73, "inv_new.json"))):
    _INV[datetime.fromisoformat(_r["t"]).replace(tzinfo=None, second=0)] = _r


def pares():
    """Lista de pares ok. Si un positivo esta en H3 y en beta73, vale el de H3 (criterio)."""
    out, vistos = [], set()
    for p in _P3:
        if p["estado"] != "ok":
            continue
        hv = _HU3[p["pos"]].astype(bool)
        out.append({"pos": p["pos"], "ctrl": p["ctrl"], "origen": "H3", "caso": p["caso"], "hv": hv, "ash": hv.copy()})
        vistos.add(p["pos"])
    for p in _PB:
        if p["estado"] != "ok" or p["pos"] in vistos:
            continue
        out.append({"pos": p["pos"], "ctrl": p["ctrl"], "origen": "B73", "caso": None,
                    "hv": _HUB["h_" + p["pos"]].astype(bool), "ash": _HUB["a_" + p["pos"]].astype(bool)})
    return out


def descartados():
    d = [(p["pos"], "H3", p["estado"]) for p in _P3 if p["estado"] != "ok"]
    d += [(p["pos"], "B73", p["estado"]) for p in _PB if p["estado"] != "ok"]
    return d


def sza(dt):
    r = _INV.get(dt)
    if r is not None:
        return float(r["sza"])
    # 28 y 29-10 no estan en el inventario de beta73: cenit solar calculado (formula estandar NOAA)
    import math
    doy = dt.timetuple().tm_yday; hr = dt.hour + dt.minute / 60
    g = 2 * math.pi / 365 * (doy - 1 + (hr - 12) / 24)
    decl = 0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    tst = hr * 60 + eqt + 4 * CRATER[1]
    ha = math.radians(tst / 4 - 180); la = math.radians(CRATER[0])
    c = math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)
    return math.degrees(math.acos(max(-1, min(1, c))))


def zonas(hv, ash):
    """huella; anillo CF = 1 a 12 px del borde (Chebyshev) fuera de ceniza; anillo espectral = 2 a 6 px fuera de ceniza."""
    d12 = ndimage.binary_dilation(hv, np.ones((25, 25), bool))
    d6 = ndimage.binary_dilation(hv, np.ones((13, 13), bool))
    d1 = ndimage.binary_dilation(hv, np.ones((3, 3), bool))
    return {"h": hv, "cf": d12 & ~hv & ~ash, "an": d6 & ~d1 & ~ash}


# ------------------------------------------------------------------ cielo empirico (prueba de nube del anillo CF)
CAND_H3 = {1: [(2026, 10, d) for d in (26, 27, 30, 31)] + [(2026, 11, d) for d in range(1, 7)],
           3: [(2026, 11, d) for d in (1, 2, 3, 4, 5, 6, 9, 12, 13, 15)]}
CAND_H3[2] = CAND_H3[1]
EXCL_B73 = {"2026-10-28", "2026-10-29"}
DIA0, DIA1 = datetime(2026, 10, 20), datetime(2026, 11, 19)


def _limpio(dt):
    r = _INV.get(dt)
    if r is None or not r["barra"] or r["manto"] or r["n50"] > 0:
        return False
    for m in range(-60, 61, 10):
        q = _INV.get(dt + timedelta(minutes=m))
        if q is not None and (q["n50"] > 0 or q["manto"]):
            return False
    return True


def candidatos(par):
    dt = dtk(par["pos"])
    if par["origen"] == "H3":
        return [dt.replace(year=y, month=mo, day=d) for (y, mo, d) in CAND_H3[par["caso"]]]
    out = []
    for dd in range(-10, 11):
        c = dt + timedelta(days=dd)
        if dd == 0 or not (DIA0 <= c.replace(hour=0, minute=0) <= DIA1) or f"{c:%Y-%m-%d}" in EXCL_B73:
            continue
        if _limpio(c):
            out.append(c)
    return out


def bt11_empirico(par):
    esc = [load(c) for c in candidatos(par)]
    esc = [e[14] for e in esc if e is not None]
    if len(esc) < 5:
        return None, len(esc)
    s = np.sort(np.where(np.isfinite(np.stack(esc)), np.stack(esc), -1e9), axis=0)[::-1][:3]
    return np.median(s, axis=0), len(esc)
