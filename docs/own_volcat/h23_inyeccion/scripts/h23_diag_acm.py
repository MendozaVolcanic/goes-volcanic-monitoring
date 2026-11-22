r"""H23 (enmienda post hoc 1): comprueba, antes de usarla, como se porta la mascara de nubes de NOAA (ABI-L2-ACMF)
en esta cordillera. Solo datos de instrumento: BT11 cruda y mascara, sin inyeccion ni detectores.

Para cada dia pedido y siete horas, imprime por grupo de pixeles (cumbre de Chillan, su entorno de 6 a 16 km,
terreno bajo de Chillan, valle bajo 300 m) la BT11 mediana y la fraccion que la mascara da por despejada
(niveles 0 y 1 de ACM). Los dias 15 al 18-10 son los mas despejados del bloque segun la BT11 cruda.
Salida: resultados\h23_diag_acm.json. Uso: python -I h23_diag_acm.py 20261015 20261016 ...
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h23_comun as K  # noqa: E402
import h23_medir as M  # noqa: E402


def main(dias):
    z = np.load(os.path.join(K.H23, "cubo_oct.npz"))
    co = z["co14"]
    r14 = z["rad14"].reshape(33, 144, M.NP_)
    g = M.grupos("chillan")
    anillo = np.unique(np.concatenate([M.entorno(p) for p in g["cumbre"]]))
    grupos = {"cumbre": g["cumbre"], "entorno_cumbre": anillo, "bajo": g["bajo"], "valle": np.where(M.ZDEM < 300)[0]}
    filas = []
    for dia in dias:
        d = (K.datetime.strptime(dia, "%Y%m%d") - K.BLOQUE_OCT[0]).days
        for hh in (3, 9, 13, 16, 18, 20, 22):
            f = os.path.join(K.H23, "acm", f"{dia}_{hh:02d}00.npz")
            if not os.path.exists(f):
                continue
            a = np.load(f)["acm"].ravel()
            bt = K.bt_de_rad(r14[d, hh * 6].astype("float64"), co)
            fila = {"dia": dia, "hora_utc": hh}
            for n, px in grupos.items():
                fila[n] = {"bt11": round(float(np.nanmedian(bt[px])), 1), "despejado": round(float(np.mean(a[px] <= 1)), 2)}
            filas.append(fila)
            print(dia, f"{hh:02d}", " | ".join(f"{n}: {v['bt11']} K, {v['despejado']}" for n, v in fila.items() if isinstance(v, dict)))
    cum = [f["cumbre"]["despejado"] for f in filas]
    print("cumbre: fraccion despejada maxima", max(cum), "en", len(cum), "cuadros")
    res = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
    json.dump(filas, open(os.path.join(res, "h23_diag_acm.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
