"""Regla y escala para medir hasta donde llega la ceniza sobre la imagen.

Por que existe: el operador necesita decir "la pluma esta a 60 km al este del
crater" mirando el mapa. En grados eso no se lee: un grado de longitud vale
106 km en Parinacota y 64 km en la zona austral. Esta pieza resuelve dos cosas.

1. **Grilla del volcan en km.** `figura_en_km` pasa una figura dibujada en
   lon/lat a un plano local centrado en el crater (x hacia el este, y hacia el
   norte, en km). Con eso una linea trazada encima ya mide km, y plotly la
   rotula en el navegador (`activar_regla`), sin recargar la pagina ni gastar
   un rerun de Streamlit. Medir desde el crater en ese plano se desvia menos de
   1,5 % de la distancia real hasta 3 grados de radio en todo Chile
   (tests/test_regla.py lo fija de norte a sur).

2. **Barra norte-sur en Nacional y Zona.** Esos mapas estan en grados con
   aspecto 1:1, asi que un km horizontal no mide lo mismo arriba que abajo del
   mapa. Un grado de meridiano si vale casi lo mismo en todas partes (110,6 a
   111,4 km), por eso la barra va vertical.

Lo que la regla NO corrige: el paralaje. GOES-19 mira Chile de lado, y una
pluma alta aparece corrida hacia el sur (lejos del satelite) entre 0,4 km por
km de altura en el norte y 1,5 en la zona austral. Va dicho en pantalla junto
al interruptor. No decide nada: muestra una distancia y la lectura queda al
geologo de turno.
"""

from __future__ import annotations

import math

import numpy as np

# Radio medio de la Tierra (IUGG), solo para la distancia de referencia.
_R_TIERRA_KM = 6371.0088

# Candidatos de anillos y de barra. Redondos para que se lean de un vistazo.
_ANILLOS_KM = (5, 10, 25, 50, 100, 200, 300, 500)
_BARRA_KM = (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000)

_COLOR_REGLA = "#ffd23f"
_COLOR_BARRA = "rgba(255,255,255,0.92)"


def km_por_grado_lat(lat: float) -> float:
    """Largo de un grado de latitud en km, elipsoide WGS84.

    Por que no 111 fijo: el meridiano es mas largo hacia los polos; usar la
    serie del elipsoide cuesta lo mismo y quita 0,5 % de error en el norte.
    """
    p = math.radians(lat)
    return (111132.954 - 559.822 * math.cos(2 * p)
            + 1.175 * math.cos(4 * p)) / 1000.0


def km_por_grado_lon(lat: float) -> float:
    """Largo de un grado de longitud en km a esa latitud, WGS84."""
    p = math.radians(lat)
    return (111412.84 * math.cos(p) - 93.5 * math.cos(3 * p)
            + 0.118 * math.cos(5 * p)) / 1000.0


