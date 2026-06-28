"""Pagina VOLCAT: productos pre-procesados por SSEC/CIMSS.

Dos APIs distintas:
- RealEarth API (https://realearth.ssec.wisc.edu): Ash RGB + SO2 RGB Full Disk +
  Volcanic Ash Advisories como overlay.
- VOLCAT portal API (https://volcano.ssec.wisc.edu/imagery): productos
  cuantitativos por sector — Ash Height (km), Ash Loading (g/m²), Ash
  Probability, Ash Reff (radio efectivo de partícula).
"""

import logging

import numpy as np
import plotly.graph_objects as go
import streamlit as st

try:
    from dashboard.style import (
        C_ACCENT, C_ASH, C_SO2,
        ash_legend, ash_so2_legend, header, info_panel, kpi_card, refresh_info_badge,
    )
    from dashboard.utils import fmt_chile
    from src.config import CHILE_BOUNDS, VOLCANIC_ZONES
    from src.fetch.realearth_api import (
        fetch_image,
        fetch_vaa_geojson,
        get_latest_time,
    )
    from src.fetch.volcat_api import (
        VOLCANO_TO_SECTOR, get_sector_for_volcano, resolve_volcat_sector,
        volcat_latest,
    )
    from src.volcanos import CATALOG, PRIORITY_VOLCANOES, get_volcano
except Exception:
    # Streamlit Cloud hot-reload race condition: retry import dentro de funciones.
    # Si esto se ejecuta, hay un bug — log y reraise para que Streamlit muestre el error.
    import logging as _logging
    _logging.exception("Cross-package import fallo top-level — gotcha Streamlit Cloud")
    raise

logger = logging.getLogger(__name__)

ZONE_OPTIONS = {
    "Chile completo": CHILE_BOUNDS,
    "Zona Norte": VOLCANIC_ZONES["norte"],
    "Zona Centro": VOLCANIC_ZONES["centro"],
    "Zona Sur": VOLCANIC_ZONES["sur"],
    "Zona Austral": VOLCANIC_ZONES["austral"],
}


def _norm_origin_lon(origin_lon: float) -> float:
    """ORIGIN_LON de SSEC normalizado a [-180, 180]. Los sectores regionales lo
    dan en forma 0-360 (286 -> -74, hay que restar 360) pero algunos chicos ya
    vienen negativos (Planchon_500m: -73.5). Restar 360 incondicionalmente daba
    -433 y rompia el georef de esos sectores. (fix jun 2026)"""
    return origin_lon - 360.0 if origin_lon > 180.0 else origin_lon


def _overlay_volcanoes_border(fig, bounds, marker_size: int = 9):
    """Dibuja TODOS los volcanes monitoreados (CATALOG = RNVV) dentro de
    `bounds` como triangulos cyan + etiqueta anti-encime (prioritarios
    primero), y la frontera Chile-Argentina con halo (oscuro ancho + claro
    fino, visible sobre nubes/oceano).

    Compartido por la vista de altura georef y los RGB SSEC -> los MISMOS
    volcanes monitoreados + la frontera en todas las vistas VOLCAT. Antes la
    altura no mostraba ningun volcan y ninguna de las dos tenia frontera.
    (jun 2026, pedido OVDAS)
    """
    lat0, lat1 = bounds["lat_min"], bounds["lat_max"]
    lon0, lon1 = bounds["lon_min"], bounds["lon_max"]
    vis = [v for v in CATALOG if lat0 <= v.lat <= lat1 and lon0 <= v.lon <= lon1
           and v.zone != "test"]
    if vis:
        fig.add_trace(go.Scatter(
            x=[v.lon for v in vis], y=[v.lat for v in vis], mode="markers",
            marker=dict(symbol="triangle-up", size=marker_size, color="#00ffff",
                        line=dict(color="#0f1218", width=1.1)),
            hovertext=[f"{v.name} ({v.elevation:,} m)" for v in vis],
            hoverinfo="text", showlegend=False, name="Volcanes monitoreados",
        ))
        # Etiqueta a la IZQUIERDA (xanchor=right): si hay pluma se va al ESTE,
        # asi el nombre no la tapa. Anti-encime greedy (prioritarios primero).
        _mdlat = (lat1 - lat0) * 0.04
        _placed: list[tuple[float, float]] = []
        for v in sorted(vis, key=lambda v: (v.name not in PRIORITY_VOLCANOES,
                                            v.lat)):
            if any(abs(v.lat - pl) < _mdlat and abs(v.lon - pn) < 0.45
                   for pl, pn in _placed):
                continue
            fig.add_annotation(
                x=v.lon, y=v.lat, text=v.name, showarrow=False,
                font=dict(size=11, color="#ffffff"), xanchor="right",
                yanchor="middle", xshift=-7, bgcolor="rgba(8,11,16,0.42)",
                borderpad=2,
            )
            _placed.append((v.lat, v.lon))
    try:
        from dashboard.map_helpers import add_chile_border
        add_chile_border(fig, color="rgba(20,24,32,0.9)", width=3.2)
        add_chile_border(fig, color="rgba(235,240,250,0.9)", width=1.2)
    except Exception:
        logger.warning("add_chile_border fallo en vista VOLCAT", exc_info=True)
    return fig


