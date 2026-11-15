"""Lo que el dashboard vuelve a bajar en cada ciclo de 10 minutos.

Por qué importa, antes que el cómo: cada scan GOES-19 Full Disk se publica una
sola vez y no cambia después. Un tile RAMMB lleva el timestamp del scan en la
URL; un gránulo FDCF lleva el inicio del scan en el nombre. Bajarlos de nuevo
no trae información nueva: sólo gasta red, demora los paneles y, en la sala que
se proyecta 24/7, hace que la rotación pierda ticks porque cada uno tarda más
que su período. Medido en nov-2026: Modo Guardia hacía unas 850 peticiones por
ciclo, y 560 de los 739 pedidos de tiles terminaban en 404.

Cuatro causas, una prueba (o un grupo) por causa:

1. Ash RGB y SO2 se piden en zoom 4, que RAMMB NO publica para esos productos.
   No es una falla intermitente: el RGB se arma con bandas IR de 2 km, y la
   configuración del propio Slider (`define-products.js`, goes-19 full_disk)
   declara `max_zoom_level` 5 con `zoom_level_adjust` 2 para `eumetsat_ash` y
   `jma_so2`, o sea zoom máximo 3. GeoColor (banda 2 de 0,5 km) llega a 5.
2. Los tiles inmutables no se memorizaban: cada tick los bajaba de nuevo.
3. El mismo FDCF se bajaba una vez por zona y otra por volcán.
4. Modo Guardia y Vista Operacional ejecutaban todas sus pestañas, aunque se
   viera una sola (`st.tabs` no difiere nada por defecto).

Lo que estas pruebas cuidan además: memorizar NUNCA puede convertir una falla
en dato. Un 404 o un error de red no se guarda (el próximo tick vuelve a
intentar), y un FDCF memorizado no salva un listado que falló: si S3 no
contesta, la vista sigue sabiendo que el scan no es verificable.
"""
from __future__ import annotations

import ast
import contextlib
import io
import sys
import threading
import time
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.fetch import rammb_slider as RS  # noqa: E402

TS_NUEVO = "20261115131021"
TS_PREVIO = "20261115130021"
VILLARRICA = {"lat_min": -39.42 - 0.35, "lat_max": -39.42 + 0.35,
              "lon_min": -71.93 - 0.35, "lon_max": -71.93 + 0.35}


def _png(lado: int = 512) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (lado, lado), (120, 40, 200)).save(buf, format="PNG")
    return buf.getvalue()


class _Resp:
    def __init__(self, status: int, content: bytes = b""):
        self.status_code = status
        self.content = content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _RammbFalso:
    """Sesión HTTP que imita al Slider: zoom 4 de Ash/SO2 es 404, como en vivo.

    `respuestas` permite forzar, por URL completa, una secuencia de estados
    (para simular un 404 o un error de red que se arregla en el tick siguiente).
    """

    MAX_ZOOM_REAL = {"eumetsat_ash": 3, "jma_so2": 3, "geocolor": 5}

    def __init__(self):
        self.urls: list[str] = []
        self.forzadas: dict[str, list] = {}
        self._png = _png()
        self._lock = threading.Lock()

    def get(self, url, **kw):
        with self._lock:
            self.urls.append(url)
            cola = self.forzadas.get(url)
            forzada = cola.pop(0) if cola else None
        if isinstance(forzada, Exception):
            raise forzada
        if forzada is not None:
            return _Resp(forzada, self._png if forzada == 200 else b"")
        partes = url.split("/")
        producto, zoom = partes[-4], int(partes[-2])
        if zoom > self.MAX_ZOOM_REAL.get(producto, 5):
            return _Resp(404)
        return _Resp(200, self._png)

    def tiles(self) -> list[str]:
        return [u for u in self.urls if "/imagery/" in u]


@pytest.fixture()
def rammb(monkeypatch):
    s = _RammbFalso()
    monkeypatch.setattr(RS, "_get_session", lambda *a, **k: s)
    return s


# ── 1. Zoom por producto ─────────────────────────────────────────────────

