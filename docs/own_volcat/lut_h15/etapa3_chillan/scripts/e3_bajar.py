r"""H15 etapa 3: bajadas para los 60 cuadros de evento (nunca full-disk a disco).

  python -I e3_bajar.py l1b   C10, C11, C14 y C15 en la ventana 83 × 94 (misma lectura que fetch_e2 / H13), desde
                              noaa-goes19 en AWS, por rango de bytes; ~1 MB por cuadro a E3_DIR\l1b
  python -I e3_bajar.py gfs   perfil GFS 0,25° por hora válida (misma lectura que fetch_gfs_e2) a E3_DIR\gfs,
                              las dos horas que encierran cada cuadro
Reanudable: salta lo que ya existe aquí o en los cachés de H13.
"""
import glob
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e3_comun as K  # noqa: E402
import h13_comun as H  # noqa: E402
import fetch_e2 as F  # noqa: E402

F.CACHE = K.L1B


def cuadros():
    return sorted(datetime.strptime(os.path.basename(f).split("_s")[1][:12], "%Y%m%d%H%M")
                  for f in glob.glob(os.path.join(K.EVDIR, "*.nc")))


def path_escena(dt):
    p = os.path.join(K.L1B, H.k(dt) + ".npz")
    return p if os.path.exists(p) else H.path_escena(dt)


def path_gfs(h):
    p = os.path.join(K.GFS, f"gfs_{h:%Y%m%d%H}.npz")
    return p if os.path.exists(p) else H.path_gfs_hora(h)


def get_scan(kk):
    dt = datetime.strptime(kk, "%Y%m%d_%H%M")
    if path_escena(dt) is not None:
        return kk, "cache"
    return F.get_scan(kk)


def horas():
    hs = set()
    for t in cuadros():
        h0, h1, _ = H.horas_que_encierran(t)
        hs |= {h0, h1}
    return sorted(hs)


if __name__ == "__main__":
    if sys.argv[1] == "l1b":
        ks = [H.k(t) for t in cuadros()]
        t0 = time.time()
        with ProcessPoolExecutor(6) as ex:
            for kk, st in ex.map(get_scan, ks):
                print(kk, st, f"{time.time() - t0:.0f}s", flush=True)
    elif sys.argv[1] == "gfs":
        import fetch_gfs_e2 as G
        G.OUT = K.GFS

        def una(h):
            if path_gfs(h) is not None:
                return h, "cache"
            err = None
            for i in range(3):
                try:
                    return h, G.bajar(h)[1]
                except Exception as e:  # noqa: BLE001
                    err = e
                    time.sleep(5 * (i + 1))
            return h, f"FALLA {err}"
        with ThreadPoolExecutor(1) as ex:
            for h, st in ex.map(una, horas()):
                print(f"{h:%Y-%m-%d %H}", st, flush=True)
