r"""S27b: reglas comunes de la altura por rapidez (criterio_2026-11-25.md). Lo usan s27b_resolucion.py (estimación previa,
sin datos de pluma) y s27b_medir.py (medida).

Física. Un pulso de ceniza que sale del cráter en t0 y aparece en el anillo en ta, a una distancia d del cráter, avanzó
a d / (ta - t0). Si la pluma es pasiva, esa rapidez es la del viento a su altura. Comparada con el perfil de rapidez
del viento GFS, da las alturas compatibles. La distancia d depende de la altura supuesta, porque GOES-19 ve algo a h km
corrido hacia el sur (paralaje); por eso d se calcula para cada altura candidata, como el rumbo en S22c.

Incertidumbres que fija el criterio (§3): la emisión ocurrió entre el cuadro anterior y t0 (tiempo de viaje entre Δt y
Δt + 10 min); la posición de llegada vale más o menos un píxel (DELTA_KM); la rapidez del GFS vale más o menos
max(2 m/s, 25 %).
"""
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
REPO = os.path.abspath(os.path.join(OV, "..", ".."))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(OV, "s22c_altura_propia", "scripts"))
import s22c_medir as C22  # noqa: E402  (viento, rumbo, ZS, paralaje)
from src.process.parallax import parallax_shift  # noqa: E402

ZS = C22.ZS                       # 3,2 a 14 km cada 0,1 km, sobre el nivel del mar
SAT_LON = C22.SAT_LON
CLAT, CLON = C22.CLAT, C22.CLON   # cráter (el de S20b, H29, S22a y S22c)
KX, KY = C22.KX, C22.KY

# ---------- parámetros del criterio (§3) ----------
DELTA_KM = 2.8                    # un píxel ABI en Chillán en sentido N-S (2,8 km; E-O 2,1 km)
DT_EMISION_MIN = 10.0             # la emisión cae en algún momento de los 10 min antes del cuadro t0
ERR_V_ABS, ERR_V_REL = 2.0, 0.25  # error de la rapidez del GFS: max(2 m/s, 25 %)
TAU, VMIN_RUMBO = C22.TAU, C22.VMIN   # rumbo: 30 grados y viento de 3 m/s o más, como S22c
ANCHO_MAX = 3.0                   # restringe: banda de 3 km o menos, como S22c
H_SOMBRA, TOL_SOMBRA = 4.7, 0.5   # la verdad del 08-11 y su tolerancia
H_CAPA_ALTA = 8.0                 # "separa capas": la banda queda entera bajo 8 km (o entera sobre)


def corregir(lat, lon, h_km):
    """Posición real de algo que GOES-19 ve en (lat, lon) si está a h_km sobre el mar."""
    return parallax_shift(np.atleast_1d(np.asarray(lat, float)), np.atleast_1d(np.asarray(lon, float)),
                          h_km * 1000.0, sat_lon=SAT_LON)


def aparente(lat, lon, h_km):
    """Inversa de corregir: dónde ve GOES-19 algo que está en (lat, lon) a h_km (3 iteraciones de punto fijo)."""
    la0, lo0 = np.atleast_1d(np.asarray(lat, float)), np.atleast_1d(np.asarray(lon, float))
    la, lo = la0.copy(), lo0.copy()
    for _ in range(4):
        cla, clo = corregir(la, lo, h_km)
        la, lo = la - (cla - la0), lo - (clo - lo0)
    return la, lo


def dist_y_rumbo_por_h(lat, lon):
    """Para cada h de ZS: distancia mediana (km) y rumbo medio (grados) desde el cráter de los píxeles (lat, lon)
    vistos por GOES-19, corregidos por paralaje a h."""
    lat, lon = np.atleast_1d(lat).astype(float), np.atleast_1d(lon).astype(float)
    d = np.empty(len(ZS))
    r = np.empty(len(ZS))
    for i, h in enumerate(ZS):
        la, lo = corregir(lat, lon, h)
        az, dd = C22.az_dist(la, lo)
        d[i] = float(np.median(dd))
        r[i] = C22.media_circ(np.atleast_1d(az))[0]
    return d, r


def tolerancia_v(v):
    return np.maximum(ERR_V_ABS, ERR_V_REL * np.abs(v))


def intervalo_v(d_km, dt_min):
    """Rapidez observada posible (m/s) para cada h: d ± un píxel en un tiempo de viaje entre Δt y Δt + 10 min."""
    d_km = np.asarray(d_km, float)
    v_lo = np.maximum(d_km - DELTA_KM, 0.0) * 1000.0 / ((dt_min + DT_EMISION_MIN) * 60.0)
    v_hi = (d_km + DELTA_KM) * 1000.0 / (dt_min * 60.0)
    return v_lo, v_hi


def compat_rapidez(d_km, dt_min, V):
    """Máscara sobre ZS: la rapidez del GFS a h cae en el intervalo observado, ensanchado por su propio error."""
    v_lo, v_hi = intervalo_v(d_km, dt_min)
    return (V >= v_lo - tolerancia_v(v_lo)) & (V <= v_hi + tolerancia_v(v_hi))


def compat_rumbo(theta_o, tw, V):
    """Máscara sobre ZS: rumbo corregido a 30 grados o menos del viento (S22c). Cambio respecto de S22c (criterio §3,
    por la estimación previa): donde el viento GFS no llega a 3 m/s el rumbo no excluye, porque en calma la dirección
    del modelo no significa nada (H10, S22c); en esas capas decide sólo la rapidez."""
    return (C22.dang(theta_o, tw) <= TAU) | (V < VMIN_RUMBO)


