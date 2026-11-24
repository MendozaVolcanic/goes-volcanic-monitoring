r"""S22c: viento GFS 0,25 grados (UGRD, VGRD, HGT de 1000 a 200 hPa) en una caja de 10 x 10 nodos alrededor de Nevados
de Chillán, por hora, desde el archivo público noaa-gfs-bdp-pds leído por rango de bytes (criterio §2).

Por qué así: la altura por rumbo necesita el perfil de viento de cada hora. Es el descargador de H10
(direccion_pluma/scripts/fetch_gfs_viento_h10.py) con dos cambios: llega a 200 hPa (VOLCAT pinta hasta 11 km) y la
salida va a D:\goes_notas\s22\s22c\gfs. Hora válida = la hora pedida; ciclo = último 00/06/12/18 UTC <= esa hora;
plazo f000 a f005. El GRIB no se guarda: sólo la caja chica en npz.

Uso: python -I s22c_viento.py 2026-11-08 2026-11-14 [...]   (baja 10 a 24 UTC de cada día y el 00 UTC siguiente)
     python -I s22c_viento.py 2026102514 2026102515           (horas sueltas)
"""
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, REPO)
from src.fetch.gfs_archive import _parse_idx, _read_range  # noqa: E402

OUT = r"D:\goes_notas\s22\s22c\gfs"
LEVELS = [1000, 975, 950, 925, 900, 850, 800, 750, 700, 650, 600, 550, 500, 450, 400, 350, 300, 250, 200]
LATS = np.arange(-35.75, -38.0 - 1e-6, -0.25)
LONS = np.arange(287.5, 289.75 + 1e-6, 0.25)
MIN_LIBRE_GB = 6.0


def ruta(h):
    return os.path.join(OUT, f"gfsv_{h:%Y%m%d%H}.npz")


def bajar(h):
    out = ruta(h)
    if os.path.exists(out):
        return "cache"
    libre = shutil.disk_usage("D:\\").free / 1e9
    if libre < MIN_LIBRE_GB:
        raise RuntimeError(f"D: con {libre:.1f} GB libres, bajo {MIN_LIBRE_GB}")
    import s3fs
    import eccodes
    cyc = h.replace(hour=(h.hour // 6) * 6)
    fh = int((h - cyc).total_seconds() // 3600)
    s3 = s3fs.S3FileSystem(anon=True)
    g = f"noaa-gfs-bdp-pds/gfs.{cyc:%Y%m%d}/{cyc:%H}/atmos/gfs.t{cyc:%H}z.pgrb2.0p25.f{fh:03d}"
    recs = _parse_idx(s3.cat(g + ".idx").decode())
    size = int(s3.info(g)["size"])
    idx = {(r["var"], r["level"]): r for r in recs}
    need = [(v, f"{p} mb") for v in ("UGRD", "VGRD", "HGT") for p in LEVELS]
    falt = [k for k in need if k not in idx]
    if falt:
        raise RuntimeError(f"faltan registros {falt[:5]}")

    def rng(k):
        r = idx[k]
        e = r["end"] if r["end"] is not None else size - 1
        return _read_range(s3, g, r["start"], e)
    with ThreadPoolExecutor(8) as ex:
        raws = list(ex.map(rng, need))
    vals = {}
    for k, raw in zip(need, raws):          # decodificación en serie, desde memoria (eccodes no es seguro en hilos)
        gid = eccodes.codes_new_from_message(raw)
        try:
            ni = eccodes.codes_get(gid, "Ni")
            nj = eccodes.codes_get(gid, "Nj")
            lat0 = eccodes.codes_get(gid, "latitudeOfFirstGridPointInDegrees")
            lon0 = eccodes.codes_get(gid, "longitudeOfFirstGridPointInDegrees")
            d = eccodes.codes_get(gid, "iDirectionIncrementInDegrees")
            v = eccodes.codes_get_values(gid).reshape(nj, ni)
        finally:
            eccodes.codes_release(gid)
        jj = np.rint((lat0 - LATS) / d).astype(int)
        ii = np.rint(((LONS - lon0) % 360) / d).astype(int)
        vals[k] = v[np.ix_(jj, ii)].astype("float32")
    o = {"lat": LATS, "lon": LONS - 360.0, "p": np.array(LEVELS, float),
         "u": np.stack([vals[("UGRD", f"{p} mb")] for p in LEVELS]),
         "v": np.stack([vals[("VGRD", f"{p} mb")] for p in LEVELS]),
         "z": np.stack([vals[("HGT", f"{p} mb")] for p in LEVELS]),
         "archivo": np.array(g), "valida": np.array(f"{h:%Y-%m-%d %H:%M}")}
    os.makedirs(OUT, exist_ok=True)
    tmp = out + ".tmp.npz"
    np.savez_compressed(tmp, **o)
    os.replace(tmp, out)
    return "ok"


def horas(args):
    hs = set()
    for a in args:
        if len(a) == 10 and "-" in a:
            d = datetime.strptime(a, "%Y-%m-%d")
            hs |= {d + timedelta(hours=k) for k in range(10, 25)}
        else:
            hs.add(datetime.strptime(a, "%Y%m%d%H"))
    return sorted(hs)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for h in horas(sys.argv[1:]):
        try:
            print(h, bajar(h), flush=True)
        except Exception as e:  # noqa: BLE001
            print(h, "FALLA", repr(e), flush=True)
