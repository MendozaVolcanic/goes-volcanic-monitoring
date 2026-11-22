r"""H23: temperatura del aire a la altura de la capa inyectada. Analisis GFS archivado (noaa-gfs-bdp-pds, GRIB2 de
0,25 grados, f000 de los ciclos 00/06/12/18 UTC), leido por rango de bytes con el indice .idx, en la misma caja de
10 x 10 nodos alrededor de Chillan que usa H3 (h3_h7/scripts_h3/fetch_gfs.py). Solo temperatura y altura
geopotencial en niveles de 850 a 200 hPa, la temperatura de la tropopausa y la altura del terreno del modelo.

Por que solo el analisis cada 6 h: en la troposfera libre (3 a 10 km) la temperatura cambia menos de ~1 K en 6 h
fuera de un frente; se interpola linealmente en el tiempo. No se usa la temperatura de piel del GFS.
Uso: python -I h23_gfs.py   -> H23_DIR\gfs\gfs_YYYYmmddHH.npz
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h23_comun as K  # noqa: E402

LEVELS = [850, 750, 700, 650, 600, 550, 500, 400, 300, 250, 200]
LATS = np.arange(-35.75, -38.0 - 1e-6, -0.25)       # 10 nodos
LONS = np.arange(287.5, 289.75 + 1e-6, 0.25)        # 10 nodos (-72,5 a -70,25)
SUELTOS = [("TMP", "tropopause"), ("HGT", "surface")]
# Dias con inyeccion o con evento: 01-10 a 23-10 y 11-11 a 21-11 (mas el 00 UTC del dia siguiente)
TRAMOS = [(datetime(2026, 10, 1), datetime(2026, 10, 24)), (datetime(2026, 11, 11), datetime(2026, 11, 22))]


def parse_idx(txt):
    recs = []
    for ln in txt.strip().splitlines():
        p = ln.split(":")
        recs.append({"start": int(p[1]), "var": p[3], "level": p[4]})
    for a, b in zip(recs, recs[1:]):
        a["end"] = b["start"] - 1
    recs[-1]["end"] = None
    return recs


def bajar(cyc):
    """Baja los registros GRIB de un ciclo (red, en hilos). La decodificacion va aparte y en serie: eccodes no es
    seguro entre hilos (con hilos fallo el analizador de definiciones: "flex scanner internal error")."""
    import s3fs
    out = os.path.join(K.GFS, f"gfs_{cyc:%Y%m%d%H}.npz")
    if os.path.exists(out):
        return cyc, "cache", None, None
    s3 = s3fs.S3FileSystem(anon=True)
    g = f"noaa-gfs-bdp-pds/gfs.{cyc:%Y%m%d}/{cyc:%H}/atmos/gfs.t{cyc:%H}z.pgrb2.0p25.f000"
    err = None
    need = [(v, f"{p} mb") for v in ("TMP", "HGT") for p in LEVELS] + SUELTOS
    for i in range(4):
        try:
            idx = {(r["var"], r["level"]): r for r in parse_idx(s3.cat(g + ".idx").decode())}
            falt = [k for k in need if k not in idx]
            if falt:
                return cyc, f"FALTAN {falt[:4]}", None, None
            raws = {k: s3.cat_file(g, start=idx[k]["start"], end=idx[k]["end"] + 1) for k in need}
            return cyc, "ok", raws, g
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(3 * (i + 1))
    return cyc, "FALLA " + repr(err), None, None


def decodificar(cyc, raws, g):
    import eccodes
    vals = {}
    for k, raw in raws.items():
        gid = eccodes.codes_new_from_message(raw)   # desde memoria: en Windows el archivo temporal queda tomado
        try:
            ni = eccodes.codes_get(gid, "Ni"); nj = eccodes.codes_get(gid, "Nj")
            lat0 = eccodes.codes_get(gid, "latitudeOfFirstGridPointInDegrees")
            lon0 = eccodes.codes_get(gid, "longitudeOfFirstGridPointInDegrees")
            d = eccodes.codes_get(gid, "iDirectionIncrementInDegrees")
            v = eccodes.codes_get_values(gid).reshape(nj, ni)
        finally:
            eccodes.codes_release(gid)
        jj = np.rint((lat0 - LATS) / d).astype(int); ii = np.rint(((LONS - lon0) % 360) / d).astype(int)
        vals[k] = v[np.ix_(jj, ii)].astype("float32")
    out = os.path.join(K.GFS, f"gfs_{cyc:%Y%m%d%H}.npz")
    np.savez_compressed(out + ".tmp.npz", lat=LATS, lon=LONS - 360.0, p=np.array(LEVELS, float),
                        T=np.stack([vals[("TMP", f"{p} mb")] for p in LEVELS]),
                        Z=np.stack([vals[("HGT", f"{p} mb")] for p in LEVELS]),
                        ttropo=vals[("TMP", "tropopause")], zsfc=vals[("HGT", "surface")], archivo=np.array(g))
    os.replace(out + ".tmp.npz", out)


if __name__ == "__main__":
    os.makedirs(K.GFS, exist_ok=True)
    ciclos = []
    for a, b in TRAMOS:
        t = a
        while t <= b:
            ciclos.append(t)
            t += timedelta(hours=6)
    print("ciclos", len(ciclos), flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(4) as ex:
        for i, (c, r, raws, g) in enumerate(ex.map(bajar, ciclos), 1):
            if raws is not None:
                decodificar(c, raws, g)
            if r not in ("ok", "cache") or i % 20 == 0:
                print(i, c, r, f"{time.time() - t0:.0f}s", flush=True)
    print("FIN", len(os.listdir(K.GFS)), "archivos", f"{time.time() - t0:.0f}s", flush=True)
