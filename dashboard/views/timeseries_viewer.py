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
from src.fetch.rammb_slider import ZOOM_VOLCAN, ZOOM_ZONE, fetch_frame_for_bounds
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


@st.cache_data(ttl=1200, show_spinner=False)
def _cached_frame(
    product: str, ts: str, lat: float, lon: float, radius_deg: float, zoom: int,
) -> np.ndarray | None:
    """Frame por (producto, ts, vbox, zoom) — para thumbnails de pico/último.

    Cache 20 min. Se llama solo 2 veces por sesión (peak + latest), barato.
    """
    bounds = {
        "lat_min": lat - radius_deg, "lat_max": lat + radius_deg,
        "lon_min": lon - radius_deg, "lon_max": lon + radius_deg,
    }
    return fetch_frame_for_bounds(product, ts, bounds, zoom=zoom)


def _thumb_with_marker(
    img: np.ndarray, vlat: float, vlon: float, bounds: dict,
    label: str = "", peak: bool = False,
) -> bytes:
    """Anotar imagen con marcador del volcán + label en banda inferior.

    Retorna PNG bytes listo para st.image. Si peak=True, banda inferior roja.
    """
    from PIL import Image, ImageDraw, ImageFont
    import io as _io

    pil = Image.fromarray(img).convert("RGB")
    w, h = pil.size

    # Marcador del volcán: convertir lat/lon a (x, y) en la imagen.
    fx = (vlon - bounds["lon_min"]) / (bounds["lon_max"] - bounds["lon_min"])
    fy = 1.0 - (vlat - bounds["lat_min"]) / (bounds["lat_max"] - bounds["lat_min"])
    cx, cy = int(fx * w), int(fy * h)

    draw = ImageDraw.Draw(pil)
    # Triangulo rojo invertido apuntando al volcan
    s = max(8, w // 50)
    tri = [(cx, cy - s), (cx - s, cy + s // 2), (cx + s, cy + s // 2)]
    draw.polygon(tri, fill=(255, 60, 60), outline=(255, 255, 255))
    # Cruz central pequeña en el vertice del triangulo (la coordenada exacta)
    draw.line([(cx - 3, cy), (cx + 3, cy)], fill=(255, 255, 255), width=1)
    draw.line([(cx, cy - 3), (cx, cy + 3)], fill=(255, 255, 255), width=1)

    if label:
        try:
            fs = max(11, int(w * 0.025))
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", fs)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", fs)
            except Exception:
                font = ImageFont.load_default()
        pad = 5
        bbox = draw.textbbox((0, 0), label, font=font)
        band_h = (bbox[3] - bbox[1]) + pad * 2
        # Banda al pie con color segun pico/normal
        col = (180, 50, 50, 200) if peak else (0, 0, 0, 200)
        overlay = Image.new("RGBA", pil.size, (0, 0, 0, 0))
        ovd = ImageDraw.Draw(overlay)
        ovd.rectangle([0, h - band_h, w, h], fill=col)
        pil = Image.alpha_composite(pil.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(pil)
        draw.text((pad, h - band_h + pad), label, fill=(255, 255, 255), font=font)

    buf = _io.BytesIO()
    pil.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


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

    # ── Aviso de NO confiabilidad de la métrica automática ──
    # La fracción "% píxeles con firma de ceniza" se calcula contando
    # píxeles con perfil RGB tipo ceniza en la receta EUMETSAT. Esa receta
    # confunde ceniza con cirros finos, nieve fresca sobre Andes, sombras
    # de nubes altas, polvo desértico y calima costera. En Chile invierno
    # los falsos positivos pueden ser >30% sin evento volcánico real.
    # Se deja la vista para tendencia visual solo — un experto debe cruzar
    # con el imagen Ash RGB cruda en En Vivo o Modo Guardia antes de
    # interpretar.
    st.warning(
        "**⚠ Métrica no validada — usar con criterio.** "
        "El '% píxeles con firma de ceniza' usa la receta RGB EUMETSAT que "
        "confunde ceniza con cirros, nieve sobre Andes, sombras y polvo. "
        "Falsos positivos típicos en Chile invierno: 30-60%. "
        "**Esta serie sirve para detectar CAMBIOS bruscos** (saltos súbitos), "
        "no para magnitud absoluta. Antes de actuar, verificar el frame "
        "Ash RGB en **En Vivo** o **Modo Guardia**, y cruzar con hot spots "
        "NOAA FDCF (producto validado). Trabajamos en sumar filtros (cirros, "
        "albedo) y/o reemplazar por métricas validadas (e.g. detección "
        "tri-espectral Pavolonis 2013, ya disponible en VOLCAT)."
    )

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
        st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
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

    st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)

    # ── Plot ──
    fig = _plot_series(points, product, volc_name)
    st.plotly_chart(fig, use_container_width=True)

    # ── Thumbnails contextuales: PICO + ÚLTIMO ──
    # El plot dice "cuánta señal hay"; estas imágenes dicen "DÓNDE está".
    # Triángulo rojo = posición exacta del volcán (WGS84). Banda inferior
    # roja indica el frame del pico (máximo de la serie).
    valid_pts = [p for p in points if p["available"]]
    if valid_pts and len(valid_pts) >= 2:
        v_obj = get_volcano(volc_name)
        if v_obj is not None:
            ys = [p["metric"] for p in valid_pts]
            peak_idx = ys.index(max(ys))
            peak_pt = valid_pts[peak_idx]
            last_pt = valid_pts[-1]

            # Bounds del bbox usado para extraer la métrica
            bds = {
                "lat_min": v_obj.lat - cur["radius"],
                "lat_max": v_obj.lat + cur["radius"],
                "lon_min": v_obj.lon - cur["radius"],
                "lon_max": v_obj.lon + cur["radius"],
            }

            st.markdown(
                '<div style="font-size:0.78rem; color:#8899aa; '
                'margin:0.4rem 0 0.2rem 0;">'
                '<b style="color:#c0ccd8;">¿Dónde está la señal?</b> '
                'El triángulo rojo marca la coordenada del volcán. '
                'La banda inferior roja indica el frame del pico de la serie '
                '(qué se vio en el momento del máximo).'
                '</div>',
                unsafe_allow_html=True,
            )

            t_col1, t_col2 = st.columns(2)

            with st.spinner("Cargando imágenes contextuales (pico + último)..."):
                peak_img = _cached_frame(
                    product, peak_pt["ts"], v_obj.lat, v_obj.lon,
                    cur["radius"], ZOOM_ZONE,
                )
                last_img = _cached_frame(
                    product, last_pt["ts"], v_obj.lat, v_obj.lon,
                    cur["radius"], ZOOM_ZONE,
                )

            with t_col1:
                if peak_img is not None:
                    label = (
                        f"PICO · {peak_pt['dt'].strftime('%Y-%m-%d %H:%M UTC')} "
                        f"({fmt_chile(peak_pt['dt'])} CL) · {peak_pt['metric']:.2f}%"
                    )
                    png = _thumb_with_marker(
                        peak_img, v_obj.lat, v_obj.lon, bds, label, peak=True,
                    )
                    st.image(
                        png,
                        caption=f"Frame en el pico de la serie — {volc_name}",
                        use_container_width=True,
                    )
                else:
                    st.warning("No se pudo cargar el frame del pico.")

            with t_col2:
                if last_img is not None:
                    label = (
                        f"ÚLTIMO · {last_pt['dt'].strftime('%Y-%m-%d %H:%M UTC')} "
                        f"({fmt_chile(last_pt['dt'])} CL) · {last_pt['metric']:.2f}%"
                    )
                    png = _thumb_with_marker(
                        last_img, v_obj.lat, v_obj.lon, bds, label, peak=False,
                    )
                    st.image(
                        png,
                        caption=f"Último frame disponible — {volc_name}",
                        use_container_width=True,
                    )
                else:
                    st.warning("No se pudo cargar el último frame.")

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
