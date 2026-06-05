"""Helpers compartidos para mapas Plotly del dashboard.

Centraliza overlays comunes (frontera Chile, anillos de distancia, etc.)
que cualquier vista puede invocar sin duplicar codigo.

NOTA: las coordenadas de Chile estan inline aca (no importadas de
src.borders) para evitar problemas de import en Streamlit Cloud
(cache stale entre deploys). El modulo src.borders sigue existiendo
por si otro proyecto del ecosistema lo necesita.
"""

import base64
import io

import numpy as np
import plotly.graph_objects as go


# ── Lazy load de geometria Chile ─────────────────────────────────────
# _COAST y _BORDER son arrays grandes (~4500 puntos c/u) que estaban
# inline antes — eso hacia map_helpers.py de 110KB y causaba race
# conditions de Streamlit Cloud hot-reload (KeyError 'dashboard.*' al
# importar mientras Streamlit detecta cambio). Ahora viven en JSON.
import json as _json
from pathlib import Path as _Path
_GEO_CACHE: dict | None = None


def _load_geo() -> dict:
    """Cargar chile_geometry.json una vez. Cache en module-level.

    DEFENSIVO: si falla por CUALQUIER razon (archivo missing, JSON corrupto,
    permisos, OOM, lo que sea), devolver dict vacio. La app sigue cargando
    SIN frontera de Chile pero NO crashea. Mejor app degradada que 'Oh no'.
    """
    import logging
    global _GEO_CACHE
    if _GEO_CACHE is None:
        try:
            path = _Path(__file__).parent / "chile_geometry.json"
            with open(path, encoding="utf-8") as f:
                data = _json.load(f)
            coast = [tuple(p) if p[0] is not None else (None, None) for p in data["coast"]]
            border = [tuple(p) for p in data["border"]]
            _GEO_CACHE = {"coast": coast, "border": border}
        except Exception as e:
            logging.exception("Error cargando chile_geometry.json: %s", e)
            _GEO_CACHE = {"coast": [], "border": []}
    return _GEO_CACHE


def _COAST_lazy():
    return _load_geo()["coast"]


def _BORDER_lazy():
    return _load_geo()["border"]




