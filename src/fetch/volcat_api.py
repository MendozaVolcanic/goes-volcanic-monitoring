"""Cliente del API VOLCAT (CIMSS/SSEC) para altura de pluma volcanica.

Endpoint unico: GET {BASE}/imagery/get_list/json/sector:X::instr:Y::...

Devuelve PNG color-codificado de Ash Height (altitud km), Ash Loading (g/m^2),
Ash Probability y Ash Reff. Sin autenticacion, gratis, cadencia ABI 10 min.

Documentacion completa en docs/altura_pluma/VOLCAT_api_reference.md
"""

from __future__ import annotations

import logging
import unicodedata
from typing import Optional

from src.fetch._http_session import get_session as _get_session

logger = logging.getLogger(__name__)

BASE = "https://volcano.ssec.wisc.edu"
TIMEOUT = 20

# Mapping nombre de volcano -> sector VOLCAT recomendado
# Ver docs/altura_pluma/sectores_VOLCAT_chile.md
VOLCANO_TO_SECTOR: dict[str, tuple[str, str]] = {
    # volcano name (como aparece en CATALOG) -> (sector, instr)
    # Sectores con ABI nativo (cadencia 10 min)
    "Copahue": ("Copahue_250_m", "ABI"),
    "Calbuco": ("Calbuco_1_km", "ABI"),
    "Planchón-Peteroa": ("Planchon-Peteroa_500_m", "ABI"),
    # Zona norte -> Chile_North_2_km
    "Taapaca": ("Chile_North_2_km", "ABI"),
    "Parinacota": ("Chile_North_2_km", "ABI"),
    "Guallatiri": ("Chile_North_2_km", "ABI"),
    "Isluga": ("Chile_North_2_km", "ABI"),
    "Irruputuncu": ("Chile_North_2_km", "ABI"),
    "Olca": ("Chile_North_2_km", "ABI"),
    "Aucanquilcha": ("Chile_North_2_km", "ABI"),
    "Ollagüe": ("Chile_North_2_km", "ABI"),
    "San Pedro": ("Chile_North_2_km", "ABI"),
    "Putana": ("Chile_North_2_km", "ABI"),
    "Láscar": ("Chile_North_2_km", "ABI"),
    "Lastarria": ("Chile_North_2_km", "ABI"),
    "Ojos del Salado": ("Chile_North_2_km", "ABI"),
    # Zona centro
    "Nevado de Longaví": ("Chile_Central_2_km", "ABI"),
    "Descabezado Grande": ("Chile_Central_2_km", "ABI"),
    "Cerro Azul / Quizapu": ("Chile_Central_2_km", "ABI"),
    "Laguna del Maule": ("Chile_Central_2_km", "ABI"),
    "Nevados de Chillán": ("Chile_Central_2_km", "ABI"),
    "Antuco": ("Chile_Central_2_km", "ABI"),
    "Callaqui": ("Chile_Central_2_km", "ABI"),
    # Zona sur
    "Lonquimay": ("Chile_South_2_km", "ABI"),
    "Llaima": ("Chile_South_2_km", "ABI"),
    "Sollipulli": ("Chile_South_2_km", "ABI"),
    "Villarrica": ("Chile_South_2_km", "ABI"),
    "Quetrupillán": ("Chile_South_2_km", "ABI"),
    "Lanín": ("Chile_South_2_km", "ABI"),
    "Mocho-Choshuenco": ("Chile_South_2_km", "ABI"),
    "Puyehue-Cordón Caulle": ("Chile_South_2_km", "ABI"),
    "Casablanca / Antillanca": ("Chile_South_2_km", "ABI"),
    "Osorno": ("Chile_South_2_km", "ABI"),
    "Yate": ("Chile_South_2_km", "ABI"),
    "Hornopirén": ("Chile_South_2_km", "ABI"),
    "Huequi": ("Chile_South_2_km", "ABI"),
    "Michinmahuida": ("Chile_South_2_km", "ABI"),
    "Chaitén": ("Chile_South_2_km", "ABI"),
    # Austral
    "Corcovado": ("Chile_South_2_km", "ABI"),
    "Melimoyu": ("Chile_South_2_km", "ABI"),
    "Mentolat": ("Chile_South_2_km", "ABI"),
    "Hudson": ("Chile_South_2_km", "ABI"),
    "Lautaro": ("Argentina_5_km", "ABI"),
    # Test volcanoes
    "Kīlauea (Hawái)": ("Kilauea_250_m", "ABI"),
    "Popocatépetl (México)": ("Popocatepetl_250_m", "ABI"),
}

