"""H10: viento GFS 0,25 grados (UGRD, VGRD, HGT en 1000 a 300 hPa) en una caja de 10x10 nodos alrededor de
Chillan, del archivo noaa-gfs-bdp-pds por byte-range (reusa _parse_idx y _read_range de
src/fetch/gfs_archive.py sin editarlo). Hora valida = hora del cuadro redondeada; ciclo = ultimo 00/06/12/18Z
<= esa hora; plazo f000 a f005 (criterio seccion 5).
Uso: python -I fetch_gfs_viento_h10.py YYYYmmddHH [YYYYmmddHH ...] -> h10/gfs/gfsv_YYYYmmddHH.npz"""
import os, sys, tempfile, uuid
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h10 as C  # noqa: E402
from src.fetch.gfs_archive import _parse_idx, _read_range  # noqa: E402
import s3fs  # noqa: E402

OUT = os.path.join(C.WORK, "gfs"); os.makedirs(OUT, exist_ok=True)
LEVELS = [1000, 975, 950, 925, 900, 850, 800, 750, 700, 650, 600, 550, 500, 450, 400, 350, 300]
LATS = np.arange(-35.75, -38.0 - 1e-6, -0.25)
LONS = np.arange(287.5, 289.75 + 1e-6, 0.25)


def ruta(h):
    return os.path.join(OUT, f"gfsv_{h:%Y%m%d%H}.npz")


def bajar(h):
    out = ruta(h)
    if os.path.exists(out):
        return "cache"
    cyc = h.replace(hour=(h.hour // 6) * 6); fh = int((h - cyc).total_seconds() // 3600)
    s3 = s3fs.S3FileSystem(anon=True)
    g = f"noaa-gfs-bdp-pds/gfs.{cyc:%Y%m%d}/{cyc:%H}/atmos/gfs.t{cyc:%H}z.pgrb2.0p25.f{fh:03d}"
    recs = _parse_idx(s3.cat(g + ".idx").decode()); size = int(s3.info(g)["size"])
    idx = {(r["var"], r["level"]): r for r in recs}
    need = [(v, f"{p} mb") for v in ("UGRD", "VGRD", "HGT") for p in LEVELS]
    falt = [kk for kk in need if kk not in idx]
    if falt:
        raise RuntimeError(f"faltan registros {falt[:5]}")

    def rng(kk):
        r = idx[kk]; e = r["end"] if r["end"] is not None else size - 1
        return _read_range(s3, g, r["start"], e)
    with ThreadPoolExecutor(8) as ex:
        raws = list(ex.map(rng, need))
    import eccodes
    vals = {}
    for kk, raw in zip(need, raws):
        tmp = os.path.join(tempfile.gettempdir(), f"h10gfs_{uuid.uuid4().hex}.grib2")
        open(tmp, "wb").write(raw)
        with open(tmp, "rb") as fo:
            gid = eccodes.codes_grib_new_from_file(fo)
            ni = eccodes.codes_get(gid, "Ni"); nj = eccodes.codes_get(gid, "Nj")
            lat0 = eccodes.codes_get(gid, "latitudeOfFirstGridPointInDegrees")
            lon0 = eccodes.codes_get(gid, "longitudeOfFirstGridPointInDegrees")
            d = eccodes.codes_get(gid, "iDirectionIncrementInDegrees")
            v = eccodes.codes_get_values(gid).reshape(nj, ni)
            eccodes.codes_release(gid)
        try:
            os.remove(tmp)
        except OSError:
            pass
        jj = np.rint((lat0 - LATS) / d).astype(int); ii = np.rint(((LONS - lon0) % 360) / d).astype(int)
        vals[kk] = v[np.ix_(jj, ii)]
    o = {"lat": LATS, "lon": LONS - 360.0, "p": np.array(LEVELS, float),
         "u": np.stack([vals[("UGRD", f"{p} mb")] for p in LEVELS]),
         "v": np.stack([vals[("VGRD", f"{p} mb")] for p in LEVELS]),
         "z": np.stack([vals[("HGT", f"{p} mb")] for p in LEVELS]),
         "archivo": np.array(g), "valida": np.array(f"{h:%Y-%m-%d %H:%M}")}
    tmpo = out + ".tmp.npz"
    np.savez_compressed(tmpo, **o); os.replace(tmpo, out)
    return "ok"


def bilineal(campo, la, lo, LAT_, LON_):
    i = np.interp(la, LAT_[::-1], np.arange(len(LAT_))[::-1]); j = np.interp(lo, LON_, np.arange(len(LON_)))
    i0, j0 = int(np.floor(i)), int(np.floor(j)); di, dj = i - i0, j - j0
    return ((1 - di) * (1 - dj) * campo[..., i0, j0] + di * (1 - dj) * campo[..., i0 + 1, j0]
            + (1 - di) * dj * campo[..., i0, j0 + 1] + di * dj * campo[..., i0 + 1, j0 + 1])


def viento_capa(h, z0_km, z1_km):
    """Media vectorial de (u, v) entre z0 y z1 km s.n.m. en el crater. Devuelve (az_hacia, rapidez m/s, u, v)."""
    d = np.load(ruta(h))
    u = bilineal(d["u"], C.CLAT, C.CLON, d["lat"], d["lon"])
    v = bilineal(d["v"], C.CLAT, C.CLON, d["lat"], d["lon"])
    z = bilineal(d["z"], C.CLAT, C.CLON, d["lat"], d["lon"]) / 1000.0
    o = np.argsort(z)
    zz = np.arange(z0_km, z1_km + 1e-9, 0.1)
    uu = np.interp(zz, z[o], u[o]).mean(); vv = np.interp(zz, z[o], v[o]).mean()
    return C.azimut(uu, vv), float(np.hypot(uu, vv)), float(uu), float(vv)


def hora(dt):
    return (dt + timedelta(minutes=30)).replace(minute=0, second=0, microsecond=0)


if __name__ == "__main__":
    hs = sorted({datetime.strptime(a, "%Y%m%d%H") for a in sys.argv[1:] if a != "inverso"}, reverse="inverso" in sys.argv)
    for h in hs:
        try:
            print(h, bajar(h), flush=True)
        except Exception as e:
            print(h, "FALLA", repr(e), flush=True)
