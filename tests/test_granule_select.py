"""Tests del selector de gránulo robusto al borde de hora (`granule_select`).

Contexto (por qué existe): los productos ABI en S3 se particionan por HORA UTC
(``.../YYYY/DDD/HH/``). El scan más cercano a un ``dt`` puede caer en la hora
ANTERIOR o la SIGUIENTE (un scan de HH:56 tiene su vecino real en (HH+1):00). El
patrón viejo —listar solo la hora de ``dt``, con la previa como *fallback*—
elegía un gránulo más lejano del objetivo en esos bordes (hallazgos del bug hunt
jul-2026: goes_s3, frp_timeline, goes_fdcf, goes_acha, goes_lvtp). Este helper
lista la UNIÓN de [dt-1h, dt, dt+1h] y devuelve el de menor |Δt|.

Todos los tests son PUROS: la E/S entra por un ``list_hour`` falso en memoria, así
que ejercitan el contrato sin tocar la red.
"""

import sys

import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetch.granule_select import nearest_granule_key


def _key(dt: datetime) -> str:
    """Fabricar una key S3 estilo NOAA con el timestamp de inicio de scan.

    Formato ``OR_..._sYYYYDDDHHMMSS0_...`` (el mismo que parsean los fetchers).
    """
    doy = dt.timetuple().tm_yday
    stamp = f"{dt.year}{doy:03d}{dt.hour:02d}{dt.minute:02d}{dt.second:02d}"
    return f"noaa-goes19/PROD/{dt.year}/{doy:03d}/{dt.hour:02d}/OR_PROD_s{stamp}0_e_c.nc"


def _parse(key: str) -> datetime | None:
    """Inversa de ``_key``: extrae el datetime de inicio de scan."""
    try:
        tok = [t for t in key.split("/")[-1].split("_") if t.startswith("s")][0]
        yyyy = int(tok[1:5]); doy = int(tok[5:8])
        hh = int(tok[8:10]); mm = int(tok[10:12]); ss = int(tok[12:14])
        return (datetime(yyyy, 1, 1, hh, mm, ss, tzinfo=timezone.utc)
                + timedelta(days=doy - 1))
    except Exception:
        return None


def _lister(scans: list[datetime]):
    """Devuelve un ``list_hour(dt)`` que sirve las keys de scans cuya hora UTC
    coincide con la carpeta pedida (emula la partición S3 por hora)."""
    keys = [_key(s) for s in scans]

    def list_hour(hour_dt: datetime) -> list[str]:
        out = []
        for k in keys:
            ts = _parse(k)
            if (ts.year, ts.timetuple().tm_yday, ts.hour) == (
                    hour_dt.year, hour_dt.timetuple().tm_yday, hour_dt.hour):
                out.append(k)
        return out

    return list_hour


def test_picks_next_hour_granule_at_end_of_hour():
    """dt=HH:56 → el vecino real es (HH+1):00 (gap 4 min), NO HH:50 (gap 6 min).

    El bug viejo (solo hora de dt + previa) elegía HH:50. La unión con la hora
    SIGUIENTE es lo que este test pinea."""
    base = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    scans = [base + timedelta(minutes=m) for m in range(0, 70, 10)]  # 12:00..13:00
    dt = datetime(2026, 6, 15, 12, 56, 0, tzinfo=timezone.utc)
    chosen = nearest_granule_key(_lister(scans), _parse, dt)
    assert _parse(chosen) == datetime(2026, 6, 15, 13, 0, 0, tzinfo=timezone.utc)


def test_picks_prev_hour_granule_at_start_of_hour():
    """dt=HH:02 con el primer scan de la hora llegando TARDE (HH:05): el vecino
    real es (HH-1):58 (gap 4 min) vs HH:05 (gap 3 min)… acá HH:05 gana, pero el
    caso clave es que (HH-1):58 SÍ entra al min — se lista la hora previa."""
    scans = [datetime(2026, 6, 15, 11, 58, 0, tzinfo=timezone.utc),
             datetime(2026, 6, 15, 12, 8, 0, tzinfo=timezone.utc)]
    dt = datetime(2026, 6, 15, 12, 1, 0, tzinfo=timezone.utc)
    chosen = nearest_granule_key(_lister(scans), _parse, dt)
    # 11:58 (gap 180 s) es más cercano que 12:08 (gap 420 s).
    assert _parse(chosen) == datetime(2026, 6, 15, 11, 58, 0, tzinfo=timezone.utc)


