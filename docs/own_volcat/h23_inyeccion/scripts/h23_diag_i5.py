r"""H23: diagnostico de la comprobacion de instrumento I5 (ciclo diurno), que fallo en la primera corrida:
el criterio pedia que la linea base de BT11 del terreno bajo subiera al menos 8 K entre las 09 y las 18 UTC y
subio 3,9 K. Solo datos de instrumento (ninguna inyeccion, ningun detector).

Este script es autonomo: trae adentro la linea base ORIGINAL del criterio (percentil 90 de los 10 dias anteriores)
y el intento descartado (percentil 90 de todos los otros dias del bloque), porque h23_medir.py ya usa la linea base
de la enmienda 1. Mira:
1. La forma del ciclo diurno de la linea base y de la BT11 cruda por grupo de pixeles: a que hora esta el minimo
   y el maximo. Un eje de tiempo corrido o un instrumento congelado no darian un ciclo con maximo cerca del
   mediodia solar.
2. Cuantos dias de prueba estan "tibios" (a 8 K o menos del dia mas tibio) a cada hora: mide cuan nublado fue el
   periodo.
3. El ciclo crudo del dia mas tibio.

Uso: python -I h23_diag_i5.py 10dias   -> resultados\h23_diag_i5_corrida1.json
     python -I h23_diag_i5.py bloque   -> resultados\h23_diag_i5_intento_p90_bloque.json
"""
import json
import os
import sys
import warnings

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h23_comun as K  # noqa: E402
import h23_medir as M  # noqa: E402

warnings.simplefilter("ignore", RuntimeWarning)
T_INI, T_FIN = 10 * 144, 33 * 144          # dias de prueba del criterio original: 01-10 al 23-10


def linea_base_p90(bt11, modo):
    """Percentil 90 a la misma hora (cuadro anterior, mismo y siguiente). modo '10dias': los 10 dias anteriores
    (criterio original). modo 'bloque': todos los otros dias del bloque salvo el 22-10. Minimo 15 muestras.
    Devuelve la referencia y el apoyo (muestras a 2 K o menos de la referencia)."""
    nt, ntot = T_FIN - T_INI, bt11.shape[0]
    ref = np.full((nt, M.NP_), np.nan, "float32")
    apoyo = np.zeros((nt, M.NP_), "uint8")
    with np.errstate(invalid="ignore"):
        for i in range(nt):
            t = T_INI + i
            if modo == "10dias":
                idx = [t - 144 * k + j for k in range(1, 11) for j in (-1, 0, 1)]
            else:
                idx = [t + 144 * k + j for k in range(-33, 34) if k != 0 for j in (-1, 0, 1)]
                idx = [x for x in idx if 0 <= x < ntot and x // 144 != 31]
            S = bt11[idx]
            r, n = M.cuantil_ordenado(np.sort(S, 0), 0.9)
            r[n < 15] = np.nan
            ref[i], apoyo[i] = r, np.minimum((S >= r - 2.0).sum(0), 255)
    return ref, apoyo


def main(modo):
    z = np.load(os.path.join(K.H23, "cubo_oct.npz"))
    bt11 = K.bt_de_rad(z["rad14"].reshape(-1, M.NP_).astype("float64"), z["co14"]).astype("float32")
    ref, apoyo = linea_base_p90(bt11, modo)
    nd = (T_FIN - T_INI) // 144
    bt = bt11[T_INI:T_FIN].reshape(nd, 144, M.NP_)
    ref = ref.reshape(nd, 144, M.NP_)
    g = M.grupos("chillan")
    grupos = {"cumbre": g["cumbre"], "bajo": g["bajo"], "valle_bajo_300m": np.where(M.ZDEM < 300)[0],
              "cota_300_a_800": np.where((M.ZDEM >= 300) & (M.ZDEM < 800))[0],
              "cota_1500_a_2000": np.where((M.ZDEM >= 1500) & (M.ZDEM < 2000))[0]}
    out = {}
    for nombre, px in grupos.items():
        r = np.nanmedian(np.nanmedian(ref[:, :, px], 2), 0)          # ciclo de la linea base (mediana de dias)
        m = np.nanmedian(bt[:, :, px], 2)                            # BT11 cruda del grupo por dia y cuadro
        crudo90 = np.nanpercentile(m, 90, axis=0)
        crudo50 = np.nanmedian(m, 0)
        hmin, hmax = int(np.nanargmin(r)), int(np.nanargmax(r))
        d = int(np.nanargmax(np.nanmean(m, 1)))
        ap = apoyo.reshape(nd, 144, M.NP_)[:, :, px]
        out[nombre] = dict(n_pixeles=int(len(px)), cota_mediana=float(np.median(M.ZDEM[px])),
                           ref_09=float(r[54]), ref_18=float(r[108]), ref_18_menos_09=float(r[108] - r[54]),
                           ref_min=float(np.nanmin(r)), hora_min_utc=f"{hmin // 6:02d}:{hmin % 6 * 10:02d}",
                           ref_max=float(np.nanmax(r)), hora_max_utc=f"{hmax // 6:02d}:{hmax % 6 * 10:02d}",
                           ref_amplitud=float(np.nanmax(r) - np.nanmin(r)),
                           crudo_p90_amplitud=float(np.nanmax(crudo90) - np.nanmin(crudo90)),
                           crudo_p50_18_menos_09=float(crudo50[108] - crudo50[54]),
                           ref_cada_3h=[round(float(r[i]), 2) for i in range(0, 144, 18)],
                           dias_tibios_de_23={f"{h:02d}utc": int((m[:, h * 6] >= np.nanmax(m[:, h * 6]) - 8).sum())
                                              for h in (3, 9, 15, 18, 20, 22)},
                           dia_mas_tibio=dict(dia_de_prueba=d, bt_09=float(m[d, 54]), bt_16=float(m[d, 96]),
                                              bt_18=float(m[d, 108]), bt_20=float(m[d, 120])),
                           apoyo_mediano_por_hora={f"{h:02d}utc": float(np.median(ap[:, h * 6]))
                                                   for h in (3, 9, 15, 18, 20, 22)})
        print(nombre, json.dumps(out[nombre]))
    res = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
    sal = {"10dias": "h23_diag_i5_corrida1.json", "bloque": "h23_diag_i5_intento_p90_bloque.json"}[modo]
    json.dump(out, open(os.path.join(res, sal), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
