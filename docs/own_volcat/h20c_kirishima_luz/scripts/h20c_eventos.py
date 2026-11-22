r"""H20c paso 1: pasa a npz la huella (event_idx >= 0) de los archivos ASHPLUMEPUFF de Kirishima: lat, lon, S.
Uso: python -I h20c_eventos.py <carpeta events> <carpeta salida fuera del repo>"""
import glob, os, sys
import numpy as np, netCDF4
ev, out = sys.argv[1], sys.argv[2]
for f in sorted(glob.glob(os.path.join(ev, "*vid282090*.nc"))):
    d = netCDF4.Dataset(f); g = lambda k: np.ma.filled(d.variables[k][:].astype("f8"), np.nan)
    m = g("event_idx") >= 0
    t = os.path.basename(f).split("_s")[1][8:14]
    np.savez(os.path.join(out, f"ev_{t}.npz"), lat=g("latitude")[m], lon=g("longitude")[m],
             s=g("ash_spectral_signature_strength")[m], zen=float(d.variables["mean_feature_solar_zenith_angle"][:][0]))
    print(t, int(m.sum()))
