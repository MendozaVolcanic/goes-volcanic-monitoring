"""H10: baja por ventana (83x94, la del detector) las escenas L1b C11/C14/C15 que faltan para la prueba de
senal (criterio seccion 6): scans de las jornadas 25-10, 27-10 y 28-10 dentro de las ventanas REAV con
direccion, y sus candidatos de control (mismo minuto, +-10 dias, regla _limpio). Reanudable: salta lo que
ya esta en cualquiera de los tres caches. Uso: python -I bajar_l1b_h10.py [listar]"""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h10 as C  # noqa: E402
import h5py, s3fs  # noqa: E402

WIN = json.load(open(os.path.join(C.DET, "window.json")))
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
    for kk in listing(dt):
        n = kk.split("/")[-1]
        if f"C{band:02d}_" in n and tag in n:
            return kk
    return None


def read(key):
    err = None
    for i in range(4):
        try:
            with fs.open(key, "rb", block_size=2 ** 18, cache_type="readahead") as fo:
                with h5py.File(fo, "r") as f:
                    r = f["Rad"]; raw = r[WIN["y0"]:WIN["y1"], WIN["x0"]:WIN["x1"]].astype("float64")
                    fill = r.attrs["_FillValue"][0]
                    rad = raw * r.attrs["scale_factor"][0] + r.attrs["add_offset"][0]
                    rad[raw == fill] = np.nan
                    fk1, fk2, bc1, bc2 = (float(f[n][()]) for n in ("planck_fk1", "planck_fk2", "planck_bc1", "planck_bc2"))
                    with np.errstate(invalid="ignore", divide="ignore"):
                        rad = np.where(rad > 0, rad, np.nan)
                        return (((fk2 / np.log(fk1 / rad + 1)) - bc1) / bc2).astype("float32")
        except Exception as e:
            err = e; time.sleep(2 * (i + 1))
    print("FALLA", key, err, flush=True)
    return None


def get_scan(dt):
    if C.escena(dt) is not None:
        return "cache"
    out = os.path.join(C.CACHE_OWN, C.k(dt) + ".npz")
    kks = [key_for(dt, b) for b in (11, 14, 15)]
    if any(kk is None for kk in kks):
        return "sin_key"
    with ThreadPoolExecutor(3) as ex3:
        bt3 = list(ex3.map(read, kks))
    if any(bt is None for bt in bt3):
        return "falla"
    bts = {f"b{b}": bt for b, bt in zip((11, 14, 15), bt3)}
    tmp = out + ".tmp.npz"
    np.savez_compressed(tmp, **bts); os.replace(tmp, out)
    return "ok"


def necesarios():
    pos, ctl = set(), set()
    for e in C.EP:
        if e[5] is None or e[1] not in ("25-10", "27-10", "28-10"):
            continue
        for t in C.slots(e):
            pos.add(t)
            ctl.update(C.candidatos(t))
    return sorted(pos), sorted(ctl - pos)


if __name__ == "__main__":
    pos, ctl = necesarios()
    falt = [t for t in pos if C.escena(t) is None] + [t for t in ctl if C.escena(t) is None]   # positivos primero
    if len(sys.argv) > 1 and sys.argv[1] == "controles":
        # Desviacion declarada en INFORME.md (ancho de banda): solo controles que faltan para slots positivos
        # ya en disco de las jornadas pedidas (p. ej. "controles 28-10").
        js = set(sys.argv[2:])
        falt = sorted({c for e in C.EP if e[5] is not None and e[1] in js for t in C.slots(e) if C.escena(t) is not None
                       for c in C.candidatos(t) if C.escena(c) is None})
    print(f"positivos {len(pos)}  controles candidatos {len(ctl)}  faltan {len(falt)}", flush=True)
    print("a bajar", len(falt), flush=True)
    if len(sys.argv) > 1 and sys.argv[1] == "listar":
        sys.exit(0)
    t0 = time.time(); cuenta = {}
    with ThreadPoolExecutor(int(os.environ.get("H10_HILOS", "16"))) as ex:
        for i, (dt, st) in enumerate(zip(falt, ex.map(get_scan, falt))):
            cuenta[st] = cuenta.get(st, 0) + 1
            if st not in ("ok", "cache") or i % 50 == 0:
                print(i, dt, st, f"{time.time() - t0:.0f}s", flush=True)
    print("listo", cuenta, f"{time.time() - t0:.0f}s", flush=True)