def banda(mask):
    """Banda de alturas compatibles: [mín, máx] de ZS donde mask, ancho, y si restringe (§3)."""
    if not np.any(mask):
        return {"banda": None, "ancho": None, "restringe": False, "n": 0}
    hs = ZS[mask]
    ancho = round(float(hs.max() - hs.min()), 2)
    return {"banda": [round(float(hs.min()), 2), round(float(hs.max()), 2)], "ancho": ancho,
            "restringe": bool(ancho <= ANCHO_MAX + 1e-9), "n": int(mask.sum()),
            "toca_sombra": bool(((hs >= H_SOMBRA - TOL_SOMBRA - 1e-9) & (hs <= H_SOMBRA + TOL_SOMBRA + 1e-9)).any()),
            "separa_capas": bool(hs.max() <= H_CAPA_ALTA + 1e-9 or hs.min() > H_CAPA_ALTA + 1e-9)}


def h_estrella(d_km, dt_min, V, mask):
    """Altura de mejor ajuste dentro de la banda: la que deja la rapidez del GFS más cerca de d / (Δt + 5 min)."""
    if not np.any(mask):
        return None
    v_c = np.asarray(d_km, float) * 1000.0 / ((dt_min + DT_EMISION_MIN / 2) * 60.0)
    err = np.where(mask, np.abs(V - v_c), np.inf)
    return round(float(ZS[int(np.argmin(err))]), 2)


def alturas(lat, lon, dt_min, vw):
    """Todo lo de una llegada: bandas por rapidez, por rumbo y por las dos, más h*."""
    tw, V = vw
    d, th = dist_y_rumbo_por_h(lat, lon)
    mv = compat_rapidez(d, dt_min, V)
    mr = compat_rumbo(th, tw, V)
    mvr = mv & mr
    i47 = int(np.argmin(np.abs(ZS - H_SOMBRA)))
    v_lo, v_hi = intervalo_v(d, dt_min)
    return {"dt_min": dt_min, "d_km_3p2_4p7_10": [round(float(d[0]), 1), round(float(d[i47]), 1),
                                                   round(float(d[int(np.argmin(np.abs(ZS - 10)))]), 1)],
            "v_obs_4p7": [round(float(v_lo[i47]), 1), round(float(v_hi[i47]), 1)],
            "rapidez": banda(mv), "rumbo": banda(mr), "rapidez_y_rumbo": banda(mvr),
            "h_estrella": h_estrella(d, dt_min, V, mvr), "h_estrella_solo_rapidez": h_estrella(d, dt_min, V, mv)}


def veredicto_caso(b):
    """Veredicto de una llegada contra la sombra (§4): b es la banda de rapidez y rumbo."""
    if b["banda"] is None:
        return "SIN SOLUCIÓN"
    if not b["restringe"]:
        return "NO RESTRINGE"
    return "ACIERTA" if b["toca_sombra"] else "FALLA"


def pruebas():
    # paralaje: aparente y corregir son inversas
    la, lo = aparente(CLAT - 0.15, CLON + 0.10, 6.0)
    cla, clo = corregir(la, lo, 6.0)
    assert abs(cla[0] - (CLAT - 0.15)) < 1e-6 and abs(clo[0] - (CLON + 0.10)) < 1e-6
    # algo a 4,7 km se ve unos 4,3 km al sur
    la, lo = aparente(CLAT, CLON, 4.7)
    assert 4.0 < (CLAT - la[0]) * KY < 4.6, (CLAT - la[0]) * KY
    # intervalo de rapidez: 20 km en 60 min, más o menos 2,8 km, viaje de 60 a 70 min
    v_lo, v_hi = intervalo_v(20.0, 60.0)
    assert abs(v_lo - 17200 / 4200) < 1e-9 and abs(v_hi - 22800 / 3600) < 1e-9
    # perfil sintético: 5 m/s hasta 8 km, luego 20 m/s; 20 km en 60 min -> sólo la capa baja
    V = np.where(ZS <= 8.0, 5.0, 20.0)
    b = banda(compat_rapidez(np.full(len(ZS), 20.0), 60.0, V))
    assert b["banda"] == [3.2, 8.0] and not b["restringe"] and b["separa_capas"], b
    # el mismo trayecto en 20 min (16 a 17 m/s) -> sólo la capa alta
    b = banda(compat_rapidez(np.full(len(ZS), 20.0), 20.0, V))
    assert b["banda"][0] > 8.0 and b["separa_capas"], b
    # cizalle fuerte: rapidez lineal 2 a 35 m/s (3 m/s por km); 30 km en 50 min -> 5,6 a 13,6 m/s -> 4,4 a 7,0 km
    V = np.interp(ZS, [3.2, 14.0], [2.0, 35.0])
    b = banda(compat_rapidez(np.full(len(ZS), 30.0), 50.0, V))
    assert b["restringe"] and abs(b["banda"][0] - 4.4) < 0.15 and abs(b["banda"][1] - 7.0) < 0.15, b
    assert veredicto_caso({"banda": [4.0, 6.5], "restringe": True, "toca_sombra": True}) == "ACIERTA"
    assert veredicto_caso({"banda": [6.0, 8.0], "restringe": True, "toca_sombra": False}) == "FALLA"
    assert veredicto_caso({"banda": [3.2, 8.0], "restringe": False, "toca_sombra": True}) == "NO RESTRINGE"
    assert veredicto_caso({"banda": None}) == "SIN SOLUCIÓN"
    print("s27b_comun pruebas OK")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    pruebas()
