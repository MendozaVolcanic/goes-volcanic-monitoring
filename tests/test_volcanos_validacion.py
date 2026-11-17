"""Volcanes fuera de Chile usados SOLO para validar la altura propia contra VOLCAT.

Los valores son los del GVP (Smithsonian), consultados el 16-11-2026 por su WFS
oficial; no de memoria. Esta prueba fija que no se cambien sin fuente y que no
entren al catálogo operacional (el dashboard no los muestra).
"""


def test_coordenadas_y_cota_son_las_del_gvp():
    from src.volcanos_validacion import VALIDACION
    esperado = {  # nº GVP: (lat, lon, cota m), WFS GVP-VOTW 16-11-2026
        352010: (-0.077, -77.656, 3562),    # Reventador
        352050: (-0.677, -78.436, 5911),    # Cotopaxi
        354006: (-15.787, -71.857, 5960),   # Sabancaya
    }
    got = {g.gvp: (g.volcano.lat, g.volcano.lon, g.volcano.elevation) for g in VALIDACION.values()}
    assert got == esperado


def test_cada_volcan_cita_su_fuente_y_su_sector_volcat():
    from src.volcanos_validacion import VALIDACION
    for g in VALIDACION.values():
        assert "volcano.si.edu" in g.fuente
        assert g.sector_volcat.endswith("_m")


def test_no_entran_al_catalogo_operacional():
    from src.volcanos import CATALOG
    from src.volcanos_validacion import VALIDACION
    nombres = {v.name for v in CATALOG}
    assert not any(g.volcano.name in nombres for g in VALIDACION.values())