# Sectores REGIONALES de VOLCAT que cubren zonas completas (no un volcan
# puntual). Permite ver altura de pluma por zona en vez de obligar a
# elegir un volcan. Verificado: los 3 tienen cobertura GOES-19 nativa.
# No existe sector "austral" en VOLCAT — Chile_South_2_km cubre hasta el
# extremo sur, asi que la zona austral cae bajo "Sur".
ZONE_TO_SECTOR: dict[str, tuple[str, str]] = {
    "Norte":  ("Chile_North_2_km",   "ABI"),
    "Centro": ("Chile_Central_2_km", "ABI"),
    "Sur":    ("Chile_South_2_km",   "ABI"),
}

# Variante de 4 zonas para igualar el grid de los RGB (Norte/Centro/Sur/Austral).
# VOLCAT NO tiene sector austral propio: Chile_South_2_km cubre hasta el extremo
# sur, asi que 'Austral' reusa ese sector pero RECORTADO a la franja austral
# (el encuadre lo definen los view-bounds en zonas_fullscreen.VOLCAT_VIEW_4).
# ZONE_TO_SECTOR (3) se mantiene intacto para el resto del codigo. (jun 2026)
ZONE_TO_SECTOR_4: dict[str, tuple[str, str]] = {
    "Norte":   ("Chile_North_2_km",   "ABI"),
    "Centro":  ("Chile_Central_2_km", "ABI"),
    # Sur usa Chile_CENTRAL (no Chile_South): Villarrica/Llaima/Osorno/Calbuco
    # (-37 a -41) caen en Chile_Central (-46.3..-32.3); Chile_South arranca en
    # -40.3 y se los pierde. El encuadre lo acota a la franja sur (VOLCAT_VIEW_4).
    "Sur":     ("Chile_Central_2_km", "ABI"),
    "Austral": ("Chile_South_2_km",   "ABI"),  # de Chaitén hacia el sur
}

# Leyenda color->producto
LEGEND_KEY = {
    "Ash_Height": "ASH_HGT-LOAD",
    "Ash_Loading": "ASH_HGT-LOAD",
    "Ash_Probability": "ASH_PROB",
    "Ash_Reff": "ASH_REFF",
    "BT11um": "BT11um",
    "BTD1112um": "BTD1112um",
    "REF065um": "REF065um",
}


def get_sector_for_volcano(volcano_name: str) -> Optional[tuple[str, str]]:
    """Retorna (sector, instr) para un volcano, o None si no mapea."""
    # Match exacto primero, luego substring
    if volcano_name in VOLCANO_TO_SECTOR:
        return VOLCANO_TO_SECTOR[volcano_name]
    vlow = volcano_name.lower()
    for k, v in VOLCANO_TO_SECTOR.items():
        if vlow in k.lower() or k.lower() in vlow:
            return v
    return None


def _norm(s: str) -> str:
    """minuscula SIN tildes — para matchear nombres del CATALOG (sin tilde,
    'Lascar'/'Nevados de Chillan') contra las claves de VOLCANO_TO_SECTOR
    (con tilde, 'Láscar'/'Nevados de Chillán')."""
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c)).lower()


# Sectores REGIONALES (2 km / 5 km): cubren franjas grandes y NO siempre
# contienen al volcan que tienen mapeado (bug verificado jun 2026: Chile_South
# arranca en lat -40.3 y se pierde Villarrica/Llaima/Lonquimay, que estan al
# norte). Por eso para el encuadre regional elegimos por LATITUD, no por el
# mapeo. Solo los sectores DEDICADOS chicos (250/500/1000 m) se honran tal cual.
_REGIONAL_SECTORS = {"Chile_North_2_km", "Chile_Central_2_km",
                     "Chile_South_2_km", "Argentina_5_km"}


def _regional_sector_for_lat(lat: float) -> tuple[str, str]:
    """Sector regional VOLCAT que CONTIENE esa latitud. Bounds reales medidos
    (jun 2026): North lat[-30,-16]; Central lat[-46,-32]; South lat[-54,-40].
    Umbrales -31 / -42 mantienen cada volcan bien adentro de su sector."""
    if lat >= -31.0:
        return ("Chile_North_2_km", "ABI")
    if lat >= -42.0:
        return ("Chile_Central_2_km", "ABI")
    return ("Chile_South_2_km", "ABI")


