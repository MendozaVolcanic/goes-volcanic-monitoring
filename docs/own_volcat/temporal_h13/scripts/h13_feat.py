"""H13: variables de UN cuadro por pixel en el disco de 40 km, para cada scan de las secuencias y controles.

Mismas formulas que la etapa 2 (e2_features.una: eps_tot, beta_tot, beta_opaque, prefiltros SECO 1, A5), con
una sola diferencia declarada en el criterio: R_clr y R_cld (y la tropopausa) se interpolan linealmente en el
tiempo entre las dos horas GFS que encierran el scan, para que el cambio de hora del GFS no aparezca como un
cambio falso entre dos cuadros consecutivos. Las variables temporales se arman despues (h13_analisis.py).

Etiqueta por pixel: cuadros anclados = ceniza VOLCAT (e2_features.etiqueta); cuadros con n50 = 0 = sin
ceniza; el resto (objeto a <= 50 km no anclado, o sin registro) queda con etiqueta -1 (no se usa para
entrenar ni como negativo).
Uso: python h13_feat.py [n_procesos] -> <H13DIR>/feat/<YYYYmmdd_HHMM>.npz (reanudable)
"""
import os, sys
import numpy as np
from multiprocessing import Pool
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h13_comun as H  # noqa: E402
C = H.C
import rt_e2 as E  # noqa: E402
import huella_png as HP  # noqa: E402
import h11_analisis as A  # noqa: E402
import e2_features as EF  # noqa: E402

EF.PNGDIRS = EF.PNGDIRS + [H.PNG13]
I73, I85, I11, I12 = 0, 1, 2, 3
ANC = set(H.anclados())


def bil_nodos(a, ys, xs):
    """Bilineal de un campo de nodos (forma (ny*nx, ...)) a los pixeles, igual que rt_e2.interp."""
    ny, nx = len(E.NODOS_Y), len(E.NODOS_X)
    a = a.reshape((ny, nx) + a.shape[1:])
    fy = (ys - E.Y0) / E.PASO; fx = (xs - E.X0) / E.PASO
    iy = np.clip(np.floor(fy).astype(int), 0, ny - 2); ix = np.clip(np.floor(fx).astype(int), 0, nx - 2)
    wy = (fy - iy); wx = (fx - ix)
    sh = (-1,) + (1,) * (a.ndim - 2)
    w00 = ((1 - wy) * (1 - wx)).reshape(sh); w01 = ((1 - wy) * wx).reshape(sh)
    w10 = (wy * (1 - wx)).reshape(sh); w11 = (wy * wx).reshape(sh)
    return a[iy, ix] * w00 + a[iy, ix + 1] * w01 + a[iy + 1, ix] * w10 + a[iy + 1, ix + 1] * w11


def nodos_t(dt):
    """Campos de nodos interpolados en el tiempo. Devuelve (dict, nota)."""
    h0, h1, w = H.horas_que_encierran(dt)
    f0 = os.path.join(H.RTH, f"gfs_{h0:%Y%m%d%H}.npz"); f1 = os.path.join(H.RTH, f"gfs_{h1:%Y%m%d%H}.npz")
    e0, e1 = os.path.exists(f0), os.path.exists(f1)
    if not e0 and not e1:
        return None, "sin_rt"
    if e0 and e1:
        z0, z1 = np.load(f0), np.load(f1)
        d = {k: (1 - w) * z0[k] + w * z1[k] for k in ("rclr", "rcld", "ptropo", "zsfc")}
        return d, "interp"
    if os.environ.get("H13_FINAL") != "1":
        return None, "espera_rt"           # la otra hora puede estar calculandose todavia
    z = np.load(f0 if e0 else f1)
    return {k: z[k] for k in ("rclr", "rcld", "ptropo", "zsfc")}, "una_hora"


def etiqueta(dt):
    r = C._INV.get(dt)
    if dt in ANC:
        ash, fuente = EF.etiqueta(dt, "pos")
        return (ash.astype(np.int8) if ash is not None else None), fuente
    if r is not None and r["n50"] == 0 and not r["manto"] and r["barra"]:
        return np.zeros(C.LAT.shape, np.int8), "n50_0"
    return np.full(C.LAT.shape, -1, np.int8), "sin_etiqueta"


def una(dt):
    out = os.path.join(H.FEAT13, H.k(dt) + ".npz")
    if os.path.exists(out):
        return out, "ya"
    s = H.load(dt)
    if s is None:
        return out, "sin_l1b"
    nd, nota = nodos_t(dt)
    if nd is None:
        return out, nota
    lab, fuente = etiqueta(dt)
    if lab is None:
        return out, "sin_etiqueta_pos"
    ys, xs = np.nonzero(E.REG)
    rclr = bil_nodos(nd["rclr"], ys, xs); rcld = bil_nodos(nd["rcld"], ys, xs)
    ptropo = bil_nodos(nd["ptropo"], ys, xs); zsfc = bil_nodos(nd["zsfc"], ys, xs)
    robs = np.stack([s["rad"][b][ys, xs] for b in C.BANDS], 1)
    btobs = np.stack([s[b][ys, xs] for b in C.BANDS], 1)
    btclr = np.stack([C.rt.bt_de_rad(rclr[:, j], s["co"][b]) for j, b in enumerate(C.BANDS)], 1)
    n = len(ys)
    F = {kk: np.full(n, np.nan) for kk in ("e11", "e12", "e85", "e73", "bt12", "bt85", "bt73", "bo12", "bo85")}
    for i in range(n):
        if np.isfinite(rcld[i][:, 0]).sum() < 2 or not np.isfinite(robs[i]).all():
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
    np.savez_compressed(tmp, ys=ys, xs=xs, lab=lab[ys, xs], fuente=fuente, nota_rt=nota, dist=HP.DIST[ys, xs],
                        sza=C.sza(dt), btclr11=btclr[:, I11], bt11=btobs[:, I11], btd=btd, btd_bias=btd_bias,
                        btd85_12=btobs[:, I85] - btobs[:, I12], btsd=sd, pre=pre, a5=a5, zsfc=zsfc, **F)
    os.replace(tmp, out)
    return out, f"{fuente} {nota} {n} px"


if __name__ == "__main__":
    npr = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    L = H.scans_necesarios()
    with Pool(npr) as pool:
        for out, msg in pool.imap_unordered(una, L):
            if msg != "ya":
                print(os.path.basename(out), msg, flush=True)
