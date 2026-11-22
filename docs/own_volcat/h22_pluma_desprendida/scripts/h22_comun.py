r"""H22: piezas comunes. Lee los caches L1b que ya existen (solo lectura, via h17_comun.indice), arma una pila
de BT 11,2 um (C14), 12,3 um (C15) y 8,4 um (C11) de la ventana del detector (83 x 94 pixeles de 2 km), calcula la
linea base del mismo pixel y ubica la huella event_idx de los archivos de evento de VOLCAT en esa ventana.

No baja nada. Nada de SSEC sale de D:. Salidas grandes en D:\goes_notas\s17\h22 (variable H22_DIR).
"""
import glob
import os
import sys
from datetime import datetime, timedelta

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "h17_regla_propia", "scripts"))
import h17_comun as K  # noqa: E402

H22 = os.environ.get("H22_DIR", r"D:\goes_notas\s17\h22")
PILA = os.path.join(H22, "pila.npz")
DEM = r"D:\goes_cache\etapa3_chillan\dem_ventana.npz"
EVDIR = K.EVDIR
CRATER = (-36.863, -71.377)          # el mismo punto que H14
LAT, LON, WIN = K.LAT, K.LON, K.WIN
DIST = K.hav(LAT, LON, *CRATER)       # km al crater, posicion nominal del pixel (como H14)
ZDEM = np.load(DEM)["zdem"]           # cota vista por cada pixel, m (etapa 3 de H15, con paralaje)

# Decisiones de metodo fijadas con la medicion de ruido (dias sin evento), antes de mirar la pluma
BASE_DIAS = 6          # dias previos de la linea base
BASE_TOD_MIN = 20      # +- minutos de hora del dia
BASE_MIN_N = 5         # cuadros minimos
BASE_PCT = 75          # percentil de BT11 que define "lo mas despejado"
BASE_CLARO_K = 2.0     # un cuadro de la base cuenta como despejado si BT11 >= base - 2 K
T_NUBE_BETA = 215.0    # K, temperatura efectiva para las emisividades de beta (tropopausa nominal, Pavolonis 2010)


def bt(rad, co):
    return K.bt(rad, co)


def rad_de_bt(T, co):
    """Inversa de Planck con los coeficientes del NetCDF L1b (fk1, fk2, bc1, bc2)."""
    fk1, fk2, bc1, bc2 = co
    return fk1 / (np.exp(fk2 / (bc1 + bc2 * T)) - 1.0)


def construir_pila():
    """Todos los cuadros con C14 y C15 en los caches. Guarda BT y los coeficientes Planck (mediana, se comprueba que
    no cambian entre cuadros)."""
    idx = K.indice()
    cs = sorted(c for c in idx if 14 in idx[c] and 15 in idx[c])
    n = len(cs)
    b14 = np.full((n,) + LAT.shape, np.nan, "float32")
    b15 = np.full_like(b14, np.nan)
    b11 = np.full_like(b14, np.nan)
    cos = {14: [], 15: [], 11: []}
    for i, c in enumerate(cs):
        for b, dst in ((14, b14), (15, b15), (11, b11)):
            r = K.banda(idx, c, b)
            if r is None:
                continue
            rad, co = r
            dst[i] = bt(rad, co)
            cos[b].append(co)
    co = {}
    for b in cos:
        a = np.array(cos[b])
        co[b] = np.median(a, axis=0)
        print(f"C{b:02d}: {len(a)} cuadros, Planck max desviacion relativa {np.max(np.abs(a / co[b] - 1)):.2e}")
    os.makedirs(H22, exist_ok=True)
    np.savez_compressed(PILA, cs=np.array(cs), b14=b14, b15=b15, b11=b11, co14=co[14], co15=co[15], co11=co[11])
    print("pila", n, "cuadros ->", PILA)


