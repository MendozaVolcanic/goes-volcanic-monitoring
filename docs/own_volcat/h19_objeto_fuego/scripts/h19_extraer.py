"""H19: pasa a npz (fuera del repo) las variables por pixel y por objeto de cada cuadro. No calcula acuerdos.
Universo de pixeles guardado: todo pixel de un objeto de geocatASHOBJ o geocatICEOBJ, todo pixel con grupo
de ceniza o de nube convectiva (actual o del cuadro anterior) y un margen de 6 pixeles alrededor de los grupos.
Uso: venv_hdf4 python -I h19_extraer.py REF SALIDA"""
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h19_io import ruta, leer, HORAS, DB


def lista(O, pre):
    size = O[pre + "Object_Size"].astype(int)
    fin = np.cumsum(size)
    ini = fin - size
    x = O[pre + "Object_X_Index"].astype(int) - 1
    y = O[pre + "Object_Y_Index"].astype(int) - 1
    ido = np.full((601, 601), -1, np.int32)
    for k in range(len(size)):
        ido[y[ini[k]:fin[k]], x[ini[k]:fin[k]]] = k
    return ido


def dilata(m, n):
    out = m.copy()
    for _ in range(n):
        o = out.copy()
        o[1:, :] |= out[:-1, :]; o[:-1, :] |= out[1:, :]
        o[:, 1:] |= out[:, :-1]; o[:, :-1] |= out[:, 1:]
        out = o
    return out


def main(ref, out):
    os.makedirs(out, exist_ok=True)
    prev = None
    for h in HORAS:
        capas = {}
        for tipo in ["L2", "L2S1", "DIAG", "DIAGS1", "L1", "RTM"]:
            D = leer(ruta(ref, tipo, h))
            for k, a in D.items():
                if a.shape == (601, 601):
                    capas.setdefault(k, a)
                elif a.ndim == 3 and a.shape[:2] == (601, 601):
                    for i in range(a.shape[2]):
                        capas.setdefault("%s__%d" % (k, i), a[:, :, i])
        A = leer(ruta(ref, "ASHOBJ", h), escalar=False)
        I = leer(ruta(ref, "ICEOBJ", h), escalar=False)
        H = leer(ruta(ref, "HOTOBJ", h), escalar=False)
        idA = lista(A, "ASHOBJ_")
        idI = lista(I, "ICEOBJ_")
        idH = lista(H, "HOTOBJ_") if len(H.get("HOTOBJ_Object_Size", [])) else np.full((601, 601), -1, np.int32)
        ag = capas["Ash_Group_Id_2d"] > 0
        ig = capas["Ice_Group_Id_2d"] > 0
        grupos = ag | ig
        U = (idA >= 0) | (idI >= 0) | dilata(grupos, 6)
        if prev is not None:
            U |= prev["ag"] | prev["ig"]
        iy, ix = np.nonzero(U)
        d = {"iy": iy.astype(np.int16), "ix": ix.astype(np.int16),
             "idA": idA[U], "idI": idI[U], "idH": idH[U]}
        for k, a in capas.items():
            d["p__" + k] = a[U].astype(np.float32) if a.dtype.kind == "f" else a[U]
        if prev is not None:
            d["prev__ag"] = prev["ag"][U]
            d["prev__ig"] = prev["ig"][U]
            d["prev__P"] = prev["P"][U].astype(np.float32)
            d["prev__idA"] = prev["idA"][U]
        for pre, O in (("A__", A), ("I__", I), ("H__", H)):
            for k, a in O.items():
                kk = k.replace("ASHOBJ_", "").replace("ICEOBJ_", "").replace("HOTOBJ_", "").replace(DB, "")
                if "Object_X_Index" in kk or "Object_Y_Index" in kk:
                    continue
                d[pre + kk] = a
        np.savez_compressed(os.path.join(out, "h19_%s.npz" % h), **d)
        prev = {"ag": ag, "ig": ig, "idA": idA,
                "P": capas["vcat_ashdet_pix_2_7_10_11_13_14_15_ash_probability"]}
        print(h, "pixeles", len(iy), "variables", len(d), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
