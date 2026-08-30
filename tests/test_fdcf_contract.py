"""Contrato de salida de los lectores FDCF (`scan_dt` como testigo del dato).

Por qué importa, antes que el cómo: el dashboard de guardia pinta un KPI de
"hot spots" a partir de `fetch_latest_hotspots`. Un `0` puede significar dos
cosas OPUESTAS para un volcán:

  1. NOAA procesó el scan y no detectó anomalía térmica → el volcán está en
     calma y el KPI verde es la verdad.
  2. No se pudo consultar el dato (S3 caído, gránulo no publicado, NetCDF
     roto) → **no sabemos nada**, y el volcán puede estar en erupción mientras
     la pantalla muestra exactamente lo mismo que un día tranquilo.

La función distingue los dos casos con `scan_dt`: no-None = verificado,
None = no verificable (y entonces la lista SIEMPRE viene vacía). Era un
contrato accidental, sin docstring ni test, y por eso los consumidores lo
ignoraban. Acá queda pineado en las dos direcciones, con fakes y sin red.

El test clave es `test_exito_con_cero_detecciones_trae_scan_dt`: es el único
que separa "vacío verificado" de "no verificado", que es justo la distinción
que el modo de falla borraba.
"""
import contextlib
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

sys.path.insert(0, str(Path(__file__).parent.parent))

pytest.importorskip("pyproj")

H = 35786023.0
SAT_LON = -75.0
GRID = 400

# Nombre NOAA real (parseable por _parse_scan_time): 2026 doy=115 12:00:21 UTC
KEY = ("noaa-goes19/ABI-L2-FDCF/2026/115/12/"
       "OR_ABI-L2-FDCF-M6_G19_s20261151200216_e20261151209524_c20261151210037.nc")
SCAN_DT = datetime(2026, 4, 25, 12, 0, 21, tzinfo=timezone.utc)

CHILE = {"lat_min": -56, "lat_max": -17, "lon_min": -76, "lon_max": -66}
VILLARRICA = (-39.42, -71.93, 10, 120.0)          # lat, lon, Mask, FRP MW
BOX_CON_HOTSPOT = {"lat_min": -40.0, "lat_max": -38.8,
                   "lon_min": -72.6, "lon_max": -71.3}
# Mismo tamaño de encuadre, sobre mar abierto frente a Valparaíso: dentro del
# disco visible y del grid sintético, pero sin ningún píxel caliente.
BOX_SIN_HOTSPOT = {"lat_min": -34.0, "lat_max": -32.8,
                   "lon_min": -74.5, "lon_max": -73.2}


def _fdcf_ds():
    """NetCDF FDCF sintético: grilla geos sobre Chile con 1 píxel caliente.

    Fondo Mask=50 (no-fire) y Power=NaN, como un scan real sin incendios.
    """
    from pyproj import Proj
    p = Proj(proj="geos", lon_0=SAT_LON, h=H, ellps="GRS80", sweep="x")

    lons = [CHILE["lon_min"], CHILE["lon_max"]] * 2
    lats = [CHILE["lat_min"]] * 2 + [CHILE["lat_max"]] * 2
    xm, ym = p(lons, lats)
    x_rad = np.linspace(min(xm) / H - 0.002, max(xm) / H + 0.002, GRID)
    y_rad = np.linspace(max(ym) / H + 0.002, min(ym) / H - 0.002, GRID)

    mask = np.full((GRID, GRID), 50, dtype="uint8")
    power = np.full((GRID, GRID), np.nan)
    temp = np.full((GRID, GRID), np.nan)
    area = np.full((GRID, GRID), np.nan)

    lat, lon, m_v, frp = VILLARRICA
    xm1, ym1 = p(lon, lat)
    c = int(np.argmin(np.abs(x_rad - xm1 / H)))
    r = int(np.argmin(np.abs(y_rad - ym1 / H)))
    mask[r, c] = m_v
    power[r, c] = frp
    temp[r, c] = 350.0
    area[r, c] = 1.5

    return xr.Dataset(
        {"Mask": (("y", "x"), mask), "Power": (("y", "x"), power),
         "Temp": (("y", "x"), temp), "Area": (("y", "x"), area),
         "goes_imager_projection": ((), 0, {
             "longitude_of_projection_origin": SAT_LON,
             "perspective_point_height": H})},
        coords={"x": x_rad, "y": y_rad})


