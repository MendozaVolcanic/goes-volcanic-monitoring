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

# Ancho minimo del cuadro: con menos, la nota de vacio y la hora no caben en
# una linea a la letra que se lee en un celular.
ANCHO_MIN_PX = 520

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
    from dashboard.utils import desfase_chile, utc_to_chile
    local = utc_to_chile(dt)
    hora_local = (local.strftime("%H:%M") if local.date() == dt.date()
                  else local.strftime("%Y-%m-%d %H:%M"))
    return (f"{dt.strftime('%Y-%m-%d %H:%M')} UTC · {hora_local} "
            f"hora de Chile ({desfase_chile(dt)})")


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


def barra_escala_ns(view: dict, alto_px: int) -> tuple[int, float]:
    """(largo en km, largo en px) de una barra VERTICAL para un mapa de zona.

    Una zona abarca hasta 12,7 grados de latitud (Norte): ahi un km
    horizontal no vale lo mismo arriba que abajo del mapa (cos 17° contra
    cos 29°, 8 % de diferencia). Un grado de meridiano si vale casi lo mismo
    en todo el mapa (110,7 a 110,9 km), asi que la barra va N-S. Mismo
    criterio que `regla.agregar_barra_ns` en las vistas Nacional y Zona.
    """
    lat_m = (view["lat_min"] + view["lat_max"]) / 2.0
    alto_km = (view["lat_max"] - view["lat_min"]) * km_por_grado_lat(lat_m)
    km = largo_barra_km(alto_km)
    return km, km / alto_km * alto_px


# ── Encuadres: un volcan o una zona ──────────────────────────────────────

def encuadre_volcan(v, pad: float) -> dict:
    """Encuadre de ±pad grados centrado en el crater, barra horizontal.

    `archivo` lleva el radio: dos loops del mismo volcan a radios distintos
    no pueden llamarse igual (regla del repo para encuadres ajustables).
    """
    return {
        "titulo": f"{v.name} ±{pad:g}°",
        "archivo": f"{v.name.replace(' ', '_')}_r{pad:g}deg",
        "view": {"lat_min": v.lat - pad, "lat_max": v.lat + pad,
                 "lon_min": v.lon - pad, "lon_max": v.lon + pad},
        "centro": (v.lat, v.lon),
        "barra": "ew",
        "alto": 600,
    }


