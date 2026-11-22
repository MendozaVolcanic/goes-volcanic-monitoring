"""H9: lectura por ventana de C07 (3,9 um) y C14 (11,2 um) de ABI L1b RadF para todos los cuadros del inventario
VOLCAT de Chillan (20-10 al 19-11-2026). Ventana = la del cache del detector (window.json, 83 x 94 pixeles de 2 km),
que contiene Chillan y los dos volcanes de control (Antuco y Nevado de Longavi). Guarda radiancia y coeficientes
Planck de cada NetCDF; la BT se calcula despues. Reanudable: salta lo que ya esta en disco.
Uso: python fetch_c07.py test | python fetch_c07.py todo [nproc]
"""
import sys, os, time, json
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np

SCR = r"D:\goes_notas\scratch_rescate_2026-11-21\h9_calor_rayos_11c46882"
OUT = os.path.join(SCR, "c07cache")
DET = r"D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat"
B73 = r"D:\goes_cache\h13\shim\b73"
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


def read(key):
    import h5py
    y0, y1, x0, x1 = WIN["y0"], WIN["y1"], WIN["x0"], WIN["x1"]
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
                    dqf = f["DQF"][y0:y1, x0:x1].astype("int8")
                    co = [float(np.ravel(f[n][()])[0]) for n in ("planck_fk1", "planck_fk2", "planck_bc1", "planck_bc2")]
                    return rad.astype("float32"), dqf, np.array(co)
        except Exception as e:  # noqa: BLE001
            err = e; time.sleep(2 * (i + 1))
    print("FALLA", key, repr(err), flush=True)
    return None, None, None


def get_scan(dt):
    out = os.path.join(OUT, f"{dt:%Y%m%d_%H%M}.npz")
    if os.path.exists(out):
        return dt, "cache", 0.0
    miss = os.path.join(OUT, f"{dt:%Y%m%d_%H%M}.sin_key")
    if os.path.exists(miss):
        return dt, "cache_sin_key", 0.0
    t0 = time.time(); d = {}
    for b in (7, 14):
        k = key_for(dt, b)
        if k is None:
            open(miss, "w").write(f"C{b:02d}")
            return dt, "sin_key", time.time() - t0
        rad, dqf, co = read(k)
        if rad is None:
            return dt, "falla", time.time() - t0
        d[f"rad{b}"] = rad; d[f"dqf{b}"] = dqf; d[f"co{b}"] = co; d[f"key{b}"] = np.array(k)
    np.savez_compressed(out + ".tmp.npz", **d)
    os.replace(out + ".tmp.npz", out)
    return dt, "ok", time.time() - t0


def frames():
    """Orden de prioridad (el ancho de banda manda, ~0,7 MB/s hacia S3 el 19-11):
    0) positivos y la hora previa a cada uno; 1) mismos minutos UTC de los positivos nocturnos (cenit >= 80) en
    +-10 dias, que deciden H9a; 2) mismos minutos de los positivos diurnos en +-10 dias (extension); 3) el resto,
    noche antes que dia (H9b, tasa base de H9c)."""
    a = json.load(open(os.path.join(B73, "inv_local.json"))) + json.load(open(os.path.join(B73, "inv_new.json")))
    inv = {datetime.fromisoformat(r["t"]).replace(tzinfo=None, second=0): r for r in a}
    pos = [t for t, r in inv.items() if r["barra"] and r["anc"] and not r["manto"]]
    p0 = set(pos) | {t - timedelta(minutes=m) for t in pos for m in range(10, 61, 10)}
    def cerca(t, grupo):
        return any(abs((t - u).days) <= 10 and (t.hour, t.minute) == (u.hour, u.minute) for u in grupo)
    pn = [t for t in pos if inv[t]["sza"] >= 80]; pd_ = [t for t in pos if inv[t]["sza"] < 80]
    def prio(t):
        if t in p0:
            return 0
        if cerca(t, pn):
            return 1
        if cerca(t, pd_):
            return 2
        return 3 if inv[t]["sza"] >= 80 else 4
    return sorted(inv, key=lambda t: (prio(t), t))


def run(dts, nproc):
    t0 = time.time(); n = 0; st_c = {}
    with ProcessPoolExecutor(nproc) as ex:
        futs = [ex.submit(get_scan, dt) for dt in dts]
        for fu in as_completed(futs):
            dt, st, dur = fu.result(); n += 1; st_c[st] = st_c.get(st, 0) + 1
            if st not in ("cache", "cache_sin_key") and (n % 50 == 0 or st != "ok"):
                print(f"{dt:%Y-%m-%d %H:%M} {st} {dur:.1f}s [{n}/{len(dts)} {time.time()-t0:.0f}s] {st_c}", flush=True)
    print("listo", len(dts), f"{time.time()-t0:.0f}s", st_c, flush=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "test":
        run([datetime(2026, 11, 10, 3, 0), datetime(2026, 11, 12, 3, 0)], 2)
    else:
        dts = frames()
        print("cuadros del inventario", len(dts), flush=True)
        run(dts, int(sys.argv[2]) if len(sys.argv) > 2 else 8)
