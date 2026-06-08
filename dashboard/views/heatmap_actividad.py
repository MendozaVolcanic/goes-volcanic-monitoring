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

import plotly.graph_objects as go
import streamlit as st

try:
    from dashboard.style import header
    from src.volcanos import PRIORITY_VOLCANOES, get_volcano
except Exception:
    # Streamlit Cloud hot-reload race condition: retry import dentro de funciones.
    # Si esto se ejecuta, hay un bug — log y reraise para que Streamlit muestre el error.
    import logging as _logging
    _logging.exception("Cross-package import fallo top-level — gotcha Streamlit Cloud")
    raise

logger = logging.getLogger(__name__)

LOOKBACK_DAYS = 7
RADIUS_KM = 50
FRP_TIMELINE_PATH = Path(__file__).parent.parent.parent / "data" / "frp_timeline.json"

# Paleta estable por volcán prioritario (para el timeline intradía).
_VOLCANO_COLORS = {
    "Villarrica": "#ff5252", "Lascar": "#ffb74d", "Copahue": "#ba68c8",
    "Puyehue-Cordon Caulle": "#4fc3f7", "Calbuco": "#81c784",
    "Nevados de Chillan": "#f06292", "Llaima": "#fff176", "Hudson": "#a1887f",
}


def _build_heatmap(counts_by_day: list[dict], today: datetime) -> go.Figure:
    """Heatmap semanal: días en X, volcanes en Y, scans-con-detección como color.

    La métrica (counts_by_day[i][volcan]) es el número de scans de ~10 min con
    ≥1 hotspot ese día — medida de persistencia derivada del roll-up diario de
    frp_timeline.json (NO de un solo scan).
    """
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
        zmin=0, zmax=12,
        hovertemplate=("<b>%{y}</b><br>%{x}<br>Scans con detección: "
                       "%{z}<extra></extra>"),
        colorbar=dict(title="Scans", thickness=12, len=0.6),
    ))
    fig.update_layout(
        height=420, margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
        font=dict(color="#e0e0e0"),
        xaxis=dict(tickfont=dict(size=11)),
        yaxis=dict(tickfont=dict(size=11)),
    )
    return fig


def _load_frp_timeline() -> dict:
    """Lee frp_timeline.json (pre-cocinado por GitHub Action incremental)."""
    if not FRP_TIMELINE_PATH.exists():
        return {}
    try:
        return json.loads(FRP_TIMELINE_PATH.read_text())
    except Exception as e:
        logger.warning("frp_timeline.json corrupto: %s", e)
        return {}


