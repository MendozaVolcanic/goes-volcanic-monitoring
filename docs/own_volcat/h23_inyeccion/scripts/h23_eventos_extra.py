r"""H23, descriptivo y POST HOC (escrito despues de ver el veredicto; no decide nada): pone los eventos reales de
VOLCAT en la misma escala que la inyeccion, para contestar si la pluma real queda sobre o bajo el limite.

Para cada evento, en los 6 pixeles de cumbre de Chillan (regla geometrica, no la huella de VOLCAT):
- cuantos cuadros tienen la escena despejada segun la mascara de NOAA;
- BT11 observada, linea base, D1 y D2 (medianas);
- contraste termico con una capa a 3, 4 y 5 km (BT11 observada menos T del aire del GFS);
- que cambio de BT11 y de BTD produciria ahi mismo una capa de e 0,05, 0,10 y 0,15 (beta 0,70) a 4 y 5 km.
Y el fondo sin inyectar de D2 en la cumbre con entorno despejado (poblacion B, octubre), por tramo.

Salida: resultados\h23_eventos_extra.json. Uso: python -I h23_eventos_extra.py
"""
import json
import os
import sys
import warnings
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h23_comun as K  # noqa: E402
import h23_medir as M  # noqa: E402

warnings.simplefilter("ignore", RuntimeWarning)


def main():
    out = {"fondo_D2_cumbre_B_oct": {}, "eventos": []}
    c = M.contexto("oct", "chillan", M.bloque_datos("oct"))
    cum = (c["terreno"] == "cumbre")[None, :]
    for tr in range(4):
        m = c["pob"]["B"] & cum & (c["tramo"] == tr)
        if m.sum() < M.MIN_N:
            out["fondo_D2_cumbre_B_oct"][str(tr)] = "SIN DATO"
            continue
        q = np.quantile(c["d0"]["D2"][m], [0.01, 0.05, 0.25, 0.5, 0.75, 0.95])
        q1 = np.quantile(c["d0"]["D1"][m], [0.05, 0.5, 0.95])
        out["fondo_D2_cumbre_B_oct"][str(tr)] = dict(n=int(m.sum()), p1=float(q[0]), p5=float(q[1]), p25=float(q[2]),
                                                     p50=float(q[3]), p75=float(q[4]), p95=float(q[5]),
                                                     D1_p5=float(q1[0]), D1_p50=float(q1[1]), D1_p95=float(q1[2]))
        print("fondo D2 cumbre B tramo", tr, json.dumps(out["fondo_D2_cumbre_B_oct"][str(tr)]))
    del c
    c = M.contexto("nov", "chillan", M.bloque_datos("nov"))
    cum = c["terreno"] == "cumbre"
    tn = np.array(c["tiempos"])
    bt11 = K.bt_de_rad(c["I14"], c["co"][14])
    btd = bt11 - K.bt_de_rad(c["I15"], c["co"][15])
    for a, b in M.EVENTOS:
        ta, tb = datetime.strptime(a, "%Y-%m-%d %H:%M"), datetime.strptime(b, "%Y-%m-%d %H:%M")
        mt = (tn >= ta) & (tn <= tb)
        sel = np.ix_(mt, cum)
        fila = {"evento": f"{a} a {b[-5:]} UTC", "cuadros": int(mt.sum()),
                "cuadros_con_escena_despejada": int(c["F"][mt].sum()),
                "muestras_con_referencia": int(np.isfinite(c["ref11"][sel]).sum()), "muestras": int(mt.sum() * cum.sum()),
                "bt11_obs": float(np.nanmedian(bt11[sel])), "bt11_ref": float(np.nanmedian(c["ref11"][sel])),
                "btd_obs": float(np.nanmedian(btd[sel])), "btd_ref": float(np.nanmedian(c["refd"][sel])),
                "D1": float(np.nanmedian(c["d0"]["D1"][sel])), "D2": float(np.nanmedian(c["d0"]["D2"][sel])),
                "D2_p25": float(np.nanpercentile(c["d0"]["D2"][sel], 25)), "D2_p75": float(np.nanpercentile(c["d0"]["D2"][sel], 75)),
                "dias_que_sostienen_la_referencia": float(np.median(c["ndias_ref"][sel]))}
        for iz, z in enumerate(M.ALTURAS):
            fila[f"contraste_{z / 1000:.0f}km"] = float(np.nanmedian(bt11[sel] - c["Ttop"][mt, iz][:, None]))
        for iz in (1, 2):
            for eps in (0.05, 0.10, 0.15):
                I14, I15 = M.inyectar(c, eps, iz)
                b1 = K.bt_de_rad(I14, c["co"][14])
                d11 = (b1 - bt11)[sel]
                dd = ((b1 - K.bt_de_rad(I15, c["co"][15])) - btd)[sel]
                fila[f"capa_{M.ALTURAS[iz] / 1000:.0f}km_e{eps:.2f}"] = dict(dbt11=float(np.nanmedian(d11)), dbtd=float(np.nanmedian(dd)))
        out["eventos"].append(fila)
        print(json.dumps(fila))
    res = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
    json.dump(out, open(os.path.join(res, "h23_eventos_extra.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
