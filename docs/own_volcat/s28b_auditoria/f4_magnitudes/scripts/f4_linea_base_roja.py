r"""S28b F4, línea base roja: s23_medir.Detector.base fija el largo del anillo con M.NA (Chillán, 837 píxeles).

Por qué: si una geometría con otro largo de anillo (las vecinas de S28a) pasara por Detector.base, ¿el error sería
ruidoso (excepción) o silencioso (una base mal alineada que igual da números)? Se llama la función ORIGINAL con un
objeto mínimo (datos sintéticos, sin cuadros GOES) con el largo de cada geometría de S28a, y la versión corregida de
S28a (Anillo.base) con los mismos datos.

Uso: python -I f4_linea_base_roja.py
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s28a_vecinas", "scripts"))
import s28a_medir as V  # noqa: E402  (importa s27a, s26a, s25a, s23, s22b, s22a)

S, M = V.S, V.M


class Stub:
    def __init__(self, na, nd=4):
        rng = np.random.default_rng(0)
        self.DIASR = list(range(nd))
        self.NULR = np.ones((nd, 144), bool)
        self.E1R = np.ones((nd, 144), bool)
        self.GATER = np.ones((nd, 144), bool)
        self.mmR = rng.normal(0, 1, (nd, 144, na)).astype(np.float32)
        self._B = {}


class GeoStub:
    def __init__(self, na):
        self.NA = na


print("M.NA (Chillán) =", M.NA)
for nom, na in (("chillan", M.NA), ("antuco_principal", 552), ("antuco_sin_excluir", 831),
                ("longavi_principal", 641), ("longavi_sin_excluir", 851)):
    st = Stub(na)
    try:
        b = S.Detector.base(st, None)
        res = f"original: corre, forma {b.shape}"
    except Exception as e:  # noqa: BLE001
        res = f"original: {type(e).__name__}: {str(e)[:90]}"
    st2 = Stub(na)
    st2.geo = GeoStub(na)
    b2 = V.Anillo.base(st2, None)
    print(f"{nom:22s} NA={na:4d}  {res}  |  S28a Anillo.base: forma {b2.shape}")