def test_zoom_maximo_por_producto_sale_de_la_resolucion_de_sus_bandas():
    """Ash y SO2 (bandas IR de 2 km) topan en zoom 3; GeoColor no se recorta."""
    assert RS.zoom_efectivo("eumetsat_ash", 4) == 3
    assert RS.zoom_efectivo("jma_so2", 4) == 3
    assert RS.zoom_efectivo("geocolor", 4) == 4
    # Pedir menos que el máximo nunca se toca: el zoom 2 de Chile sigue en 2.
    assert RS.zoom_efectivo("eumetsat_ash", 2) == 2
    # Producto desconocido: no se inventa un tope.
    assert RS.zoom_efectivo("producto_nuevo", 4) == 4


def test_ash_y_so2_nunca_piden_un_zoom_que_rammb_no_publica(rammb):
    """La cadena de 404 desaparece: ni un solo pedido a zoom 4 para Ash/SO2."""
    for producto in ("eumetsat_ash", "jma_so2"):
        img, ts, zoom = RS.fetch_frame_robust(
            producto, [TS_NUEVO, TS_PREVIO], VILLARRICA,
            zoom_preferred=RS.ZOOM_VOLCAN, zoom_fallback=RS.ZOOM_ZONE)
        assert img is not None
        assert ts == TS_NUEVO, "con el zoom correcto el scan más nuevo carga"
        assert zoom == 3
    pedidos_z4 = [u for u in rammb.tiles() if "/04/" in u]
    assert pedidos_z4 == [], f"{len(pedidos_z4)} tiles a zoom 4 que siempre son 404"


def test_geocolor_sigue_en_zoom_4(rammb):
    """El recorte es por producto: GeoColor no pierde resolución."""
    img, ts, zoom = RS.fetch_frame_robust(
        "geocolor", [TS_NUEVO], VILLARRICA,
        zoom_preferred=RS.ZOOM_VOLCAN, zoom_fallback=RS.ZOOM_ZONE)
    assert img is not None and zoom == 4
    assert all("/04/" in u for u in rammb.tiles())


def test_un_pedido_directo_de_ash_a_zoom_4_tambien_carga(rammb):
    """`fetch_frame_for_bounds` sin fallback (loops, timeseries) devolvía None
    para Ash a zoom 4: el loop quedaba vacío en vez de bajar un nivel."""
    img = RS.fetch_frame_for_bounds("eumetsat_ash", TS_NUEVO, VILLARRICA,
                                    zoom=RS.ZOOM_VOLCAN)
    assert img is not None
    assert not [u for u in rammb.tiles() if "/04/" in u]


# ── 2. Tiles memorizados ─────────────────────────────────────────────────

def test_el_mismo_tile_no_se_baja_dos_veces(rammb):
    """Dos ticks seguidos con el mismo scan: la segunda vez no sale a la red."""
    RS.fetch_frame_robust("eumetsat_ash", [TS_NUEVO], VILLARRICA,
                          zoom_preferred=RS.ZOOM_VOLCAN,
                          zoom_fallback=RS.ZOOM_ZONE)
    primera = len(rammb.tiles())
    assert primera > 0
    img, _, _ = RS.fetch_frame_robust("eumetsat_ash", [TS_NUEVO], VILLARRICA,
                                      zoom_preferred=RS.ZOOM_VOLCAN,
                                      zoom_fallback=RS.ZOOM_ZONE)
    assert img is not None
    assert len(rammb.tiles()) == primera, "el tick repetido volvió a bajar tiles"


def test_un_scan_nuevo_si_se_baja(rammb):
    """La clave incluye el timestamp: memorizar no puede congelar la imagen."""
    RS.fetch_frame_for_bounds("geocolor", TS_PREVIO, VILLARRICA, zoom=3)
    antes = len(rammb.tiles())
    RS.fetch_frame_for_bounds("geocolor", TS_NUEVO, VILLARRICA, zoom=3)
    nuevos = rammb.tiles()[antes:]
    assert nuevos and all(TS_NUEVO in u for u in nuevos)


