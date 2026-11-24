r"""S21b: piezas comunes. Lectura de las ventanas de C02, C05 y C06 bajadas por s21b_bajar.py, reflectancia con el
sol del momento en que el ABI mira cada fila, geometria del ABI (directa e inversa) y el modelo de pluma del criterio.

Por que asi: en luz reflejada lo que cambia de un dia a otro es sobre todo el sol. Se divide por el coseno del
cenital solar de cada pixel a la hora en que fue mirado, para que dos cuadros sean comparables; lo que quede (laderas
que se sombrean, nieve que se derrite) lo absorbe el nulo de cada prueba, no una correccion.

Geometria: la misma que s20b_comun.py (PUG GOES-R 4.2.8, satelite en -75,0, GRS80), aqui con la inversa para dar
lat/lon del elipsoide a cada pixel de cada banda desde sus angulos de barrido.
Criterio: docs/own_volcat/s21b_reflejadas/criterio_2026-11-24.md. Datos en D:\goes_notas\s21\b.
"""
import os
from datetime import datetime, timedelta

import numpy as np
from pyproj import Transformer

L1B = r"D:\goes_notas\s21\b\l1b"
TRABAJO = r"D:\goes_notas\s21\b"
MASCARA = r"D:\goes_notas\s20b\mascara_2026-10-25.npz"
EPOCA = datetime(2000, 1, 1, 12)

SAT_LON = -75.0
H_SAT = 35786023.0
RE, RP = 6378137.0, 6356752.31414
E2 = 1 - (RP / RE) ** 2
HT = H_SAT + RE

CRATER = (-36.863, -71.377, 3200.0)          # h29_comun.CRATER y tope de H24 (3,2 km)
CUMBRES = {"chillan": CRATER, "antuco": (-37.41, -71.35, 2979.0), "longavi": (-36.19, -71.16, 3242.0)}  # H24 SITIOS

# Modelo de pluma fijado en el criterio §1.3 con Landsat (no se toca despues de medir)
T_PLUMA = 0.47
RHO_P = {"C02": 0.109, "C05": 0.109, "C06": 0.094}

# Grilla local de 30 m de S20b (UTM 19 S, +-20 km alrededor del crater de S20b)
_CR20 = (-36.863, -71.377)
_t = Transformer.from_crs(4326, "EPSG:32719", always_xy=True)
_CX, _CY = _t.transform(_CR20[1], _CR20[0])
_N, _RES, _MEDIO = int(2 * 20000.0 / 30.0), 30.0, 20000.0
_XX = _CX - _MEDIO + (np.arange(_N) + 0.5) * _RES
_YY = _CY + _MEDIO - (np.arange(_N) + 0.5) * _RES
_GX, _GY = np.meshgrid(_XX, _YY)
GLON, GLAT = Transformer.from_crs("EPSG:32719", 4326, always_xy=True).transform(_GX, _GY)
CELDA_KM2 = _RES * _RES / 1e6


def ecef(lat, lon, h):
    p, l = np.radians(lat), np.radians(lon)
    n = RE / np.sqrt(1 - E2 * np.sin(p) ** 2)
    return (n + h) * np.cos(p) * np.cos(l), (n + h) * np.cos(p) * np.sin(l), (n * (1 - E2) + h) * np.sin(p)


def barrido(lat, lon, h=0.0):
    """Angulos de barrido (x, y) en rad de un punto a h m sobre el elipsoide (igual que s20b_comun.barrido)."""
    X, Y, Z = ecef(lat, np.asarray(lon) - SAT_LON, h)
    sx, sy, sz = HT - X, -Y, Z
    return np.arcsin(-sy / np.sqrt(sx ** 2 + sy ** 2 + sz ** 2)), np.arctan(sz / sx)


