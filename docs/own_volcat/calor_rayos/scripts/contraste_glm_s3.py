"""H9d: contraste obligatorio de la serie GLM de Lightning-v1 contra GLM-L2-LCFA crudo de noaa-goes19.

Para cada hora pedida baja todos los archivos LCFA (20 s cada uno), lee flash_lat, flash_lon y la hora de cada
destello con el desfase ESCALADO (int16 * scale_factor + add_offset) y cuenta destellos a <= 30 km y <= 100 km del
crater real, y en la zona que cubren las dos fuentes (<= 100 km del crater real y <= 100 km del centro que usa
Lightning-v1). Compara con resultados/glm_destellos_chillan.csv emparejando por posicion (lat, lon a 4 decimales).
Reanudable: un JSON por archivo LCFA en scratchpad/glm_s3/.
Uso: python contraste_glm_s3.py 2026-10-26T22 2026-11-14T17
"""
import os, sys, json, io, time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "resultados")
SCR = r"D:\goes_notas\scratch_rescate_2026-11-21\h9_calor_rayos_11c46882\glm_s3"
os.makedirs(SCR, exist_ok=True)
HOST = "https://noaa-goes19.s3.amazonaws.com"
VLAT, VLON = -36.86, -71.38
LV1 = (-37.411, -71.352)
J2000 = datetime(2000, 1, 1, 12, 0, 0)


def hav(la, lo, la0, lo0):
    p1, p2 = np.radians(la0), np.radians(la)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lo - lo0) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def listar(h):
    pre = f"GLM-L2-LCFA/{h:%Y}/{h.timetuple().tm_yday:03d}/{h:%H}/"
    import xml.etree.ElementTree as ET
    r = requests.get(f"{HOST}/?list-type=2&prefix={pre}", timeout=300); r.raise_for_status()
    ns = "{http://s3.amazonaws.com/doc/2006-03-01/}"
    return [c.findtext(f"{ns}Key") for c in ET.fromstring(r.text).findall(f"{ns}Contents")]


def uno(key):
    out = os.path.join(SCR, key.split("/")[-1] + ".json")
    if os.path.exists(out):
        return json.load(open(out))
    import h5py
    for i in range(5):
        try:
            r = requests.get(f"{HOST}/{key}", timeout=300); r.raise_for_status()
            with h5py.File(io.BytesIO(r.content), "r") as f:
                la = f["flash_lat"][:].astype(float); lo = f["flash_lon"][:].astype(float)
                v = f["flash_time_offset_of_first_event"]
                off = v[:].astype(float) * float(v.attrs["scale_factor"][0]) + float(v.attrs["add_offset"][0])
                base = J2000 + timedelta(seconds=float(f["product_time"][()]))
            d = hav(la, lo, VLAT, VLON); m = d <= 150
            res = dict(key=key, n_total=int(len(la)),
                       fl=[[float(a), float(b), (base + timedelta(seconds=float(o))).isoformat()] for a, b, o in zip(la[m], lo[m], off[m])])
            json.dump(res, open(out, "w"))
            return res
        except Exception as e:  # noqa: BLE001
            err = e; time.sleep(3 * (i + 1))
    print("FALLA", key, repr(err), flush=True)
    return None


def main():
    lv = pd.read_csv(os.path.join(RES, "glm_destellos_chillan.csv"), parse_dates=["desde", "hasta"])
    lv["k"] = list(zip(lv.lat.round(4), lv.lon.round(4)))
    L = []
    for arg in sys.argv[1:]:
        h = datetime.strptime(arg, "%Y-%m-%dT%H")
        keys = listar(h)
        with ThreadPoolExecutor(6) as ex:
            rs = list(ex.map(uno, keys))
        ok = [r for r in rs if r is not None]
        fl = pd.DataFrame([x for r in ok for x in r["fl"]], columns=["lat", "lon", "t"])
        fl["t"] = pd.to_datetime(fl.t)
        fl = fl[(fl.t >= h) & (fl.t < h + timedelta(hours=1))]
        fl["d"] = hav(fl.lat.values, fl.lon.values, VLAT, VLON)
        fl["d_lv1"] = hav(fl.lat.values, fl.lon.values, *LV1)
        fl["k"] = list(zip(fl.lat.round(4), fl.lon.round(4)))
        mid = lv.desde + (lv.hasta - lv.desde) / 2
        lvh = lv[(mid >= h) & (mid < h + timedelta(hours=1))]
        L.append(f"Hora {h:%Y-%m-%d %H}:00 UTC: archivos LCFA {len(keys)}, leidos {len(ok)}")
        for nombre, ms3, mlv in (("<= 30 km del crater real", fl.d <= 30, lvh.d_km <= 30),
                                 ("zona comun (<= 100 km del crater y del centro de Lightning-v1)",
                                  (fl.d <= 100) & (fl.d_lv1 <= 100), lvh.d_km <= 100),
                                 ("<= 100 km del crater real (S3; Lightning-v1 no cubre todo)", fl.d <= 100, lvh.d_km <= 100)):
            a = fl[ms3]; b = lvh[mlv]
            com = sum(1 for la, lo in zip(b.lat, b.lon) if len(a) and hav(a.lat.values, a.lon.values, la, lo).min() <= 0.05)
            L.append(f"  {nombre}: S3 {len(a)}, Lightning-v1 {len(b)}, de Lightning-v1 con un destello S3 a <= 50 m: {com}")
        # horas reales de los destellos de Lightning-v1 a <= 30 km en esta hora, contra su intervalo asignado
        if len(fl):
            j = lvh[lvh.d_km <= 30]; dentro = 0
            for _, r in j.iterrows():
                d = hav(fl.lat.values, fl.lon.values, r.lat, r.lon); i = int(d.argmin())
                t = fl.t.iloc[i]
                dentro += int(d[i] <= 0.05 and r.desde - timedelta(seconds=20) <= t <= r.hasta + timedelta(seconds=20))
            L.append(f"  destellos de Lightning-v1 a <= 30 km cuya hora real (S3) cae en el intervalo asignado (+-20 s, duracion de un archivo): {dentro} de {len(j)}")
    txt = "\n".join(L)
    open(os.path.join(RES, "h9_contraste_glm_s3.txt"), "w", encoding="utf-8").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
