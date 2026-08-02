"""Tests de la corrección de parallax de 1er orden (georef de pluma en altura).

Por qué (geología → pipeline): GOES ve una pluma a altura h desplazada respecto de
su proyección vertical, porque mira de reojo desde el geoestacionario. El pixel de
la grilla fija queda MÁS LEJOS del subsatélite que la posición real → hay que
correr la pluma HACIA el subsatélite Δ ≈ h·tan(θ_zenit). Todo PURO/vectorizable.
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.process.parallax import (parallax_correct_field, parallax_shift,
                                   satellite_zenith_angle)

SAT_LON = -75.0
H = 35786023.0


def test_zenith_zero_at_subsatellite():
    """En el punto subsatélite (0, sat_lon) el ángulo cenital del satélite es 0."""
    thz = satellite_zenith_angle(0.0, SAT_LON, SAT_LON, H)
    assert abs(thz) < 1e-6


def test_zenith_grows_with_distance():
    """El ángulo cenital crece al alejarse del subsatélite."""
    a = satellite_zenith_angle(-20.0, -71.0, SAT_LON, H)
    b = satellite_zenith_angle(-45.0, -71.0, SAT_LON, H)
    assert 0 < a < b < math.radians(90)


def test_no_shift_at_zero_height():
    """Altura 0 → sin corrección (la pluma está en el suelo)."""
    lat, lon = parallax_shift(-40.0, -71.0, 0.0, SAT_LON, H)
    assert abs(lat - (-40.0)) < 1e-12 and abs(lon - (-71.0)) < 1e-12


def test_no_shift_at_subsatellite():
    """En el subsatélite θ=0 → sin desplazamiento aunque haya altura."""
    lat, lon = parallax_shift(0.0, SAT_LON, 10000.0, SAT_LON, H)
    assert abs(lat) < 1e-9 and abs(lon - SAT_LON) < 1e-9


def test_shift_toward_subsatellite_chile():
    """Chile (−40,−71) está al SUR y al ESTE del subsatélite (0,−75): la
    corrección debe mover la pluma al NORTE (lat sube hacia 0) y al OESTE (lon
    baja hacia −75)."""
    lat, lon = parallax_shift(-40.0, -71.0, 5000.0, SAT_LON, H)
    assert lat > -40.0            # hacia el norte (hacia el ecuador)
    assert lon < -71.0            # hacia el oeste (hacia −75)


def test_magnitude_about_1km_per_km_at_minus40():
    """A −40°S el desplazamiento es ~1 km por km de altura (tan θ ≈ 1.05).

    El audit lo estimó ~1.2 km/km; verificamos el orden de magnitud (0.9–1.3)."""
    lat0, lon0 = -40.0, -71.0
    lat, lon = parallax_shift(lat0, lon0, 1000.0, SAT_LON, H)
    # distancia desplazada en metros (equirectangular local)
    dn = math.radians(lat - lat0) * 6378137.0
    de = math.radians(lon - lon0) * 6378137.0 * math.cos(math.radians(lat0))
    dist_km = math.hypot(dn, de) / 1000.0
    assert 0.9 < dist_km < 1.3, dist_km


def test_shift_scales_linearly_with_height():
    """1er orden: el desplazamiento escala lineal con la altura."""
    lat0, lon0 = -38.0, -70.0
    d1 = parallax_shift(lat0, lon0, 2000.0, SAT_LON, H)
    d2 = parallax_shift(lat0, lon0, 6000.0, SAT_LON, H)
    m1 = math.hypot(d1[0] - lat0, d1[1] - lon0)
    m2 = math.hypot(d2[0] - lat0, d2[1] - lon0)
    assert abs(m2 / m1 - 3.0) < 0.05, (m1, m2)


def test_vectorized_arrays():
    """Acepta arrays (lat/lon/height) y devuelve arrays de la misma forma."""
    lat = np.array([-40.0, -35.0, -23.0])
    lon = np.array([-71.0, -70.0, -67.0])
    h = np.array([1000.0, 3000.0, 6000.0])
    clat, clon = parallax_shift(lat, lon, h, SAT_LON, H)
    assert clat.shape == lat.shape and clon.shape == lon.shape
    assert np.all(clat >= lat)              # todos al norte (hemisferio sur)
    # altura 0 no se testea acá; con h>0 todos se mueven.
    assert np.all(np.hypot(clat - lat, clon - lon) > 0)


def test_datum_es_amsl_no_altura_sobre_terreno():
    """La altura de entrada es AMSL/elipsoide, NO altura sobre el terreno.

    Pinea el contrato que el audit de ago-2026 encontró mal documentado: en Láscar
    (tope 10.6 km AMSL sobre terreno de 5.6 km) la corrección debe usar los 10.6 km
    completos. Si alguien pasara la altura sobre el terreno (5.0 km) el corrimiento
    sería ~la mitad, dejando kilómetros de error silencioso.
    """
    lat0, lon0 = -23.37, -67.73          # Láscar
    top_amsl_m = 10600.0
    terreno_m = 5600.0

    def _shift_km(h_m):
        lat, lon = parallax_shift(lat0, lon0, h_m, SAT_LON, H)
        dn = math.radians(lat - lat0) * 6378137.0
        de = math.radians(lon - lon0) * 6378137.0 * math.cos(math.radians(lat0))
        return math.hypot(dn, de) / 1000.0

    d_amsl = _shift_km(top_amsl_m)
    d_terreno = _shift_km(top_amsl_m - terreno_m)

    # Con AMSL el corrimiento es del orden de 5-6 km (tanθ ≈ 0.55 a esa latitud).
    assert 4.5 < d_amsl < 7.0, d_amsl
    # Usar altura sobre terreno perdería más de 2 km de corrección: el error que
    # el contrato ambiguo podía inducir.
    assert d_amsl - d_terreno > 2.0, (d_amsl, d_terreno)
    # Linealidad exacta en la altura (1er orden): la razón es la de las alturas.
    assert abs(d_terreno / d_amsl - (top_amsl_m - terreno_m) / top_amsl_m) < 1e-6


def test_field_leaves_non_plume_pixels_intact():
    """En un campo, los píxeles con altura NaN (sin pluma) NO se mueven; solo se
    corren los de la pluma (altura finita)."""
    lat = np.array([[-40.0, -40.0], [-39.0, -39.0]])
    lon = np.array([[-71.0, -70.0], [-71.0, -70.0]])
    h = np.array([[5000.0, np.nan], [np.nan, 3000.0]])   # 2 con pluma, 2 sin
    clat, clon = parallax_correct_field(lat, lon, h)
    # Sin pluma → intactos.
    assert clat[0, 1] == -40.0 and clon[0, 1] == -70.0
    assert clat[1, 0] == -39.0 and clon[1, 0] == -71.0
    # Con pluma → movidos hacia el norte (hemisferio sur).
    assert clat[0, 0] > -40.0 and clat[1, 1] > -39.0


if __name__ == "__main__":
    for fn in list(globals().values()):
        if callable(fn) and getattr(fn, "__name__", "").startswith("test_"):
            fn()
    print("OK — parallax puro")