@pytest.mark.parametrize("falla", [404, ConnectionError("RAMMB no contestó")])
def test_una_falla_no_queda_memorizada(rammb, falla):
    """Un 404 o un error de red se reintenta en el tick siguiente.

    Si se memorizara, un tropiezo de RAMMB dejaría el panel en el scan anterior
    (o en negro) durante toda la vida del caché, aunque el tile ya exista.
    """
    rows, cols = RS.get_tiles_for_bounds(VILLARRICA, 3)
    url = (f"{RS.BASE_URL}/data/imagery/2026/11/15/goes-19---full_disk/"
           f"geocolor/{TS_NUEVO}/03/{rows[0]:03d}_{cols[0]:03d}.png")
    rammb.forzadas[url] = [falla]
    assert RS.fetch_tile("geocolor", TS_NUEVO, 3, rows[0], cols[0]) is None
    tile = RS.fetch_tile("geocolor", TS_NUEVO, 3, rows[0], cols[0])
    assert tile is not None, "la falla del primer intento quedó pegada"
    assert rammb.urls.count(url) == 2


def test_dos_hilos_que_piden_el_mismo_tile_lo_bajan_una_vez(monkeypatch):
    """El productor de la sala y un fragment arrancan juntos con caché frío."""
    llamadas = []
    png = _png(64)

    class _Lenta:
        def get(self, url, **kw):
            llamadas.append(url)
            time.sleep(0.2)
            return _Resp(200, png)

    monkeypatch.setattr(RS, "_get_session", lambda *a, **k: _Lenta())
    hilos = [threading.Thread(target=RS.fetch_tile,
                              args=("geocolor", TS_NUEVO, 3, 5, 3))
             for _ in range(4)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert len(llamadas) == 1


def test_el_cache_de_tiles_tiene_techo_de_memoria():
    """Un servidor 24/7 no puede acumular tiles sin límite."""
    from src.fetch.cache_inmutable import CacheInmutable
    c = CacheInmutable("prueba", max_bytes=1000)
    for i in range(10):
        c.obtener(i, lambda: b"x" * 300)
    assert c.stats()["bytes"] <= 1000
    # Lo más reciente sobrevive; lo más viejo salió.
    assert c.obtener(9, lambda: pytest.fail("el último debía seguir")) == b"x" * 300


# ── 3. Un FDCF por scan, no uno por zona ─────────────────────────────────

from tests.test_fdcf_contract import (  # noqa: E402
    BOX_CON_HOTSPOT, BOX_SIN_HOTSPOT, KEY, SCAN_DT, _fdcf_ds)

ZONAS = [BOX_CON_HOTSPOT, BOX_SIN_HOTSPOT,
         {"lat_min": -46.0, "lat_max": -41.0, "lon_min": -75.0, "lon_max": -71.0},
         {"lat_min": -24.0, "lat_max": -17.0, "lon_min": -70.0, "lon_max": -66.0}]


class _S3Contador:
    def __init__(self, keys=(KEY,)):
        self.keys = list(keys)
        self.abiertos: list[str] = []
        self.ls_exc = None

    def ls(self, prefix, **kw):
        if self.ls_exc is not None:
            raise self.ls_exc
        return list(self.keys)

    def open(self, key, mode="rb", **kw):
        self.abiertos.append(key)
        return contextlib.nullcontext(io.BytesIO(b"granulo-fdcf"))


@pytest.fixture()
def fdcf(monkeypatch):
    import xarray as xr

    import src.fetch.goes_fdcf as mod
    ds = _fdcf_ds()
    monkeypatch.setattr(xr, "open_dataset", lambda f, **kw: ds)
    s3 = _S3Contador()
    monkeypatch.setattr(mod, "_get_s3", lambda *a, **k: s3)
    return mod, s3


def test_cuatro_zonas_leen_un_solo_fdcf(fdcf):
    """Sala y Guardia piden hot spots por zona y por volcán: un GET por scan."""
    mod, s3 = fdcf
    resultados = [mod.fetch_latest_hotspots(bounds=b) for b in ZONAS]
    assert s3.abiertos == [KEY], f"{len(s3.abiertos)} descargas del mismo gránulo"
    # Y el recorte por zona sigue siendo el de cada zona.
    assert len(resultados[0][0]) == 1 and resultados[0][1] == SCAN_DT
    assert resultados[1] == ([], SCAN_DT)


def test_un_fdcf_nuevo_si_se_baja(fdcf):
    mod, s3 = fdcf
    mod.fetch_latest_hotspots(bounds=BOX_CON_HOTSPOT)
    nuevo = KEY.replace("s20261151200216", "s20261151210216")
    s3.keys = [nuevo, KEY]
    mod.fetch_latest_hotspots(bounds=BOX_CON_HOTSPOT)
    assert s3.abiertos == [KEY, nuevo]


def test_fdcf_memorizado_no_tapa_un_listado_caido(fdcf):
    """Ausencia de dato no es calma: con S3 caído el scan NO es verificable,
    aunque el gránulo anterior siga en memoria."""
    mod, s3 = fdcf
    assert mod.fetch_latest_hotspots(bounds=BOX_CON_HOTSPOT)[1] == SCAN_DT
    s3.ls_exc = OSError("S3 unreachable")
    assert mod.fetch_latest_hotspots(bounds=BOX_CON_HOTSPOT) == ([], None)


def test_el_historico_comparte_el_mismo_cache(fdcf):
    """`fetch_hotspots_at_time` (backfill, Evento) usa el mismo camino."""
    mod, s3 = fdcf
    mod.fetch_latest_hotspots(bounds=BOX_CON_HOTSPOT)
    hs, dt = mod.fetch_hotspots_at_time(SCAN_DT, bounds=BOX_SIN_HOTSPOT)
    assert dt == SCAN_DT
    assert s3.abiertos == [KEY]


# ── 4. Pestañas perezosas ────────────────────────────────────────────────

def _llamadas_tabs(fuente: str):
    arbol = ast.parse(fuente)
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "tabs"
                and isinstance(nodo.func.value, ast.Name)
                and nodo.func.value.id == "st"):
            yield nodo


