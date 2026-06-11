"""Cliente del API VOLCAT (CIMSS/SSEC) para altura de pluma volcanica.

Endpoint unico: GET {BASE}/imagery/get_list/json/sector:X::instr:Y::...

Devuelve PNG color-codificado de Ash Height (altitud km), Ash Loading (g/m^2),
Ash Probability y Ash Reff. Sin autenticacion, gratis, cadencia ABI 10 min.

Documentacion completa en docs/altura_pluma/VOLCAT_api_reference.md
"""

from __future__ import annotations

import logging
from typing import Optional

import requests
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
    "Sur":     ("Chile_South_2_km",   "ABI"),
    "Austral": ("Chile_South_2_km",   "ABI"),  # mismo sector, recorte austral
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


def _query_frames(sector: str, instr: str, image_type: str, sat: str) -> list:
    """Helper: pega al API VOLCAT y devuelve la lista de frames (puede vacia)."""
    url = (
        f"{BASE}/imagery/get_list/json/"
        f"sector:{sector}::instr:{instr}::sat:{sat}"
        f"::image_type:{image_type}::endtime:latest::daterange:180"
    )
    try:
        r = _get_session().get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            logger.warning("VOLCAT API %s -> %s", url, r.status_code)
            return []
        d = r.json()
    except Exception as e:
        logger.warning("VOLCAT API fail: %s", e)
        return []
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
