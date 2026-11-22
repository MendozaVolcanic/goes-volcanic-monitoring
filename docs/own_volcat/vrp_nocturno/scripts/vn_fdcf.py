r"""FDCF de NOAA en los mismos cuadros nocturnos de Chillán (criterio §4, informativo). Para cada cuadro de la serie
de Chillán desde el 25-09 fuera del periodo de H17, lee la máscara del FDCF del mismo scan (ABI-L2-FDCF, misma
grilla de 2 km) en la ventana de Chillán y cuenta píxeles con clase de fuego (HOTSPOT_MASK_VALUES de
src/fetch/goes_fdcf.py) a <= 10 km de la cumbre aparente. Escribe D:\goes_cache\vrp_nocturno\fdcf.csv.
"Sin scan" queda como fila con n_fuego vacío: no verificable, no cero.
Uso: python -I vn_fdcf.py [nproc]
"""
import os
import sys
import time
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vn_comun as K  # noqa: E402
from src.fetch.goes_fdcf import HOTSPOT_MASK_VALUES  # noqa: E402

S = K.Sitio("Nevados de Chillan")
_la, _lo = K.cumbre_aparente("Nevados de Chillan")
CERCA = K.hav(S.lat, S.lon, _la, _lo) <= 10.0
_fs = None
_list = {}


def fs():
    global _fs
    if _fs is None:
        import s3fs
        _fs = s3fs.S3FileSystem(anon=True)
    return _fs


def tarea(c):
    import h5py
    dt = datetime.strptime(c, "%Y%m%d_%H%M")
    p = f"noaa-goes19/ABI-L2-FDCF/{dt:%Y}/{dt.timetuple().tm_yday:03d}/{dt:%H}/"
    tag = f"_s{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}"
    for i in range(4):
        try:
            if p not in _list:
                _list[p] = fs().ls(p)
            ks = [k for k in _list[p] if tag in k]
            if not ks:
                return dict(t=dt, n_fuego=np.nan, clases="sin_scan")
            r0, r1, c0, c1 = K.ventana("Nevados de Chillan")
            with fs().open(ks[0], "rb") as fo, h5py.File(fo, "r") as f:
                m = f["Mask"][r0:r1, c0:c1]
            hot = np.isin(m, list(HOTSPOT_MASK_VALUES)) & CERCA
            return dict(t=dt, n_fuego=int(hot.sum()), clases=" ".join(str(int(v)) for v in m[hot]))
        except FileNotFoundError:
            return dict(t=dt, n_fuego=np.nan, clases="sin_hora")
        except Exception as e:  # noqa: BLE001
            err = repr(e)
            time.sleep(2 * (i + 1))
    return dict(t=dt, n_fuego=np.nan, clases="error " + err[:80])


def lista():
    from vn_bajar import lista as lista_l1b
    out = []
    for c, _ in lista_l1b():
        dt = datetime.strptime(c, "%Y%m%d_%H%M")
        if dt < datetime(2026, 9, 25) or datetime(2026, 10, 20) <= dt < datetime(2026, 11, 19, 12):
            continue
        if K.sza(dt, S.v.lat, S.v.lon) < 90:
            continue
        out.append(c)
    return sorted(out)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    T = lista()
    print("cuadros", len(T), flush=True)
    with ProcessPoolExecutor(n) as ex:
        R = list(ex.map(tarea, T, chunksize=4))
    df = pd.DataFrame(R)
    df.to_csv(os.path.join(K.OUT, "fdcf.csv"), index=False)
    print(df.clases.value_counts().head(10))
    print("con fuego:", int((df.n_fuego > 0).sum()), "| sin verificar:", int(df.n_fuego.isna().sum()))