class _FakeS3:
    """s3fs mínimo: `ls` devuelve keys fijas, `open` un buffer vacío.

    Cada operación puede configurarse para explotar, que es como se simulan los
    dos modos de falla de red sin tocar la red.
    """

    def __init__(self, keys=(KEY,), ls_exc=None, open_exc=None):
        self.keys = list(keys)
        self.ls_exc = ls_exc
        self.open_exc = open_exc

    def ls(self, prefix, **kw):
        if self.ls_exc is not None:
            raise self.ls_exc
        return list(self.keys)

    def open(self, key, mode="rb", **kw):
        if self.open_exc is not None:
            raise self.open_exc
        return contextlib.nullcontext(io.BytesIO(b""))


@pytest.fixture()
def fdcf(monkeypatch):
    """Módulo goes_fdcf con S3 y xarray fakeados; devuelve un instalador."""
    import src.fetch.goes_fdcf as mod

    ds = _fdcf_ds()
    monkeypatch.setattr(xr, "open_dataset", lambda f, **kw: ds)

    def instalar(**kw):
        fake = _FakeS3(**kw)
        monkeypatch.setattr(mod, "_get_s3", lambda *a, **k: fake)
        return fake

    mod._instalar = instalar
    try:
        yield mod
    finally:
        del mod._instalar


# --------------------------------------------------------------------------
# Éxito: scan_dt es el testigo de "esto se leyó de verdad"
# --------------------------------------------------------------------------

def test_exito_con_detecciones_trae_scan_dt(fdcf):
    """Camino feliz: hay hotspot en el encuadre y viene fechado."""
    fdcf._instalar()
    hs, scan_dt = fdcf.fetch_latest_hotspots(bounds=BOX_CON_HOTSPOT)

    assert len(hs) == 1, [h.to_dict() for h in hs]
    assert hs[0].frp_mw == 120.0
    assert scan_dt is not None
    assert scan_dt == SCAN_DT


def test_exito_con_cero_detecciones_trae_scan_dt(fdcf):
    """EL test del contrato: cero detecciones NO es cero información.

    El scan se leyó completo y el encuadre no tiene píxeles calientes. La lista
    viene vacía, pero `scan_dt` NO es None — es lo único que le permite a la
    vista pintar "0 hot spots a las 12:00Z" en vez de "FDCF no consultable".
    """
    fdcf._instalar()
    hs, scan_dt = fdcf.fetch_latest_hotspots(bounds=BOX_SIN_HOTSPOT)

    assert hs == []
    assert scan_dt is not None, (
        "vacío verificado quedó indistinguible de no-verificado: el KPI "
        "no puede saber si el 0 es calma real o S3 caído")
    assert scan_dt == SCAN_DT


# --------------------------------------------------------------------------
# Falla: los cuatro caminos devuelven ([], None), nunca un cero presentable
# --------------------------------------------------------------------------

def test_falla_de_open_devuelve_no_verificable(fdcf):
    """S3 lista el gránulo pero no lo deja abrir (timeout / conexión cortada)."""
    fdcf._instalar(open_exc=OSError("connection reset by peer"))
    hs, scan_dt = fdcf.fetch_latest_hotspots(bounds=BOX_CON_HOTSPOT)

    assert hs == []
    assert scan_dt is None


def test_falla_de_listado_devuelve_no_verificable(fdcf):
    """`ls` explota en todas las horas: no hay ni siquiera un gránulo candidato."""
    fdcf._instalar(ls_exc=OSError("S3 unreachable"))
    hs, scan_dt = fdcf.fetch_latest_hotspots(bounds=BOX_CON_HOTSPOT)

    assert hs == []
    assert scan_dt is None


def test_listado_vacio_devuelve_no_verificable(fdcf):
    """S3 contesta pero NOAA no publicó nada: tampoco se verificó el volcán."""
    fdcf._instalar(keys=())
    hs, scan_dt = fdcf.fetch_latest_hotspots(bounds=BOX_CON_HOTSPOT)

    assert hs == []
    assert scan_dt is None


def test_import_error_de_s3fs_devuelve_no_verificable(fdcf, monkeypatch):
    """Sin s3fs no se consultó nada. `sys.modules[x] = None` hace que
    `import x` levante ImportError, que es el camino que queremos ejercitar."""
    fdcf._instalar()
    monkeypatch.setitem(sys.modules, "s3fs", None)
    hs, scan_dt = fdcf.fetch_latest_hotspots(bounds=BOX_CON_HOTSPOT)

    assert hs == []
    assert scan_dt is None


