"""Serie rodante del indicador nocturno de calor en el cráter (ficha SDA §A.8).

Por qué existe: el estado de una noche necesita todos sus cuadros y la referencia de
cielo despejado necesita las 7 noches previas. Eso no se puede calcular en cada
refresco del dashboard; se pre-cocina aquí y el dashboard sólo lee el JSON.

Qué hace cada corrida (workflow ``calor_nocturno.yml``, cron cada 10 min):
1. Lista los cuadros de :00 y :30 de la ventana (la última noche terminada, sus 7
   previas y la que está en curso) en que algún volcán del catálogo está de noche.
2. Baja, del más nuevo al más viejo y con presupuesto (``--gap-fill``), los que la
   serie no tiene: C07 y C14 de ABI L1b RadF en las ventanas de 25 x 25 píxeles de
   cada volcán, nada más. GitHub atrasa los cron de repos poco activos (frp_timeline
   mide 2 a 12 h entre corridas), así que el relleno de huecos no es opcional.
3. Calcula ``vrp_nocturno.vrp_cuadro`` para cada volcán que esté de noche.
4. Poda lo que quedó fuera de la ventana y escribe ``data/calor_nocturno.json``.

Lo que NO hace: escribir un cero por un gránulo que falta o una lectura que falló.
Un cuadro ausente es un hueco, y la noche con huecos queda "sin dato" si no le
alcanzan los cuadros visibles. Un gránulo que NOAA no publicó en 2 h se anota en
``sin_granulo`` para no reintentarlo en cada corrida.

Uso:
    python scripts/build_calor_nocturno.py                      # corrida normal
    python scripts/build_calor_nocturno.py --gap-fill 400 --nproc 8   # arranque, 8 noches
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402

from src.process import calor_nocturno as C  # noqa: E402
from src.process import vrp_nocturno as V  # noqa: E402

log = logging.getLogger("calor_nocturno")

SALIDA = Path(__file__).resolve().parent.parent / "data" / "calor_nocturno.json"
# Un gránulo que no aparece en 2 h no va a aparecer: NOAA publica a los ~10 min.
SIN_GRANULO_TRAS_H = 2
# El cuadro de :00 o :30 es el scan que EMPIEZA ahí; más lejos que esto es otro scan.
DESFASE_MAX_S = 5 * 60


class GranuloAusente(Exception):
    """NOAA no tiene el scan pedido (no es una falla de red)."""


def volcanes_catalogo():
    """Los 43 RNVV + Lastarria, sin los de prueba de otros países."""
    from src.volcanos import CATALOG
    return [v for v in CATALOG if v.zone != "test"]


def sitios_de(volcanes) -> dict:
    return {v.name: V.sitio(v.lat, v.lon, float(v.elevation)) for v in volcanes}


def nocturnos(t: datetime, volcanes) -> list:
    return [v for v in volcanes if V.es_nocturno(t, v.lat, v.lon)]


def _resueltos(serie: dict) -> set:
    return set(serie.get("cuadros") or {}) | set(serie.get("sin_granulo") or [])


def pendientes(serie: dict, ahora: datetime, volcanes) -> list:
    """Cuadros de la ventana con algún volcán de noche que la serie no tiene, del más
    nuevo al más viejo: los que mira el turno primero."""
    desde = C.inicio_noche(C.primera_noche_de_ventana(ahora))
    hechos = _resueltos(serie)
    return [t for t in reversed(C.grilla(desde, C.ultimo_esperado(ahora)))
            if t.strftime(C.ISO) not in hechos and nocturnos(t, volcanes)]


def _ultimo_resuelto(serie: dict, ahora: datetime, volcanes):
    """Cuadro más nuevo de la ventana que ya no hay que bajar: está en la serie, NOAA
    no lo publicó, o es de día en todos los volcanes. Sin esto último toda tarde se
    leería como "serie atrasada"."""
    desde = C.inicio_noche(C.primera_noche_de_ventana(ahora))
    hechos = _resueltos(serie)
    previo = C.parse_iso(serie.get("ultimo_cuadro_utc"))
    for t in reversed(C.grilla(desde, C.ultimo_esperado(ahora))):
        if t.strftime(C.ISO) in hechos or not nocturnos(t, volcanes):
            return max(t, previo) if previo else t
    return previo


def procesar(t: datetime, volcanes, sitios: dict, leer):
    """("ok", fila) | ("sin_granulo", None) | ("error", None). Nunca inventa un cero."""
    noct = nocturnos(t, volcanes)
    try:
        bandas = leer(t, {v.name: sitios[v.name] for v in noct})
    except GranuloAusente:
        return "sin_granulo", None
    except Exception as e:  # noqa: BLE001  (red, h5py: se reintenta en la próxima)
        log.warning("cuadro %s falló: %r", t.strftime(C.ISO), e)
        return "error", None
    (r7, co7), (r14, co14) = bandas[7], bandas[14]
    fila = {}
    for v in noct:
        if v.name not in r7 or v.name not in r14:
            continue
        fila[v.name] = C.fila(V.vrp_cuadro(r7[v.name], co7, r14[v.name], co14, sitios[v.name]))
    return "ok", fila


def podar(serie: dict, ahora: datetime) -> dict:
    corte = C.inicio_noche(C.primera_noche_de_ventana(ahora)).strftime(C.ISO)
    serie["cuadros"] = {k: v for k, v in sorted((serie.get("cuadros") or {}).items())
                        if k >= corte}
    serie["sin_granulo"] = sorted(k for k in set(serie.get("sin_granulo") or []) if k >= corte)
    return serie


def actualizar(serie: dict, ahora: datetime, volcanes, leer, presupuesto: int,
               mapear=map) -> dict:
    """Una corrida: baja hasta ``presupuesto`` cuadros pendientes y poda.

    ``leer(t, sitios)`` devuelve {7: ({volcán: rad}, planck), 14: (...)} o lanza
    ``GranuloAusente``. ``mapear`` permite repartir los cuadros en procesos.
    """
    serie = {"cuadros": dict((serie or {}).get("cuadros") or {}),
             "sin_granulo": list((serie or {}).get("sin_granulo") or []),
             "ultimo_cuadro_utc": (serie or {}).get("ultimo_cuadro_utc")}
    ahora = C._utc(ahora)
    sitios = sitios_de(volcanes)
    lote = pendientes(serie, ahora, volcanes)[:max(0, presupuesto)]
    if lote:
        log.info("pendientes en la ventana: %d; esta corrida baja %d",
                 len(pendientes(serie, ahora, volcanes)), len(lote))
    resultados = mapear(lambda t: (t, procesar(t, volcanes, sitios, leer)), lote)
    n_ok = 0
    for t, (estado, fila) in resultados:
        iso = t.strftime(C.ISO)
        if estado == "ok":
            serie["cuadros"][iso] = fila
            n_ok += 1
        elif estado == "sin_granulo" and t < ahora - timedelta(hours=SIN_GRANULO_TRAS_H):
            serie["sin_granulo"].append(iso)
    serie = podar(serie, ahora)
    ult = _ultimo_resuelto(serie, ahora, volcanes)
    serie.update(version=1, cadencia_min=C.CADENCIA_MIN,
                 actualizado_utc=ahora.strftime(C.ISO),
                 ultimo_cuadro_utc=ult.strftime(C.ISO) if ult else None)
    log.info("cuadros bajados: %d; en la serie: %d", n_ok, len(serie["cuadros"]))
    return serie


# ── E/S real (NOAA S3) ───────────────────────────────────────────────────────

def _key(t: datetime, banda: int):
    from src.fetch.goes_s3 import _scan_start, list_band_files
    from src.fetch.granule_select import nearest_granule_key
    return nearest_granule_key(lambda h: list_band_files(h, banda), _scan_start, t,
                               max_gap_s=DESFASE_MAX_S)


def _leer_banda(key: str, sitios: dict):
    """Radiancias de las ventanas de cada volcán, leídas por rebanada (sin bajar el
    disco entero) y los Planck del propio NetCDF."""
    import h5py

    from src.fetch.goes_s3 import _get_fs

    err = None
    for i in range(4):
        try:
            out = {}
            with _get_fs().open(key, "rb", block_size=2 ** 18, cache_type="readahead") as fo, \
                    h5py.File(fo, "r") as f:
                r = f["Rad"]
                sf, ao = float(r.attrs["scale_factor"][0]), float(r.attrs["add_offset"][0])
                fv = r.attrs["_FillValue"][0]
                for nombre, s in sorted(sitios.items(), key=lambda kv: kv[1].ventana[0]):
                    r0, r1, c0, c1 = s.ventana
                    raw = r[r0:r1, c0:c1]
                    rad = raw.astype("float64") * sf + ao
                    rad[raw == fv] = np.nan
                    out[nombre] = rad
                co = tuple(float(np.ravel(f[n][()])[0])
                           for n in ("planck_fk1", "planck_fk2", "planck_bc1", "planck_bc2"))
            return out, co
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(2 * (i + 1))
    raise OSError(f"no se pudo leer {key}: {err!r}")


def leer_s3(t: datetime, sitios: dict) -> dict:
    from src.fetch.goes_s3 import _scan_start
    k7, k14 = _key(t, 7), _key(t, 14)
    if k7 is None or k14 is None:
        raise GranuloAusente(t)
    # Las dos bandas tienen que ser del MISMO scan (mismo guard que scene.py).
    if _scan_start(k7) != _scan_start(k14):
        raise OSError(f"C07 y C14 de scans distintos en {t:%Y-%m-%d %H:%M}")
    return {7: _leer_banda(k7, sitios), 14: _leer_banda(k14, sitios)}


def _tarea(args):
    t, nombres = args
    vols = [v for v in volcanes_catalogo() if v.name in nombres]
    return t, procesar(t, vols, sitios_de(vols), leer_s3)


def cargar(ruta: Path) -> dict:
    if not ruta.exists():
        return {}
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        log.warning("serie existente ilegible, se rehace: %s", e)
        return {}


def guardar(serie: dict, ruta: Path) -> None:
    """Un cuadro por línea: el diff de cada commit del bot queda legible."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    cab = {k: serie[k] for k in ("version", "cadencia_min", "actualizado_utc",
                                 "ultimo_cuadro_utc", "sin_granulo")}
    lineas = [json.dumps(k) + ":" + json.dumps(v, ensure_ascii=False) for k, v in cab.items()]
    cuadros = ",\n".join(f"  {json.dumps(k)}: {json.dumps(v, ensure_ascii=False, separators=(',', ':'))}"
                         for k, v in sorted(serie["cuadros"].items()))
    texto = "{\n" + ",\n".join(lineas) + ',\n"cuadros": {\n' + cuadros + "\n}\n}\n"
    json.loads(texto)  # que lo escrito sea JSON válido antes de pisar el archivo
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(texto, encoding="utf-8")
    tmp.replace(ruta)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--gap-fill", type=int, default=30,
                    help="cuadros pendientes a bajar por corrida, del más nuevo al más viejo")
    ap.add_argument("--nproc", type=int, default=4)
    ap.add_argument("--salida", type=Path, default=SALIDA)
    ap.add_argument("--ahora", help="UTC 'YYYY-mm-ddTHH:MMZ' (sólo para pruebas)")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ahora = C.parse_iso(a.ahora) if a.ahora else datetime.now(timezone.utc)
    volcanes = volcanes_catalogo()
    serie = cargar(a.salida)
    t0 = time.time()
    if a.nproc > 1:
        from concurrent.futures import ProcessPoolExecutor

        # Cada proceso abre su propio s3fs y h5py (h5py no se reparte entre hilos).
        with ProcessPoolExecutor(a.nproc) as ex:
            def mapear(fn, lote):
                pedidos = [(t, [v.name for v in nocturnos(t, volcanes)]) for t in lote]
                return list(ex.map(_tarea, pedidos))
            serie = actualizar(serie, ahora, volcanes, leer_s3, a.gap_fill, mapear=mapear)
    else:
        serie = actualizar(serie, ahora, volcanes, leer_s3, a.gap_fill)
    guardar(serie, a.salida)
    log.info("listo en %.0f s: %s", time.time() - t0, a.salida)


if __name__ == "__main__":
    main()