def _nombres_en(expr) -> set[str]:
    return {n.id for n in ast.walk(expr) if isinstance(n, ast.Name)}


def _objetivos(t) -> set[str]:
    return {n.id for n in ast.walk(t) if isinstance(n, ast.Name)}


def _with_de_pestanas(fuente: str):
    """Cada `with <pestaña>:` del módulo.

    Pestaña = nombre que sale de `st.tabs`/`pestanas_perezosas`, o que se deriva
    de uno (el `dict(zip(...))` de sub-pestañas, `sub_tabs[prod]`, el `for` que
    las recorre). Se propaga hasta punto fijo: así la prueba sigue a la pestaña
    aunque el código la pase por un diccionario, que es justo como live_viewer
    arma sus sub-pestañas por producto.
    """
    arbol = ast.parse(fuente)
    nombres: set[str] = set()
    asignaciones = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Assign):
            asignaciones.append((nodo.targets, nodo.value))
            f = nodo.value.func if isinstance(nodo.value, ast.Call) else None
            es_tabs = ((isinstance(f, ast.Attribute) and f.attr == "tabs")
                       or (isinstance(f, ast.Name)
                           and f.id == "pestanas_perezosas"))
            if es_tabs:
                for t in nodo.targets:
                    nombres |= _objetivos(t)
        elif isinstance(nodo, ast.For):
            asignaciones.append(([nodo.target], nodo.iter))
    assert nombres, "no encontré ninguna pestaña: la prueba quedaría vacía"
    cambio = True
    while cambio:
        cambio = False
        for targets, valor in asignaciones:
            if _nombres_en(valor) & nombres:
                nuevos = set().union(*(_objetivos(t) for t in targets)) - nombres
                if nuevos:
                    nombres |= nuevos
                    cambio = True
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.With):
            for item in nodo.items:
                ctx = item.context_expr
                if isinstance(ctx, ast.Name) and ctx.id in nombres:
                    yield ctx.id, nodo
                elif (isinstance(ctx, ast.Subscript)
                      and _nombres_en(ctx.value) & nombres):
                    # `with sub_tabs[prod]:` no se puede guardar por nombre:
                    # se reporta como pestaña sin guardia.
                    yield "<subíndice>", nodo


