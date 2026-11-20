"""H13: nodos del modelo radiativo (R_clr y R_cld por nivel) UNA vez por hora GFS.

Por que por hora: rt_niveles.tarea depende del scan solo a traves del perfil GFS (perfil, presion y temperatura
de superficie, tropopausa) y del cenit satelital, que es fijo por pixel. Todos los scans de una misma hora
GFS tienen los mismos nodos. Si la etapa 2 ya calculo nodos para esa hora (en cualquier scan), se reutilizan.
Uso: python h13_rt.py [n_procesos]  -> <H13DIR>/rt_hora/gfs_YYYYmmddHH.npz (reanudable)
"""
import os, sys, glob, shutil
import numpy as np
from datetime import datetime
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h13_comun as H  # noqa: E402
C = H.C
C.path_gfs = lambda dt: H.path_gfs_hora(C.hora_gfs(dt))   # que rt_niveles encuentre tambien los GFS nuevos
import rt_niveles as R  # noqa: E402
import rt_e2 as E  # noqa: E402


def horas():
    hs = set()
    for t in H.scans_necesarios():
        h0, h1, _ = H.horas_que_encierran(t); hs |= {h0, h1}
    return sorted(hs)


def reutilizar():
    m = {}
    for f in glob.glob(os.path.join(E.RTE2, "*.npz")):
        m.setdefault(str(np.load(f)["gfs"]), f)
    return m


def tarea(h):
    out = os.path.join(H.RTH, f"gfs_{h:%Y%m%d%H}.npz")
    if os.path.exists(out):
        return out, "ya"
    if H.path_gfs_hora(h) is None:
        return out, "sin_gfs"
    ys, xs = E.nodos()
    return R.tarea((out, h, ys, xs, np.ones(len(ys), bool)))


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    hs = horas(); m = reutilizar(); nre = 0; pend = []
    for h in hs:
        out = os.path.join(H.RTH, f"gfs_{h:%Y%m%d%H}.npz")
        if os.path.exists(out):
            continue
        f = m.get(f"gfs_{h:%Y%m%d%H}.npz")
        if f is not None:
            shutil.copyfile(f, out); nre += 1
        else:
            pend.append(h)
    print("horas", len(hs), "reutilizadas ahora", nre, "por calcular", len(pend), flush=True)
    with Pool(n) as pool:
        for out, msg in pool.imap_unordered(tarea, pend):
            print(os.path.basename(out), msg, flush=True)
