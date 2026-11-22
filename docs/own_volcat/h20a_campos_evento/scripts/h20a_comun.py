"""H20a: utilidades comunes. Lee archivos de evento (NetCDF4) y los npz del L2 hechos por h20a_extraer.py.
Nada de esto escribe grillas en el repo."""
import os
import re
import glob
import numpy as np
import netCDF4 as nc

EV_FUEGO = os.environ.get(
    "H20A_EVENTOS_FUEGO",
    r"D:\goes_notas\s16\modo_dia\fuego\fuego_goes16-fulldisk_june2018_r20260709-volcat-code-ancil"
    r"\reference_data\events")
EV_CHILLAN = os.environ.get("H20A_EVENTOS_CHILLAN", r"D:\goes_notas\busqueda_2026-11-20\volcat_eventos_357070")
L2 = os.environ.get("H20A_L2", r"D:\goes_notas\s17\h20a\l2")
RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")

ELECCION = ["171600", "173100", "174600", "180100", "181600", "183100", "184600",
            "190100", "191600", "193100", "194600", "200100", "201600"]
VALIDACION = ["203100", "204600", "210100", "211600", "213100", "214600", "220100",
              "221600", "223100", "224600", "230100", "231600", "233100"]
HORAS = ["%02d%02d00" % (h, m) for h in range(14, 24) for m in (1, 16, 31, 46)]


def hora_de(path):
    """Hora del L2 (HHMM00, minuto + 1) a partir del nombre s2018060317154840 del archivo de evento."""
    m = re.search(r"_s20180603(\d\d)(\d\d)\d+_", os.path.basename(path))
    return "%s%02d00" % (m.group(1), int(m.group(2)) + 1)


def eventos_fuego(vid):
    """Lista ordenada de (hora, ruta) de los NetCDF de evento del volcan vid."""
    fs = sorted(glob.glob(os.path.join(EV_FUEGO, "VOLCAT-FD-vid%s_*.nc" % vid)))
    return [(hora_de(f), f) for f in fs]


def granulos_fuego():
    fs = sorted(glob.glob(os.path.join(EV_FUEGO, "VOLCAT-FD_v3p9_*.nc")))
    return [(hora_de(f), f) for f in fs]


def arr(ds, k):
    """Variable como float64 con NaN en el relleno (netCDF4 aplica scale_factor y add_offset)."""
    v = ds[k][:]
    return np.ma.filled(np.ma.asarray(v).astype("float64"), np.nan)


def cargar_l2(hora):
    return np.load(os.path.join(L2, "l2_%s.npz" % hora))


def anterior(hora):
    i = HORAS.index(hora)
    return HORAS[i - 1] if i > 0 else None


def ventana(ds, lat2, lon2):
    """Busca la ventana del recorte del evento dentro de la grilla 601 x 601 del L2 por coincidencia de
    latitud y longitud. Devuelve (fila0, col0, max|dlat|, max|dlon|, n_validos) o None."""
    la = arr(ds, "latitude")
    lo = arr(ds, "longitude")
    ny, nx = la.shape
    ok = np.isfinite(la) & np.isfinite(lo)
    if not ok.any():
        return None
    iy, ix = np.argwhere(ok)[ok.sum() // 2]
    d = np.abs(lat2 - la[iy, ix]) + np.abs(lon2 - lo[iy, ix])
    d[~np.isfinite(d)] = 1e9
    jy, jx = np.unravel_index(np.argmin(d), d.shape)
    f0, c0 = int(jy - iy), int(jx - ix)
    if f0 < 0 or c0 < 0 or f0 + ny > lat2.shape[0] or c0 + nx > lat2.shape[1]:
        return (f0, c0, np.nan, np.nan, 0)
    a = lat2[f0:f0 + ny, c0:c0 + nx]
    b = lon2[f0:f0 + ny, c0:c0 + nx]
    m = ok & np.isfinite(a) & np.isfinite(b)
    return (f0, c0, float(np.abs(a - la)[m].max()), float(np.abs(b - lo)[m].max()), int(m.sum()))


def recorte(a, f0, c0, ny, nx, df=0, dc=0):
    """Recorte de la grilla del L2 en la ventana del evento, con corrimiento opcional (nulo). Los bordes
    que se salen quedan en NaN."""
    out = np.full((ny, nx), np.nan)
    y0, x0 = f0 + df, c0 + dc
    ya, yb = max(y0, 0), min(y0 + ny, a.shape[0])
    xa, xb = max(x0, 0), min(x0 + nx, a.shape[1])
    out[ya - y0:yb - y0, xa - x0:xb - x0] = a[ya:yb, xa:xb]
    return out


def acuerdo(x, y, tol, m=None):
    """(n, fraccion con |x - y| < tol) en los pixeles donde ambos tienen valor (y m, si se da)."""
    ok = np.isfinite(x) & np.isfinite(y)
    if m is not None:
        ok &= m
    n = int(ok.sum())
    if n == 0:
        return 0, float("nan")
    return n, float((np.abs(x[ok] - y[ok]) < tol).mean())


def jaccard(a, b):
    u = (a | b).sum()
    return float("nan") if u == 0 else float((a & b).sum() / u)


def hav(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def logit(p):
    p = np.asarray(p, "float64")
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.log(p) - np.log1p(-p)
