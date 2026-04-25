"""Pagina Series de tiempo: intensidad de señal por volcán a lo largo de N horas.

Para cada volcán seleccionado, baja los últimos N scans de RAMMB en el área
del volcán y computa una métrica escalar de "qué tan activa está la firma de
ceniza/SO2". Plotea N puntos vs tiempo. Útil para responder
"¿está empeorando o estable?" — la animación dice qué pasa ahora, esto dice
la tendencia.
"""

from __future__ import annotations

import logging
from datetime import timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.style import (
    C_ACCENT, C_ASH, C_SO2,
    header, info_panel, kpi_card, refresh_info_badge,
)
from dashboard.utils import fmt_chile, parse_rammb_ts
from src.fetch.timeseries import (
    METRIC_LABEL, fetch_volcano_timeseries,
)
from src.fetch.rammb_slider import ZOOM_VOLCAN, ZOOM_ZONE
from src.volcanos import CATALOG, PRIORITY_VOLCANOES, get_volcano

logger = logging.getLogger(__name__)


WINDOW_OPTIONS = {
    "1 hora (6 puntos)":   (6, 0.06),
    "3 horas (18 puntos)": (18, 0.06),
    "6 horas (36 puntos)": (36, 0.06),
    "12 horas (72 puntos)": (72, 0.06),
    "24 horas (144 puntos)": (144, 0.10),
}

PRODUCTS = {
    "eumetsat_ash": "Ash RGB (firma de ceniza)",
    "jma_so2":      "SO2 RGB (firma de SO2)",
}

PRODUCT_COLORS = {
    "eumetsat_ash": "#ff6644",
    "jma_so2":      "#44dd88",
}


@st.cache_data(ttl=600, show_spinner=False)
def _cached_series(
    lat: float, lon: float, product: str, n_frames: int,
    radius_deg: float, zoom: int,
) -> list[dict]:
    """Wrapper cacheado. TTL 10 min — no tiene sentido recomputar antes
    porque RAMMB publica cada 10 min."""
    pts = fetch_volcano_timeseries(
        volcano_lat=lat, volcano_lon=lon,
        product=product, n_frames=n_frames,
        radius_deg=radius_deg, zoom=zoom,
    )
    return [
        {"ts": p.ts, "dt": p.dt, "metric": p.metric, "available": p.available}
        for p in pts
    ]


