"""H7 senal (b): hot spots FDCF GOES-19 cerca de Nevados de Chillan, scan por scan.

Usa las piezas del repo (src/fetch/goes_fdcf.py): nearest_granule_key + _list_files_at_hour para elegir el
granulo, _abrir_granulo para bajarlo y extract_hotspots(ds, bounds) para los hot spots (Mask 10-15,
HOTSPOT_MASK_VALUES, el conjunto por defecto del repo). Ademas, como sensibilidad, cuenta los pixeles
Mask 30-35 (detecciones con filtro temporal) a <= 10 km, que el conjunto por defecto NO incluye.

Guarda una linea JSON por scan en fdcf.jsonl (append; se puede relanzar y salta lo hecho).
Uso: python fetch_fdcf.py YYYY-MM-DD HH:MM YYYY-MM-DD HH:MM
"""
import sys, os, json, time, math
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import numpy as np
REPO = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\h3-cielo-modelado-beta-114fd5"
sys.path.insert(0, REPO)
from src.fetch import goes_fdcf as G  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "fdcf.jsonl")
VLAT, VLON = -36.86, -71.38
BOUNDS = dict(lat_min=VLAT - 0.5, lat_max=VLAT + 0.5, lon_min=VLON - 0.6, lon_max=VLON + 0.6)


def hav(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def uno(dt):
    s3 = G._get_s3()
    errores = []
    key = G.nearest_granule_key(lambda h: G._list_files_at_hour(s3, h, errores), G._parse_scan_time, dt,
                                max_gap_s=G.SCAN_MAX_GAP_S)
    if key is None:
        return dict(slot=dt.strftime("%Y-%m-%d %H:%M"), scan=None, err="sin_granulo", errores=len(errores))
    for i in range(4):
        try:
            # Granulo entero (~1,9 MB) con la pieza del repo; la apertura perezosa por sub-bloque se probo y
            # fue mas lenta (muchas peticiones chicas con la red compartida).
            ds = G._abrir_granulo(s3, key)
            hs = G.extract_hotspots(ds, bounds=BOUNDS)
            # sensibilidad: Mask 30-35 a <= 10 km (sub-bloque igual que el repo)
            x, y = ds["x"].values, ds["y"].values
            slon = float(ds["goes_imager_projection"].attrs.get("longitude_of_projection_origin", -75.2))
            c0, c1, r0, r1 = G.xy_index_range(x, y, slon, BOUNDS)
            m = ds["Mask"][r0:r1 + 1, c0:c1 + 1].values
            rr, cc = np.where(np.isin(m, [30, 31, 32, 33, 34, 35]))
            tf = []
            if len(rr):
                la, lo = G._abi_to_latlon(x[c0:c1 + 1][cc], y[r0:r1 + 1][rr], sat_lon=slon)
                tf = [dict(lat=float(a), lon=float(b), mask=int(m[r, c]), d_km=round(hav(VLAT, VLON, a, b), 1))
                      for a, b, r, c in zip(la, lo, rr, cc)]
            ds.close()
            scan = G._parse_scan_time(key)
            return dict(slot=dt.strftime("%Y-%m-%d %H:%M"), scan=scan.strftime("%Y-%m-%d %H:%M:%S"),
                        key=key.split("/")[-1],
                        hs=[dict(lat=h.lat, lon=h.lon, frp=h.frp_mw, mask=h.mask, d_km=round(hav(VLAT, VLON, h.lat, h.lon), 1))
                            for h in hs],
                        tf=tf)
        except Exception as e:  # noqa: BLE001
            err = repr(e); time.sleep(2 * (i + 1))
    return dict(slot=dt.strftime("%Y-%m-%d %H:%M"), scan=None, err=err)


if __name__ == "__main__":
    d0 = datetime.strptime(sys.argv[1] + " " + sys.argv[2], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    d1 = datetime.strptime(sys.argv[3] + " " + sys.argv[4], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    hechos = set()
    if os.path.exists(OUT):
        for ln in open(OUT):
            r = json.loads(ln)
            if r.get("scan"):
                hechos.add(r["slot"])
    dts = []; t = d0
    while t <= d1:
        if t.strftime("%Y-%m-%d %H:%M") not in hechos:
            dts.append(t)
        t += timedelta(minutes=10)
    print("por bajar", len(dts), flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(10) as ex, open(OUT, "a") as fo:
        for r in ex.map(uno, dts):
            fo.write(json.dumps(r) + "\n"); fo.flush()
            if not r.get("scan"):
                print("FALLA", r, flush=True)
    print("listo", sys.argv[1:], f"{time.time()-t0:.0f}s", flush=True)
