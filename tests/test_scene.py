"""Tests de la adquisición común de escena (`src/process/scene.py`, ola 2 del
audit ago-2026).

Por qué importan: hasta ahora el preámbulo de adquisición estaba TRIPLICADO en
wen_rose / bt_matching / acha, y con él los **guards de honestidad**. El audit
detectó que el guard de mismo-scan (fix C1, jun-2026) NO tenía test: el fixture
`synthetic_s3` monkeypatchea `_scan_start` a una constante, así que la rama
nunca se ejecutaba. Ahora el guard vive en un solo lugar y se prueba acá.

También se cierra el hueco de orquestación de `bt_matching_top_height` y
`plume_top_height`, que solo se testeaban con volcán inexistente.
"""
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from conftest import COEFS, N, PLUME, SCAN_DT, scene_latlon


# ── Guards de honestidad (el corazón SDA que estaba sin test) ───────────────

def test_scene_same_scan_guard(synthetic_s3, monkeypatch):
    """GUARD DE MISMO-SCAN: si una banda cae en un scan vecino (hueco de S3),
    la escena degrada a no_data en vez de mezclar tiempos.

    Es el guard que el audit ago-2026 encontró SIN test (el fixture pinea
    `_scan_start` a una constante). Un misregistro silencioso se vería como una
    pluma desplazada varios km — peor que no reportar.
    """
    import src.fetch.goes_s3 as goes_s3
    from src.process.scene import acquire_ash_scene

    # C15 llega del scan siguiente (+10 min); C11/C14 del scan de referencia.
    monkeypatch.setattr(
        goes_s3, "_scan_start",
        lambda name: SCAN_DT + timedelta(minutes=10) if "C15" in str(name)
        else SCAN_DT)

    r = acquire_ash_scene(SCAN_DT, "Lascar", radius_deg=0.6, source="test")
    assert isinstance(r, dict), "debería degradar, no devolver escena"
    assert r["status"] == "no_data"
    assert "scans distintos" in r["reason"], r["reason"]
    assert r["scan_dt"] == SCAN_DT       # se reporta el scan ancla igual


def test_scene_same_scan_guard_reaches_all_three_retrievals(synthetic_s3,
                                                            monkeypatch):
    """El guard unificado protege a los TRES retrievals — el punto del refactor:
    antes había que arreglarlo tres veces o quedaba inconsistente."""
    import src.fetch.goes_s3 as goes_s3
    from src.process.bt_matching_height import bt_matching_top_height
    from src.process.wen_rose_height import wen_rose_top_height

    monkeypatch.setattr(
        goes_s3, "_scan_start",
        lambda name: SCAN_DT + timedelta(minutes=10) if "C15" in str(name)
        else SCAN_DT)

    for fn in (wen_rose_top_height, bt_matching_top_height):
        r = fn(SCAN_DT, "Lascar", radius_deg=0.6)
        assert r["status"] == "no_data", (fn.__name__, r["status"])
        assert "scans distintos" in r["reason"], (fn.__name__, r["reason"])


def test_scene_missing_band(synthetic_s3, monkeypatch):
    """Banda ausente en S3 → no_data nombrando la banda (no un crash tardío)."""
    import src.fetch.goes_s3 as goes_s3
    from src.process.scene import acquire_ash_scene

    real = goes_s3.download_band_at
    monkeypatch.setattr(goes_s3, "download_band_at",
                        lambda dt, band, **kw: None if band == 15
                        else real(dt, band, **kw))

    r = acquire_ash_scene(SCAN_DT, "Lascar", radius_deg=0.6, source="test")
    assert r["status"] == "no_data" and r["reason"] == "sin banda C15", r


def test_scene_bbox_off_disk(synthetic_s3, monkeypatch):
    """Bbox fuera del disco visible → no_data explícito."""
    import src.fetch.goes_acha as goes_acha
    from src.process.scene import acquire_ash_scene

    monkeypatch.setattr(goes_acha, "_geos_index_bbox",
                        lambda x, y, bounds, **kw: None)
    r = acquire_ash_scene(SCAN_DT, "Lascar", radius_deg=0.6, source="test")
    assert r["status"] == "no_data" and "fuera del disco" in r["reason"], r


