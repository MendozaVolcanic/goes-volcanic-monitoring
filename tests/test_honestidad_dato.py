"""Ausencia de dato no es ausencia de fenómeno, y un dato viejo no es un dato actual.

Si estas reglas estuvieran rotas, las pruebas fallan: cada una afirma lo que se le
dice al operador con la fuente caída o atrasada. La línea base roja se obtuvo sobre
el código anterior.
"""

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

AHORA = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)
VISTAS = Path(__file__).resolve().parents[1] / "dashboard" / "views"


def _hace(minutos):
    return AHORA - timedelta(minutes=minutos)


# ── estado_hotspots ──────────────────────────────────────────────────────────

def test_cero_con_scan_reciente_es_verde():
    from dashboard.map_helpers import estado_hotspots
    est = estado_hotspots([], _hace(12), ahora=AHORA)
    assert est["valor"] == "0"
    assert est["color"] == "#44dd88"


def test_cero_con_scan_vencido_no_es_verde_ni_afirma_calma():
    from dashboard.map_helpers import estado_hotspots
    est = estado_hotspots([], _hace(150), ahora=AHORA)
    assert est["color"] != "#44dd88"
    assert "150" in est["detalle"]
    assert "no descarta" in est["detalle"]


def test_sin_scan_nunca_es_un_cero():
    from dashboard.map_helpers import estado_hotspots
    est = estado_hotspots([], None, ahora=AHORA)
    assert est["valor"] != "0"
    assert est["verificado"] is False


# ── KPI del hot spot más cercano ─────────────────────────────────────────────

def test_kpi_cercano_con_fdcf_caido_no_queda_verde():
    from dashboard.map_helpers import kpi_hotspot_cercano
    color, valor, detalle = kpi_hotspot_cercano(None, float("inf"), None, ahora=AHORA)
    assert color != "#44dd88"
    assert valor != "sin hotspots"
    assert "no consultable" in detalle


def test_kpi_cercano_sin_hotspots_con_scan_reciente_es_verde():
    from dashboard.map_helpers import kpi_hotspot_cercano
    color, valor, _ = kpi_hotspot_cercano(None, float("inf"), _hace(12), ahora=AHORA)
    assert color == "#44dd88"
    assert valor == "sin hotspots"


def test_kpi_cercano_con_hotspot_a_5_km_es_rojo():
    from dashboard.map_helpers import kpi_hotspot_cercano
    hs = SimpleNamespace(temp_k=400.0, frp_mw=12.5)
    color, valor, detalle = kpi_hotspot_cercano(hs, 5.0, _hace(12), ahora=AHORA)
    assert color == "#ff4444"
    assert valor == "5 km"
    assert "12.5" in detalle


# ── Frases que afirman calma ─────────────────────────────────────────────────

def test_frase_nacional_no_dice_lo_normal_si_no_hubo_scan():
    from dashboard.map_helpers import frase_hotspots_chile
    assert frase_hotspots_chile(0, None) is None


def test_frase_nacional_con_scan_y_cero_explica_que_es_normal():
    from dashboard.map_helpers import frase_hotspots_chile
    frase = frase_hotspots_chile(0, "2026-11-09T11:50:00")
    assert "11:50" in frase
    assert "normal" in frase


def test_frase_nacional_con_detecciones_da_el_conteo():
    from dashboard.map_helpers import frase_hotspots_chile
    assert "3 hot spot" in frase_hotspots_chile(3, "2026-11-09T11:50:00")


def test_tira_de_altura_no_afirma_sin_hot_spot_si_fdcf_cayo():
    from dashboard.map_helpers import aviso_altura_sin_disparo
    texto = aviso_altura_sin_disparo(None, "78 MB")
    assert "Sin hot spot" not in texto
    assert "no consultable" in texto
    assert "78 MB" in texto


def test_tira_de_altura_dice_sin_hot_spot_si_noaa_miro():
    from dashboard.map_helpers import aviso_altura_sin_disparo
    assert "Sin hot spot" in aviso_altura_sin_disparo(_hace(12), "78 MB")


def test_vaa_caido_no_se_lee_como_condiciones_normales():
    from dashboard.map_helpers import mensaje_vaa
    texto = mensaje_vaa(None)
    assert "normales" not in texto
    assert "no se pudo" in texto.lower()


def test_vaa_consultado_y_vacio_si_es_ausencia():
    from dashboard.map_helpers import mensaje_vaa
    assert "normales" in mensaje_vaa({"features": []})


# ── Escena en caché ──────────────────────────────────────────────────────────

