r"""Baja de NOAA S3 (ABI-L1b-RadF, GOES-19, sin credenciales) C07 y C14 sólo en las ventanas de los sitios, para la
lista de cuadros fijada en el criterio (§3). Guarda D:\goes_cache\vrp_nocturno\l1b\<cuadro>.npz con, por sitio,
rad7_<i>, rad14_<i> y los Planck co7, co14. Reanudable.
Uso: python -I vn_bajar.py [nproc] [contar]
"""
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vn_comun as K  # noqa: E402

SITIOS = K.H17_SITIOS + K.CONTROLES + K.ACTIVOS + K.EXTRA
CHILLAN3 = [SITIOS.index(n) for n in K.H17_SITIOS]
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
            _list[p] = None
    if _list[p] is None:
        return "ERR"
    tag = f"_s{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}"
    for kk in _list[p]:
        n = kk.split("/")[-1]
        if f"C{b:02d}_" in n and tag in n:
            return kk
    return None


def leer(key, idx):
    import h5py
    err = None
    for i in range(4):
        try:
            out = {}
            with fs().open(key, "rb", block_size=2**18, cache_type="readahead") as fo, h5py.File(fo, "r") as f:
                r = f["Rad"]
                sf, ao, fv = r.attrs["scale_factor"][0], r.attrs["add_offset"][0], r.attrs["_FillValue"][0]
                for j in sorted(idx, key=lambda j: K.ventana(SITIOS[j])[0]):
                    r0, r1, c0, c1 = K.ventana(SITIOS[j])
                    raw = r[r0:r1, c0:c1].astype("float64")
                    rad = raw * sf + ao
                    rad[raw == fv] = np.nan
                    out[j] = rad.astype("float32")
                co = np.array([float(np.ravel(f[n][()])[0])
                               for n in ("planck_fk1", "planck_fk2", "planck_bc1", "planck_bc2")])
            return out, co
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(2 * (i + 1))
    print("FALLA", key, repr(err), flush=True)
    return None, None


def tarea(c, idx):
    dt = datetime.strptime(c, "%Y%m%d_%H%M")
    fn = os.path.join(K.L1B, c + ".npz")
    d = dict(np.load(fn)) if os.path.exists(fn) else {}
    t0 = time.time()
    falta = []
    for b in (7, 14):
        need = [j for j in idx if f"rad{b}_{j}" not in d]
        if not need:
            continue
        kk = key_for(dt, b)
        if kk is None or kk == "ERR":
            falta.append((b, kk))
            continue
        out, co = leer(kk, need)
        if out is None:
            falta.append((b, "lectura"))
            continue
        for j, rad in out.items():
            d[f"rad{b}_{j}"] = rad
        d[f"co{b}"] = co
    if d:
        np.savez_compressed(fn + ".tmp.npz", **d)
        os.replace(fn + ".tmp.npz", fn)
    return c, falta, time.time() - t0


def noches(d0, d1, paso=1):
    d = d0
    while d <= d1:
        yield d
        d += timedelta(days=paso)


def cuadros_noche(d):
    """Cuadros cada 30 min de 23:00 UTC del día previo a 10:30 UTC del día d (cubre toda la noche en Chile en
    septiembre a noviembre; la noche se recorta después por cenit solar)."""
    t = d - timedelta(hours=1)
    while t <= d + timedelta(hours=10, minutes=30):
        yield t
        t += timedelta(minutes=30)


def lista():
    """Criterio §3. Serie A: Chillán, Antuco, Longaví, todas las noches del 26-08 al 19-10 y del 20-11 al 22-11.
    Serie B: todos los sitios, una noche de cada tres del 26-08 al 22-11 (la primera semana es arranque)."""
    T = {}
    A = list(noches(datetime(2026, 8, 26), datetime(2026, 10, 19))) + \
        list(noches(datetime(2026, 11, 20), datetime(2026, 11, 22)))
    B = list(noches(datetime(2026, 8, 26), datetime(2026, 11, 22), 3))
    for d in A:
        for t in cuadros_noche(d):
            T.setdefault(K.k(t) if hasattr(K, "k") else f"{t:%Y%m%d_%H%M}", set()).update(CHILLAN3)
    for d in B:
        for t in cuadros_noche(d):
            T.setdefault(f"{t:%Y%m%d_%H%M}", set()).update(range(len(SITIOS)))
    ahora = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=30)
    return sorted((c, sorted(s)) for c, s in T.items() if datetime.strptime(c, "%Y%m%d_%H%M") <= ahora)


if __name__ == "__main__":
    os.makedirs(K.L1B, exist_ok=True)
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    T = lista()
    if len(sys.argv) > 2 and sys.argv[2] == "contar":
        print("cuadros", len(T), "con todos los sitios", sum(len(s) == len(SITIOS) for _, s in T))
        sys.exit()
    if len(sys.argv) > 2 and sys.argv[2] == "uno":
        T = T[-1:]
    print("cuadros", len(T), flush=True)
    t0 = time.time()
    hechas = 0
    with ProcessPoolExecutor(n) as ex:
        fut = [ex.submit(tarea, c, s) for c, s in T]
        for f in as_completed(fut):
            c, falta, s = f.result()
            hechas += 1
            if falta:
                print("falta", c, falta, flush=True)
            if hechas % 50 == 0:
                print(f"{hechas}/{len(T)} {time.time() - t0:.0f}s", flush=True)
    print("FIN", hechas, f"{time.time() - t0:.0f}s", flush=True)
