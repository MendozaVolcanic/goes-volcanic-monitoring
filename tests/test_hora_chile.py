"""Hora de Chile en pantalla: desfase en numeros, nunca una sigla.

Por que existe: la base tz de IANA saco en 2017 las siglas inventadas de
America/Santiago (CLT/CLST). `strftime("%Z")` devuelve ahora "-03" o "-04",
y el dashboard mostraba "10:10 -03", una hora que nadie en la sala reconoce
como hora de Chile. Peor: el badge de scan escribia "CLT" a mano, que es la
sigla de INVIERNO, tambien en verano.

Lo que se pina:
  * el formato ("10:10 Chile (UTC-3)") y que el desfase siga la fecha
    (UTC-3 en verano, UTC-4 en invierno);
  * que la fecha local aparezca cuando no coincide con la UTC (de 21 a 24 h
    en Chile ya es el dia siguiente en UTC);
  * que ninguna vista le pegue " CL" o " Chile" al rotulo (quedaria
    "Chile (UTC-3) CL");
  * que el texto mas largo siga cabiendo en las bandas PNG que se proyectan.
"""

import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from dashboard import utils

UTC = timezone.utc
VERANO = datetime(2026, 11, 15, 13, 10, 30, tzinfo=UTC)   # 10:10 en Chile
INVIERNO = datetime(2026, 7, 15, 13, 10, tzinfo=UTC)      # 09:10 en Chile
CRUCE_DIA = datetime(2026, 11, 16, 1, 10, tzinfo=UTC)     # 22:10 del 15 en Chile

# Lo que imprimia %Z sin sigla: "-03", "+00", "-0430". "UTC-3" no calza
# porque el lookbehind exige que no venga de "UTC".
SIGLA_NUMERICA = re.compile(r"(?<![A-Za-z\d])[+-]\d{2}(?:\d{2})?\b")

RAIZ = Path(__file__).resolve().parents[1]


# ── Formato ────────────────────────────────────────────────────────────────

def test_fmt_chile_verano_e_invierno():
    assert utils.fmt_chile(VERANO) == "10:10 Chile (UTC-3)"
    assert utils.fmt_chile(INVIERNO) == "09:10 Chile (UTC-4)"


def test_desfase_chile_en_numeros():
    assert utils.desfase_chile(VERANO) == "UTC-3"
    assert utils.desfase_chile(INVIERNO) == "UTC-4"


