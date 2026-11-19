"""Baja la banda C13 (10,3 um) de GOES-19 L1b en la misma ventana del cache del detector previo.

Por que: la prueba London VAAC usa el canal SEVIRI de 10,8 um, que cae entre C13 (10,3) y C14 (11,2)
del ABI. El cache del detector previo solo tiene C11, C14 y C15; la variante con C13 necesita esta banda
en los mismos scans (positivos, negativos, 16-11 y los dias de referencia de cielo despejado).

Lectura remota por ventana con procesos (h5py tiene un lock global y con hilos se serializa), igual que
`fetch_mp.py` del detector previo. Coeficientes Planck SIEMPRE del NetCDF L1b (se guardan en planck_c13.json).
Cada scan se escribe atomico (tmp + replace), asi que un corte del PC no deja archivos a medias y la
corrida se retoma sola (salta lo que ya existe).

Uso: python fetch_c13.py <nproc>
"""
import os, sys, json, time
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rutas as R  # noqa: E402

_fs = None
_list = {}


def fs():
    global _fs
    if _fs is None:
        import s3fs
        _fs = s3fs.S3FileSystem(anon=True)
    return _fs


def listing(dt):
    p = f"noaa-goes19/ABI-L1b-RadF/{dt:%Y}/{dt.timetuple().tm_yday:03d}/{dt:%H}/"
    if p not in _list:
        for i in range(4):
            try:
                _list[p] = fs().ls(p); break
            except FileNotFoundError:
                _list[p] = []; break
            except Exception:  # noqa: BLE001
                time.sleep(2 * (i + 1))
        else:
            _list[p] = []
    return _list[p]


def key_for(dt, band):
    tag = f"_s{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}"
    for k in listing(dt):
        n = k.split("/")[-1]
        if f"C{band:02d}_" in n and tag in n:
            return k
    return None


def read(key, win):
    import h5py
    err = None
    for i in range(4):
        try:
            with fs().open(key, "rb", block_size=2**18, cache_type="readahead") as fo:
                with h5py.File(fo, "r") as f:
                    r = f["Rad"]
                    raw = r[win["y0"]:win["y1"], win["x0"]:win["x1"]].astype("float64")
                    fill = r.attrs["_FillValue"][0]
                    rad = raw * r.attrs["scale_factor"][0] + r.attrs["add_offset"][0]
                    rad[raw == fill] = np.nan
                    co = [float(f[n][()]) for n in ("planck_fk1", "planck_fk2", "planck_bc1", "planck_bc2")]
                    fk1, fk2, bc1, bc2 = co
                    with np.errstate(invalid="ignore", divide="ignore"):
                        rad = np.where(rad > 0, rad, np.nan)
                        bt = ((fk2 / np.log(fk1 / rad + 1)) - bc1) / bc2
                    return bt.astype("float32"), co
        except Exception as e:  # noqa: BLE001
            err = e; time.sleep(2 * (i + 1))
    print("FALLA", key, repr(err), flush=True)
    return None, None


def get_scan(dt):
    out = os.path.join(R.CACHE13, f"{dt:%Y%m%d_%H%M}.npz")
    if os.path.exists(out):
        return dt, "cache", 0.0
    t0 = time.time()
    win = json.load(open(R.WINDOW))
    k = key_for(dt, 13)
    if k is None:
        return dt, "sin_key", time.time() - t0
    bt, co = read(k, win)
    if bt is None:
        return dt, "falla", time.time() - t0
    np.savez_compressed(out + ".tmp.npz", b13=bt)
    os.replace(out + ".tmp.npz", out)
    if not os.path.exists(R.PLANCK13):
        tmp = R.PLANCK13 + ".tmp"
        json.dump({"C13": co, "archivo": k}, open(tmp, "w"))
        os.replace(tmp, R.PLANCK13)
    return dt, "ok", time.time() - t0


def objetivos():
    """Todos los scans del cache del detector previo; primero los de la foto fija (los del estudio)."""
    snap = set(open(R.SNAPSHOT).read().split())
    todos = sorted(f for f in os.listdir(R.CACHE_PREV) if f.endswith(".npz") and ".tmp" not in f)
    dts = [datetime.strptime(f[:13], "%Y%m%d_%H%M") for f in todos]
    return sorted(dts, key=lambda t: (f"{t:%Y%m%d_%H%M}.npz" not in snap, t))


if __name__ == "__main__":
    os.makedirs(R.CACHE13, exist_ok=True)
    nproc = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    dts = objetivos()
    t0 = time.time(); n = 0
    with ProcessPoolExecutor(nproc) as ex:
        futs = [ex.submit(get_scan, dt) for dt in dts]
        for fu in as_completed(futs):
            dt, st, dur = fu.result(); n += 1
            if st != "cache":
                print(f"{dt:%Y-%m-%d %H:%M} {st} {dur:.1f}s  [{n}/{len(dts)}  {time.time()-t0:.0f}s]", flush=True)
    print("listo", len(dts), f"{time.time()-t0:.0f}s total", flush=True)
