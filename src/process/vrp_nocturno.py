# ════════════════════════════════════════════════════════════════════
# FICHA SDA · vrp_nocturno.py  ·  SDA: Monitoreo Volcánico GOES-19 · ID: SDA-GOES-01 §C.1
# Objetivo      : decir, noche a noche y por volcán, si el cráter tiene material
#                 incandescente con más de ~10 MW de potencia radiativa, como
#                 contexto térmico para el turno de OVDAS. No es una alerta ni un
#                 detector de erupciones o de ceniza.
# Lógica        : a 3,9 µm un material incandescente que cubre una fracción mínima
#                 del píxel sube mucho la temperatura de brillo y casi nada a
#                 11 µm; ese exceso, contra un fondo coherente tomado del entorno,
#                 se convierte en megawatts (método del infrarrojo medio). Una
#                 noche se marca "encendida" si una parte de sus cuadros con el
#                 cráter visible supera 10 MW.
# Modelo/método : reglas físicas determinísticas y umbrales fijos. Sin ML.
# Datos entrada : ABI L1b RadF de GOES-19 (bandas C07 y C14, NOAA S3) y el
#                 catálogo RNVV del repo. Sin datos personales.
# Variables     : umbral de potencia (10 MW), fracción mínima de cuadros (25 %),
#                 mínimo de cuadros visibles (4), cenit solar ≥ 90°, vara de
#                 visibilidad (BT14 del cráter ≥ referencia despejada − 4 K).
# Limitaciones  : sólo de noche; no ve actividad bajo ~5 a 10 MW (lagos de lava
#                 chicos, fumarolas calientes); una nube sobre el cráter deja la
#                 noche "sin dato"; sin corrección atmosférica (ABI da 0,86 veces
#                 lo de MIROVA en mediana). Validado en un solo volcán chileno
#                 sobre el límite (Nevados de Chillán, 6 noches).
# Refs/datos    : Wooster y otros 2003 (método MIR); validación fuera de muestra
#                 contra MIROVA en docs/own_volcat/vrp_nocturno/INFORME.md
#                 (PR 87); hallazgo en docs/own_volcat/h17_regla_propia/.
# ════════════════════════════════════════════════════════════════════
"""Indicador nocturno de calor en el cráter (VRP a 3,9 µm desde la L1b de GOES-19).

Funciones puras (numpy), sin acceso a red: quien baje la L1b les pasa la radiancia
de la ventana del volcán. La regla es idéntica a la validada en
``docs/own_volcat/vrp_nocturno/`` (criterio del 22-11-2026, PR 87); cambiarla exige
volver a validar, no sólo pasar los tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional

import numpy as np

# Proyección fija de GOES-19 (atributos del NetCDF RadF): ángulos de barrido en rad.
REQ, RPOL = 6378137.0, 6356752.31414
HSAT = 35786023.0 + REQ
LON0 = -75.0
XS, XO, YS, YO = 5.6e-05, -0.151844, -5.6e-05, 0.151844
SIGMA = 5.670374419e-8

MEDIO_VENTANA = 12      # px: ventana de 25 x 25 píxeles de 2 km, el anillo de 14 km cabe
ZONA_KM = 6.0           # zona del cráter alrededor de la cumbre aparente (H9, H17)
ANILLO_KM = (8.0, 14.0) # entorno que da el fondo de la escena
UMBRAL_MW = 10.0        # potencia que enciende un cuadro (validado; 5 MW no decide)
FRACCION_MIN = 0.25     # parte de los cuadros visibles de la noche sobre el umbral
CUADROS_ENC_MIN = 2     # cuadros sobre el umbral; uno solo no enciende la noche
CUADROS_VIS_MIN = 4     # bajo esto la noche es "sin dato", nunca "apagada"
SZA_NOCHE = 90.0        # cenit solar mínimo: de día el 3,9 µm suma sol reflejado
VARA_VISIBLE_K = 4.0    # BT14 del cráter hasta 4 K bajo el cielo despejado (H9)
REF_CUADROS_MIN = 10    # cuadros nocturnos previos para fijar el cielo despejado
REF_NOCHES = 7          # noches previas que alimentan la referencia
REF_PERCENTIL = 90


# ── geometría ────────────────────────────────────────────────────────────────

def latlon_a_xy(lat, lon, h_m=0.0):
    """Ángulos de barrido ABI de un punto a ``h_m`` metros sobre el elipsoide.

    Con altura se usa la posición 3D real del punto, así que el ángulo ya lleva
    el paralaje: ABI navega al elipsoide y una cumbre de 3 km aparece corrida
    hacia el lado contrario al satélite (en Chillán, ~3 km al sur).
    """
    la, lo = np.radians(lat), np.radians(lon - LON0)
    e2 = 1 - RPOL ** 2 / REQ ** 2
    N = REQ / np.sqrt(1 - e2 * np.sin(la) ** 2)
    X = (N + h_m) * np.cos(la) * np.cos(lo)
    Y = (N + h_m) * np.cos(la) * np.sin(lo)
    Z = (N * (1 - e2) + h_m) * np.sin(la)
    sx, sy, sz = HSAT - X, -Y, Z
    return np.arcsin(-sy / np.sqrt(sx ** 2 + sy ** 2 + sz ** 2)), np.arctan(sz / sx)


def xy_a_latlon(x, y):
    """Inversa de la proyección fija (GOES-R PUG): lat/lon en el elipsoide."""
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


def cumbre_aparente(lat, lon, elevacion_m):
    """(lat, lon) donde ABI muestra la cumbre (paralaje por línea de vista)."""
    return xy_a_latlon(*latlon_a_xy(lat, lon, float(elevacion_m)))


def ventana(lat, lon, elevacion_m, medio=MEDIO_VENTANA):
    """(r0, r1, c0, c1) en la grilla de 2 km, centrada en la cumbre aparente.

    Es el recorte que hay que leer de C07 y de C14 (``Rad[r0:r1, c0:c1]``).
    """
    x, y = latlon_a_xy(lat, lon, float(elevacion_m))
    c, r = int(round((x - XO) / XS)), int(round((y - YO) / YS))
    return r - medio, r + medio + 1, c - medio, c + medio + 1


def _hav_km(lat, lon, la0, lo0):
    p1, p2 = np.radians(la0), np.radians(lat)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon - lo0) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


@dataclass(frozen=True)
class SitioVRP:
    """Máscaras de un volcán sobre su ventana. Se calcula una vez por volcán."""
    zona: np.ndarray
    anillo: np.ndarray
    area_km2: np.ndarray
    ventana: tuple


def sitio(lat, lon, elevacion_m, medio=MEDIO_VENTANA) -> SitioVRP:
    r0, r1, c0, c1 = ventana(lat, lon, elevacion_m, medio)
    cc, rr = np.meshgrid(np.arange(c0, c1), np.arange(r0, r1))
    glat, glon = xy_a_latlon(XO + XS * cc, YO + YS * rr)
    la, lo = cumbre_aparente(lat, lon, elevacion_m)
    d = _hav_km(glat, glon, la, lo)
    # Área por píxel desde la grilla (crece hacia el sur y hacia el borde del disco).
    R = 6371.0
    pla, plo = np.radians(glat), np.radians(glon)
    dly, dlx = np.gradient(pla)
    doy, dox = np.gradient(plo)
    cs = np.cos(pla)
    area = np.abs(R * dlx * R * cs * doy - R * cs * dox * R * dly)
    return SitioVRP(zona=d <= ZONA_KM, anillo=(d >= ANILLO_KM[0]) & (d <= ANILLO_KM[1]),
                    area_km2=area, ventana=(r0, r1, c0, c1))


# ── potencia por cuadro ──────────────────────────────────────────────────────

def _bt(rad, co):
    fk1, fk2, bc1, bc2 = co
    with np.errstate(invalid="ignore", divide="ignore"):
        return (fk2 / np.log(fk1 / rad + 1.0) - bc1) / bc2


def coef_mir(co7) -> float:
    """``a`` de L7(T) ≈ a·T⁴ entre 600 y 1.500 K con los Planck del propio NetCDF.

    Es la constante del método del infrarrojo medio: convierte exceso de radiancia
    a 3,9 µm en potencia sin conocer la temperatura ni el área de la lava.
    """
    fk1, fk2, bc1, bc2 = co7
    T = np.linspace(600, 1500, 901)
    L = fk1 / (np.exp(fk2 / (bc1 + bc2 * T)) - 1)
    return float(np.sum(L * T ** 4) / np.sum(T ** 8))


@dataclass(frozen=True)
class CuadroVRP:
    vrp_mw: float          # NaN si el cuadro no se puede evaluar (banda vacía, anillo sin datos)
    bt14_zona_k: float     # BT14 máxima de la zona: sirve para decidir si el cráter se ve
    n_calientes: int


def vrp_cuadro(rad7, co7, rad14, co14, s: SitioVRP) -> CuadroVRP:
    """VRP (MW) de un cuadro con el fondo coherente validado.

    QUÉ: píxel caliente = en la zona del cráter, BT7 − BT14 supera la mediana del
    anillo en máx(2 K, 3 desviaciones robustas) y su radiancia a 3,9 µm supera la
    de fondo. Fondo de cada píxel = Planck7(BT14 del propio píxel + mediana del
    anillo de BT7 − BT14).
    POR QUÉ ese fondo: la cumbre nevada es más fría que el entorno en las dos
    bandas; restarle la radiancia ABSOLUTA del anillo borraba su exceso (defecto
    encontrado en H17). Con el fondo del propio píxel el test y la potencia usan
    la misma referencia.
    """
    rad7 = np.asarray(rad7, dtype="float64")
    rad14 = np.asarray(rad14, dtype="float64")
    b7, b14 = _bt(rad7, co7), _bt(rad14, co14)
    D = b7 - b14
    dr = D[s.anillo]
    ok = np.isfinite(dr)
    if ok.sum() < 20 or not np.isfinite(D[s.zona]).any():
        return CuadroVRP(float("nan"), float("nan"), 0)
    med = float(np.median(dr[ok]))
    mad = float(np.median(np.abs(dr[ok] - med)))
    umb = max(2.0, 3 * 1.4826 * mad)
    fk1, fk2, bc1, bc2 = co7
    with np.errstate(over="ignore", invalid="ignore"):
        l7_fondo = fk1 / (np.exp(fk2 / (bc1 + bc2 * (b14 + med))) - 1)
    exceso = rad7 - l7_fondo
    cal = s.zona & ((D - med) >= umb) & (exceso > 0)
    vrp = float(np.nansum(s.area_km2[cal] * 1e6 * SIGMA / coef_mir(co7) * exceso[cal]) / 1e6)
    return CuadroVRP(vrp, float(np.nanmax(np.where(s.zona, b14, np.nan))), int(cal.sum()))


# ── noche ────────────────────────────────────────────────────────────────────

def cenit_solar(dt: datetime, lat: float, lon: float) -> float:
    """Cenit solar en grados (fórmula NOAA, ~0,1°). ``dt`` en UTC."""
    doy = dt.timetuple().tm_yday
    g = 2 * np.pi / 365 * (doy - 1 + (dt.hour - 12) / 24 + dt.minute / 1440)
    decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
            + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g)
                    - 0.040849 * np.sin(2 * g))
    ha = np.radians((dt.hour * 60 + dt.minute + eqt + 4 * lon) / 4 - 180)
    la = np.radians(lat)
    c = np.sin(la) * np.sin(decl) + np.cos(la) * np.cos(decl) * np.cos(ha)
    return float(np.degrees(np.arccos(np.clip(c, -1, 1))))


def es_nocturno(dt: datetime, lat: float, lon: float) -> bool:
    return cenit_solar(dt, lat, lon) >= SZA_NOCHE


def clave_noche(dt: datetime):
    """Noche D = de 18:00 UTC del día D−1 a 12:00 UTC del día D (en Chile, la que
    termina la mañana de D). Así una noche no se parte en dos fechas UTC."""
    return (dt + timedelta(hours=6)).date()


def referencia_despejado(bt14_previas: Iterable[float]) -> Optional[float]:
    """Cielo despejado del cráter: percentil 90 de la BT14 máxima de la zona en los
    cuadros nocturnos de las 7 noches previas. None si hay menos de 10: sin
    referencia no se puede decir si el cráter se ve, y la noche queda sin dato."""
    v = np.asarray([x for x in bt14_previas if x is not None and np.isfinite(x)], dtype="float64")
    if v.size < REF_CUADROS_MIN:
        return None
    return float(np.percentile(v, REF_PERCENTIL))


ESTADOS = ("encendido", "bajo_limite", "sin_dato", "de_dia")


def estado_noche(cuadros: Iterable[CuadroVRP], referencia_k: Optional[float],
                 nocturno: bool = True) -> dict:
    """Estado de una noche a partir de sus cuadros nocturnos.

    - ``de_dia``: no se evalúa (``nocturno=False``). Nunca se lee como calma.
    - ``sin_dato``: sin referencia de cielo despejado o con menos de 4 cuadros con
      el cráter visible. Una nube sobre el cráter apaga la señal: eso es "no se
      ve", no "frío".
    - ``encendido``: al menos 2 cuadros visibles con ≥ 10 MW que sean al menos el
      25 % de los visibles. Uno o dos cuadros sueltos en una noche larga no
      bastan (en Chillán, antes de calentarse, hubo noches con 1 a 3 cuadros
      sueltos sobre 10 MW y MIROVA en cero).
    - ``bajo_limite``: cráter visible y sin calor sobre ~10 MW. NO dice que el
      volcán esté frío: la actividad débil (MIROVA bajo 5 MW) queda siempre aquí.
    """
    base = {"n_cuadros": 0, "n_visibles": 0, "n_sobre_umbral": 0, "vrp_max_mw": None,
            "vrp_mediana_mw": None, "referencia_k": referencia_k}
    if not nocturno:
        return {"estado": "de_dia", **base}
    cs = list(cuadros)
    base["n_cuadros"] = len(cs)
    if referencia_k is None:
        return {"estado": "sin_dato", "motivo": "sin referencia de cielo despejado", **base}
    vis = [c for c in cs if np.isfinite(c.vrp_mw) and np.isfinite(c.bt14_zona_k)
           and c.bt14_zona_k >= referencia_k - VARA_VISIBLE_K]
    v = np.array([c.vrp_mw for c in vis], dtype="float64")
    k = int((v >= UMBRAL_MW).sum())
    base.update(n_visibles=len(vis), n_sobre_umbral=k,
                vrp_max_mw=float(v.max()) if v.size else None,
                vrp_mediana_mw=float(np.median(v)) if v.size else None)
    if len(vis) < CUADROS_VIS_MIN:
        return {"estado": "sin_dato", "motivo": "cráter cubierto o sin cuadros", **base}
    if k >= CUADROS_ENC_MIN and k >= FRACCION_MIN * len(vis):
        return {"estado": "encendido", **base}
    return {"estado": "bajo_limite", **base}
