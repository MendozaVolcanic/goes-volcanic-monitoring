"""beta73 (copia de fetch_gfs_nomads.py de H3; cambia carpeta y modulo base): mismo perfil GFS 0,25 grados que fetch_gfs.py, pero pedido al filtro GRIB de NOMADS (NCEP, publico, sin
cuenta) con subregion, para los dias que NOMADS aun guarda (ultimos ~10 dias). Mismo archivo, misma hora valida,
mismo ciclo y plazo; solo cambia el recorte espacial (unos 50 KB en vez de ~90 MB por hora), necesario porque la
red quedo en ~50 KB/s. Se verifica contra un archivo bajado de S3 (modo 'verificar').
Uso: python -I fetch_gfs_nomads.py YYYYmmddHHMM ...   |  python -I fetch_gfs_nomads.py verificar YYYYmmddHHMM
"""
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import os, sys, time, urllib.request
import numpy as np
from datetime import datetime
from fetch_gfs_b73 import archivo, LEVELS, LATS, LONS

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DL = os.path.join(HERE, "dl", "nomads"); os.makedirs(DL, exist_ok=True)
OUT = os.path.join(HERE, "gfs")


def url(cyc, fh):
    lev = "".join(f"&lev_{p}_mb=on" for p in LEVELS)
    return ("https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25_1hr.pl?"
            f"dir=%2Fgfs.{cyc:%Y%m%d}%2F{cyc:%H}%2Fatmos&file=gfs.t{cyc:%H}z.pgrb2.0p25.f{fh:03d}"
            "&var_TMP=on&var_SPFH=on&var_O3MR=on&var_PRES=on&var_HGT=on" + lev +
            "&lev_surface=on&lev_tropopause=on&subregion=&toplat=-35.5&leftlon=287.25&rightlon=290&bottomlat=-38.25")


def bajar(h, out_dir=OUT, sufijo=""):
    h, cyc, fh = archivo(h)
    out = os.path.join(out_dir, f"gfs_{h:%Y%m%d%H}{sufijo}.npz")
    if os.path.exists(out):
        return out, "cache"
    gp = os.path.join(DL, f"gfs_{h:%Y%m%d%H}.grib2")
    for i in range(5):
        try:
            urllib.request.urlretrieve(url(cyc, fh), gp); break
        except Exception as e:
            err = e; time.sleep(5 * (i + 1))
    else:
        raise RuntimeError(err)
    import eccodes
    vals = {}
    with open(gp, "rb") as f:
        while True:
            g = eccodes.codes_grib_new_from_file(f)
            if g is None:
                break
            sn = eccodes.codes_get(g, "shortName"); tl = eccodes.codes_get(g, "typeOfLevel"); lv = eccodes.codes_get(g, "level")
            la = eccodes.codes_get_array(g, "latitudes"); lo = eccodes.codes_get_array(g, "longitudes")
            v = eccodes.codes_get_values(g); eccodes.codes_release(g)
            grid = {(round(a, 2), round(b, 2)): c for a, b, c in zip(la, lo, v)}
            vals[(sn, tl, lv)] = np.array([[grid[(round(a, 2), round(b, 2))] for b in LONS] for a in LATS])
    pl = lambda sn: np.stack([vals[(sn, "isobaricInhPa", p)] for p in LEVELS])   # noqa: E731
    o = {"lat": LATS, "lon": LONS - 360.0, "p": np.array(LEVELS, float), "T": pl("t"), "q": pl("q"), "o3": pl("o3mr"),
         "tskin": vals[("t", "surface", 0)], "psfc": vals[("sp", "surface", 0)] / 100.0, "zsfc": vals[("orog", "surface", 0)],
         "ttropo": vals[("t", "tropopause", 0)], "ptropo": vals[("trpp", "tropopause", 0)] / 100.0,
         "archivo": np.array(f"NOMADS filter_gfs_0p25_1hr gfs.{cyc:%Y%m%d}/{cyc:%H} f{fh:03d}"), "valida": np.array(f"{h:%Y-%m-%d %H:%M}")}
    tmp = out + ".tmp.npz"; np.savez_compressed(tmp, **o); os.replace(tmp, out)
    return out, "ok"


if __name__ == "__main__":
    if sys.argv[1] == "verificar":
        dt = datetime.strptime(sys.argv[2], "%Y%m%d%H%M")
        os.makedirs(os.path.join(HERE, "dl", "verif"), exist_ok=True)
        p, _ = bajar(dt, os.path.join(HERE, "dl", "verif"), "_nomads")
        a = np.load(p); b = np.load(os.path.join(OUT, f"gfs_{archivo(dt)[0]:%Y%m%d%H}.npz"))
        for k in ("T", "q", "o3", "tskin", "psfc", "zsfc", "ttropo", "ptropo"):
            print(k, "max |NOMADS - S3| =", float(np.max(np.abs(a[k] - b[k]))))
    else:
        for a in sys.argv[1:]:
            dt = datetime.strptime(a, "%Y%m%d%H%M")
            try:
                print(dt, *bajar(dt), flush=True)
            except Exception as e:
                print(dt, "FALLA", repr(e), flush=True)
