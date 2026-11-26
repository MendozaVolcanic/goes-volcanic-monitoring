r"""S29b, POST HOC (criterio §6, no decide): la zona a percentil 4,75 en las cumbres de Antuco y Longaví en oct-nov
2024, con la clase Zona de s27a_medir.py sin cambio (base y umbral de 2025 de cada vecina, nublado de costumbre de
Chillán de cada año, como S27a). Para tener tres cumbres en tres años de día: si en 2024 las vecinas disparan como en
2025, la subida diurna de Antuco es de 2026; si también suben en 2024, el día cambia de un año a otro en toda la zona.

Uso: python -I s29b_posthoc.py     (escribe resultados/s29b_posthoc.json)
"""
import json
import os
import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(OV, "s27a_noche_causa", "scripts"))
import s29b_medir as W  # noqa: E402
import s27a_medir as Q  # noqa: E402

Z, B, H24 = W.Z, W.B, W.H24
assert Q.Z is Z


def main():
    t = time.time()
    btd25 = np.asarray(np.load(Z._npy("r25_btd"), mmap_mode="r"))
    acm25 = np.load(Z._npy("r25_acm"))
    est25 = Z.costumbre(acm25, np.isfinite(btd25[:, :, Z.ZONA[0]]))
    btd24 = np.load(os.path.join(W.TRAB, "r24_btd.npy"))
    acm24 = np.load(os.path.join(W.TRAB, "r24_acm.npy"))
    est24 = Z.costumbre(acm24, np.isfinite(btd24[:, :, Z.ZONA[0]]))
    out = {"rotulo": "POST HOC (criterio §6): no decide", "percentil": Q.PSTAR}
    for sitio, coord in list(Q.SITIOS.items()) + [("chillan", None)]:
        if sitio == "chillan":                     # comprobación: tiene que dar la zona a 4,75 de s29b_medir
            zona, anillo, ctrl = Z.ZONA, W.M.AP, Z.CTRL
        else:
            zona, anillo, ctrl, _ = Q.zona_de(*coord)
        zv = Q.Zona(sitio, zona, anillo, ctrl).correr(btd25, acm25, est25, btd24, acm24, est24, sitio)
        sec, bla = zv.disparos(Q.PSTAR)
        per = W.periodos(bla, sec)
        m24, m25 = W.medidas(bla), W.medidas(sec)
        out[sitio] = {"total_2024": [m24["disparos"], m24["evaluados"]], "total_2025": [m25["disparos"], m25["evaluados"]],
                      "periodos": per, "top_dias_2024": W.top_dias(bla)}
        print(sitio, json.dumps(per, ensure_ascii=False), f"{time.time() - t:.0f} s", flush=True)
    json.dump(out, open(os.path.join(W.RES, "s29b_posthoc.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1, default=int)


if __name__ == "__main__":
    main()
