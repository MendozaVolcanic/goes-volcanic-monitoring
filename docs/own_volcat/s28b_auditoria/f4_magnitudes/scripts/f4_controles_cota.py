r"""S28b F4: ¿cuántos controles de cota (a más de 45 km, cota ±300 m) tiene cada píxel del anillo y de la zona, en
Chillán y en las vecinas?

Por qué: el M1 exige 20 controles con cota ±300 m Y BT11 ±0,5 K; la zona exige 20 controles de cota sin nube dinámica.
Si un píxel alto tiene pocos controles de su cota en toda la ventana (los Andes altos a más de 45 km son pocos, y en las
vecinas se pierde además el círculo de 45 km alrededor de Chillán), ese píxel queda fuera casi siempre por geometría,
no por nubes, y la regla "igual que en Chillán" no mide lo mismo. Sólo geometría y DEM: sin cuadros GOES.

Uso: python -I f4_controles_cota.py
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s28a_vecinas", "scripts"))
import s28a_medir as V  # noqa: E402

M, C29, Z, Q = V.M, V.C29, V.Z, V.Q
OUT = r"D:\goes_notas\s28\s28b\f4"
ZD = C29.ZDEM.ravel()


def resumen(n, cotas):
    n = np.asarray(n)
    return {"n_pix": int(len(n)), "min": int(n.min()), "p10": int(np.percentile(n, 10)), "mediana": int(np.median(n)),
            "menos_de_20": int((n < 20).sum()), "menos_de_100": int((n < 100).sum()),
            "cota_de_los_menos_de_100_m": sorted(int(c) for c in cotas[n < 100])[:20]}


def main():
    out = {}
    for nom in ("chillan", "antuco", "longavi"):
        g = V.geo_de(nom, excluir=(nom != "chillan"))
        nfull = np.array([len(c) for c in g.CTRL_COTA])            # por píxel del anillo completo
        keep = g.KEEP
        r = {"anillo_usado": resumen(nfull[keep], ZD[g.AP_FULL][keep]),
             "cota_anillo_m": [int(ZD[g.AP].min()), int(np.median(ZD[g.AP])), int(ZD[g.AP].max())]}
        if nom == "chillan":
            zona, ctrl = Z.ZONA, Z.CTRL
        else:
            zona, _, ctrl, _ = Q.zona_de(*V.SITIOS[nom])
        nz = np.array([int((np.abs(ZD[ctrl] - ZD[p]) <= Z.COTA_M).sum()) for p in zona])
        r["zona"] = {"pixeles": len(zona), "controles_de_cota_por_pixel": nz.tolist(),
                     "cotas_m": [int(ZD[p]) for p in zona]}
        r["controles_totales"] = int(len(ctrl))
        out[nom] = r
        print(nom, json.dumps(r, ensure_ascii=False), flush=True)
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "f4_controles_cota.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)


if __name__ == "__main__":
    main()
