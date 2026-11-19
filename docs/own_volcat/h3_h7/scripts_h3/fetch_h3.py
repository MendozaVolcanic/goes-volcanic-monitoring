"""H3: lectura remota por ventana de L1b GOES-19 (C10, C11, C14, C15) para Chillan.

Misma ventana 83x94 que el estudio previo (det/window.json). Guarda por scan un npz en h3/cache con
radiancia (mW m-2 sr-1 (cm-1)-1), BT (K) y los coeficientes Planck (fk1, fk2, bc1, bc2) de CADA NetCDF.
No toca el cache viejo.  Uso: python fetch_h3.py  (lista de scans fija, ver escenas()).
"""
import sys, os, time, json
import numpy as np, h5py, s3fs
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache"); os.makedirs(CACHE, exist_ok=True)
DET = r"C:\Users\nmend\AppData\Local\Temp\claude\d6ea8719dcf88502\536a0873-47fb-4b33-9ee5-de0197c3f321\scratchpad\det"
WIN = json.load(open(os.path.join(DET, "window.json")))
BANDS = (10, 11, 14, 15)
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
            with fs.open(key, "rb", block_size=2**16, cache_type="blockcache") as fo:
                with h5py.File(fo, "r") as f:
                    r = f["Rad"]
                    raw = r[WIN["y0"]:WIN["y1"], WIN["x0"]:WIN["x1"]].astype("float64")
                    fill = r.attrs["_FillValue"][0]
                    rad = raw * r.attrs["scale_factor"][0] + r.attrs["add_offset"][0]
                    rad[raw == fill] = np.nan
                    co = tuple(float(f[n][()]) for n in ("planck_fk1", "planck_fk2", "planck_bc1", "planck_bc2"))
                    fk1, fk2, bc1, bc2 = co
                    with np.errstate(invalid="ignore", divide="ignore"):
                        rp = np.where(rad > 0, rad, np.nan)
                        bt = ((fk2 / np.log(fk1 / rp + 1)) - bc1) / bc2
                    return rad.astype("float32"), bt.astype("float32"), np.array(co)
        except Exception as e:
            err = e; time.sleep(2 * (i + 1))
    print("FALLA", key, err, flush=True)
    return None


def get_scan(dt):
    out = os.path.join(CACHE, f"{dt:%Y%m%d_%H%M}.npz")
    if os.path.exists(out):
        return "cache"
    d = {}
    for b in BANDS:
        k = key_for(dt, b)
        if k is None:
            return f"sin_key_C{b}"
        r = read(k)
        if r is None:
            return f"falla_C{b}"
        d[f"rad{b}"], d[f"bt{b}"], d[f"co{b}"] = r
        d[f"key{b}"] = np.array(k.split("/")[-1])
    tmp = out + ".tmp.npz"
    np.savez_compressed(tmp, **d); os.replace(tmp, out)
    return "ok"


def escenas():
    c12 = [datetime(2026, 10, d) for d in (26, 27, 30, 31)] + [datetime(2026, 11, d) for d in range(1, 7)]
    c3 = [datetime(2026, 11, d) for d in (1, 2, 3, 4, 5, 6, 9, 12, 13, 15)]
    out = []
    for hm in ("22:40", "23:00", "23:20", "23:40"):
        h, m = int(hm[:2]), int(hm[3:])
        out += [d.replace(hour=h, minute=m) for d in [datetime(2026, 10, 28)] + c12]
    for hm in ("01:00", "01:10", "01:20"):
        h, m = int(hm[:2]), int(hm[3:])
        out += [d.replace(hour=h, minute=m) for d in [datetime(2026, 10, 29)] + c12]
    import pandas as pd
    t = pd.read_csv(os.path.join(DET, "volcat", "cuadros_10min.csv"))
    pos = t[(t.toca_crater_10km == 1) & t.slot_utc.str.startswith("2026-11-14")].slot_utc
    for s in pos:
        h, m = int(s[11:13]), int(s[14:16])
        out += [d.replace(hour=h, minute=m) for d in [datetime(2026, 11, 14)] + c3]
    return out


if __name__ == "__main__":
    dts = escenas()
    print("scans", len(dts), flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(12) as ex:
        for dt, st in zip(dts, ex.map(get_scan, dts, chunksize=1)):
            if st != "cache":
                print(dt, st, f"{time.time()-t0:.0f}s", flush=True)
    print("listo", f"{time.time()-t0:.0f}s", flush=True)
