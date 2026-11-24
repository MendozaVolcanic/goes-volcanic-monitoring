r"""S21c: baja de NOAA S3 (sin credenciales) la ventana de 81 x 81 px de C02 de GOES-18 y GOES-19 centrada en el
centro de emision, para los cuadros del criterio §3. Guarda radiancia, DQF, kappa0 y el nombre del archivo en
D:\goes_notas\s21\c\l1b\g<sat>_<AAAAMMDD_HHMM>.npz. Reanudable. Corta si D: baja de 6 GB libres.

Uso: python -I s21c_bajar.py [nproc]
"""
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s21c_comun as K  # noqa: E402

MEDIO = 40
_fs = None


def fs():
    global _fs
    if _fs is None:
        import s3fs
        _fs = s3fs.S3FileSystem(anon=True)
    return _fs


def centro(sat):
    r, c = K.a_pixel(sat, *K.VENT, K.CRATER_KM * 1000)
    return int(round(float(r))), int(round(float(c)))


def lista_cuadros():
    out = []
    def tramo(d, h0, m0, h1, m1):
        t, fin = datetime(*d, h0, m0), datetime(*d, h1, m1)
        while t <= fin:
            out.append(t)
            t += timedelta(minutes=10)
    tramo((2026, 10, 28), 15, 0, 22, 30)
    for d in ((2026, 9, 21), (2026, 10, 15), (2026, 10, 16), (2026, 10, 17)):
        tramo(d, 14, 0, 22, 30)
    tramo((2026, 10, 25), 14, 10, 14, 50)
    tramo((2026, 10, 28), 14, 30, 14, 50)       # registro de navegacion del 28-10 (14:40) y vecinos
    return sorted(set(out))


def listar(sat, h):
    p = f"noaa-goes{sat}/ABI-L1b-RadF/{h:%Y}/{h.timetuple().tm_yday:03d}/{h:%H}/"
    for i in range(4):
        try:
            return fs().ls(p)
        except FileNotFoundError:
            return []
        except Exception:  # noqa: BLE001
            time.sleep(2 * (i + 1))
    return []


def leer(key, r0, c0):
    import h5py
    err = None
    for i in range(4):
        try:
            with fs().open(key, "rb", block_size=2**18, cache_type="readahead") as fo, h5py.File(fo, "r") as f:
                r = f["Rad"]
                raw = r[r0 - MEDIO:r0 + MEDIO + 1, c0 - MEDIO:c0 + MEDIO + 1].astype("float64")
                rad = raw * r.attrs["scale_factor"][0] + r.attrs["add_offset"][0]
                rad[raw == r.attrs["_FillValue"][0]] = np.nan
                dqf = f["DQF"][r0 - MEDIO:r0 + MEDIO + 1, c0 - MEDIO:c0 + MEDIO + 1]
                k0 = float(np.ravel(f["kappa0"][()])[0])
                lonp = float(np.ravel(f["goes_imager_projection"].attrs["longitude_of_projection_origin"])[0])
                return rad.astype("float32"), dqf.astype("uint8"), k0, lonp
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(2 * (i + 1))
    print("FALLA", key, repr(err), flush=True)
    return None


def uno(sat, dt):
    out = K.ruta_cuadro(sat, dt)
    if os.path.exists(out):
        return sat, dt, "ya"
    if shutil.disk_usage(K.TRABAJO).free < 6 * 2**30:
        return sat, dt, "DISCO"
    tag = f"_s{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}"
    kk = [x for x in listar(sat, dt) if "M6C02_" in x and tag in x]
    if not kk:
        return sat, dt, "sin archivo"
    r0, c0 = centro(sat)
    res = leer(kk[0], r0, c0)
    if res is None:
        return sat, dt, "falla"
    rad, dqf, k0, lonp = res
    if abs(lonp - K.SAT_LON[sat]) > 1e-6:
        return sat, dt, f"proyeccion inesperada {lonp}"
    tmp = out + f".{os.getpid()}.tmp.npz"
    np.savez_compressed(tmp, rad=rad, dqf=dqf, kappa0=k0, fila0=r0 - MEDIO, col0=c0 - MEDIO,
                        archivo=np.array(kk[0].split("/")[-1]))
    os.replace(tmp, out)
    return sat, dt, "ok"


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    os.makedirs(os.path.join(K.TRABAJO, "l1b"), exist_ok=True)
    tareas = [(s, t) for t in lista_cuadros() for s in (18, 19)]
    print(f"{len(tareas)} cuadros-satelite", flush=True)
    t0 = time.time()
    cuenta = {}
    with ProcessPoolExecutor(n) as ex:
        futs = [ex.submit(uno, s, t) for s, t in tareas]
        for i, fu in enumerate(as_completed(futs)):
            s, t, est = fu.result()
            cuenta[est] = cuenta.get(est, 0) + 1
            if est not in ("ok", "ya"):
                print(s, f"{t:%Y-%m-%d %H:%M}", est, flush=True)
            if i % 50 == 0:
                print(i, f"{time.time() - t0:.0f} s", cuenta, flush=True)
    print("FIN", cuenta, f"{time.time() - t0:.0f} s", flush=True)
