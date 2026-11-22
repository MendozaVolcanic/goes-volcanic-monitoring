r"""H23: ciclo diurno de la linea base enmendada (E2) y de la escena despejada (E1), hora por hora. Solo datos de
instrumento: sin inyeccion ni detectores. Sirve para leer la comprobacion I5 cuando no hay referencia a las
18 UTC por falta de tardes despejadas.

Por hora UTC: cuantos dias tienen la escena despejada en esa hora exacta, que fraccion de los pixeles de cada
grupo tiene referencia, y la mediana de BT11_ref y de BTD_ref.
Salida: resultados\h23_diag_ref.json. Uso: python -I h23_diag_ref.py [oct|nov] [volcan]
"""
import json
import os
import sys
import warnings

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h23_medir as M  # noqa: E402

warnings.simplefilter("ignore", RuntimeWarning)


def main(bloque="oct", volcan="chillan"):
    c = M.contexto(bloque, volcan, M.bloque_datos(bloque))
    nd = c["ref11"].shape[0] // 144
    F = c["F"].reshape(nd, 144)
    out = {"bloque": bloque, "volcan": volcan, "dias": nd, "horas": {}}
    for h in range(24):
        fila = {"dias_con_escena_despejada": int(F[:, h * 6].sum())}
        for terr in ("cumbre", "bajo"):
            m = c["terreno"] == terr
            r = c["ref11"].reshape(nd, 144, -1)[:, h * 6][:, m]
            rd = c["refd"].reshape(nd, 144, -1)[:, h * 6][:, m]
            fila[terr] = dict(frac_con_ref=round(float(np.isfinite(r).mean()), 2),
                              bt11_ref=None if not np.isfinite(r).any() else round(float(np.nanmedian(r)), 2),
                              btd_ref=None if not np.isfinite(rd).any() else round(float(np.nanmedian(rd)), 2))
        out["horas"][f"{h:02d}"] = fila
        print(f"{h:02d} UTC", json.dumps(fila))
    res = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
    json.dump(out, open(os.path.join(res, f"h23_diag_ref_{bloque}_{volcan}.json"), "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:])