def _plot_series(
    points: list[dict], product: str, volcano_name: str,
) -> go.Figure:
    if not points:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_dark",
            height=400,
            title=f"Sin datos para {volcano_name}",
        )
        return fig

    valid = [p for p in points if p["available"]]
    if not valid:
        fig = go.Figure()
        fig.update_layout(template="plotly_dark", height=400,
                          title="Todos los frames fallaron")
        return fig

    xs = [p["dt"] for p in valid]
    ys = [p["metric"] for p in valid]
    color = PRODUCT_COLORS.get(product, C_ACCENT)

    # Banda movil (3 frames) para resaltar tendencia
    if len(ys) >= 3:
        ser = pd.Series(ys)
        baseline = ser.rolling(window=3, center=True, min_periods=1).mean()
    else:
        baseline = pd.Series(ys)

    fig = go.Figure()
    # Trazo principal (puntos + linea fina)
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines+markers",
        line=dict(color=color, width=1.5),
        marker=dict(size=6, color=color,
                    line=dict(width=0.8, color="white")),
        name="Métrica",
        hovertemplate=(
            "%{x|%Y-%m-%d %H:%M} UTC<br>"
            "<b>%{y:.2f}%</b><extra></extra>"
        ),
    ))
    # Trazo media movil
    fig.add_trace(go.Scatter(
        x=xs, y=baseline.tolist(),
        mode="lines",
        line=dict(color=color, width=3, dash="dot"),
        opacity=0.55,
        name="Media móvil 3-pt",
        hoverinfo="skip",
    ))

    fig.update_layout(
        title=dict(
            text=f"{volcano_name} — {METRIC_LABEL.get(product, product)}",
            font=dict(size=14, color="#ccc"),
        ),
        xaxis=dict(
            title="Tiempo (UTC)",
            showgrid=True, gridcolor="rgba(100,120,140,0.15)",
        ),
        yaxis=dict(
            title=METRIC_LABEL.get(product, "Métrica"),
            showgrid=True, gridcolor="rgba(100,120,140,0.15)",
            rangemode="tozero",
        ),
        template="plotly_dark",
        height=420,
        margin=dict(t=50, b=50, l=60, r=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
    )
    return fig


def _kpis_from_points(points: list[dict]) -> dict:
    """Estadisticos para mostrar como KPI."""
    valid = [p for p in points if p["available"]]
    if not valid:
        return {"current": 0.0, "max": 0.0, "max_dt": None, "mean": 0.0,
                "trend_pct": 0.0, "n": 0}
    ys = [p["metric"] for p in valid]
    current = ys[-1]
    max_v = max(ys)
    max_idx = ys.index(max_v)
    mean_v = sum(ys) / len(ys)

    # Trend: media de la ultima cuarta parte vs primera cuarta parte
    q = max(1, len(ys) // 4)
    first = sum(ys[:q]) / q
    last  = sum(ys[-q:]) / q
    trend = ((last - first) / first * 100.0) if first > 0.01 else 0.0

    return {
        "current": current, "max": max_v,
        "max_dt": valid[max_idx]["dt"],
        "mean": mean_v, "trend_pct": trend, "n": len(valid),
    }


def render():
    header(
        "Series de tiempo por volcán",
        "Tendencia de firma de ceniza/SO2 en las últimas horas — RAMMB/CIRA GOES-19",
    )
    refresh_info_badge(context="general")

    # ── Controles ──
    c1, c2, c3, c4 = st.columns([1.6, 1.4, 1.2, 0.8])
    with c1:
        priority_names = [v.name for v in CATALOG if v.name in PRIORITY_VOLCANOES]
        other_names    = [v.name for v in CATALOG if v.name not in priority_names]
        options = [f"★ {n}" for n in priority_names] + other_names
        sel_raw = st.selectbox("Volcán", options, index=0, key="ts_volc")
        volc_name = sel_raw.replace("★ ", "")
    with c2:
        product = st.selectbox(
            "Producto",
            list(PRODUCTS.keys()),
            format_func=lambda k: PRODUCTS[k],
            index=0, key="ts_prod",
        )
    with c3:
        window_label = st.selectbox(
            "Ventana", list(WINDOW_OPTIONS.keys()),
            index=2, key="ts_window",
        )
    with c4:
        st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
        fetch = st.button("Calcular", type="primary",
                          use_container_width=True)

    n_frames, default_radius = WINDOW_OPTIONS[window_label]

    c5, c6 = st.columns([1, 3])
    with c5:
        radius = st.slider(
            "Radio (°)", 0.5, 2.0, 1.0, 0.25, key="ts_radius",
            help="Tamaño del bbox alrededor del volcán para extraer la métrica.",
        )

    if not fetch and "ts_data" not in st.session_state:
        info_panel(
            "<b>Series de tiempo de intensidad de señal</b><br><br>"
            "Para el volcán seleccionado, descarga los últimos N scans RAMMB "
            "en el área del volcán y computa una métrica escalar de "
            "<b>cuánta firma de ceniza (rojo en Ash RGB)</b> o "
            "<b>cuánta firma de SO2 (verde en SO2 RGB)</b> hay en cada scan.<br><br>"
            "Útil para responder <b>'¿está empeorando o estable?'</b>. La animación "
            "muestra qué pasa ahora; esto muestra la tendencia.<br><br>"
            "<i>Nota:</i> esta métrica es un proxy rápido (% píxeles con color "
            "dominante). Tiene sesgo en presencia de cirrus, polvo del Atacama "
            "y luz oblicua al amanecer/atardecer. Para análisis definitivo "
            "usar BTD desde L1b — TODO v2."
        )
        return

    # Fetch
    if fetch or "ts_data" not in st.session_state:
        v = get_volcano(volc_name)
        if v is None:
            st.error(f"Volcán '{volc_name}' no encontrado.")
            return
        with st.spinner(
            f"Descargando {n_frames} scans para {v.name} (paralelo, max ~10s)..."
        ):
            try:
                points = _cached_series(
                    lat=v.lat, lon=v.lon, product=product,
                    n_frames=n_frames, radius_deg=radius,
                    zoom=ZOOM_ZONE,
                )
            except Exception as e:
                logger.exception("ts fetch failed")
                st.error(f"Error: {e}")
                return
        st.session_state["ts_data"] = {
            "points": points, "volc_name": v.name, "product": product,
            "n_frames": n_frames, "radius": radius,
        }

    cur = st.session_state["ts_data"]
    points = cur["points"]
    volc_name = cur["volc_name"]
    product = cur["product"]

    if not points:
        st.error("No se pudo descargar la serie. Intenta otro volcán o ventana.")
        return

    # ── KPIs ──
    k = _kpis_from_points(points)
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        kpi_card(f"{k['current']:.2f}%", "Último valor",
                 delta=f"de {k['n']} pts disponibles")
    with k2:
        kpi_card(f"{k['max']:.2f}%", "Máximo en ventana",
                 delta=k["max_dt"].strftime("%H:%M UTC") if k["max_dt"] else "")
    with k3:
        kpi_card(f"{k['mean']:.2f}%", "Promedio")
    with k4:
        trend = k["trend_pct"]
        delta_type = ("negative" if trend > 20
                      else "positive" if trend < -20
                      else "neutral")
        kpi_card(f"{trend:+.0f}%", "Tendencia (1° vs 4° cuarto)",
                 delta="ascendente" if trend > 5 else
                       "descendente" if trend < -5 else "estable",
                 delta_type=delta_type)
    with k5:
        if points:
            t_first = parse_rammb_ts(points[0]["ts"])
            t_last  = parse_rammb_ts(points[-1]["ts"])
            span_h = (t_last - t_first).total_seconds() / 3600
            kpi_card(f"{span_h:.1f} h", "Ventana real")

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    # ── Plot ──
    fig = _plot_series(points, product, volc_name)
    st.plotly_chart(fig, use_container_width=True)

    # ── Tabla descargable ──
    df = pd.DataFrame([
        {"timestamp_utc": p["dt"].strftime("%Y-%m-%d %H:%M:%S"),
         "timestamp_chile": fmt_chile(p["dt"]),
         "metric_pct": round(p["metric"], 3),
         "available": p["available"]}
        for p in points
    ])
    with st.expander("Ver / descargar datos como CSV", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            f"⬇ Descargar CSV ({len(points)} pts)",
            data=csv_bytes,
            file_name=(f"goes19_timeseries_{product}_"
                       f"{volc_name.lower().replace(' ', '_')}_"
                       f"{points[0]['ts'][:12]}_{points[-1]['ts'][:12]}.csv"),
            mime="text/csv",
            key="ts_csv",
        )

    st.markdown(
        '<div style="font-size:0.72rem; color:#445566; margin-top:0.5rem;">'
        '<b>Cómo se calcula:</b> para cada scan, contamos qué fracción de '
        'píxeles del bbox tienen el color característico del producto '
        '(rojo en Ash RGB, verde en SO2 RGB). Es un proxy rápido y '
        'consistente entre scans, no un valor cuantitativo absoluto. '
        'Para tendencia operacional sirve; para reportes formales con '
        'unidades reales (DU, MW, área km²) hace falta calcular desde '
        'L1b — pendiente para v2.'
        '</div>',
        unsafe_allow_html=True,
    )