def a_km(lat, lon, lat0: float, lon0: float):
    """(x, y) en km respecto del crater: x hacia el este, y hacia el norte.

    Plano equirectangular local con la escala del crater. Es lineal, asi que
    la imagen (que viene en una grilla lon/lat) se reubica sin deformarse.
    """
    x = (np.asarray(lon, dtype=float) - lon0) * km_por_grado_lon(lat0)
    y = (np.asarray(lat, dtype=float) - lat0) * km_por_grado_lat(lat0)
    if np.ndim(x) == 0:
        return float(x), float(y)
    return x, y


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia sobre la esfera media (haversine). Es la referencia contra la
    que se mide el error del plano local; no se dibuja."""
    a1, o1, a2, o2 = map(math.radians, (lat1, lon1, lat2, lon2))
    h = (math.sin((a2 - a1) / 2) ** 2
         + math.cos(a1) * math.cos(a2) * math.sin((o2 - o1) / 2) ** 2)
    return 2 * _R_TIERRA_KM * math.asin(math.sqrt(h))


def radios_anillos_km(radio_km: float, maximo: int = 4) -> list[int]:
    """Anillos que se ven en un encuadre de +-radio_km.

    Entran los que alcanzan a asomar en las esquinas (radio * raiz de 2) y se
    quedan los `maximo` mas grandes: con anillos fijos de 5 a 50 km, abrir el
    radio a 3 grados para seguir una pluma dejaba los anillos apinados en el
    centro y no median nada.
    """
    visibles = [r for r in _ANILLOS_KM if r <= radio_km * math.sqrt(2)]
    return visibles[-maximo:] if visibles else [_ANILLOS_KM[0]]


def largo_barra_km(ancho_km: float) -> int:
    """Largo redondo de la barra: el mayor 1-2-5 que no pase un tercio del
    ancho, para que se lea sin tapar el mapa."""
    tope = ancho_km / 3.0
    candidatos = [b for b in _BARRA_KM if b <= tope]
    return candidatos[-1] if candidatos else _BARRA_KM[0]


# -- figura en km -----------------------------------------------------------

def _es_dato(ref) -> bool:
    """Una referencia de anotacion o forma va en coordenadas de datos si no es
    'paper' (plotly deja None cuando no se especifica)."""
    return ref is None or str(ref).startswith(("x", "y"))


def _convertir_serie(valores, escala: float, origen: float):
    """Convierte una serie conservando los None, que son los cortes de linea
    (asi viene la costa y la frontera de Chile)."""
    return [None if v is None else (float(v) - origen) * escala
            for v in valores]


def figura_en_km(fig, lat0: float, lon0: float):
    """Pasa una figura dibujada en lon/lat al plano en km del crater.

    Mueve TODO con la misma conversion: trazas, imagen de fondo, anotaciones y
    formas en coordenadas de datos, y el rango de los ejes. Si una sola pieza
    quedara en grados se dibujaria a cientos de km de donde esta y la regla
    mediria contra un fondo corrido. Lo que va en coordenadas de papel (hora,
    barras de color de VOLCAT) no se toca.

    Los tooltips que mostraban lon/lat con %{x}/%{y} pasan a leer la
    coordenada geografica desde `customdata`: en km dirian 0.000, 0.000.
    """
    kx, ky = km_por_grado_lon(lat0), km_por_grado_lat(lat0)

    for tr in fig.data:
        xs, ys = getattr(tr, "x", None), getattr(tr, "y", None)
        if xs is None or ys is None:
            continue
        lons, lats = list(xs), list(ys)
        ht = getattr(tr, "hovertemplate", None)
        if ht and ("%{x" in ht or "%{y" in ht):
            tr.customdata = [[la, lo] for la, lo in zip(lats, lons)]
            tr.hovertemplate = (ht.replace("%{x", "%{customdata[1]")
                                  .replace("%{y", "%{customdata[0]"))
        tr.x = _convertir_serie(lons, kx, lon0)
        tr.y = _convertir_serie(lats, ky, lat0)

    for im in fig.layout.images:
        if im.xref == "x" and im.yref == "y":
            im.x = (im.x - lon0) * kx
            im.y = (im.y - lat0) * ky
            im.sizex = im.sizex * kx
            im.sizey = im.sizey * ky

    for an in fig.layout.annotations:
        if _es_dato(an.xref) and an.x is not None:
            an.x = (an.x - lon0) * kx
        if _es_dato(an.yref) and an.y is not None:
            an.y = (an.y - lat0) * ky

    for sh in fig.layout.shapes:
        if _es_dato(sh.xref):
            sh.x0 = (sh.x0 - lon0) * kx
            sh.x1 = (sh.x1 - lon0) * kx
        if _es_dato(sh.yref):
            sh.y0 = (sh.y0 - lat0) * ky
            sh.y1 = (sh.y1 - lat0) * ky

    xr, yr = fig.layout.xaxis.range, fig.layout.yaxis.range
    if xr is not None:
        fig.layout.xaxis.range = [(xr[0] - lon0) * kx, (xr[1] - lon0) * kx]
    if yr is not None:
        fig.layout.yaxis.range = [(yr[0] - lat0) * ky, (yr[1] - lat0) * ky]
    # En km un km horizontal y uno vertical miden lo mismo en pantalla: el
    # 1/cos(lat) que se usaba en grados ya va dentro de la conversion.
    fig.layout.yaxis.scaleanchor = "x"
    fig.layout.yaxis.scaleratio = 1
    return fig


def activar_regla(fig, decimales: int = 0):
    """Arrastrar sobre el mapa dibuja una linea rotulada con su largo en km.

    Lo calcula plotly en el navegador: no hay rerun, y la linea sobrevive al
    refresco del panel mientras la imagen no cambie (verificado en Streamlit
    1.56). Con un scan nuevo se borra, que es lo correcto: hay que volver a
    medir sobre la imagen nueva.
    """
    fig.update_layout(
        dragmode="drawline",
        newshape=dict(
            line=dict(color=_COLOR_REGLA, width=3),
            label=dict(texttemplate=f"%{{length:.{decimales}f}} km",
                       font=dict(color=_COLOR_REGLA, size=13),
                       textposition="end"),
        ),
    )
    return fig


def _barra(fig, x0, y0, x1, y1, texto, tx, ty, xanchor, yanchor):
    """Barra con halo oscuro: legible sobre nubes blancas y sobre oceano."""
    for color, ancho in (("rgba(10,14,20,0.85)", 6), (_COLOR_BARRA, 2.5)):
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1,
                      xref="x", yref="y", line=dict(color=color, width=ancho))
    fig.add_annotation(x=tx, y=ty, xref="x", yref="y", text=texto,
                       showarrow=False, xanchor=xanchor, yanchor=yanchor,
                       font=dict(color=_COLOR_BARRA, size=11),
                       bgcolor="rgba(10,14,20,0.6)", borderpad=2)
    return fig


def agregar_barra_escala(fig, x_rango, y_rango, x_frac: float = 0.05):
    """Barra horizontal abajo a la izquierda, para una figura YA en km.

    `x_frac` corre el inicio cuando el borde izquierdo esta ocupado (la barra
    de color de VOLCAT).
    """
    x_min, x_max = x_rango
    y_min, y_max = y_rango
    largo = largo_barra_km(x_max - x_min)
    x0 = x_min + x_frac * (x_max - x_min)
    y0 = y_min + 0.06 * (y_max - y_min)
    return _barra(fig, x0, y0, x0 + largo, y0, f"{largo} km",
                  x0 + largo / 2, y0, "center", "bottom")


def agregar_barra_ns(fig, bounds: dict):
    """Barra vertical abajo a la izquierda, para un mapa en grados.

    Vertical porque un grado de meridiano vale lo mismo en todo el mapa y uno
    de paralelo no. El rotulo dice N-S para que nadie la use de lado.
    """
    alto_grados = bounds["lat_max"] - bounds["lat_min"]
    ancho_grados = bounds["lon_max"] - bounds["lon_min"]
    lat_base = bounds["lat_min"] + 0.04 * alto_grados
    largo = largo_barra_km(alto_grados * km_por_grado_lat(lat_base))
    # El grado de meridiano se evalua a media barra (dos pasadas bastan):
    # en una barra de 1000 km la diferencia con la base ya es de 1 km.
    dlat = largo / km_por_grado_lat(lat_base)
    dlat = largo / km_por_grado_lat(lat_base + dlat / 2)
    x = bounds["lon_min"] + 0.05 * ancho_grados
    return _barra(fig, x, lat_base, x, lat_base + dlat, f"{largo} km N-S",
                  x + 0.012 * ancho_grados, lat_base + dlat / 2,
                  "left", "middle")
