r"""S20b: piezas comunes. Grilla local de 30 m alrededor del crater, lectura de Sentinel-2 L2A (Element 84) y
Landsat C2 L2 (Planetary Computer) sin cuenta, DEM Copernicus GLO-30, y proyeccion de un punto a una altura dada
sobre la ventana ABI de 83 x 94 de los cubos de H23 y H24.

Por que asi: la pregunta es cuanta senal deja en el pixel de GOES una pluma cuya huella conocemos por un sensor
fino. Para eso hay que poner la huella fina en la misma grilla que GOES, y GOES ve la pluma corrida por paralaje:
un objeto a H km sobre el elipsoide aparece donde la linea de vista del satelite corta el elipsoide, no encima de
su sombra. Se calcula exacto con la geometria del ABI (angulos de barrido), no con un factor por km.

Sin escritura al repo de nada que venga de SSEC. Datos en D:\goes_notas\s20b.
"""
import json
import math
import os
import urllib.request

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT

TRABAJO = r"D:\goes_notas\s20b"
LATLON = r"D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\latlon.npz"
DEMV = r"D:\goes_cache\etapa3_chillan\dem_ventana.npz"
NY, NX = 83, 94
LAT, LON = (np.load(LATLON)[k] for k in ("lat", "lon"))
ZDEM = np.load(DEMV)["zdem"]
CRATER = (-36.863, -71.377)            # el de H29 (h29_comun.CRATER)

# geometria ABI (GOES-19): src/config.py GOES19_SAT_LON y GOES19_PERSPECTIVE_POINT_HEIGHT, elipsoide GRS80
SAT_LON = -75.0
H_SAT = 35786023.0
RE, RP = 6378137.0, 6356752.31414
E2 = 1 - (RP / RE) ** 2

# grilla local: UTM 19 S, 30 m, +-20 km alrededor del crater
CRS = "EPSG:32719"
RES_M, MEDIO = 30.0, 20000.0
_t = Transformer.from_crs(4326, CRS, always_xy=True)
CX, CY = _t.transform(CRATER[1], CRATER[0])
N = int(2 * MEDIO / RES_M)
TRANSF = from_origin(CX - MEDIO, CY + MEDIO, RES_M, RES_M)
XX = CX - MEDIO + (np.arange(N) + 0.5) * RES_M
YY = CY + MEDIO - (np.arange(N) + 0.5) * RES_M
GX, GY = np.meshgrid(XX, YY)
_inv = Transformer.from_crs(CRS, 4326, always_xy=True)
GLON, GLAT = _inv.transform(GX, GY)


def leer(href, escala=1.0, suma=0.0, rs=Resampling.bilinear, nodata=0):
    """Banda en la grilla local (float32, NaN donde no hay dato)."""
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="2"):
        with rasterio.open(href) as ds:
            with WarpedVRT(ds, crs=CRS, transform=TRANSF, width=N, height=N, resampling=rs,
                           src_nodata=nodata if nodata is not None else ds.nodata, nodata=np.nan,
                           dtype="float32") as v:
                a = v.read(1).astype("float32")
    return np.where(np.isfinite(a), a * escala + suma, np.nan).astype("float32")


def pc_token():
    u = "https://planetarycomputer.microsoft.com/api/sas/v1/token/landsateuwest/landsat-c2"
    return json.load(urllib.request.urlopen(u, timeout=60))["token"]


def stac_post(url, body):
    r = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=90))


def dem_local():
    """Copernicus GLO-30 (cota sobre el geoide EGM2008, m) en la grilla local; teselas S37 y S38 W072."""
    out = np.full((N, N), np.nan, "float32")
    for t in ("S37_00_W072_00", "S38_00_W072_00"):
        n = f"Copernicus_DSM_COG_10_{t}_DEM"
        a = leer(f"https://copernicus-dem-30m.s3.amazonaws.com/{n}/{n}.tif", nodata=None)
        out = np.where(np.isfinite(a), a, out)
    return out


