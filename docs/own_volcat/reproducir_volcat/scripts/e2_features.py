"""Etapa 2: variables SECO por pixel en el disco de 40 km del crater, para cada escena con etiqueta.

Uso: python e2_features.py [n_procesos]  -> <TRABAJO>/feat_e2/<YYYYmmdd_HHMM>.npz (reanudable)

Mismas formulas que H11 (h11_analisis.py: eps_tot, beta_tot, beta_opaque, prefiltros de SECO Parte 1, A5),
con R_clr y R_cld interpolados desde la rejilla de rt_e2.py. Etiqueta VOLCAT por pixel desde el PNG
(huella_png.py): ceniza VOLCAT en la grilla ABI. Sin canales solares ni 3,9 um (declarado en el criterio).
"""
import os, sys
import numpy as np
from multiprocessing import Pool
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h11 as C  # noqa: E402
import rt_e2 as E  # noqa: E402
import huella_png as HP  # noqa: E402
import h11_analisis as A  # noqa: E402

FEAT = os.path.join(C.TRABAJO, "feat_e2"); os.makedirs(FEAT, exist_ok=True)
PNGDIRS = [os.path.join(C.B73, "png_new"), os.path.join(C.TRABAJO, "png_e2")]
I73, I85, I11, I12 = 0, 1, 2, 3


def png_de(dt):
    r = C._INV.get(dt)
    if r is None:
        return None
    for d in PNGDIRS:
        p = os.path.join(d, r["fn"])
        if os.path.exists(p):
            return p
    return None


def etiqueta(dt, tipo):
    """Ceniza VOLCAT en la grilla ABI. Positivos: del PNG o, si no esta, de huellas_b73/h3 (<= 50 km).
    Negativos y manto: el inventario ya dice que no hay objeto a <= 50 km (n50 = 0) o que es manto."""
    kk = C.k(dt)
    p = png_de(dt)
    if p is not None:
        _, ash, _ = HP.huella(p)
        return ash, "png"
    if "a_" + kk in C._HUB:
        return C._HUB["a_" + kk].astype(bool), "huellas_b73"
    if kk in C._HU3:
        return C._HU3[kk].astype(bool), "huellas_h3"
    if tipo == "neg":
        return np.zeros(C.LAT.shape, bool), "inventario_n50_0"
    return None, "sin_etiqueta"


def una(args):
    dt, tipo = args
    out = os.path.join(FEAT, C.k(dt) + ".npz")
    if os.path.exists(out):
        return out, "ya"
    g = os.path.join(E.RTE2, C.k(dt) + ".npz")
    if not os.path.exists(g):
        return out, "sin_rt"
    ash, fuente = etiqueta(dt, tipo)
    if ash is None:
        return out, "sin_etiqueta"
    s = E.load(dt); w = np.load(g)
    ys, xs = np.nonzero(E.REG)
    rclr, rcld = E.interp(w, ys, xs)
    # tropopausa y altura de superficie del GFS por pixel (interpolacion directa, barata)
    g2 = dict(np.load(C.path_gfs(dt)))
    from rt_niveles import _i2
    la, lo = C.LAT[ys, xs], C.LON[ys, xs]
    ptropo = _i2(g2, g2["ptropo"], la, lo); zsfc = _i2(g2, g2["zsfc"], la, lo)
    robs = np.stack([s["rad"][b][ys, xs] for b in C.BANDS], 1)
    btobs = np.stack([s[b][ys, xs] for b in C.BANDS], 1)
    btclr = np.stack([C.rt.bt_de_rad(rclr[:, j], s["co"][b]) for j, b in enumerate(C.BANDS)], 1)
    n = len(ys)
    F = {k: np.full(n, np.nan) for k in ("e11", "e12", "e85", "e73", "bt12", "bt85", "bt73", "bo12", "bo85")}
    for i in range(n):
        if np.isfinite(rcld[i][:, 0]).sum() < 2:
            continue
        rc = A.cld_en(rcld[i], np.log(ptropo[i]))
        e = A.eps(robs[i], rclr[i], rc)
        F["e11"][i], F["e12"][i], F["e85"][i], F["e73"][i] = e[I11], e[I12], e[I85], e[I73]
        F["bt12"][i] = A.beta(e[I12], e[I11]); F["bt85"][i] = A.beta(e[I85], e[I11]); F["bt73"][i] = A.beta(e[I73], e[I11])
        F["bo12"][i] = A.beta_opaco(robs[i], rclr[i], rcld[i], ptropo[i], I12)
        F["bo85"][i] = A.beta_opaco(robs[i], rclr[i], rcld[i], ptropo[i], I85)
    btd = btobs[:, I11] - btobs[:, I12]; btd_bias = (btclr[:, I11] - btclr[:, I12]) - btd
    bt11 = s[14]
    sd = np.sqrt(np.maximum(ndimage.uniform_filter(bt11 ** 2, 3) - ndimage.uniform_filter(bt11, 3) ** 2, 0))[ys, xs]
    e11, b12, bo12 = F["e11"], F["bt12"], F["bo12"]
    with np.errstate(invalid="ignore"):
        pre = np.isfinite(b12) & (e11 >= 0.02) & (b12 <= 1.05)
        pre &= np.where(e11 >= 0.5, btd < -1.19 * e11 + 1.14, True)
        pre &= np.where(e11 < 0.5, btd_bias > -0.70 * e11 + 0.03, True)
        pre &= np.where(btd > 0, np.isfinite(bo12) & (bo12 < 1.36), True)
        a5 = (F["bt85"] > 1.5) & (F["bo85"] > 2.5) & (F["bt73"] > 1.0) & (e11 > 0.01)
    tmp = out + ".tmp.npz"
    np.savez_compressed(tmp, ys=ys, xs=xs, ash=ash[ys, xs], dist=HP.DIST[ys, xs], tipo=tipo, fuente=fuente,
                        sza=C.sza(dt), btclr11=btclr[:, I11], bt11=btobs[:, I11], btd=btd, btd_bias=btd_bias,
                        btd85_12=btobs[:, I85] - btobs[:, I12], btsd=sd, pre=pre, a5=a5, zsfc=zsfc, **F)
    os.replace(tmp, out)
    return out, f"{tipo} {fuente} {n} px"


if __name__ == "__main__":
    npr = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    L = E.lista_escenas()
    with Pool(npr) as pool:
        for out, msg in pool.imap_unordered(una, L):
            if msg != "ya":
                print(os.path.basename(out), msg, flush=True)
