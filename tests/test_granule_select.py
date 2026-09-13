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

import ast
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


# Los consumidores S3 del repo y el nombre por el que cada uno pide el
# filesystem. La lista es explicita a proposito: si aparece un fetcher nuevo,
# el guard de fuente de mas abajo lo obliga a pasar por `granule_select`, y
# sumarlo aca lo somete tambien al test de identidad.
_CONSUMIDORES_S3 = [
    ("src.fetch.goes_s3", "_get_fs"),
    ("src.fetch.goes_fdcf", "_get_s3"),
    ("src.fetch.goes_acha", "_get_s3"),
    ("src.fetch.goes_lvtp", "_get_s3"),
    ("src.fetch.gfs_archive", "_get_s3"),
    ("src.process.historic_l1b_rgb", "_get_fs"),
]


@pytest.mark.parametrize("modname,attr", _CONSUMIDORES_S3)
def test_todos_los_fetchers_comparten_el_mismo_filesystem(modname, attr):
    """Cada consumidor S3 debe resolver a LA MISMA instancia (misma cache,
    misma expiración). Si alguno vuelve a construir `S3FileSystem(anon=True)`
    pelado, s3fs le da otra instancia —los kwargs difieren— cuyo DirCache nace
    eterno, y el bug del "scan más reciente" atrasado hasta ~1 h vuelve por ahí.

    Por qué se ejerce la FUNCION y no se lee el fuente: la version anterior de
    este test decia cubrir "los 6 fetchers S3" y solo tocaba `goes_s3`. Darle
    a `goes_fdcf` un `_get_s3()` propio con `S3FileSystem(anon=True)` la dejaba
    verde (verificado por mutacion, ago-2026).
    """
    pytest.importorskip("s3fs")
    import importlib

    from src.fetch.granule_select import get_s3

    mod = importlib.import_module(modname)
    fn = getattr(mod, attr, None)
    assert callable(fn), f"{modname} no expone {attr}()"
    fs = fn()
    assert fs is get_s3(), (
        f"{modname}.{attr}() devuelve otra instancia de S3FileSystem: su "
        f"DirCache no comparte la expiracion de granule_select")
    assert fs.dircache.listings_expiry_time is not None, modname


def test_nadie_construye_un_s3filesystem_por_su_cuenta():
    """Guard de fuente: `S3FileSystem(` solo puede aparecer en el modulo que
    centraliza la construccion. Complementa al test de identidad: agarra al
    fetcher NUEVO que todavia no esta en `_CONSUMIDORES_S3` y a los caminos que
    construyen el filesystem inline, sin funcion que ejercer."""
    raiz = Path(__file__).parent.parent
    permitidos = {raiz / "src" / "fetch" / "granule_select.py"}
    culpables = []
    for py in list((raiz / "src").rglob("*.py")) + list((raiz / "dashboard").rglob("*.py")):
        if py in permitidos:
            continue
        src = py.read_text(encoding="utf-8")
        # Solo el codigo: un comentario que explique el bug no es una violacion.
        for nodo in ast.walk(ast.parse(src)):
            if not isinstance(nodo, ast.Call):
                continue
            nombre = getattr(nodo.func, "attr", getattr(nodo.func, "id", ""))
            if nombre == "S3FileSystem":
                culpables.append(f"{py.relative_to(raiz)}:{nodo.lineno}")
    assert not culpables, (
        "construir S3FileSystem fuera de granule_select crea una instancia con "
        f"DirCache eterno: {culpables}")


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


# ── Tope de desfase (max_gap_s) ─────────────────────────────────────────────
#
# Por qué: la unión [dt-1h, dt, dt+1h] resuelve el borde de hora, pero ante un
# hueco de datos NOAA el "más cercano" podía estar a ~60 min y se usaba como si
# fuera el scan pedido: una escena de ceniza, un FRP o una altura de otro momento
# presentada con la hora que el operador pidió. El tope convierte ese caso en
# "no hay gránulo" (no verificable), que cada fetcher ya sabe degradar.

_T0 = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)


def test_tope_rechaza_granulo_demasiado_lejano():
    dt = _T0 + timedelta(minutes=50)
    assert nearest_granule_key(_lister([_T0]), _parse, dt, max_gap_s=30 * 60) is None


def test_tope_acepta_justo_en_el_limite():
    dt = _T0 + timedelta(minutes=30)
    chosen = nearest_granule_key(_lister([_T0]), _parse, dt, max_gap_s=30 * 60)
    assert _parse(chosen) == _T0


def test_sin_tope_conserva_el_comportamiento_previo():
    """Default ``max_gap_s=None``: llamadores no revisados (LVTPF) no cambian."""
    dt = _T0 + timedelta(minutes=50)
    assert _parse(nearest_granule_key(_lister([_T0]), _parse, dt)) == _T0


def test_tope_por_defecto_cubre_la_latencia_nrt_medida():
    """En NRT se pide ``dt=ahora`` y el scan más nuevo en S3 empieza hasta
    cadencia + latencia antes. Medido el 13-sep-2026 sobre 24 h de S3
    (LastModified menos inicio de scan): L1b C14 máx 10,1 min, FDCF 10,8,
    ACHA 12,4, LVTPF 13,1; cadencia 10 min. Un tope menor que 10 + 13,1 min
    rechazaría el scan vigente y la vista diría "sin dato" en operación normal.
    """
    from src.fetch.granule_select import SCAN_MAX_GAP_S
    assert SCAN_MAX_GAP_S >= (10.0 + 13.1) * 60
    assert SCAN_MAX_GAP_S < 60 * 60, "el tope tiene que cortar el caso de ~1 h"


