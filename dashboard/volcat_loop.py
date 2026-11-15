"""Loop animado de VOLCAT: cuadros anotados, GIF y MP4.

Por que existe: el ultimo cuadro de VOLCAT dice a que altura esta la ceniza
AHORA; el loop dice hacia donde va, si la columna crece o se corta, y si el
pulso fue uno o varios. Eso es lo que el geologo de turno necesita para
contar la evolucion de la pluma en un informe.

FICHA SDA (Nivel 1): visualizacion de un producto externo
  Que decide: NADA. Recorta y anota cuadros del producto VOLCAT de
    SSEC/CIMSS (Pavolonis 2013); no mide ni clasifica la pluma.
  Reglas de honestidad que este modulo sostiene:
    - Cada cuadro lleva su hora UTC y la hora de Chile sobreimpresas: un GIF
      se reenvia por correo y pierde todo contexto que no venga dentro.
    - Barra de escala en km y barra de color de la altura DENTRO del archivo.
    - Dice que sector VOLCAT usa y que un cuadro sin dibujo es lo normal
      (VOLCAT solo pinta cuando detecta ceniza).
    - No rellena: si SSEC no publico un cuadro, el siguiente lleva el aviso
      del salto en vez de repetir el anterior.
    - El mapa se escala con vecino mas cercano: la paleta de VOLCAT codifica
      altura por color, e interpolar mezcla colores que no estan en la escala.
  Trazabilidad: src/fetch/volcat_api.py::volcat_ventana (cuadros),
    dashboard/views/volcat_viewer.py::_render_volcat_loop (pantalla),
    tests/test_volcat_loop.py.

No importa Streamlit: es PIL puro, asi se prueba sin levantar la app.
"""

from __future__ import annotations

import io
import logging
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from dashboard.regla import km_por_grado_lat, km_por_grado_lon, largo_barra_km

logger = logging.getLogger(__name__)

# Fuera del sector SSEC no hay dato: gris azulado oscuro, distinto del negro
# que algunos productos usan como fondo.
FONDO_FUERA = (28, 32, 40)
_FONDO = (10, 14, 20)
_BLANCO = (255, 255, 255)
_GRIS_TXT = (200, 210, 222)
_AMARILLO = (255, 210, 63)

NOTA_VACIO = ("sin dibujo = VOLCAT no detecta ceniza en ese cuadro "
              "(normal, no es una falla)")


