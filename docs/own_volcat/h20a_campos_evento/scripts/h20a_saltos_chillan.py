"""H20a, post hoc y descriptivo: valores del salto logit(S) - logit(SL) en los pixeles de dia de Chillan.
Pregunta: ¿se repiten pocos valores, como el salto que H19 midio en Fuego entre P y P_sub?
Aviso: el archivo de evento no trae P_sub, asi que este salto es contra P_IR y solo equivale al de H19 si
P_sub fuera igual a P_IR. Escribe resultados/saltos_chillan.txt.

Uso: python -I h20a_saltos_chillan.py
"""
import os
import sys
import glob
import numpy as np
import netCDF4 as nc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h20a_comun import EV_CHILLAN, RES, arr, logit

L2_VISTOS = (0.11, 4.56, 8.60, 12.74, 16.37, 17.07, 18.27, 18.96)


def main():
    js, ss, sls = [], [], []
    for p in sorted(glob.glob(os.path.join(EV_CHILLAN, "VOLCAT-FD-vid357070_*.nc"))):
        ds = nc.Dataset(p)
        idx = np.ma.filled(ds["event_idx"][:], -1).astype(int)
        S = arr(ds, "ash_spectral_signature_strength")
        SL = arr(ds, "ash_spectral_signature_strength_lwir_only")
        sza = float(np.ma.filled(ds["mean_feature_solar_zenith_angle"][:].astype("f8"), np.nan).ravel()[0])
        m = (idx >= 0) & np.isfinite(S) & np.isfinite(SL)
        if sza < 85:
            j = logit(S[m]) - logit(SL[m])
            ok = np.isfinite(j)
            js += j[ok].tolist()
            ss += S[m][ok].tolist()
            sls += SL[m][ok].tolist()
        ds.close()
    j, s, sl = np.array(js), np.array(ss), np.array(sls)
    lin = []
    lin.append("Chillan, cuadros de dia (cenit solar < 85): %d pixeles con S y SL" % j.size)
    lin.append("salto: p5 %.2f p25 %.2f p50 %.2f p75 %.2f p95 %.2f ; negativos: %d ; >= 5: %d" % (
        *np.percentile(j, [5, 25, 50, 75, 95]), (j < 0).sum(), (j >= 5).sum()))
    v, c = np.unique(np.round(j, 2), return_counts=True)
    o = np.argsort(-c)[:10]
    lin.append("valores mas repetidos (redondeo 0,01): %s" % [(float(v[i]), int(c[i])) for i in o])
    lin.append("valores distintos: %d de %d pixeles ; valor mas repetido aparece %d veces" % (v.size, j.size, c.max()))
    lin.append("pixeles a menos de 0,01 de los saltos vistos en el L2 de Fuego y San Cristobal %s: %s" % (
        L2_VISTOS, [int((np.abs(j - x) < 0.01).sum()) for x in L2_VISTOS]))
    alto = s >= 0.5
    lin.append("pixeles con S >= 0,5: %d ; su SL: mediana %.5f, max %.4f ; su salto: p10 %.2f p50 %.2f p90 %.2f" % (
        alto.sum(), np.median(sl[alto]), sl[alto].max(), *np.percentile(j[alto], [10, 50, 90])))
    with open(os.path.join(RES, "saltos_chillan.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lin) + "\n")
    print("\n".join(lin))


if __name__ == "__main__":
    main()