def _key_noaa(producto: str, dt: datetime) -> str:
    doy = dt.timetuple().tm_yday
    stamp = f"{dt.year}{doy:03d}{dt.hour:02d}{dt.minute:02d}{dt.second:02d}"
    return (f"noaa-goes19/{producto}/{dt.year}/{doy:03d}/{dt.hour:02d}/"
            f"OR_{producto}-M6_G19_s{stamp}0_e_c.nc")


class _S3Registro:
    """s3fs falso: lista keys fijas y registra qué se intentó abrir.

    ``open`` explota a propósito: los fetchers atrapan la excepción y devuelven
    "no verificable" igual que con el tope, así que el resultado solo no
    distingue los dos caminos. Lo que se verifica es si se intentó abrir.
    """

    def __init__(self, keys):
        self.keys = list(keys)
        self.abiertos: list = []

    def ls(self, prefix, **kw):
        return list(self.keys)

    def open(self, key, mode="rb", **kw):
        self.abiertos.append(key)
        raise OSError("fake: sin contenido")


def test_download_band_at_no_baja_un_scan_fuera_de_tope(monkeypatch):
    import src.fetch.goes_s3 as goes_s3
    bajados: list = []
    lister = _lister([_T0])
    monkeypatch.setattr(goes_s3, "list_band_files", lambda h, band: lister(h))
    monkeypatch.setattr(goes_s3, "_download_cached",
                        lambda key, use_cache=True: bajados.append(key) or Path(key))
    assert goes_s3.download_band_at(_T0 + timedelta(minutes=50), 14) is None
    assert bajados == []


def test_download_band_at_nrt_con_latencia_normal_si_baja(monkeypatch):
    """dt=ahora con el último scan a 23 min (latencia normal): se usa."""
    import src.fetch.goes_s3 as goes_s3
    bajados: list = []
    lister = _lister([_T0])
    monkeypatch.setattr(goes_s3, "list_band_files", lambda h, band: lister(h))
    monkeypatch.setattr(goes_s3, "_download_cached",
                        lambda key, use_cache=True: bajados.append(key) or Path(key))
    assert goes_s3.download_band_at(_T0 + timedelta(minutes=23), 14) is not None
    assert len(bajados) == 1


@pytest.mark.parametrize("modulo,funcion", [
    ("src.fetch.goes_fdcf", "fetch_hotspots_at_time"),
    ("src.fetch.frp_timeline", "fetch_scan_sliced"),
])
def test_fdcf_historico_no_abre_scan_fuera_de_tope(monkeypatch, modulo, funcion):
    """Backfill de FRP y hot spots: un scan a 50 min NO se atribuye a ``dt``.

    ``build_backfill`` guarda los hot spots con la etiqueta del ``ts`` pedido;
    sin tope quedaban bajo la hora equivocada.
    """
    import importlib

    import src.fetch.goes_fdcf as fdcf
    fake = _S3Registro([_key_noaa("ABI-L2-FDCF", _T0)])
    monkeypatch.setattr(fdcf, "_get_s3", lambda *a, **k: fake)
    fn = getattr(importlib.import_module(modulo), funcion)

    hs, scan_dt = fn(_T0 + timedelta(minutes=50), bounds={
        "lat_min": -40, "lat_max": -39, "lon_min": -72.5, "lon_max": -71.5})
    assert (hs, scan_dt) == ([], None)
    assert fake.abiertos == []

    fn(_T0 + timedelta(minutes=4), bounds={
        "lat_min": -40, "lat_max": -39, "lon_min": -72.5, "lon_max": -71.5})
    assert len(fake.abiertos) == 1, "dentro del tope sí debe intentar leerlo"


def test_acha_no_abre_granulo_fuera_de_tope(monkeypatch):
    """La altura ACHA se cruza con bandas L1b del mismo scan y se muestra con
    la hora pedida: un gránulo a 50 min no puede entrar como el vigente."""
    import src.fetch.goes_acha as goes_acha
    fake = _S3Registro([_key_noaa("ABI-L2-ACHA2KMF", _T0)])
    monkeypatch.setattr(goes_acha, "_get_s3", lambda *a, **k: fake)
    bounds = {"lat_min": -40, "lat_max": -39, "lon_min": -72.5, "lon_max": -71.5}

    assert goes_acha.fetch_acha_height_at(_T0 + timedelta(minutes=50), bounds) is None
    assert fake.abiertos == []

    goes_acha.fetch_acha_height_at(_T0 + timedelta(minutes=23), bounds)
    assert len(fake.abiertos) == 1, "latencia NRT normal: sí debe intentar leerlo"


if __name__ == "__main__":
    test_picks_next_hour_granule_at_end_of_hour()
    test_picks_prev_hour_granule_at_start_of_hour()
    test_exact_hour_middle_picks_same_hour()
    test_no_granules_returns_none()
    test_dedup_same_key_across_hours()
    test_naive_dt_treated_as_utc()
    test_unparseable_keys_skipped()
    print("OK — granule_select puro")