def _fuente(size: int):
    """TrueType con respaldo: DejaVu en Linux/HF, Arial en Windows."""
    for name in ("DejaVuSans-Bold.ttf", "arialbd.ttf", "arial.ttf",
                 "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _texto(draw, xy, s, font, fill=_BLANCO):
    """Texto con contorno negro: legible sobre nube blanca y sobre oceano."""
    draw.text(xy, s, font=font, fill=fill,
              stroke_width=max(2, getattr(font, "size", 12) // 9),
              stroke_fill=(0, 0, 0))


# ── Rotulos ───────────────────────────────────────────────────────────────

def rotulo_hora(dt: datetime) -> str:
    """'2026-11-15 13:10 UTC · 10:10 hora de Chile (UTC-3)'.

    El desfase va escrito en numeros y no como sigla: la base tz de IANA ya
    no trae CLT/CLST para Santiago y la sigla impresa saldria como '-03'.
    Si la fecha local es otra (noche en Chile, madrugada UTC) va la fecha.
    """
    from dashboard.utils import utc_to_chile
    local = utc_to_chile(dt)
    off = int(local.utcoffset().total_seconds() // 3600)
    hora_local = (local.strftime("%H:%M") if local.date() == dt.date()
                  else local.strftime("%Y-%m-%d %H:%M"))
    return (f"{dt.strftime('%Y-%m-%d %H:%M')} UTC · {hora_local} "
            f"hora de Chile (UTC{off:+d})")


def aviso_salto(dt_prev: datetime | None, dt: datetime,
                cadencia_min: float = 10) -> str | None:
    """Aviso para el cuadro que viene despues de un hueco, o None.

    Es la forma de mostrar el faltante sin rellenarlo: el loop salta, y el
    cuadro siguiente dice cuanto salto.
    """
    if dt_prev is None:
        return None
    minutos = (dt - dt_prev).total_seconds() / 60.0
    n = int(round(minutos / cadencia_min)) - 1
    if n < 1:
        return None
    cuadros = "falta 1 cuadro" if n == 1 else f"faltan {n} cuadros"
    return f"Salto de {minutos:.0f} min: {cuadros} antes de este"


def barra_escala(view: dict, ancho_px: int) -> tuple[int, float]:
    """(largo en km, largo en px) de la barra para un mapa de `ancho_px`.

    Mismo criterio de largo que la grilla del volcan (`regla.largo_barra_km`).
    El km por grado de longitud se toma en la latitud media del encuadre, que
    es donde el mapa (ya en proporcion de km) es exacto.
    """
    lat_m = (view["lat_min"] + view["lat_max"]) / 2.0
    ancho_km = (view["lon_max"] - view["lon_min"]) * km_por_grado_lon(lat_m)
    km = largo_barra_km(ancho_km)
    return km, km / ancho_km * ancho_px


# ── Recorte ───────────────────────────────────────────────────────────────

def recortar_encuadre(png: bytes, bounds: dict, view: dict) -> Image.Image | None:
    """Recorta el mapa del sector (lat/lon lineal) al encuadre del volcan.

    `bounds` son los de `_volcat_map_only`: los sectores CE ya vienen lineales
    y el PS (Chile_South) llega reproyectado, asi que la cuenta es la misma.
    Lo que cae fuera del sector se pinta FONDO_FUERA, nunca se estira.
    """
    try:
        base = Image.open(io.BytesIO(png)).convert("RGB")
    except Exception:
        logger.warning("loop VOLCAT: cuadro ilegible", exc_info=True)
        return None
    W, H = base.size
    sx = W / (bounds["lon_max"] - bounds["lon_min"])
    sy = H / (bounds["lat_max"] - bounds["lat_min"])
    left = round((view["lon_min"] - bounds["lon_min"]) * sx)
    top = round((bounds["lat_max"] - view["lat_max"]) * sy)
    w = max(1, round((view["lon_max"] - view["lon_min"]) * sx))
    h = max(1, round((view["lat_max"] - view["lat_min"]) * sy))
    out = Image.new("RGB", (w, h), FONDO_FUERA)
    out.paste(base, (-left, -top))
    return out


# ── Composicion de un cuadro ──────────────────────────────────────────────

def escalar_mapa(mapa: Image.Image, w: int, h: int) -> Image.Image:
    """Agranda el recorte con vecino mas cercano.

    Cada color de VOLCAT es un valor de la escala (altura, carga...). Un
    filtro suave mezclaria dos colores vecinos en uno intermedio que la
    barra leeria como una altura que el producto nunca dio. Se ven los
    pixeles de 2 km: es la resolucion real del dato.
    """
    return mapa.convert("RGB").resize((w, h), Image.NEAREST)


def _dibujar_frontera(draw, view, x0, y0, w, h):
    """Costa y limite con Argentina, con halo, como en los loops RAMMB."""
    try:
        from dashboard.map_helpers import _load_geo
        geo = _load_geo()
    except Exception:
        return

    def xy(lat, lon):
        return (x0 + (lon - view["lon_min"]) / (view["lon_max"] - view["lon_min"]) * w,
                y0 + (view["lat_max"] - lat) / (view["lat_max"] - view["lat_min"]) * h)

    ancho, fino = max(3, w // 260), max(1, w // 700)
    for pts in (geo.get("coast", []), geo.get("border", [])):
        for color, grosor in (((20, 24, 32), ancho), ((236, 240, 250), fino)):
            prev = None
            for p in pts:
                if not p or p[0] is None:
                    prev = None
                    continue
                cur = xy(p[0], p[1])
                if prev is not None:
                    draw.line([prev, cur], fill=color, width=grosor)
                prev = cur


def _se_tocan(a, b) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _dibujar_volcanes(draw, view, x0, y0, w, h, font, evitar=()):
    """Triangulos HUECOS del RNVV (mismo helper que el resto de los PNG) y
    nombres a la izquierda, porque la pluma suele irse al este.

    El triangulo se dibuja siempre; el NOMBRE se omite si cae encima de otro
    nombre o de un rectangulo de `evitar` (la barra de escala): dos textos
    encimados no se leen ninguno. Devuelve los rectangulos de los nombres.
    """
    from dashboard.map_helpers import draw_volcano_marker_pil
    from src.volcanos import CATALOG
    vis = [v for v in CATALOG if v.zone != "test"
           and view["lat_min"] <= v.lat <= view["lat_max"]
           and view["lon_min"] <= v.lon <= view["lon_max"]]
    tri = max(6, w // 55)
    fs = getattr(font, "size", 12)
    rotulos = []
    lat_c = (view["lat_min"] + view["lat_max"]) / 2
    lon_c = (view["lon_min"] + view["lon_max"]) / 2
    # El del centro primero: es el volcan del loop y su nombre no se omite.
    for v in sorted(vis, key=lambda v: (v.lat - lat_c) ** 2 + (v.lon - lon_c) ** 2):
        x = x0 + (v.lon - view["lon_min"]) / (view["lon_max"] - view["lon_min"]) * w
        y = y0 + (view["lat_max"] - v.lat) / (view["lat_max"] - view["lat_min"]) * h
        draw_volcano_marker_pil(draw, x, y, size=tri)
        tw = draw.textlength(v.name, font=font)
        tx = x - tri - 6 - tw
        if tx < x0 + 4:
            tx = x + tri + 6
        rect = (tx - 2, y - fs * 0.8, tx + tw + 2, y + fs * 0.8)
        if any(_se_tocan(rect, r) for r in list(evitar) + rotulos):
            continue
        _texto(draw, (tx, y - fs * 0.6), v.name, font)
        rotulos.append(rect)
    return rotulos


def _geometria_barra(view, x0, y0, w, h, font):
    """Posicion de la barra de escala y su rectangulo (con rotulo), para
    dibujarla y para que los nombres de volcanes le hagan espacio."""
    km, largo = barra_escala(view, w)
    m = max(10, w // 30)
    bx0, by = x0 + m, y0 + h - m
    grosor = max(3, w // 160)
    fs = getattr(font, "size", 12)
    rect = (bx0 - 4, by - grosor * 2 - fs * 1.4, bx0 + largo + 4, by + grosor + 4)
    return {"km": km, "bx0": bx0, "bx1": bx0 + largo, "by": by,
            "grosor": grosor, "rect": rect}


def _dibujar_barra(draw, g, font):
    """Barra de escala blanca abajo a la izquierda, con halo oscuro."""
    bx0, bx1, by, grosor = g["bx0"], g["bx1"], g["by"], g["grosor"]
    draw.line([(bx0, by), (bx1, by)], fill=(10, 14, 20), width=grosor + 4)
    draw.line([(bx0, by), (bx1, by)], fill=_BLANCO, width=grosor)
    for xt in (bx0, bx1):
        draw.line([(xt, by - grosor * 2), (xt, by + grosor)], fill=_BLANCO,
                  width=max(2, grosor // 2))
    s = f"{g['km']} km"
    fs = getattr(font, "size", 12)
    _texto(draw, ((bx0 + bx1) / 2 - draw.textlength(s, font=font) / 2,
                  by - grosor * 2 - fs * 1.25), s, font)


def componer_cuadro(mapa: Image.Image, view: dict, centro: tuple[float, float],
                    dt: datetime, titulo: str, sector_txt: str,
                    barra_color: Image.Image | None = None,
                    aviso: str | None = None,
                    alto_mapa: int = 640) -> tuple[Image.Image, dict]:
    """Un cuadro del loop listo para GIF/MP4.

    Disposicion: banda superior (volcan, producto, sector) · mapa con
    frontera, volcanes y barra de escala · barra de color de la altura AL
    COSTADO del mapa (encima taparia la cordillera, que es justo donde nace
    la pluma) · banda inferior (hora UTC y de Chile, nota de vacio, aviso de
    salto).

    El mapa va en proporcion de km (ancho = alto * km_lon / km_lat en el
    crater): asi un km horizontal mide lo mismo que uno vertical y la barra
    de escala vale en las dos direcciones.

    Devuelve (imagen, geo) con `geo` = {"mapa_xy", "mapa_px", "textos",
    "rotulos", "barra_rect"}.
    """
    lat0 = centro[0]
    alto_km = (view["lat_max"] - view["lat_min"]) * km_por_grado_lat(lat0)
    ancho_km = (view["lon_max"] - view["lon_min"]) * km_por_grado_lon(lat0)
    h = int(alto_mapa)
    w = int(round(h * ancho_km / alto_km))
    mapa = escalar_mapa(mapa, w, h)

    fs = max(14, h // 36)
    f_tit, f_txt, f_peq = _fuente(int(fs * 1.15)), _fuente(fs), _fuente(int(fs * 0.85))
    pad = max(6, fs // 2)
    linea = int(fs * 1.45)
    banda_sup = pad * 2 + linea * 2
    # Siempre 3 lineas, haya aviso o no: el GIF toma el tamano del primer
    # cuadro y uno mas alto saldria cortado justo en el renglon del aviso.
    banda_inf = pad * 2 + linea * 3

    barra = None
    if barra_color is not None:
        bw = max(1, round(barra_color.width * h / barra_color.height))
        barra = barra_color.convert("RGB").resize((bw, h), Image.LANCZOS)
    ancho_total = w + (barra.width if barra else 0)

    # Frontera, volcanes y barra se dibujan sobre el MAPA solo y despues se
    # pega: asi lo que sigue de largo (la frontera cruza el encuadre entero)
    # queda recortado al borde y no tacha la hora de la banda de abajo.
    dm = ImageDraw.Draw(mapa)
    _dibujar_frontera(dm, view, 0, 0, w, h)
    gbarra = _geometria_barra(view, 0, 0, w, h, f_peq)
    rotulos = _dibujar_volcanes(dm, view, 0, 0, w, h, f_peq,
                                evitar=[gbarra["rect"]])
    _dibujar_barra(dm, gbarra, f_peq)

    img = Image.new("RGB", (ancho_total, banda_sup + h + banda_inf), _FONDO)
    x0, y0 = 0, banda_sup
    img.paste(mapa, (x0, y0))
    if barra:
        img.paste(barra, (x0 + w, y0))
    draw = ImageDraw.Draw(img)

    hora = rotulo_hora(dt)
    sector_linea = f"Sector VOLCAT {sector_txt}"
    marca = "VOLCAT SSEC/CIMSS · GOES-19"
    textos = [titulo, sector_linea, hora, NOTA_VACIO] + ([aviso] if aviso else [])

    _texto(draw, (pad, pad), titulo, f_tit)
    _texto(draw, (pad, pad + linea), sector_linea, f_peq, fill=_GRIS_TXT)
    mw = draw.textlength(marca, font=f_peq)
    if mw < ancho_total - draw.textlength(titulo, font=f_tit) - 3 * pad:
        _texto(draw, (ancho_total - pad - mw, pad), marca, f_peq, fill=_GRIS_TXT)
    yb = banda_sup + h + pad
    _texto(draw, (pad, yb), hora, f_txt)
    _texto(draw, (pad, yb + linea), NOTA_VACIO, f_peq, fill=_GRIS_TXT)
    if aviso:
        _texto(draw, (pad, yb + 2 * linea), aviso, f_txt, fill=_AMARILLO)

    # rotulos y barra_rect van en coordenadas del mapa (origen arriba-izq).
    return img, {"mapa_xy": (x0, y0), "mapa_px": (w, h), "textos": textos,
                 "rotulos": rotulos, "barra_rect": gbarra["rect"]}


# ── Salidas ───────────────────────────────────────────────────────────────

def armar_gif(cuadros: list[Image.Image], ms_por_cuadro: int = 500) -> bytes:
    """GIF en loop infinito con exactamente los cuadros recibidos."""
    if not cuadros:
        return b""
    buf = io.BytesIO()
    cuadros[0].save(buf, format="GIF", save_all=True,
                    append_images=cuadros[1:], duration=ms_por_cuadro,
                    loop=0, optimize=True, disposal=2)
    return buf.getvalue()


def armar_mp4(cuadros: list[Image.Image], fps: float = 3.0) -> bytes:
    """MP4 H.264 yuv420p (lo abre PowerPoint, el navegador y el celular).

    H.264 exige lados pares: se rellena con el fondo, no se reescala, para
    no tocar los pixeles del producto.
    """
    if not cuadros:
        return b""
    try:
        import imageio.v2 as iio
        import numpy as np
    except Exception:
        logger.error("imageio no disponible para MP4", exc_info=True)
        return b""
    import os
    import tempfile

    W = max(c.width for c in cuadros)
    H = max(c.height for c in cuadros)
    W, H = W + W % 2, H + H % 2
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name
        writer = iio.get_writer(tmp_path, format="FFMPEG", mode="I", fps=fps,
                                codec="libx264", quality=8,
                                pixelformat="yuv420p", macro_block_size=1,
                                ffmpeg_log_level="error")
        try:
            for c in cuadros:
                lienzo = Image.new("RGB", (W, H), _FONDO)
                lienzo.paste(c.convert("RGB"), (0, 0))
                writer.append_data(np.asarray(lienzo))
        finally:
            writer.close()
        with open(tmp_path, "rb") as f:
            return f.read()
    except Exception:
        logger.exception("loop VOLCAT: fallo el MP4")
        return b""
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