def array_to_data_url(arr: "np.ndarray") -> str:
    """Convertir array numpy uint8 (H, W, 3) a data URL PNG para layout_image.

    Uso tipico en plotly: `fig.add_layout_image(source=array_to_data_url(rgb), ...)`.

    Centraliza la receta que estaba copiada en 8 vistas (modo_guardia,
    modo_guardia_volcan, mosaico_chile, comparador, zonas_fullscreen,
    modo_evento, replay_reciente, backfill_viewer).
    """
    from PIL import Image
    img = Image.fromarray(arr.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def hotspot_distance_km(lat1: float, lon1: float,
                        lat2: float, lon2: float) -> float:
    """Distancia plana km entre dos puntos cercanos (small-angle approximation).

    Usa cos(lat) para corregir la separacion de meridianos. Valido para
    distancias < ~500 km. Centraliza calculo duplicado en modo_guardia,
    modo_evento y heatmap_actividad.
    """
    dlat = (lat2 - lat1) * 111.0
    dlon = (lon2 - lon1) * 111.0 * float(np.cos(np.radians(lat1)))
    return float(np.hypot(dlat, dlon))


def nearest_hotspot(hotspots, lat: float, lon: float):
    """Hotspot mas cercano a (lat, lon) + distancia km. (None, inf) si lista vacia.

    `hotspots` debe ser iterable de objetos con atributos .lat y .lon.
    """
    if not hotspots:
        return None, float("inf")
    best, best_d = None, float("inf")
    for h in hotspots:
        d = hotspot_distance_km(lat, lon, h.lat, h.lon)
        if d < best_d:
            best, best_d = h, d
    return best, best_d


def render_top_navigation_button(label: str, query_string: str,
                                  key: str | None = None,
                                  height: int = 50, full_width: bool = False,
                                  bg: str = "#ff4b4b") -> None:
    """Boton de navegacion interna: setea query_params + rerun.

    HISTORIA de 5 intentos fallidos para "navegar el top frame":
    1. `st.button + st.rerun` — pareciamos pensar que NO funcionaba.
    2. `<a target="_top">` href relativo — resolvia contra iframe URL.
    3. `<button onclick>` en st.markdown — Streamlit sanitiza on*.
    4. `components.html` con onclick top.location — write bloqueado.
    5. `components.html` con anchor + target=_top — sandbox bloquea
       `allow-top-navigation`. Error explicito en console:
       "frame attempting navigation of the top-level window is sandboxed,
        but the flag of 'allow-top-navigation' is not set".

    APRENDIZAJE: el iframe sandbox de Streamlit Cloud NUNCA permite navegar
    el top frame. NINGUN truco JS/HTML funciona. NO insistir.

    SOLUCION DEFINITIVA (intento 6 = vuelta a 1): NO intentar navegar el
    top. Solo setear st.query_params + st.rerun. La URL del browser
    principal NO cambia, pero:
    - app.py lee st.query_params y aplica CSS fullscreen
    - modo_guardia.py lee tv_mode y entra al branch TV
    - El user VE el TV mode aunque la URL del browser sea la misma

    Es la unica forma 100% confiable en Streamlit Cloud.

    Args:
        label:        texto del boton.
        query_string: query params a setear (ej. 'vista=guardia&tv=mosaico').
                      SIN el `?` inicial. Separados por `&`.
        key:          key unico para el st.button (REQUERIDO si hay varios
                      botones en la misma vista — Streamlit lanza error sino).
        height:       NO USADO en esta version (st.button es nativo).
        full_width:   si True, button ocupa 100% del column width.
        bg:           NO USADO (st.button usa estilo primary de Streamlit).
    """
    import streamlit as st
    # CAUSA RAIZ ENCONTRADA (mayo 2026, diagnostico empirico en Chrome):
    # el bug de "Salir no escapa el fullscreen" NUNCA fue el iframe ni el
    # fragment. Era que `st.link_button` renderiza el <a> con
    # **target="_blank"** SIEMPRE (Streamlit lo fuerza). Al hacer click
    # abria una PESTANA NUEVA en ?vista=guardia y dejaba la pantalla de
    # sala intacta en fullscreen. Verificado en vivo: cambiando el target
    # del mismo <a> a "_self" y clickeando, la URL paso de
    # ?vista=guardia&fullscreen=1&tv=1 a ?vista=guardia (escapo OK).
    #
    # Historia de intentos previos (todos fallaban por NO atacar el target):
    #   1. st.button + st.rerun           4. components.html onclick
    #   2. <a> sin target                 5. st.link_button (target=_blank)
    #   3. <form method=get>
    #
    # SOLUCION DEFINITIVA: <a> propio en st.markdown con **target="_self"**
    # (navega la pestana actual). En HF la app NO esta en iframe, asi que
    # _self == pestana. En Streamlit Cloud (iframe) _self recarga el
    # iframe a la nueva query, que tambien sale del fullscreen. href es
    # query-relativa (`?vista=...`) -> reemplaza la querystring actual.
    # Streamlit NO sanitiza href/target en <a> de markdown.
    width_css = "display:block; width:100%; box-sizing:border-box;" if full_width \
        else "display:inline-block;"
    st.markdown(
        f'<a href="?{query_string}" target="_self" '
        f'style="{width_css} text-decoration:none; text-align:center; '
        f'padding:0.4rem 1.2rem; background:{bg}; color:white; '
        f'border-radius:6px; font-weight:600; font-size:0.9rem; '
        f'cursor:pointer; margin-bottom:0.4rem;">{label}</a>',
        unsafe_allow_html=True,
    )


def _interp_segments(pts: list[tuple[float | None, float | None]],
                      n_extra: int = 2
                      ) -> list[tuple[float | None, float | None]]:
    """Linea mas suave: agrega `n_extra` puntos interpolados entre cada
    par consecutivo.

    Soporta (None, None) como separador "lift pen" entre segments
    discontinuos (ej. costa Pacifica chilena = 82 segments separados de
    Natural Earth: continente + islas Chiloe + Tierra del Fuego + etc).
    Plotly interpreta None en x/y arrays como "no conectar" — ESENCIAL
    para no dibujar lineas falsas entre islas.

    Skip interpolacion alrededor de None (evita TypeError).
    """
    out = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        out.append(a)
        # Skip si alguno de los dos es separador (None, None)
        if a[0] is None or b[0] is None:
            continue
        for k in range(1, n_extra + 1):
            t = k / (n_extra + 1)
            out.append((
                a[0] + t * (b[0] - a[0]),
                a[1] + t * (b[1] - a[1]),
            ))
    out.append(pts[-1])
    return out


# Costa Pacifica (oeste) — Arica -> Cabo de Hornos + grandes islas
# (Chiloe, Tierra del Fuego, archipelagos australes).
#
# Fuente: Natural Earth 10m coastline (public domain). Filtrado a bbox
# Chile (lat -56.5 a -17, lon -76.5 a -68.5) + simplificacion Douglas-
# Peucker tolerance 0.003° (~300m).
# 82 segments separados con (None, None) como "lift pen" para Plotly
# (sin las None, dibujaria lineas falsas entre islas distantes).
# Total: 4541 vertices vs 89 hardcoded simplificado antes.
# _COAST removido — ahora se carga lazy desde chile_geometry.json (ver _load_geo)
# Frontera Andina (este, con Argentina/Bolivia/Peru)
# Sur a norte: Tierra del Fuego -> frontera Peru
# Generado desde data/borders/V4_limite_internacional_50k.shp (IGM Chile,
# SIRGAS-Chile / GRS80 ~ WGS84). Concatena: Deslinde ZEE austral + Argentina
# austral (shape 5) + Argentina norte (shape 2) + Bolivia (shape 4).
# 79.158 vertices originales decimados 1:98 -> 809 puntos para Plotly.
# _BORDER removido — ahora se carga lazy desde chile_geometry.json (ver _load_geo)
# Leyendas inline compactas para los 3 productos (modo TV).
# Se renderizan como una sola fila horizontal — caben en el espacio
# negro de la parte superior sin alterar las proporciones del grid.
_LEGEND_ITEMS = {
    "eumetsat_ash": [
        ("#ff3344", "Ceniza"),
        ("#bbff44", "Cirros / nubes altas"),
        ("#ee9944", "Mezcla ceniza+SO2"),
        ("#88aacc", "Superficie"),
        ("#445566", "Nubes met."),
    ],
    "jma_so2": [
        ("#44dd66", "SO2"),
        ("#bbff44", "Cirros"),
        ("#dd4488", "Ash + SO2"),
        ("#88aacc", "Superficie"),
        ("#445566", "Nubes met."),
    ],
    "geocolor": [
        ("#ffffff", "Nubes / nieve"),
        ("#88bb44", "Vegetación"),
        ("#aa8855", "Suelo desnudo"),
        ("#3344aa", "Agua / océano"),
        ("#222244", "Noche (IR)"),
    ],
}

_PRODUCT_LABELS_TV = {
    "eumetsat_ash": "Ash RGB · EUMETSAT B15-B14 / B14-B11 / B13",
    "jma_so2": "SO2 RGB · JMA B07-B09 / B09-B11",
    "geocolor": "GeoColor · Visible mejorado (CIRA)",
}


def render_scan_status_badge(scan_dt, refresh_seconds: int,
                              now=None) -> str:
    """HTML compacto con hora del scan + edad + cadencia de refresh.

    Devuelve un fragment HTML para insertar en otros banners (no usa
    st.markdown directamente). Pensado para Modo Sala: el operador ve
    de un vistazo cuán fresca es la imagen y cuándo viene la próxima
    actualizacion.

    Args:
        scan_dt:          datetime UTC del scan satelital (puede ser None).
        refresh_seconds:  cadencia del fragment (10 = TV rotando,
                          60 = panel normal).
        now:              datetime UTC actual (default = now()).
    """
    from datetime import datetime, timezone
    if now is None:
        now = datetime.now(timezone.utc)
    if scan_dt is None:
        return (
            '<span style="color:#888; font-size:0.78rem;">'
            f'Sin scan · refresh cada {refresh_seconds}s</span>'
        )
    age_min = int((now - scan_dt).total_seconds() / 60)
    if age_min < 15:
        c = "#3fb950"
    elif age_min < 30:
        c = "#d29922"
    else:
        c = "#ff4444"
    # Hora local Chile aprox = UTC-3 (CLST) o UTC-4 (CLT).
    # Usamos zoneinfo para que sea correcto segun horario verano/invierno.
    try:
        from zoneinfo import ZoneInfo
        scan_clt = scan_dt.astimezone(ZoneInfo("America/Santiago"))
        clt_str = scan_clt.strftime("%H:%M CLT")
    except Exception:
        clt_str = ""
    return (
        f'<span style="font-size:0.78rem; color:#cdd; '
        f'display:flex; gap:0.6rem; align-items:center;">'
        f'<span><b style="color:#aabbcc;">Scan:</b> '
        f'{scan_dt.strftime("%H:%M UTC")}'
        f'{(" · " + clt_str) if clt_str else ""}</span>'
        f'<span style="color:{c}; font-weight:700;">·  hace {age_min} min</span>'
        f'<span style="color:#778; border-left:1px solid #334; '
        f'padding-left:0.6rem;">↻ refresh cada {refresh_seconds}s</span>'
        f'</span>'
    )


def render_compact_legend(product: str, extra_left: str = "",
                          extra_right: str = "",
                          height_px: int = 36) -> None:
    """Renderiza una leyenda compacta horizontal para el modo TV.

    Aprovecha el espacio negro arriba de los mapas con swatches +
    labels cortos. Cambia segun el producto actual (Ash / SO2 / GeoColor).

    `extra_left`: HTML opcional para agregar a la izquierda (ej. el
    marcador '🔄 Mosaico ·' que ya existe).
    """
    import streamlit as st
    items = _LEGEND_ITEMS.get(product, [])
    label = _PRODUCT_LABELS_TV.get(product, product)
    html = (
        # clase tv-legend: el CSS del Modo Sala TV la convierte en overlay
        # translucido sobre el top del mapa para no restar alto al grid.
        f'<div class="tv-legend" style="display:flex; gap:0.8rem; '
        f'align-items:center; '
        f'background:rgba(0,0,0,0.65); padding:6px 14px; border-radius:4px; '
        f'margin-bottom:0.3rem; height:{height_px}px; '
        f'font-size:0.76rem; color:#e0e0e0; flex-wrap:wrap;">'
    )
    if extra_left:
        html += extra_left
    html += (
        f'<span style="color:#ff6644; font-weight:700; '
        f'border-right:1px solid #334; padding-right:0.7rem; '
        f'margin-right:0.2rem;">{label}</span>'
    )
    for color, txt in items:
        html += (
            f'<span style="display:flex; align-items:center; gap:4px;">'
            f'<span style="display:inline-block; width:11px; height:11px; '
            f'background:{color}; border:1px solid rgba(255,255,255,0.3); '
            f'border-radius:2px;"></span>{txt}</span>'
        )
    if extra_right:
        html += (
            f'<span style="margin-left:auto; padding-left:0.8rem;">'
            f'{extra_right}</span>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def add_chile_border(fig: go.Figure, color: str = "rgba(255,255,255,0.65)",
                     width: float = 1.4, dash: str = "solid",
                     smooth: bool = False) -> go.Figure:
    """Agrega el contorno de Chile (costa + frontera Andina) como 2 lineas.

    smooth=False (default desde 2026-05-18): _COAST y _BORDER ahora tienen
    densidad nativa alta (Natural Earth 10m + Douglas-Peucker 200-300m).
    Interpolar mas seria desperdicio. Ya no se ven 'jagged' a la escala
    del mosaico.

    Antes (con coords hardcoded de baja densidad) smooth=True triplicaba
    densidad para suavizar — innecesario ahora.
    """
    coast_pts = _COAST_lazy()
    border_pts = _BORDER_lazy()
    coast = _interp_segments(coast_pts, n_extra=2) if smooth else coast_pts
    border = _interp_segments(border_pts, n_extra=2) if smooth else border_pts
    coast_lons = [pt[1] for pt in coast]
    coast_lats = [pt[0] for pt in coast]
    border_lons = [pt[1] for pt in border]
    border_lats = [pt[0] for pt in border]
    # NOTA: shape='spline' rompe en algunas versiones Plotly/Streamlit Cloud.
    # Usamos shape='linear' (default) — la densidad de puntos ya da curvas
    # visualmente suaves sin necesidad de spline.
    line_style = dict(color=color, width=width, dash=dash)
    fig.add_trace(go.Scatter(
        x=coast_lons, y=coast_lats, mode="lines",
        line=line_style,
        hoverinfo="skip", showlegend=False, name="Costa Pacifica",
    ))
    fig.add_trace(go.Scatter(
        x=border_lons, y=border_lats, mode="lines",
        line=line_style,
        hoverinfo="skip", showlegend=False, name="Frontera Andina",
    ))
    return fig
