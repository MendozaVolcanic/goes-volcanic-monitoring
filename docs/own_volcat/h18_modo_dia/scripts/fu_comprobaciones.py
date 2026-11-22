r"""H18 etapa 1: comprobaciones previas del criterio (1 y 2, y rango de entradas), antes de calcular nada nuestro.

Sólo mira lo que publica VOLCAT en el caso de Fuego (npz de fu_extraer.py, D:\goes_notas\s16\modo_dia\npz).
"""
import glob
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
NPZ = r"D:\goes_notas\s16\modo_dia\npz"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")


def main():
    filas, tot = [], {"dia": 0, "dia_ge05": 0, "dia_difIR": 0, "dia_ref2_ok": 0, "dia_nrat_lrc_fin": 0}
    tipos = {}
    for f in sorted(glob.glob(os.path.join(NPZ, "fu_*.npz"))):
        d = np.load(f)
        h = os.path.basename(f)[3:9]
        sz = d["geocatL1__pixel_solar_zenith_angle"].ravel()
        p = d["geocatL2__ash_probability"].ravel()
        pir = d["geocatL2__ash_probability_IR"].ravel()
        r2 = d["geocatL1__channel_2_reflectance"].ravel()
        nl = d["geocatDIAGS1__ref_rat_nir_lrc"].ravel()
        st = d["geocatL1__pixel_surface_type"].ravel()
        dia = (sz < 85) & np.isfinite(p)
        dif = dia & np.isfinite(pir) & (np.abs(p - pir) > 0.05)
        for v, c in zip(*np.unique(st[dia & np.isfinite(st)], return_counts=True)):
            tipos[int(v)] = tipos.get(int(v), 0) + int(c)
        fila = {"hora": h, "sza_min": float(np.nanmin(sz)), "sza_max": float(np.nanmax(sz)),
                "n_dia": int(dia.sum()), "n_dia_ge05": int((dia & (p >= 0.5)).sum()),
                "n_dia_difIR": int(dif.sum()),
                "ref2_rango_ok": int((dia & (r2 >= 0) & (r2 <= 120)).sum()),
                "nrat_lrc_finito": int((dia & np.isfinite(nl)).sum()),
                "p_constante": bool(np.nanstd(p[dia]) == 0) if dia.any() else None}
        filas.append(fila)
        tot["dia"] += fila["n_dia"]; tot["dia_ge05"] += fila["n_dia_ge05"]; tot["dia_difIR"] += fila["n_dia_difIR"]
        tot["dia_ref2_ok"] += fila["ref2_rango_ok"]; tot["dia_nrat_lrc_fin"] += fila["nrat_lrc_finito"]
    tot["frac_difIR"] = tot["dia_difIR"] / max(tot["dia"], 1)
    tot["frac_nrat_lrc_finito"] = tot["dia_nrat_lrc_fin"] / max(tot["dia"], 1)
    tot["frac_ref2_rango"] = tot["dia_ref2_ok"] / max(tot["dia"], 1)
    tot["cuadros_con_dia"] = sum(1 for x in filas if x["n_dia"] > 0)
    tot["superficie_dia"] = tipos
    tot["comprobacion_1"] = tot["dia"] >= 10000 and tot["dia_ge05"] >= 100
    tot["comprobacion_2"] = tot["frac_difIR"] >= 0.01
    json.dump({"total": tot, "cuadros": filas}, open(os.path.join(OUT, "fu_comprobaciones.json"), "w"), indent=1)
    print(json.dumps(tot, indent=1))
    for x in filas:
        print(x["hora"], f'{x["sza_min"]:.0f}-{x["sza_max"]:.0f}', x["n_dia"], x["n_dia_ge05"], x["n_dia_difIR"])


if __name__ == "__main__":
    main()
