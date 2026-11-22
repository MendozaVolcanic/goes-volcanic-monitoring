"""H20a: relacion entre S (P publicada) y SL (P_IR) segun el cenit solar del objeto, solo con archivos de
evento. Sirve de comprobacion interna de la transferencia a Chillan: si de noche no hay rama solar, S deberia
ser igual a SL. Post hoc (decidido despues de ver el perfil). Escribe resultados/sza_S_SL.json.

Uso: python -I h20a_sza.py
"""
import os
import sys
import glob
import json
import numpy as np
import netCDF4 as nc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h20a_comun import EV_FUEGO, EV_CHILLAN, RES, arr, logit

sys.stdout.reconfigure(encoding="utf-8")
TRAMOS = [(0, 50), (50, 70), (70, 85), (85, 180)]


def main():
    out = {}
    for caso, patron in (("chillan", os.path.join(EV_CHILLAN, "VOLCAT-FD-vid357070_*.nc")),
                         ("fuego", os.path.join(EV_FUEGO, "VOLCAT-FD-vid342090_*.nc")),
                         ("san_cristobal", os.path.join(EV_FUEGO, "VOLCAT-FD-vid344020_*.nc"))):
        acc = {t: {"cuadros": 0, "pares": 0, "iguales_exactos": 0, "iguales_rel_1e-3": 0, "S_mayor_005": 0,
                   "S_menor_005": 0, "S_ge05": 0, "SL_ge05": 0, "saltos": []} for t in TRAMOS}
        for p in sorted(glob.glob(patron)):
            ds = nc.Dataset(p)
            idx = np.ma.filled(ds["event_idx"][:], -1).astype(int)
            S = arr(ds, "ash_spectral_signature_strength")
            SL = arr(ds, "ash_spectral_signature_strength_lwir_only")
            sza = np.ma.filled(ds["mean_feature_solar_zenith_angle"][:].astype("f8"), np.nan).ravel()
            for k in sorted(set(idx[idx >= 0].tolist())):
                t = next(t for t in TRAMOS if t[0] <= sza[k] < t[1])
                m = (idx == k) & np.isfinite(S) & np.isfinite(SL)
                s, sl = S[m], SL[m]
                a = acc[t]
                a["cuadros"] += 1
                a["pares"] += int(m.sum())
                a["iguales_exactos"] += int((s == sl).sum())
                a["iguales_rel_1e-3"] += int((np.abs(s - sl) <= 1e-3 * np.maximum(s, sl)).sum())
                a["S_mayor_005"] += int((s > sl + 0.05).sum())
                a["S_menor_005"] += int((s < sl - 0.05).sum())
                a["S_ge05"] += int((s >= 0.5).sum())
                a["SL_ge05"] += int((sl >= 0.5).sum())
                j = logit(s) - logit(sl)
                a["saltos"] += j[np.isfinite(j)].tolist()
            ds.close()
        out[caso] = {}
        for t, a in acc.items():
            j = np.array(a.pop("saltos"))
            a["salto_mediana"] = round(float(np.median(j)), 2) if j.size else None
            a["salto_p10_p90"] = [round(float(np.percentile(j, q)), 2) for q in (10, 90)] if j.size else None
            a["salto_abs_lt_0p01"] = int((np.abs(j) < 0.01).sum())
            out[caso]["sza_%d_%d" % t] = a
            print(caso, "sza %3d-%3d" % t, a)
    json.dump(out, open(os.path.join(RES, "sza_S_SL.json"), "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
