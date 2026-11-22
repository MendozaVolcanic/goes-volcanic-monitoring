r"""H23: diagnostico de la comprobacion de instrumento I5 (ciclo diurno), que fallo en la primera corrida:
el criterio pedia que la linea base de BT11 del terreno bajo subiera al menos 8 K entre las 09 y las 18 UTC y
subio 3,9 K. Antes de tocar nada se mira, solo con datos de instrumento (ninguna inyeccion, ningun detector):

1. La forma del ciclo diurno de BT11_ref y de la BT11 cruda (mediana y percentiles) por grupo de pixeles: a que
   hora esta el minimo y el maximo. Un eje de tiempo corrido o un instrumento congelado no darian un ciclo con
   el maximo en la tarde de Chile.
2. El mismo ciclo en los pixeles mas bajos de toda la ventana (valle central, bajo 300 m), donde la superficie
   son cultivos y no bosque de ladera.
3. La amplitud por grupo de cota.

Salida: resultados\h23_diag_i5.json. Uso: python -I h23_diag_i5.py
"""
import json
import os
import sys
import warnings

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h23_medir as M  # noqa: E402

warnings.simplefilter("ignore", RuntimeWarning)


def main():
    B = M.bloque_datos("oct")
    nd = (B["t_fin"] - B["t_ini"]) // 144
    bt = (B["D1"] + B["ref"]).reshape(nd, 144, M.NP_)        # BT11 cruda de los dias de prueba
    ref = B["ref"].reshape(nd, 144, M.NP_)
    g = M.grupos("chillan")
    grupos = {"cumbre": g["cumbre"], "bajo": g["bajo"], "valle_bajo_300m": np.where(M.ZDEM < 300)[0],
              "cota_300_a_800": np.where((M.ZDEM >= 300) & (M.ZDEM < 800))[0],
              "cota_1500_a_2000": np.where((M.ZDEM >= 1500) & (M.ZDEM < 2000))[0]}
    out = {}
    for nombre, px in grupos.items():
        r = np.nanmedian(np.nanmedian(ref[:, :, px], 2), 0)          # ciclo de la linea base (mediana de dias)
        crudo90 = np.nanpercentile(np.nanmedian(bt[:, :, px], 2), 90, axis=0)   # dias tibios (despejados) crudos
        crudo50 = np.nanmedian(np.nanmedian(bt[:, :, px], 2), 0)
        hmin, hmax = int(np.nanargmin(r)), int(np.nanargmax(r))
        out[nombre] = dict(n_pixeles=int(len(px)), cota_mediana=float(np.median(M.ZDEM[px])),
                           ref_09=float(r[54]), ref_18=float(r[108]), ref_18_menos_09=float(r[108] - r[54]),
                           ref_min=float(np.nanmin(r)), hora_min_utc=f"{hmin // 6:02d}:{hmin % 6 * 10:02d}",
                           ref_max=float(np.nanmax(r)), hora_max_utc=f"{hmax // 6:02d}:{hmax % 6 * 10:02d}",
                           ref_amplitud=float(np.nanmax(r) - np.nanmin(r)),
                           crudo_p90_amplitud=float(np.nanmax(crudo90) - np.nanmin(crudo90)),
                           crudo_p50_18_menos_09=float(crudo50[108] - crudo50[54]),
                           ref_cada_3h=[round(float(r[i]), 2) for i in range(0, 144, 18)])
        # Cuantos dias de prueba estan "tibios" (a 8 K o menos del dia mas tibio) a cada hora: mide cuan nublado
        # fue el periodo, y el ciclo crudo del dia mas despejado
        m = np.nanmedian(bt[:, :, px], 2)
        out[nombre]["dias_tibios_de_%d" % nd] = {f"{h:02d}utc": int((m[:, h * 6] >= np.nanmax(m[:, h * 6]) - 8).sum())
                                                 for h in (3, 9, 15, 18, 20, 22)}
        d = int(np.nanargmax(np.nanmean(m, 1)))
        out[nombre]["dia_mas_tibio"] = dict(dia_de_prueba=d, bt_09=float(m[d, 54]), bt_16=float(m[d, 96]),
                                            bt_18=float(m[d, 108]), bt_20=float(m[d, 120]))
        ap = B["apoyo"].reshape(nd, 144, M.NP_)[:, :, px]
        out[nombre]["apoyo_mediano_por_hora"] = {f"{h:02d}utc": float(np.median(ap[:, h * 6])) for h in (3, 9, 15, 18, 20, 22)}
        print(nombre, json.dumps(out[nombre]))
    res = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
    sal = sys.argv[1] if len(sys.argv) > 1 else "h23_diag_i5.json"
    json.dump(out, open(os.path.join(res, sal), "w"), indent=1)


if __name__ == "__main__":
    main()