@pytest.mark.parametrize("modulo", ["dashboard/views/modo_guardia.py",
                                    "dashboard/views/live_viewer.py"])
def test_las_pestanas_son_perezosas(modulo):
    """Ninguna `st.tabs` ansiosa: todas pasan por `pestanas_perezosas`."""
    fuente = (ROOT / modulo).read_text(encoding="utf-8")
    ansiosas = [n.lineno for n in _llamadas_tabs(fuente)]
    assert ansiosas == [], (
        f"{modulo}: st.tabs en líneas {ansiosas} ejecuta TODAS las pestañas en "
        "cada rerun; usar dashboard.pestanas.pestanas_perezosas")


@pytest.mark.parametrize("modulo", ["dashboard/views/modo_guardia.py",
                                    "dashboard/views/live_viewer.py"])
def test_cada_pestana_corre_solo_si_esta_abierta(modulo):
    """Con pestañas que llevan estado, el contenido de una oculta se salta.

    El `with` de cada pestaña tiene que empezar con `if <pestaña>.open` (o
    `if visible(<pestaña>)`). Sin eso la pestaña perezosa sigue corriendo
    entera: el `on_change` sólo agrega un rerun por clic, no ahorra nada.
    """
    fuente = (ROOT / modulo).read_text(encoding="utf-8")
    sin_guardia = []
    vistos = 0
    for nombre, nodo in _with_de_pestanas(fuente):
        vistos += 1
        primero = nodo.body[0]
        # La guardia tiene que mirar el estado abierto: `visible(x)` o `x.open`.
        ok = isinstance(primero, ast.If) and nombre in _nombres_en(primero.test) \
            and ("visible" in _nombres_en(primero.test)
                 or any(isinstance(n, ast.Attribute) and n.attr == "open"
                        for n in ast.walk(primero.test)))
        if not ok:
            sin_guardia.append(f"{nombre} (línea {nodo.lineno})")
    assert vistos, f"{modulo}: no hay ningún `with <pestaña>`"
    assert sin_guardia == [], f"{modulo}: pestañas sin guardia: {sin_guardia}"


def test_visible_distingue_oculta_de_sin_estado():
    """`.open` es None si las pestañas no llevan estado: entonces se corre todo
    (comportamiento viejo), nunca se esconde contenido por error."""
    from dashboard.pestanas import visible

    class _T:
        def __init__(self, open_):
            self.open = open_

    assert visible(_T(True)) is True
    assert visible(_T(None)) is True
    assert visible(_T(False)) is False


# ── 5. "Zoom reducido" sólo cuando de verdad se degradó ──────────────────

def test_zoom_reducido_se_mide_contra_lo_que_el_producto_publica():
    """Ash a zoom 3 es su resolución máxima: no es una degradación. GeoColor a
    zoom 3 sí lo es (debió venir a 4). Sin esto, el aviso "⚠ zoom reducido"
    quedaba encendido permanente en Ash y SO2 y nadie lo leía."""
    assert RS.zoom_reducido("eumetsat_ash", 3, RS.ZOOM_VOLCAN) is False
    assert RS.zoom_reducido("jma_so2", 3, RS.ZOOM_VOLCAN) is False
    assert RS.zoom_reducido("geocolor", 3, RS.ZOOM_VOLCAN) is True
    assert RS.zoom_reducido("geocolor", 4, RS.ZOOM_VOLCAN) is False
    assert RS.zoom_reducido("eumetsat_ash", 2, RS.ZOOM_VOLCAN) is True


# ── 6. Modo Sala no reenvía el mismo PNG por websocket ───────────────────

