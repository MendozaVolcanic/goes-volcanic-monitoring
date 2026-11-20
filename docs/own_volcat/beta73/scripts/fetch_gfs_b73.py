"""beta73 (copia de fetch_gfs.py de H3; cambia la carpeta de salida y el repo): perfil GFS archivado (noaa-gfs-bdp-pds, GRIB2 0,25 grados por byte-range) en una caja de 10x10 nodos
alrededor de Chillan. Extiende src/fetch/gfs_archive.py (reusa _parse_idx y _read_range, sin editar el repo)
para pedir ademas humedad especifica (SPFH), ozono (O3MR), presion y altura de superficie y la tropopausa.

Archivo elegido por escena: hora valida = hora del scan redondeada a la hora mas cercana; ciclo = ultimo
ciclo 00/06/12/18Z <= esa hora; plazo = diferencia (f000 a f005). Asi la temperatura de piel (que tiene
ciclo diurno fuerte sobre tierra) corresponde a la hora del scan con a lo mas 30 min de desfase.
Uso: python fetch_gfs.py YYYYmmddHHMM [YYYYmmddHHMM ...]   -> gfs/gfs_YYYYmmddHH.npz (hora valida)
"""
import os, sys
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\beta73-episodios-nuevos-f566cb"
sys.path.insert(0, REPO)
from src.fetch.gfs_archive import _parse_idx, _read_range  # noqa: E402
import s3fs  # noqa: E402

OUT = os.path.join(HERE, "gfs"); os.makedirs(OUT, exist_ok=True)
LEVELS = [1000, 975, 950, 925, 900, 850, 800, 750, 700, 650, 600, 550, 500, 450, 400, 350, 300, 250, 200,
          150, 100, 70, 50, 40, 30, 20, 15, 10, 7, 5, 3, 2, 1]
LATS = np.arange(-35.75, -38.0 - 1e-6, -0.25)       # 10 nodos
LONS = np.arange(287.5, 289.75 + 1e-6, 0.25)        # 10 nodos (-72,5 a -70,25)
SFC = [("TMP", "surface"), ("PRES", "surface"), ("HGT", "surface"), ("TMP", "tropopause"), ("PRES", "tropopause")]


def archivo(dt):
    h = (dt + timedelta(minutes=30)).replace(minute=0, second=0, microsecond=0)
    cyc = h.replace(hour=(h.hour // 6) * 6)
    return h, cyc, int((h - cyc).total_seconds() // 3600)


def bajar(dt):
    s3 = s3fs.S3FileSystem(anon=True)
    h, cyc, fh = archivo(dt)
    out = os.path.join(OUT, f"gfs_{h:%Y%m%d%H}.npz")
    if os.path.exists(out):
        return out, "cache"
    g = f"noaa-gfs-bdp-pds/gfs.{cyc:%Y%m%d}/{cyc:%H}/atmos/gfs.t{cyc:%H}z.pgrb2.0p25.f{fh:03d}"
    recs = _parse_idx(s3.cat(g + ".idx").decode()); size = int(s3.info(g)["size"])
    idx = {(r["var"], r["level"]): r for r in recs}
    need = [(v, f"{p} mb") for v in ("TMP", "SPFH", "O3MR") for p in LEVELS] + SFC
    falt = [k for k in need if k not in idx]
    if falt:
        raise RuntimeError(f"faltan registros {falt[:5]}")

    def rng(k):
        r = idx[k]; e = r["end"] if r["end"] is not None else size - 1
        return _read_range(s3, g, r["start"], e)
    with ThreadPoolExecutor(8) as ex:
        raws = list(ex.map(rng, need))
    import eccodes
    vals = {}
    for k, raw in zip(need, raws):
        # El mensaje GRIB se decodifica desde memoria, sin archivo temporal. Antes se escribia a %TEMP% y se
        # leia con codes_grib_new_from_file: cffi le pasa a eccodes un FILE* duplicado que nunca se cierra, asi
        # que en Windows os.remove fallaba (WinError 32) y el except OSError: pass lo callaba. Quedaban ~100 MB
        # de GRIB2 por hora GFS (12,1 GB en C: el 20-11-2026). codes_new_from_message copia los bytes.
        gid = eccodes.codes_new_from_message(raw)
        try:
            ni = eccodes.codes_get(gid, "Ni"); nj = eccodes.codes_get(gid, "Nj")
            lat0 = eccodes.codes_get(gid, "latitudeOfFirstGridPointInDegrees")
            lon0 = eccodes.codes_get(gid, "longitudeOfFirstGridPointInDegrees")
            d = eccodes.codes_get(gid, "iDirectionIncrementInDegrees")
            v = eccodes.codes_get_values(gid).reshape(nj, ni)
        finally:
            eccodes.codes_release(gid)
        jj = np.rint((lat0 - LATS) / d).astype(int); ii = np.rint(((LONS - lon0) % 360) / d).astype(int)
        vals[k] = v[np.ix_(jj, ii)]
    o = {"lat": LATS, "lon": LONS - 360.0, "p": np.array(LEVELS, float),
         "T": np.stack([vals[("TMP", f"{p} mb")] for p in LEVELS]),
         "q": np.stack([vals[("SPFH", f"{p} mb")] for p in LEVELS]),
         "o3": np.stack([vals[("O3MR", f"{p} mb")] for p in LEVELS]),
         "tskin": vals[("TMP", "surface")], "psfc": vals[("PRES", "surface")] / 100.0,
         "zsfc": vals[("HGT", "surface")], "ttropo": vals[("TMP", "tropopause")],
         "ptropo": vals[("PRES", "tropopause")] / 100.0,
         "archivo": np.array(g), "valida": np.array(f"{h:%Y-%m-%d %H:%M}")}
    np.savez_compressed(out, **o)
    return out, "ok"


if __name__ == "__main__":
    dts = sorted({archivo(datetime.strptime(a, "%Y%m%d%H%M"))[0] for a in sys.argv[1:]})
    for h in dts:
        try:
            print(h, *bajar(h), flush=True)
        except Exception as e:
            print(h, "FALLA", repr(e), flush=True)