def test_escena_ash_vieja_no_conserva_el_banner_verde():
    from dashboard.map_helpers import resumen_escena_ash
    ts = (AHORA - timedelta(days=217)).isoformat()
    texto, estado = resumen_escena_ash("Sin actividad significativa", "ok", ts, ahora=AHORA)
    assert estado != "ok"
    assert "Sin actividad" not in texto
    assert "217" in texto


def test_escena_ash_reciente_conserva_su_diagnostico():
    from dashboard.map_helpers import resumen_escena_ash
    ts = _hace(12).isoformat()
    assert resumen_escena_ash("Sin actividad", "ok", ts, ahora=AHORA) == ("Sin actividad", "ok")


def test_escena_ash_sin_fecha_legible_no_es_ok():
    from dashboard.map_helpers import resumen_escena_ash
    _, estado = resumen_escena_ash("Sin actividad", "ok", "basura", ahora=AHORA)
    assert estado != "ok"


# ── Imagen atrasada ──────────────────────────────────────────────────────────

def test_alerta_de_edad_callada_con_imagen_al_dia():
    from dashboard.map_helpers import alerta_edad
    assert alerta_edad(16) == ""


def test_alerta_de_edad_avisa_con_imagen_atrasada():
    from dashboard.map_helpers import alerta_edad
    assert "atrasada" in alerta_edad(30)


def test_alerta_de_edad_respeta_la_latencia_propia_de_volcat():
    from dashboard.map_helpers import alerta_edad
    assert alerta_edad(45, limite_min=120) == ""
    assert "atrasada" in alerta_edad(130, limite_min=120)


def test_alerta_de_edad_sin_edad_no_inventa_nada():
    from dashboard.map_helpers import alerta_edad
    assert alerta_edad(None) == ""


def test_clase_del_banner_de_loop_depende_de_la_edad():
    from dashboard.map_helpers import clase_banner_edad
    assert clase_banner_edad(16) == "ok"
    assert clase_banner_edad(200) == "warn"
    assert clase_banner_edad(None) == "warn"


# ── Defectos puntuales ───────────────────────────────────────────────────────

def test_comparador_acepta_la_fecha_con_zona_que_le_pasa_la_vista():
    from dashboard.views.comparador import _build_target_ts_window
    ventana = _build_target_ts_window(AHORA, window_hours=2)
    assert ventana[0] == "20261109120000"
    assert len(ventana) == 25


def test_volcat_zona_sur_contiene_villarrica_y_llaima():
    from dashboard.views.volcat_viewer import sector_y_encuadre_zona
    sector, _instr, vista = sector_y_encuadre_zona("Sur")
    assert sector == "Chile_Central_2_km"
    for lat, lon in ((-39.42, -71.93), (-38.69, -71.73)):
        assert vista["lat_min"] <= lat <= vista["lat_max"]
        assert vista["lon_min"] <= lon <= vista["lon_max"]


def test_volcat_zona_austral_usa_el_sector_sur():
    from dashboard.views.volcat_viewer import sector_y_encuadre_zona
    sector, _instr, vista = sector_y_encuadre_zona("Austral")
    assert sector == "Chile_South_2_km"
    assert vista["lat_max"] <= -40.0


# ── Guarda de familia ────────────────────────────────────────────────────────

# El panel de mapa no afirma un conteo: sin dato dibuja sin diamantes, y la
# cabecera de la misma grilla es la que avisa.
DESCARTE_PERMITIDO = {("modo_guardia_volcan.py", "_panel_rammb")}


def _descartes_de_scan():
    """Lecturas ``x, _ = _hotspots_*()`` por archivo y función, y total de lecturas."""
    descartes, total = set(), 0
    for ruta in VISTAS.glob("*.py"):
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        for funcion in ast.walk(arbol):
            if not isinstance(funcion, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for nodo in ast.walk(funcion):
                if not (isinstance(nodo, ast.Assign)
                        and isinstance(nodo.value, ast.Call)
                        and isinstance(nodo.value.func, ast.Name)
                        and nodo.value.func.id.startswith("_hotspots_")
                        and isinstance(nodo.targets[0], ast.Tuple)):
                    continue
                total += 1
                segundo = nodo.targets[0].elts[1]
                if isinstance(segundo, ast.Name) and segundo.id == "_":
                    descartes.add((ruta.name, funcion.name))
    return descartes, total


def test_ninguna_vista_descarta_la_hora_del_scan_de_hot_spots():
    descartes, total = _descartes_de_scan()
    assert total >= 6, "la guarda no encontró las lecturas: revisar el patrón"
    assert descartes <= DESCARTE_PERMITIDO, sorted(descartes - DESCARTE_PERMITIDO)
