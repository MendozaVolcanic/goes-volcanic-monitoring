r"""H20b: probabilidad publicada (S) e infrarroja (SL) en la huella de los archivos ASHPLUMEPUFF de Kirishima.

Uso: python -I h20b_medir.py <carpeta events del paquete kirsh> <csv de salida>
S = ash_spectral_signature_strength, SL = ..._lwir_only (calibrados en Fuego por H20a, PR 92).
Huella = event_idx >= 0. Regla: criterio_2026-11-22.md.
"""
import csv, glob, os, sys
import numpy as np
import netCDF4

ev, out = sys.argv[1], sys.argv[2]
filas, attrs = [], set()
for f in sorted(glob.glob(os.path.join(ev, "*vid*.nc"))):
    d = netCDF4.Dataset(f)
    if "event_type" not in d.variables or str(d.variables["event_type"][:][0]) != "ASHPLUMEPUFF":
        continue
    v = d.variables
    attrs.add((v["ash_spectral_signature_strength"].long_name, getattr(v["ash_spectral_signature_strength"], "units", ""),
               v["ash_spectral_signature_strength_lwir_only"].long_name))
    g = lambda k: np.ma.filled(v[k][:].astype("f8"), np.nan)
    idx, s, sl = g("event_idx"), g("ash_spectral_signature_strength"), g("ash_spectral_signature_strength_lwir_only")
    m = np.isfinite(idx) & (idx >= 0)
    n = int(m.sum())
    ok = m & np.isfinite(s) & (s >= 0) & (s <= 1) & np.isfinite(sl) & (sl >= 0) & (sl <= 1)
    frac = ok.sum() / n if n else 0.0
    ms = float(np.median(s[ok])) if ok.any() else np.nan
    if n == 0 or frac < 0.8:
        clase = "SIN DATO"
    elif ms >= 0.5:
        clase = "ALTA"
    elif ms < 0.05:
        clase = "BAJA"
    else:
        clase = "INTERMEDIA"
    filas.append(dict(inicio=os.path.basename(f).split("_s")[1][:13], n_huella=n, frac_valida=round(frac, 3),
                      S_mediana=round(ms, 4), S_ge05=int((s[ok] >= 0.5).sum()), SL_mediana=round(float(np.median(sl[ok])), 4) if ok.any() else np.nan,
                      SL_ge05=int((sl[ok] >= 0.5).sum()), cenit_solar=round(float(v["mean_feature_solar_zenith_angle"][:][0]), 1),
                      feature_age_min=round(float(v["feature_age"][:][0]), 3) if "feature_age" in v else np.nan, clase=clase))
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(filas[0])); w.writeheader(); w.writerows(filas)
for r in filas: print(r)
print("atributos:", attrs)
