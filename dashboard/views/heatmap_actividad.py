"""Heatmap calendario de actividad — días × volcanes prioritarios.

Muestra una grilla similar a GitHub contributions: cada celda es un día
× volcán, coloreada por número de hot spots NOAA FDCF detectados ese día.

Limitación: implementación MVP usa hot spots de la última hora * 24 / día
como aproximación. Para una versión real hay que escanear el archivo S3
diario de FDCF (~144 archivos/día × 7 días = 1000 fetches), idealmente
pre-cocinado en GitHub Actions.

Usar como termómetro visual de "qué se está moviendo en Chile".
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.style import header
from src.fetch.goes_fdcf import fetch_latest_hotspots
from src.volcanos import PRIORITY_VOLCANOES, get_volcano

logger = logging.getLogger(__name__)

LOOKBACK_DAYS = 7
RADIUS_KM = 50
HISTORIC_PATH = Path(__file__).parent.parent.parent / "data" / "hotspots_daily.json"


def _load_historic() -> dict:
    """Lee hotspots_daily.json (pre-cocinado por GitHub Action)."""
    if not HISTORIC_PATH.exists():
        return {}
    try:
        return json.loads(HISTORIC_PATH.read_text()).get("days", {})
    except Exception as e:
        logger.warning("hotspots_daily.json corrupto: %s", e)
        return {}


@st.cache_data(ttl=600, show_spinner="Calculando hot spots última hora…")
def _hotspots_today() -> list:
    """Hot spots Chile en la última hora — proxy del día actual.

    NOTA: para versión real con backfill histórico hay que escanear el
    archivo S3 NOAA-19 FDCF de los últimos N días. Eso requiere ~1000
    requests, y debería estar pre-cocinado por un GitHub Action diario.
    """
    bounds = {
        "lat_min": -56, "lat_max": -17,
        "lon_min": -76, "lon_max": -66,
    }
    try:
        hs, dt = fetch_latest_hotspots(bounds=bounds, hours_back=1)
        return hs
    except Exception as e:
        logger.warning("hotspots fetch fallo: %s", e)
        return []


def _count_hotspots_per_volcano(hotspots: list) -> dict[str, int]:
    """Por volcán prioritario: cuántos hot spots ≤RADIUS_KM."""
    counts = {}
    for name in PRIORITY_VOLCANOES:
        v = get_volcano(name)
        if v is None:
            continue
        n = 0
        for h in hotspots:
            dlat = (h.lat - v.lat) * 111.0
            dlon = (h.lon - v.lon) * 111.0 * float(np.cos(np.radians(v.lat)))
            d = float(np.hypot(dlat, dlon))
            if d <= RADIUS_KM:
                n += 1
        counts[name] = n
    return counts


def _build_heatmap(counts_by_day: list[dict], today: datetime) -> go.Figure:
    """Plotly heatmap con días en X, volcanes en Y, count como color."""
    days = [(today - timedelta(days=i)).strftime("%d-%b") for i in range(LOOKBACK_DAYS)][::-1]
    z = []
    for name in PRIORITY_VOLCANOES:
        row = [counts_by_day[i].get(name, 0) for i in range(LOOKBACK_DAYS)]
        z.append(row)

    fig = go.Figure(go.Heatmap(
        z=z,
        x=days,
        y=PRIORITY_VOLCANOES,
        colorscale=[[0, "#0f1418"], [0.01, "#1a3322"], [0.3, "#3fb950"],
                    [0.6, "#d29922"], [1.0, "#ff4444"]],
        zmin=0, zmax=10,
        hovertemplate="<b>%{y}</b><br>%{x}<br>Hot spots: %{z}<extra></extra>",
        colorbar=dict(title="Hot spots", thickness=12, len=0.6),
    ))
    fig.update_layout(
        height=420, margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
        font=dict(color="#e0e0e0"),
        xaxis=dict(tickfont=dict(size=11)),
        yaxis=dict(tickfont=dict(size=11)),
    )
    return fig


def render():
    header(
        "📅 Heatmap actividad — últimos 7 días",
        f"Hot spots NOAA FDCF en radio {RADIUS_KM} km de cada volcán prioritario",
    )

    today = datetime.now(timezone.utc)

    # Hoy: datos reales calculados live. Dias previos: del archivo historico
    # pre-cocinado por GitHub Action (.github/workflows/hotspots_daily.yml).
    counts_today = _count_hotspots_per_volcano(_hotspots_today())
    historic = _load_historic()

    counts_by_day = []
    for i in range(LOOKBACK_DAYS):
        day = today - timedelta(days=i)
        day_key = day.strftime("%Y-%m-%d")
        if i == 0:
            counts_by_day.insert(0, counts_today)
        elif day_key in historic:
            counts_by_day.insert(0, historic[day_key])
        else:
            counts_by_day.insert(0, {})  # placeholder vacio

    fig = _build_heatmap(counts_by_day, today)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    total_today = sum(counts_today.values())
    if total_today > 0:
        active = [k for k, v in counts_today.items() if v > 0]
        st.success(
            f"🔥 **Hoy ({today.strftime('%d-%b')})**: {total_today} hot spots "
            f"distribuidos en {len(active)} volcán(es): {', '.join(active)}"
        )
    else:
        st.info(
            f"✅ **Hoy ({today.strftime('%d-%b')})**: cero hot spots NOAA en los "
            f"{len(PRIORITY_VOLCANOES)} volcanes prioritarios. Calma operacional."
        )

    historic_days = sum(1 for c in counts_by_day[:-1] if c)
    if historic_days > 0:
        st.success(
            f"📊 Histórico: {historic_days}/{LOOKBACK_DAYS - 1} días cargados "
            f"desde `data/hotspots_daily.json` (pre-cocinado por GitHub Action diario)."
        )
    else:
        st.info(
            "📊 Días anteriores aparecen vacíos hasta que el GitHub Action "
            "diario (`.github/workflows/hotspots_daily.yml`) corra al menos "
            "una vez. La primera corrida es a las 02:00 UTC del día siguiente "
            "al deploy."
        )

    # Tabla de detalles del día
    if counts_today:
        st.markdown("### Detalle día actual")
        rows = []
        for name, n in counts_today.items():
            v = get_volcano(name)
            if v is None:
                continue
            status = "🔥 Activo" if n > 0 else "✅ Calmo"
            rows.append({
                "Volcán": name,
                "Hot spots ≤50 km": n,
                "Estado": status,
                "Región": v.region,
                "Elev (m)": v.elevation,
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