def test_scene_no_profile_still_reports_so2(synthetic_s3, monkeypatch):
    """Sin perfil GFS no hay altura, PERO el contexto de SO₂ ya medido viaja en
    el error: el dashboard puede explicar la escena en vez de quedarse mudo."""
    import src.fetch.gfs_profile as gfs_profile
    from src.process.scene import acquire_ash_scene

    monkeypatch.setattr(gfs_profile, "fetch_gfs_profile",
                        lambda lat, lon, dt=None: None)
    r = acquire_ash_scene(SCAN_DT, "Lascar", radius_deg=0.6, source="test")
    assert r["status"] == "no_data" and "perfil GFS" in r["reason"]
    assert r["so2_px"] == 64 and r["so2_min"] < -9.0, r


def test_scene_unknown_volcano_short_circuits(monkeypatch):
    """Volcán inexistente → no_data ANTES de tocar la red."""
    import src.fetch.goes_s3 as goes_s3
    from src.process.scene import acquire_ash_scene

    def _boom(*a, **kw):
        raise AssertionError("no debería bajar nada")

    monkeypatch.setattr(goes_s3, "download_band_at", _boom)
    r = acquire_ash_scene(SCAN_DT, "NoExisteVolcan", source="test")
    assert r["status"] == "no_data" and "no encontrado" in r["reason"]


# ── Contenido de la escena ──────────────────────────────────────────────────

def test_scene_content_mask_so2_and_coefs(synthetic_s3):
    """La escena entrega máscara, contexto SO₂ y coeficientes Planck POR BANDA
    (si se intercambiaran, la corrección Wen-Rose sería otra física)."""
    from src.process.scene import acquire_ash_scene

    scene = acquire_ash_scene(SCAN_DT, "Lascar", radius_deg=0.6,
                              with_coefs=True, source="test")
    assert not isinstance(scene, dict), scene
    assert int(scene.mask.sum()) == 64                    # el bloque de pluma
    assert scene.so2_px == 64 and abs(scene.so2_min + 10.0) < 0.1
    assert set(scene.bts) == {11, 14, 15}
    for b in (11, 14, 15):
        assert scene.coefs[b] == COEFS[b], b
    assert scene.window == (0, N, 0, N)
    assert scene.profile is not None and scene.scan_dt == SCAN_DT
    assert scene.lat.shape == (N, N) and scene.lon.shape == (N, N)


def test_scene_without_profile_skips_gfs(synthetic_s3, monkeypatch):
    """with_profile=False (el caso ACHA: la altura la pone el L2) no llama GFS."""
    import src.fetch.gfs_profile as gfs_profile
    from src.process.scene import acquire_ash_scene

    def _boom(*a, **kw):
        raise AssertionError("no debería pedir perfil GFS")

    monkeypatch.setattr(gfs_profile, "fetch_gfs_profile", _boom)
    scene = acquire_ash_scene(SCAN_DT, "Lascar", radius_deg=0.6,
                              with_profile=False, source="test")
    assert not isinstance(scene, dict) and scene.profile is None


def test_scene_respects_caller_window(synthetic_s3, monkeypatch):
    """Con ``window``/``ref_dt`` impuestos (caso ACHA) NO se deriva la ventana
    de la banda ancla: la grilla la fija el producto L2."""
    import src.fetch.goes_acha as goes_acha
    from src.process.scene import acquire_ash_scene

    def _boom(*a, **kw):
        raise AssertionError("no debería recalcular la ventana geos")

    monkeypatch.setattr(goes_acha, "_geos_index_bbox", _boom)
    lat2d, lon2d = scene_latlon()
    scene = acquire_ash_scene(
        SCAN_DT, "Lascar", 0.6, with_profile=False, source="test",
        window=(0, N, 0, N), ref_dt=SCAN_DT, latlon=(lat2d, lon2d))
    assert not isinstance(scene, dict) and int(scene.mask.sum()) == 64
    assert scene.scan_dt == SCAN_DT


# ── Orquestación end-to-end de los retrievals que no la tenían ──────────────

