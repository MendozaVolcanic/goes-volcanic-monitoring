# ════════════════════════════════════════════════════════════════════
# FICHA SDA · parallax.py · SDA: Monitoreo Volcánico GOES-19 · ID: SDA-GOES-01
# Objetivo      : corregir la georef de la pluma por su altura (parallax geoestacionario) — dónde está la pluma en el mapa
# Lógica        : una pluma a altura h se ve corrida hacia afuera del subsatélite; se la devuelve hacia adentro Δ=h·tan(θ_zenit)
# Modelo/método : geometría determinística (ángulo cenital del satélite + desplazamiento de 1er orden)
# Datos entrada : lat/lon del pixel + altura del tope sobre el ELIPSOIDE/AMSL (de la cadena propia o VOLCAT) — SIN datos personales
# Variables     : ángulo cenital del satélite, desplazamiento horizontal h·tan(θ), azimut hacia el subsatélite
# Limitaciones  : 1er orden (ignora curvatura fina y elipsoide); NO cambia el tope, solo su posición en el mapa; la altura DEBE ser AMSL (restar el terreno subcorrige ~50% sobre los Andes)
# Refs/datos    : Vicente et al. 2002 (parallax GOES); geometría geos estándar; hallazgo F4 del audit jul-2026
# Ficha completa: docs/FICHA_SDA_GOES.md
# ════════════════════════════════════════════════════════════════════
"""Corrección de parallax de 1er orden para la georef de una pluma en altura.

Por qué importa (geología → pipeline): GOES-19 es geoestacionario sobre el ecuador
a −75°. Mira Chile "de reojo" (ángulo cenital ~45–55°). Una pluma a altura ``h``
sobre el elipsoide se proyecta en la grilla fija del ABI en un punto **más alejado
del subsatélite** que su posición vertical real: la línea de visión oblicua
intercepta el tope de la pluma antes de llegar al suelo, y ese pixel se rotula con
la coordenada de suelo de más allá. El corrimiento crece con la altura y con el
ángulo de visión: a −40°S ronda **~1 km por km de altura** (tan θ ≈ 1.05).

Este módulo NO cambia la altura del tope — solo corrige **dónde** cae la pluma en
el mapa, moviéndola de vuelta hacia el subsatélite. Es 1er orden (Δ = h·tan θ),
suficiente para un producto INDICATIVO: el error residual (curvatura, elipsoide)
es chico frente a la resolución de 2 km del ABI y frente al propio corrimiento que
corrige. Fuera de esto, la pluma se dibuja hasta ~1.2 km desplazada a −40°S.

Todo PURO y vectorizable (escala a arrays de píxeles). Ver hallazgo F4 del audit.
"""

from __future__ import annotations

import numpy as np

try:
    from src.config import GOES19_PERSPECTIVE_POINT_HEIGHT as _H_DEFAULT
    from src.config import GOES19_SAT_LON as _SAT_LON_DEFAULT
except Exception:
    _SAT_LON_DEFAULT = -75.0
    _H_DEFAULT = 35786023.0

# Semieje mayor GRS80 (m) — la esfera de referencia para la geometría de 1er orden.
R_EARTH = 6378137.0


def satellite_zenith_angle(lat, lon, sat_lon=_SAT_LON_DEFAULT, sat_height_m=_H_DEFAULT):
    """Ángulo cenital del satélite (rad) en el punto (lat,lon).

    Es el ángulo entre el cenit local y la línea al satélite geoestacionario. En el
    subsatélite es 0 (satélite al cenit) y crece hacia el limbo. Fórmula por el
    triángulo Tierra-centro / punto / satélite (ley de senos):
    ``sin θ = r_s·sin γ / d``, con ``γ`` = ángulo central al subsatélite,
    ``r_s`` = radio geocéntrico del satélite, ``d`` = distancia punto→satélite.
    PURA, vectorizable.
    """
    lat_r = np.radians(np.asarray(lat, dtype="float64"))
    dlon_r = np.radians(np.asarray(lon, dtype="float64") - sat_lon)
    cos_g = np.clip(np.cos(lat_r) * np.cos(dlon_r), -1.0, 1.0)  # subsat lat = 0
    gamma = np.arccos(cos_g)
    rs = R_EARTH + sat_height_m
    d = np.sqrt(rs * rs + R_EARTH * R_EARTH - 2.0 * rs * R_EARTH * cos_g)
    sin_thz = np.clip(rs * np.sin(gamma) / d, -1.0, 1.0)
    return np.arcsin(sin_thz)


