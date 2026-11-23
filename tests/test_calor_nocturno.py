"""Cableado del indicador nocturno de calor en el cráter (ficha SDA §A.8).

La regla vive en `src/process/vrp_nocturno.py` y la vigila `tests/test_vrp_nocturno.py`.
Esto vigila lo que se agrega al cablearla, que es donde un indicador validado se puede
echar a perder sin tocar un solo umbral:

1. La serie (`src/process/calor_nocturno.py`) aplica la MISMA regla: reconstruye las
   744 noches por volcán de la validación (PR 87) desde sus cuadros.
2. Un hueco de la serie es "sin dato", nunca un cero, y la referencia de cielo
   despejado sale sólo de las 7 noches previas.
3. La edad del dato va junto al estado y se avisa el atraso de más de 30 min.
4. El workflow (`scripts/build_calor_nocturno.py`) no escribe ceros por un gránulo que
   falta, rellena huecos con presupuesto y poda a la ventana de 8 noches.
5. Se ve en la cabecera de la grilla de volcán del Modo Guardia y de Vista Operacional,
   NO en la pared del Modo Sala.
"""

import ast
import csv
import functools
import importlib.util
import inspect
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

from src.process import calor_nocturno as C
from src.process import vrp_nocturno as V

RAIZ = Path(__file__).resolve().parent.parent
RES = RAIZ / "docs" / "own_volcat" / "vrp_nocturno" / "resultados"
VIEWS = RAIZ / "dashboard" / "views"
GRID = VIEWS / "modo_guardia_volcan.py"
LIVE = VIEWS / "live_viewer.py"
GUARDIA = VIEWS / "modo_guardia.py"
WF = RAIZ / ".github" / "workflows" / "calor_nocturno.yml"

CHILLAN = ("Nevados de Chillan", -36.86, -71.38)
UTC = timezone.utc


def _t(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)