def _fig_volcat_height_geo(img_bytes, bounds, title, view_bounds=None):
    """Producto VOLCAT (altura/carga/prob/reff) GEOREFERENCIADO + volcanes
    monitoreados + frontera, como plotly.

    `img_bytes` = recorte del mapa (sin titulo ni colorbar quemados) que
    devuelve `_volcat_map_only`; `bounds` = sus lat/lon. Reemplaza al
    `st.image` plano de la seccion de altura para que muestre NUESTROS
    volcanes (RNVV) y la frontera, georeferenciados sobre el sector.

    `view_bounds`: encuadre opcional (zoom). La IMAGEN siempre se coloca sobre
    el sector completo `bounds`, pero los EJES se recortan a `view_bounds`
    (clampeado al sector) -> zoom al volcan elegido en vez del sector regional
    gigante. None = mostrar el sector completo (modo Zona). (jun 2026)
    """
    import base64
    fig = go.Figure()
    if img_bytes:
        b64 = base64.b64encode(img_bytes).decode()
        fig.add_layout_image(
            source=f"data:image/png;base64,{b64}", xref="x", yref="y",
            x=bounds["lon_min"], y=bounds["lat_max"],
            sizex=bounds["lon_max"] - bounds["lon_min"],
            sizey=bounds["lat_max"] - bounds["lat_min"],
            sizing="stretch", layer="below",
        )
    # Encuadre de los ejes: zoom (view_bounds) clampeado al sector, o el sector
    # completo. La imagen ya quedo colocada en `bounds` -> recortar los ejes
    # hace el zoom sin re-descargar nada.
    if view_bounds:
        vb = {
            "lat_min": max(view_bounds["lat_min"], bounds["lat_min"]),
            "lat_max": min(view_bounds["lat_max"], bounds["lat_max"]),
            "lon_min": max(view_bounds["lon_min"], bounds["lon_min"]),
            "lon_max": min(view_bounds["lon_max"], bounds["lon_max"]),
        }
    else:
        vb = bounds
    # Scatter invisible para fijar el dominio de los ejes al encuadre.
    fig.add_trace(go.Scatter(
        x=[vb["lon_min"], vb["lon_max"]],
        y=[vb["lat_min"], vb["lat_max"]],
        mode="markers", marker=dict(opacity=0), showlegend=False,
        hoverinfo="skip",
    ))
    _overlay_volcanoes_border(fig, vb, marker_size=9)
    cos_lat = max(0.1, float(np.cos(np.radians(
        (vb["lat_min"] + vb["lat_max"]) / 2))))
    fig.update_xaxes(range=[vb["lon_min"], vb["lon_max"]],
                     showgrid=False, visible=False, constrain="domain")
    fig.update_yaxes(range=[vb["lat_min"], vb["lat_max"]],
                     showgrid=False, visible=False, scaleanchor="x",
                     scaleratio=1.0 / cos_lat, constrain="domain")
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#ccc")),
        height=640, margin=dict(l=0, r=0, t=34, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _fig_ssec_image(img_rgba, bounds, title, volcanoes):
    """Mostrar imagen SSEC como go.Image con volcanes."""
    fig = go.Figure()

    lat_min = bounds["lat_min"]
    lat_max = bounds["lat_max"]
    lon_min = bounds["lon_min"]
    lon_max = bounds["lon_max"]

    import base64, io
    from PIL import Image as PILImage

    # Convertir RGBA a RGB
    rgb = img_rgba[:, :, :3].copy()
    alpha = img_rgba[:, :, 3:4].astype(np.float32) / 255.0
    rgb = (rgb.astype(np.float32) * alpha).astype(np.uint8)

    buf = io.BytesIO()
    PILImage.fromarray(rgb).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    # Scatter invisible para fijar el dominio del eje
    fig.add_trace(go.Scatter(
        x=[lon_min, lon_max], y=[lat_min, lat_max],
        mode="markers", marker=dict(opacity=0), showlegend=False,
        hoverinfo="skip",
    ))

    # Imagen georeferenciada con add_layout_image (respeta eje Y geográfico)
    fig.add_layout_image(
        source=f"data:image/png;base64,{b64}",
        xref="x", yref="y",
        x=lon_min, y=lat_max,
        xanchor="left", yanchor="top",
        sizex=lon_max - lon_min,
        sizey=lat_max - lat_min,
        sizing="stretch",
        layer="below",
    )

    # Volcanes monitoreados (RNVV) + frontera Chile-Argentina (helper comun
    # con la vista de altura). marker_size chico porque la region RGB puede
    # ser Chile completo (muchos volcanes apilados).
    _overlay_volcanoes_border(fig, bounds, marker_size=6)

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#ccc")),
        xaxis_title="Longitud", yaxis_title="Latitud",
        height=700, template="plotly_dark",
        yaxis=dict(scaleanchor="x", scaleratio=1),
        margin=dict(t=45, b=40, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ── VOLCAT portal: productos por sector (Ash Height, Loading, Probability, Reff) ──

# Cada producto tiene 4 campos:
#   label_es: nombre en dropdown (con unidad)
#   short:    descripcion corta (1 linea, para badge debajo del selector)
#   icon:     icono visual para cheat-sheet
#   long:     panel interpretativo extendido (Markdown) usado en expander
VOLCAT_PRODUCTS = {
    "Ash_Height": {
        "label_es": "Altura de pluma (km AMSL)",
        "short":    "Altura del tope de la pluma sobre el nivel del mar. Más alto = más energético.",
        "icon":     "⬆",
        "long":     """
- **Unidad**: km sobre el nivel del mar (AMSL).
- **Algoritmo**: Pavolonis et al. 2013 — ajuste simultáneo de
  temperatura del tope, espesor óptico y radio efectivo contra
  forward model RTM. Tc → altura usando perfil GFS de temperatura.
- **Precisión**: ±1-2 km en plumas opacas, ±3-4 km en plumas
  delgadas (τ<0.5) o sobre cirrus.
- **Limitación**: si pluma transparente al IR, subestima. Si hay
  nube meteo debajo, también subestima. Cruzar con Ash RGB.
""",
    },
    "Ash_Loading": {
        "label_es": "Carga columnar (g/m²)",
        "short":    "Cuántos gramos de ceniza por m² hay en la columna. Más alto = pluma más densa.",
        "icon":     "⚖",
        "long":     """
- **Unidad**: g/m² (carga columnar de masa de ceniza).
- **Uso**: integrar sobre área de pluma → tonelaje total.
  Combinado con velocidad → tasa de emisión (MER, kg/s).
- **Limitación**: solo cuantificable cuando hay detección estable
  y τ moderado (0.3-2). Plumas opacas saturan; delgadas tienen
  ruido alto.
""",
    },
    "Ash_Probability": {
        "label_es": "Probabilidad de ceniza (%)",
        "short":    "Confianza de que el píxel sea ceniza real (no cirrus/polvo). Filtro recomendado: >60%.",
        "icon":     "✓",
        "long":     """
- **Unidad**: 0-100%.
- **Uso**: confianza de que el píxel contiene ceniza volcánica
  vs cirrus / dust del desierto / nube de hielo.
- **Tip operativo**: usar como filtro sobre Ash_Height y
  Ash_Loading. Solo confiar en valores con probability > 60-70%.
""",
    },
    "Ash_Reff": {
        "label_es": "Radio efectivo (μm)",
        "short":    "Tamaño típico de partícula. <5 μm = fino (transporte largo). >10 μm = grueso (cae cerca).",
        "icon":     "●",
        "long":     """
- **Unidad**: μm (radio efectivo de partícula).
- **Uso**: indicador del modo de eyección. Finas (Reff < 5 μm)
  → eyección violenta + transporte largo. Gruesas (Reff > 10 μm)
  → eyección débil o cerca del cráter.
- **Limitación**: requiere asunción de composición (silicato).
  Basáltica vs riolítica tienen propiedades ópticas distintas.
""",
    },
}


def _volcat_cheatsheet_html() -> str:
    """Mini cheat-sheet de los 4 productos VOLCAT como chips visuales.

    Pensado para ir arriba del selector — el usuario ve los 4 productos
    de un vistazo antes de elegir.
    """
    chips = []
    for k, p in VOLCAT_PRODUCTS.items():
        chips.append(
            f'<div style="background:rgba(17,24,34,0.55); '
            f'border:1px solid rgba(100,120,140,0.2); '
            f'border-radius:6px; padding:0.35rem 0.6rem; '
            f'font-size:0.72rem; line-height:1.35; flex:1; min-width:160px;">'
            f'<div style="color:#c0ccd8; font-weight:700; margin-bottom:0.1rem;">'
            f'<span style="color:#4a9eff;">{p["icon"]}</span> '
            f'{p["label_es"]}'
            f'</div>'
            f'<div style="color:#7a8a99; font-size:0.7rem;">{p["short"]}</div>'
            f'</div>'
        )
    return (
        '<div style="display:flex; gap:0.4rem; flex-wrap:wrap; margin:0.3rem 0 0.5rem 0;">'
        + "".join(chips) + '</div>'
    )


try:
    from src.cache_ttl import TTL_VOLCAT, TTL_FRAME_IMAGE
except Exception:
    # Fallback si Streamlit Cloud falla el import cross-package
    TTL_VOLCAT = 300
    TTL_FRAME_IMAGE = 7200


@st.cache_data(ttl=TTL_VOLCAT, show_spinner=False)
def _volcat_latest_cached(sector: str, instr: str, image_type: str) -> dict | None:
    """Cache TTL_VOLCAT — el VOLCAT publica cada 10 min con scan ABI."""
    return volcat_latest(sector, instr=instr, image_type=image_type)


# Wrappers cacheados de RealEarth API. Antes las llamadas a fetch_image y
# fetch_vaa_geojson eran sin cache → cada rerun bajaba 600x600 PNGs (~50KB c/u).
# Con cache TTL_VOLCAT, dentro de la misma ventana 5 min se reutilizan.
@st.cache_data(ttl=TTL_VOLCAT, show_spinner=False)
def _get_latest_time_cached(product_key: str) -> str | None:
    return get_latest_time(product_key)


@st.cache_data(ttl=TTL_VOLCAT, show_spinner=False)
def _fetch_image_cached(product_key: str, bounds: dict, time: str | None):
    """Wrapper cacheado de RealEarth fetch_image. Bounds cacheado por dict
    serializable (Streamlit hashea el dict)."""
    return fetch_image(product_key, bounds=bounds, time=time)


@st.cache_data(ttl=TTL_VOLCAT, show_spinner=False)
def _fetch_vaa_cached():
    return fetch_vaa_geojson()


@st.cache_data(ttl=TTL_FRAME_IMAGE, show_spinner=False)
def _volcat_image_bytes(image_url: str) -> bytes:
    """Descargar PNG raw del VOLCAT (cache 10 min por URL — la URL incluye timestamp)."""
    import requests
    try:
        r = requests.get(image_url, timeout=30)
        r.raise_for_status()
        return r.content
    except Exception as e:
        logger.warning("Error bajando %s: %s", image_url, e)
        return b""


@st.cache_data(ttl=TTL_FRAME_IMAGE, show_spinner=False)
def _volcat_colorbar_strip(image_url: str) -> bytes:
    """Extrae la TIRA DEL COLORBAR (escala km AMSL) de la imagen VOLCAT completa.

    El `legend_url` de SSEC (overlays/maps/...MAP...) NO es un colorbar: es un
    mapa de costa. El colorbar REAL está QUEMADO al pie de la imagen del producto
    (image_url): a la derecha 'Ash/Dust Height [km AMSL]' (arcoíris) y a la
    izquierda '10.3 µm BT [K]'. Recortamos esa franja inferior EXCLUYENDO el
    globo RealEarth (izq) y los logos NOAA (der). Reutiliza el download cacheado.
    """
    import io
    from PIL import Image
    raw = _volcat_image_bytes(image_url)
    if not raw:
        return b""
    try:
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        w, h = im.size
        # Fracciones medidas sobre el layout SSEC (1000x821). El globo RealEarth
        # y los logos NOAA/CIMSS están ARRIBA (y<0.93); los 2 colorbars con sus
        # NÚMEROS y UNIDADES ("10.3 µm BT [K]" / "Ash/Dust Height [km, ASL]")
        # están en la franja inferior (y 0.935→1.0). Tomamos esa franja desde
        # 0.065*w hasta el BORDE DERECHO (w) para NO cortar ni el inicio de la
        # escala BT ni el final de la escala de altura. (fix jun 2026: el 0.985*w
        # previo cortaba el "0" del "20" en Ash/Dust Height — verificado contra
        # la imagen SSEC 1000×821: el "20" llega hasta ~x=993, no hay logo a la
        # derecha de la franja inferior.)
        crop = im.crop((int(0.065 * w), int(0.935 * h), w, h))
        buf = io.BytesIO()
        crop.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        logger.warning("colorbar strip fail: %s", e)
        return b""


# Fraccion del ANCHO del strip donde cae el GAP entre la barra BT (grayscale,
# izq) y la de altura (arcoiris, der). Medido sobre el layout SSEC (935px): BT
# ~x[0,440], gap blanco ~[420,467], altura ~[467,935]. Cortar a 0.48 separa las
# dos escalas sin partir numeros ni labels. (jun 2026)
_COLORBAR_SPLIT_FRAC = 0.48


def _volcat_colorbar_split_vertical(image_url: str) -> tuple[bytes, bytes]:
    """Separa el colorbar VOLCAT en sus DOS escalas y las devuelve VERTICALES.

    El strip SSEC trae dos escalas pegadas: '10.3 µm BT [K]' (grayscale, izq) y
    'Ash/Dust Height [km, ASL]' (arcoiris, der). Las corto en el gap (~48% del
    ancho) y roto cada una 90° CCW (valores abajo→arriba, label de costado).
    Devuelve (bt_vertical, height_vertical) para incrustar una a cada lado del
    mapa -> ninguna tapa la cordillera ni va debajo (evita scroll). Reusa el
    strip horizontal cacheado. (jun 2026, pedido OVDAS)
    """
    raw = _volcat_colorbar_strip(image_url)
    if not raw:
        return b"", b""
    try:
        import io
        from PIL import Image
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        w, h = im.size
        split = int(_COLORBAR_SPLIT_FRAC * w)
        parts = (im.crop((0, 0, split, h)).rotate(90, expand=True),      # BT
                 im.crop((split, 0, w, h)).rotate(90, expand=True))      # altura
        out = []
        for p in parts:
            buf = io.BytesIO()
            p.save(buf, format="PNG")
            out.append(buf.getvalue())
        return out[0], out[1]
    except Exception as e:
        logger.warning("colorbar split vertical fail: %s", e)
        return b"", b""


@st.cache_data(ttl=TTL_FRAME_IMAGE, show_spinner=False)
def _volcat_image_with_overlays(image_url: str,
                                 volcanoes_url: str | None,
                                 latlon_url: str | None) -> bytes:
    """Compone la imagen VOLCAT base + overlays de SSEC (fronteras lat/lon
    y marcadores de volcanes), todos pre-alineados al mismo sector.

    Los overlays de SSEC son PNG RGBA del MISMO tamano que la base, asi que
    es alpha-composite directo (fronteras primero, volcanes encima). Asi la
    imagen VOLCAT pasa a mostrar los volcanes — antes era IR pelado sin
    referencia geografica. Cacheada por las 3 URLs (incluyen timestamp).
    """
    import io
    from concurrent.futures import ThreadPoolExecutor
    import requests
    from PIL import Image

    def _dl(url):
        """Baja una URL y la abre como PIL RGBA (None si falla/vacia)."""
        if not url:
            return None
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            return Image.open(io.BytesIO(r.content)).convert("RGBA")
        except Exception as e:
            logger.warning("VOLCAT dl %s: %s", url, e)
            return None

    # Descargas EN PARALELO (base + fronteras + volcanes). Antes eran
    # seriales -> 3 round-trips x 3 zonas = 9 seriales, hacian el frame
    # VOLCAT tan lento que trababa la rotacion de 10s del Modo Sala.
    with ThreadPoolExecutor(max_workers=3) as ex:
        f_base = ex.submit(_dl, image_url)
        f_ll = ex.submit(_dl, latlon_url)
        f_vol = ex.submit(_dl, volcanoes_url)
        base, ll, vol = f_base.result(), f_ll.result(), f_vol.result()

    if base is None:
        return b""
    # Composicion: fronteras/grilla primero, volcanes ENCIMA (mas visibles).
    for ov in [ll, vol]:
        if ov is not None and ov.size == base.size:
            base = Image.alpha_composite(base, ov)
    buf = io.BytesIO()
    base.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


def _volcat_reproject_ps(base, coords: dict, left: int, top: int,
                         right: int, bot: int) -> dict | None:
    """Reproyecta la region [left,right]x[top,bot] de una imagen VOLCAT en
    Polar Stereographic (sector Chile_South_2_km) a una grilla regular lat/lon
    (Plate Carree), y devuelve {'png','bounds'} listo para georeferenciar lineal
    en plotly. None si faltan pyproj/scipy.

    POR QUE: el sector sur de SSEC se sirve en PS (coords PROJECTION='PS',
    SCALE_FACTOR en metros/pixel, ECCENT/SECOND_REF_LAT/REF_LON). La imagen es
    lineal en el PLANO de proyeccion, NO en lat/lon, asi que el stretch lineal
    de plotly desalinea el overlay (volcanes/frontera) hacia los bordes: medido
    ~0.45 deg ~ 50 km abajo, vs ~ancho de linea con esta reproyeccion. El path
    CE (Chile_North/Central) NO pasa por aca.

    Convencion SSEC validada (jun 2026) contra la grilla cyan: el pixel origen
    (col=OFFSET_X, row=OFFSET_Y) cae en (ORIGIN_LAT, ORIGIN_LON); el paso es
    SCALE_FACTOR metros/pixel en el plano; proj stere lat_0=-90 lat_ts=
    SECOND_REF_LAT lon_0=REF_LON sobre WGS84. -> lat enteras -42..-54 y lon
    enteras -85..-60 caen exactas en sus lineas.
    """
    try:
        import io as _io
        import numpy as np
        from pyproj import Transformer
        from scipy.ndimage import map_coordinates
    except Exception:
        return None
    try:
        reflon = _norm_origin_lon(coords["REF_LON"])
        olon = _norm_origin_lon(coords["ORIGIN_LON"])
        olat = coords["ORIGIN_LAT"]
        OX = coords.get("OFFSET_X", 0)
        OY = coords.get("OFFSET_Y", 0)
        SF = float(coords["SCALE_FACTOR"])          # metros/pixel en el plano
        lat_ts = coords.get("SECOND_REF_LAT", -60)
        P = Transformer.from_crs(
            "EPSG:4326",
            f"+proj=stere +lat_0=-90 +lat_ts={lat_ts} +lon_0={reflon} "
            f"+ellps=WGS84 +x_0=0 +y_0=0",
            always_xy=True)
        Xo, Yo = P.transform(olon, olat)            # (X,Y) del pixel origen
        # pixel (col,row) -> plano: X = Xo+(col-OX)*SF ; Y = Yo+(OY-row)*SF
        arr = np.asarray(base.convert("RGB"))

        # bounds lat/lon de la region cropeada (muestreo grueso -> min/max, PS
        # curva los meridianos asi que no basta con las 4 esquinas).
        cc = np.linspace(left, right, 40)
        rr = np.linspace(top, bot, 40)
        CC, RR = np.meshgrid(cc, rr)
        Xg = Xo + (CC - OX) * SF
        Yg = Yo + (OY - RR) * SF
        lon_g, lat_g = P.transform(Xg.ravel(), Yg.ravel(), direction="INVERSE")
        lon_g = np.asarray(lon_g); lat_g = np.asarray(lat_g)
        bounds = {
            "lat_min": float(np.nanmin(lat_g)), "lat_max": float(np.nanmax(lat_g)),
            "lon_min": float(np.nanmin(lon_g)), "lon_max": float(np.nanmax(lon_g)),
        }

        # grilla de salida Plate Carree; cada pixel de salida -> pixel fuente.
        out_w = max(64, int(right - left))
        out_h = max(64, int(bot - top))
        lats_out = np.linspace(bounds["lat_max"], bounds["lat_min"], out_h)
        lons_out = np.linspace(bounds["lon_min"], bounds["lon_max"], out_w)
        LON, LAT = np.meshgrid(lons_out, lats_out)
        Xs, Ys = P.transform(LON.ravel(), LAT.ravel())   # latlon -> plano
        Xs = np.asarray(Xs); Ys = np.asarray(Ys)
        src_col = (Xs - Xo) / SF + OX                     # -> pixel original
        src_row = OY - (Ys - Yo) / SF
        rc = np.array([src_row, src_col])                # (2, N)
        out = np.zeros((out_h, out_w, 3), dtype=np.uint8)
        for ch in range(3):
            vals = map_coordinates(arr[:, :, ch].astype(np.float32), rc,
                                   order=1, mode="constant", cval=0.0,
                                   prefilter=False)
            out[:, :, ch] = np.clip(vals.reshape(out_h, out_w), 0, 255
                                    ).astype(np.uint8)
        from PIL import Image as _PILImg
        buf = _io.BytesIO()
        _PILImg.fromarray(out).save(buf, format="PNG")
        return {"png": buf.getvalue(), "bounds": bounds}
    except Exception as e:
        logger.warning("VOLCAT PS reproject fallo: %s", e)
        return None


class _VolcatMapUnavailable(Exception):
    """Fallo TRANSITORIO al bajar/recortar el frame VOLCAT (SSEC caido o coords
    rotas). El core cacheado lo LANZA en vez de devolver {} porque st.cache_data
    NO cachea excepciones -> la proxima llamada reintenta hasta exito, en lugar
    de dejar la zona en blanco las 2h del TTL. (fix jun 2026, audit Modo Guardia)
    """


@st.cache_data(ttl=TTL_FRAME_IMAGE, show_spinner=False)
def _volcat_map_only_cached(image_url: str, latlon_url: str | None,
                            coords: dict) -> dict:
    """Core cacheado de _volcat_map_only. Lanza _VolcatMapUnavailable en fallo
    (NO devuelve {}) para no envenenar la cache con el negativo. Solo los
    EXITOS quedan cacheados. Usar via el wrapper _volcat_map_only."""
    import io
    import math
    from concurrent.futures import ThreadPoolExecutor
    import numpy as np
    import requests
    from PIL import Image

    def _dl(url):
        if not url:
            return None
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            return Image.open(io.BytesIO(r.content)).convert("RGBA")
        except Exception as e:
            logger.warning("VOLCAT dl %s: %s", url, e)
            return None

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_base = ex.submit(_dl, image_url)
        f_ll = ex.submit(_dl, latlon_url)
        base, ll = f_base.result(), f_ll.result()
    if base is None:
        raise _VolcatMapUnavailable("descarga SSEC del frame fallo")
    w, h = base.size

    # Extent del mapa via lineas de grilla cyan del overlay latlon.
    top, bot, left, right = 0, h - 1, 0, w - 1
    if ll is not None and ll.size == base.size:
        a = np.array(ll)
        alpha = a[:, :, 3] > 40
        cyan = (a[:, :, 1] > 150) & (a[:, :, 2] > 150) & (a[:, :, 0] < 120) & alpha
        ys = np.where(cyan.any(axis=1))[0]
        xs = np.where(cyan.any(axis=0))[0]
        if len(ys) and len(xs):
            top, bot = int(ys.min()), int(ys.max())
            left, right = int(xs.min()), int(xs.max())

    # SSEC tambien quema el texto amarillo "GOES-19 ABI (fecha)" SOBRE la
    # esquina superior del mapa (debajo del titulo blanco ya recortado).
    # Lo detectamos por su color amarillo brillante y recortamos hasta
    # despues — redundante con nuestro header de zona+hora.
    try:
        rgb = np.array(base.convert("RGB"))
        scan_to = min(top + 70, h)
        yellow = ((rgb[:scan_to, :, 0] > 170) & (rgb[:scan_to, :, 1] > 170)
                  & (rgb[:scan_to, :, 2] < 110))
        yrows = np.where(yellow.sum(axis=1) > 5)[0]
        if len(yrows):
            top = max(top, int(yrows.max()) + 4)
    except Exception:
        pass

    # PROYECCION: Chile_South_2_km se sirve en Polar Stereographic (PS), no en
    # Plate Carree como North/Central. En PS la imagen es lineal en el plano de
    # proyeccion, NO en lat/lon -> reproyectamos a Plate Carree para que el
    # stretch lineal de plotly + el overlay (volcanes/frontera) alineen (sin
    # esto el corrimiento llega a ~0.45 deg ~50 km en los bordes). El path CE de
    # abajo queda intacto para los demas sectores. (fix jun 2026, validado vs la
    # grilla cyan)
    if str(coords.get("PROJECTION", "")).upper() == "PS":
        ps = _volcat_reproject_ps(base, coords, left, top, right, bot)
        if ps is not None:
            return ps
        # sin pyproj/scipy -> caemos al path CE lineal (aproximado pero algo).

    try:
        dp = math.degrees(coords["SCALE_FACTOR"] / coords["EQ_RADIUS"])
        lat0 = coords["ORIGIN_LAT"] + coords.get("OFFSET_Y", 0) * dp
        lon0 = _norm_origin_lon(coords["ORIGIN_LON"]) + coords.get("OFFSET_X", 0) * dp
        bounds = {
            "lat_max": lat0 - top * dp, "lat_min": lat0 - bot * dp,
            "lon_min": lon0 + left * dp, "lon_max": lon0 + right * dp,
        }
    except Exception as e:
        raise _VolcatMapUnavailable("coords del sector invalidas") from e

    crop = base.crop((left, top, right + 1, bot + 1)).convert("RGB")
    buf = io.BytesIO()
    crop.save(buf, format="PNG")
    return {"png": buf.getvalue(), "bounds": bounds}


def _volcat_map_only(image_url: str, latlon_url: str | None,
                     coords: dict) -> dict:
    """Baja la imagen VOLCAT y la RECORTA al area del mapa, quitando el titulo
    quemado (arriba) y la colorbar quemada (abajo) de SSEC. Usa el overlay de
    grilla latlon como referencia robusta del extent. Devuelve {'png','bounds'}
    o {} si el frame no esta disponible.

    Wrapper NO cacheado sobre _volcat_map_only_cached: traduce el fallo
    transitorio (_VolcatMapUnavailable) a {} para los callers, SIN cachear el
    negativo -> un blip de SSEC no deja la zona en blanco las 2h del TTL; se
    reintenta en cada render hasta que SSEC responde. (fix jun 2026)
    """
    try:
        return _volcat_map_only_cached(image_url, latlon_url, coords)
    except _VolcatMapUnavailable:
        return {}


def _volcat_sector_bounds(coords: dict, w: int, h: int) -> dict | None:
    """Deriva los lat/lon bounds de la imagen VOLCAT desde la proyeccion
    Cylindrical Equidistant (Plate Carree) de SSEC.

    OJO: SOLO vale para sectores CE (Chile_North/Central). Para PS
    (Chile_South_2_km) la relacion pixel->lat/lon NO es lineal -> usar el
    camino de _volcat_reproject_ps. Esta funcion hoy NO tiene call sites (el
    georef vivo pasa por _volcat_map_only); se mantiene como utilitario CE.

    VALIDADO (mayo 2026) contra las lineas de grilla del overlay latlon:
    con OFFSET_Y aplicado al lat de origen, las lineas caen en enteros
    exactos (lon -75/-65, lat -18/-20/...-30). Esto permite georeferenciar
    la imagen en plotly y dibujar NUESTROS volcanes (mismos que las RGB)
    en vez del overlay sobrecargado de SSEC.
    """
    try:
        import math
        dp = math.degrees(coords["SCALE_FACTOR"] / coords["EQ_RADIUS"])
        lon_min = _norm_origin_lon(coords["ORIGIN_LON"]) + coords.get("OFFSET_X", 0) * dp
        lat_max = coords["ORIGIN_LAT"] + coords.get("OFFSET_Y", 0) * dp
        return {
            "lon_min": lon_min, "lon_max": lon_min + w * dp,
            "lat_max": lat_max, "lat_min": lat_max - h * dp,
        }
    except Exception:
        return None


def _volcat_dt_obj(s: str | None):
    """'2026-04-25_17-20-30' -> datetime UTC (o None)."""
    if not s:
        return None
    try:
        from datetime import datetime, timezone
        d, t = s.split("_")
        hh, mm, ss = t.split("-")
        return datetime(*map(int, d.split("-")), int(hh), int(mm), int(ss),
                        tzinfo=timezone.utc)
    except Exception:
        return None


def _parse_volcat_dt(s: str | None) -> str:
    """'2026-04-25_17-20-30' -> '2026-04-25 17:20 UTC (...CL)'."""
    dt = _volcat_dt_obj(s)
    if dt is None:
        return s or "—"
    return f"{dt.strftime('%Y-%m-%d %H:%M UTC')} ({fmt_chile(dt)} Chile)"


# ── Altura propia INDICATIVA: ACHA NOAA (ABI-L2-ACHA2KMF) ∩ máscara de ceniza ──
# Complementa al VOLCAT (que sigue siendo el primario cuantitativo) con MENOR
# latencia (~13 min vs 30-50) y de forma independiente del host SSEC. NO es el
# producto VAA: ACHA es altura de nube genérica, la máscara de ceniza la pone
# nuestra detección tri-espectral. Ver docs/own_volcat/FASE0_ARRANQUE.md.


@st.cache_data(ttl=TTL_VOLCAT, show_spinner=False)
def _acha_plume_cached(volc_name: str, radius_deg: float, bucket: str) -> dict | None:
    """Wrapper cacheado de plume_top_height. `bucket` (cuño de 10 min) invalida
    el cache cuando llega un scan nuevo. Lazy import por el gotcha de hot-reload.

    El dict resultante trae numpy arrays (field_km/lat/lon) — picklables, ok
    para st.cache_data. Devuelve None si el módulo no carga (deploy degradado)."""
    from datetime import datetime, timezone
    try:
        from src.process.acha_plume_height import plume_top_height
    except Exception:
        logger.exception("acha_plume_height no importable")
        return None
    return plume_top_height(datetime.now(timezone.utc), volc_name,
                            radius_deg=radius_deg)


@st.cache_data(ttl=TTL_VOLCAT, show_spinner=False)
def _btmatch_cached(volc_name: str, radius_deg: float, bucket: str) -> dict | None:
    """Wrapper cacheado del 2º método de altura propia (BT-matching, Fase 3a):
    BT(11µm) del tope de ceniza → perfil GFS T(z). Independiente de ACHA — sirve
    de cross-check y rescata casos donde la L2 de ACHA no tiene retrieval."""
    from datetime import datetime, timezone
    try:
        from src.process.bt_matching_height import bt_matching_top_height
    except Exception:
        logger.exception("bt_matching_height no importable")
        return None
    return bt_matching_top_height(datetime.now(timezone.utc), volc_name,
                                  radius_deg=radius_deg)


def _fig_acha_field(field_km, lat, lon, view_bounds, title: str):
    """Campo de altura del tope (km) sobre los píxeles de ceniza, georef +
    volcanes monitoreados + frontera. Heatmap plotly: las celdas sin ceniza
    quedan transparentes (NaN), así se ve SOLO la pluma coloreada.

    La grilla ACHA es geos (curva), pero sobre un encuadre de ±1° la curvatura
    es sub-pixel → usamos los ejes 1-D del centro de la ventana (aprox. Plate
    Carrée). Suficiente para un producto INDICATIVO. (Fase 0)
    """
    h, w = field_km.shape
    # Defensivo: si _plume_top_stats recortó field_km (guard de shapes), lat/lon
    # conservan el shape original de la ventana ACHA → alinearlos a field_km
    # antes de derivar los ejes, o el Heatmap quedaría desfasado. (review jun 2026)
    lat = lat[:h, :w]
    lon = lon[:h, :w]
    lat_1d = lat[:, w // 2]
    lon_1d = lon[h // 2, :]
    finite = field_km[np.isfinite(field_km)]
    vmax = float(finite.max()) if finite.size else 12.0
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=field_km, x=lon_1d, y=lat_1d,
        colorscale="Turbo", zmin=0.0, zmax=max(vmax, 4.0),
        hoverongaps=False,
        colorbar=dict(title=dict(text="km<br>AMSL", side="right"),
                      thickness=14, len=0.9),
        hovertemplate="lat %{y:.2f}°, lon %{x:.2f}°<br>"
                      "tope %{z:.1f} km<extra></extra>",
    ))
    _overlay_volcanoes_border(fig, view_bounds, marker_size=11)
    cos_lat = max(0.1, float(np.cos(np.radians(
        (view_bounds["lat_min"] + view_bounds["lat_max"]) / 2))))
    fig.update_xaxes(range=[view_bounds["lon_min"], view_bounds["lon_max"]],
                     showgrid=False, visible=False, constrain="domain")
    fig.update_yaxes(range=[view_bounds["lat_min"], view_bounds["lat_max"]],
                     showgrid=False, visible=False, scaleanchor="x",
                     scaleratio=1.0 / cos_lat, constrain="domain")
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#ccc")),
        height=560, margin=dict(l=0, r=0, t=34, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(8,11,16,1)",
    )
    return fig


# Mínimo de píxeles con firma SO2 (BT 8.4−11.2 < umbral) para etiquetar una
# detección sin ceniza como "pluma de SO2/gas" en vez de "sin pluma". (review jun)
_SO2_CONTEXT_MIN_PX = 6


def _render_acha_indicative_section(v_obj, radius_deg: float,
                                    key_suffix: str) -> None:
    """Bloque de la altura propia INDICATIVA (ACHA ∩ ceniza) para UN volcán.

    Detrás de un botón (baja 3 bandas L1b + el gránulo ACHA, ~varios MB) y
    cacheado 10 min. Etiquetado sin ambigüedad: complementa, no reemplaza, al
    VOLCAT cuantitativo de arriba.
    """
    st.markdown(
        '<div style="background:rgba(255,176,32,0.08); '
        'border-left:3px solid #ffb020; padding:0.45rem 0.75rem; '
        'border-radius:0 6px 6px 0; margin:0.5rem 0; font-size:0.78rem; '
        'line-height:1.5;">'
        '<b style="color:#ffb020;">⬆ Altura del tope · propia (INDICATIVO)</b> '
        '<span style="color:#aabbc8;">— dos métodos independientes sobre los '
        'píxeles de <b>ceniza</b> del scan: <b>(1) ACHA NOAA</b> '
        '(<code>ABI-L2-ACHA2KMF</code>) enmascarado por nuestra detección '
        'tri-espectral, y <b>(2) BT-matching propio</b> (BT 11 µm → perfil GFS '
        'T(z), independiente de SSEC y de ACHA, cota inferior). <b>No es '
        'VOLCAT</b> ni mide gas/SO₂. El VOLCAT/SSEC de arriba sigue siendo el '
        'número cuantitativo de referencia.</span></div>',
        unsafe_allow_html=True,
    )

    flag_key = f"acha_go_{v_obj.name}_{key_suffix}"
    if st.button("Calcular tope de pluma propio (ACHA + BT-matching)",
                 key=f"acha_btn_{v_obj.name}_{key_suffix}"):
        st.session_state[flag_key] = True
    if not st.session_state.get(flag_key):
        st.caption("Producto propio NRT — apretá para bajar las bandas del scan, "
                   "el gránulo ACHA y el perfil GFS, y calcular el tope por los "
                   "dos métodos. El VOLCAT de arriba sigue siendo la referencia.")
        return

    from datetime import datetime, timezone
    bucket = datetime.now(timezone.utc).strftime("%Y%m%d%H") + \
        str(datetime.now(timezone.utc).minute // 10)
    acha_radius = min(float(radius_deg), 1.5)   # acotar la ventana de descarga
    with st.spinner("Bajando bandas + ACHA + perfil GFS y calculando el tope "
                    "(2 métodos)..."):
        acha = _acha_plume_cached(v_obj.name, acha_radius, bucket)
        btm = _btmatch_cached(v_obj.name, acha_radius, bucket)

    acha_ok = bool(acha) and acha.get("status") == "ok"
    btm_ok = bool(btm) and btm.get("status") == "ok"
    acha_nd = (acha is None) or acha.get("status") == "no_data"
    btm_nd = (btm is None) or btm.get("status") == "no_data"

    if acha_nd and btm_nd:
        reason = (acha or btm or {}).get("reason", "sin datos accesibles")
        st.warning(f"No pude calcular la altura propia: {reason}. "
                   "Puede ser scan ABI atrasado o S3/Open-Meteo intermitente — "
                   "reintentá.")
        return

    # scan/contexto: preferir ACHA (trae el contexto SO2), si no BT-matching.
    primary = acha if (acha and acha.get("status") in ("ok", "no_plume")) else btm
    scan_dt = (primary or {}).get("scan_dt")
    ts_txt = "—"
    if scan_dt is not None:
        ts_txt = f"{scan_dt.strftime('%Y-%m-%d %H:%M UTC')} ({fmt_chile(scan_dt)} Chile)"

    # ── Sin ceniza por ninguno de los dos métodos ───────────────────────
    if not acha_ok and not btm_ok:
        # El contexto SO2 puede venir de cualquiera de los dos resultados (ACHA
        # falla a no_data sin SO2; entonces lo toma de BT-matching). (review jun)
        so2_px = int((acha or {}).get("so2_px") or (btm or {}).get("so2_px") or 0)
        if so2_px >= _SO2_CONTEXT_MIN_PX:
            so2_min = (acha or {}).get("so2_min") or (btm or {}).get("so2_min")
            so2_txt = f" (mín BT 8.4−11.2 µm ≈ {so2_min:.1f} K)" if so2_min else ""
            st.info(
                f"Scan **{ts_txt}**: nuestra detección marcó **pluma de SO₂/gas** "
                f"(~{so2_px} píxeles{so2_txt}) pero **sin ceniza silicatada "
                "IR-opaca**. La altura propia **no aplica a plumas de gas**: el "
                "SO₂ es transparente en 11 µm, así que ACHA/BT-matching darían "
                "alturas espurias (por debajo del cráter). Para el SO₂ usá el "
                "**indicador SO₂** (Modo Guardia / RGB). *(Validado con la pluma "
                "de Chillán del 27-jun.)*"
            )
        else:
            st.info(
                f"Scan **{ts_txt}**: sin firma de ceniza en el encuadre "
                f"(±{acha_radius:g}°) → sin tope que reportar. Sin pluma activa "
                "de ceniza esto es lo esperado."
            )
        return

    # ── Al menos un método dio tope → cross-validación ──────────────────
    cols = st.columns(4)
    with cols[0]:
        if acha_ok:
            kpi_card(f"{acha['top_km']:.1f} km", "ACHA NOAA · p95")
        else:
            kpi_card("—", "ACHA (sin retrieval)")
    with cols[1]:
        if btm_ok:
            kpi_card(f"{btm['top_km']:.1f} km", "BT-matching · p95")
        else:
            kpi_card("—", "BT-matching")
    with cols[2]:
        mp = acha.get("mask_px") if acha_ok else (btm or {}).get("mask_px", 0)
        kpi_card(f"{mp:,}", "Píxeles de ceniza")
    with cols[3]:
        lat_min = (primary or {}).get("latency_min")
        kpi_card(f"~{lat_min:.0f} min" if lat_min is not None else "—", "Latencia")

    # Acuerdo entre métodos (cross-check de confianza).
    def _capped_txt(r):
        nc = (r or {}).get("n_capped") or 0
        if (r or {}).get("all_capped"):
            return " · ⚠ todos los píxeles en la tropopausa (cirros/overshooting)"
        return (f" · {nc} px en la tropopausa excluidos del tope" if nc else "")

    if acha_ok and btm_ok:
        d = btm["top_km"] - acha["top_km"]
        agree = ("✓ concuerdan (|Δ| ≤ 1.5 km)" if abs(d) <= 1.5
                 else "⚠ discrepan > 1.5 km — revisar")
        st.caption(
            f"|Δ(BT-matching − ACHA)| = **{abs(d):.1f} km** ({d:+.1f}) · {agree}. "
            "Ambos métodos tienden a subestimar (BT-matching y la OE de ACHA son "
            "cotas inferiores en plumas semi-transparentes), así que el signo de "
            f"Δ no está garantizado.{_capped_txt(btm)}"
        )
    elif btm_ok and not acha_ok:
        st.caption(
            f"ACHA no tuvo retrieval válido sobre los píxeles de ceniza; "
            f"el **BT-matching propio** (independiente de la L2 de NOAA) sí: "
            f"tope p95 **{btm['top_km']:.1f} km** (máx {btm['top_max_km']:.1f} km). "
            f"Típicamente cota inferior.{_capped_txt(btm)}"
        )
    elif acha_ok and not btm_ok:
        low_conf = acha["mask_px"] < 3
        st.caption(
            f"Pico ACHA: {acha['top_max_km']:.1f} km (1 px, referencia)."
            + ("  ⚠ Detección muy chica (&lt; 3 px): confianza baja."
               if low_conf else "")
        )

    # Mapa del campo: preferir el que tenga ceniza (ACHA, si no BT-matching).
    fld = acha if acha_ok else btm
    view_bounds = {
        "lat_min": v_obj.lat - acha_radius, "lat_max": v_obj.lat + acha_radius,
        "lon_min": v_obj.lon - acha_radius, "lon_max": v_obj.lon + acha_radius,
    }
    method_lbl = "ACHA ∩ ceniza" if acha_ok else "BT-matching ∩ ceniza"
    st.plotly_chart(
        _fig_acha_field(fld["field_km"], fld["lat"], fld["lon"], view_bounds,
                        f"Tope de pluma ({method_lbl}) · INDICATIVO · {ts_txt}"),
        width="stretch",
        config={"displayModeBar": False, "responsive": True},
        key=f"acha_field_{v_obj.name}_{key_suffix}",
    )
    st.caption(
        "▲ cyan = volcanes monitoreados (RNVV) · color = altura del tope (km "
        f"AMSL) SOLO donde hay firma de ceniza · **fuente**: {fld['source']}."
    )
    with st.expander("Cómo se calculan y sus límites", expanded=False):
        st.markdown(
            "**Dos métodos independientes sobre los mismos píxeles de ceniza** "
            "(`detect_ash_enhanced`: BTD split-window 11–12 µm + tri-espectral "
            "con 8.4 µm, del MISMO scan ABI):\n\n"
            "1. **ACHA NOAA** (`ABI-L2-ACHA2KMF`, var `HT`): retrieval de altura "
            "de tope de nube de NOAA (Heidinger OE), 2 km, filtrado por DQF "
            "(*good*+*marginal*+*opaque*). Latencia ~13 min.\n"
            "2. **BT-matching propio** (Fase 3a): la BT(11 µm) del tope opaco ≈ "
            "su temperatura efectiva; se la busca en el **perfil GFS T(z)** "
            "(Open-Meteo) y se interpola a altitud. Independiente de SSEC y de "
            "la L2 de NOAA → rescata casos donde ACHA no tiene retrieval. Es "
            "**cota inferior**: subestima plumas semi-transparentes.\n\n"
            "- **Tope reportado**: percentil 95 (robusto) + pico de referencia.\n"
            "- **No miden gas**: una pluma de SO₂/gas (transparente en 11 µm) NO "
            "da altura válida — se reporta aparte.\n"
            "- **Cuantitativo validado**: el primario sigue siendo el "
            "**VOLCAT/SSEC** de arriba (Pavolonis 2013)."
        )


def _render_height_section(key_suffix: str = "tab") -> None:
    """Render del bloque Altura/Loading/Probability/Reff.

    Reutilizado en la tab dedicada (cuando se hizo fetch del RGB) y en la
    pantalla inicial (cuando no se hizo fetch — porque la altura no requiere
    descarga pesada).
    """
    # Bajada compacta — solo lo esencial, fuentes en expander al final.
    st.markdown(
        '<div style="font-size:0.78rem; color:#8899aa; margin-bottom:0.2rem;">'
        '<b style="color:#c0ccd8;">VOLCAT</b> · SSEC/CIMSS · Pavolonis 2013 '
        '(optimal estimation 3-canal IR) · cadencia 10 min ABI + refuerzo MODIS/VIIRS'
        '</div>',
        unsafe_allow_html=True,
    )

    # Cheat-sheet con los 4 productos antes del selector — ayuda a elegir.
    st.markdown(_volcat_cheatsheet_html(), unsafe_allow_html=True)

    # ── Modo de seleccion: por VOLCAN puntual o por ZONA regional ──
    # VOLCAT tiene sectores regionales (Chile_North/Central/South_2km) que
    # cubren zonas completas. Antes solo se accedia eligiendo un volcan;
    # ahora ofrecemos el acceso directo por zona tambien.
    from src.fetch.volcat_api import ZONE_TO_SECTOR
    modo_sel = st.radio(
        "Ver por", ["Volcán", "Zona"], horizontal=True,
        index=1,  # default = Zona (la zona default es Norte) al abrir la vista
        key=f"volcat_height_modo_{key_suffix}",
        help="Volcán = sector dedicado del volcán elegido. "
             "Zona = sector regional completo (Norte/Centro/Sur).",
    )

    # TODOS los volcanes monitoreados (RNVV), no solo los con sector dedicado.
    # Los que no tienen sector propio resuelven al regional por zona via
    # resolve_volcat_sector. Antes el filtro `v.name in VOLCANO_TO_SECTOR`
    # dejaba afuera ~la mitad (nombres con/sin tilde no matcheaban + muchos sin
    # mapeo: Tupungatito, San Jose, Antuco, Sollipulli, Osorno...). (jun 2026)
    _cat = [v for v in CATALOG if v.zone != "test"]
    priority_names = [v.name for v in _cat if v.name in PRIORITY_VOLCANOES]
    other_names    = [v.name for v in _cat if v.name not in PRIORITY_VOLCANOES]
    volc_options   = [f"★ {n}" for n in priority_names] + other_names

    cv1, cv2 = st.columns([1.5, 1.5])
    with cv1:
        if modo_sel == "Zona":
            zona_sel = st.selectbox(
                "Zona volcánica", list(ZONE_TO_SECTOR.keys()), index=0,
                key=f"volcat_height_zona_{key_suffix}",
                help="Sector regional VOLCAT. 'Sur' cubre tambien la zona austral.",
            )
            volc_name_h = f"Zona {zona_sel}"
        else:
            sel_raw = st.selectbox(
                "Volcán", volc_options, index=0,
                key=f"volcat_height_volcano_{key_suffix}",
                help="★ = volcán prioritario (con sector dedicado en VOLCAT)",
            )
            volc_name_h = sel_raw.replace("★ ", "")
            # Control de acercamiento: radio del encuadre alrededor del volcan.
            # Default ±1° (~111 km) — bastante cerca; bajable a ±0.5° (~55 km)
            # para maximo detalle. (jun 2026, pedido OVDAS "aun mas zoom")
            zoom_pad = st.select_slider(
                "Acercamiento",
                options=[0.5, 0.75, 1.0, 1.5, 2.0, 3.0], value=1.0,
                format_func=lambda d: f"±{d:g}° (~{int(round(d * 111))} km)",
                key=f"volcat_height_zoom_{key_suffix}",
                help="Radio del encuadre alrededor del volcán. Más cerca = más "
                     "detalle, pero el producto VOLCAT es ~2 km/px en los "
                     "sectores regionales (se pixela al acercar mucho).",
            )
    with cv2:
        # Tooltip ampliado en el selectbox + descripción inline debajo.
        help_text = "\n".join(
            f"• {p['icon']} {p['label_es']}: {p['short']}"
            for p in VOLCAT_PRODUCTS.values()
        )
        prod_h = st.selectbox(
            "Producto VOLCAT",
            list(VOLCAT_PRODUCTS.keys()),
            format_func=lambda k: VOLCAT_PRODUCTS[k]["label_es"],
            index=0, key=f"volcat_height_product_{key_suffix}",
            help=help_text,
        )

    # Descripción visible del producto seleccionado (inline, destacado).
    sel_meta = VOLCAT_PRODUCTS[prod_h]
    st.markdown(
        f'<div style="background:rgba(74,158,255,0.08); '
        f'border-left:3px solid #4a9eff; padding:0.4rem 0.7rem; '
        f'border-radius:0 6px 6px 0; margin:0.3rem 0; '
        f'font-size:0.78rem; line-height:1.45;">'
        f'<span style="color:#4a9eff; font-weight:700;">'
        f'{sel_meta["icon"]} {sel_meta["label_es"]}</span> '
        f'<span style="color:#aabbc8;">— {sel_meta["short"]}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # view_bounds: en modo Volcán encuadramos CERCA del volcán elegido (±_PAD)
    # en vez del sector regional gigante. En modo Zona = sector entero (None).
    view_bounds = None
    if modo_sel == "Zona":
        # Sector regional directo — no pasa por resolve_volcat_sector.
        sector, instr = ZONE_TO_SECTOR[zona_sel]
    else:
        v_obj = get_volcano(volc_name_h)
        if v_obj is None:
            st.error(f"No encontré '{volc_name_h}' en el catálogo RNVV.")
            return
        # Sector dedicado si existe (match exacto sin tildes), si no el regional
        # por zona -> TODOS los volcanes resuelven a algo (nunca None).
        sector, instr = resolve_volcat_sector(v_obj)
        _PAD = float(zoom_pad)   # radio del encuadre, elegido en el slider
        view_bounds = {
            "lat_min": v_obj.lat - _PAD, "lat_max": v_obj.lat + _PAD,
            "lon_min": v_obj.lon - _PAD, "lon_max": v_obj.lon + _PAD,
        }
    with st.spinner(
        f"Consultando VOLCAT para {volc_name_h} (sector {sector}, {prod_h})..."
    ):
        meta = _volcat_latest_cached(sector, instr, prod_h)

    if meta is None:
        st.warning(
            f"VOLCAT no devolvió frames recientes para sector "
            f"**{sector}** producto **{prod_h}** instr **{instr}**. "
            "Posibles causas: scan ABI atrasado, sector con cobertura "
            "intermitente, o el producto solo está disponible cuando "
            "VOLCAT detecta una pluma activa (Ash_Loading/Reff suelen "
            "ser nulos sin erupción). Probá Ash_Probability como "
            "indicador siempre disponible."
        )
        return

    ts_h = _parse_volcat_dt(meta.get("datetime"))
    kh1, kh2, kh3 = st.columns(3)
    with kh1:
        kpi_card(volc_name_h, "Zona" if modo_sel == "Zona" else "Volcán")
    with kh2:
        kpi_card(sector.replace("_", " "), "Sector VOLCAT")
    with kh3:
        short_ts = meta.get("datetime", "—").split("_")[-1].replace("-", ":")
        kpi_card(short_ts[:5] + " UTC" if len(short_ts) >= 5 else "—",
                 "Hora del scan")

    def _render_map_block():
        # Georef + NUESTROS volcanes monitoreados (RNVV) + frontera, igual que
        # las vistas RGB / zonas. `_volcat_map_only` recorta el mapa (saca
        # titulo y colorbar quemados de SSEC) y da los lat/lon bounds. Si falla
        # (sin coords o sin grid latlon detectable) -> fallback a imagen plana.
        img_bytes = _volcat_image_bytes(meta["image_url"])
        try:
            geo = _volcat_map_only(meta["image_url"], meta.get("latlon_url"),
                                   meta.get("coords") or {})
        except Exception:
            logger.warning("VOLCAT georef fallo, uso imagen plana", exc_info=True)
            geo = None
        if geo and geo.get("png"):
            st.plotly_chart(
                _fig_volcat_height_geo(geo["png"], geo["bounds"],
                                       f"{sel_meta['label_es']} · {ts_h}",
                                       view_bounds=view_bounds),
                width='stretch',
                config={"displayModeBar": False, "responsive": True},
                key=f"volcat_height_geo_{sector}_{prod_h}_{key_suffix}",
            )
            st.caption("▲ cyan = volcanes monitoreados (RNVV) · línea = "
                       "frontera Chile-Argentina · producto VOLCAT "
                       "georreferenciado sobre el sector.")
        elif img_bytes:
            st.image(img_bytes, caption=f"{sel_meta['label_es']} · {ts_h}",
                     width='stretch')
        if img_bytes:
            st.download_button(
                f"⬇ Descargar PNG VOLCAT ({len(img_bytes)//1024} KB)",
                data=img_bytes,
                file_name=(
                    f"volcat_{prod_h.lower()}_{sector.lower()}_"
                    f"{(meta.get('datetime') or 'latest').replace(':', '-')}.png"
                ),
                mime="image/png",
                key=f"dl_volcat_height_{prod_h}_{sector}_{key_suffix}",
                width='stretch',
            )
        elif not (geo and geo.get("png")):
            st.error("No se pudo descargar la imagen.")
            st.caption(f"URL: {meta.get('image_url', '?')}")

    # Colorbar VERTICAL dividido en dos, FLANQUEANDO el mapa (BT [K] a la izq,
    # escala del producto a la der) como el Modo Sala -> mucho mas grande y
    # legible que la tira horizontal chica. (jun 2026, pedido OVDAS "color bar
    # vertical y dividida en dos"). Fallback a la tira horizontal si el split
    # no esta disponible para este producto.
    bt_leg, ht_leg = _volcat_colorbar_split_vertical(meta["image_url"])
    if bt_leg and ht_leg:
        col_bt, col_im, col_ht = st.columns([0.62, 6, 0.72],
                                            vertical_alignment="center")
        with col_bt:
            st.image(bt_leg, width='stretch')   # 10.3 µm BT [K]
        with col_im:
            _render_map_block()
        with col_ht:
            st.image(ht_leg, width='stretch')   # escala del producto (km/% /…)
    else:
        col_im, col_lg = st.columns([4, 1.4])
        with col_im:
            _render_map_block()
        with col_lg:
            st.markdown("<b style='font-size:0.78rem; color:#8899aa;'>"
                        "Colorbar</b>", unsafe_allow_html=True)
            leg_bytes = _volcat_colorbar_strip(meta["image_url"])
            if leg_bytes:
                st.image(leg_bytes, width='stretch')
            else:
                st.caption("(sin leyenda)")

    # ── Altura propia INDICATIVA (ACHA NOAA ∩ ceniza). Solo en modo Volcán
    # (es el tope de UN volcán, necesita lat/lon puntual). Va DEBAJO del VOLCAT
    # primario, claramente diferenciada. ──
    if modo_sel == "Volcán":
        st.markdown("---")
        _render_acha_indicative_section(v_obj, float(zoom_pad), key_suffix)

    # Panel interpretativo: usa el campo "long" de cada producto.
    with st.expander(
        f"Cómo leer {sel_meta['label_es']} (detalle técnico)", expanded=False,
    ):
        st.markdown(sel_meta["long"])

    st.markdown(
        f'<div style="font-size:0.72rem; color:#445566; margin-top:0.7rem;">'
        f'Ver en el portal SSEC: '
        f'<a href="https://volcano.ssec.wisc.edu/imagery/view/'
        f'#sector:{sector}::instr:{instr}::sat:all'
        f'::image_type:{prod_h}::endtime:latest::daterange:2880" '
        f'target="_blank" style="color:#667788;">abrir en VOLCAT viewer →</a>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _parse_timestamp(ts_str):
    """Convertir timestamp SSEC (YYYYMMDD.HHMMSS) a legible con hora local."""
    if not ts_str:
        return "—"
    try:
        from datetime import datetime, timezone
        date_part = ts_str.split(".")[0]
        time_part = ts_str.split(".")[1] if "." in ts_str else "000000"
        utc_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]} UTC"
        # Agregar hora local Chile
        dt = datetime(
            int(date_part[:4]), int(date_part[4:6]), int(date_part[6:8]),
            int(time_part[:2]), int(time_part[2:4]),
            tzinfo=timezone.utc,
        )
        ch_str = fmt_chile(dt)
        return f"{utc_str}  ({ch_str} Chile)"
    except Exception:
        return ts_str


def _ssec_png_download(img_rgba, filename: str, button_label: str, key: str):
    """Boton de descarga para imagen SSEC (RGBA -> PNG con alpha aplicado)."""
    if img_rgba is None:
        return
    import io as _io
    from PIL import Image as _PIL
    rgb = img_rgba[:, :, :3].copy()
    alpha = img_rgba[:, :, 3:4].astype(np.float32) / 255.0
    rgb = (rgb.astype(np.float32) * alpha).astype(np.uint8)
    buf = _io.BytesIO()
    _PIL.fromarray(rgb).save(buf, format="PNG", optimize=True)
    png = buf.getvalue()
    size_kb = len(png) / 1024
    size_str = f"{size_kb/1024:.1f} MB" if size_kb >= 1024 else f"{size_kb:.0f} KB"
    st.download_button(
        f"⬇ {button_label} ({size_str})",
        data=png, file_name=filename, mime="image/png",
        key=key, width='stretch',
    )


def _render_vaa_block():
    """Avisos VAA (Volcanic Ash Advisories) globales — GeoJSON liviano."""
    vaa = _fetch_vaa_cached()
    feats = vaa.get("features", []) if vaa else []
    if feats:
        st.markdown(
            f'<div class="status-banner warn">'
            f'<b>&#9888; {len(feats)} Volcanic Ash Advisory(ies) activos globalmente</b>'
            f'</div>',
            unsafe_allow_html=True,
        )
        for feat in feats:
            props = feat.get("properties", {})
            name = props.get("name", props.get("title", "Sin nombre"))
            desc = props.get("description", "")
            st.markdown(
                f'<div class="volcano-card"><h3>{name}</h3>'
                f'<div class="detail">{desc}</div></div>',
                unsafe_allow_html=True,
            )
    else:
        info_panel(
            "<b>Sin Volcanic Ash Advisories activos.</b><br>"
            "Los VAA son emitidos por los VAACs (Volcanic Ash Advisory Centers) "
            "cuando se detecta ceniza volcanica que puede afectar la aviacion. "
            "La ausencia de VAA indica condiciones normales."
        )


def _render_ssec_rgb_block():
    """Ash/SO2 RGB de SSEC (RealEarth) — REDUNDANTE con Modo Guardia.

    Se renderiza colapsado como respaldo. La descarga es pesada (Full Disk),
    por eso detras de un boton explicito.
    """
    st.caption(
        "Estos Ash/SO2 RGB vienen de **SSEC RealEarth** y son equivalentes a "
        "los de **Modo Guardia** (que usan RAMMB/CIRA) — misma idea, otro "
        "proveedor. Utiles solo como respaldo si RAMMB no responde."
    )
    c1, c2 = st.columns([1.5, 1])
    with c1:
        zone_key = st.selectbox("Region", list(ZONE_OPTIONS.keys()), index=0,
                                key="volcat_zone")
    with c2:
        st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
        fetch = st.button("Obtener imagenes SSEC", type="primary", width='stretch')
    bounds = ZONE_OPTIONS[zone_key]

    if not fetch:
        ash_ts = get_latest_time("ash_rgb")
        so2_ts = get_latest_time("so2_rgb")
        st.markdown(
            f'<div class="legend-container">'
            f'<div class="legend-title">Ultima imagen disponible</div>'
            f'<div style="font-size:0.82rem; color:#99aabb; line-height:2;">'
            f'<b>Ash RGB:</b> {_parse_timestamp(ash_ts)}<br>'
            f'<b>SO2 RGB:</b> {_parse_timestamp(so2_ts)}'
            f'</div></div>',
            unsafe_allow_html=True,
        )
        st.info("Apreta **Obtener imagenes SSEC** para descargar los RGB Full Disk (~10s).")
        return

    with st.spinner("Descargando productos SSEC (Ash RGB + SO2 RGB)..."):
        ash_ts = _get_latest_time_cached("ash_rgb")
        so2_ts = _get_latest_time_cached("so2_rgb")
        ash_img = _fetch_image_cached("ash_rgb", bounds, ash_ts)
        so2_img = _fetch_image_cached("so2_rgb", bounds, so2_ts)

    products_ok = sum(1 for x in [ash_img, so2_img] if x is not None)
    ts_display = _parse_timestamp(ash_ts)
    st.markdown(
        f'<div class="status-banner ok">'
        f'<b>&#10003; {products_ok}/2 productos descargados</b>'
        f'<span style="color:#556677; font-size:0.78rem;">{ts_display}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["Ash RGB (SSEC)", "SO2 RGB (SSEC)"])
    with tab1:
        col_img, col_leg = st.columns([5, 1.2])
        with col_img:
            if ash_img is not None:
                fig = _fig_ssec_image(
                    ash_img, bounds,
                    f"Ash RGB — SSEC/CIMSS GOES-19 ({ts_display})", CATALOG,
                )
                st.plotly_chart(fig, width='stretch')
                _ssec_png_download(
                    ash_img, filename=f"volcat_ssec_ash_rgb_{ash_ts or 'latest'}.png",
                    button_label="Descargar Ash RGB SSEC (PNG)", key="dl_volcat_ash",
                )
            else:
                st.error("No se pudo descargar la imagen Ash RGB de SSEC")
        with col_leg:
            ash_legend()
    with tab2:
        col_img2, col_leg2 = st.columns([5, 1.2])
        with col_img2:
            if so2_img is not None:
                fig = _fig_ssec_image(
                    so2_img, bounds,
                    f"SO2 RGB — SSEC/CIMSS GOES-19 ({_parse_timestamp(so2_ts)})", CATALOG,
                )
                st.plotly_chart(fig, width='stretch')
                _ssec_png_download(
                    so2_img, filename=f"volcat_ssec_so2_rgb_{so2_ts or 'latest'}.png",
                    button_label="Descargar SO2 RGB SSEC (PNG)", key="dl_volcat_so2",
                )
            else:
                st.error("No se pudo descargar la imagen SO2 RGB de SSEC")
        with col_leg2:
            ash_so2_legend()


def render():
    from dashboard.manuals import render_manual
    render_manual("volcat")
    header(
        "VOLCAT — Altura de pluma (SSEC/CIMSS)",
        "Caracterizacion cuantitativa de pluma via algoritmo Pavolonis 2013 &middot; GOES-19",
    )

    refresh_info_badge(context="volcat")

    # ── PROTAGONISTA: altura de pluma VOLCAT. Es lo UNICO exclusivo de
    # esta pagina (altura km / carga g/m² / probabilidad / radio µm que
    # ningun otro modulo calcula). Va ARRIBA, disponible siempre, sin
    # botones pesados. (reordenado mayo 2026 — antes estaba al final y lo
    # primero era el boton de RGB redundantes). ──
    _render_height_section(key_suffix="main")

    # ── Complemento opcional y colapsado: Ash/SO2 RGB de SSEC (redundantes
    # con Modo Guardia, otro proveedor) + Avisos VAA de aviacion. ──
    st.markdown("---")
    with st.expander(
        "🛰 Ash / SO2 RGB de SSEC + Avisos VAA (respaldo opcional)",
        expanded=False,
    ):
        _render_ssec_rgb_block()
        st.markdown("---")
        st.markdown("**Avisos de ceniza volcánica (VAA) — global**")
        _render_vaa_block()
