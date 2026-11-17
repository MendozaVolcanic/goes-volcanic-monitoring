"""Volcanes fuera de Chile usados SOLO para validar la altura propia contra VOLCAT.

Por qué existen: en las plumas chilenas finas VOLCAT casi nunca dibuja nada, así
que la magnitud de la altura propia se valida en plumas densas de Ecuador y Perú
que VOLCAT sí mide (docs/own_volcat/PLAN_VALIDACION_MAGNITUD.md, paso 2). Para
anclar el objeto VOLCAT al volcán hace falta su coordenada real: en los sectores
dedicados el volcán NO está en el centro del cuadro (Reventador a ~5 km, Sabancaya
a ~10 km del centro).

Fuente: Global Volcanism Program (Smithsonian), servicio WFS oficial
GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes, consultado el 16-11-2026. Coinciden
con la exportación GVP local de openVIS-code/cfg/volcanoes.csv.

No entran al CATALOG operacional: el dashboard no los muestra.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.volcanos import Volcano

_WFS = ("https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows "
        "(Smithsonian_VOTW_Holocene_Volcanoes), consultado 16-11-2026")


@dataclass(frozen=True)
class VolcanValidacion:
    volcano: Volcano
    gvp: int             # número de volcán del GVP
    sector_volcat: str   # sector dedicado de VOLCAT que lo contiene
    fuente: str


def _gvp(n: int) -> str:
    return f"https://volcano.si.edu/volcano.cfm?vn={n} · {_WFS}"


VALIDACION = {
    "Reventador": VolcanValidacion(
        Volcano("Reventador", -0.077, -77.656, 3562, "Ecuador", "validacion", 0),
        352010, "Reventador_250_m", _gvp(352010)),
    "Cotopaxi": VolcanValidacion(
        Volcano("Cotopaxi", -0.677, -78.436, 5911, "Ecuador", "validacion", 0),
        352050, "Cotopaxi_150_m", _gvp(352050)),
    "Sabancaya": VolcanValidacion(
        Volcano("Sabancaya", -15.787, -71.857, 5960, "Peru", "validacion", 0),
        354006, "Sabancaya_250_m", _gvp(354006)),
}
