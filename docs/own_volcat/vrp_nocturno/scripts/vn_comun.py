r"""VRP nocturno a 3,9 µm: piezas comunes de la validación fuera de muestra (criterio_2026-11-22.md).

Proyección fija de ABI (PUG GOES-R, vol. 3, §5.1.2), corrección de paralaje por línea de vista, ventanas por sitio,
cenit solar y la regla de calor (la misma de H17, "fondo coherente"). Nada de esto toca src/ ni el dashboard.
Lo pesado va a D:\goes_cache\vrp_nocturno.
"""
import os
import sys

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
sys.path.insert(0, REPO)
from src.volcanos import CATALOG  # noqa: E402  coordenadas del catálogo RNVV del repo, no a mano

OUT = os.environ.get("VN_DIR", r"D:\goes_cache\vrp_nocturno")
L1B = os.path.join(OUT, "l1b")

# Proyección de GOES-19 (atributos del NetCDF, leídos el 22-11-2026 de un C07 RadF)
REQ, RPOL, HSAT, LON0 = 6378137.0, 6356752.31414, 35786023.0 + 6378137.0, -75.0
XS, XO, YS, YO = 5.6e-05, -0.151844, -5.6e-05, 0.151844
SIGMA = 5.670374419e-8
MEDIO = 12          # media ventana en píxeles (14 km del anillo caben con holgura a >= 2 km/píxel)
ZONA, A0, A1 = 6.0, 8.0, 14.0  # km: zona del cráter y anillo (H9, H17)

CONTROLES = ["Parinacota", "Tinguiririca", "Descabezado Grande", "Lonquimay", "Lanin", "Osorno", "Hudson"]
ACTIVOS = ["Isluga", "Lascar", "Lastarria", "Tupungatito", "Planchon-Peteroa", "Copahue", "Llaima", "Villarrica",
           "Puyehue-Cordon Caulle", "Chaiten"]
H17_SITIOS = ["Nevados de Chillan", "Antuco", "Nevado de Longavi"]
EXTRA = ["Sangay (Ecuador)"]   # informativo, fuera del RNVV


def volcan(nombre):
    for v in CATALOG:
        if v.name == nombre:
            return v
    raise KeyError(nombre)


def latlon_a_xy(lat, lon, h=0.0):
    """Ángulos de barrido ABI (rad) de un punto a altura h (m) sobre el elipsoide. Con h > 0 se usa la posición 3D
    real del punto: el ángulo resultante ya incluye el paralaje."""
    la, lo = np.radians(lat), np.radians(lon - LON0)
    e2 = 1 - RPOL ** 2 / REQ ** 2
    N = REQ / np.sqrt(1 - e2 * np.sin(la) ** 2)
    X = (N + h) * np.cos(la) * np.cos(lo)
    Y = (N + h) * np.cos(la) * np.sin(lo)
    Z = (N * (1 - e2) + h) * np.sin(la)
    sx, sy, sz = HSAT - X, -Y, Z
    x = np.arcsin(-sy / np.sqrt(sx ** 2 + sy ** 2 + sz ** 2))
    y = np.arctan(sz / sx)
    return x, y


def xy_a_latlon(x, y):
    """Inversa de la proyección fija (PUG): lat/lon geodésicas en el elipsoide de los ángulos de barrido."""
    a = np.sin(x) ** 2 + np.cos(x) ** 2 * (np.cos(y) ** 2 + REQ ** 2 / RPOL ** 2 * np.sin(y) ** 2)
    b = -2 * HSAT * np.cos(x) * np.cos(y)
    c = HSAT ** 2 - REQ ** 2
    with np.errstate(invalid="ignore"):
        rs = (-b - np.sqrt(b ** 2 - 4 * a * c)) / (2 * a)
    sx = rs * np.cos(x) * np.cos(y)
    sy = -rs * np.sin(x)
    sz = rs * np.cos(x) * np.sin(y)
    lat = np.degrees(np.arctan(REQ ** 2 / RPOL ** 2 * sz / np.sqrt((HSAT - sx) ** 2 + sy ** 2)))
    lon = LON0 - np.degrees(np.arctan(sy / (HSAT - sx)))
    return lat, lon


def cumbre_aparente(nombre):
    """(lat, lon) donde ABI, que navega al elipsoide, muestra la cumbre (paralaje por línea de vista)."""
    v = volcan(nombre)
    x, y = latlon_a_xy(v.lat, v.lon, float(v.elevation))
    return xy_a_latlon(x, y)


