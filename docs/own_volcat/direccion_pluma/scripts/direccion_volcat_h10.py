"""H10: direccion de la huella VOLCAT anclada al crater en cada cuadro de las ventanas REAV (criterio secciones
3 y 4). Decodifica el PNG con src/process/volcat_colorbar (misma regla que paso4_analisis.py: objetos de 4 a
500 px con un pixel a <= 10 km del crater; fuera los cuadros con manto o con objeto > 500 px a < 50 km).
Salida: h10/direccion_cuadros.json (una fila por slot de cada episodio) y huellas en h10/huellas_h10.npz
(mascara en la grilla ABI 83x94, para la prueba de senal). Uso: python -I direccion_volcat_h10.py"""
import os, sys, json
from datetime import timedelta
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h10 as C  # noqa: E402
from src.process import volcat_colorbar as vc  # noqa: E402

rr, cc = np.mgrid[0:755, 0:1000]
_la, _lo = C.png_latlon(rr, cc)
_ex, _ny = C.km(_la, _lo)
DCHI = np.hypot(_ex, _ny)
SEED, NEAR50 = DCHI <= 10, DCHI <= 50
VALIDO = np.ones((755, 1000), bool)
VALIDO[:70] = False; VALIDO[640:, :140] = False; VALIDO[640:, 840:] = False
# grilla ABI -> pixel PNG mas cercano (como huellas.py)
RR = np.rint((C.LAT0 - C.LAT) / C.DP).astype(int); CC = np.rint((C.LON - C.LON0) / C.DP).astype(int)


def frame_de(slot):
    for m in (0, -10, 10):
        t = slot + timedelta(minutes=m)
        r = C.INV.get(t)
        if r is not None and abs(m) <= 0:
            return t, r
    return slot, None


def decodificar(path):
    a = np.asarray(Image.open(path).convert("RGB"), dtype="float64")
    H, W = a.shape[:2]; hmap = int(vc.MAP_FRAC * H)
    bins = vc.palette_bins(a[hmap:])
    if bins is None:
        return None
    m = a[:hmap]; cmask = vc._saturation(m) >= 0.2
    ok = np.zeros(cmask.shape, bool)
    if cmask.any():
        ok[cmask] = vc.classify_pixels(m[cmask], bins)["ok"]
    ok &= VALIDO[:hmap, :W]
    lab, n = ndimage.label(ok, structure=np.ones((3, 3), int))
    tam = np.bincount(lab.ravel(), minlength=n + 1); tam[0] = 0
    manto = bool((tam / ok.size > vc.MAX_SECTOR_FRAC).any())
    near = np.unique(lab[NEAR50[:hmap, :W] & ok]); near = near[near > 0]
    grande = bool(any(tam[i] > 500 for i in near))
    ids = np.unique(lab[SEED[:hmap, :W] & ok]); ids = ids[ids > 0]
    anc = [i for i in ids if 4 <= tam[i] <= 500]
    hv = np.isin(lab, anc)
    return dict(manto=manto, grande=grande, hv=hv, hmap=hmap, W=W, tams=[int(tam[i]) for i in anc])


def medir(hv, h_km):
    r, c = np.nonzero(hv)
    la, lo = C.png_latlon(r, c)
    out = {}
    for nom, (a, b) in (("P1", (la, lo)), ("P0", C.corregir_p0(la, lo, h_km))):
        dx, dy = C.km(a, b)
        mx, my = float(np.mean(dx)), float(np.mean(dy))
        dmax = np.hypot(dx, dy); j = int(np.argmax(dmax))
        out[nom] = dict(cx=mx, cy=my, dist=float(np.hypot(mx, my)), az=C.azimut(mx, my),
                        az_lejano=C.azimut(float(dx[j]), float(dy[j])), dist_lejano=float(dmax[j]))
    return out


if __name__ == "__main__":
    filas, huellas = [], {}
    for e in C.EP:
        h_km = C.ZC_KM + e[4] / 1000.0
        for s in C.slots(e):
            t, r = frame_de(s)
            fila = dict(ep=e[0], jornada=e[1], slot=f"{s:%Y-%m-%d %H:%M}", az_reav=e[5], H=e[4])
            if r is None:
                fila["estado"] = "sin_cuadro"; filas.append(fila); continue
            p = C.png_path(r["fn"])
            if p is None:
                fila["estado"] = "sin_png"; filas.append(fila); continue
            d = decodificar(p)
            if d is None:
                fila["estado"] = "sin_barra"; filas.append(fila); continue
            fila["sza"] = round(r["sza"], 1)
            if d["manto"] or d["grande"]:
                fila["estado"] = "manto_o_grande"; filas.append(fila); continue
            if not d["tams"]:
                fila["estado"] = "sin_objeto_anclado"; filas.append(fila); continue
            m = medir(d["hv"], h_km)
            fila.update(tams=d["tams"], npx=int(d["hv"].sum()), **{f"{kk}_{q}": round(v, 2) for kk in m for q, v in m[kk].items()})
            fila["estado"] = "resuelta" if (m["P0"]["dist"] >= 2.0 and m["P1"]["dist"] >= 2.0) else "centroide_<2km"
            hv = d["hv"]; inside = (RR >= 0) & (RR < d["hmap"]) & (CC >= 0) & (CC < d["W"])
            hab = np.zeros(C.LAT.shape, bool); hab[inside] = hv[RR[inside], CC[inside]]
            huellas[C.k(s)] = hab
            filas.append(fila)
    json.dump(filas, open(os.path.join(C.WORK, "direccion_cuadros.json"), "w"), indent=1)
    np.savez_compressed(os.path.join(C.WORK, "huellas_h10.npz"), **huellas)
    from collections import Counter
    print(Counter((f["jornada"], f["estado"]) for f in filas))
