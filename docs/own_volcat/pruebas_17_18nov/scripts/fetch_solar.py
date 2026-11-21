"""Paso 2: lectura por ventana de C02 (0,5 km), C07 y C14 (2 km) para Chillan. Mismo metodo que fetch_mp.py.
Uso: python fetch_solar.py test   |   python fetch_solar.py plan [nproc]"""
import sys, os, time, json
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "solar")
DET = r"C:\Users\nmend\AppData\Local\Temp\claude\d6ea8719dcf88502\536a0873-47fb-4b33-9ee5-de0197c3f321\scratchpad\det"
WIN = json.load(open(os.path.join(DET, "window.json")))
_fs = None; _list = {}


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


def read(key, f_):
    import h5py
    y0, y1, x0, x1 = WIN["y0"] * f_, WIN["y1"] * f_, WIN["x0"] * f_, WIN["x1"] * f_
    err = None
    for i in range(4):
        try:
            with fs().open(key, "rb", block_size=2**18, cache_type="readahead") as fo:
                with h5py.File(fo, "r") as f:
                    r = f["Rad"]
                    raw = r[y0:y1, x0:x1].astype("float64")
                    fill = r.attrs["_FillValue"][0]
                    rad = raw * r.attrs["scale_factor"][0] + r.attrs["add_offset"][0]
                    rad[raw == fill] = np.nan
                    attrs = {}
                    for n in ("kappa0", "esun", "planck_fk1", "planck_fk2", "planck_bc1", "planck_bc2",
                              "earth_sun_distance_anomaly_in_AU"):
                        if n in f:
                            v = f[n][()]
                            attrs[n] = float(v) if np.ndim(v) == 0 else float(np.ravel(v)[0])
                    return rad.astype("float32"), attrs
        except Exception as e:  # noqa: BLE001
            err = e; time.sleep(2 * (i + 1))
    print("FALLA", key, repr(err), flush=True)
    return None, None


def get_scan(dt):
    out = os.path.join(OUT, f"{dt:%Y%m%d_%H%M}.npz")
    if os.path.exists(out):
        return dt, "cache", 0.0, 0
    t0 = time.time(); d = {}; meta = {}
    for b, f_ in ((2, 4), (7, 1), (14, 1)):
        k = key_for(dt, b)
        if k is None:
            return dt, "sin_key", time.time() - t0, 0
        rad, at = read(k, f_)
        if rad is None:
            return dt, "falla", time.time() - t0, 0
        d[f"rad{b:02d}"] = rad; meta[f"C{b:02d}"] = at
    d["meta"] = np.array(json.dumps(meta))
    np.savez_compressed(out + ".tmp.npz", **d)
    os.replace(out + ".tmp.npz", out)
    return dt, "ok", time.time() - t0, os.path.getsize(out)


def plan():
    sys.path.insert(0, DET)
    import comun as C
    import paso3_objetos as p  # sza()
    from datetime import timezone
    H = np.load(os.path.join(DET, "volcat", "huellas.npz"))
    pos = [dt for dt in C.POS_AJ + C.POS_PR if C.key(dt) in H.files and H[C.key(dt)].any()
           and p.sza(dt.replace(tzinfo=timezone.utc), C.VLAT, C.VLON) < 75]
    dts = set(pos)
    for dt in pos:
        for d in C.NEG_AJ_DIAS + C.NEG_PR_DIAS:
            dts.add(dt.replace(day=d))
    return pos, sorted(dts)


def run(dts, nproc):
    t0 = time.time(); n = 0; tot = 0
    with ProcessPoolExecutor(nproc) as ex:
        futs = [ex.submit(get_scan, dt) for dt in dts]
        for fu in as_completed(futs):
            dt, st, dur, sz = fu.result(); n += 1; tot += sz
            if st != "cache":
                print(f"{dt:%Y-%m-%d %H:%M} {st} {dur:.1f}s {sz/1e6:.2f}MB [{n}/{len(dts)} {time.time()-t0:.0f}s {tot/1e6:.0f}MB]", flush=True)
    print("listo", len(dts), f"{time.time()-t0:.0f}s", f"{tot/1e6:.0f}MB", flush=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sys.path.insert(0, HERE)
    if sys.argv[1] == "test":
        run([datetime(2026, 11, 10, 18, 0), datetime(2026, 11, 12, 18, 0)], 2)
    else:
        pos, dts = plan()
        print("positivos con sol alto", len(pos), "escenas a bajar", len(dts), flush=True)
        if sys.argv[1] == "plan":
            run(dts, int(sys.argv[2]) if len(sys.argv) > 2 else 8)
