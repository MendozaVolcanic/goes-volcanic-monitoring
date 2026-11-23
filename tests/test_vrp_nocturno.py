"""Indicador nocturno de calor en el cráter (src/process/vrp_nocturno.py, ficha SDA §A.8).

Tres cosas que estas pruebas sostienen:
1. La regla es la validada fuera de muestra (PR 87): mismos números sobre cuadros
   reales guardados en tests/fixtures, misma ventana y mismo paralaje.
2. La física: un píxel con 10 MW da 10 MW; una cumbre nevada, más fría que su
   entorno en las dos bandas, no da calor (el defecto de H17).
3. Ausencia de dato no es calma: nube, falta de referencia, pocos cuadros y el día
   quedan "sin dato" o "de día", y ni eso ni "bajo el límite" se pintan verde.
"""

from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

from src.process import vrp_nocturno as V

FIX = Path(__file__).resolve().parent / "fixtures"
CHILLAN = (-36.86, -71.38, 3212)   # src/volcanos.py
# Planck (fk1, fk2, bc1, bc2) del NetCDF real guardado en la fixture, no valores tipeados a mano
_Z = np.load(FIX / "vrp_nocturno_chillan_20261018_0500.npz")
CO7, CO14 = tuple(float(x) for x in _Z["co7"]), tuple(float(x) for x in _Z["co14"])


def _cuadro_fixture(nombre):
    z = np.load(FIX / nombre)
    return z["rad7"], tuple(z["co7"]), z["rad14"], tuple(z["co14"])


def _rad(bt, co):
    fk1, fk2, bc1, bc2 = co
    return fk1 / (np.exp(fk2 / (bc1 + bc2 * bt)) - 1)


# ── 1. la regla validada ─────────────────────────────────────────────────────

def test_ventana_y_paralaje_de_chillan_son_los_validados():
    assert V.ventana(*CHILLAN) == (4527, 4552, 2854, 2879)
    la, lo = V.cumbre_aparente(*CHILLAN)
    assert 2.8 < (CHILLAN[0] - la) * 111.2 < 3.1      # ~3 km al sur, como H9 y H17


def test_cuadro_real_con_chillan_encendido_da_lo_validado():
    """18-10-2026 05:00 UTC: la validación dio 18,65 MW (MIROVA 05:06, 19,6 a 21,3 MW)."""
    s = V.sitio(*CHILLAN)
    c = V.vrp_cuadro(*_cuadro_fixture("vrp_nocturno_chillan_20261018_0500.npz"), s=s)
    assert c.vrp_mw == pytest.approx(18.65, abs=0.05)
    assert c.n_calientes == 4
    assert c.bt14_zona_k == pytest.approx(272.34, abs=0.05)


def test_cuadro_real_con_chillan_frio_da_cero():
    """04-09-2026 05:00 UTC: antes del encendido, MIROVA en cero."""
    s = V.sitio(*CHILLAN)
    c = V.vrp_cuadro(*_cuadro_fixture("vrp_nocturno_chillan_20260904_0500.npz"), s=s)
    assert c.vrp_mw == 0.0


# ── 2. la física ─────────────────────────────────────────────────────────────

def _escena(s, bt=268.0, ruido=0.2, seed=1):
    rng = np.random.default_rng(seed)
    shape = s.zona.shape
    b14 = bt + rng.normal(0, ruido, shape)
    b7 = b14 + 1.0 + rng.normal(0, ruido, shape)
    return _rad(b7, CO7), _rad(b14, CO14)


def test_un_pixel_con_10_mw_da_10_mw():
    s = V.sitio(*CHILLAN)
    r7, r14 = _escena(s, ruido=0.0)   # sin ruido: el ruido del propio píxel corre el fondo ~0,3 MW
    i = np.argwhere(s.zona)[0]
    # exceso de radiancia que corresponde a 10 MW en ese píxel: VRP = A·σ/a·ΔL
    r7[tuple(i)] += 10.0 / (s.area_km2[tuple(i)] * V.SIGMA / V.coef_mir(CO7))
    c = V.vrp_cuadro(r7, CO7, r14, CO14, s)
    assert c.n_calientes == 1
    assert c.vrp_mw == pytest.approx(10.0, rel=0.005)


def test_cumbre_nevada_mas_fria_en_las_dos_bandas_no_da_calor():
    """El defecto de H17: contra la radiancia absoluta del anillo, la cumbre fría
    daba exceso cero o negativo de día y apagaba la señal. Con el fondo coherente,
    una cumbre fría SIN anomalía en BT7 − BT14 da 0 MW, no un número espurio."""
    s = V.sitio(*CHILLAN)
    b14 = np.full(s.zona.shape, 268.0)
    b14[s.zona] -= 12.0
    r7, r14 = _rad(b14 + 1.0, CO7), _rad(b14, CO14)
    assert V.vrp_cuadro(r7, CO7, r14, CO14, s).vrp_mw == 0.0