def test_bt_matching_orchestration_end_to_end(synthetic_s3):
    """Hueco del audit: `bt_matching_top_height` solo se probaba con volcán
    inexistente. Sobre la escena sintética debe detectar la pluma y dar la
    **cota inferior** — por debajo del Tc verdadero (228 K ≈ 9.2 km), porque el
    satélite ve el suelo cálido a través de la pluma semitransparente."""
    from src.process.bt_matching_height import bt_matching_top_height

    r = bt_matching_top_height(SCAN_DT, "Lascar", radius_deg=0.6)
    assert r["status"] == "ok", r.get("reason")
    assert r["mask_px"] == 64
    assert 0.1 < r["top_km"] < 9.2, r["top_km"]      # cota: NO llega al tope real
    assert r["n_capped"] == 0 and r["all_capped"] is False
    assert r["so2_px"] == 64
    assert r["tropopause_km"] == 12.0
    assert np.isfinite(r["field_km"][PLUME]).all()
    # fuera de la pluma no hay altura (la máscara no marcó nada)
    assert np.isnan(r["field_km"][0, 0])


def test_bt_matching_is_lower_bound_of_wen_rose(synthetic_s3):
    """Coherencia física entre los dos retrievals que comparten escena:
    Wen-Rose corrige la semitransparencia hacia ARRIBA, así que su tope debe
    quedar por encima del BT-matching sobre los MISMOS píxeles."""
    from src.process.bt_matching_height import bt_matching_top_height
    from src.process.wen_rose_height import wen_rose_top_height

    bt = bt_matching_top_height(SCAN_DT, "Lascar", radius_deg=0.6)
    wr = wen_rose_top_height(SCAN_DT, "Lascar", radius_deg=0.6)
    assert bt["status"] == "ok" and wr["status"] == "ok"
    assert bt["mask_px"] == wr["mask_px"] == 64
    # el BT-matching que Wen-Rose calcula internamente es EL MISMO producto
    assert abs(wr["top_bt_matching_km"] - bt["top_km"]) < 1e-9
    assert wr["top_km"] > bt["top_km"]


def test_acha_plume_top_orchestration_end_to_end(synthetic_s3, monkeypatch):
    """Hueco del audit: `plume_top_height` tampoco tenía test de orquestación.
    Con un gránulo ACHA sintético a 9 km, la intersección con NUESTRA máscara
    debe dar 9 km sobre los 64 píxeles de pluma."""
    import src.fetch.goes_acha as goes_acha
    from src.process.acha_plume_height import plume_top_height

    lat2d, lon2d = scene_latlon()
    monkeypatch.setattr(goes_acha, "fetch_acha_height_at",
                        lambda dt, bounds, **kw: {
                            "window": (0, N, 0, N),
                            "height_m": np.full((N, N), 9000.0),
                            "lat": lat2d, "lon": lon2d,
                            "scan_dt": SCAN_DT,
                            "product": "ABI-L2-ACHA2KMF"})

    r = plume_top_height(SCAN_DT, "Lascar", radius_deg=0.6)
    assert r["status"] == "ok", r.get("reason")
    assert r["mask_px"] == 64
    assert abs(r["top_km"] - 9.0) < 1e-6 and abs(r["top_max_km"] - 9.0) < 1e-6
    assert r["so2_px"] == 64                       # contexto de gas presente
    assert r["product"] == "ABI-L2-ACHA2KMF"
    assert "tropopause_km" not in r                # ACHA no usa perfil GFS


def test_acha_undated_granule_refuses(synthetic_s3, monkeypatch):
    """Sin timestamp del gránulo ACHA no se puede garantizar el mismo scan →
    no_data (mejor nada que una intersección desalineada)."""
    import src.fetch.goes_acha as goes_acha
    from src.process.acha_plume_height import plume_top_height

    lat2d, lon2d = scene_latlon()
    monkeypatch.setattr(goes_acha, "fetch_acha_height_at",
                        lambda dt, bounds, **kw: {
                            "window": (0, N, 0, N),
                            "height_m": np.full((N, N), 9000.0),
                            "lat": lat2d, "lon": lon2d,
                            "scan_dt": None, "product": "ABI-L2-ACHA2KMF"})

    r = plume_top_height(SCAN_DT, "Lascar", radius_deg=0.6)
    assert r["status"] == "no_data" and "datar" in r["reason"], r
