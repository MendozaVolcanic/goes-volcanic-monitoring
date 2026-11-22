r"""H20b, análisis POSTERIOR (no estaba en el criterio): salto de log-odds logit(S) - logit(SL) por píxel de la huella.

Uso: python -I h20b_saltos_posthoc.py <carpeta events del paquete kirsh> <txt de salida>
"""
import glob, os, sys
import numpy as np
import netCDF4

ev, out = sys.argv[1], sys.argv[2]
with open(out, "w", encoding="utf-8") as fh:
    fh.write("inicio | cenit solar | saltos de log-odds ordenados (logit S - logit SL), huella event_idx >= 0\n")
    for f in sorted(glob.glob(os.path.join(ev, "*vid282090*.nc"))):
        d = netCDF4.Dataset(f)
        g = lambda k: np.ma.filled(d.variables[k][:].astype("f8"), np.nan)
        m = g("event_idx") >= 0
        s = np.clip(g("ash_spectral_signature_strength")[m], 1e-12, 1 - 1e-12)
        sl = np.clip(g("ash_spectral_signature_strength_lwir_only")[m], 1e-12, 1 - 1e-12)
        j = np.sort(np.log(s / (1 - s)) - np.log(sl / (1 - sl)))
        z = float(d.variables["mean_feature_solar_zenith_angle"][:][0])
        fh.write(f"{os.path.basename(f).split('_s')[1][:13]} | {z:.1f} | {' '.join(f'{x:.2f}' for x in j)}\n")
print(open(out, encoding="utf-8").read())
