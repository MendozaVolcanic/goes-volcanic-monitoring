r"""S31i: baja de NOAA S3 (sin credenciales) C03 (0,86 µm) y C05 (1,6 µm), las dos a 1 km, de GOES-16 (2024) y GOES-19
(2025 y 2026), sólo una franja que cubre las cumbres de Longaví, Chillán y Antuco: filas 4504 a 4572 y columnas 2856 a
2887 de la grilla de 2 km (x2 en la de 1 km). Del 21-09 al 21-11 de cada año (los días de los cubos de BT11 y BTD), de
día, cada 20 min (casillas pares de 72 a 136: 12:00 a 22:40 UTC).

Por qué: la luz reflejada separa lo que el infrarrojo térmico confunde. A 0,86 µm la nieve y la nube brillan y la roca
volcánica es oscura; a 1,6 µm la nieve es oscura (el hielo absorbe) y la nube de agua sigue brillando. Con las dos se
distingue nube baja de nieve y de roca sobre la cumbre, que es lo que decide entre las candidatas (a) y (b) del
criterio. Cada 20 min y no cada 10: un disparo pide dos cuadros seguidos, así que cada episodio tiene al menos un
cuadro par; baja la mitad.

Método de s31f_bajar.py (h5py sobre s3fs sólo baja los trozos que tocan la ventana), con bloque de lectura de 64 KB
(S25b). Guarda por cuadro D:\goes_notas\s31\s31i\l1b\<AAAAMMDD_HHMM>.npz con, por banda: radiancia (NaN en relleno),
kappa0, x e y (rad), time_bounds y el nombre del archivo. Reanudable. Corta si D: baja de 6 GB libres o la carpeta
pasa de 3 GB. Ningún día posterior al 24-11-2026.
Uso: python -I -B s31i_bajar.py [nproc] [prueba]
"""
import json
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta

import numpy as np

OUT = r"D:\goes_notas\s31\s31i\l1b"
WIN2 = dict(y0=4504, y1=4573, x0=2856, x1=2888)
BANDAS = {3: 2, 5: 2}
SLOTS = list(range(72, 137, 2))
PERIODOS = [(16, "2024-09-21", "2024-11-21"), (19, "2025-09-21", "2025-11-21"), (19, "2026-09-21", "2026-11-21")]
MIN_LIBRE_GB, MAX_CARPETA_GB = 6.0, 3.0
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
        if f"C{b:02d}_" in n and tag in n:
            return k
    return None


def leer(key, fct):
    import h5py
    y0, y1, x0, x1 = (WIN2[k] * fct for k in ("y0", "y1", "x0", "x1"))
    err = None
    for i in range(4):
        try:
            with fs().open(key, "rb", block_size=2**16, cache_type="readahead") as fo, h5py.File(fo, "r") as f:
                r = f["Rad"]
                raw = r[y0:y1, x0:x1].astype("float64")
                rad = raw * r.attrs["scale_factor"][0] + r.attrs["add_offset"][0]
                rad[raw == r.attrs["_FillValue"][0]] = np.nan
                ya, xa = f["y"].attrs, f["x"].attrs
                y = np.arange(y0, y1) * ya["scale_factor"][0] + ya["add_offset"][0]
                x = np.arange(x0, x1) * xa["scale_factor"][0] + xa["add_offset"][0]
                return dict(rad=rad.astype("float32"), x=x, y=y, tb=np.asarray(f["time_bounds"][()], "float64"),
                            kappa0=float(np.ravel(f["kappa0"][()])[0]))
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
        r = leer(k, fct)
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
    for sat, d0, d1 in PERIODOS:
        dia = datetime.strptime(d0, "%Y-%m-%d")
        fin = datetime.strptime(d1, "%Y-%m-%d")
        assert fin <= datetime(2026, 11, 24), "ningún día posterior al 24-11-2026"
        while dia <= fin:
            out += [(sat, dia + timedelta(minutes=10 * s)) for s in SLOTS]
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
            if st != "cache" and (st != "ok" or n % 50 == 0):
                print(f"{dt:%Y-%m-%d %H:%M} {st} {dur:.1f}s {sz / 1e3:.0f}kB [{n}/{len(tareas)} "
                      f"{time.time() - t0:.0f}s {tot / 1e6:.0f}MB]", flush=True)
            if n % 200 == 0 and (shutil.disk_usage("D:\\").free / 1e9 < MIN_LIBRE_GB or carpeta_gb() > MAX_CARPETA_GB):
                print("CORTE: D: bajo 6 GB libres o carpeta sobre 3 GB", flush=True)
                for f in futs:
                    f.cancel()
                break
    print("listo", n, f"{time.time() - t0:.0f}s", f"{tot / 1e6:.0f}MB", json.dumps(WIN2), flush=True)


if __name__ == "__main__":
    main()