def ventana(nombre):
    """(r0, r1, c0, c1) de la ventana de 2·MEDIO+1 píxeles centrada en la cumbre aparente, en la grilla de 2 km."""
    v = volcan(nombre)
    x, y = latlon_a_xy(v.lat, v.lon, float(v.elevation))
    c, r = int(round((x - XO) / XS)), int(round((y - YO) / YS))
    return r - MEDIO, r + MEDIO + 1, c - MEDIO, c + MEDIO + 1


def grilla(nombre):
    r0, r1, c0, c1 = ventana(nombre)
    cc, rr = np.meshgrid(np.arange(c0, c1), np.arange(r0, r1))
    return xy_a_latlon(XO + XS * cc, YO + YS * rr)


def hav(lat, lon, la0, lo0):
    p1, p2 = np.radians(la0), np.radians(lat)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon - lo0) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def area_pixel(lat, lon):
    """km² por píxel desde la grilla lat/lon (igual que H16 y H17)."""
    R = 6371.0
    la, lo = np.radians(lat), np.radians(lon)
    dly, dlx = np.gradient(la)
    doy, dox = np.gradient(lo)
    c = np.cos(la)
    return np.abs(R * dlx * R * c * doy - R * c * dox * R * dly)


class Sitio:
    """Máscaras y área de un volcán, calculadas una vez."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.v = volcan(nombre)
        self.lat, self.lon = grilla(nombre)
        la, lo = cumbre_aparente(nombre)
        d = hav(self.lat, self.lon, la, lo)
        self.zona, self.anillo = d <= ZONA, (d >= A0) & (d <= A1)
        self.area = area_pixel(self.lat, self.lon)


def bt(rad, co):
    fk1, fk2, bc1, bc2 = co
    with np.errstate(invalid="ignore", divide="ignore"):
        return (fk2 / np.log(fk1 / rad + 1.0) - bc1) / bc2


def a_mir(co):
    """a de L7(T) ≈ a T⁴ entre 600 y 1.500 K con los Planck del NetCDF (H17 §1)."""
    fk1, fk2, bc1, bc2 = co
    T = np.linspace(600, 1500, 901)
    L = fk1 / (np.exp(fk2 / (bc1 + bc2 * T)) - 1)
    return float(np.sum(L * T ** 4) / np.sum(T ** 8))


def calor(s, r7, co7, r14, co14):
    """Regla del criterio §2 (= `vrp_ctx` de H17). Devuelve VRP (MW), máx BT14 de la zona, n píxeles calientes.

    Fondo coherente: el fondo a 3,9 µm de cada píxel es la radiancia de Planck a BT14 del propio píxel más la
    mediana de BT7 − BT14 del anillo. Así el test de píxel caliente y la potencia usan la misma referencia."""
    b7, b14 = bt(r7, co7), bt(r14, co14)
    D = b7 - b14
    dr = D[s.anillo]
    ok = np.isfinite(dr)
    if ok.sum() < 20 or not np.isfinite(D[s.zona]).any():
        return np.nan, np.nan, 0
    med = np.median(dr[ok])
    mad = np.median(np.abs(dr[ok] - med))
    umb = max(2.0, 3 * 1.4826 * mad)
    fk1, fk2, bc1, bc2 = co7
    with np.errstate(over="ignore", invalid="ignore"):
        l7bg = fk1 / (np.exp(fk2 / (bc1 + bc2 * (b14 + med))) - 1)
    dl = r7 - l7bg
    cal = s.zona & ((D - med) >= umb) & (dl > 0)
    vrp = float(np.nansum(s.area[cal] * 1e6 * SIGMA / a_mir(co7) * dl[cal]) / 1e6)
    return vrp, float(np.nanmax(np.where(s.zona, b14, np.nan))), int(cal.sum())


def sza(dt, lat, lon):
    """Cenit solar (NOAA, precisión ~0,1°), igual que H17."""
    doy = dt.timetuple().tm_yday
    g = 2 * np.pi / 365 * (doy - 1 + (dt.hour - 12) / 24 + dt.minute / 1440)
    decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
            + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g)
                    - 0.040849 * np.sin(2 * g))
    tst = dt.hour * 60 + dt.minute + eqt + 4 * lon
    ha = np.radians(tst / 4 - 180)
    la = np.radians(lat)
    c = np.sin(la) * np.sin(decl) + np.cos(la) * np.cos(decl) * np.cos(ha)
    return float(np.degrees(np.arccos(np.clip(c, -1, 1))))
