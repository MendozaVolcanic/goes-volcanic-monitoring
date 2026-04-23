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


def volcat_latest(
    sector: str,
    instr: str = "ABI",
    image_type: str = "Ash_Height",
    sat: str = "all",
) -> Optional[dict]:
    """Consulta el API y devuelve el frame mas reciente disponible.

    Returns:
        dict con keys: datetime, image_url, legend_url, annot_url, coords.
        None si no hay frames o falla el request.
    """
    url = (
        f"{BASE}/imagery/get_list/json/"
        f"sector:{sector}::instr:{instr}::sat:{sat}"
        f"::image_type:{image_type}::endtime:latest::daterange:180"
    )
    try:
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            logger.warning("VOLCAT API %s -> %s", url, r.status_code)
            return None
        d = r.json()
    except Exception as e:
        logger.warning("VOLCAT API fail: %s", e)
        return None

    frames = d.get("endtime") or []
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
        "coords": d.get("coordinates"),
        "sector": sector,
        "instr": instr,
        "image_type": image_type,
        "sat": last.get("filename", "").split("/")[-1].split(".")[0] if last.get("filename") else None,
    }


def volcat_available_types(sector: str, instr: str = "ABI") -> list[str]:
    """Lista productos image_type disponibles para un sector."""
    url = (
        f"{BASE}/imagery/get_list/json/"
        f"sector:{sector}::instr:{instr}::sat:all::endtime:latest::daterange:60"
    )
    try:
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        d = r.json()
        return d.get("image_type") or []
    except Exception:
        return []
