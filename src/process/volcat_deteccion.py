# ════════════════════════════════════════════════════════════════════
# FICHA SDA · volcat_deteccion.py · SDA: Monitoreo Volcánico GOES-19 · ID: SDA-GOES-01
# Objetivo      : señal por volcán "VOLCAT dibuja un objeto anclado al cráter" en el último cuadro publicado por SSEC/CIMSS
# Lógica        : píxel del volcán en la grilla del sector (CE o PS) → objeto VOLCAT que toca el disco de 10 km → estado según área y edad
# Modelo/método : determinístico, sin ML propio. La DETECCIÓN es de VOLCAT (SSEC/CIMSS, experimental); aquí sólo se lee su PNG
# Datos entrada : PNG Ash_Height de VOLCAT (SSEC/CIMSS, público) y su georef; SIN datos personales
# Variables     : área mínima 12 km² (3 píxeles IR), unión de pedazos a 6 km, objeto extenso > 2.000 km², cuadro atrasado ≥ 120 min (umbrales nuestros, declarados abajo)
# Limitaciones  : no validada contra el OVDAS; VOLCAT falla en ambos sentidos (pierde plumas y pinta nubes); sin corrección de paralaje
# Refs/datos    : Pavolonis et al. 2013 (VOLCAT); medición propia 16 y 17-11-2026 (docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md §3.3 y §3.4)
# Ficha completa: docs/FICHA_SDA_GOES.md (§A.7)
# ════════════════════════════════════════════════════════════════════
"""Señal por volcán: ¿VOLCAT dibuja un objeto anclado al cráter?

Por qué existe. Nuestro detector split-window (`detect_ash_enhanced`, BTD < -1 K)
no ve las plumas débiles de Nevados de Chillán de octubre y noviembre de 2026,
que VOLCAT (SSEC/CIMSS) sí dibuja y que el OVDAS confirmó como ceniza. No se
puede reproducir VOLCAT: depende de umbrales por volcán y de aprendizaje
automático no públicos (docs/own_volcat/POR_QUE_VOLCAT_VE_Y_NOSOTROS_NO.md).
Decisión de Nicolás (19-11-2026): usar VOLCAT como capa de detección.

Qué NO es. No es una detección nuestra ni una alerta del OVDAS. Es la lectura de
lo que VOLCAT dibujó en su último cuadro. VOLCAT es experimental en GOES-19 y no
lo hemos validado: pierde plumas (40 de 43 volcanes caen en sectores regionales
de 2 km) y pinta sistemas meteorológicos (Chillán 16-11, plan §3.4).

Cómo se lee. Se reutiliza la lectura por objeto de `volcat_colorbar`
(`volcat_object_heights`): componente conexa de píxeles con color de la barra de
altura que toca un disco de 10 km alrededor del cráter, uniendo antes los
pedazos separados por 6 km o menos (tres píxeles IR), para que el pedazo de un
sistema grande no se mida como pluma. Aquí sólo se agrega la
georreferencia del sector (CE lineal o estereográfica polar) y la regla que
pasa esa lectura a un estado que el operador entiende.

Estados (`evaluar_senal`):
- ``detecta``: objeto anclado de 12 km² o más y de 2.000 km² o menos.
- ``extenso``: objeto anclado mayor a 2.000 km² o manto de más del 5 % del
  sector. Es una detección de VOLCAT, pero de un tamaño que ninguna pluma medida
  alcanzó: puede ser un sistema meteorológico o la nube de una erupción grande.
  No se descarta: se muestra aparte, para que el operador mire el loop.
- ``sin_deteccion``: el cuadro está al día y no hay objeto anclado (o el que hay
  mide menos de 12 km²). Es el estado normal.
- ``atrasado``: no hay objeto, pero el último cuadro tiene 120 min o más. Un
  "nada" viejo no dice nada de lo que pasa ahora.
- ``no_disponible``: SSEC no respondió, no publicó cuadros, el PNG no bajó o no
  se pudo leer, o el volcán cae fuera del sector.

Ventana: el ÚLTIMO cuadro publicado, nada más. Cada volcán cuesta cero
descargas extra (el PNG es el mismo que ya baja el panel VOLCAT) y el historial
lo muestra el loop VOLCAT. Un criterio temporal (objeto anclado antes de crecer,
plan §3.4 opción b) atraparía mejor los sistemas que pasan por encima, pero
pide varios cuadros por sector y por ciclo; queda como mejora posible.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional

from src.process.volcat_colorbar import (MAX_SECTOR_FRAC, SEED_RADIUS_KM,
                                         TOP_MIN_AREA_KM2,
                                         volcat_object_heights)

R_TIERRA_MEDIO_KM = 6371.0  # radio medio terrestre (IUGG), igual que volcat_api

# Área mínima del objeto anclado para contarlo como detección: la misma que fija
# un tope en `volcat_colorbar` (12 km², ~3 píxeles IR de 2 km de ABI). Menos que
# eso es ruido del retrieval (Sabancaya 26-10: píxeles IR sueltos, plan §3.3).
AREA_MIN_KM2 = TOP_MIN_AREA_KM2

# Objeto "extenso" (umbral nuestro). Medido el 16 y 17-11-2026: la pluma
# anclada más grande de Chillán en 2.181 cuadros midió ~270 km² (67 píxeles de
# 2 km); las plumas de los sectores de 250 m llegan al 1,7 % del sector, unos
# 950 km²; los mantos sinópticos de esos sectores, del 12 al 49 %, desde
# ~6.700 km², y el sistema que cubrió Chillán el 16-11 ~126.000 km² (pasó el
# 5 % porque el sector de 2 km es enorme). 2.000 km² queda al doble de la pluma
# más grande medida y a menos de un tercio del manto más chico.
AREA_EXTENSO_KM2 = 2000.0

# Unión de pedazos de un mismo sistema antes de medirlo (umbral nuestro):
# 6 km, tres píxeles IR de ABI, pasados a píxeles del cuadro (3 en un sector
# de 2 km, 22 en uno de 250 m). Por qué: un sistema grande sale roto al
# decodificarlo (el bloque de 18 a 20 km de la barra es negro, igual que el
# suelo caliente en el IR, y los píxeles mezclados ambiguos se descartan).
# Criterio escrito ANTES de medir (19-11-2026), elegir la unión más chica que:
# (1) deje como detección todos los pulsos de Chillán de 08, 10, 11 y 14-11
# (100 cuadros, 70 con objeto); (2) deje como extenso el sistema del 16-11; (3)
# no deje ningún volcán del norte en detección con el sistema de 16 a 18 km
# del 19-11 (10:00 a 13:30 UTC). Sin unión fallan (2) y (3): en Chillán 16-11
# de 08:30 a 09:30 UTC el objeto anclado medía 8 a 49 km², una "pluma"
# perfecta, al lado de un sistema de ~90.000 km². Con 1 píxel (2 km) falla (3):
# Taapaca 12:20 y 12:30 UTC, un pedazo de 3 a 4 píxeles a 3 píxeles del
# sistema. Con 3 píxeles se cumplen las tres; el pulso más grande queda en
# 247 km². Ver `volcat_colorbar.anchored_object`.
UNION_GAP_KM = 6.0

# Edad desde la que un "sin detección" ya no describe el presente. SSEC publica
# con 30 a 50 min de atraso por diseño; es el mismo límite que usa
# `alerta_edad` para VOLCAT (dashboard/map_helpers.py).
VOLCAT_ATRASO_MIN = 120

ESTADOS = ("detecta", "extenso", "sin_deteccion", "atrasado", "no_disponible")


def _nlon(x: float) -> float:
    """Longitud de SSEC a [-180, 180]. Unos sectores la dan 0-360 (289) y otros
    ya negativa (Planchón-Peteroa: -73,5): restar 360 siempre la rompería."""
    return x - 360.0 if x > 180.0 else x


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_TIERRA_MEDIO_KM * math.asin(math.sqrt(a))


def georef_pixel(coords: dict, lat: float, lon: float) -> Optional[dict]:
    """Píxel (fila, columna) de (lat, lon) en el PNG de un sector VOLCAT y el
    tamaño de ese píxel en km. None si la georef no se puede usar.

    Dos proyecciones (las que entrega SSEC para Chile, medido 19-11-2026):
    - ``CE`` (Chile_North, Chile_Central y los sectores dedicados): lineal en
      grados. ``EQ_RADIUS`` = 206264,8 son segundos de arco por radián, así que
      ``SCALE_FACTOR`` es el píxel en segundos de arco, NO en km. El píxel mide
      ``px_km`` N-S y ``px_km·cos(lat)`` E-O.
    - ``PS`` (Chile_South_2_km, de ~-40° al sur): estereográfica polar,
      ``SCALE_FACTOR`` en metros por píxel en el plano. Misma convención que la
      reproyección del visor (`volcat_viewer._volcat_reproject_ps`, validada
      contra la grilla de SSEC): el píxel (OFFSET_X, OFFSET_Y) cae en
      (ORIGIN_LAT, ORIGIN_LON). El tamaño del píxel se mide en el terreno,
      porque el plano sólo es fiel a la latitud ``SECOND_REF_LAT``.

    Devuelve ``{row, col, px_km, px_km_ew}`` (píxel N-S y E-O en km).
    """
    try:
        proj = str(coords.get("PROJECTION", "")).upper()
        ox = float(coords.get("OFFSET_X", 0))
        oy = float(coords.get("OFFSET_Y", 0))
        olat = float(coords["ORIGIN_LAT"])
        olon = _nlon(float(coords["ORIGIN_LON"]))
        sf = float(coords["SCALE_FACTOR"])
    except (AttributeError, KeyError, TypeError, ValueError):
        return None

    if proj == "CE":
        try:
            dp = math.degrees(sf / float(coords["EQ_RADIUS"]))
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            return None
        row = int(round(oy + (olat - lat) / dp))
        col = int(round(ox + (lon - olon) / dp))
        px_km = math.radians(dp) * R_TIERRA_MEDIO_KM
        return {"row": row, "col": col, "px_km": px_km,
                "px_km_ew": px_km * math.cos(math.radians(lat))}

    if proj == "PS":
        try:
            from pyproj import Transformer
            reflon = _nlon(float(coords["REF_LON"]))
            lat_ts = float(coords.get("SECOND_REF_LAT", -60))
            t = Transformer.from_crs(
                "EPSG:4326",
                f"+proj=stere +lat_0=-90 +lat_ts={lat_ts} +lon_0={reflon} "
                f"+ellps=WGS84 +x_0=0 +y_0=0", always_xy=True)
            xo, yo = t.transform(olon, olat)
            x, y = t.transform(lon, lat)
            colf = ox + (x - xo) / sf
            rowf = oy - (y - yo) / sf
            # Lado del píxel en el terreno: distancia a los vecinos de abajo y
            # de la derecha, devueltos a lat/lon.
            lo_s, la_s = t.transform(x, y - sf, direction="INVERSE")
            lo_e, la_e = t.transform(x + sf, y, direction="INVERSE")
        except Exception:
            return None
        return {"row": int(round(rowf)), "col": int(round(colf)),
                "px_km": _haversine_km(lat, lon, la_s, lo_s),
                "px_km_ew": _haversine_km(lat, lon, la_e, lo_e)}

    return None


def leer_objeto_anclado(img_rgb, coords: dict, lat: float, lon: float,
                        seed_radius_km: float = SEED_RADIUS_KM,
                        mapa: Optional[dict] = None) -> dict:
    """Lectura VOLCAT del objeto que toca el cráter, con su área en km². PURA.

    Es `volcat_object_heights` más la georef del sector. Agrega ``area_km2``
    (píxeles del objeto por el área de un píxel en el terreno) cuando hay
    objeto. Sin georef utilizable devuelve ``motivo: "sin_georef"``.

    ``mapa``: salida de `clasificar_mapa` del mismo cuadro, para no clasificar
    el PNG una vez por volcán (un sector regional tiene hasta 26 volcanes).
    """
    g = georef_pixel(coords or {}, lat, lon)
    if g is None:
        return {"note": "la georreferencia del sector no se pudo usar",
                "motivo": "sin_georef"}
    res = volcat_object_heights(img_rgb, g["row"], g["col"], px_km=g["px_km"],
                                px_km_ew=g["px_km_ew"],
                                seed_radius_km=seed_radius_km, mapa=mapa,
                                gap_km=UNION_GAP_KM)
    if "n" in res:
        res["area_km2"] = float(res["n"]) * g["px_km"] * g["px_km_ew"]
    res["px_km"], res["px_km_ew"] = g["px_km"], g["px_km_ew"]
    return res


def evaluar_senal(lectura: Optional[dict], frame_dt: Optional[datetime],
                  ahora: Optional[datetime] = None,
                  error: Optional[str] = None) -> dict:
    """Estado de la señal VOLCAT de un volcán a partir de la lectura del último
    cuadro. PURA.

    ``lectura``: salida de `leer_objeto_anclado` (None si no hubo cuadro).
    ``frame_dt``: hora UTC del cuadro. ``error``: por qué no hay lectura, para
    decirlo en pantalla.

    Devuelve ``{estado, edad_min, area_km2, top_lo_km, top_hi_km, frac_sector,
    manto, motivo}``. ``estado`` es uno de `ESTADOS`. La edad va siempre que se conozca:
    una detección sin hora no dice si es de hace 40 min o de ayer.
    """
    ahora = ahora or datetime.now(timezone.utc)
    out = {"estado": "no_disponible", "edad_min": None, "area_km2": None,
           "top_lo_km": None, "top_hi_km": None, "frac_sector": None,
           "manto": False, "motivo": error}
    if frame_dt is not None:
        try:
            out["edad_min"] = max(0, int((ahora - frame_dt).total_seconds() // 60))
        except (TypeError, ValueError):
            out["edad_min"] = None
    if error is not None or lectura is None or frame_dt is None:
        out["motivo"] = error or "sin cuadro VOLCAT"
        return out

    motivo = lectura.get("motivo")
    out["motivo"] = lectura.get("note")
    out["frac_sector"] = lectura.get("frac_sector")
    area = lectura.get("area_km2")
    out["area_km2"] = area

    # sin_barra, fuera, sin_georef o un motivo desconocido caen al último
    # `else`: no_disponible. Nunca a sin_deteccion.
    if motivo == "manto":
        out["estado"] = "extenso"
        out["manto"] = True
        return out

    if motivo in ("tope", "sin_tope") and area is not None:
        if area < AREA_MIN_KM2:
            estado = "sin_deteccion"
            out["motivo"] = (f"objeto de {area:.0f} km², bajo el mínimo de "
                             f"{AREA_MIN_KM2:g} km²: ruido del retrieval")
        elif area > AREA_EXTENSO_KM2:
            estado = "extenso"
        else:
            estado = "detecta"
        if estado != "sin_deteccion":
            out["top_lo_km"] = lectura.get("top_lo_km")
            out["top_hi_km"] = lectura.get("top_hi_km")
    elif motivo == "sin_objeto":
        estado = "sin_deteccion"
    else:
        out["estado"] = "no_disponible"
        return out

    if (estado == "sin_deteccion" and out["edad_min"] is not None
            and out["edad_min"] >= VOLCAT_ATRASO_MIN):
        estado = "atrasado"
    out["estado"] = estado
    return out


__all__ = ["AREA_EXTENSO_KM2", "AREA_MIN_KM2", "ESTADOS", "MAX_SECTOR_FRAC",
           "UNION_GAP_KM", "VOLCAT_ATRASO_MIN", "evaluar_senal", "georef_pixel",
           "leer_objeto_anclado"]
