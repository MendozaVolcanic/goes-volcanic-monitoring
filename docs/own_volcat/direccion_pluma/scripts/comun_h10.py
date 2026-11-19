"""H10: piezas comunes (episodios REAV, ventanas, georreferencia VOLCAT, paralaje, regiones, escenas L1b).

Criterio: docs/own_volcat/direccion_pluma/criterio_H10_direccion_pluma_2026-11-19.md (commit 002640b).
Datos de entrada que reusa (fuera del repo, sesiones anteriores de la serie):
- Inventario de cuadros VOLCAT del 20-10 al 19-11 (inv_local.json + inv_new.json de beta73).
- PNG VOLCAT del sector Chile_Central_2_km (tres carpetas de scratch).
- Escenas L1b por ventana 83x94 (C11, C14, C15): cache del detector, cache de beta73 y cache propio.
"""
import os, sys, json, math
from datetime import datetime, timedelta
import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)
from src.process.parallax import parallax_shift  # noqa: E402

WORK = r"C:\Users\nmend\AppData\Local\Temp\claude\3eed1f0fb6f1d795\70cd3716-38bb-4bad-9d2f-cd60906a40d4\scratchpad\h10"
os.makedirs(WORK, exist_ok=True)
CACHE_OWN = os.path.join(WORK, "cache"); os.makedirs(CACHE_OWN, exist_ok=True)
DET = r"C:\Users\nmend\AppData\Local\Temp\claude\d6ea8719dcf88502\536a0873-47fb-4b33-9ee5-de0197c3f321\scratchpad\det"
B73 = r"C:\Users\nmend\AppData\Local\Temp\claude\f4710304fa6a9a5b\6cc950d4-5fd7-4e45-a0af-882008093b90\scratchpad\b73"
PNG_DIRS = [r"C:\Users\nmend\AppData\Local\Temp\claude\58c6c65788fdfd96\9c58fda3-6424-4269-8b61-4905a4c1d033\scratchpad\volcat_chillan_10min\png",
            r"C:\Users\nmend\AppData\Local\Temp\claude\3960f3d64983ed82\91527e04-4416-4efd-b41a-e8b2d704158c\scratchpad\volcat_extra\png",
            os.path.join(B73, "png_new")]

# Centro de emision (RAV 06-11) y cota de referencia del crater (criterio, seccion 1)
CLAT, CLON = -36.8677, -71.3793
ZC_KM = 3.2

# Episodios REAV (criterio, seccion 2). (id, jornada, inicio UTC, fin UTC, altura sobre crater m, azimut o None)
EP = [
    ("E1", "25-10", "2026-10-25 10:41", "2026-10-25 10:41", 1320, 135.0),
    ("E2", "25-10", "2026-10-25 11:27", "2026-10-25 11:34", 920, 135.0),
    ("E3", "25-10", "2026-10-25 13:15", "2026-10-25 13:15", 1540, 135.0),
    ("E4", "25-10", "2026-10-25 14:44", "2026-10-25 16:48", 1740, 135.0),
    ("E5", "25-10", "2026-10-25 16:23", "2026-10-25 21:16", 2300, 135.0),
    ("E6", "27-10", "2026-10-27 09:26", "2026-10-27 09:26", 2000, 315.0),
    ("E7", "27-10", "2026-10-27 10:26", "2026-10-27 10:26", 960, 22.5),
    ("E8", "27-10", "2026-10-27 11:04", "2026-10-27 15:00", 1640, 0.0),
    ("E9", "28-10", "2026-10-28 15:34", "2026-10-28 15:34", 1320, 315.0),
    ("E10", "28-10", "2026-10-28 17:38", "2026-10-28 17:38", 2200, 315.0),
    ("E11", "28-10b", "2026-10-28 20:32", "2026-10-28 20:32", 2440, None),
    ("E12", "28-10b", "2026-10-28 21:49", "2026-10-28 21:49", 2020, None),
    ("E13", "10-11", "2026-11-10 21:54", "2026-11-10 22:36", 2400, None),
    ("E14", "12-11", "2026-11-12 20:03", "2026-11-12 20:03", 400, None),
]
EXCL_CTRL = {"2026-10-25", "2026-10-27", "2026-10-28", "2026-10-29", "2026-11-10", "2026-11-12", "2026-11-16"}
DIA0, DIA1 = datetime(2026, 10, 20), datetime(2026, 11, 19, 23, 59)