# ---------- ABI ----------
def ecef(lat, lon, h):
    p, l = np.radians(lat), np.radians(lon)
    n = RE / np.sqrt(1 - E2 * np.sin(p) ** 2)
    return (n + h) * np.cos(p) * np.cos(l), (n + h) * np.cos(p) * np.sin(l), (n * (1 - E2) + h) * np.sin(p)


def barrido(lat, lon, h=0.0):
    """Angulos de barrido ABI (x, y) en rad de un punto a altura h (m) sobre el elipsoide (PUG GOES-R, 4.2.8)."""
    X, Y, Z = ecef(lat, np.asarray(lon) - SAT_LON, h)
    sx, sy, sz = (H_SAT + RE) - X, -Y, Z
    return np.arcsin(-sy / np.sqrt(sx ** 2 + sy ** 2 + sz ** 2)), np.arctan(sz / sx)


def _ajuste():
    """Fila y columna de la ventana como funcion lineal de y y x de barrido (grilla fija del ABI)."""
    x, y = barrido(LAT, LON)
    r, c = np.mgrid[:NY, :NX]
    A = np.c_[np.ones(r.size), y.ravel()]
    ar = np.linalg.lstsq(A, r.ravel(), rcond=None)[0]
    B = np.c_[np.ones(c.size), x.ravel()]
    ac = np.linalg.lstsq(B, c.ravel(), rcond=None)[0]
    res = max(np.abs(A @ ar - r.ravel()).max(), np.abs(B @ ac - c.ravel()).max())
    return ar, ac, res, x, y


AR, AC, RESID, XB, YB = _ajuste()


def a_ventana(lat, lon, h):
    """Fila y columna (fraccionarias) de la ventana donde el ABI ve un punto a h m sobre el elipsoide."""
    x, y = barrido(lat, lon, h)
    return AR[0] + AR[1] * y, AC[0] + AC[1] * x


def area_pixel_km2():
    """Area de cada pixel ABI de la ventana sobre el elipsoide (km2), por diferencias de lat/lon."""
    la, lo = np.radians(LAT), np.radians(LON)
    dla_r, dlo_r = np.gradient(la, axis=0), np.gradient(lo, axis=0)
    dla_c, dlo_c = np.gradient(la, axis=1), np.gradient(lo, axis=1)
    k = 6371.0
    return np.abs(dla_r * dlo_c - dla_c * dlo_r) * np.cos(la) * k * k


def hav(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def acumular(mask, h_m, peso=None):
    """Area (km2) de los pixeles True de la grilla local, puestos a h_m sobre el elipsoide, en cada pixel ABI."""
    out = np.zeros((NY, NX))
    if not mask.any():
        return out
    r, c = a_ventana(GLAT[mask], GLON[mask], h_m)
    ri, ci = np.rint(r).astype(int), np.rint(c).astype(int)
    ok = (ri >= 0) & (ri < NY) & (ci >= 0) & (ci < NX)
    w = np.full(ri.shape, RES_M * RES_M / 1e6) if peso is None else peso[mask] * RES_M * RES_M / 1e6
    np.add.at(out, (ri[ok], ci[ok]), w[ok])
    return out


def mover(mask, de_m, dn_m):
    """Corre una mascara de la grilla local de_m al este y dn_m al norte (redondeado a la celda)."""
    dc, dr = int(round(de_m / RES_M)), -int(round(dn_m / RES_M))
    out = np.zeros_like(mask)
    r0, r1 = max(0, -dr), N - max(0, dr)
    c0, c1 = max(0, -dc), N - max(0, dc)
    out[r0 + dr:r1 + dr, c0 + dc:c1 + dc] = mask[r0:r1, c0:c1]
    return out


def rumbo_sat(lat, lon):
    """Azimut (grados desde el N) desde el punto hacia el subsatelite de GOES-19."""
    p0, p1, dl = math.radians(lat), 0.0, math.radians(SAT_LON - lon)
    y = math.sin(dl) * math.cos(p1)
    x = math.cos(p0) * math.sin(p1) - math.sin(p0) * math.cos(p1) * math.cos(dl)
    return math.degrees(math.atan2(y, x)) % 360
