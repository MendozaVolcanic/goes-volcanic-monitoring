"""Heatmap calendario de actividad — días × volcanes prioritarios.

Muestra una grilla similar a GitHub contributions: cada celda es un día
× volcán, coloreada por número de hot spots NOAA FDCF detectados ese día.

Limitación: implementación MVP usa hot spots de la última hora * 24 / día
como aproximación. Para una versión real hay que escanear el archivo S3
diario de FDCF (~144 archivos/día × 7 días = 1000 fetches), idealmente
pre-cocinado en GitHub Actions.

Usar como termómetro visual de "qué se está moviendo en Chile".
"""

import logging
from datetime import datetime, timedelta, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.style import header
from src.fetch.goes_fdcf import fetch_latest_hotspots
from src.volcanos import PRIORITY_VOLCANOES, get_volcano

logger = logging.getLogger(__name__)

LOOKBACK_DAYS = 7
RADIUS_KM = 50


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

    # MVP: solo el día actual con datos reales; los días anteriores son placeholders
    # que indican "datos pendientes" (necesitan backfill).
    counts_today = _count_hotspots_per_volcano(_hotspots_today())

    # Para días anteriores: 0 (placeholder honest, no inventado)
    counts_by_day = []
    for i in range(LOOKBACK_DAYS):
        if i == 0:
            counts_by_day.insert(0, counts_today)
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

    st.warning(
        "**MVP — solo día actual con datos reales.** Los 6 días anteriores "
        "aparecen vacíos porque escanear el archivo NOAA FDCF S3 de cada día "
        "(~144 archivos × 7 = 1000 fetches) es lento desde el dashboard. "
        "Para versión histórica completa, agendar un **GitHub Action diario** "
        "que pre-cocine los conteos y los guarde en `data/hotspots_daily.json`. "
        "Sesión futura — ~3-4 h de trabajo."
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
