"""beta73: huellas VOLCAT de los cuadros positivos en la grilla ABI de la ventana 83x94.

Usa huellas_h3.huella (decodificacion de pruebaA_28oct.py: ceniza a <= 50 km del crater, vecino mas cercano,
sin dilatar). Ademas guarda la mascara de ceniza a CUALQUIER distancia, para sacar del anillo los pixeles
con ceniza (criterio, seccion 5.3). Cuadros con < 3 px de huella: descartados antes de medir.
Salida: huellas_b73.npz (claves h_YYYYmmdd_HHMM y a_YYYYmmdd_HHMM) y huellas_b73.json.
"""
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import os, sys, json
import numpy as np
import comun_b73 as C
sys.path.insert(0, C.H3)
import huellas_h3 as H  # noqa: E402
from PIL import Image  # noqa: E402

vc, p = H.vc, H.p


def ceniza_toda(fn):
    """Mascara de ceniza a cualquier distancia, misma decodificacion, en la grilla ABI."""
    a = np.asarray(Image.open(fn).convert("RGB"), dtype="float64"); hmap = int(vc.MAP_FRAC * a.shape[0])
    bins = vc.palette_bins(a[hmap:]); m = a[:hmap]; cm = vc._saturation(m) >= 0.2
    ok = np.zeros(cm.shape, bool)
    if cm.any() and bins is not None:
        ok[cm] = vc.classify_pixels(m[cm], bins)["ok"]
    ok &= p.VALIDO[:hmap]
    out = np.zeros(H.LAT.shape, bool)
    ins = (H.RR >= 0) & (H.RR < hmap) & (H.CC >= 0) & (H.CC < a.shape[1])
    out[ins] = ok[H.RR[ins], H.CC[ins]]
    return out


if __name__ == "__main__":
    out, meta = {}, {}
    for dt, est in C.positivos():
        kk = C.k(dt); fn = C.png(dt)
        hv, hh = H.huella(fn)
        n = int(hv.sum()) if hv is not None else 0
        e = "ok" if n >= 3 else "descartado_<3px"
        meta[kk] = {"estrato": est, "estado": e, "n_px": n, "png": os.path.basename(fn),
                    "altura_med_km": float(np.nanmedian(hh[hv])) if n else None}
        out["h_" + kk] = hv; out["a_" + kk] = ceniza_toda(fn)
        print(kk, est, e, n, meta[kk]["altura_med_km"], flush=True)
    np.savez_compressed(os.path.join(C.HERE, "huellas_b73.npz"), **out)
    json.dump(meta, open(os.path.join(C.HERE, "huellas_b73.json"), "w"), indent=1)
