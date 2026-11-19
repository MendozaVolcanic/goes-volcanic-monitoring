"""Señal VOLCAT por volcán en el dashboard: lectura cacheada y su HTML.

FICHA SDA (Nivel 1): señal "VOLCAT detecta un objeto anclado al cráter"
  Qué decide: NADA por sí sola. Lee lo que VOLCAT (SSEC/CIMSS) dibujó en su
    último cuadro y lo pone en uno de cinco estados (ver
    src/process/volcat_deteccion.py). La detección es de SSEC/CIMSS,
    experimental y no validada por nosotros; no es una alerta del OVDAS. La
    interpretación queda en el geólogo de turno.
  Costo: cero descargas extra. El PNG es el mismo que ya bajan el panel VOLCAT
    de la grilla y las celdas de "VOLCAT por zona" (`_volcat_image_bytes`,
    cacheado por URL, que lleva la hora del cuadro). Se clasifica UNA vez por
    cuadro y sector y se ancla cada volcán del sector sobre esa clasificación.
  Trazabilidad: src/process/volcat_deteccion.py (estados), dashboard/
    map_helpers.estado_volcat (color y texto), tests/test_volcat_deteccion.py,
    docs/FICHA_SDA_GOES.md §A.7.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import streamlit as st

logger = logging.getLogger(__name__)

try:
    from src.cache_ttl import TTL_FRAME_IMAGE
except Exception:
    TTL_FRAME_IMAGE = 7200


class _PNGNoDisponible(Exception):
    """El PNG del cuadro no se pudo bajar en este intento.

    Se lanza DENTRO de la función cacheada para que st.cache_data no memorice
    la falla: el próximo refresco reintenta (mismo patrón que
    `map_helpers.FDCFNoVerificable`).
    """


def volcanes_chilenos():
    """Volcanes del catálogo operacional (43 RNVV + Lastarria), sin los de
    prueba de otros países."""
    from src.volcanos import CATALOG
    return [v for v in CATALOG if v.zone != "test"]


def _grupos_por_sector(volcanes) -> dict:
    """{(sector, instr): [Volcano, ...]} según `resolve_volcat_sector`."""
    from src.fetch.volcat_api import resolve_volcat_sector
    grupos: dict = {}
    for v in volcanes:
        grupos.setdefault(resolve_volcat_sector(v), []).append(v)
    return grupos


@st.cache_data(ttl=TTL_FRAME_IMAGE, show_spinner=False)
def _lecturas_sector(image_url: str, coords: dict, volcanes: tuple) -> dict:
    """{nombre: lectura} de todos los volcanes de un sector en un cuadro.

    `volcanes` es una tupla de (nombre, lat, lon): la grilla de un volcán y el
    resumen nacional piden la MISMA tupla para el mismo sector, así que
    comparten la entrada de caché y el cuadro se clasifica una sola vez.
    """
    import io

    import numpy as np
    from PIL import Image

    from dashboard.views.volcat_viewer import _volcat_image_bytes
    from src.process.volcat_colorbar import clasificar_mapa
    from src.process.volcat_deteccion import leer_objeto_anclado

    raw = _volcat_image_bytes(image_url)
    if not raw:
        raise _PNGNoDisponible(image_url)
    a = np.asarray(Image.open(io.BytesIO(raw)).convert("RGB")).astype("float64")
    mapa = clasificar_mapa(a)
    return {nombre: leer_objeto_anclado(a, coords, lat, lon, mapa=mapa)
            for nombre, lat, lon in volcanes}


def _senales_de_grupo(sector: str, instr: str, volcanes, ahora) -> dict:
    """Señal de cada volcán de un sector. Nunca lanza: una falla de SSEC o de
    la descarga sale como `no_disponible` con su motivo."""
    from dashboard.views.modo_guardia_volcan import etiqueta_sector_volcat
    from dashboard.views.volcat_viewer import _volcat_latest_cached
    from src.fetch.volcat_api import _parse_volcat_frame_dt
    from src.process.volcat_deteccion import evaluar_senal

    etiqueta = etiqueta_sector_volcat(sector)
    try:
        meta = _volcat_latest_cached(sector, instr, "Ash_Height")
    except Exception:
        logger.exception("VOLCAT latest %s", sector)
        meta = None
    frame_dt = _parse_volcat_frame_dt(meta.get("datetime")) if meta else None
    lecturas, error = {}, None
    if not meta:
        error = "SSEC no respondió o no publicó cuadros del sector"
    elif not meta.get("coords"):
        error = "SSEC no entregó la georreferencia del sector"
    else:
        tupla = tuple((v.name, v.lat, v.lon) for v in volcanes)
        try:
            lecturas = _lecturas_sector(meta["image_url"], meta["coords"], tupla)
        except _PNGNoDisponible:
            error = "no se pudo bajar el cuadro VOLCAT"
        except Exception:
            logger.exception("lectura VOLCAT %s", sector)
            error = "no se pudo leer el cuadro VOLCAT"
    out = {}
    for v in volcanes:
        s = evaluar_senal(lecturas.get(v.name), frame_dt, ahora=ahora,
                          error=error)
        s.update(volcan=v.name, sector=sector, etiqueta_sector=etiqueta,
                 frame_dt=frame_dt)
        out[v.name] = s
    return out


def senales_volcat(ahora=None) -> dict:
    """{nombre: señal} de los 44 volcanes chilenos, en orden norte a sur."""
    from concurrent.futures import ThreadPoolExecutor

    ahora = ahora or datetime.now(timezone.utc)
    vols = volcanes_chilenos()
    grupos = list(_grupos_por_sector(vols).items())
    # Los 6 sectores en PARALELO: con caché fría cada uno es una consulta a la
    # API de SSEC y un PNG de ~0,4 MB, 4 a 7 s medidos el 19-11-2026; en serie
    # eran ~40 s antes de mostrar nada. Mismo patrón que
    # `zonas_fullscreen._prewarm_volcat_specs`. `_senales_de_grupo` no lanza.
    with ThreadPoolExecutor(max_workers=len(grupos) or 1) as ex:
        partes = list(ex.map(
            lambda kv: _senales_de_grupo(kv[0][0], kv[0][1], kv[1], ahora),
            grupos))
    todas = {}
    for parte in partes:
        todas.update(parte)
    return {v.name: todas[v.name] for v in vols}


def senal_volcat(nombre: str, ahora=None) -> dict | None:
    """Señal de un volcán. Pide el grupo ENTERO de su sector para compartir la
    caché con el resumen nacional (misma tupla, misma entrada)."""
    from src.fetch.volcat_api import resolve_volcat_sector
    from src.volcanos import get_volcano

    v = get_volcano(nombre)
    if v is None:
        return None
    ahora = ahora or datetime.now(timezone.utc)
    clave = resolve_volcat_sector(v)
    grupo = _grupos_por_sector(volcanes_chilenos()).get(clave) or [v]
    if v not in grupo:      # volcán de prueba fuera del catálogo operacional
        grupo = [v]
    return _senales_de_grupo(clave[0], clave[1], grupo, ahora)[v.name]


def html_senal(senal: dict, compacto: bool = False, aviso: bool = True) -> str:
    """Una tira con el estado, el detalle y el aviso de fuente.

    `compacto` es para la cabecera de la grilla (letra más chica). `aviso`
    False sólo para las filas del resumen nacional, que lo ponen UNA vez
    arriba de la lista: repetido bajo cada volcán se dejaba de leer.
    """
    from dashboard.map_helpers import AVISO_VOLCAT_FUENTE, estado_volcat

    e = estado_volcat(senal)
    tam = "0.8rem" if compacto else "0.85rem"
    return (
        f"<div style='font-size:{tam}; color:#9aaabb; line-height:1.35;'>"
        f"<span style='color:{e['color']}; font-weight:700;'>● {e['titulo']}"
        f"</span> <span>({e['detalle']})</span>"
        + (f"<br><span style='font-size:0.72rem; color:#7a8a9a;'>"
           f"{AVISO_VOLCAT_FUENTE}</span>" if aviso else "")
        + "</div>")


def resumen_nacional(senales: dict) -> dict:
    """Conteo por estado y la lista de volcanes que no están en el estado
    normal, en orden norte a sur."""
    from src.process.volcat_deteccion import ESTADOS
    cuenta = {e: 0 for e in ESTADOS}
    for s in senales.values():
        cuenta[s["estado"]] = cuenta.get(s["estado"], 0) + 1
    fuera_de_lo_normal = [s for s in senales.values()
                          if s["estado"] != "sin_deteccion"]
    return {"cuenta": cuenta, "lista": fuera_de_lo_normal}
