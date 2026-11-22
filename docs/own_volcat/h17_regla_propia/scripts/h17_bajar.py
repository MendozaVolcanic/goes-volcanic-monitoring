r"""H17: baja de NOAA S3 (ABI-L1b-RadF, GOES-19, sin credenciales) las bandas que faltan en los cachés, sólo la ventana
del detector. Guarda radiancia + coeficientes Planck del NetCDF en D:\goes_cache\h17\l1b\<cuadro>.npz.

Lista de cuadros (decidida antes de medir, sólo por cobertura, sin mirar resultados):
 A) C07 para todo cuadro que ya tiene C14 y C15 en los cachés y no tiene C07 (calor en los cuadros de la pluma).
 B) C07, C14 y C15 cada 10 min en las mañanas de los eventos VOLCAT que no tienen línea base IR: 08 al 14-11 de
    11:00 a 14:50 UTC (evento del 14-11 12:40) y 12 al 18-11 de 08:40 a 11:40 UTC (evento del 18-11 10:10).
Reanudable. Uso: python -I h17_bajar.py [nproc]
"""
import os
import sys
import time
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h17_comun as K  # noqa: E402

_fs = None
_list = {}


def fs():
    global _fs
    if _fs is None:
        import s3fs
        _fs = s3fs.S3FileSystem(anon=True)
    return _fs


def key_for(dt, b):
    p = f"noaa-goes19/ABI-L1b-RadF/{dt:%Y}/{dt.timetuple().tm_yday:03d}/{dt:%H}/"
    if p not in _list:
        for i in range(4):
            try:
                _list[p] = fs().ls(p)
                break
            except FileNotFoundError:
                _list[p] = []
                break
            except Exception:
                time.sleep(2 * (i + 1))
        else:
            _list[p] = []
    tag = f"_s{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}"
    for kk in _list[p]:
        n = kk.split("/")[-1]
        if f"C{b:02d}_" in n and tag in n:
            return kk
    return None


def leer(key):
    import h5py
    W = K.WIN
    err = None
    for i in range(4):
        try:
            with fs().open(key, "rb", block_size=2**18, cache_type="readahead") as fo, h5py.File(fo, "r") as f:
                r = f["Rad"]
                raw = r[W["y0"]:W["y1"], W["x0"]:W["x1"]].astype("float64")
                rad = raw * r.attrs["scale_factor"][0] + r.attrs["add_offset"][0]
                rad[raw == r.attrs["_FillValue"][0]] = np.nan
                co = [float(np.ravel(f[n][()])[0]) for n in ("planck_fk1", "planck_fk2", "planck_bc1", "planck_bc2")]
                return rad.astype("float32"), np.array(co)
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(2 * (i + 1))
    print("FALLA", key, repr(err), flush=True)
    return None, None


def tarea(c, bandas):
    dt = datetime.strptime(c, "%Y%m%d_%H%M")
    out = os.path.join(K.L1B17, c + ".npz")
    d = dict(np.load(out)) if os.path.exists(out) else {}
    t0 = time.time()
    falta = []
    for b in bandas:
        if f"rad{b}" in d:
            continue
        kk = key_for(dt, b)
        if kk is None:
            falta.append(b)
            continue
        rad, co = leer(kk)
        if rad is None:
            falta.append(b)
            continue
        d[f"rad{b}"] = rad
        d[f"co{b}"] = co
        d[f"key{b}"] = np.array(kk)
    if d:
        np.savez_compressed(out + ".tmp.npz", **d)
        os.replace(out + ".tmp.npz", out)
    return c, falta, time.time() - t0


def rango(dias, h0, h1):
    for d in dias:
        t = d.replace(hour=h0[0], minute=h0[1])
        while t <= d.replace(hour=h1[0], minute=h1[1]):
            yield t
            t += timedelta(minutes=10)


def lista():
    idx = K.indice()
    tareas = {}
    for c, bs in idx.items():
        if 14 in bs and 15 in bs and 7 not in bs:
            tareas[c] = [7]
    extra = list(rango([datetime(2026, 11, d) for d in range(8, 15)], (11, 0), (14, 50))) + \
        list(rango([datetime(2026, 11, d) for d in range(12, 19)], (8, 40), (11, 40)))
    for t in extra:
        c = K.k(t)
        falta = [b for b in (7, 14, 15) if b not in idx.get(c, {})]
        if falta:
            tareas[c] = sorted(set(tareas.get(c, []) + falta))
    return sorted(tareas.items())


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    T = lista()
    if len(sys.argv) > 2 and sys.argv[2] == "contar":
        print("tareas", len(T), "bandas", sum(len(b) for _, b in T))
        sys.exit()
    print("tareas", len(T), "bandas", sum(len(b) for _, b in T), flush=True)
    t0 = time.time()
    hechas = 0
    with ProcessPoolExecutor(n) as ex:
        fut = [ex.submit(tarea, c, b) for c, b in T]
        for f in as_completed(fut):
            c, falta, s = f.result()
            hechas += 1
            if falta:
                print("sin_key", c, falta, flush=True)
            if hechas % 25 == 0:
                print(f"{hechas}/{len(T)} {time.time() - t0:.0f}s", flush=True)
    print("FIN", hechas, f"{time.time() - t0:.0f}s", flush=True)
