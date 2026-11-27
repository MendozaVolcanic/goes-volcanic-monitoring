r"""S31g: forma de la componente principal de la mascara del 25-11 y nubes SCL del dia cerca del crater.
Lee solo el cache de reflectancia ya bajado por s31g_s2_25nov.py (no baja nada, no lee GOES ni termico).
Por que: el rotulo del criterio §2.1 distingue PLUMA VISIBLE (se alarga en una direccion) de BOCANADA CHICA
(< 0,5 km2 pegada al crater); hace falta el largo y el ancho de lo que nace en el crater, no de toda la mascara.

Uso: python -I -B s31g_s2_forma.py
"""
import json
import os
import sys

import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s31g_s2_25nov as G  # noqa: E402

C, P = G.C, G.P


def main():
    bo = G.bandas({"id": G.OBJ_ID})
    br, _, _ = P.referencia_compuesta(G.DIA, G.OBJ_ID)
    nieve = P.nieve_de(br)
    ok = np.isfinite(bo["swir16"]) & np.isfinite(bo["red"])
    with np.errstate(invalid="ignore"):
        pl = (nieve & ok & ((bo["swir16"] - br["swir16"]) > P.DSW1_MIN) & (bo["red"] > P.ROJO_MIN)
              & (P.ndsi(bo) < P.NDSI_OBJ_MAX))
    pl = P.limpiar(pl)
    d = C.hav(C.GLAT, C.GLON, *C.CRATER)
    lab, n = ndimage.label(pl, structure=np.ones((3, 3)))
    k = lab[np.unravel_index(np.argmin(np.where(pl, d, 99)), d.shape)]
    princ = lab == k
    nube = bo["nube"]
    labn, nn = ndimage.label(nube & (d <= 15), structure=np.ones((3, 3)))
    objs = []
    for j in range(1, nn + 1):
        m = labn == j
        if m.sum() >= 20:
            objs.append({"celdas_30m": int(m.sum()), "km2": round(m.sum() * 9e-4, 3),
                         "dist_min_km": round(float(d[m].min()), 2),
                         "azimut_centroide": P.forma(m).get("azimut_centroide_desde_crater")})
    objs.sort(key=lambda x: x["dist_min_km"])
    out = {"componente_principal": P.forma(princ), "celdas": int(princ.sum()),
           "nubes_scl_0_15km_ge_20_celdas": objs,
           "scl_nube_0_15km_km2": round(float((nube & (d <= 15)).sum() * 9e-4), 3)}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    with open(os.path.join(os.path.dirname(AQUI), "resultados", "s2_2026-11-25_forma.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
