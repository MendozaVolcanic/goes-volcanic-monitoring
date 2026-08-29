"""Exportacion de un frame satelital a archivo desde el encuadre de volcan.

Por que: el tab Volcan de la Vista Operacional ofrecia, por producto, PNG con
timestamp sobre-impreso + GeoTIFF georreferenciado para QGIS. Al migrar a la
grilla compartida quedo solo un PNG compuesto de los 3 productos, y el turno
perdio la via de exportar el encuadre que sirve para analizar un evento.

Dos invariantes se pinean aca:

1. Los helpers de descarga viven en `dashboard/exports.py`, no en una vista.
   Una vista importando de otra vista es lo que ya nos costo una deuda en esta
   misma rama (`zonas_fullscreen` importando de `modo_guardia_volcan`).
2. El RADIO del encuadre queda escrito en el archivo. Con radio ajustable
   (0.35-3 grados) dos capturas del mismo minuto a radios distintos son
   indistinguibles por nombre y por contenido, y estas imagenes terminan en
   informes.
"""
import ast
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

VIEW = (Path(__file__).parent.parent / "dashboard" / "views"
        / "modo_guardia_volcan.py")
LIVE = (Path(__file__).parent.parent / "dashboard" / "views"
        / "live_viewer.py")


# ── 1. El modulo compartido ──────────────────────────────────────────

def test_los_helpers_de_descarga_viven_en_un_modulo_compartido():
    """`dashboard/exports.py` es la unica definicion de los tres helpers."""
    from dashboard import exports

    for nombre in ("img_to_png_bytes", "png_download_button",
                   "download_buttons"):
        assert callable(getattr(exports, nombre, None)), nombre

    # y NO quedaron duplicados en la vista que los tenia
    tree = ast.parse(LIVE.read_text(encoding="utf-8"))
    definidas = {n.name for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef)}
    for nombre in ("_img_to_png_bytes", "_png_download_button",
                   "_download_buttons", "img_to_png_bytes",
                   "png_download_button", "download_buttons"):
        assert nombre not in definidas, f"{nombre} sigue definido en live_viewer"


def test_ninguna_vista_importa_las_descargas_de_otra_vista():
    """La grilla no puede colgarse de live_viewer para bajar un archivo.

    Ese acoplamiento (una vista importando de otra) es el que nos dejo dos
    fuentes de verdad de las recetas de producto en esta misma rama.
    """
    for path in (VIEW, LIVE):
        src = path.read_text(encoding="utf-8")
        assert "views.live_viewer import" not in src, path.name
        assert "views import live_viewer" not in src, path.name


# ── 2. El PNG con label sobre-impreso ────────────────────────────────

def test_el_label_se_imprime_de_verdad_sobre_el_png():
    """El label no es metadata: es una banda pintada al pie de la imagen.

    Se compara pixel a pixel con la misma imagen sin label, porque un PNG
    "valido" sale igual aunque el overlay nunca se dibuje.
    """
    from PIL import Image
    import io

    from dashboard.exports import img_to_png_bytes

    arr = np.full((80, 160, 3), 200, dtype=np.uint8)
    sin = np.array(Image.open(io.BytesIO(img_to_png_bytes(arr))))
    con = np.array(Image.open(io.BytesIO(
        img_to_png_bytes(arr, "Villarrica 12:00 UTC"))))

    assert sin.shape == con.shape == (80, 160, 3)
    # la banda de abajo (label) y la esquina arriba-derecha (marca) cambian;
    # el centro-izquierda de la imagen queda intacto
    assert not np.array_equal(sin[-10:], con[-10:])
    assert not np.array_equal(sin[:20, 100:], con[:20, 100:])
    assert np.array_equal(sin[30:50, :60], con[30:50, :60])


# ── 3. El GeoTIFF del encuadre de volcan ─────────────────────────────

