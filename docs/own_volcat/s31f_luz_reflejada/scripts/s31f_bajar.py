r"""S31f: baja de NOAA S3 (sin credenciales) C02 (0,5 km), C05 (1 km) y C14 (2 km) de GOES-19 (2025 y 2026) y GOES-16
(2024), sólo una ventana de 29 x 29 píxeles de 2 km centrada en el cráter de Nevados de Chillán (filas 4525 a 4553,
columnas 2852 a 2880 de la grilla de 2 km; x4 en C02 y x2 en C05), para los cuadros del criterio §3.

Por qué así: los NetCDF de L1b van en trozos, así que h5py sobre s3fs sólo baja los trozos que tocan la ventana (no los
~400 MB del disco completo de C02), y se guarda sólo la ventana. Mismo método que s21b_bajar.py y h23_bajar.py.
La grilla fija del ABI anida exacto: el píxel (r, c) de 2 km cubre los (2r..2r+1, 2c..2c+1) de C05 y los
(4r..4r+3, 4c..4c+3) de C02.

Guarda por cuadro `D:\goes_notas\s31\s31f\l1b\<AAAAMMDD_HHMM>.npz` con, por banda: radiancia (NaN en relleno), kappa0
(C02 y C05) o coeficientes de Planck (C14), ángulos de barrido x e y (rad), time_bounds y el nombre del archivo.
Reanudable. Corta si D: baja de 6 GB libres o si la carpeta pasa de 8 GB.
Uso: python -I -B s31f_bajar.py [nproc] [prueba]
"""
import json
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta

import numpy as np

OUT = r"D:\goes_notas\s31\s31f\l1b"
WIN2 = dict(y0=4525, y1=4554, x0=2852, x1=2881)
BANDAS = {2: 4, 5: 2, 14: 1}
MIN_LIBRE_GB, MAX_CARPETA_GB = 6.0, 8.0

# §3 del criterio: cuadros de las horas de los P de día de VOLCAT (32 casillas de 10 min, 15:00 a 21:40 UTC)
SLOTS_P = [90, 91, 100, 101, 102] + list(range(104, 131))
SLOTS_B = sorted({s + k for s in SLOTS_P for k in (-2, -1, 0, 1, 2)})
PERIODOS = [  # (satélite, primer día, último día, casillas)
    (16, "2024-10-21", "2024-11-24", SLOTS_P),
    (19, "2025-10-14", "2025-12-01", SLOTS_B),
    (19, "2026-10-21", "2026-11-24", SLOTS_P),
]
_fs = None
_ls = {}


def fs():
    global _fs
    if _fs is None:
        import s3fs
        _fs = s3fs.S3FileSystem(anon=True)
    return _fs


def listar(sat, dt):
    p = f"noaa-goes{sat}/ABI-L1b-RadF/{dt:%Y}/{dt.timetuple().tm_yday:03d}/{dt:%H}/"
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


def clave(sat, dt, b):
    tag = f"_s{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}"
    for k in listar(sat, dt):
        n = k.split("/")[-1]
        if f"M6C{b:02d}_" in n and tag in n:
            return k
    return None


def leer(key, b, fct):
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
                d = dict(rad=rad.astype("float32"), x=x, y=y, tb=np.asarray(f["time_bounds"][()], "float64"))
                if b == 14:
                    d["co"] = np.array([float(np.ravel(f[k][()])[0]) for k in
                                        ("planck_fk1", "planck_fk2", "planck_bc1", "planck_bc2")])
                else:
                    d["kappa0"] = float(np.ravel(f["kappa0"][()])[0])
                return d
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(2 * (i + 1))
    print("FALLA", key, repr(err), flush=True)
    return None


def cuadro(sat, dt):
    out = os.path.join(OUT, f"{dt:%Y%m%d_%H%M}.npz")
    if os.path.exists(out):
        return dt, "cache", 0.0, 0
    t0 = time.time()
    d = {}
    for b, fct in BANDAS.items():
        k = clave(sat, dt, b)
        if k is None:
            return dt, f"sin_clave_C{b:02d}", time.time() - t0, 0
        r = leer(k, b, fct)
        if r is None:
            return dt, f"falla_C{b:02d}", time.time() - t0, 0
        for n, v in r.items():
            d[f"C{b:02d}_{n}"] = v
        d[f"C{b:02d}_clave"] = np.array(k.split("/")[-1])
    np.savez_compressed(out + ".tmp.npz", **d)
    os.replace(out + ".tmp.npz", out)
    return dt, "ok", time.time() - t0, os.path.getsize(out)


def plan():
    out = []
    for sat, d0, d1, slots in PERIODOS:
        dia = datetime.strptime(d0, "%Y-%m-%d")
        fin = datetime.strptime(d1, "%Y-%m-%d")
        assert fin <= datetime(2026, 11, 24), "ningún día posterior al 24-11-2026"
        while dia <= fin:
            out += [(sat, dia + timedelta(minutes=10 * s)) for s in slots]
            dia += timedelta(days=1)
    return out


def carpeta_gb():
    return sum(e.stat().st_size for e in os.scandir(OUT)) / 1e9


def main():
    nproc = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    os.makedirs(OUT, exist_ok=True)
    tareas = plan()
    if len(sys.argv) > 2:
        tareas = tareas[:: max(1, len(tareas) // int(sys.argv[2]))][: int(sys.argv[2])]
    print("cuadros", len(tareas), flush=True)
    t0, n, tot = time.time(), 0, 0
    with ProcessPoolExecutor(nproc) as ex:
        futs = [ex.submit(cuadro, sat, dt) for sat, dt in tareas]
        for fu in as_completed(futs):
            dt, st, dur, sz = fu.result()
            n += 1
            tot += sz
            if st != "cache":
                print(f"{dt:%Y-%m-%d %H:%M} {st} {dur:.1f}s {sz / 1e3:.0f}kB [{n}/{len(tareas)} "
                      f"{time.time() - t0:.0f}s {tot / 1e6:.0f}MB]", flush=True)
            if n % 200 == 0 and (shutil.disk_usage("D:\\").free / 1e9 < MIN_LIBRE_GB or carpeta_gb() > MAX_CARPETA_GB):
                print("CORTE: D: bajo 6 GB libres o carpeta sobre 8 GB", flush=True)
                for f in futs:
                    f.cancel()
                break
    print("listo", n, f"{time.time() - t0:.0f}s", f"{tot / 1e6:.0f}MB", json.dumps(WIN2), flush=True)


if __name__ == "__main__":
    main()
