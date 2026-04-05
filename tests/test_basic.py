"""Tests básicos para verificar la infraestructura del proyecto."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Verificar que todos los módulos se importan correctamente."""
    from src.config import GOES_BUCKET, VOLCANIC_BANDS, ASH_RGB, CHILE_BOUNDS
    from src.volcanos import CATALOG, get_volcano, get_priority
    from src.process.brightness_temp import rad_to_bt
    from src.process.ash_rgb import generate_ash_rgb, normalize
    from src.process.ash_detection import detect_ash_basic, detect_ash_enhanced
    from src.process.geo import get_lat_lon


def test_config():
    """Verificar configuración."""
    from src.config import GOES_BUCKET, VOLCANIC_BANDS, ASH_RGB

    assert GOES_BUCKET == "noaa-goes19"
    assert 14 in VOLCANIC_BANDS
    assert 15 in VOLCANIC_BANDS
    assert 11 in VOLCANIC_BANDS
    assert "red" in ASH_RGB
    assert "green" in ASH_RGB
    assert "blue" in ASH_RGB


def test_volcano_catalog():
    """Verificar catálogo de volcanes."""
    from src.volcanos import CATALOG, get_volcano, get_by_zone, get_priority

    assert len(CATALOG) == 43

    # Verificar volcán conocido
    villarrica = get_volcano("Villarrica")
    assert villarrica is not None
    assert villarrica.lat == -39.42
    assert villarrica.lon == -71.93
    assert villarrica.elevation == 2847

    # Verificar zonas
    norte = get_by_zone("norte")
    assert len(norte) > 0
    assert all(v.zone == "norte" for v in norte)

    # Volcanes prioritarios
    priority = get_priority()
    assert len(priority) == 8
    names = [v.name for v in priority]
    assert "Villarrica" in names
    assert "Láscar" in names


def test_ash_rgb_normalize():
    """Verificar normalización para Ash RGB."""
    import numpy as np
    from src.process.ash_rgb import normalize

    data = np.array([-6.7, 0.0, 2.6, -10.0, 5.0])
    result = normalize(data, -6.7, 2.6)

    assert result[0] == 0.0   # min
    assert result[2] == 1.0   # max
    assert result[3] == 0.0   # clipped below
    assert result[4] == 1.0   # clipped above
    assert 0 < result[1] < 1  # mid value


def test_chile_bounds():
    """Verificar que bounds cubren todo Chile."""
    from src.config import CHILE_BOUNDS
    from src.volcanos import CATALOG

    for v in CATALOG:
        assert CHILE_BOUNDS["lat_min"] <= v.lat <= CHILE_BOUNDS["lat_max"], \
            f"{v.name} lat {v.lat} fuera de bounds"
        assert CHILE_BOUNDS["lon_min"] <= v.lon <= CHILE_BOUNDS["lon_max"], \
            f"{v.name} lon {v.lon} fuera de bounds"


if __name__ == "__main__":
    test_imports()
    test_config()
    test_volcano_catalog()
    test_ash_rgb_normalize()
    test_chile_bounds()
    print("All tests passed!")