def parallax_shift(lat, lon, height_m, sat_lon=_SAT_LON_DEFAULT,
                   sat_height_m=_H_DEFAULT):
    """Corrige (lat,lon) de un pixel de pluma a altura ``height_m`` por parallax.

    Devuelve ``(lat_corr, lon_corr)`` — la posición movida **hacia el subsatélite**
    en Δ = ``height_m``·tan(θ_zenit). Escalar o array (misma forma que la entrada).
    1er orden: la magnitud es lineal en la altura y el desplazamiento se descompone
    en el azimut hacia el subsatélite (0, ``sat_lon``) en el plano tangente local.

    Args:
        lat, lon:      posición aparente del pixel (grados; escalar o array).
        height_m:      altura del tope sobre el ELIPSOIDE / AMSL (m) — el mismo datum
                       que devuelven `top_km`/`field_km` de la cadena propia y VOLCAT.
                       **NO restar la elevación del terreno**: la navegación del ABI
                       proyecta la línea de visión sobre el elipsoide GRS80, así que el
                       corrimiento aparente es h_elipsoide·tanθ. Pasar altura sobre el
                       terreno subcorrige gravemente donde el terreno es alto — en
                       Láscar (tope 10.6 km AMSL, terreno 5.6 km) corregiría 2.7 km en
                       vez de 5.8 km, dejando 3.1 km de error silencioso.
        sat_lon:       longitud subsatélite (−75° GOES-19).
        sat_height_m:  altura de perspectiva del satélite (del NetCDF L1b).
    """
    lat = np.asarray(lat, dtype="float64")
    lon = np.asarray(lon, dtype="float64")
    h = np.asarray(height_m, dtype="float64")

    thz = satellite_zenith_angle(lat, lon, sat_lon, sat_height_m)
    d_h = h * np.tan(thz)                       # desplazamiento horizontal (m)

    # Dirección hacia el subsatélite (0, sat_lon) en metros locales (ENU): norte y
    # este. Se normaliza a versor; d_h se reparte por sus componentes.
    lat_r = np.radians(lat)
    north_m = np.radians(0.0 - lat) * R_EARTH
    east_m = np.radians(sat_lon - lon) * R_EARTH * np.cos(lat_r)
    norm = np.hypot(north_m, east_m)
    # En el subsatélite norm=0 (y d_h=0): evitar 0/0 → sin desplazamiento.
    safe = norm > 0
    un = np.where(safe, north_m / np.where(safe, norm, 1.0), 0.0)
    ue = np.where(safe, east_m / np.where(safe, norm, 1.0), 0.0)

    dn = d_h * un
    de = d_h * ue
    dlat = np.degrees(dn / R_EARTH)
    dlon = np.degrees(de / (R_EARTH * np.cos(lat_r)))

    lat_c = lat + dlat
    lon_c = lon + dlon
    # Devolver escalares si la entrada era escalar (contrato amable).
    if lat_c.ndim == 0:
        return float(lat_c), float(lon_c)
    return lat_c, lon_c


def parallax_correct_field(lat, lon, height_m, sat_lon=_SAT_LON_DEFAULT,
                           sat_height_m=_H_DEFAULT):
    """Corrige un CAMPO de píxeles de pluma: cada pixel se mueve por SU altura.

    Pensado para la georef del mapa (``lat``/``lon`` 2D de la ventana + campo de
    altura por pixel). Donde la altura es NaN (sin pluma) el pixel queda **intacto**
    (desplazamiento 0), así solo se corren los píxeles de la pluma y el resto de la
    grilla no se mueve. ``height_m`` en metros sobre el ELIPSOIDE/AMSL — el mismo datum
    de ``field_km`` de los retrievals (NO restar la elevación del terreno; ver
    :func:`parallax_shift`). NaN = sin corrección. PURA.
    """
    h = np.asarray(height_m, dtype="float64")
    h = np.where(np.isfinite(h), h, 0.0)     # sin altura → sin desplazamiento
    return parallax_shift(lat, lon, h, sat_lon, sat_height_m)
