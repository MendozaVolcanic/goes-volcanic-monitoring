# ════════════════════════════════════════════════════════════════════
# FICHA SDA · calor_nocturno.py · SDA: Monitoreo Volcánico GOES-19 · ID: SDA-GOES-01 §A.8
# Objetivo      : leer la serie data/calor_nocturno.json y decir, para un volcán, el
#                 estado de la noche en curso o de la última noche (encendido, bajo el
#                 límite, sin dato), con la edad del dato. Contexto térmico para el
#                 turno de OVDAS; no es una alerta.
# Lógica        : agrupa los cuadros del volcán por noche, toma la referencia de cielo
#                 despejado de las 7 noches previas y llama a la regla validada de
#                 src/process/vrp_nocturno.py, que NO se toca aquí.
# Modelo/método : determinístico, sin ML. Sólo agrupación y conteo.
# Datos entrada : data/calor_nocturno.json (scripts/build_calor_nocturno.py, workflow
#                 calor_nocturno.yml), hecho de ABI L1b C07 y C14 de NOAA S3. Sin
#                 datos personales.
# Variables     : cadencia 30 min (la validada), latencia 15 min, atraso tolerado 30 min,
#                 4 cuadros para mostrar la noche en curso (= mínimo de visibles de la regla).
# Limitaciones  : las de vrp_nocturno (sólo de noche, ve sobre ~10 MW, una nube deja la
#                 noche sin dato). Un hueco de la serie es un cuadro que falta, nunca un
#                 cero: si faltan muchos, la noche queda sin dato.
# Refs/datos    : validación PR 87 (docs/own_volcat/vrp_nocturno/INFORME.md); la serie
#                 reproduce sus 744 noches (tests/test_calor_nocturno.py).
# Ficha completa: docs/FICHA_SDA_GOES.md (§A.8)
# ════════════════════════════════════════════════════════════════════
"""Serie de calor nocturno por volcán: de los cuadros guardados al estado de una noche.

Funciones puras, sin red. El workflow escribe la serie y el dashboard la lee con
``evaluar_volcan``. La regla por noche es ``vrp_nocturno.estado_noche`` tal cual.

Esquema de ``data/calor_nocturno.json``::

    {"version": 1, "cadencia_min": 30,
     "actualizado_utc": "2026-11-23T15:02Z",
     "ultimo_cuadro_utc": "2026-11-23T14:30Z",   # cuadro más nuevo ya resuelto
     "cuadros": {"2026-11-23T05:00Z": {"Nevados de Chillan": [vrp_mw, bt14_k, n_cal], ...}},
     "sin_granulo": ["2026-11-20T03:30Z"]}       # cuadros que NOAA no publicó

Un cuadro sólo trae los volcanes que estaban de noche. ``vrp_mw`` y ``bt14_k`` van en
``null`` cuando el cuadro no se pudo evaluar (banda vacía, anillo sin datos).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

import numpy as np

from src.process import vrp_nocturno as V

ISO = "%Y-%m-%dT%H:%MZ"

# QUÉ: se evalúan sólo los cuadros de :00 y :30.
# POR QUÉ: la regla (2 cuadros sobre 10 MW, 4 visibles, 10 para la referencia) se
# validó con un cuadro cada 30 min (criterio_2026-11-22.md §3). Con los de 10 min
# esos mínimos se cumplen tres veces más rápido y eso no está medido (INFORME §3):
# pasar a 10 min exige volver a validar, no sólo cambiar este número.
CADENCIA_MIN = 30
# NOAA publica el C14 hasta ~10 min después del inicio del scan (medido 13-09-2026,
# granule_select.SCAN_MAX_GAP_S): antes de 15 min un cuadro todavía puede no estar.
LATENCIA_MIN = 15
# Más atrás que esto, el estado no describe la noche de hoy y el texto lo dice.
ATRASO_MAX_MIN = 30


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.strptime(s, ISO).replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def piso_cadencia(dt: datetime) -> datetime:
    dt = _utc(dt).replace(second=0, microsecond=0)
    return dt - timedelta(minutes=dt.minute % CADENCIA_MIN)


def ultimo_esperado(ahora: datetime) -> datetime:
    """Cuadro más nuevo que NOAA ya debería haber publicado."""
    return piso_cadencia(_utc(ahora) - timedelta(minutes=LATENCIA_MIN))


def grilla(desde: datetime, hasta: datetime) -> list:
    """Cuadros de :00 y :30 entre ``desde`` y ``hasta``, inclusive."""
    t = piso_cadencia(desde)
    if t < _utc(desde):
        t += timedelta(minutes=CADENCIA_MIN)
    out = []
    while t <= _utc(hasta):
        out.append(t)
        t += timedelta(minutes=CADENCIA_MIN)
    return out


def inicio_noche(noche: date) -> datetime:
    """Noche D empieza a las 18:00 UTC de D−1 (``vrp_nocturno.clave_noche``)."""
    return datetime(noche.year, noche.month, noche.day, tzinfo=timezone.utc) - timedelta(hours=6)


def ultima_noche_terminada(ahora: datetime) -> date:
    """De día, la noche que terminó esta mañana.

    Entre 18:00 UTC y la puesta de sol ``clave_noche`` ya apunta a la noche que viene,
    que no tiene cuadros; restar 12 h cae siempre en la que pasó."""
    return V.clave_noche(_utc(ahora) - timedelta(hours=12))


def primera_noche_de_ventana(ahora: datetime) -> date:
    """Ventana de la serie: la última noche terminada y sus 7 previas (las que pide su
    referencia), más la que esté en curso."""
    return ultima_noche_terminada(ahora) - timedelta(days=V.REF_NOCHES)


def _cuadro(fila) -> V.CuadroVRP:
    vrp, b14 = fila[0], fila[1]
    ncal = int(fila[2]) if len(fila) > 2 and fila[2] is not None else 0
    return V.CuadroVRP(float("nan") if vrp is None else float(vrp),
                       float("nan") if b14 is None else float(b14), ncal)


def cuadros_por_noche(serie: Optional[dict], nombre: str) -> dict:
    """{noche: [(t, CuadroVRP), ...]} del volcán, en orden temporal."""
    out: dict = {}
    for iso, fila_cuadro in sorted(((serie or {}).get("cuadros") or {}).items()):
        fila = (fila_cuadro or {}).get(nombre)
        t = parse_iso(iso)
        if fila is None or t is None:
            continue
        out.setdefault(V.clave_noche(t), []).append((t, _cuadro(fila)))
    return out


def evaluar_noche(por_noche: dict, noche: date) -> dict:
    """Estado de ``noche`` con la referencia de sus 7 noches previas.

    ``por_noche`` es {noche: [CuadroVRP]} (o [(t, CuadroVRP)]), sólo cuadros nocturnos.
    Es exactamente el procedimiento de la validación (vn_medir.visibilidad y noches).
    """
    def cs(d):
        return [c[1] if isinstance(c, tuple) else c for c in por_noche.get(d, [])]
    previas = [c.bt14_zona_k for i in range(1, V.REF_NOCHES + 1)
               for c in cs(noche - timedelta(days=i))]
    ref = V.referencia_despejado(previas)
    return V.estado_noche(cs(noche), ref, nocturno=True)


def _noche_a_mostrar(por_noche: dict, ahora: datetime, lat: float, lon: float):
    """(noche, en_curso). De noche, la en curso si ya tiene 4 cuadros; si no, la
    anterior: recién empezada, "sin dato" sólo diría que la noche es joven."""
    if V.es_nocturno(ahora, lat, lon):
        hoy = V.clave_noche(ahora)
        if len(por_noche.get(hoy, [])) >= V.CUADROS_VIS_MIN:
            return hoy, True
        return hoy - timedelta(days=1), False
    return ultima_noche_terminada(ahora), False


def _esperados(noche: date, lat: float, lon: float, hasta: datetime) -> list:
    fin = min(inicio_noche(noche) + timedelta(hours=18), hasta)
    return [t for t in grilla(inicio_noche(noche), fin) if V.es_nocturno(t, lat, lon)]


def atraso_min(serie: Optional[dict], ahora: datetime) -> Optional[int]:
    ult = parse_iso((serie or {}).get("ultimo_cuadro_utc"))
    if ult is None:
        return None
    return max(0, int((ultimo_esperado(ahora) - ult).total_seconds() // 60))


def evaluar_volcan(serie: Optional[dict], nombre: str, lat: float, lon: float,
                   ahora: Optional[datetime] = None) -> dict:
    """Estado del indicador para un volcán, listo para ``estado_calor_nocturno``.

    Agrega a la salida de ``estado_noche``: ``noche``, ``en_curso``, ``n_esperados``,
    ``n_huecos`` (cuadros que la serie debería tener y no tiene), ``serie_hasta``,
    ``edad_min``, ``atraso_min`` y ``atrasada``. Nunca lanza.
    """
    ahora = _utc(ahora or datetime.now(timezone.utc))
    serie_hasta = parse_iso((serie or {}).get("ultimo_cuadro_utc"))
    edad = (None if serie_hasta is None
            else max(0, int((ahora - serie_hasta).total_seconds() // 60)))
    atr = atraso_min(serie, ahora)
    meta = {"serie_hasta": serie_hasta, "edad_min": edad, "atraso_min": atr,
            "atrasada": atr is not None and atr > ATRASO_MAX_MIN}
    if not serie or not serie.get("cuadros"):
        return {"estado": "sin_dato", "motivo": "no se pudo leer la serie de calor nocturno",
                "n_cuadros": 0, "n_visibles": 0, "n_sobre_umbral": 0, "noche": None,
                "en_curso": False, "n_esperados": 0, "n_huecos": 0, **meta}
    por_noche = cuadros_por_noche(serie, nombre)
    noche, en_curso = _noche_a_mostrar(por_noche, ahora, lat, lon)
    res = evaluar_noche(por_noche, noche)
    tiene = {t for t, _ in por_noche.get(noche, [])}
    # Hasta el último cuadro que NOAA ya publicó, no hasta donde llega la serie: un
    # cuadro que la serie no tiene es un hueco aunque la causa sea el atraso.
    esperados = _esperados(noche, lat, lon, ultimo_esperado(ahora))
    huecos = sum(1 for t in esperados if t not in tiene)
    if res["estado"] == "sin_dato" and not tiene:
        res["motivo"] = "la serie no tiene cuadros de esa noche"
    ultimo_volcan = max(tiene) if tiene else None
    res.update(noche=noche, en_curso=en_curso, n_esperados=len(esperados),
               n_huecos=huecos, ultimo_cuadro_volcan=ultimo_volcan, **meta)
    return res


def fila(c: V.CuadroVRP) -> list:
    """Fila compacta del JSON: NaN viaja como null (JSON no tiene NaN)."""
    def r(x):
        return None if x is None or not np.isfinite(x) else round(float(x), 2)
    return [r(c.vrp_mw), r(c.bt14_zona_k), int(c.n_calientes)]