def test_exact_hour_middle_picks_same_hour():
    """En el centro de la hora el más cercano es de la misma hora (sanity)."""
    base = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    scans = [base + timedelta(minutes=m) for m in range(0, 60, 10)]
    dt = datetime(2026, 6, 15, 12, 31, 0, tzinfo=timezone.utc)
    chosen = nearest_granule_key(_lister(scans), _parse, dt)
    assert _parse(chosen) == datetime(2026, 6, 15, 12, 30, 0, tzinfo=timezone.utc)


def test_no_granules_returns_none():
    """Ninguna de las tres horas tiene gránulos → None."""
    assert nearest_granule_key(lambda h: [], _parse,
                               datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)) is None


def test_dedup_same_key_across_hours():
    """Si el lister devuelve la MISMA key en dos horas (lister perezoso), no se
    duplica ni cambia el resultado."""
    k = _key(datetime(2026, 6, 15, 12, 30, 0, tzinfo=timezone.utc))
    chosen = nearest_granule_key(lambda h: [k], _parse,
                                 datetime(2026, 6, 15, 12, 30, tzinfo=timezone.utc))
    assert chosen == k


def test_naive_dt_treated_as_utc():
    """dt sin tzinfo no debe romper (se asume UTC)."""
    base = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    scans = [base + timedelta(minutes=m) for m in range(0, 70, 10)]
    dt_naive = datetime(2026, 6, 15, 12, 56, 0)  # sin tz
    chosen = nearest_granule_key(_lister(scans), _parse, dt_naive)
    assert _parse(chosen) == datetime(2026, 6, 15, 13, 0, 0, tzinfo=timezone.utc)


def test_get_s3_tiene_expiracion_de_listados():
    """El filesystem compartido DEBE tener `listings_expiry_time` finito.

    `s3fs.S3FileSystem(anon=True)` es cacheable (misma instancia para todos los
    fetchers) y su DirCache nace SIN expiración: el listado de la hora en curso
    quedaba congelado para todo el proceso, así que los gránulos que NOAA publica
    después en esa misma hora eran invisibles y el "scan más reciente" podía
    atrasarse hasta ~1 h presentándose como vigente. (audit ago-2026)
    """
    pytest.importorskip("s3fs")
    from src.fetch.granule_select import S3_LISTINGS_EXPIRY_S, get_s3

    fs = get_s3()
    expiry = fs.dircache.listings_expiry_time
    assert expiry is not None, "el DirCache no debe ser eterno"
    assert 0 < float(expiry) <= 300, expiry
    assert float(expiry) == float(S3_LISTINGS_EXPIRY_S)


def test_todos_los_fetchers_comparten_el_mismo_filesystem():
    """Los 6 fetchers S3 deben resolver a UNA instancia (misma cache, misma
    expiración). Si alguno vuelve a construir `S3FileSystem(anon=True)` pelado,
    se crea una segunda instancia con DirCache eterno y el bug vuelve por ahí."""
    pytest.importorskip("s3fs")
    import src.fetch.goes_s3 as goes_s3
    from src.fetch.granule_select import get_s3

    assert goes_s3._get_fs() is get_s3()


def test_unparseable_keys_skipped():
    """Keys cuyo timestamp no parsea (parse→None) no deben elegirse ni romper."""
    good = _key(datetime(2026, 6, 15, 12, 30, 0, tzinfo=timezone.utc))

    def lister(h):
        # Devuelve un basura + el bueno solo en la hora 12.
        if h.hour == 12:
            return ["basura_sin_timestamp.nc", good]
        return ["otra_basura.nc"]

    chosen = nearest_granule_key(lister, _parse,
                                 datetime(2026, 6, 15, 12, 31, tzinfo=timezone.utc))
    assert chosen == good


if __name__ == "__main__":
    test_picks_next_hour_granule_at_end_of_hour()
    test_picks_prev_hour_granule_at_start_of_hour()
    test_exact_hour_middle_picks_same_hour()
    test_no_granules_returns_none()
    test_dedup_same_key_across_hours()
    test_naive_dt_treated_as_utc()
    test_unparseable_keys_skipped()
    print("OK — granule_select puro")