def resolve_volcat_sector(volcano) -> tuple[str, str]:
    """(sector, instr) para CUALQUIER volcan del CATALOG — nunca None, asi que
    TODOS son seleccionables en la vista por volcan, y el volcan SIEMPRE cae
    dentro de la imagen del sector (necesario para el zoom).

    1) Sector dedicado CHICO (250/500/1000 m) si existe — centrado en ESTE
       volcan (match exacto ignorando tildes: 'Planchon-Peteroa' del catalogo
       encuentra su sector 500 m). Los sectores regionales mapeados se IGNORAN
       aca (a veces no contienen al volcan).
    2) Si no, el sector regional por LATITUD (garantiza contencion).

    `volcano` es un objeto Volcano (usa .name, .lat).
    """
    dedicated = None
    if volcano.name in VOLCANO_TO_SECTOR:
        dedicated = VOLCANO_TO_SECTOR[volcano.name]
    else:
        vnorm = _norm(volcano.name)
        for k, sec in VOLCANO_TO_SECTOR.items():
            if _norm(k) == vnorm:
                dedicated = sec
                break
    if dedicated and dedicated[0] not in _REGIONAL_SECTORS:
        return dedicated
    return _regional_sector_for_lat(volcano.lat)


def _query_frames(sector: str, instr: str, image_type: str,
                  sat: str) -> tuple[list, dict | None]:
    """Helper: pega al API VOLCAT y devuelve (frames, coords).

    SIEMPRE devuelve una 2-tupla — los callers desempacan con
    `frames, coords = _query_frames(...)`. Antes los paths de error devolvían
    `[]` (lista desnuda) -> ValueError al desempacar y crash de la página VOLCAT
    cuando SSEC fallaba. (fix audit jun 2026)
    """
    url = (
        f"{BASE}/imagery/get_list/json/"
        f"sector:{sector}::instr:{instr}::sat:{sat}"
        f"::image_type:{image_type}::endtime:latest::daterange:180"
    )
    try:
        r = _get_session().get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            logger.warning("VOLCAT API %s -> %s", url, r.status_code)
            return [], None
        d = r.json()
    except Exception as e:
        logger.warning("VOLCAT API fail: %s", e)
        return [], None
    return d.get("endtime") or [], d.get("coordinates")


def volcat_latest(
    sector: str,
    instr: str = "ABI",
    image_type: str = "Ash_Height",
    sat: str = "GOES-19",
) -> Optional[dict]:
    """Consulta el API y devuelve el frame mas reciente disponible.

    SATELITE (fix mayo 2026): el API VOLCAT devuelve frames de GOES-18
    (West) Y GOES-19 (East) MEZCLADOS, ordenados por timestamp. Tomar
    `frames[-1]` ciego daba a veces GOES-18 — que ve Chile desde el
    Pacifico con angulo MUY oblicuo (peor parallax, peor geolocalizacion,
    pluma "tumbada"). Para Sudamerica GOES-19 (East) es SIEMPRE mejor.

    Por eso el default ahora es `sat="GOES-19"`. Pero algunos sectores
    de test (Kilauea/Hawai) SOLO tienen GOES-18 — para esos hacemos
    fallback automatico a `sat="all"` si GOES-19 no devuelve nada.

    Returns:
        dict con keys: datetime, image_url, legend_url, annot_url, coords.
        None si no hay frames o falla el request.
    """
    frames, coords = _query_frames(sector, instr, image_type, sat)
    # Fallback: si pedimos un satelite especifico y no hay cobertura
    # (caso Hawai con GOES-19), reintentar con "all" para no quedar sin
    # imagen. Asi Chile usa GOES-19 y Hawai cae a GOES-18 transparente.
    used_sat = sat
    if not frames and sat != "all":
        logger.info("VOLCAT: sin frames %s para %s, fallback a sat=all",
                    sat, sector)
        frames, coords = _query_frames(sector, instr, image_type, "all")
        used_sat = "all"
    if not frames:
        return None
    last = frames[-1]

    legend_key = LEGEND_KEY.get(image_type, "ASH_HGT-LOAD")
    return {
        "datetime": last.get("datetime"),
        "image_url": BASE + last["filename"],
        "annot_url": (BASE + last["annot"]) if last.get("annot") else None,
        "legend_url": f"{BASE}/data/sector_imagery_config/overlays/maps/{sector}.MAP.{legend_key}.png",
        "latlon_url": f"{BASE}/data/sector_imagery_config/overlays/latlon/{sector}.LATLON.CYAN.png",
        "volcanoes_url": f"{BASE}/data/sector_imagery_config/overlays/volcanoes/{sector}.VOLCANOES.CYAN.png",
        "coords": coords,
        "sector": sector,
        "instr": instr,
        "image_type": image_type,
        "sat": last.get("filename", "").split("/")[-1].split(".")[0] if last.get("filename") else None,
    }


