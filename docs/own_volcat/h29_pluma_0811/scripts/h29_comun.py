r"""H29: piezas comunes. Huella del PNG de VOLCAT (Chile_Central_2_km) en la ventana ABI de 83 x 94 y carga del cubo.

Por que asi: para el 08-11 no hay archivo de evento NetCDF, asi que la huella sale del PNG Ash_Height. Se decodifica
igual que huella_png.py de reproducir_volcat (pixel con ceniza = pixel que volcat_colorbar.classify_pixels asigna a
un bloque de la barra, saturacion >= 0,2), llevado a la grilla ABI por vecino mas cercano. H14 midio contra los
archivos de evento del 14-11 que esa lectura cae 1 fila al S y 1 columna al E de lo que VOLCAT publica; por eso la
huella principal se corre 1 fila al N y 1 columna al O (DESF_H14) y la nominal queda como sensibilidad.

Insumos en D: (solo lectura, nada de SSEC al repo): PNG y capas de VOLCAT, cubo L1b, ACMF y GFS de H23.
"""
import math
import os
import re
import sys
from datetime import datetime

import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, REPO)
from src.process import volcat_colorbar as vc  # noqa: E402

RES = os.path.join(os.path.dirname(AQUI), "resultados")
VOLCAT = r"D:\goes_notas\volcat_validacion_copia_2026-11-21\Chile_Central_2_km"
FRAMES = os.path.join(VOLCAT, "frames")
CAPAS = os.path.join(VOLCAT, "capas")
H23 = r"D:\goes_notas\s17\h23"
TRABAJO = r"D:\goes_notas\s19\h29"
LATLON = r"D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\latlon.npz"
DEM = r"D:\goes_cache\etapa3_chillan\dem_ventana.npz"
NY, NX = 83, 94
LAT, LON = (np.load(LATLON)[k] for k in ("lat", "lon"))
ZDEM = np.load(DEM)["zdem"]
CRATER = (-36.863, -71.377)

# proyeccion CE del PNG (la misma de h14_georef.py y huella_png.py)
DP = math.degrees(72.80000305175781 / 206264.796875)
LAT0 = -31.8007698059082 + 36 * DP
LON0 = 278.9210815429688 - 360.0
RR = np.rint((LAT0 - LAT) / DP).astype(int)
CC = np.rint((LON - LON0) / DP).astype(int)
DESF_H14 = (-1, -1)          # (filas, columnas) en la grilla ABI: huella PNG corrida 1 al N y 1 al O
RX = re.compile(r"(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-\d{2}\.png$")


def hav(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


DIST = hav(LAT, LON, *CRATER)


def valido(shape):
    v = np.ones(shape, bool)
    v[:70] = False
    v[640:, :140] = False
    v[640:, 840:] = False
    return v


def dt_de(fn):
    m = RX.search(os.path.basename(fn))
    return datetime(*[int(x) for x in m.groups()]) if m else None


def frames_del_dia(dia="2026-11-08"):
    fs = sorted(f for f in os.listdir(FRAMES) if f.startswith(dia) and f.endswith(".png") and "_annot" not in f)
    return [os.path.join(FRAMES, f) for f in fs]


def decodifica_png(fn):
    """Mapa del PNG: (ceniza bool, altura media del bloque en km) en coordenadas del PNG, mas barra_ok."""
    a = np.asarray(Image.open(fn).convert("RGB"), dtype="float64")
    hmap = int(vc.MAP_FRAC * a.shape[0])
    bins = vc.palette_bins(a[hmap:])
    if bins is None:
        return None, None, False
    m = a[:hmap]
    cm = vc._saturation(m) >= 0.2
    ok = np.zeros(cm.shape, bool)
    mid = np.full(cm.shape, np.nan)
    if cm.any():
        c = vc.classify_pixels(m[cm], bins)
        ok[cm] = c["ok"]
        mid[cm] = (np.asarray(c["lo_km"]) + np.asarray(c["hi_km"])) / 2
    ok &= valido(a.shape[:2])[:hmap]
    return ok, mid, True


def a_abi(ok, mid, desf=DESF_H14):
    """Lleva el mapa del PNG a la ventana ABI. desf = (df, dc): la huella en ABI[r, c] es la lectura nominal de
    ABI[r - df, c - dc] (desf (-1, -1): lo que la lectura nominal pone en (r, c) va a (r - 1, c - 1))."""
    hmap = ok.shape[0]
    ash = np.zeros((NY, NX), bool)
    hh = np.full((NY, NX), np.nan)
    ins = (RR >= 0) & (RR < hmap) & (CC >= 0) & (CC < ok.shape[1])
    ash[ins] = ok[RR[ins], CC[ins]]
    hh[ins] = np.where(ash[ins], mid[RR[ins], CC[ins]], np.nan)
    return corre(ash, hh, desf)


def corre(ash, hh, desf):
    """Destino (r + df, c + dc) <- origen (r, c); lo que sale de la ventana se pierde, lo que entra queda vacio."""
    df, dc = desf
    if (df, dc) == (0, 0):
        return ash, hh
    a2 = np.zeros_like(ash)
    h2 = np.full_like(hh, np.nan)
    r0, r1 = max(0, -df), NY - max(0, df)          # filas de origen que quedan dentro
    c0, c1 = max(0, -dc), NX - max(0, dc)
    a2[r0 + df:r1 + df, c0 + dc:c1 + dc] = ash[r0:r1, c0:c1]
    h2[r0 + df:r1 + df, c0 + dc:c1 + dc] = hh[r0:r1, c0:c1]
    return a2, h2


def fuera_de_ventana(ok):
    """Pixeles de ceniza del PNG que caen fuera de la ventana ABI (en el mapa, a <= 200 km del crater)."""
    hmap = ok.shape[0]
    rr, cc = np.mgrid[:hmap, :ok.shape[1]]
    la = LAT0 - rr * DP
    lo = LON0 + cc * DP
    dentro = (la <= LAT.max()) & (la >= LAT.min()) & (lo >= LON.min()) & (lo <= LON.max())
    cerca = hav(la, lo, *CRATER) <= 200
    return int((ok & ~dentro & cerca).sum()), int((ok & dentro).sum())


def bt_de_rad(rad, co):
    fk1, fk2, bc1, bc2 = co
    with np.errstate(invalid="ignore", divide="ignore"):
        return (fk2 / np.log(fk1 / rad + 1.0) - bc1) / bc2


def rad_de_bt(T, co):
    fk1, fk2, bc1, bc2 = co
    return fk1 / np.expm1(fk2 / (bc1 + bc2 * np.asarray(T, float)))