def encuadre_zona(zona: str, view: dict) -> dict:
    """Encuadre de una zona (el mismo de Modo Guardia), barra N-S.

    Mas alto que el de un volcan: la zona cubre cientos de km y a 600 px una
    pluma de 20 km quedaria en un punado de pixeles.
    """
    return {
        "titulo": f"Zona {zona}",
        "archivo": f"Zona_{zona}",
        "view": dict(view),
        "centro": ((view["lat_min"] + view["lat_max"]) / 2.0,
                   (view["lon_min"] + view["lon_max"]) / 2.0),
        "barra": "ns",
        "alto": 760,
    }


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
    from src.volcanos import CATALOG, PRIORITY_VOLCANOES
    vis = [v for v in CATALOG if v.zone != "test"
           and view["lat_min"] <= v.lat <= view["lat_max"]
           and view["lon_min"] <= v.lon <= view["lon_max"]]
    tri = max(6, w // 55)
    fs = getattr(font, "size", 12)
    rotulos = []
    lat_c = (view["lat_min"] + view["lat_max"]) / 2
    lon_c = (view["lon_min"] + view["lon_max"]) / 2
    # Orden de prioridad para el nombre: el del centro (en un loop de volcan
    # es el volcan del loop y su nombre no se omite), despues los
    # prioritarios ★ (en una zona hay decenas y no caben todos), despues el
    # resto por cercania al centro.
    def _d2(v):
        return (v.lat - lat_c) ** 2 + (v.lon - lon_c) ** 2
    centro_v = min(vis, key=_d2) if vis else None
    for v in sorted(vis, key=lambda v: (v is not centro_v,
                                        v.name not in PRIORITY_VOLCANOES,
                                        _d2(v))):
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


def _geometria_barra(view, x0, y0, w, h, font, orient: str = "ew"):
    """Posicion de la barra de escala, su rotulo y su rectangulo, para
    dibujarla y para que los nombres de volcanes le hagan espacio.

    orient "ew": horizontal (loop de volcan, mapa en km del crater).
    orient "ns": vertical (loop de zona, ver `barra_escala_ns`).
    """
    m = max(10, min(w, h) // 30)
    grosor = max(3, min(w, h) // 160)
    fs = getattr(font, "size", 12)
    if orient == "ns":
        km, largo = barra_escala_ns(view, h)
        bx, by0 = x0 + m, y0 + h - m
        texto = f"{km} km N-S"
        tw = font.getlength(texto) if hasattr(font, "getlength") else fs * len(texto)
        rect = (bx - grosor * 2 - 4, by0 - largo - 4,
                bx + grosor * 2 + 8 + tw, by0 + grosor + 4)
        return {"orient": "ns", "km": km, "bx": bx, "by0": by0,
                "by1": by0 - largo, "grosor": grosor, "texto": texto,
                "rect": rect}
    km, largo = barra_escala(view, w)
    bx0, by = x0 + m, y0 + h - m
    rect = (bx0 - 4, by - grosor * 2 - fs * 1.4, bx0 + largo + 4, by + grosor + 4)
    return {"orient": "ew", "km": km, "bx0": bx0, "bx1": bx0 + largo,
            "by": by, "grosor": grosor, "texto": f"{km} km", "rect": rect}


def _dibujar_barra(draw, g, font):
    """Barra de escala blanca abajo a la izquierda, con halo oscuro."""
    fs = getattr(font, "size", 12)
    if g["orient"] == "ns":
        bx, by0, by1, grosor = g["bx"], g["by0"], g["by1"], g["grosor"]
        draw.line([(bx, by0), (bx, by1)], fill=(10, 14, 20), width=grosor + 4)
        draw.line([(bx, by0), (bx, by1)], fill=_BLANCO, width=grosor)
        for yt in (by0, by1):
            draw.line([(bx - grosor * 2, yt), (bx + grosor, yt)], fill=_BLANCO,
                      width=max(2, grosor // 2))
        _texto(draw, (bx + grosor * 2 + 6, (by0 + by1) / 2 - fs * 0.6),
               g["texto"], font)
        return
    bx0, bx1, by, grosor = g["bx0"], g["bx1"], g["by"], g["grosor"]
    draw.line([(bx0, by), (bx1, by)], fill=(10, 14, 20), width=grosor + 4)
    draw.line([(bx0, by), (bx1, by)], fill=_BLANCO, width=grosor)
    for xt in (bx0, bx1):
        draw.line([(xt, by - grosor * 2), (xt, by + grosor)], fill=_BLANCO,
                  width=max(2, grosor // 2))
    s = g["texto"]
    _texto(draw, ((bx0 + bx1) / 2 - draw.textlength(s, font=font) / 2,
                  by - grosor * 2 - fs * 1.25), s, font)


def componer_cuadro(mapa: Image.Image, view: dict, centro: tuple[float, float],
                    dt: datetime, titulo: str, sector_txt: str,
                    barra_color: Image.Image | None = None,
                    aviso: str | None = None,
                    alto_mapa: int = 640,
                    barra: str = "ew") -> tuple[Image.Image, dict]:
    """Un cuadro del loop listo para GIF/MP4.

    Disposicion: banda superior (volcan, producto, sector) · mapa con
    frontera, volcanes y barra de escala · barra de color de la altura AL
    COSTADO del mapa (encima taparia la cordillera, que es justo donde nace
    la pluma) · banda inferior (hora UTC y de Chile, nota de vacio, aviso de
    salto).

    El mapa va en proporcion de km (ancho = alto * km_lon / km_lat en el
    crater): asi un km horizontal mide lo mismo que uno vertical y la barra
    de escala vale en las dos direcciones.

    `barra` = "ew" (volcan) o "ns" (zona, ver `barra_escala_ns`). El lienzo
    se ensancha hasta ANCHO_MIN_PX o hasta el texto mas largo: una zona alta
    y angosta (Norte) deja un mapa de ~270 px y los rotulos se cortaban. El
    mapa no se estira, el espacio extra queda de fondo.

    Devuelve (imagen, geo) con `geo` = {"mapa_xy", "mapa_px", "textos",
    "texto_cabe", "rotulos", "barra_rect", "barra_txt"}.
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

    orient = barra
    barra = None
    if barra_color is not None:
        bw = max(1, round(barra_color.width * h / barra_color.height))
        barra = barra_color.convert("RGB").resize((bw, h), Image.LANCZOS)

    hora = rotulo_hora(dt)
    sector_linea = f"Sector VOLCAT {sector_txt}"
    marca = "VOLCAT SSEC/CIMSS · GOES-19"
    textos = [titulo, sector_linea, hora, NOTA_VACIO] + ([aviso] if aviso else [])
    medir = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    fuentes = [f_tit, f_peq, f_txt, f_peq] + ([f_txt] if aviso else [])
    mas_largo = max(medir.textlength(t, font=f) for t, f in zip(textos, fuentes))
    ancho_total = max(w + (barra.width if barra else 0), ANCHO_MIN_PX,
                      int(mas_largo + 2 * pad + 4))

    # Frontera, volcanes y barra se dibujan sobre el MAPA solo y despues se
    # pega: asi lo que sigue de largo (la frontera cruza el encuadre entero)
    # queda recortado al borde y no tacha la hora de la banda de abajo.
    dm = ImageDraw.Draw(mapa)
    _dibujar_frontera(dm, view, 0, 0, w, h)
    gbarra = _geometria_barra(view, 0, 0, w, h, f_peq, orient=orient)
    rotulos = _dibujar_volcanes(dm, view, 0, 0, w, h, f_peq,
                                evitar=[gbarra["rect"]])
    _dibujar_barra(dm, gbarra, f_peq)

    img = Image.new("RGB", (ancho_total, banda_sup + h + banda_inf), _FONDO)
    x0, y0 = 0, banda_sup
    img.paste(mapa, (x0, y0))
    if barra:
        img.paste(barra, (x0 + w, y0))
    draw = ImageDraw.Draw(img)

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
    texto_cabe = all(pad + draw.textlength(t, font=f) <= ancho_total
                     for t, f in zip(textos, fuentes))
    return img, {"mapa_xy": (x0, y0), "mapa_px": (w, h), "textos": textos,
                 "texto_cabe": texto_cabe, "rotulos": rotulos,
                 "barra_rect": gbarra["rect"], "barra_txt": gbarra["texto"]}


# ── Salidas ───────────────────────────────────────────────────────────────

def colores_de_escala(barra: Image.Image, min_px: int = 20) -> list[tuple]:
    """Colores de los bloques de la barra de color (los que tienen area).

    Se descartan los grises (fondo blanco, numeros, borde) y los colores con
    menos de `min_px` pixeles, que son el antialias del texto: no son
    valores de la escala.
    """
    cols = barra.convert("RGB").getcolors(1 << 20) or []
    return [c for n, c in cols if n >= min_px and max(c) - min(c) >= 25]


# Colores que dibujamos encima del producto: tambien se reservan, si no el
# triangulo cian del volcan salia verdoso en el GIF.
_COLORES_DIBUJO = [(0, 255, 255), _BLANCO, _AMARILLO, _FONDO, FONDO_FUERA,
                   (20, 24, 32), (236, 240, 250), (0, 0, 0), _GRIS_TXT,
                   (15, 18, 24)]


def _paleta_fija(colores_fijos: list[tuple]) -> Image.Image:
    """Paleta de 256: los colores de la escala y del dibujo EXACTOS, y el
    resto una rampa de grises para el fondo IR (que es gris)."""
    fijos = []
    for c in list(colores_fijos) + _COLORES_DIBUJO:
        c = tuple(int(v) for v in c[:3])
        if c not in fijos:
            fijos.append(c)
    fijos = fijos[:200]          # deja al menos 56 grises para el fondo
    n = 256 - len(fijos)
    grises = [(round(i * 255 / (n - 1)),) * 3 for i in range(n)]
    pal = Image.new("P", (1, 1))
    pal.putpalette([v for c in fijos + grises for v in c])
    return pal


def armar_gif(cuadros: list[Image.Image], ms_por_cuadro: int = 500,
              colores_fijos: list[tuple] | None = None) -> bytes:
    """GIF en loop infinito con exactamente los cuadros recibidos.

    Un GIF tiene 256 colores. Con `colores_fijos` (los de la escala, ver
    `colores_de_escala`) cada cuadro se pasa a una paleta que los contiene
    EXACTOS, sin tramado: el pixel de la pluma conserva el color con que
    figura en la barra y la altura se lee igual que en el producto. Con la
    paleta adaptativa de PIL el fondo IR en grises competia por los cupos y
    los colores de la escala se corrian.
    """
    if not cuadros:
        return b""
    if colores_fijos:
        pal = _paleta_fija(colores_fijos)
        cuadros = [c.convert("RGB").quantize(palette=pal,
                                             dither=Image.Dither.NONE)
                   for c in cuadros]
    buf = io.BytesIO()
    cuadros[0].save(buf, format="GIF", save_all=True,
                    append_images=cuadros[1:], duration=ms_por_cuadro,
                    loop=0, optimize=not colores_fijos, disposal=2)
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