def test_nombre_de_archivo_no_fechable_devuelve_no_verificable(fdcf):
    """Un gránulo cuyo nombre no se puede parsear se descarta ENTERO.

    Devolver `(hotspots, None)` rompería el invariante en la otra dirección: el
    consumidor que chequea `scan_dt is None` para pintar "no consultable"
    tiraría detecciones reales, y el que no lo chequea mostraría un conteo sin
    poder decir de cuándo es.
    """
    fdcf._instalar(keys=("noaa-goes19/ABI-L2-FDCF/2026/115/12/basura.nc",))
    hs, scan_dt = fdcf.fetch_latest_hotspots(bounds=BOX_CON_HOTSPOT)

    assert scan_dt is None
    assert hs == [], "con scan_dt=None la lista tiene que venir vacía"


# --------------------------------------------------------------------------
# La variante histórica respeta el MISMO contrato
# --------------------------------------------------------------------------

def test_historico_exito_trae_scan_dt(fdcf):
    """Backfill: mismo testigo. Un bucket de FRP sin scan_dt no es calma."""
    fdcf._instalar()
    hs, scan_dt = fdcf.fetch_hotspots_at_time(
        datetime(2026, 4, 25, 12, 3, tzinfo=timezone.utc),
        bounds=BOX_CON_HOTSPOT)

    assert len(hs) == 1
    assert scan_dt == SCAN_DT


def test_historico_cero_detecciones_trae_scan_dt(fdcf):
    """Vacío verificado también en el camino histórico."""
    fdcf._instalar()
    hs, scan_dt = fdcf.fetch_hotspots_at_time(
        datetime(2026, 4, 25, 12, 3, tzinfo=timezone.utc),
        bounds=BOX_SIN_HOTSPOT)

    assert hs == []
    assert scan_dt is not None


@pytest.mark.parametrize("kw", [
    {"open_exc": OSError("connection reset by peer")},
    {"ls_exc": OSError("S3 unreachable")},
    {"keys": ()},
])
def test_historico_fallas_devuelven_no_verificable(fdcf, kw):
    fdcf._instalar(**kw)
    hs, scan_dt = fdcf.fetch_hotspots_at_time(
        datetime(2026, 4, 25, 12, 3, tzinfo=timezone.utc),
        bounds=BOX_CON_HOTSPOT)

    assert hs == []
    assert scan_dt is None


def test_historico_import_error_devuelve_no_verificable(fdcf, monkeypatch):
    fdcf._instalar()
    monkeypatch.setitem(sys.modules, "s3fs", None)
    hs, scan_dt = fdcf.fetch_hotspots_at_time(
        datetime(2026, 4, 25, 12, 3, tzinfo=timezone.utc),
        bounds=BOX_CON_HOTSPOT)

    assert hs == []
    assert scan_dt is None


# --------------------------------------------------------------------------
# Invariante global, escrito una vez
# --------------------------------------------------------------------------

@pytest.mark.parametrize("fn", ["fetch_latest_hotspots", "fetch_hotspots_at_time"])
@pytest.mark.parametrize("kw", [
    {}, {"open_exc": OSError("boom")}, {"ls_exc": OSError("boom")}, {"keys": ()},
    {"keys": ("noaa-goes19/ABI-L2-FDCF/2026/115/12/basura.nc",)},
])
@pytest.mark.parametrize("box", [BOX_CON_HOTSPOT, BOX_SIN_HOTSPOT, CHILE])
def test_scan_dt_none_implica_lista_vacia(fdcf, fn, kw, box):
    """`scan_dt is None` ⟹ `hotspots == []`, en TODA combinación.

    Es la mitad del contrato que un consumidor podría violar sin darse cuenta
    (la otra —vacío con fecha— la cubren los tests de éxito de arriba).
    """
    fdcf._instalar(**kw)
    if fn == "fetch_latest_hotspots":
        hs, scan_dt = fdcf.fetch_latest_hotspots(bounds=box)
    else:
        hs, scan_dt = fdcf.fetch_hotspots_at_time(
            datetime(2026, 4, 25, 12, 3, tzinfo=timezone.utc), bounds=box)

    if scan_dt is None:
        assert hs == [], (fn, kw, box, [h.to_dict() for h in hs])
    else:
        assert isinstance(scan_dt, datetime) and scan_dt.tzinfo is not None
