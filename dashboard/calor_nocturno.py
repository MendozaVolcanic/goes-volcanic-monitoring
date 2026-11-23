"""Indicador nocturno de calor en el cráter en el dashboard: lectura de la serie y su HTML.

FICHA SDA (Nivel 1): "calor en el cráter sobre ~10 MW" (ficha §A.8)
  Qué decide: el estado de la noche en curso o de la última noche de un volcán
    (encendido, bajo el límite, sin dato). Es contexto térmico, no una alerta del
    OVDAS. La regla es src/process/vrp_nocturno.py (validada, PR 87) y la lectura
    de la serie src/process/calor_nocturno.py.
  Costo: cero descargas de satélite. Lee data/calor_nocturno.json, que el workflow
    calor_nocturno.yml mantiene en main; caché de 5 min.
  Dónde se ve: cabecera de la grilla de volcán, sólo en el sub-tab Volcán del Modo
    Guardia y en el tab Volcán de Vista Operacional. NO en la pared del Modo Sala:
    primero lo lee quien lo puede interpretar (decisión de Nicolás, 23-11-2026).
  Trazabilidad: tests/test_calor_nocturno.py, tests/test_vrp_nocturno.py,
    docs/FICHA_SDA_GOES.md §A.8.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

logger = logging.getLogger(__name__)

SERIE_PATH = Path(__file__).resolve().parent.parent / "data" / "calor_nocturno.json"
# El deploy de HF es una FOTO del repo: sin bajar el JSON vivo de main, la cabecera
# mostraría para siempre la noche del último deploy (mismo motivo que
# heatmap_actividad.FRP_TIMELINE_URL).
SERIE_URL = ("https://raw.githubusercontent.com/MendozaVolcanic/"
             "goes-volcanic-monitoring/main/data/calor_nocturno.json")


def _serie_local() -> dict:
    try:
        return json.loads(SERIE_PATH.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        logger.warning("calor_nocturno.json local ilegible: %s", e)
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def _cargar_serie() -> dict:
    """La serie viva de main y, si la red falla, la del disco. `_source` dice cuál."""
    try:
        import time as _t

        from src.fetch._http_session import get_session

        r = get_session().get(f"{SERIE_URL}?_={int(_t.time())}", timeout=12)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and isinstance(data.get("cuadros"), dict):
            data["_source"] = "remoto"
            return data
        logger.warning("calor_nocturno remoto sin 'cuadros'; uso el local")
    except Exception as e:  # noqa: BLE001
        logger.warning("calor_nocturno remoto falló (%s); uso el local", e)
    data = _serie_local()
    if data:
        data["_source"] = "local"
    return data


def senal_calor(nombre: str, ahora=None) -> dict:
    """Estado del indicador para un volcán. Nunca lanza: una falla es "sin dato"."""
    from src.process.calor_nocturno import evaluar_volcan
    from src.volcanos import get_volcano

    ahora = ahora or datetime.now(timezone.utc)
    v = get_volcano(nombre)
    if v is None:
        return {"estado": "sin_dato", "motivo": "volcán fuera del catálogo"}
    try:
        serie = _cargar_serie()
    except Exception:  # noqa: BLE001
        logger.exception("serie calor nocturno")
        serie = {}
    res = evaluar_volcan(serie, v.name, v.lat, v.lon, ahora=ahora)
    res["noche_txt"] = noche_txt(res)
    return res


def noche_txt(res: dict) -> str:
    """"noche en curso, 23 al 24-11" o "última noche, 22 al 23-11" (fechas de Chile)."""
    from datetime import timedelta
    d = res.get("noche")
    if d is None:
        return ""
    a = d - timedelta(days=1)
    rango = f"{a.day} al {d.day}-{d.month:02d}" if a.month == d.month else \
        f"{a.day}-{a.month:02d} al {d.day}-{d.month:02d}"
    return f"{'noche en curso' if res.get('en_curso') else 'última noche'}, {rango}"


def html_calor(res: dict, compacto: bool = False) -> str:
    """Tira con estado, detalle (noche, conteo, huecos y edad) y aviso de fuente, con
    el mismo formato que `volcat_senal.html_senal`."""
    from dashboard.map_helpers import AVISO_CALOR_NOCTURNO, estado_calor_nocturno

    e = estado_calor_nocturno(res, noche_txt=res.get("noche_txt", ""))
    tam = "0.8rem" if compacto else "0.85rem"
    return (
        f"<div style='font-size:{tam}; color:#9aaabb; line-height:1.35;'>"
        f"<span style='color:{e['color']}; font-weight:700;'>● {e['titulo']}"
        f"</span> <span>({e['detalle']})</span>"
        f"<br><span style='font-size:0.72rem; color:#7a8a9a;'>"
        f"{AVISO_CALOR_NOCTURNO}</span></div>")