def test_anillo_sin_datos_no_inventa_un_cero():
    s = V.sitio(*CHILLAN)
    r7, r14 = _escena(s)
    r7[s.anillo] = np.nan
    assert np.isnan(V.vrp_cuadro(r7, CO7, r14, CO14, s).vrp_mw)


# ── 3. la noche, y ausencia de dato no es calma ──────────────────────────────

def _c(vrp, bt=270.0):
    return V.CuadroVRP(vrp, bt, 0)


def test_noche_y_dia_en_chillan():
    assert V.es_nocturno(datetime(2026, 10, 18, 5, 0), -36.86, -71.38)
    assert not V.es_nocturno(datetime(2026, 10, 18, 18, 0), -36.86, -71.38)
    assert V.clave_noche(datetime(2026, 10, 17, 23, 30)) == V.clave_noche(datetime(2026, 10, 18, 9, 0))


def test_referencia_pide_diez_cuadros():
    assert V.referencia_despejado([270.0] * 9) is None
    assert V.referencia_despejado([270.0] * 10 + [float("nan")]) == pytest.approx(270.0)


def test_sin_referencia_es_sin_dato():
    r = V.estado_noche([_c(30.0)] * 20, None)
    assert r["estado"] == "sin_dato"


def test_cuadros_bajo_nube_no_cuentan_y_la_noche_queda_sin_dato():
    nubes = [_c(0.0, bt=250.0)] * 20          # 20 K bajo la referencia: cráter tapado
    r = V.estado_noche(nubes + [_c(0.0)] * 3, 270.0)
    assert r["estado"] == "sin_dato"
    assert r["n_visibles"] == 3


def test_cuadros_sueltos_sobre_el_umbral_no_encienden_la_noche():
    """Caso real: Chillán 07-09-2026, 3 de 24 cuadros sobre 10 MW con MIROVA en cero."""
    r = V.estado_noche([_c(36.0)] * 3 + [_c(0.0)] * 21, 270.0)
    assert r["estado"] == "bajo_limite"


def test_un_solo_cuadro_no_enciende_aunque_sea_un_cuarto():
    assert V.estado_noche([_c(20.0)] + [_c(0.0)] * 3, 270.0)["estado"] == "bajo_limite"


def test_noche_encendida():
    r = V.estado_noche([_c(15.0)] * 6 + [_c(0.0)] * 14, 270.0)
    assert r["estado"] == "encendido"
    assert (r["n_visibles"], r["n_sobre_umbral"]) == (20, 6)


def test_de_dia_no_se_evalua():
    assert V.estado_noche([_c(50.0)] * 20, 270.0, nocturno=False)["estado"] == "de_dia"


@pytest.mark.parametrize("res", [
    {"estado": "sin_dato", "motivo": "cráter cubierto o sin cuadros"},
    {"estado": "sin_dato"},
    {"estado": "de_dia"},
    {"estado": "bajo_limite", "n_visibles": 20, "n_sobre_umbral": 0},
    {"estado": "desconocido"},
    {},
])
def test_nada_que_no_sea_calor_se_pinta_verde(res):
    from dashboard.map_helpers import COLOR_CALMA, estado_calor_nocturno
    est = estado_calor_nocturno(res)
    assert est["color"] != COLOR_CALMA
    assert "No descarta" in est["detalle"] or res.get("estado") == "de_dia"


def test_sin_dato_no_es_verificado_y_bajo_limite_si():
    from dashboard.map_helpers import COLOR_SIN_DATO, estado_calor_nocturno
    sd = estado_calor_nocturno({"estado": "sin_dato"})
    assert sd["verificado"] is False and sd["color"] == COLOR_SIN_DATO
    bl = estado_calor_nocturno({"estado": "bajo_limite", "n_visibles": 12, "n_sobre_umbral": 1})
    assert bl["verificado"] is True
    assert "débil" in bl["detalle"]


def test_encendido_dice_cuantos_cuadros_y_cuanta_potencia():
    from dashboard.map_helpers import estado_calor_nocturno
    est = estado_calor_nocturno({"estado": "encendido", "n_visibles": 20, "n_sobre_umbral": 11,
                                 "vrp_max_mw": 32.7}, noche_txt="noche del 15-10")
    assert "11 de 20" in est["detalle"] and "33 MW" in est["detalle"]
    assert est["detalle"].startswith("noche del 15-10")
