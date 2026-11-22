r"""H23: baja de NOAA S3 (noaa-goes19, ABI-L1b-RadF, sin credenciales) las bandas C14 (11,2 um) y C15 (12,3 um),
solo la ventana del detector, cada 10 min, para los dos bloques de dias del criterio. Guarda radiancia y los
coeficientes de Planck del NetCDF en H23_DIR\l1b\<cuadro>.npz. Reanudable. Mismo metodo de lectura que
h17_bajar.py (h5py sobre s3fs, solo los bloques de la ventana).

Corta solo si D: baja de 6 GB libres (limite de la tarea).
Uso: python -I h23_bajar.py [nproc] [oct|nov|todo] [rev]
"""
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h23_comun as K  # noqa: E402

BANDAS = (14, 15)
_fs = None


def fs():
    global _fs
    if _fs is None:
        import s3fs
        _fs = s3fs.S3FileSystem(anon=True)
    return _fs


def listar(h):
    p = f"noaa-goes19/ABI-L1b-RadF/{h:%Y}/{h.timetuple().tm_yday:03d}/{h:%H}/"
    for i in range(4):
        try:
            return fs().ls(p)
        except FileNotFoundError:
            return []
        except Exception:  # noqa: BLE001
            time.sleep(2 * (i + 1))
    return []


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


def hora(h):
    """Los 6 cuadros de una hora. Devuelve (hora, n hechos, lista de (cuadro, bandas sin archivo o sin lectura))."""
    if shutil.disk_usage(K.H23).free < 6 * 2**30:
        return h, 0, [("DISCO", [])]
    lst = None
    hechos, faltas = 0, []
    for m in range(0, 60, 10):
        dt = h + timedelta(minutes=m)
        out = os.path.join(K.L1B, K.clave(dt) + ".npz")
        if os.path.exists(out):
            hechos += 1
            continue
        if lst is None:
            lst = listar(h)
        tag = f"_s{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}"
        d, falta = {}, []
        for b in BANDAS:
            kk = [x for x in lst if f"C{b:02d}_" in x and tag in x]
            if not kk:
                falta.append(b)
                continue
            rad, co = leer(kk[0])
            if rad is None:
                falta.append(b)
                continue
            d[f"rad{b}"] = rad
            d[f"co{b}"] = co
            d[f"key{b}"] = np.array(kk[0].split("/")[-1])
        if falta:
            faltas.append((K.clave(dt), falta))     # no se guarda un cuadro incompleto: se reintenta en otra corrida
            continue
        tmp = out + f".{os.getpid()}.tmp.npz"       # nombre propio por proceso: dos corridas pueden cruzarse
        np.savez_compressed(tmp, **d)
        os.replace(tmp, out)
        hechos += 1
    return h, hechos, faltas


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    cual = sys.argv[2] if len(sys.argv) > 2 else "todo"
    os.makedirs(K.L1B, exist_ok=True)
    bl = {"oct": [K.BLOQUE_OCT], "nov": [K.BLOQUE_NOV], "todo": [K.BLOQUE_OCT, K.BLOQUE_NOV]}[cual]
    horas = [d + timedelta(hours=i) for b in bl for d in K.dias(b) for i in range(24)]
    if len(sys.argv) > 3 and sys.argv[3] == "rev":      # del final hacia atras, para sumar una segunda corrida
        horas = horas[::-1]
    print("horas", len(horas), "cuadros", 6 * len(horas), flush=True)
    t0 = time.time()
    tot, sin = 0, []
    with ProcessPoolExecutor(n) as ex:
        fut = [ex.submit(hora, h) for h in horas]
        for i, f in enumerate(as_completed(fut), 1):
            h, hechos, faltas = f.result()
            tot += hechos
            sin += faltas
            if i % 50 == 0:
                print(f"{i}/{len(horas)} horas, {tot} cuadros, {len(sin)} sin dato, {time.time() - t0:.0f}s", flush=True)
    print("FIN", tot, "cuadros;", len(sin), "sin dato;", f"{time.time() - t0:.0f}s", flush=True)
    for c, b in sorted(sin):
        print("sin_dato", c, b)