def test_el_geotiff_del_encuadre_de_volcan_queda_georreferenciado():
    """El bbox que se pide tiene que ser el bbox que el archivo declara.

    Se lee el .tif generado con rasterio: si `build_geotiff_bytes` fallara para
    este encuadre (o devolviera bytes vacios), esto es rojo — no queremos
    enterarnos por un boton que baja 0 KB.
    """
    rasterio = pytest.importorskip("rasterio")

    from src.export.geotiff import build_geotiff_bytes

    # Villarrica a radio 0.35 grados, el encuadre por defecto de la grilla
    lat, lon, r = -39.42, -71.93, 0.35
    bounds = {"lat_min": lat - r, "lat_max": lat + r,
              "lon_min": lon - r, "lon_max": lon + r}
    arr = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)

    data = build_geotiff_bytes(arr, bounds, description="test")
    assert data[:2] in (b"II", b"MM"), "no arranca con magic de TIFF"

    with rasterio.io.MemoryFile(data) as mem, mem.open() as ds:
        assert ds.crs.to_string() == "EPSG:4326"
        assert (ds.width, ds.height, ds.count) == (64, 64, 3)
        assert ds.bounds.left == pytest.approx(bounds["lon_min"])
        assert ds.bounds.right == pytest.approx(bounds["lon_max"])
        assert ds.bounds.bottom == pytest.approx(bounds["lat_min"])
        assert ds.bounds.top == pytest.approx(bounds["lat_max"])


# ── 4. Trazabilidad del encuadre ─────────────────────────────────────

def test_el_encuadre_se_lee_distinto_a_radios_distintos():
    """Dos capturas del mismo minuto a radios distintos tienen que
    distinguirse, y no solo por un decimal escondido."""
    from dashboard.views.modo_guardia_volcan import (etiqueta_encuadre,
                                                     sufijo_encuadre)

    assert etiqueta_encuadre(0.35) != etiqueta_encuadre(2.0)
    assert sufijo_encuadre(0.35) != sufijo_encuadre(2.0)
    # el sufijo va en un nombre de archivo: nada de puntos ni signos
    for r in (0.35, 1.0, 2.5):
        s = sufijo_encuadre(r)
        assert all(c.isalnum() or c in "-_" for c in s), s
    # la etiqueta lleva los grados y su equivalente en km (39 km a 0.35 deg)
    assert "0.35" in etiqueta_encuadre(0.35)
    assert "39 km" in etiqueta_encuadre(0.35)


# ── 5. Los botones por producto en la grilla ─────────────────────────

class _StubCtx:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _StubSt:
    """Streamlit minimo: registra expanders y descargas sin runtime."""

    def __init__(self):
        self.expanders = []
        self.downloads = []
        self.captions = []

    def expander(self, label, expanded=False):
        self.expanders.append({"label": label, "expanded": expanded})
        return _StubCtx()

    def caption(self, txt, **kw):
        self.captions.append(txt)

    def markdown(self, txt, **kw):
        self.captions.append(txt)

    def download_button(self, label, **kw):
        self.downloads.append({"label": label, **kw})

    def columns(self, n):
        return [_StubCtx() for _ in range(n)]

    def warning(self, txt):
        self.captions.append(txt)


class _Volcan:
    name = "Villarrica"
    lat = -39.42
    lon = -71.93
    elevation = 2847
    region = "Araucania"


def _grilla_sin_red(monkeypatch, stub_st):
    """Grilla con `fetch_volcan_product` y hot spots mockeados."""
    from dashboard.views import modo_guardia_volcan as MGV

    monkeypatch.setattr(MGV, "st", stub_st)
    monkeypatch.setattr(
        MGV, "fetch_volcan_product",
        lambda pid, *a, **k: (np.zeros((8, 8, 3), dtype=np.uint8),
                              "12:00 UTC"))
    monkeypatch.setattr(MGV, "_hotspots_volcan", lambda *a, **k: ([], None))
    monkeypatch.setattr(MGV, "_wind_at_volcano", lambda *a, **k: {})
    return MGV