class Pila:
    def __init__(self):
        z = np.load(PILA)
        b14, b15 = z["b14"], z["b15"]
        ok = np.isfinite(b14).all(axis=(1, 2)) & np.isfinite(b15).all(axis=(1, 2))
        # cuadros con algun relleno en la ventana: fuera de la pila (no entran ni a la base ni a la prueba)
        self.descartados = [str(c) for c in z["cs"][~ok]]
        self.cs = [str(c) for c in z["cs"][ok]]
        self.T = np.array([datetime.strptime(c, "%Y%m%d_%H%M") for c in self.cs])
        self.pos = {c: i for i, c in enumerate(self.cs)}
        self.b14, self.b15, self.b11 = b14[ok], b15[ok], z["b11"][ok]
        self.btd = self.b14 - self.b15            # split window 11,2 - 12,3
        self.btd8 = self.b11 - self.b14           # 8,4 - 11,2 (exploratorio)
        self.co14, self.co15 = tuple(z["co14"]), tuple(z["co15"])
        self.tod = np.array([t.hour * 60 + t.minute for t in self.T])
        self._base = {}

    def sel_base(self, i, dias=BASE_DIAS, tod=BASE_TOD_MIN):
        t = self.T[i]
        d = np.abs(((self.tod - self.tod[i]) + 720) % 1440 - 720)
        return np.nonzero((self.T >= t - timedelta(days=dias)) & (self.T <= t - timedelta(hours=3)) & (d <= tod))[0]

    def base(self, i, dias=BASE_DIAS, tod=BASE_TOD_MIN, pct=BASE_PCT):
        """Linea base del cuadro i: (B11, Bbtd, Bbtd8, n) o None. B11 = percentil pct de BT11 del mismo pixel en los
        `dias` previos a la misma hora del dia +- tod min; Bbtd = mediana de la BTD en los cuadros de esa base que
        estan a <= 2 K de B11 (lo despejado)."""
        k = (i, dias, tod, pct)
        if k in self._base:
            return self._base[k]
        sel = self.sel_base(i, dias, tod)
        if len(sel) < BASE_MIN_N:
            self._base[k] = None
            return None
        x = self.b14[sel]
        if not np.isfinite(x).all():
            raise ValueError(f"BT11 con NaN en la base de {self.cs[i]}")
        B11 = np.percentile(x, pct, axis=0)
        claro = x >= B11 - BASE_CLARO_K
        Bd = mediana_mascara(self.btd[sel], claro)
        Bd8 = mediana_mascara(self.btd8[sel], claro)
        self._base[k] = (B11.astype("float32"), Bd.astype("float32"), Bd8.astype("float32"), len(sel))
        return self._base[k]

    def anomalias(self, i, **kw):
        """(d11, dbtd, dbtd8, beta, e11) del cuadro i contra su linea base, o None."""
        b = self.base(i, **kw)
        if b is None:
            return None
        B11, Bd, Bd8, _ = b
        d11 = self.b14[i] - B11
        dbtd = self.btd[i] - Bd
        dbtd8 = self.btd8[i] - Bd8
        beta, e11 = beta_base(self.b14[i], self.b15[i], B11, B11 - Bd, self.co14, self.co15)
        return d11, dbtd, dbtd8, beta, e11


