r"""H20c paso 2: en la huella, compara P publicada con P_SW_IR, P_IR y subset de la L2 (regla del criterio).
Uso: <venv_hdf4 python> -I h20c_medir.py <carpeta l2_data> <carpeta npz de eventos> <csv salida>"""
import csv, glob, os, sys
import numpy as np
from pyhdf.SD import SD, SDC
L2, EV, OUT = sys.argv[1:4]
P = "vcat_ashdet_pix_2_7_10_11_13_14_15_"
l2 = sorted(glob.glob(os.path.join(L2, "geocatL2.HIMAWARI-9.JP.2025183.*.hdf")))
def l2t(f): return f.split(".")[-2]
def sec(h): return int(h[:2]) * 3600 + int(h[2:4]) * 60 + int(h[4:6])
filas = []
for e in sorted(glob.glob(os.path.join(EV, "ev_*.npz"))):
    z = np.load(e); t = os.path.basename(e)[3:9]
    # la L2 cuyo nombre (hora redondeada) es la más cercana anterior o igual al inicio del barrido
    cand = [f for f in l2 if sec(l2t(f)) <= sec(t) + 60]
    f = max(cand, key=lambda x: sec(l2t(x)))
    sd = SD(f, SDC.READ)
    def r(k):
        ds = sd.select(k); a = np.asarray(ds[:]).astype("f8"); fv = ds.attributes().get("_FillValue")
        if fv is not None: a[a == fv] = np.nan
        return a
    la, lo = r("pixel_latitude"), r("pixel_longitude")
    p, pir, psw, sub = r(P + "ash_probability"), r(P + "ash_probability_IR"), r(P + "ash_probability_SW_IR"), r(P + "ash_probability_subset")
    key = {(round(a, 4), round(b, 4)): i for i, (a, b) in enumerate(zip(la.ravel(), lo.ravel())) if np.isfinite(a)}
    ii = [key.get((round(a, 4), round(b, 4))) for a, b in zip(z["lat"], z["lon"])]
    n, nal = len(ii), sum(i is not None for i in ii)
    fila = dict(evento=t, l2=l2t(f), cenit=round(float(z["zen"]), 1), n_huella=n, alineados=nal)
    if nal < n:
        fila["clase"] = "SIN DATO (alineacion)"; filas.append(fila); continue
    ii = np.array(ii)
    P_, I_, W_, B_ = p.ravel()[ii], pir.ravel()[ii], psw.ravel()[ii], sub.ravel()[ii]
    fila["max_dif_S_vs_P"] = float(np.nanmax(np.abs(z["s"] - P_)))
    fila["SW_IR_finita"] = int(np.isfinite(W_).sum())
    fila["SW_IR_igual_IR"] = int((np.abs(W_ - I_) <= 0.01).sum())
    alto = P_ >= 0.5
    fila["n_P_ge05"] = int(alto.sum())
    if alto.any():
        fila["frac_P_igual_SW"] = round(float((np.abs(P_[alto] - W_[alto]) <= 0.01).mean()), 3)
        fila["frac_P_sobre_SW"] = round(float((P_[alto] > W_[alto] + 0.05).mean()), 3)
        fila["frac_P_igual_subset"] = round(float((np.abs(P_[alto] - B_[alto]) <= 0.01).mean()), 3)
        fila["P_med"], fila["SW_med"], fila["IR_med"] = [round(float(np.nanmedian(x[alto])), 4) for x in (P_, W_, I_)]
    if fila["max_dif_S_vs_P"] > 1e-6 or fila["SW_IR_finita"] < n or np.nanstd(W_) == 0:
        fila["clase"] = "SIN DATO (lectura o SW_IR muerta)"
    elif not alto.any():
        fila["clase"] = "sin P>=0,5"
    elif fila["frac_P_igual_SW"] >= 0.9:
        fila["clase"] = "LUZ"
    elif fila["frac_P_sobre_SW"] >= 0.5:
        fila["clase"] = "SEGUIMIENTO"
    else:
        fila["clase"] = "MIXTO"
    filas.append(fila)
campos = sorted({k for f in filas for k in f}, key=lambda k: list(filas[-1]).index(k) if k in filas[-1] else 99)
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=campos); w.writeheader(); w.writerows(filas)
for f in filas: print(f)