@functools.lru_cache(maxsize=1)
def _script():
    """Una sola instancia del módulo: si no, `GranuloAusente` del lector falso sería
    otra clase que la que el script captura."""
    spec = importlib.util.spec_from_file_location(
        "build_calor_nocturno", RAIZ / "scripts" / "build_calor_nocturno.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _serie(filas, ultimo=None):
    """Serie mínima: {iso: {volcán: [vrp, bt14, ncal]}}."""
    cuadros = {}
    for t, nombre, vrp, bt14 in filas:
        cuadros.setdefault(t.strftime(C.ISO), {})[nombre] = [vrp, bt14, 0]
    ult = ultimo or (max(t for t, *_ in filas) if filas else None)
    return {"version": 1, "cadencia_min": C.CADENCIA_MIN, "cuadros": cuadros,
            "sin_granulo": [], "ultimo_cuadro_utc": ult.strftime(C.ISO) if ult else None}


def _noche_de(noche: date, vrp=0.0, bt14=270.0, cada=30, desde_h=23, hasta_h=10):
    """Cuadros de Chillán de la noche `noche`, por defecto de 23:00 a 10:00 UTC."""
    t = datetime.combine(noche - timedelta(days=1), datetime.min.time(), UTC) \
        + timedelta(hours=desde_h)
    fin = datetime.combine(noche, datetime.min.time(), UTC) + timedelta(hours=hasta_h)
    out = []
    while t <= fin:
        out.append((t, CHILLAN[0], vrp, bt14))
        t += timedelta(minutes=cada)
    return out


# ── 1. la serie aplica la regla validada ─────────────────────────────────────

def test_la_serie_reproduce_las_noches_de_la_validacion():
    """744 noches por volcán de `resultados/noches.csv`, reconstruidas desde
    `cuadros.csv` con la función que usa el dashboard. Si alguien cambia la
    referencia, la vara de visibilidad o el conteo al cablear, esto lo ve."""
    por_sitio: dict = {}
    with open(RES / "cuadros.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["nocturno"] != "True":
                continue
            t = datetime.strptime(r["cuadro"], "%Y%m%d_%H%M")
            noche = date.fromisoformat(r["noche"])
            assert V.clave_noche(t) == noche
            vrp = float(r["vrp"]) if r["vrp"] else math.nan
            b14 = float(r["bt14z"]) if r["bt14z"] else math.nan
            por_sitio.setdefault(r["sitio"], {}).setdefault(noche, []).append(
                V.CuadroVRP(vrp, b14, int(r["ncal"])))
    n = 0
    with open(RES / "noches.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            esperado = ("encendido" if r["enc"] == "True" else
                        "bajo_limite" if r["con_dato"] == "True" else "sin_dato")
            res = C.evaluar_noche(por_sitio[r["sitio"]], date.fromisoformat(r["noche"]))
            assert res["estado"] == esperado, (r["sitio"], r["noche"], res)
            assert res["n_visibles"] == int(r["n_vis"]), (r["sitio"], r["noche"])
            n += 1
    assert n == 744


def test_la_referencia_sale_solo_de_las_siete_noches_previas():
    """La noche misma no se usa como su propia referencia de cielo despejado:
    una noche sola, sin previas, queda sin dato aunque traiga 20 cuadros."""
    d = date(2026, 11, 22)
    sola = {d: [V.CuadroVRP(30.0, 270.0, 3)] * 20}
    assert C.evaluar_noche(sola, d)["estado"] == "sin_dato"
    # con 7 noches previas despejadas, la misma noche se evalúa
    prev = {d - timedelta(days=i): [V.CuadroVRP(0.0, 270.0, 0)] * 5 for i in range(1, 8)}
    assert C.evaluar_noche({**sola, **prev}, d)["estado"] == "encendido"
    # una noche a 8 días ya no entra en la referencia
    lejos = {d - timedelta(days=8): [V.CuadroVRP(0.0, 270.0, 0)] * 30}
    assert C.evaluar_noche({**sola, **lejos}, d)["estado"] == "sin_dato"


# ── 2. qué noche se muestra, huecos ─────────────────────────────────────────

def _semana(ultima: date, **kw):
    filas = []
    for i in range(0, 8):
        filas += _noche_de(ultima - timedelta(days=i), **kw)
    return filas


@pytest.mark.parametrize("ahora", ["2026-11-23 14:52", "2026-11-23 20:00", "2026-11-23 12:30"])
def test_de_dia_se_muestra_la_ultima_noche_terminada(ahora):
    serie = _serie(_semana(date(2026, 11, 23)))
    r = C.evaluar_volcan(serie, *CHILLAN, ahora=_t(ahora))
    assert r["noche"] == date(2026, 11, 23) and r["en_curso"] is False


def test_de_noche_se_muestra_la_noche_en_curso_si_ya_tiene_cuadros():
    filas = _semana(date(2026, 11, 23)) + _noche_de(date(2026, 11, 24), hasta_h=1)
    r = C.evaluar_volcan(_serie(filas), *CHILLAN, ahora=_t("2026-11-24 01:20"))
    assert r["noche"] == date(2026, 11, 24) and r["en_curso"] is True


def test_recien_empezada_la_noche_se_muestra_la_anterior():
    """Con menos de 4 cuadros la noche en curso sería "sin dato" sólo por joven."""
    filas = _semana(date(2026, 11, 23)) + _noche_de(date(2026, 11, 24), desde_h=24, hasta_h=1)
    r = C.evaluar_volcan(_serie(filas), *CHILLAN, ahora=_t("2026-11-24 01:10"))
    assert r["noche"] == date(2026, 11, 23) and r["en_curso"] is False


def test_un_hueco_es_sin_dato_nunca_un_cero():
    """La noche evaluada sólo tiene 2 cuadros en la serie (el cron no corrió): con
    el cráter visible en los dos y 0 MW, NO puede salir "bajo el límite"."""
    d = date(2026, 11, 23)
    filas = _semana(d - timedelta(days=1)) + _noche_de(d)[:2]
    r = C.evaluar_volcan(_serie(filas), *CHILLAN, ahora=_t("2026-11-23 15:00"))
    assert r["estado"] == "sin_dato"
    assert r["n_huecos"] > 10
    from dashboard.map_helpers import COLOR_SIN_DATO, estado_calor_nocturno
    assert estado_calor_nocturno(r)["color"] == COLOR_SIN_DATO


def test_serie_ilegible_es_sin_dato_gris():
    from dashboard.map_helpers import COLOR_SIN_DATO, estado_calor_nocturno
    for serie in (None, {}, {"cuadros": {}}):
        r = C.evaluar_volcan(serie, *CHILLAN, ahora=_t("2026-11-23 15:00"))
        assert r["estado"] == "sin_dato"
        e = estado_calor_nocturno(r)
        assert e["color"] == COLOR_SIN_DATO and e["verificado"] is False


def test_semana_encendida_se_ve_encendida():
    serie = _serie(_semana(date(2026, 11, 23), vrp=25.0))
    r = C.evaluar_volcan(serie, *CHILLAN, ahora=_t("2026-11-23 15:00"))
    assert r["estado"] == "encendido" and r["n_huecos"] == 0


# ── 3. edad y atraso ─────────────────────────────────────────────────────────

def test_ultimo_scan_esperado():
    assert C.ultimo_esperado(_t("2026-11-23 14:52")) == _t("2026-11-23 14:30")
    assert C.ultimo_esperado(_t("2026-11-23 14:44")) == _t("2026-11-23 14:00")


def test_atraso_mayor_a_30_min_se_avisa_y_menor_no():
    from dashboard.map_helpers import estado_calor_nocturno
    filas = _semana(date(2026, 11, 23))
    al_dia = C.evaluar_volcan(_serie(filas, ultimo=_t("2026-11-23 14:00")), *CHILLAN,
                              ahora=_t("2026-11-23 14:52"))
    assert al_dia["atrasada"] is False
    assert "atrasada" not in estado_calor_nocturno(al_dia)["detalle"]
    viejo = C.evaluar_volcan(_serie(filas, ultimo=_t("2026-11-23 13:30")), *CHILLAN,
                             ahora=_t("2026-11-23 14:52"))
    assert viejo["atrasada"] is True and viejo["atraso_min"] == 60
    assert "atrasada" in estado_calor_nocturno(viejo)["detalle"]


@pytest.mark.parametrize("estado", ["encendido", "bajo_limite", "sin_dato", "de_dia"])
def test_la_edad_va_junto_al_estado(estado):
    from dashboard.map_helpers import estado_calor_nocturno
    con = estado_calor_nocturno({"estado": estado, "n_visibles": 8, "n_sobre_umbral": 3,
                                 "serie_hasta": _t("2026-11-23 14:00"), "edad_min": 52})
    assert "serie hasta" in con["detalle"] and "52 min" in con["detalle"]
    sin = estado_calor_nocturno({"estado": estado})
    assert "sin hora" in sin["detalle"]


def test_html_lleva_aviso_de_fuente_y_no_es_verde():
    from dashboard.calor_nocturno import html_calor
    from dashboard.map_helpers import AVISO_CALOR_NOCTURNO, COLOR_CALMA
    for est in ("encendido", "bajo_limite", "sin_dato", "de_dia"):
        h = html_calor({"estado": est, "n_visibles": 8, "n_sobre_umbral": 0}, compacto=True)
        assert AVISO_CALOR_NOCTURNO in h and COLOR_CALMA not in h


# ── 4. el workflow ───────────────────────────────────────────────────────────

class _Ausente(Exception):
    pass


def _volcanes():
    from src.volcanos import get_volcano
    return [get_volcano("Nevados de Chillan"), get_volcano("Lascar")]


# Planck del NetCDF real de la fixture, no tipeados a mano
_Z = np.load(RAIZ / "tests" / "fixtures" / "vrp_nocturno_chillan_20261018_0500.npz")
CO7, CO14 = tuple(float(x) for x in _Z["co7"]), tuple(float(x) for x in _Z["co14"])


def _lector_falso(faltan=(), fallan=()):
    """rad7/rad14 sintéticos de una escena fría y pareja (0 MW en todo volcán)."""
    S = _script()

    def leer(t, sitios):
        if t in faltan:
            raise S.GranuloAusente(t)
        if t in fallan:
            raise OSError("S3 cortó")
        co, co14 = CO7, CO14
        out7, out14 = {}, {}
        for nombre, s in sitios.items():
            b14 = np.full(s.zona.shape, 270.0)
            fk1, fk2, bc1, bc2 = co
            r7 = fk1 / (np.exp(fk2 / (bc1 + bc2 * (b14 + 2.0))) - 1)
            fk1b, fk2b, bc1b, bc2b = co14
            r14 = fk1b / (np.exp(fk2b / (bc1b + bc2b * b14)) - 1)
            out7[nombre], out14[nombre] = r7, r14
        return {7: (out7, co), 14: (out14, co14)}
    return leer


def test_el_workflow_no_escribe_ceros_por_un_granulo_que_falta():
    S = _script()
    ahora = _t("2026-11-23 08:00")
    viejo, reciente = _t("2026-11-23 03:00"), _t("2026-11-23 07:30")
    serie = S.actualizar({}, ahora, _volcanes(),
                         _lector_falso(faltan=(viejo, reciente), fallan=(_t("2026-11-23 05:00"),)),
                         presupuesto=200)
    cuadros = serie["cuadros"]
    assert viejo.strftime(C.ISO) not in cuadros
    assert reciente.strftime(C.ISO) not in cuadros
    assert _t("2026-11-23 05:00").strftime(C.ISO) not in cuadros
    # el viejo queda anotado para no reintentarlo; el reciente y el que falló, no
    assert viejo.strftime(C.ISO) in serie["sin_granulo"]
    assert reciente.strftime(C.ISO) not in serie["sin_granulo"]
    assert _t("2026-11-23 05:00").strftime(C.ISO) not in serie["sin_granulo"]
    # un cuadro sano sí está, y sólo con los volcanes de noche
    fila = cuadros[_t("2026-11-23 04:00").strftime(C.ISO)]
    assert set(fila) <= {"Nevados de Chillan", "Lascar"} and fila


def test_el_workflow_solo_guarda_volcanes_de_noche():
    S = _script()
    ahora = _t("2026-11-23 15:00")
    serie = S.actualizar({}, ahora, _volcanes(), _lector_falso(), presupuesto=400)
    for iso, fila in serie["cuadros"].items():
        t = datetime.strptime(iso, C.ISO).replace(tzinfo=UTC)
        for nombre in fila:
            v = next(x for x in _volcanes() if x.name == nombre)
            assert V.es_nocturno(t, v.lat, v.lon), (iso, nombre)
        assert t.minute in (0, 30), iso       # cadencia validada de 30 min


def test_gap_fill_con_presupuesto_y_los_mas_nuevos_primero():
    S = _script()
    ahora = _t("2026-11-23 08:00")
    serie = S.actualizar({}, ahora, _volcanes(), _lector_falso(), presupuesto=5)
    ts = sorted(serie["cuadros"])
    assert len(ts) == 5
    assert ts[-1] == C.ultimo_esperado(ahora).strftime(C.ISO)
    # la corrida siguiente sigue hacia atrás sin repetir
    serie2 = S.actualizar(serie, ahora, _volcanes(), _lector_falso(), presupuesto=5)
    assert len(serie2["cuadros"]) == 10


def test_la_ventana_es_la_noche_evaluada_y_sus_siete_previas():
    S = _script()
    ahora = _t("2026-11-23 15:00")
    serie = S.actualizar({}, ahora, _volcanes(), _lector_falso(), presupuesto=2000)
    noches = {V.clave_noche(datetime.strptime(i, C.ISO)) for i in serie["cuadros"]}
    assert min(noches) == date(2026, 11, 16) and max(noches) == date(2026, 11, 23)
    # 3 días después, lo viejo se poda
    luego = S.actualizar(serie, ahora + timedelta(days=3), _volcanes(), _lector_falso(),
                         presupuesto=0)
    noches = {V.clave_noche(datetime.strptime(i, C.ISO)) for i in luego["cuadros"]}
    assert min(noches) == date(2026, 11, 19)


def test_el_ultimo_cuadro_avanza_de_dia_sin_bajar_nada():
    """De día no hay nada que bajar, pero la serie está al día: si no avanzara,
    toda tarde se leería como "atrasada"."""
    S = _script()
    ahora = _t("2026-11-23 18:10")

    def nunca(t, sitios):
        raise AssertionError(f"no debía bajar {t}")
    base = {"cuadros": {}, "sin_granulo": [],
            "ultimo_cuadro_utc": _t("2026-11-23 13:00").strftime(C.ISO)}
    # entre 13:00 y 17:30 UTC es de día en Chillán y Láscar: nada que bajar
    serie = S.actualizar(base, ahora, _volcanes(), nunca, presupuesto=0)
    assert serie["ultimo_cuadro_utc"] == "2026-11-23T17:30Z"


# ── 5. dónde se ve ───────────────────────────────────────────────────────────

def _llamadas(path, nombre):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [n for n in ast.walk(tree) if isinstance(n, ast.Call)
            and getattr(n.func, "id", getattr(n.func, "attr", None)) == nombre]


def _kw(call, nombre):
    for k in call.keywords:
        if k.arg == nombre:
            return ast.unparse(k.value)
    return None


def _func(path, nombre):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return next(n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name == nombre)


def test_la_grilla_lo_apaga_por_defecto():
    from dashboard.views.modo_guardia_volcan import _grid_header, volcan_grid
    assert inspect.signature(volcan_grid).parameters["mostrar_calor_nocturno"].default is False
    hdr = getattr(_grid_header, "__wrapped__", _grid_header)
    assert inspect.signature(hdr).parameters["calor_nocturno"].default is False


def test_la_grilla_le_pasa_el_flag_a_la_cabecera():
    grid = _func(GRID, "volcan_grid")
    calls = [c for c in ast.walk(grid) if isinstance(c, ast.Call)
             and getattr(c.func, "id", "") == "_grid_header"]
    assert calls and all(_kw(c, "calor_nocturno") == "mostrar_calor_nocturno" for c in calls)


def test_la_cabecera_lo_dibuja_solo_con_el_flag_y_despues_de_volcat():
    hdr = _func(GRID, "_grid_header")
    guardadas = [n for n in ast.walk(hdr) if isinstance(n, ast.If)
                 and "calor_nocturno" in ast.unparse(n.test)
                 and "html_calor(" in "".join(ast.unparse(s) for s in n.body)]
    assert guardadas, "html_calor tiene que ir bajo `if calor_nocturno`"
    fuera = [n for n in ast.walk(hdr) if isinstance(n, ast.Call)
             and getattr(n.func, "id", "") in ("html_calor", "senal_calor")]
    dentro = [n for g in guardadas for n in ast.walk(g) if isinstance(n, ast.Call)
              and getattr(n.func, "id", "") in ("html_calor", "senal_calor")]
    assert len(fuera) == len(dentro), "ninguna llamada fuera del `if calor_nocturno`"
    md = [c for c in ast.walk(hdr) if isinstance(c, ast.Call)
          and getattr(c.func, "attr", "") == "markdown"]
    txt = ast.unparse(md[-1])
    assert "senal_html" in txt and "calor_html" in txt
    assert txt.index("senal_html") < txt.index("calor_html"), "va debajo de VOLCAT"


def test_vista_operacional_lo_enciende():
    calls = _llamadas(LIVE, "volcan_grid")
    assert len(calls) == 1 and _kw(calls[0], "mostrar_calor_nocturno") == "True"


def test_el_subtab_lo_enciende_y_la_pared_de_la_sala_no():
    calls = _llamadas(GUARDIA, "volcan_grid")
    tv = [c for c in calls if _kw(c, "panels") is not None]
    sub = [c for c in calls if c not in tv]
    assert len(tv) == 1 and len(sub) == 1
    assert _kw(sub[0], "mostrar_calor_nocturno") == "True"
    assert _kw(tv[0], "mostrar_calor_nocturno") in (None, "False")


# ── 6. workflow y documentos ─────────────────────────────────────────────────

def test_workflow_cada_10_min_con_grupo_propio_y_gap_fill():
    yaml = pytest.importorskip("yaml")
    wf = yaml.safe_load(WF.read_text(encoding="utf-8"))
    on = wf.get("on", wf.get(True))
    assert on["schedule"][0]["cron"] == "*/10 * * * *"
    grupo = wf["concurrency"]["group"]
    otros = [yaml.safe_load(p.read_text(encoding="utf-8")).get("concurrency") or {}
             for p in WF.parent.glob("*.yml") if p != WF]
    assert grupo not in {o.get("group") for o in otros}, "grupo de concurrency propio"
    assert wf["concurrency"]["cancel-in-progress"] is False
    pasos = " ".join(s.get("run", "") for j in wf["jobs"].values() for s in j["steps"])
    assert "scripts/build_calor_nocturno.py" in pasos and "--gap-fill" in pasos
    assert "data/calor_nocturno.json" in pasos and "-X theirs" in pasos


def test_ficha_e_integration_al_dia():
    ficha = (RAIZ / "docs" / "FICHA_SDA_GOES.md").read_text(encoding="utf-8")
    a, c = ficha.index("## A."), ficha.index("## C.")
    assert "### A.8 Indicador nocturno de calor" in ficha[a:ficha.index("## B.")]
    tabla_c = ficha[c:ficha.index("## Historial")]
    assert "vrp_nocturno" not in tabla_c, "la fila tiene que salir de §C"
    assert "v2.10" in ficha
    integ = (RAIZ / "INTEGRATION.md").read_text(encoding="utf-8")
    assert "calor_nocturno.yml" in integ and "last_updated: 2026-11-23" in integ