def _parse_volcat_frame_dt(dstr: Optional[str]):
    """'2026-05-11_12-00-30' -> datetime UTC (o None)."""
    if not dstr:
        return None
    try:
        from datetime import datetime, timezone
        d, t = dstr.split("_")
        y, mo, da = map(int, d.split("-"))
        hh, mm, ss = map(int, t.split("-"))
        return datetime(y, mo, da, hh, mm, ss, tzinfo=timezone.utc)
    except Exception:
        return None


def volcat_at_time(
    target_dt,
    sector: str,
    instr: str = "ABI",
    image_type: str = "Ash_Height",
    sat: str = "GOES-19",
    max_gap_min: float = 30.0,
) -> Optional[dict]:
    """Frame VOLCAT más cercano a `target_dt` (histórico, no el último).

    El API devuelve hasta ~30 días de frames (Ash_Height); en vez de tomar el
    último (volcat_latest) elegimos el más cercano al timestamp objetivo. Para
    el backfill de la ALTURA cuantitativa (km AMSL, Pavolonis 2013).

    Args:
        target_dt:    datetime UTC objetivo.
        max_gap_min:  si el frame más cercano queda a más de esto, devuelve None
                      (mejor no mostrar nada que un frame de otra hora).

    Returns:
        Mismo dict que volcat_latest (datetime/image_url/legend_url/...), o None.
    """
    frames, coords = _query_frames(sector, instr, image_type, sat)
    if not frames and sat != "all":
        frames, coords = _query_frames(sector, instr, image_type, "all")
    if not frames:
        return None

    best, best_gap = None, None
    for f in frames:
        fdt = _parse_volcat_frame_dt(f.get("datetime"))
        if fdt is None:
            continue
        gap = abs((fdt - target_dt).total_seconds())
        if best_gap is None or gap < best_gap:
            best, best_gap = f, gap
    if best is None or best_gap > max_gap_min * 60:
        return None

    legend_key = LEGEND_KEY.get(image_type, "ASH_HGT-LOAD")
    return {
        "datetime": best.get("datetime"),
        "image_url": BASE + best["filename"],
        "annot_url": (BASE + best["annot"]) if best.get("annot") else None,
        "legend_url": f"{BASE}/data/sector_imagery_config/overlays/maps/{sector}.MAP.{legend_key}.png",
        "latlon_url": f"{BASE}/data/sector_imagery_config/overlays/latlon/{sector}.LATLON.CYAN.png",
        "volcanoes_url": f"{BASE}/data/sector_imagery_config/overlays/volcanoes/{sector}.VOLCANOES.CYAN.png",
        "coords": coords,
        "sector": sector,
        "instr": instr,
        "image_type": image_type,
        "gap_seconds": int(best_gap),
    }


def volcat_available_types(sector: str, instr: str = "ABI") -> list[str]:
    """Lista productos image_type disponibles para un sector."""
    url = (
        f"{BASE}/imagery/get_list/json/"
        f"sector:{sector}::instr:{instr}::sat:all::endtime:latest::daterange:60"
    )
    try:
        r = _get_session().get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        d = r.json()
        return d.get("image_type") or []
    except Exception:
        return []


