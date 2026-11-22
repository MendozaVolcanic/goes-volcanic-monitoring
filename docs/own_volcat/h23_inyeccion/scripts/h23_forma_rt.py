r"""H23, S5: cuanto se equivoca la forma analitica de la inyeccion por ignorar la atmosfera SOBRE la capa.

La forma analitica supone que la parte del pixel cubierta por la capa emite B(T_tope) hasta el satelite. En
realidad el aire que queda encima absorbe un poco y emite mas frio. Con el modelo radiativo propio (rt.py, linea
por linea, validado en mauna_loa_c2b/INFORME_C2_C2b.md) se calcula la radiancia al tope de la atmosfera de una
capa negra a T_tope puesta a 3, 4 y 5 km, con y sin el aire de encima, en perfiles GFS reales de Chillan
(20 al 23-10, cache de H13, solo lectura). La diferencia, en K, es el error de la forma analitica por unidad de
emisividad.

Pide: H3_RT_DL=D:\goes_cache\rt y H3_RT_LBL=D:\goes_notas\local_f3a7d295\h12_datos\extra\h3_meta\lbl
Uso: python -I h23_forma_rt.py   -> resultados\h23_forma_rt.json
"""
import glob
import json
import os
import sys
from datetime import datetime

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "h3_h7", "scripts_h3"))
import h23_comun as K  # noqa: E402
import rt  # noqa: E402

GFS_H13 = r"D:\goes_cache\h13\gfs"
NODO = (4, 4)            # -36,75 / -71,50: el nodo de 0,25 grados mas cercano a la cumbre
RES = os.path.join(os.path.dirname(AQUI), "resultados")


def p_de_z(valida, zs):
    """Presion (hPa) a las alturas zs en el nodo, con la altura geopotencial de los analisis de H23."""
    hs, lp = [], []
    for f in sorted(glob.glob(os.path.join(K.GFS, "gfs_202610*.npz"))):
        z = np.load(f)
        Z = z["Z"][:, NODO[0], NODO[1]]
        lp.append(np.interp(zs, Z, np.log(z["p"])))
        hs.append((datetime.strptime(os.path.basename(f)[4:14], "%Y%m%d%H") - datetime(2026, 1, 1)).total_seconds() / 3600)
    th = (valida - datetime(2026, 1, 1)).total_seconds() / 3600
    lp = np.array(lp)
    return np.exp([np.interp(th, hs, lp[:, i]) for i in range(len(zs))])


def main():
    with np.load(sorted(glob.glob(os.path.join(K.L1B, "2026*.npz")))[0]) as z0:   # Planck del NetCDF
        co = {b: z0[f"co{b}"] for b in (14, 15)}
    M = rt.Modelo()
    sec = 1.0 / np.cos(np.radians(rt.cenit_satelital(-36.86, -71.38)))
    zs = [3000.0, 4000.0, 5000.0]
    negro = {b: 1.0 for b in rt.BANDS}
    filas = []
    for f in sorted(glob.glob(os.path.join(GFS_H13, "gfs_202610*.npz"))):
        g = np.load(f)
        valida = datetime.strptime(os.path.basename(f)[4:14], "%Y%m%d%H")
        if not (datetime(2026, 10, 20) <= valida <= datetime(2026, 10, 24)):
            continue
        T, q, o3 = (g[k][:, NODO[0], NODO[1]] for k in ("T", "q", "o3"))
        ptop = p_de_z(valida, zs)
        for z, p in zip(zs, ptop):
            Ttop = float(np.interp(np.log(p), np.log(g["p"][::-1]), T[::-1]))
            con = M.radiancia(g["p"], T, q, o3, p, Ttop, sec, emis=negro)        # capa negra con el aire de encima
            sin = M.radiancia(g["p"], T, q, o3, 1.5, Ttop, sec, emis=negro)      # sin aire encima (corte a 1,5 hPa)
            d = {b: float(rt.bt_de_rad(con[b], co[b]) - rt.bt_de_rad(sin[b], co[b])) for b in (14, 15)}
            filas.append(dict(valida=f"{valida:%Y-%m-%d %H}", z_km=z / 1000, p_hPa=float(p), Ttop=Ttop,
                              d11=d[14], d12=d[15], dbtd=d[14] - d[15]))
    out = {"sec_cenit": float(sec), "perfiles": len(filas) // 3, "filas": filas, "resumen": {}}
    for z in zs:
        x = [r for r in filas if r["z_km"] == z / 1000]
        out["resumen"][f"{z / 1000:.0f}km"] = {k: dict(mediana=float(np.median([r[k] for r in x])),
                                                      min=float(np.min([r[k] for r in x])),
                                                      max=float(np.max([r[k] for r in x]))) for k in ("d11", "d12", "dbtd")}
    json.dump(out, open(os.path.join(RES, "h23_forma_rt.json"), "w"), indent=1)
    print("sec", round(sec, 3), "perfiles", out["perfiles"])
    print(json.dumps(out["resumen"], indent=1))


if __name__ == "__main__":
    main()