def test_la_grilla_ofrece_png_y_geotiff_por_producto_rammb(monkeypatch):
    """Tres productos RAMMB, cada uno con su par de botones, en un expander
    CERRADO (la grilla es para mirar en emergencia; seis botones sueltos le
    comen alto a lo que importa)."""
    stub = _StubSt()
    MGV = _grilla_sin_red(monkeypatch, stub)

    llamadas = []
    monkeypatch.setattr(
        MGV, "download_buttons",
        lambda arr, **kw: llamadas.append(kw))

    MGV._download_expander(_Volcan(), radius_deg=0.35)

    assert stub.expanders and stub.expanders[0]["expanded"] is False
    assert len(llamadas) == 3, llamadas
    ids = [kw["key_prefix"] for kw in llamadas]
    for panel in MGV.GRID_PANELS_TV:
        assert any(panel["id"] in i for i in ids), panel["id"]
    # VOLCAT NO: es un PNG compuesto por SSEC, sin array georreferenciado propio
    assert not any("volcat" in i for i in ids)

    # el bbox que se manda al GeoTIFF es el del encuadre pedido
    b = llamadas[0]["bounds"]
    assert b["lat_min"] == pytest.approx(_Volcan.lat - 0.35)
    assert b["lon_max"] == pytest.approx(_Volcan.lon + 0.35)


def test_el_radio_queda_escrito_en_nombre_y_label_por_producto(monkeypatch):
    stub = _StubSt()
    MGV = _grilla_sin_red(monkeypatch, stub)

    llamadas = []
    monkeypatch.setattr(MGV, "download_buttons",
                        lambda arr, **kw: llamadas.append(kw))

    MGV._download_expander(_Volcan(), radius_deg=0.35)
    MGV._download_expander(_Volcan(), radius_deg=2.0)
    chico, grande = llamadas[0], llamadas[3]

    assert MGV.sufijo_encuadre(0.35) in chico["base_filename"]
    assert MGV.sufijo_encuadre(2.0) in grande["base_filename"]
    assert chico["base_filename"] != grande["base_filename"]

    assert MGV.etiqueta_encuadre(0.35) in chico["label_overlay"]
    assert MGV.etiqueta_encuadre(2.0) in grande["label_overlay"]

    # y las keys de Streamlit tambien, o los dos radios chocan en el mismo widget
    assert chico["key_prefix"] != grande["key_prefix"]


def test_la_grilla_engancha_el_expander_donde_el_boton_de_captura(monkeypatch):
    """El expander cuelga del mismo `enable_capture` que el boton de captura:
    aparece en la Vista Operacional, no en la pared de la sala."""
    from dashboard.views import modo_guardia_volcan as MGV
    src = VIEW.read_text(encoding="utf-8")
    tree = ast.parse(src)
    cuerpo = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "volcan_grid":
            cuerpo = ast.get_source_segment(src, node)
    assert cuerpo and "_download_expander(" in cuerpo
    # dentro del mismo if enable_capture que _capture_button
    bloque = cuerpo.split("if enable_capture:")[1]
    assert "_capture_button(" in bloque and "_download_expander(" in bloque
    assert callable(MGV._download_expander)


# ── 6. El PNG compuesto tambien registra el encuadre ─────────────────

def test_la_captura_compuesta_registra_el_radio(monkeypatch):
    """Nombre de archivo distinto Y pixeles distintos: el radio se dibuja."""
    stub = _StubSt()
    MGV = _grilla_sin_red(monkeypatch, stub)

    MGV._capture_button(_Volcan(), show_wind=False, radius_deg=0.35)
    MGV._capture_button(_Volcan(), show_wind=False, radius_deg=2.0)
    assert len(stub.downloads) == 2
    chico, grande = stub.downloads
    assert chico["file_name"] != grande["file_name"]
    assert MGV.sufijo_encuadre(0.35) in chico["file_name"]
    assert MGV.sufijo_encuadre(2.0) in grande["file_name"]
    # el header impreso tambien cambia (si no, el PNG suelto no dice a que
    # encuadre corresponde)
    assert chico["data"] != grande["data"]