def test_el_desfase_sigue_a_la_base_tz_todo_el_anio():
    """Barrido horario de un anio: el texto dice el mismo desfase que zoneinfo.

    No se fijan a mano las fechas de cambio de hora porque el decreto chileno
    las ha movido varias veces; lo que importa es que el rotulo no se
    desacople de la conversion real.
    """
    from datetime import timedelta
    t = datetime(2026, 1, 1, tzinfo=UTC)
    vistos = set()
    while t.year == 2026:
        off_h = int(utils.utc_to_chile(t).utcoffset().total_seconds() // 3600)
        assert utils.desfase_chile(t) == f"UTC{off_h:+d}"
        assert utils.fmt_chile(t).endswith(f"Chile (UTC{off_h:+d})")
        vistos.add(off_h)
        t += timedelta(hours=1)
    assert vistos == {-3, -4}


def test_fmt_both_y_long():
    assert utils.fmt_both(VERANO) == "13:10 UTC · 10:10 Chile (UTC-3)"
    assert (utils.fmt_both_long(VERANO)
            == "2026-11-15 13:10 UTC · 10:10 Chile (UTC-3)")
    assert (utils.fmt_both_long(INVIERNO)
            == "2026-07-15 13:10 UTC · 09:10 Chile (UTC-4)")


def test_fmt_both_long_da_la_fecha_local_si_cambia_el_dia():
    assert (utils.fmt_both_long(CRUCE_DIA)
            == "2026-11-16 01:10 UTC · 2026-11-15 22:10 Chile (UTC-3)")


def test_datetime_sin_zona_se_lee_como_utc():
    ingenuo = VERANO.replace(tzinfo=None)
    assert utils.fmt_chile(ingenuo) == "10:10 Chile (UTC-3)"
    assert utils.fmt_both_long(ingenuo) == utils.fmt_both_long(VERANO)


@pytest.mark.parametrize("dt", [VERANO, INVIERNO, CRUCE_DIA])
def test_ningun_formato_imprime_la_sigla_numerica(dt):
    for f in (utils.fmt_chile, utils.fmt_both, utils.fmt_both_long):
        s = f(dt)
        assert not SIGLA_NUMERICA.search(s), (f.__name__, s)
    assert not SIGLA_NUMERICA.search(utils.ts14_to_display("20261115131000"))


def test_badge_de_scan_no_escribe_clt_fijo():
    from dashboard.map_helpers import render_scan_status_badge
    html = render_scan_status_badge(VERANO, 60, now=VERANO)
    assert "CLT" not in html
    assert "10:10 Chile (UTC-3)" in html
    html_inv = render_scan_status_badge(INVIERNO, 60, now=INVIERNO)
    assert "09:10 Chile (UTC-4)" in html_inv


def test_el_loop_volcat_comparte_el_desfase():
    from dashboard.volcat_loop import rotulo_hora
    assert rotulo_hora(VERANO).endswith("(UTC-3)")
    assert rotulo_hora(INVIERNO).endswith("(UTC-4)")


# ── Las vistas no rotulan dos veces ───────────────────────────────────────

def _fuentes():
    for carpeta in ("dashboard", "src"):
        yield from (RAIZ / carpeta).rglob("*.py")


def test_ninguna_vista_le_pega_cl_o_chile_al_rotulo():
    """'({fmt_chile(dt)} CL)' quedaria '(10:10 Chile (UTC-3) CL)'.

    Cubre la llamada directa y la indirecta: una variable o clave que trae la
    hora local ya rotulada ({ch_str}, {frame['label_local']}). La indirecta
    se escapo de la primera version de esta prueba y la encontro la app.
    """
    patrones = [
        re.compile(r"\{[^{}]*(?:fmt_chile|ch_str|local)[^{}]*\}"
                   r"[ \t]*(?:<[^>]*>[ \t]*)?(?:CL|Chile)\b"),
    ]
    malos = []
    for p in _fuentes():
        if p == RAIZ / "dashboard" / "utils.py":   # ahi nace el rotulo
            continue
        txt = p.read_text(encoding="utf-8")
        for pat in patrones:
            for m in pat.finditer(txt):
                linea = txt.count("\n", 0, m.start()) + 1
                malos.append(f"{p.relative_to(RAIZ)}:{linea}: {m.group(0)}")
    assert not malos, "\n".join(malos)


def test_nadie_imprime_la_zona_con_percent_z():
    malos = []
    for p in _fuentes():
        for i, linea in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if "%Z" in linea or re.search(r"""['"]%H:%M CLS?T['"]""", linea):
                malos.append(f"{p.relative_to(RAIZ)}:{i}: {linea.strip()}")
    assert not malos, "\n".join(malos)


# ── Lo que se proyecta sigue cabiendo ─────────────────────────────────────

def test_banda_de_zona_del_modo_sala_cabe():
    """Hora + resolucion en la banda de 50 px de cada zona (PNG de la pared).

    Peor caso: hora de dos digitos en todo y el detalle mas largo que arma
    `_tv_zones_png` ("~3.4 km/px · scan previo").
    """
    import numpy as np
    from PIL import Image, ImageDraw
    from dashboard.views.modo_guardia_volcan import _load_font
    from dashboard.views.zonas_fullscreen import _uniform_aspect_bounds

    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    f_time, f_res = _load_font(15), _load_font(12)
    ph = 700
    t1 = f"{VERANO:%H:%M} UTC · {utils.fmt_chile(VERANO)}"
    for zk, b in _uniform_aspect_bounds().items():
        lon_span = b["lon_max"] - b["lon_min"]
        lat_span = b["lat_max"] - b["lat_min"]
        cos_lat = max(0.1, float(np.cos(np.radians(
            (b["lat_min"] + b["lat_max"]) / 2))))
        pw = max(120, int(round(ph * lon_span * cos_lat / lat_span)))
        ancho = (10 + d.textlength(t1, font=f_time)
                 + d.textlength("~3.4 km/px · scan previo", font=f_res))
        assert ancho <= pw - 6, (zk, ancho, pw)


@pytest.mark.parametrize("w", [320, 480, 800])
def test_rotulo_de_miniatura_de_series_cabe(w):
    """La banda de la miniatura (pico / ultimo) cabe entera y legible.

    El peor caso es el cruce de dia: la hora de Chile lleva su propia fecha.
    En una sola linea eso no cabe en 320 px ni con letra 8 (se perdia justo
    el numero de la metrica), asi que la banda va en dos lineas: rotulo y
    metrica arriba, la hora completa abajo. Cada linea cabe y la letra no
    baja de 9 px.
    """
    from PIL import Image, ImageDraw
    from dashboard.views.timeseries_viewer import (
        _fuente_rotulo, rotulo_miniatura,
    )
    lineas = rotulo_miniatura("PICO", CRUCE_DIA, 100.0)
    assert lineas == ("PICO · 100.00%", utils.fmt_both_long(CRUCE_DIA))
    d = ImageDraw.Draw(Image.new("RGB", (w, 10)))
    font = _fuente_rotulo(d, lineas, w)
    for linea in lineas:
        assert d.textlength(linea, font=font) <= w - 10, (linea, font.size)
    assert font.size >= 9


def test_fuente_de_la_miniatura_es_la_misma_en_todo_sistema():
    """La miniatura usa DejaVu Sans Bold tambien en Windows.

    La falla de CI solo se veia en Linux porque en Windows caia a Arial, que
    es mas angosta: la prueba de ancho pasaba en local y fallaba en el
    runner. matplotlib trae DejaVu, asi que el render es el mismo en todos
    lados y la prueba mide lo que se ve en produccion.
    """
    from PIL import Image, ImageDraw
    from dashboard.views.timeseries_viewer import _fuente_rotulo
    d = ImageDraw.Draw(Image.new("RGB", (320, 10)))
    font = _fuente_rotulo(d, ("x",), 320)
    assert font.getname() == ("DejaVu Sans", "Bold")
