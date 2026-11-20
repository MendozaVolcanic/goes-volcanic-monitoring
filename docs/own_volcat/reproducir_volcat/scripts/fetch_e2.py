"""Etapa 2: baja lo que falta en disco (L1b por ventana y PNG VOLCAT). Uso:
  python fetch_e2.py png  DIA [DIA ...]        (PNG Ash_Height de Chile_Central_2_km, SSEC)
  python fetch_e2.py l1b  lista.txt            (una clave YYYYmmdd_HHMM por linea; C10, C11, C14, C15)

Misma ventana 83 x 94 que H3 y beta73 (reconstruida en ventana.py), mismo formato de npz (radiancia, BT y
coeficientes Planck de CADA NetCDF), cache propio en <TRABAJO>/cache_e2. Reanudable: salta lo que ya existe.
"""
import os, sys, re, time, json
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
TRABAJO = os.environ.get("H11_TRABAJO", r"C:\Users\nmend\AppData\Local\Temp\claude\a2570b18d9d77a03\d3ce10df-b230-48d8-900a-293980f29716\scratchpad\rv")
CACHE = os.path.join(TRABAJO, "cache_e2"); os.makedirs(CACHE, exist_ok=True)
PNGD = os.path.join(TRABAJO, "png_e2"); os.makedirs(PNGD, exist_ok=True)
WIN = json.load(open(os.path.join(TRABAJO, "window.json")))
BANDS = (10, 11, 14, 15)
URL = "https://volcano.ssec.wisc.edu/data/sector_imagery/Chile_Central_2_km/ABI/GOES-19/Ash_Height"


# ------------------------------------------------------------------ PNG
def png_dia(dia):
    import requests
    S = requests.Session(); S.headers["User-Agent"] = "research-script"
    r = S.get(f"{URL}/{dia}/", timeout=60)
    nombres = sorted(set(re.findall(r'href="(GOES-19\.ABI\.[^"]+\.png)"', r.text)))
    n_ok = 0
    for n in nombres:
        dst = os.path.join(PNGD, n)
        if os.path.exists(dst):
            continue
        for i in range(4):
            try:
                q = S.get(f"{URL}/{dia}/{n}", timeout=60)
                if q.status_code == 200 and q.content[:8] == b"\x89PNG\r\n\x1a\n":
                    open(dst + ".tmp", "wb").write(q.content); os.replace(dst + ".tmp", dst); n_ok += 1
                    break
            except Exception:
                pass
            time.sleep(3 * (i + 1))
        else:
            print("FALLA", n, flush=True)
    print(dia, "listados", len(nombres), "nuevos", n_ok, flush=True)


# ------------------------------------------------------------------ L1b
_fs = None
_list = {}


def fs():
    global _fs
    if _fs is None:
        import s3fs
        _fs = s3fs.S3FileSystem(anon=True)
    return _fs


def key_for(dt, band):
    p = f"noaa-goes19/ABI-L1b-RadF/{dt:%Y}/{dt.timetuple().tm_yday:03d}/{dt:%H}/"
    if p not in _list:
        for i in range(4):
            try:
                _list[p] = fs().ls(p); break
            except Exception:
                time.sleep(3 * (i + 1))
        else:
            _list[p] = []
    tag = f"_s{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}"
    for k in _list[p]:
        n = k.split("/")[-1]
        if f"C{band:02d}_" in n and tag in n:
            return k
    return None


def read(key):
    import h5py
    for i in range(4):
        try:
            with fs().open(key, "rb", block_size=2**16, cache_type="blockcache") as fo, h5py.File(fo, "r") as f:
                r = f["Rad"]
                raw = r[WIN["y0"]:WIN["y1"], WIN["x0"]:WIN["x1"]].astype("float64")
                fill = r.attrs["_FillValue"][0]
                rad = raw * r.attrs["scale_factor"][0] + r.attrs["add_offset"][0]; rad[raw == fill] = np.nan
                co = tuple(float(f[n][()]) for n in ("planck_fk1", "planck_fk2", "planck_bc1", "planck_bc2"))
                fk1, fk2, bc1, bc2 = co
                with np.errstate(invalid="ignore", divide="ignore"):
                    bt = ((fk2 / np.log(fk1 / np.where(rad > 0, rad, np.nan) + 1)) - bc1) / bc2
                return rad.astype("float32"), bt.astype("float32"), np.array(co)
        except Exception as e:
            err = e; time.sleep(3 * (i + 1))
    print("FALLA", key, err, flush=True)
    return None


def get_scan(kk):
    out = os.path.join(CACHE, kk + ".npz")
    if os.path.exists(out):
        return kk, "cache"
    dt = datetime.strptime(kk, "%Y%m%d_%H%M"); d = {}
    for b in BANDS:
        k = key_for(dt, b)
        if k is None:
            return kk, f"sin_key_C{b}"
        r = read(k)
        if r is None:
            return kk, f"falla_C{b}"
        d[f"rad{b}"], d[f"bt{b}"], d[f"co{b}"] = r; d[f"key{b}"] = np.array(k.split("/")[-1])
    tmp = out + ".tmp.npz"; np.savez_compressed(tmp, **d); os.replace(tmp, out)
    return kk, "ok"


if __name__ == "__main__":
    if sys.argv[1] == "png":
        with ThreadPoolExecutor(4) as ex:
            list(ex.map(png_dia, sys.argv[2:]))
    else:
        ks = [l.strip() for l in open(sys.argv[2]) if l.strip()]
        print("scans", len(ks), flush=True); t0 = time.time()
        with ProcessPoolExecutor(8) as ex:
            for kk, st in ex.map(get_scan, ks):
                print(kk, st, f"{time.time() - t0:.0f}s", flush=True)
