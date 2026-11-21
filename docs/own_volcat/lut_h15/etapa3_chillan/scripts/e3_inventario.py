r"""H15 etapa 3: inventario de los 60 cuadros de evento VOLCAT de Chillán y su ubicación en la ventana L1b.

Por qué: la huella vinculante es `event_idx` (la del PNG está corrida 1 px, H14). Cada píxel publicado se ubica
en la ventana de 83 × 94 píxeles de nuestras L1b por latitud y longitud (las dos son la grilla fija del ABI, así
que el píxel más cercano tiene que estar a ~0 km; se exige < 0,5 km). La BT de VOLCAT de esos píxeles se guarda
para comprobar después que nuestra L1b es la misma (si no lo fuera, la huella estaría corrida).

Salidas: E3_DIR\inventario.npz (grillas derivadas de archivos de acceso restringido: NO va al repo) y
resultados\inventario_cuadros.csv (sólo conteos por cuadro).
Uso: python -I e3_inventario.py
"""
import csv
import glob
import os
import sys
from datetime import datetime

import netCDF4 as nc
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e3_comun as K  # noqa: E402
import h13_comun as H  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
C = H.C
LAT, LON = C.LAT, C.LON


def arr(ds, k):
    return np.ma.filled(np.ma.asarray(ds[k][:]).astype("float64"), np.nan)


def main():
    filas, out = [], {}
    for f in sorted(glob.glob(os.path.join(K.EVDIR, "*.nc"))):
        b = os.path.basename(f)
        t = datetime.strptime(b.split("_s")[1][:12], "%Y%m%d%H%M")
        ds = nc.Dataset(f)
        ev = arr(ds, "event_idx")
        la, lo = arr(ds, "latitude"), arr(ds, "longitude")
        yy, xx = np.nonzero(ev >= 0)
        wy, wx, dk = [], [], []
        for y, x in zip(yy, xx):
            d = np.hypot((LAT - la[y, x]) * 111.2, (LON - lo[y, x]) * 111.2 * np.cos(np.radians(la[y, x])))
            j = np.nanargmin(d)
            wy.append(j // LAT.shape[1]); wx.append(j % LAT.shape[1]); dk.append(d.flat[j])
        wy, wx, dk = np.array(wy), np.array(wx), np.array(dk)
        ok = dk < 0.5
        bt = {c: arr(ds, f"brightness_temperature_{c}micron")[yy, xx] for c in (8, 11, 12)}
        k = f"{t:%Y%m%d_%H%M}"
        out[k] = dict(wy=wy[ok], wx=wx[ok], bt8=bt[8][ok], bt11=bt[11][ok], bt12=bt[12][ok])
        filas.append(dict(cuadro=k, n_evento=int(len(yy)), n_en_ventana=int(ok.sum()),
                          dist_max_km=round(float(dk.max()), 3) if len(dk) else None))
        ds.close()
    np.savez_compressed(os.path.join(K.E3DIR, "inventario.npz"),
                        **{f"{k}__{v}": a for k, d in out.items() for v, a in d.items()})
    with open(os.path.join(K.RES, "inventario_cuadros.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, fieldnames=list(filas[0]))
        w.writeheader(); w.writerows(filas)
    n = sum(r["n_evento"] for r in filas); m = sum(r["n_en_ventana"] for r in filas)
    print("cuadros", len(filas), "pixeles", n, "en ventana", m,
          "dist max km", max(r["dist_max_km"] or 0 for r in filas))


if __name__ == "__main__":
    main()