def volcat_height_at(volcano, dt, radius_deg: float = 0.6) -> Optional[dict]:
    """Reverse-map del colorbar QUEMADO de VOLCAT Ash_Height en el bbox de un
    volcán → altura (km AMSL) como **ground-truth INDICATIVO** para cruzar con
    nuestro retrieval propio.

    HONESTIDAD: es FRÁGIL (±1-2 km extra; depende de la paleta SSEC) y SOLO sirve
    de cross-check de validación, NUNCA como número operacional. Reconstruye el
    valor desde el color del PNG porque SSEC no expone el NetCDF público. Devuelve:
      - dict ``{p95_km, max_km, median_km, n_matched, frame, gap_min}`` si VOLCAT
        SÍ tiene detección de altura en el bbox del volcán;
      - dict ``{"note": ...}`` si no hay frame, el sector es PS (georef no-lineal),
        o **no hay detección de VOLCAT ahí** (común en plumas chilenas finas, que
        caen bajo el umbral de detección de VOLCAT);
      - None si fallan dependencias.

    Solo sectores CE (Chile_North/Central, equatoriales) — georef lineal. Los PS
    (Chile_South) se omiten.
    """
    try:
        import io
        import math

        import numpy as np
        import requests
        from PIL import Image

        from src.process.volcat_colorbar import (build_height_lut,
                                                 extract_rainbow_bar,
                                                 heights_from_plume)
    except Exception:
        logger.exception("volcat_height_at: deps no disponibles")
        return None

    sector, instr = resolve_volcat_sector(volcano)
    vc = volcat_at_time(dt, sector, instr=instr, image_type="Ash_Height",
                        max_gap_min=40)
    if vc is None:
        return {"note": "sin frame VOLCAT Ash_Height en ±40 min"}
    coords = vc["coords"]
    # El API puede devolver frames (endtime) pero sin 'coordinates' (respuesta
    # parcial de SSEC / sector recién creado): coords=None. Degradar a note como
    # el resto de la función, en vez de reventar con AttributeError en coords.get.
    if not coords:
        return {"note": f"sector {sector} sin coordenadas de georef en VOLCAT"}
    if str(coords.get("PROJECTION", "")).upper() == "PS":
        return {"note": f"sector {sector} es PS (georef no-lineal) — omitido"}
    try:
        raw = requests.get(vc["image_url"], timeout=30).content
        im = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        return {"note": f"descarga del frame falló ({e})"}
    W, H = im.size
    a = np.asarray(im).astype("float64")

    # LUT desde el colorbar (strip inferior, mitad derecha = escala de altura).
    strip = a[int(0.935 * H):H, :]
    bar = extract_rainbow_bar(strip[:, int(0.48 * strip.shape[1]):])
    if bar is None:
        return {"note": "no se pudo extraer el colorbar de altura"}
    lut_rgb, lut_val = build_height_lut(bar)

    # Georef CE lineal: pixel del volcán + bbox de ±radius.
    def _nlon(x):
        return x - 360.0 if x > 180.0 else x
    try:
        dp = math.degrees(coords["SCALE_FACTOR"] / coords["EQ_RADIUS"])
        lon0 = _nlon(coords["ORIGIN_LON"]) + coords.get("OFFSET_X", 0) * dp
        lat0 = coords["ORIGIN_LAT"] + coords.get("OFFSET_Y", 0) * dp
    except Exception:
        return {"note": "coords del sector incompletas"}
    row = (lat0 - volcano.lat) / dp
    col = (volcano.lon - lon0) / dp
    rpx = max(4, int(radius_deg / dp))
    r0, r1 = max(0, int(row - rpx)), min(int(0.92 * H), int(row + rpx))
    c0, c1 = max(0, int(col - rpx)), min(W, int(col + rpx))
    if r1 <= r0 or c1 <= c0:
        return {"note": "el volcán cae fuera del sector"}
    box = a[r0:r1, c0:c1]

    # Píxeles candidatos de altura: saturados (arcoíris) y NO la grilla cyan del
    # overlay SSEC. El filtro fino (distancia a la paleta) lo hace heights_from_plume.
    mx, mn = box.max(2), box.min(2)
    with np.errstate(invalid="ignore", divide="ignore"):
        sat = np.where(mx > 0, (mx - mn) / mx, 0.0)
    cyan = (box[:, :, 1] > 150) & (box[:, :, 2] > 150) & (box[:, :, 0] < 120)
    px = box[(sat > 0.35) & ~cyan]
    if len(px) < 3:
        return {"note": "sin detección de altura VOLCAT en el bbox del volcán "
                "(pluma fina bajo el umbral de VOLCAT, o ceniza en otro sitio)"}
    res = heights_from_plume(px, lut_rgb, lut_val)
    if res is None or res["n_matched"] < 3:
        return {"note": "píxeles saturados no matchean la paleta de altura "
                "(probable overlay del mapa, no ceniza)"}
    res.update({"frame": vc.get("datetime"),
                "gap_min": round(vc.get("gap_seconds", 0) / 60.0, 0)})
    return res
