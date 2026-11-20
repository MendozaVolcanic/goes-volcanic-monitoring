"""H13: bajadas por ventana (nunca full-disk a disco). Uso:
  python fetch_h13.py lista            -> escribe <H13DIR>/faltan_l1b.txt y faltan_gfs.txt
  python fetch_h13.py l1b [n_proc]     (C10, C11, C14, C15 en la ventana 83 x 94, misma lectura que fetch_e2)
  python fetch_h13.py gfs [n_hilos]    (perfil GFS por hora valida, misma lectura que fetch_gfs_e2)
  python fetch_h13.py png DIA [DIA ...] (PNG Ash_Height de SSEC, para conservar las etiquetas antes de que venzan)
Reanudable: salta lo que ya existe en cualquiera de los caches.
"""
import os, sys, time
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h13_comun as H  # noqa: E402
import fetch_e2 as F  # noqa: E402  (de reproducir_volcat/scripts, via sys.path de h13_comun)

F.CACHE = H.CACHE13
F.PNGD = H.PNG13


def get_scan(kk):
    dt = datetime.strptime(kk, "%Y%m%d_%H%M")
    if H.path_escena(dt) is not None:
        return kk, "cache"
    return F.get_scan(kk)


def lista():
    sc = H.scans_necesarios()
    falt = [H.k(t) for t in sc if H.path_escena(t) is None]
    open(os.path.join(H.H13DIR, "faltan_l1b.txt"), "w").write("\n".join(falt) + "\n")
    horas = set()
    for t in sc:
        h0, h1, _ = H.horas_que_encierran(t); horas |= {h0, h1}
    fh = sorted(h for h in horas if H.path_gfs_hora(h) is None)
    open(os.path.join(H.H13DIR, "faltan_gfs.txt"), "w").write("\n".join(f"{h:%Y%m%d%H}00" for h in fh) + "\n")
    print("scans necesarios", len(sc), "faltan L1b", len(falt), "| horas GFS", len(horas), "faltan", len(fh))


def gfs(nh):
    import fetch_gfs_e2 as G
    G.OUT = H.GFS13
    hs = [datetime.strptime(l.strip(), "%Y%m%d%H%M") for l in open(os.path.join(H.H13DIR, "faltan_gfs.txt")) if l.strip()]
    def una(h):  # noqa: E306
        if H.path_gfs_hora(h) is not None:
            return h, "cache"
        for i in range(3):
            try:
                return h, G.bajar(h)[1]
            except Exception as e:
                err = e; time.sleep(5 * (i + 1))
        return h, f"FALLA {err}"
    with ThreadPoolExecutor(nh) as ex:
        for h, st in ex.map(una, hs):
            print(f"{h:%Y-%m-%d %H}", st, flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "lista":
        lista()
    elif sys.argv[1] == "l1b":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
        ks = [l.strip() for l in open(os.path.join(H.H13DIR, "faltan_l1b.txt")) if l.strip()]
        print("scans", len(ks), flush=True); t0 = time.time()
        with ProcessPoolExecutor(n) as ex:
            for kk, st in ex.map(get_scan, ks):
                print(kk, st, f"{time.time() - t0:.0f}s", flush=True)
    elif sys.argv[1] == "gfs":
        gfs(int(sys.argv[2]) if len(sys.argv) > 2 else 6)
    elif sys.argv[1] == "png":
        with ThreadPoolExecutor(3) as ex:
            list(ex.map(F.png_dia, sys.argv[2:]))