def mediana_mascara(v, m):
    """Mediana a lo largo del eje 0 de v donde m es verdadero y v es finito (igual a nanmedian, sin su lentitud)."""
    a = np.where(m & np.isfinite(v), v, np.inf)
    a = np.sort(a, axis=0)
    n = np.isfinite(a).sum(axis=0)
    lo = np.take_along_axis(a, np.clip((n - 1) // 2, 0, None)[None], 0)[0]
    hi = np.take_along_axis(a, np.clip(n // 2, 0, a.shape[0] - 1)[None], 0)[0]
    return np.where(n > 0, 0.5 * (lo + hi), np.nan)


def beta_base(b14, b15, c14, c15, co14, co15, tnube=T_NUBE_BETA, emin=0.02):
    """beta(12/11) = ln(1 - e12) / ln(1 - e11) con emisividades efectivas contra la linea base del mismo pixel como
    cielo despejado y una nube a `tnube` (beta "de tropopausa", Pavolonis 2010). Solo donde e11 >= emin y
    0 < e12 < 1: con el pixel a la temperatura de su base, beta no existe (se informa la fraccion con dato)."""
    r14, r15 = rad_de_bt(b14.astype("float64"), co14), rad_de_bt(b15.astype("float64"), co15)
    k14, k15 = rad_de_bt(c14.astype("float64"), co14), rad_de_bt(c15.astype("float64"), co15)
    n14, n15 = rad_de_bt(tnube, co14), rad_de_bt(tnube, co15)
    with np.errstate(all="ignore"):
        e11 = (r14 - k14) / (n14 - k14)
        e12 = (r15 - k15) / (n15 - k15)
        ok = (e11 >= emin) & (e11 < 1) & (e12 > 0) & (e12 < 1)
        beta = np.where(ok, np.log(1 - e12) / np.log(1 - e11), np.nan)
    return beta.astype("float32"), e11.astype("float32")


def sza(dt, lat=CRATER[0], lon=CRATER[1]):
    """Cenit solar en grados (aproximacion NOAA, error < 0,1 grados), dt en UTC."""
    doy = dt.timetuple().tm_yday
    h = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    g = 2 * np.pi / 365.0 * (doy - 1 + (h - 12) / 24.0)
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g)
                    - 0.040849 * np.sin(2 * g))
    dec = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
           + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    ha = np.radians((h * 60 + eqt + 4 * lon) / 4.0 - 180.0)
    la = np.radians(lat)
    return float(np.degrees(np.arccos(np.sin(la) * np.sin(dec) + np.cos(la) * np.cos(dec) * np.cos(ha))))


def eventos(patron="*.nc"):
    """Lista ordenada de (clave 'YYYYMMDD_HHMM', ruta) de los archivos de evento."""
    out = []
    for f in sorted(glob.glob(os.path.join(EVDIR, patron))):
        s = os.path.basename(f).split("_s")[1][:12]
        out.append((f"{s[:8]}_{s[8:12]}", f))
    return out


def leer_evento(f):
    """Huella y campos por pixel de un archivo de evento, ubicados en la ventana L1b.

    La grilla del archivo es un recorte del disco completo: su esquina es x/y_image_feature_region_bounds (base 1).
    fila ventana = y_bounds[0] - 1 + j - WIN['y0'];  col ventana = x_bounds[0] - 1 + i - WIN['x0'].
    """
    import netCDF4 as nc
    ds = nc.Dataset(f)

    def arr(k):
        return np.ma.filled(np.ma.asarray(ds[k][:]).astype("float64"), np.nan)

    ei = np.ma.filled(ds["event_idx"][:], -1).astype(int)
    y0 = int(ds["y_image_feature_region_bounds"][0]) - 1
    x0 = int(ds["x_image_feature_region_bounds"][0]) - 1
    jj, ii = np.indices(ei.shape)
    wy, wx = jj + y0 - WIN["y0"], ii + x0 - WIN["x0"]
    d = dict(ei=ei, wy=wy, wx=wx, lat=arr("latitude"), lon=arr("longitude"),
             bt11=arr("brightness_temperature_11micron"), bt12=arr("brightness_temperature_12micron"),
             S=arr("ash_spectral_signature_strength"), SL=arr("ash_spectral_signature_strength_lwir_only"),
             masa=arr("ash_mass_loading"), alt=arr("ash_cloud_height"),
             sza=float(np.ma.filled(ds["mean_feature_solar_zenith_angle"][:].astype("f8"), np.nan).ravel()[0]),
             ttrop=float(np.ma.filled(ds["mean_feature_tropopause_temperature"][:].astype("f8"), np.nan).ravel()[0]),
             alt_unidad=getattr(ds["ash_cloud_height"], "units", "?"),
             masa_unidad=getattr(ds["ash_mass_loading"], "units", "?"),
             tipo=str(ds["event_type"][0]), primera=str(ds["time_coverage_start_first_detection"][0]))
    ds.close()
    return d


def dentro(wy, wx):
    return (wy >= 0) & (wy < LAT.shape[0]) & (wx >= 0) & (wx < LAT.shape[1])


if __name__ == "__main__":
    construir_pila()