def _build_frp_timeline_fig(scans: list[dict]) -> tuple[go.Figure, dict]:
    """Line chart de FRP (MW) vs tiempo, una traza por volcán con actividad.

    Devuelve (fig, stats) donde stats trae pico/volcán/total para el resumen.
    Volcanes con FRP=0 en toda la ventana NO se grafican (serían líneas planas
    en cero que ensucian) — se listan aparte como 'calmos'.
    """
    times = [datetime.strptime(s["t"], "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc) for s in scans]

    # Sumar FRP por volcán para decidir cuáles tienen señal en la ventana.
    active_total: dict[str, float] = {}
    for s in scans:
        for name, frp in s.get("frp", {}).items():
            if frp and frp > 0:
                active_total[name] = active_total.get(name, 0.0) + frp

    fig = go.Figure()
    peak = {"frp": 0.0, "volcano": None, "t": None}
    for name in sorted(active_total, key=lambda k: -active_total[k]):
        ys = [s.get("frp", {}).get(name, 0.0) for s in scans]
        color = _VOLCANO_COLORS.get(name, "#26c6da")
        fig.add_trace(go.Scatter(
            x=times, y=ys, mode="lines+markers", name=name,
            line=dict(color=color, width=2),
            marker=dict(size=5, color=color),
            hovertemplate=(f"<b>{name}</b><br>%{{x|%d-%b %H:%M}} UTC"
                           "<br>FRP: %{y:.1f} MW<extra></extra>"),
        ))
        m = max(ys) if ys else 0.0
        if m > peak["frp"]:
            peak = {"frp": m, "volcano": name, "t": times[ys.index(m)]}

    fig.update_layout(
        height=380, margin=dict(l=50, r=20, t=20, b=40),
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
        font=dict(color="#e0e0e0"),
        xaxis=dict(title="Tiempo (UTC)", gridcolor="#1a2230",
                   tickfont=dict(size=10)),
        yaxis=dict(title="FRP (MW)", gridcolor="#1a2230", rangemode="tozero",
                   tickfont=dict(size=10)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0,
                    font=dict(size=11)),
        hovermode="x unified",
    )
    stats = {
        "peak": peak,
        "active": active_total,
        "n_scans": len(scans),
        "span_h": round((times[-1] - times[0]).total_seconds() / 3600, 1)
        if len(times) >= 2 else 0,
    }
    return fig, stats


def _render_frp_timeline_section():
    """Sección PRIMARIA: pulso térmico intradía (cadencia GOES 10 min)."""
    header(
        "🌡️ Pulso térmico intradía — GOES cada ~10 min",
        "FRP (Fire Radiative Power) por volcán. La fortaleza única de GOES: "
        "evolución temporal que MODIS/VIIRS (2-4 pasadas/día) no capta.",
    )

    tl = _load_frp_timeline()
    scans = tl.get("scans", [])

    if not scans:
        st.info(
            "📡 Aún no hay serie pre-cocinada. El GitHub Action "
            "`frp_timeline.yml` la genera de forma incremental; la ventana de "
            f"{int(tl.get('window_hours', 48))}h se llena con las corridas. "
            "Primera corrida tras el deploy."
        )
        return

    fig, stats = _build_frp_timeline_fig(scans)
    radius = tl.get("radius_km", RADIUS_KM)
    last_upd = tl.get("last_updated_utc", "?")

    if stats["active"]:
        peak = stats["peak"]
        st.plotly_chart(fig, width="stretch",
                        config={"displayModeBar": False})
        cols = st.columns(3)
        cols[0].metric("🔥 Pico FRP", f"{peak['frp']:.1f} MW",
                       help="Máximo radiativo en la ventana")
        cols[1].metric("Volcán pico", peak["volcano"] or "—")
        cols[2].metric("Scans en ventana", stats["n_scans"],
                       help=f"~{stats['span_h']} h de cobertura GOES")
        activos = ", ".join(f"{k} ({v:.0f} MW acum.)"
                            for k, v in sorted(stats["active"].items(),
                                               key=lambda x: -x[1]))
        st.success(f"🔥 **Con señal térmica** (≤{radius:.0f} km): {activos}")
        calmos = [n for n in PRIORITY_VOLCANOES if n not in stats["active"]]
        if calmos:
            st.caption(f"✅ Sin señal en la ventana: {', '.join(calmos)}")
    else:
        st.success(
            f"✅ **Calma térmica**: 0 MW en los {len(PRIORITY_VOLCANOES)} "
            f"volcanes prioritarios durante las últimas "
            f"~{stats['span_h']:.0f} h ({stats['n_scans']} scans GOES). "
            "Normal — este panel se *enciende* durante actividad efusiva con "
            "lava expuesta (típico: Villarrica, Láscar, Nevados de Chillán)."
        )

    st.caption(f"⏱️ Última actualización del pre-cocinado: {last_upd} · "
               f"radio de atribución {radius:.0f} km · fuente NOAA FDCF GOES-19")


def render():
    from dashboard.manuals import render_manual
    render_manual("heatmap")

    # ── SECCIÓN PRIMARIA: timeline intradía de FRP (fortaleza de GOES) ──
    _render_frp_timeline_section()
    st.markdown("---")

    # ── SECCIÓN SECUNDARIA: panorama semanal (roll-up diario) ──
    header(
        "📅 Panorama semanal — persistencia térmica (7 días)",
        f"Cuántos scans de ~10 min tuvieron detección FDCF ≤{RADIUS_KM} km de "
        "cada volcán, por día. Derivado de la MISMA serie intradía (una sola "
        "fuente), no de un scan suelto. Más scans = actividad más sostenida.",
    )

    today = datetime.now(timezone.utc)

    # Fuente ÚNICA: roll-up diario derivado de frp_timeline.json (los mismos
    # scans de 10 min de la curva de arriba). Hoy y días previos salen del
    # mismo lugar — sin el bug del "conteo de un solo scan".
    daily = _load_frp_timeline().get("daily", {})

    counts_by_day = []
    covered_days = 0  # días cubiertos por el pre-cocinado (aunque sean 0 act.)
    for i in range(LOOKBACK_DAYS):
        day_key = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        if day_key in daily:
            covered_days += 1
        counts_by_day.insert(0, daily.get(day_key, {}))

    fig = _build_heatmap(counts_by_day, today)
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})

    counts_today = counts_by_day[-1]  # último elemento = hoy
    if counts_today:
        active = sorted([k for k, v in counts_today.items() if v > 0],
                        key=lambda k: -counts_today[k])
        st.success(
            f"🔥 **Hoy ({today.strftime('%d-%b')})**: detección térmica en "
            f"{len(active)} volcán(es) — "
            + ", ".join(f"{k} ({counts_today[k]} scans)" for k in active)
        )
    else:
        st.info(
            f"✅ **Hoy ({today.strftime('%d-%b')})**: sin detección FDCF en los "
            f"{len(PRIORITY_VOLCANOES)} volcanes prioritarios (aún). "
            "Calma operacional."
        )

    st.caption(
        f"📊 {covered_days}/{LOOKBACK_DAYS} días cubiertos por el pre-cocinado. "
        "El roll-up se llena hasta 7 días con las corridas horarias del "
        "workflow `frp_timeline.yml` (fuente única con el pulso intradía)."
    )

    # Tabla de detalle del día actual
    if counts_today:
        st.markdown("### Detalle día actual")
        rows = []
        for name in PRIORITY_VOLCANOES:
            v = get_volcano(name)
            if v is None:
                continue
            n = counts_today.get(name, 0)
            rows.append({
                "Volcán": name,
                "Scans con detección": n,
                "Estado": "🔥 Activo" if n > 0 else "✅ Calmo",
                "Región": v.region,
                "Elev (m)": v.elevation,
            })
        st.dataframe(rows, width='stretch', hide_index=True)
