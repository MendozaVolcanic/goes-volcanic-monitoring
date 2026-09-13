"""Pinea `_ash_red_fraction_v2`, la única métrica automática sobre Ash RGB permitida.

Por qué importa: el color del Ash RGB miente en Chile invernal. Cirros finos se
ven rosados (rojo Y azul altos) y nieve o nube opaca se ve blanca (todo alto);
la receta ingenua de "rojo dominante" los cuenta como ceniza y da 30-60 % de
falsos positivos. `_ash_red_fraction_v2` agrega dos filtros para eso, y el
proyecto la grafica como serie temporal (no como detector con umbral: ver
CLAUDE.md, "El gatillo por color NO sirve"). Hasta ahora ningún test fijaba sus
umbrales, así que un refactor podía apagar un filtro sin que nada se pusiera rojo.

Sólo tests: no cambian el comportamiento. Arrays sintéticos RGB uint8, que es lo
que entrega RAMMB. Los píxeles están elegidos en los bordes de cada umbral.

Hallazgo al escribirlos (reportado, no corregido): el filtro de nieve
(R>200 y G>200 y B>200) es inalcanzable dentro de v2. Todo píxel que lo cumple
tiene B>130 y R>100, o sea que el filtro de cirros ya lo excluyó. Lo mismo pasa
con el `R>100` del filtro de cirros: la firma roja ya exige R>100. Quitar
cualquiera de las dos condiciones no cambia ningún resultado, por eso no hay
test que pueda ponerse rojo al mutarlas. `test_nieve_no_cuenta_como_ceniza`
pinea el comportamiento observable (nieve = 0 %), que hoy lo garantiza el filtro
de cirros.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetch.timeseries import _ash_red_fraction, _ash_red_fraction_v2

CENIZA = (200, 50, 50)     # rojo dominante, azul bajo: firma de ceniza
CIRRO = (180, 40, 140)     # rojo dominante PERO azul > 130: rosado de cirro
NIEVE = (250, 210, 210)    # todo brillante, rojo apenas dominante
GRIS = (100, 100, 100)     # válido, sin firma
NEGRO = (0, 0, 0)          # fuera del disco / sin dato


def _img(*pixeles):
    """Imagen 1×N×3 uint8 con los píxeles dados."""
    return np.array([list(pixeles)], dtype=np.uint8)


# ── Casos base ───────────────────────────────────────────────────────────────

def test_ceniza_pura_es_100():
    assert _ash_red_fraction_v2(_img(CENIZA, CENIZA)) == 100.0


def test_devuelve_porcentaje_no_fraccion():
    """1 píxel de ceniza en 4 válidos = 25.0 (la serie se grafica en %)."""
    assert _ash_red_fraction_v2(_img(CENIZA, GRIS, GRIS, GRIS)) == 25.0


@pytest.mark.parametrize("img", [None, np.zeros((0, 0, 3), dtype=np.uint8)])
def test_imagen_ausente_o_vacia_da_cero(img):
    assert _ash_red_fraction_v2(img) == 0.0


def test_imagen_toda_oscura_da_cero_sin_dividir_por_cero():
    assert _ash_red_fraction_v2(_img(NEGRO, NEGRO)) == 0.0


# ── Filtro de cirros ─────────────────────────────────────────────────────────

def test_cirro_rosado_no_cuenta_como_ceniza():
    """La versión legacy lo cuenta; v2 lo excluye. Es la razón de existir de v2."""
    assert _ash_red_fraction(_img(CIRRO)) == 100.0
    assert _ash_red_fraction_v2(_img(CIRRO)) == 0.0


def test_borde_del_filtro_de_cirros_en_azul_130():
    """B=130 todavía es ceniza; B=131 ya es cirro (umbral estricto B>130)."""
    assert _ash_red_fraction_v2(_img((200, 50, 130))) == 100.0
    assert _ash_red_fraction_v2(_img((200, 50, 131))) == 0.0


# ── Filtro de nieve / nube opaca ─────────────────────────────────────────────

def test_nieve_no_cuenta_como_ceniza():
    """Nieve fresca / nube opaca: legacy la cuenta, v2 no.

    Ver el docstring del módulo: hoy la excluye el filtro de cirros, no el de
    nieve (inalcanzable). El test fija el resultado, que es lo que importa.
    """
    assert _ash_red_fraction(_img(NIEVE)) == 100.0
    assert _ash_red_fraction_v2(_img(NIEVE)) == 0.0


# ── Firma roja: umbrales ─────────────────────────────────────────────────────

def test_borde_de_rojo_minimo_100():
    """R=100 no alcanza (R>100 estricto); R=101 sí."""
    assert _ash_red_fraction_v2(_img((100, 50, 50))) == 0.0
    assert _ash_red_fraction_v2(_img((101, 50, 50))) == 100.0


def test_borde_de_dominancia_sobre_verde_15():
    """R debe superar a G por MÁS de 15."""
    assert _ash_red_fraction_v2(_img((101, 85, 50))) == 100.0
    assert _ash_red_fraction_v2(_img((101, 86, 50))) == 0.0


def test_borde_de_dominancia_sobre_azul_15():
    """R debe superar a B por MÁS de 15."""
    assert _ash_red_fraction_v2(_img((121, 50, 105))) == 100.0
    assert _ash_red_fraction_v2(_img((121, 50, 106))) == 0.0


def test_sin_desborde_uint8_al_sumar_15():
    """G=250 en uint8: G+15 daría 9 por desborde y el píxel pasaría por rojo.

    La conversión a int16 es lo que evita que un píxel amarillo brillante
    (R=255, G=250) se lea como ceniza.
    """
    assert _ash_red_fraction_v2(_img((255, 250, 10))) == 0.0


# ── Denominador: sólo píxeles válidos ────────────────────────────────────────

def test_pixeles_oscuros_no_entran_al_denominador():
    """Fuera del disco (negro) no diluye el porcentaje."""
    assert _ash_red_fraction_v2(_img(CENIZA, NEGRO, NEGRO, NEGRO)) == 100.0


def test_borde_de_validez_suma_30():
    """R+G+B=30 es inválido (umbral estricto >30); 31 ya es válido."""
    assert _ash_red_fraction_v2(_img(CENIZA, (10, 10, 10))) == 100.0
    assert _ash_red_fraction_v2(_img(CENIZA, (11, 10, 10))) == 50.0