def P(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


def ventana(e):
    return P(e[2]) - timedelta(minutes=20), P(e[3]) + timedelta(minutes=60)


def slots(e):
    a, b = ventana(e)
    t = a.replace(minute=(a.minute // 10) * 10)
    if t < a:
        t += timedelta(minutes=10)
    out = []
    while t <= b:
        out.append(t); t += timedelta(minutes=10)
    return out


# --- Inventario VOLCAT (beta73) ---------------------------------------------------------------
def _inv():
    res = json.load(open(os.path.join(B73, "inv_local.json"))) + json.load(open(os.path.join(B73, "inv_new.json")))
    out = {}
    for r in res:
        dt = datetime.fromisoformat(r["t"]).replace(tzinfo=None, second=0)
        out[dt] = r
    return out


INV = _inv()


def png_path(fn):
    for d in PNG_DIRS:
        p = os.path.join(d, fn)
        if os.path.exists(p):
            return p
    return None


def limpio(dt):
    """Regla _limpio de beta73: cuadro con barra, sin manto y sin objeto a < 50 km en +-60 min."""
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
        if not (DIA0 <= c <= DIA1) or f"{c:%Y-%m-%d}" in EXCL_CTRL:
            continue
        if limpio(c):
            out.append(c)
    return out


# --- Georreferencia del PNG VOLCAT (misma que paso3_objetos.py) --------------------------------
DP = math.degrees(72.80000305175781 / 206264.796875)
LAT0 = -31.8007698059082 + 36 * DP
LON0 = 278.9210815429688 - 360.0


def png_latlon(rows, cols):
    return LAT0 - np.asarray(rows) * DP, LON0 + np.asarray(cols) * DP


# --- Geometria local ---------------------------------------------------------------------------
KY = 110.574
KX = 111.320 * math.cos(math.radians(CLAT))


def km(lat, lon):
    """(este, norte) en km respecto del crater, plano tangente local."""
    return (np.asarray(lon) - CLON) * KX, (np.asarray(lat) - CLAT) * KY


def azimut(dx, dy):
    return (math.degrees(math.atan2(dx, dy)) + 360.0) % 360.0


def dang(a, b):
    d = abs((a - b + 180.0) % 360.0 - 180.0)
    return d


def media_circ(az):
    az = np.radians(np.asarray(az, float))
    s, c = np.sin(az).mean(), np.cos(az).mean()
    return (math.degrees(math.atan2(s, c)) + 360.0) % 360.0, float(np.hypot(s, c))


def corregir_p0(lat, lon, h_km):
    """P0: el PNG esta en geometria ABI sin corregir; lleva cada pixel a su posicion real."""
    return parallax_shift(lat, lon, h_km * 1000.0)


def vector_paralaje(h_km):
    """Corrimiento aparente (este, norte) en km de algo a h km s.n.m. sobre el crater (real -> aparente)."""
    la, lo = parallax_shift(CLAT, CLON, h_km * 1000.0)
    dx, dy = km(la, lo)
    return -float(dx), -float(dy)


# --- Escenas L1b (ventana 83x94, misma del detector) -------------------------------------------
_ll = np.load(os.path.join(DET, "latlon.npz"))
LAT, LON = _ll["lat"], _ll["lon"]
XE, YN = km(LAT, LON)


def k(dt):
    return f"{dt:%Y%m%d_%H%M}"


def escena(dt):
    """dict b11, b14, b15 (K) o None. Busca en cache del detector, de beta73 y propio."""
    p = os.path.join(DET, "cache", k(dt) + ".npz")
    if os.path.exists(p):
        z = np.load(p); return {b: z[b].astype("float64") for b in ("b11", "b14", "b15")}
    p = os.path.join(B73, "cache", k(dt) + ".npz")
    if os.path.exists(p):
        z = np.load(p)
        if all(f"bt{b}" in z for b in (11, 14, 15)):
            return {f"b{b}": z[f"bt{b}"].astype("float64") for b in (11, 14, 15)}
    p = os.path.join(CACHE_OWN, k(dt) + ".npz")
    if os.path.exists(p):
        z = np.load(p); return {b: z[b].astype("float64") for b in ("b11", "b14", "b15")}
    return None


def cuna(az, h_km, r0=2.0, r1=15.0, semi=22.5):
    """Mascara en la grilla ABI de la cuña real (az +- semi, r0..r1 km) llevada a su posicion aparente."""
    sx, sy = vector_paralaje(h_km)
    dx, dy = XE - sx, YN - sy           # posicion real de cada pixel aparente
    r = np.hypot(dx, dy)
    a = (np.degrees(np.arctan2(dx, dy)) + 360.0) % 360.0
    return (r >= r0) & (r <= r1) & (np.abs((a - az + 180.0) % 360.0 - 180.0) <= semi)