def latlon(x, y):
    """Inversa (PUG 4.2.8.1): lat, lon del elipsoide para angulos de barrido x, y (rad)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    a = np.sin(x) ** 2 + np.cos(x) ** 2 * (np.cos(y) ** 2 + (RE ** 2 / RP ** 2) * np.sin(y) ** 2)
    b = -2 * HT * np.cos(x) * np.cos(y)
    c = HT ** 2 - RE ** 2
    with np.errstate(invalid="ignore"):
        rs = (-b - np.sqrt(b ** 2 - 4 * a * c)) / (2 * a)
    sx, sy, sz = rs * np.cos(x) * np.cos(y), -rs * np.sin(x), rs * np.cos(x) * np.sin(y)
    lat = np.degrees(np.arctan((RE ** 2 / RP ** 2) * sz / np.sqrt((HT - sx) ** 2 + sy ** 2)))
    lon = SAT_LON - np.degrees(np.arctan(sy / (HT - sx)))
    return lat, lon


def sol(t, lat, lon, horas=None):
    """Cenital y azimut solar (grados) en el dia de t (datetime UTC) a la hora de t, o a `horas` (horas UTC de ese
    dia, array que se difunde contra lat/lon). Ecuaciones de NOAA."""
    doy = t.timetuple().tm_yday
    h = (t.hour + t.minute / 60 + (t.second + t.microsecond / 1e6) / 3600) if horas is None else np.asarray(horas)
    g = 2 * np.pi / 365 * (doy - 1 + (h - 12) / 24)
    eot = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g)
                    - 0.040849 * np.sin(2 * g))
    dec = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
           + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    tst = h * 60 + eot + 4 * np.asarray(lon)
    ha = np.radians(tst / 4 - 180)
    la = np.radians(lat)
    cz = np.sin(la) * np.sin(dec) + np.cos(la) * np.cos(dec) * np.cos(ha)
    z = np.degrees(np.arccos(np.clip(cz, -1, 1)))
    az = (np.degrees(np.arctan2(np.sin(ha), np.cos(ha) * np.sin(la) - np.tan(dec) * np.cos(la))) + 180) % 360
    return z, az


class Banda:
    """Geometria fija de una banda en la ventana (no cambia entre cuadros: grilla fija del ABI)."""

    def __init__(self, nombre, x, y):
        self.nombre = nombre
        self.x, self.y = np.asarray(x, float), np.asarray(y, float)
        self.dx, self.dy = self.x[1] - self.x[0], self.y[1] - self.y[0]
        X, Y = np.meshgrid(self.x, self.y)
        self.lat, self.lon = latlon(X, Y)
        self.shape = self.lat.shape
        la, lo = np.radians(self.lat), np.radians(self.lon)
        k = 6371.0
        g = [np.gradient(v, axis=a) for v in (la, lo) for a in (0, 1)]       # dla_r, dla_c, dlo_r, dlo_c
        self.area = np.abs(g[0] * g[3] - g[1] * g[2]) * np.cos(la) * k * k   # km2 por pixel

    def indices(self, lat, lon, h):
        """Fila y columna enteras (y validez) donde el ABI ve puntos a h m sobre el elipsoide."""
        x, y = barrido(lat, lon, h)
        c = np.rint((x - self.x[0]) / self.dx).astype(int)
        r = np.rint((y - self.y[0]) / self.dy).astype(int)
        ok = (r >= 0) & (r < self.shape[0]) & (c >= 0) & (c < self.shape[1])
        return r, c, ok

    def fraccion(self, mask_local, h):
        """f por pixel: area de las celdas de 30 m de la mascara puestas a h m, dividida por el area del pixel."""
        r, c, ok = self.indices(GLAT[mask_local], GLON[mask_local], h)
        out = np.zeros(self.shape)
        np.add.at(out, (r[ok], c[ok]), CELDA_KM2)
        return out / self.area

    def km_desde(self, lat0, lon0, h0):
        """Coordenadas aparentes (km este, km norte) de cada pixel desde donde el ABI ve (lat0, lon0, h0)."""
        x0, y0 = barrido(lat0, lon0, h0)
        la0, lo0 = latlon(x0, y0)
        e = (self.lon - lo0) * 111.32 * np.cos(np.radians(la0))
        n = (self.lat - la0) * 110.57
        return e, n


_GEO = {}


def geometria(npz):
    """Banda por nombre, construida una vez desde los x, y del primer cuadro (la grilla del ABI es fija)."""
    if not _GEO:
        for b in ("C02", "C05", "C06"):
            _GEO[b] = Banda(b, npz[f"{b}_x"], npz[f"{b}_y"])
    return _GEO


def archivo(dt):
    return os.path.join(L1B, f"{dt:%Y%m%d_%H%M}.npz")


def hora_fila(tb, banda):
    """Hora (datetime) en que se mira cada fila: lineal entre inicio y fin del barrido segun y (criterio §0.3)."""
    y_top, y_bot = 0.151844, -0.151844
    fr = (y_top - banda.y) / (y_top - y_bot)
    return [EPOCA + timedelta(seconds=float(tb[0] + (tb[1] - tb[0]) * f)) for f in fr]


def reflectancia(dt):
    """{banda: rho} con rho = kappa0 * L / cos(cenital solar del pixel a la hora de su fila). None si no hay archivo."""
    p = archivo(dt)
    if not os.path.exists(p):
        return None
    z = np.load(p)
    geo = geometria(z)
    out = {}
    for b, g in geo.items():
        rad = z[f"{b}_rad"].astype("float64")
        tfila = hora_fila(z[f"{b}_tb"], g)
        t0 = tfila[0].replace(hour=0, minute=0, second=0, microsecond=0)
        horas = np.array([(t - t0).total_seconds() / 3600 for t in tfila])[:, None]
        cz = np.cos(np.radians(sol(tfila[0], g.lat, g.lon, horas)[0]))
        with np.errstate(invalid="ignore", divide="ignore"):
            rho = z[f"{b}_kappa0"] * rad / cz
        rho[cz < 0.05] = np.nan
        out[b] = rho
    return out


def hora_chillan(dt):
    """Hora en que el ABI mira Chillan en el cuadro dt: minuto nominal + 8 min 39 s (criterio §0.3)."""
    return dt + timedelta(minutes=8, seconds=39)


def esperado(f, B, banda):
    """Modelo del criterio §1.2: P = f * (rho_p - (1 - T) * B)."""
    return f * (RHO_P[banda] - (1 - T_PLUMA) * B)
