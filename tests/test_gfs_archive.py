"""Tests del fetcher de GFS ARCHIVADO (GRIB2 byte-range, bucket noaa-gfs-bdp-pds).

Por qué existe: Open-Meteo devuelve null en niveles de presión pasados, así que
para validar eventos históricos (Láscar 27-jun con viento correcto, Calbuco 2015)
necesitamos el perfil GFS de archivo. GFS se publica en GRIB2 (508 MB/gránulo);
bajamos SOLO los registros que necesitamos por byte-range usando el `.idx`.

La lógica de selección (parseo del .idx → rangos de bytes, ciclo 6-horario más
cercano, índice de grilla del punto, parseo de nivel) es PURA y se testea sin red
ni eccodes. El decode real (eccodes + S3) hace skip si falta cualquiera de los dos.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetch.gfs_archive import (_cycle_for, _grid_index, _level_to_hpa,
                                    _parse_idx)

# .idx sintético con el formato real: num:offset:d=YYYYMMDDHH:VAR:LEVEL:anl:
_IDX = (
    "1:0:d=2026070200:PRMSL:mean sea level:anl:\n"
    "2:1000:d=2026070200:TMP:500 mb:anl:\n"
    "3:3000:d=2026070200:HGT:500 mb:anl:\n"
    "4:6000:d=2026070200:UGRD:500 mb:anl:\n"
    "5:6500:d=2026070200:TMP:surface:anl:\n"       # último registro (end=None)
)


def test_parse_idx_byte_ranges():
    """Cada registro obtiene [start, end] con end = (offset del siguiente − 1);
    el último queda con end=None (lo resuelve el fetcher con el tamaño del archivo)."""
    recs = _parse_idx(_IDX)
    by = {(r["var"], r["level"]): r for r in recs}
    assert by[("TMP", "500 mb")]["start"] == 1000
    assert by[("TMP", "500 mb")]["end"] == 2999          # 3000 − 1
    assert by[("HGT", "500 mb")]["start"] == 3000
    assert by[("UGRD", "500 mb")]["end"] == 6499          # 6500 − 1
    assert by[("TMP", "surface")]["end"] is None          # último → None
    # El date se conserva para datar el ciclo.
    assert by[("TMP", "500 mb")]["date"] == "2026070200"


def test_parse_idx_ignores_blank_lines():
    recs = _parse_idx(_IDX + "\n\n")
    assert len(recs) == 5


def test_level_to_hpa():
    assert _level_to_hpa("500 mb") == 500.0
    assert _level_to_hpa("0.4 mb") == 0.4
    assert _level_to_hpa("surface") is None
    assert _level_to_hpa("mean sea level") is None
    assert _level_to_hpa("2 m above ground") is None


def test_cycle_for_nearest_6h():
    """El ciclo GFS más cercano (00/06/12/18Z) a dt."""
    # 13:10 → más cerca de 12Z (1h10) que de 18Z (4h50).
    y, h, cdt, gap = _cycle_for(datetime(2026, 6, 27, 13, 10, tzinfo=timezone.utc))
    assert (y, h) == ("20260627", "12")
    assert abs(gap - 70.0) < 1e-6                          # 70 min

    # 03:00 → equidistante 00 y 06; round-half va a 00 (más temprano, determinista).
    y, h, cdt, gap = _cycle_for(datetime(2026, 6, 27, 3, 0, tzinfo=timezone.utc))
    assert h in ("00", "06")

    # 23:00 → el más cercano es 00Z del DÍA SIGUIENTE (1h), no 18Z (5h).
    y, h, cdt, gap = _cycle_for(datetime(2026, 6, 27, 23, 0, tzinfo=timezone.utc))
    assert (y, h) == ("20260628", "00")
    assert abs(gap - 60.0) < 1e-6


def test_cycle_for_naive_dt_is_utc():
    y, h, cdt, gap = _cycle_for(datetime(2026, 6, 27, 12, 0))   # sin tz
    assert (y, h) == ("20260627", "12") and gap == 0.0


def test_grid_index_gfs_0p25():
    """Índice plano en la grilla GFS 0.25° (lat0=90, lon0=0, dx=dy=0.25, Ni=1440).

    Láscar (−23.37, −67.73) → lon este 292.27. j=round((90−(−23.37))/0.25),
    i=round(292.27/0.25). El índice debe caer dentro del array (1440×721)."""
    ni, nj = 1440, 721
    idx = _grid_index(90.0, 0.0, 0.25, 0.25, ni, -23.37, -67.73)
    j = round((90.0 - (-23.37)) / 0.25)
    i = round((292.27) / 0.25) % ni
    assert idx == j * ni + i
    assert 0 <= idx < ni * nj


def test_grid_index_wraps_negative_lon():
    """lon negativa se normaliza a [0,360): −67.73 y 292.27 dan el mismo índice."""
    ni = 1440
    a = _grid_index(90.0, 0.0, 0.25, 0.25, ni, -23.37, -67.73)
    b = _grid_index(90.0, 0.0, 0.25, 0.25, ni, -23.37, 292.27)
    assert a == b


# ── Contrato del dato real (RED + eccodes; skip si falta alguno) ────────────

def _deps_ok() -> bool:
    try:
        import eccodes  # noqa: F401
        import s3fs
        s3 = s3fs.S3FileSystem(anon=True)
        s3.ls("noaa-gfs-bdp-pds/", detail=False)
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _deps_ok(), reason="eccodes o S3 noaa-gfs-bdp-pds no disponible")
def test_fetch_gfs_profile_archive_lascar():
    """Perfil T(z) archivado sobre Láscar: T decrece y HGT crece con la altura,
    rangos físicos, y la tropopausa cae en 6–20 km."""
    from src.fetch.gfs_archive import fetch_gfs_profile_archive

    # Fecha reciente del archivo (evita depender de un evento puntual).
    dt = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0,
                                            microsecond=0)
    for back_days in range(1, 4):
        prof = fetch_gfs_profile_archive(-23.37, -67.73,
                                         dt.replace(day=max(1, dt.day - back_days)))
        if prof:
            break
    if not prof:
        pytest.skip("sin gránulo GFS archivado accesible")

    levels = prof["levels"]
    assert len(levels) >= 5
    # Ordenado por altura y T monótona a grandes rasgos en la troposfera baja.
    zs = [l["z_m"] for l in levels]
    assert zs == sorted(zs)
    for l in levels:
        assert 150.0 < l["T_K"] < 330.0
        assert -500.0 < l["z_m"] < 60000.0
    trop = prof["tropopause"]
    assert trop is not None and 6000 <= trop["z_m"] <= 20000
    assert prof["source"].startswith("GFS archive")


@pytest.mark.skipif(not _deps_ok(), reason="eccodes o S3 noaa-gfs-bdp-pds no disponible")
def test_fetch_gfs_wind_profile_archive_lascar():
    """Perfil de viento archivado: u,v finitos y magnitud plausible (<150 m/s)."""
    from src.fetch.gfs_archive import fetch_gfs_wind_profile_archive
    import math

    dt = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0,
                                            microsecond=0)
    wp = None
    for back_days in range(1, 4):
        wp = fetch_gfs_wind_profile_archive(-23.37, -67.73,
                                            dt.replace(day=max(1, dt.day - back_days)))
        if wp:
            break
    if not wp:
        pytest.skip("sin gránulo GFS archivado accesible")

    assert len(wp["levels"]) >= 5
    for l in wp["levels"]:
        assert math.isfinite(l["u_ms"]) and math.isfinite(l["v_ms"])
        assert math.hypot(l["u_ms"], l["v_ms"]) < 150.0


if __name__ == "__main__":
    test_parse_idx_byte_ranges()
    test_parse_idx_ignores_blank_lines()
    test_level_to_hpa()
    test_cycle_for_nearest_6h()
    test_cycle_for_naive_dt_is_utc()
    test_grid_index_gfs_0p25()
    test_grid_index_wraps_negative_lon()
    print("OK — helpers puros gfs_archive")
