"""H7: lectura remota por ventana de L1b GOES-19 (C11/C14/C15) para Chillan.
Copia de det/fetch.py con la MISMA ventana (det/window.json, solo lectura) y cache propia en h7/cache.
BT con los coeficientes Planck de cada NetCDF L1b (planck_fk1, fk2, bc1, bc2).
Uso: python fetch_l1b.py YYYY-MM-DD HH:MM HH:MM [paso_min]"""
import sys, os, time, json, numpy as np, h5py, s3fs
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache"); os.makedirs(CACHE, exist_ok=True)
WIN = json.load(open(r"C:\Users\nmend\AppData\Local\Temp\claude\d6ea8719dcf88502\536a0873-47fb-4b33-9ee5-de0197c3f321\scratchpad\det\window.json"))
fs = s3fs.S3FileSystem(anon=True)
_list = {}


def listing(dt):
    p = f"noaa-goes19/ABI-L1b-RadF/{dt:%Y}/{dt.timetuple().tm_yday:03d}/{dt:%H}/"
    if p not in _list:
        for i in range(4):
            try:
                _list[p] = fs.ls(p); break
            except FileNotFoundError:
                _list[p] = []; break
            except Exception:
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


def read(key):
    err = None
    for i in range(4):
        try:
            with fs.open(key, "rb", block_size=2**18, cache_type="readahead") as fo:
                with h5py.File(fo, "r") as f:
                    r = f["Rad"]
                    raw = r[WIN["y0"]:WIN["y1"], WIN["x0"]:WIN["x1"]].astype("float64")
                    fill = r.attrs["_FillValue"][0]
                    rad = raw * r.attrs["scale_factor"][0] + r.attrs["add_offset"][0]
                    rad[raw == fill] = np.nan
                    fk1, fk2, bc1, bc2 = (float(f[n][()]) for n in ("planck_fk1", "planck_fk2", "planck_bc1", "planck_bc2"))
                    with np.errstate(invalid="ignore", divide="ignore"):
                        rad = np.where(rad > 0, rad, np.nan)
                        bt = ((fk2 / np.log(fk1 / rad + 1)) - bc1) / bc2
                    return bt.astype("float32")
        except Exception as e:
            err = e; time.sleep(2 * (i + 1))
    print("FALLA", key, err, flush=True)
    return None


def get_scan(dt):
    out = os.path.join(CACHE, f"{dt:%Y%m%d_%H%M}.npz")
    if os.path.exists(out):
        return "cache"
    bts = {}
    for b in (11, 14, 15):
        k = key_for(dt, b)
        if k is None:
            return "sin_key"
        bt = read(k)
        if bt is None:
            return "falla"
        bts[f"b{b}"] = bt
    tmp = out + ".tmp.npz"
    np.savez_compressed(tmp, **bts); os.replace(tmp, out)
    return "ok"


if __name__ == "__main__":
    d0 = datetime.strptime(sys.argv[1] + " " + sys.argv[2], "%Y-%m-%d %H:%M")
    d1 = datetime.strptime(sys.argv[1] + " " + sys.argv[3], "%Y-%m-%d %H:%M")
    step = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    dts = []; t = d0
    while t <= d1:
        dts.append(t); t += timedelta(minutes=step)
    t0 = time.time()
    with ThreadPoolExecutor(6) as ex:
        for dt, st in zip(dts, ex.map(get_scan, dts)):
            print(dt, st, flush=True)
    print("listo", sys.argv[1:], f"{time.time()-t0:.0f}s", flush=True)
