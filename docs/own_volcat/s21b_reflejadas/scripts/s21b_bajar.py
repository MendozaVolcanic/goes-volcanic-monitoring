r"""S21b: baja de NOAA S3 (noaa-goes19, ABI-L1b-RadF, sin credenciales) C02, C05 y C06, solo la ventana de Longavi a
Antuco (filas 4500 a 4572, columnas 2850 a 2890 de 2 km; x4 en C02 y x2 en C05), para los cuadros de §3 del criterio.

Por que asi: los NetCDF de L1b van en trozos de filas completas, asi que h5py sobre s3fs solo baja los trozos que
tocan la ventana (unos MB por archivo, no 390 MB) y se guarda solo la ventana. Mismo metodo que h23_bajar.py.

Guarda por cuadro `D:\goes_notas\s21\b\l1b\<AAAAMMDD_HHMM>.npz` con, por banda: radiancia (NaN en relleno), kappa0,
angulos de barrido x e y de la ventana (rad) y time_bounds (s desde 2000-01-01 12:00). Reanudable.
Corta si D: baja de 8 GB libres.
Uso: python -I s21b_bajar.py [nproc]
"""
import json
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta

import numpy as np

OUT = r"D:\goes_notas\s21\b\l1b"
WIN2 = dict(y0=4500, y1=4572, x0=2850, x1=2890)
BANDAS = {2: 4, 5: 2, 6: 1}           # banda: factor de resolucion respecto de 2 km
MIN_LIBRE_GB = 8.0
_fs = None
_ls = {}


def fs():
    global _fs
    if _fs is None:
        import s3fs
        _fs = s3fs.S3FileSystem(anon=True)
    return _fs


def listar(dt):
    p = f"noaa-goes19/ABI-L1b-RadF/{dt:%Y}/{dt.timetuple().tm_yday:03d}/{dt:%H}/"
    if p not in _ls:
        for i in range(4):
            try:
                _ls[p] = fs().ls(p)
                break
            except FileNotFoundError:
                _ls[p] = []
                break
            except Exception:  # noqa: BLE001
                time.sleep(2 * (i + 1))
        else:
            _ls[p] = []
    return _ls[p]


def clave(dt, b):
    tag = f"_s{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}"
    for k in listar(dt):
        n = k.split("/")[-1]
        if f"M6C{b:02d}_" in n and tag in n:
            return k
    return None


def leer(key, fct):
    import h5py
    y0, y1, x0, x1 = (WIN2[k] * fct for k in ("y0", "y1", "x0", "x1"))
    err = None
    for i in range(4):
        try:
            with fs().open(key, "rb", block_size=2**18, cache_type="readahead") as fo, h5py.File(fo, "r") as f:
                r = f["Rad"]
                raw = r[y0:y1, x0:x1].astype("float64")
                rad = raw * r.attrs["scale_factor"][0] + r.attrs["add_offset"][0]
                rad[raw == r.attrs["_FillValue"][0]] = np.nan
                ya, xa = f["y"].attrs, f["x"].attrs
                y = np.arange(y0, y1) * ya["scale_factor"][0] + ya["add_offset"][0]
                x = np.arange(x0, x1) * xa["scale_factor"][0] + xa["add_offset"][0]
                return dict(rad=rad.astype("float32"), kappa0=float(np.ravel(f["kappa0"][()])[0]),
                            x=x, y=y, tb=np.asarray(f["time_bounds"][()], "float64"))
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(2 * (i + 1))
    print("FALLA", key, repr(err), flush=True)
    return None


def cuadro(dt):
    out = os.path.join(OUT, f"{dt:%Y%m%d_%H%M}.npz")
    if os.path.exists(out):
        return dt, "cache", 0.0, 0
    t0 = time.time()
    d = {}
    for b, fct in BANDAS.items():
        k = clave(dt, b)
        if k is None:
            return dt, f"sin_clave_C{b:02d}", time.time() - t0, 0
        r = leer(k, fct)
        if r is None:
            return dt, f"falla_C{b:02d}", time.time() - t0, 0
        for n, v in r.items():
            d[f"C{b:02d}_{n}"] = v
        d[f"C{b:02d}_clave"] = np.array(k.split("/")[-1])
    np.savez_compressed(out + ".tmp.npz", **d)
    os.replace(out + ".tmp.npz", out)
    return dt, "ok", time.time() - t0, os.path.getsize(out)


def rango(dia, h0, h1):
    t = datetime.strptime(f"{dia} {h0}", "%Y-%m-%d %H:%M")
    fin = datetime.strptime(f"{dia} {h1}", "%Y-%m-%d %H:%M")
    while t <= fin:
        yield t
        t += timedelta(minutes=10)


def plan():
    dts = set()
    for dia in ("2026-10-25", "2026-09-27", "2026-10-15", "2026-10-16", "2026-10-17", "2026-11-02", "2026-11-04"):
        dts.update(rango(dia, "14:00", "15:00"))
    for dia in ("2026-10-28", "2026-09-21", "2026-10-17", "2026-11-04", "2026-10-25", "2026-10-29"):
        dts.update(rango(dia, "16:00", "23:00"))
    dts.update(rango("2026-10-25", "12:50", "13:40"))
    dts.update(rango("2026-10-27", "10:50", "11:30"))
    return sorted(dts)


def main():
    nproc = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    os.makedirs(OUT, exist_ok=True)
    dts = plan()
    print("cuadros", len(dts), flush=True)
    t0, n, tot = time.time(), 0, 0
    with ProcessPoolExecutor(nproc) as ex:
        futs = [ex.submit(cuadro, dt) for dt in dts]
        for fu in as_completed(futs):
            dt, st, dur, sz = fu.result()
            n += 1
            tot += sz
            if st != "cache":
                print(f"{dt:%Y-%m-%d %H:%M} {st} {dur:.1f}s {sz / 1e6:.2f}MB [{n}/{len(dts)} {time.time() - t0:.0f}s "
                      f"{tot / 1e6:.0f}MB]", flush=True)
            if shutil.disk_usage("D:\\").free / 1e9 < MIN_LIBRE_GB:
                print("CORTE: D: bajo 8 GB libres", flush=True)
                for f in futs:
                    f.cancel()
                break
    print("listo", n, f"{time.time() - t0:.0f}s", f"{tot / 1e6:.0f}MB", json.dumps(WIN2), flush=True)


if __name__ == "__main__":
    main()