def test_la_sala_sirve_el_png_por_url_y_no_en_base64(monkeypatch):
    """El slot de 4 zonas y el zoom de volcán se proyectan 24/7 y se repiten en
    cada vuelta de la rotación. En base64 dentro del HTML, cada aparición
    reenviaba el PNG entero (~1 MB) por el websocket: medido en nov-2026, 99,6
    MB por ciclo de 10 min en tv=1, más de la mitad repetidos. Por `st.image`
    viaja una URL `/media/<hash>`; el mismo PNG da la misma URL y el navegador
    no lo vuelve a bajar.
    """
    from dashboard.views import zonas_fullscreen as ZF
    llamadas = {"image": [], "markdown": []}
    monkeypatch.setattr(ZF.st, "image",
                        lambda img, *a, **k: llamadas["image"].append(img))
    monkeypatch.setattr(ZF.st, "markdown",
                        lambda body, *a, **k: llamadas["markdown"].append(body))
    monkeypatch.setattr(ZF.st, "container",
                        lambda *a, **k: contextlib.nullcontext())
    png = _png(32)
    ZF._emit_tv_png(png)
    assert llamadas["image"] == [png]
    assert not any("base64" in m for m in llamadas["markdown"]), (
        "el PNG volvió a viajar inline en el HTML")


def test_la_pestana_elegida_sobrevive_a_un_rerun_lanzado_desde_un_fragment(monkeypatch):
    """Defecto de Streamlit 1.56, reproducido en una app mínima (nov-2026): con
    `on_change="rerun"`, un `st.rerun(scope="app")` llamado desde un fragment
    corre con la pestaña VUELTA a la primera. Vista Operacional hace justo eso
    en `_health_banner` con cada scan nuevo: el turno que miraba "Volcán" caía
    a "Nacional" cada 10 minutos, o veía la pestaña elegida en blanco.

    El arreglo: la elección se guarda en una clave propia (no de widget) desde
    el callback del clic, y vuelve como `default`. En la reproducción, 0 de 30
    reruns lanzados desde el fragment perdieron la pestaña.
    """
    from dashboard import pestanas as P

    estado: dict = {}
    llamadas: list = []

    def tabs_falso(etiquetas, **kw):
        llamadas.append(kw)
        return [object() for _ in etiquetas]

    monkeypatch.setattr(P.st, "session_state", estado)
    monkeypatch.setattr(P.st, "tabs", tabs_falso)

    etiquetas = ["Nacional", "Zona", "Volcán"]
    P.pestanas_perezosas(etiquetas, key="op_tab")
    assert llamadas[-1]["default"] is None
    assert callable(llamadas[-1]["on_change"]), (
        "sin callback no hay dónde guardar la elección del operador")

    # El operador hace clic en "Volcán": Streamlit deja el valor en la key del
    # widget y llama al callback antes del rerun.
    estado["op_tab"] = "Volcán"
    llamadas[-1]["on_change"]()
    # El rerun que dispara el fragment trae el widget en su valor por defecto.
    estado.pop("op_tab")
    P.pestanas_perezosas(etiquetas, key="op_tab")
    assert llamadas[-1]["default"] == "Volcán"


def test_una_eleccion_vieja_que_ya_no_existe_no_rompe_las_pestanas(monkeypatch):
    """Si cambia el rótulo (p.ej. el conteo de productos del sub-tab Volcán),
    la memoria vieja no puede llegar como `default`: Streamlit lanza excepción
    con un default que no está en la lista."""
    from dashboard import pestanas as P

    estado = {"_pestana_elegida_g": "🔬 Volcán (3 productos)"}
    llamadas: list = []
    monkeypatch.setattr(P.st, "session_state", estado)
    monkeypatch.setattr(P.st, "tabs",
                        lambda e, **kw: llamadas.append(kw) or [None] * len(e))
    P.pestanas_perezosas(["🔭 Vigilancia", "🔬 Volcán (4 productos)"], key="g")
    assert llamadas[-1]["default"] is None
