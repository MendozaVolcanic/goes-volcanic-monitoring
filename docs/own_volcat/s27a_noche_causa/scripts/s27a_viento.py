r"""S27a: viento y temperatura GFS 1,0 grado (enmienda 1: el de 0,25 grados no bajaba con la red saturada) alrededor de Nevados de Chillán para todas las noches de la ventana
(21-09 a 24-11-2026 y 21-09 a 21-11-2025) y para las tardes de 2026, desde el archivo público noaa-gfs-bdp-pds leído
por rango de bytes.

Por qué: la huella de una pluma es que su disparo sigue al viento de su altura (3 a 6 km). Para ponerla a prueba hace
falta el perfil de cada noche, y el de 2025 para el nulo (un año sin pluma). Las tardes de 2026 dan la dirección en que
la pluma diaria dejó caer ceniza (prueba del depósito). Es el descargador de S22c (s22c_viento.py) con tres cambios:
sólo de 750 a 450 hPa (2,4 a 6,6 km, la capa que importa), agrega la temperatura (prueba de la nieve) y baja horas
cada 2 o 3 h. Hora válida = la hora pedida; ciclo = último 00/06/12/18 UTC <= esa hora; plazo f000 a f005. El GRIB
no se guarda: sólo la caja chica en npz.

Uso: python -I s27a_viento.py todo [k n]  (las noches de los dos años y las tardes de 2026; porción k de n)
     python -I s27a_viento.py 2026102503  (horas sueltas, AAAAMMDDHH)
"""
import os
import shutil
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, REPO)
from src.fetch.gfs_archive import _parse_idx, _read_range  # noqa: E402

OUT = r"D:\goes_notas\s27\s27a\gfs"
LEVELS = [750, 700, 650, 600, 550, 500, 450]
TMP_LEVELS = [750, 700, 650]
LATS = np.arange(-35.0, -38.0 - 1e-6, -1.0)       # GFS 1,0 grados (enmienda 1 del criterio: red saturada)
LONS = np.arange(287.0, 290.0 + 1e-6, 1.0)
MIN_LIBRE_GB = 6.0
_DECODE = threading.Lock()          # eccodes no es seguro en hilos: se decodifica de a uno
HORAS_NOCHE = (3, 6, 9)             # cubren 03:00 a 08:50 UTC (00:00 a 05:50 hora de Chile); el 1 grado es cada 3 h
HORAS_TARDE = (12, 15, 18, 21)      # 09:00 a 18:00 hora de Chile: la pluma diaria de día


def ruta(h):
    return os.path.join(OUT, f"gfst1_{h:%Y%m%d%H}.npz")


def bajar(h, s3=None):
    out = ruta(h)
    if os.path.exists(out):
        return "cache"
    libre = shutil.disk_usage("D:\\").free / 1e9
    if libre < MIN_LIBRE_GB:
        raise RuntimeError(f"D: con {libre:.1f} GB libres, bajo {MIN_LIBRE_GB}")
    import eccodes
    if s3 is None:
        import s3fs
        s3 = s3fs.S3FileSystem(anon=True)
    cyc = h.replace(hour=(h.hour // 6) * 6)
    fh = int((h - cyc).total_seconds() // 3600)
    g = f"noaa-gfs-bdp-pds/gfs.{cyc:%Y%m%d}/{cyc:%H}/atmos/gfs.t{cyc:%H}z.pgrb2.1p00.f{fh:03d}"
    recs = _parse_idx(s3.cat(g + ".idx").decode())
    size = int(s3.info(g)["size"])
    idx = {(r["var"], r["level"]): r for r in recs}
    need = [(v, f"{p} mb") for v in ("UGRD", "VGRD", "HGT") for p in LEVELS] + [("TMP", f"{p} mb") for p in TMP_LEVELS]
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
    _DECODE.acquire()
    try:
        _decodificar(need, raws, vals, eccodes)
    finally:
        _DECODE.release()
    o = _salida(vals, g, h)
    os.makedirs(OUT, exist_ok=True)
    tmp = out + ".tmp.npz"
    np.savez_compressed(tmp, **o)
    os.replace(tmp, out)
    return "ok"


def _decodificar(need, raws, vals, eccodes):
    for k, raw in zip(need, raws):
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


def _salida(vals, g, h):
    return {"lat": LATS, "lon": LONS - 360.0, "p": np.array(LEVELS, float), "p_t": np.array(TMP_LEVELS, float),
         "u": np.stack([vals[("UGRD", f"{p} mb")] for p in LEVELS]),
         "v": np.stack([vals[("VGRD", f"{p} mb")] for p in LEVELS]),
         "z": np.stack([vals[("HGT", f"{p} mb")] for p in LEVELS]),
         "t": np.stack([vals[("TMP", f"{p} mb")] for p in TMP_LEVELS]),
         "archivo": np.array(g), "valida": np.array(f"{h:%Y-%m-%d %H:%M}")}


def horas_todo():
    hs = []
    for t0, n in ((datetime(2026, 9, 21), 65), (datetime(2025, 9, 21), 62)):
        for k in range(n):
            d = t0 + timedelta(days=k)
            hs += [d + timedelta(hours=x) for x in HORAS_NOCHE]
    t0 = datetime(2026, 9, 21)
    for k in range(65):
        d = t0 + timedelta(days=k)
        hs += [d + timedelta(hours=x) for x in HORAS_TARDE]
    return hs


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import s3fs
    S3 = s3fs.S3FileSystem(anon=True)
    if sys.argv[1] == "todo":                  # todo [k n]: la porción k de n (procesos en paralelo, uno por porción)
        k, n = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 1)
        hs = horas_todo()[k::n]
    else:
        hs = [datetime.strptime(a, "%Y%m%d%H") for a in sys.argv[1:]]
    for h in hs:                              # en serie dentro del proceso: s3fs compartido entre hilos se trabó
        for intento in range(3):
            try:
                print(h, bajar(h, S3), flush=True)
                break
            except Exception as e:  # noqa: BLE001
                if intento == 2:
                    print(h, "FALLA", repr(e), flush=True)
