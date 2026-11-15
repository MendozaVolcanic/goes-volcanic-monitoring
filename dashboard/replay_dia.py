"""Replay de un dia: los 4 productos del mismo scan y reproduccion continua.

Para que sirve (15-11-2026, pedido de Nicolas): comparar contra una anomalia
vista en otro visor exige ver GeoColor, Ash RGB, SO2 y VOLCAT del MISMO scan
lado a lado, y pasar el dia entero de corrido sin apretar ▶ scan por scan.

Como lo hace: una sola figura plotly 2x2, en km alrededor del crater (la
misma conversion de `dashboard/regla.py` que la grilla de volcan), con un
frame por scan. Play, pausa y el deslizador corren en el navegador: una vez
bajado el dia no hay ida y vuelta al servidor por cuadro.

FICHA SDA (Nivel 1): composicion de imagenes que se muestran al operador
  Que decide: NADA. Ordena en el tiempo imagenes de RAMMB/CIRA (GeoColor,
    Ash RGB, SO2) y de SSEC/CIMSS (VOLCAT) ya publicadas. No clasifica ni
    mide; la lectura (hay pluma, es ceniza o gas, que altura) es del geologo.
  Regla de honestidad: un producto sin imagen en un scan queda VACIO y dice
    por que (no publicado, no conservado, no respondio). Nunca se rellena con
    el scan vecino: un cuadro repetido muestra una pluma quieta que nadie vio.
  Trazabilidad: dashboard/views/replay_reciente.py (pantalla),
    tests/test_replay_dia.py.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import plotly.graph_objects as go

# Mismo orden que la grilla de volcan (`modo_guardia_volcan.GRID_PANELS`):
# GeoColor (hay columna?) -> Ash RGB (es ceniza?) -> SO2 (es gas?) -> VOLCAT
# (que altura?). Una prueba falla si se separan.
PANELES = ("geocolor", "eumetsat_ash", "jma_so2", "volcat")
PANELES_RAMMB = ("geocolor", "eumetsat_ash", "jma_so2")
ROTULOS = {
    "geocolor": "GeoColor",
    "eumetsat_ash": "Ash RGB",
    "jma_so2": "SO2 RGB",
    "volcat": "VOLCAT · altura",
}

_FONDO = "#0a0e14"
_TXT = "#e0e0e0"
_GRIS = "#9aa8b8"
# La barra de color de VOLCAT ocupa el borde izquierdo de su panel: la barra
# de escala de ese panel parte mas a la derecha (igual que en la grilla).
_ANCHO_BARRA_VOLCAT = 0.10


# ── Linea de tiempo ──────────────────────────────────────────────────
# El Full Disk ABI escanea cada 10 min. RAMMB rotula el scan por su inicio
# (15:30:21) y VOLCAT por su hora de cuadro (15:30:30): los dos caen en el
# mismo "slot" de 10 min, que es la clave con la que se emparejan.

def slot_de_ts(ts: str) -> str:
    """'20261114153021' (RAMMB) -> '202611141530'."""
    return ts[:11] + "0"


def slot_de_dt(dt: datetime) -> str:
    """datetime UTC -> slot de 10 min ('YYYYMMDDHHM0')."""
    return f"{dt:%Y%m%d%H}{dt.minute // 10}0"


def dt_de_slot(slot: str) -> datetime:
    return datetime.strptime(slot, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)


def linea_de_tiempo(listas: dict[str, list[str]]) -> list[str]:
    """Union ordenada de los slots que tiene AL MENOS un producto RAMMB.

    Si un producto falta en un scan (RAMMB publico 135 scans de SO2 y 144 de
    Ash el 14-11-2026), el scan igual entra: los otros si tienen imagen.
    """
    return sorted({slot_de_ts(t) for ts in listas.values() for t in ts})


def emparejar(listas: dict[str, list[str]],
              slots: list[str]) -> dict[str, dict[str, str | None]]:
    """slot -> {producto: ts de ESE slot, o None}. Sin vecino de relleno."""
    por_prod = {p: {slot_de_ts(t): t for t in ts} for p, ts in listas.items()}
    return {s: {p: por_prod[p].get(s) for p in listas} for s in slots}


def volcat_por_slot(frames: list[dict], slots: list[str]) -> dict:
    """slot -> cuadro VOLCAT de ese scan, o None si SSEC no lo publico."""
    por_slot = {slot_de_dt(f["dt"]): f for f in frames if f.get("dt")}
    return {s: por_slot.get(s) for s in slots}


# ── Figura ───────────────────────────────────────────────────────────

def _a_rgb(img) -> np.ndarray:
    a = np.asarray(img)
    if a.ndim == 2:
        a = np.stack([a] * 3, axis=-1)
    return a[..., :3].astype(np.uint8)


def _url(img) -> str:
    # Lazy import (gotcha Streamlit Cloud, ver CLAUDE.md).
    from dashboard.map_helpers import array_to_data_url
    return array_to_data_url(_a_rgb(img))


def _eje(i: int) -> tuple[str, str]:
    """Panel i (1..4) -> ('x', 'y'), ('x2', 'y2'), ..."""
    s = "" if i == 1 else str(i)
    return f"x{s}", f"y{s}"


def rotulo_slot(slot: str) -> str:
    """'14-11 12:40 Chile · 15:40 UTC' (manda la hora de Chile)."""
    from dashboard.utils import utc_to_chile
    dt = dt_de_slot(slot)
    return f"{utc_to_chile(dt):%d-%m %H:%M} Chile · {dt:%H:%M} UTC"


def _hora_chile(slot: str) -> str:
    from dashboard.utils import utc_to_chile
    return f"{utc_to_chile(dt_de_slot(slot)):%H:%M}"


def figura_dia(cuadros: list[dict], lat0: float, lon0: float, bounds: dict,
               ms_por_cuadro: int = 250, regla: bool = False,
               alto: int = 820, titulo: str = "",
               barra_volcat=None) -> go.Figure:
    """Figura 2x2 en km con un frame por scan.

    `cuadros`: lista de {"slot", "imgs": {panel: array|PIL|None},
    "motivos": {panel: texto}}; `motivos` dice por que falta una imagen y se
    escribe sobre el panel vacio. Con un solo cuadro no hay animacion (es el
    modo cuadro a cuadro); con varios hay Play/Pausa y deslizador.

    `barra_volcat`: imagen de la escala de altura de VOLCAT. Va fija en el
    borde izquierdo de su panel: sin ella los colores no se pueden leer.
    """
    from plotly.subplots import make_subplots

    from dashboard.regla import a_km, activar_regla, agregar_barra_escala
    from dashboard.style import volcano_marker

    x_min, y_max = a_km(bounds["lat_max"], bounds["lon_min"], lat0, lon0)
    x_max, y_min = a_km(bounds["lat_min"], bounds["lon_max"], lat0, lon0)

    fig = make_subplots(rows=2, cols=2, horizontal_spacing=0.015,
                        vertical_spacing=0.035)
    for i, pid in enumerate(PANELES, start=1):
        xr, yr = _eje(i)
        fig.add_trace(go.Scatter(
            x=[0.0], y=[0.0], mode="markers", marker=volcano_marker("zone"),
            customdata=[[lat0, lon0]],
            hovertemplate=("Cráter<br>%{customdata[0]:.3f}, "
                           "%{customdata[1]:.3f}<extra></extra>"),
            showlegend=False,
        ), row=(i - 1) // 2 + 1, col=(i - 1) % 2 + 1)
        sufijo = "" if i == 1 else str(i)
        # constrain="domain" en los dos ejes: sin eso plotly ENSANCHA el rango
        # para cumplir el aspecto 1:1 (ver _render_product, audit 2026-08-30).
        fig.layout[f"xaxis{sufijo}"].update(
            range=[x_min, x_max], visible=False, showgrid=False,
            constrain="domain")
        fig.layout[f"yaxis{sufijo}"].update(
            range=[y_min, y_max], visible=False, showgrid=False,
            constrain="domain", scaleanchor=xr, scaleratio=1)
        x_frac = 0.14 if pid == "volcat" else 0.05
        agregar_barra_escala(fig, (x_min, x_max), (y_min, y_max),
                             x_frac=x_frac, ejes=(xr, yr))

    # Lo fijo de cada cuadro: rotulos de las barras de escala y la escala de
    # VOLCAT. Un frame que trae `annotations` o `images` REEMPLAZA la lista
    # entera, asi que cada frame los repite; si no, al dar Play la barra
    # quedaria sin numero y VOLCAT sin escala.
    anot_fijas = list(fig.layout.annotations)
    imgs_fijas = []
    if barra_volcat is not None:
        iv = PANELES.index("volcat") + 1
        xr, yr = _eje(iv)
        imgs_fijas.append(go.layout.Image(
            source=_url(barra_volcat), xref=f"{xr} domain",
            yref=f"{yr} domain", x=0, y=1, sizex=_ANCHO_BARRA_VOLCAT,
            sizey=1, xanchor="left", yanchor="top", sizing="contain",
            layer="above"))

    def _capas(c: dict):
        imgs, anots = list(imgs_fijas), list(anot_fijas)
        for i, pid in enumerate(PANELES, start=1):
            xr, yr = _eje(i)
            img = c["imgs"].get(pid)
            motivo = c.get("motivos", {}).get(pid)
            if img is not None:
                imgs.append(go.layout.Image(
                    source=_url(img), xref=xr, yref=yr, x=x_min, y=y_max,
                    sizex=x_max - x_min, sizey=y_max - y_min,
                    sizing="stretch", layer="below"))
            titulo_p = f"<b>{ROTULOS[pid]}</b>"
            if motivo and img is not None:
                titulo_p += f" · {motivo}"
            anots.append(go.layout.Annotation(
                text=titulo_p, xref=f"{xr} domain", yref=f"{yr} domain",
                x=0.99, y=0.99, xanchor="right", yanchor="top",
                showarrow=False, font=dict(color=_TXT, size=12),
                bgcolor="rgba(10,14,20,0.7)", borderpad=3))
            if img is None:
                anots.append(go.layout.Annotation(
                    text=f"Sin imagen<br>{motivo or 'no disponible'}",
                    xref=f"{xr} domain", yref=f"{yr} domain", x=0.5, y=0.5,
                    showarrow=False, font=dict(color=_GRIS, size=13)))
        anots.append(go.layout.Annotation(
            text=f"<b>{titulo}{' · ' if titulo else ''}"
                 f"{rotulo_slot(c['slot'])}</b>",
            xref="paper", yref="paper", x=0.0, y=1.0, xanchor="left",
            yanchor="bottom", showarrow=False,
            font=dict(color=_TXT, size=14)))
        return imgs, anots

    imgs0, anots0 = _capas(cuadros[0])
    fig.update_layout(
        images=imgs0, annotations=anots0, height=alto,
        margin=dict(l=0, r=0, t=30, b=70 if len(cuadros) > 1 else 0),
        paper_bgcolor=_FONDO, plot_bgcolor=_FONDO, showlegend=False,
    )

    if len(cuadros) > 1:
        frames = []
        for c in cuadros:
            imgs, anots = _capas(c)
            frames.append(go.Frame(name=c["slot"],
                                   layout=go.Layout(images=imgs,
                                                    annotations=anots)))
        fig.frames = frames
        # redraw=True: lo que cambia entre cuadros es layout.images, y plotly
        # no lo repinta sin redibujar.
        play = dict(frame=dict(duration=int(ms_por_cuadro), redraw=True),
                    fromcurrent=True, transition=dict(duration=0),
                    mode="immediate")
        pausa = dict(frame=dict(duration=0, redraw=False),
                     transition=dict(duration=0), mode="immediate")
        fig.update_layout(
            updatemenus=[dict(
                type="buttons", direction="left", showactive=False,
                x=0.0, y=0.0, xanchor="left", yanchor="top",
                pad=dict(t=8, r=8), bgcolor="#1f2a36", bordercolor=_GRIS,
                font=dict(color=_TXT, size=13),
                buttons=[dict(label="▶ Reproducir", method="animate",
                              args=[None, play]),
                         dict(label="⏸ Pausa", method="animate",
                              args=[[None], pausa])],
            )],
            # Rotulo solo en las horas en punto: 144 rotulos en una linea se
            # pisan. La hora exacta del cuadro va arriba de la figura.
            sliders=[dict(
                active=0, x=0.16, len=0.84, y=0.0, yanchor="top",
                pad=dict(t=8), currentvalue=dict(visible=False),
                font=dict(color=_GRIS, size=10), tickcolor=_GRIS,
                steps=[dict(
                    method="animate", label=(_hora_chile(c["slot"])
                                             if c["slot"].endswith("00")
                                             else ""),
                    args=[[c["slot"]], dict(mode="immediate",
                                            frame=dict(duration=0,
                                                       redraw=True),
                                            transition=dict(duration=0))])
                    for c in cuadros],
            )],
        )

    if regla:
        # Bajo ~100 km de ancho un pixel vale menos de 1 km: un decimal.
        activar_regla(fig, decimales=1 if (x_max - x_min) < 222 else 0)
    return fig
