"""Decodifica un PNG VOLCAT Ash_Height (Chile_Central_2_km) a la grilla ABI de la ventana 83 x 94.

Misma decodificacion que H3 y beta73 (huellas_h3.py, pruebaA_28oct.py): pixel con ceniza = pixel que
src/process/volcat_colorbar.classify_pixels asigna a un bloque de la barra (saturacion >= 0,2), dentro de la
zona util del mapa, llevado a la grilla ABI por vecino mas cercano, sin dilatar.

Zona util: fuera el titulo (filas < 70), el globo (filas >= 640, columnas < 140) y los logos (filas >= 640,
columnas >= 840). La mascara de frecuencia de paso3 (pixeles clasificados en > 20 % de los cuadros) se perdio
con su scratchpad; su docstring dice que en el mapa (filas 70 a 640) no habia ninguno, asi que no cambia la
zona que cubre la ventana ABI (filas ~ 300 a 420 del PNG). Se valida contra huellas_b73 en validar_huella().
"""
import os, sys, math, re
import numpy as np
from PIL import Image

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
sys.path.insert(0, REPO)
from src.process import volcat_colorbar as vc  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h11 as C  # noqa: E402

dp = math.degrees(72.80000305175781 / 206264.796875)
LAT0 = -31.8007698059082 + 36 * dp
LON0 = 278.9210815429688 - 360.0
CHI = (-36.86, -71.38)
RR = np.rint((LAT0 - C.LAT) / dp).astype(int)
CC = np.rint((C.LON - LON0) / dp).astype(int)
RX = re.compile(r"ABI\.(\d{4})-(\d{2})-(\d{2})\.(\d{2})-(\d{2})-\d{2}\.Ash_Height")


def hav(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


DIST = hav(C.LAT, C.LON, *CHI)      # km al crater, por pixel ABI


def valido(shape):
    v = np.ones(shape, bool); v[:70] = False; v[640:, :140] = False; v[640:, 840:] = False
    return v


def decodifica(fn):
    """(ceniza en grilla ABI a cualquier distancia, altura media del bloque en km, barra_ok)."""
    a = np.asarray(Image.open(fn).convert("RGB"), dtype="float64"); hmap = int(vc.MAP_FRAC * a.shape[0])
    bins = vc.palette_bins(a[hmap:])
    if bins is None:
        return None, None, False
    m = a[:hmap]; cm = vc._saturation(m) >= 0.2
    ok = np.zeros(cm.shape, bool); mid = np.full(cm.shape, np.nan)
    if cm.any():
        c = vc.classify_pixels(m[cm], bins); ok[cm] = c["ok"]
        mid[cm] = (np.asarray(c["lo_km"]) + np.asarray(c["hi_km"])) / 2
    ok &= valido(a.shape[:2])[:hmap]
    ash = np.zeros(C.LAT.shape, bool); hh = np.full(C.LAT.shape, np.nan)
    ins = (RR >= 0) & (RR < hmap) & (CC >= 0) & (CC < a.shape[1])
    ash[ins] = ok[RR[ins], CC[ins]]; hh[ins] = np.where(ash[ins], mid[RR[ins], CC[ins]], np.nan)
    return ash, hh, True


def huella(fn):
    """Huella = ceniza a <= 50 km del crater (regla de H3 y beta73, aplicada en la grilla del PNG; aqui en la
    grilla ABI, que es la misma regla salvo pixeles de borde, ver validar_huella)."""
    ash, hh, ok = decodifica(fn)
    if not ok:
        return None, None, None
    return ash & (DIST <= 50), ash, hh


def dt_de(fn):
    from datetime import datetime
    m = RX.search(os.path.basename(fn))
    return datetime(*[int(x) for x in m.groups()])


def validar_huella():
    pngs = os.path.join(C.B73, "png_new")
    n = 0; dif = 0
    for kk in [k[2:] for k in C._HUB if k.startswith("h_")]:
        r = C._INV.get(C.dtk(kk))
        fn = os.path.join(pngs, r["fn"]) if r else None
        if not fn or not os.path.exists(fn):
            continue
        h, a, _ = huella(fn)
        dif += int((h != C._HUB["h_" + kk]).sum()) + int((a != C._HUB["a_" + kk]).sum()); n += 1
        print(kk, "px huella", int(h.sum()), "ref", int(C._HUB["h_" + kk].sum()), "dif h", int((h != C._HUB["h_" + kk]).sum()), "dif ceniza", int((a != C._HUB["a_" + kk]).sum()))
    print("cuadros comparados", n, "pixeles distintos", dif)


if __name__ == "__main__":
    validar_huella()
