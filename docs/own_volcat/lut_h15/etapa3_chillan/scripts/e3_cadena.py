r"""H15 etapa 3: aplica la cadena del criterio (criterio_2026-11-21.md, commit 617f531) a huella y controles.

Por cuadro: (1) pareo de controles por BT11 del mismo cuadro (una vez, no depende de la banda); (2) cielo despejado
por cota, nube negra en el punto frío, ε y β de todos los píxeles (vectorizado) para la banda S0, y la distancia a
nube espesa (εtot >= 0,5) que usa S2; (3) para cada banda (S0, S1, S2, T-, T+) la probabilidad IR de VOLCAT en los
píxeles de huella y sus controles, con la variante que decide (V0) y las informativas (V1 + tabla BTD, V2 sin 8,5).

Salidas: E3_DIR\e3_pixeles_completo.csv (con fila y columna; fuera del repo) y resultados/e3_pixeles.csv.gz (una
fila por píxel y banda, sin posiciones; sólo números nuestros y la pertenencia a la huella) y resultados/e3_georef.json (comprobación previa 1).
Uso: python -I e3_cadena.py
"""
import csv
import glob
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np
from scipy import ndimage
from scipy.interpolate import RegularGridInterpolator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e3_comun as K  # noqa: E402
import h13_comun as H  # noqa: E402
import e3_bajar as B  # noqa: E402
import h11_analisis as A  # noqa: E402
import lut_volcat as LV  # noqa: E402
import nt_comun as N  # noqa: E402
import nt_regla as NR  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
C = H.C
NY, NX = C.LAT.shape
BANDAS_ABI = C.BANDS                     # (10, 11, 14, 15): 7,3 / 8,4 / 11,2 / 12,3 µm
I73, I85, I11, I12 = 0, 1, 2, 3
MU = np.cos(np.radians(C.rt.cenit_satelital(C.LAT, C.LON)))
ZDEM = np.load(os.path.join(K.E3DIR, "dem_ventana.npz"))["zdem"]
SEMILLA = 20261121
TOL1, TOL2, NCTRL, SEP = 0.5, 1.0, 5, 4
S2_TRAMOS = [(2, -1.60), (5, -1.50), (10, -1.27), (20, -1.04), (np.inf, -0.86)]
BANDAS = ["S0", "S1", "S2", "Tm5", "Tp5"]
TBTD = [t for t in LV.IR_S1 if t[0] == "EMISS14_TOT_BTD1112_IR"][0]


def inventario():
    z = np.load(os.path.join(K.E3DIR, "inventario.npz"))
    out = {}
    for k in z.files:
        c, v = k.split("__")
        out.setdefault(c, {})[v] = z[k]
    return out


def eventos(cuadros):
    """Evento = tramo de cuadros separados por <= 60 min (da los 4 eventos de H14)."""
    ev, n, prev = {}, 0, None
    for c in cuadros:
        t = datetime.strptime(c, "%Y%m%d_%H%M")
        if prev is not None and t - prev > timedelta(minutes=60):
            n += 1
        ev[c] = n
        prev = t
    return ev


def escena(dt):
    z = np.load(B.path_escena(dt))
    return ({b: z[f"rad{b}"].astype("float64") for b in BANDAS_ABI},
            {b: z[f"bt{b}"].astype("float64") for b in BANDAS_ABI},
            {b: tuple(float(c) for c in z[f"co{b}"]) for b in BANDAS_ABI})


def nodos_t(dt):
    h0, h1, w = H.horas_que_encierran(dt)
    z0 = np.load(os.path.join(K.RT, f"gfs_{h0:%Y%m%d%H}.npz"))
    z1 = np.load(os.path.join(K.RT, f"gfs_{h1:%Y%m%d%H}.npz"))
    d = {k: (1 - w) * z0[k] + w * z1[k] for k in ("rclrk", "rcld", "tcp", "ptropo", "tpwk")}
    d.update(nody=z0["nody"], nodx=z0["nodx"], zk=z0["zk"])
    return d


def a_pixeles(nd):
    """Bilineal de nodos a todos los píxeles y lineal en la cota del modelo de elevación."""
    ny, nx = len(nd["nody"]), len(nd["nodx"])
    yy, xx = np.mgrid[0:NY, 0:NX]
    pts = np.column_stack([yy.ravel(), xx.ravel()])
    f = lambda a: RegularGridInterpolator((nd["nody"], nd["nodx"]), a.reshape((ny, nx) + a.shape[1:]))(pts)  # noqa: E731
    rk, tk = f(nd["rclrk"]), f(nd["tpwk"])                    # (npx, nk, 4), (npx, nk)
    zk = nd["zk"]
    z = np.clip(ZDEM.ravel(), zk[0], zk[-1])
    j = np.clip(np.searchsorted(zk, z) - 1, 0, len(zk) - 2)
    w = (z - zk[j]) / (zk[j + 1] - zk[j])
    ii = np.arange(len(z))
    rclr = rk[ii, j] * (1 - w)[:, None] + rk[ii, j + 1] * w[:, None]
    tpw = tk[ii, j] * (1 - w) + tk[ii, j + 1] * w
    return dict(rclr=rclr.reshape(NY, NX, 4), tpw=tpw.reshape(NY, NX), rcld=f(nd["rcld"]).reshape(NY, NX, -1, 4),
                tcp=f(nd["tcp"]).reshape(NY, NX), ptropo=f(nd["ptropo"]).reshape(NY, NX))


def planck(bt, co):
    return LV.planck_rad(bt, *co)


def campos(rad, bt, co, px, delta11):
    """ε por banda (oblicuos), εtot al nadir, β y entradas de tabla en todos los píxeles. delta11: K (escalar o 2D)."""
    rclr = {b: px["rclr"][..., j] for j, b in enumerate(BANDAS_ABI)}
    bt14c = C.rt.bt_de_rad(rclr[14], co[14]) + delta11
    rclr[14] = planck(bt14c, co[14])
    rcld = {b: planck(px["tcp"], co[b]) for b in BANDAS_ABI}
    e = {b: LV.emisividad(rad[b], rclr[b], rcld[b]) for b in BANDAS_ABI}
    with np.errstate(all="ignore"):
        etot = 1 - (1 - e[14]) ** MU
    b12 = LV.beta(e[15], e[14])
    corr = np.where((etot < 0.25) & (px["tpw"] > 2.5), 0.2, np.where((etot < 0.25) & (px["tpw"] > 1.5), 0.05, 0.0))
    return dict(e=e, eps=etot, b_tot=b12 + corr, b73=LV.beta(e[10], e[14]), b85=LV.beta(e[11], e[14]),
                btd=bt[14] - bt[15], btclr=bt14c, rclr=rclr)


def beta_op(rad, f, px, y, x):
    robs = np.array([rad[b][y, x] for b in BANDAS_ABI])
    rclr = np.array([f["rclr"][b][y, x] for b in BANDAS_ABI])
    rcld = px["rcld"][y, x]
    if np.isfinite(rcld[:, 0]).sum() < 2 or not np.isfinite(robs).all():
        return np.nan, np.nan
    return (A.beta_opaco(robs, rclr, rcld, px["ptropo"][y, x], I12),
            A.beta_opaco(robs, rclr, rcld, px["ptropo"][y, x], I85))


def probabilidades(ent):
    """P de V0 (decide), V1 (+ tabla BTD) y V2 (sin 8,5 µm). P = 0 sin probabilidad definida (criterio, punto 9)."""
    agua = np.zeros(len(ent["eps"]), bool)
    C2 = NR.contribuciones(ent, agua, r2=True)
    c85 = ~((ent["eps"] < 0.1) & (ent["b85"] > 1.05) & (ent["b85"] < 2.0))
    L0 = NR.logit_regla(C2, ent, r1=True, cond85=c85)
    L1 = L0 + N.contrib(ent, agua, TBTD)
    L2 = NR.logit_regla(C2, ent, r1=True, cond85=np.zeros(len(agua), bool))
    with np.errstate(all="ignore"):
        e11 = 1 - (1 - ent["eps"]) ** (1 / ent["mu"])
    valido = np.isfinite(ent["eps"]) & (ent["eps"] >= 0.01) & (e11 < 1) & np.isfinite(ent["b_tot"])
    return [np.where(valido, LV.prob(L), 0.0) for L in (L0, L1, L2)], valido


def parear(bt11, huella, rng):
    """Controles por píxel de huella: mismo cuadro, >= SEP px de la huella, |ΔBT11| <= 0,5 K (si no, 1,0 K)."""
    dist = ndimage.distance_transform_edt(~huella)
    cand = (dist >= SEP) & np.isfinite(bt11)
    cy, cx = np.nonzero(cand)
    cb = bt11[cy, cx]
    out = []
    for y, x in zip(*np.nonzero(huella)):
        if not np.isfinite(bt11[y, x]):
            out.append(((y, x), [], None)); continue
        for tol in (TOL1, TOL2):
            m = np.nonzero(np.abs(cb - bt11[y, x]) <= tol)[0]
            if len(m):
                s = rng.choice(m, size=min(NCTRL, len(m)), replace=False)
                out.append(((y, x), [(cy[i], cx[i]) for i in s], tol)); break
        else:
            out.append(((y, x), [], None))
    return out


def publicar():
    import pandas as pd
    d = pd.read_csv(os.path.join(K.E3DIR, "e3_pixeles_completo.csv"))
    d.drop(columns=["fila", "col"]).to_csv(os.path.join(K.RES, "e3_pixeles.csv.gz"), index=False)


def main():
    inv = inventario()
    cuadros = sorted(inv)
    ev = eventos(cuadros)
    rng = np.random.default_rng(SEMILLA)
    filas, geo = [], []
    for c in cuadros:
        dt = datetime.strptime(c, "%Y%m%d_%H%M")
        rad, bt, co = escena(dt)
        px = a_pixeles(nodos_t(dt))
        hu = np.zeros((NY, NX), bool); hu[inv[c]["wy"], inv[c]["wx"]] = True
        geo.extend((bt[14][inv[c]["wy"], inv[c]["wx"]] - inv[c]["bt11"]).tolist())
        pares = parear(bt[14], hu, rng)
        f0 = campos(rad, bt, co, px, 0.0)
        espesa = np.isfinite(f0["eps"]) & (f0["eps"] >= 0.5)
        dth = ndimage.distance_transform_edt(~espesa) if espesa.any() else np.full((NY, NX), np.inf)
        d2 = np.select([dth < u for u, _ in S2_TRAMOS], [v for _, v in S2_TRAMOS])
        deltas = {"S0": 0.0, "S1": -0.86, "S2": d2, "Tm5": -5.0, "Tp5": 5.0}
        # píxeles a evaluar: huella y controles (con id del píxel de huella al que pertenecen)
        reg = []
        for ih, ((y, x), ctrl, tol) in enumerate(pares):
            reg.append((y, x, "h", ih, tol, len(ctrl)))
            reg.extend((cy, cx, "c", ih, tol, len(ctrl)) for cy, cx in ctrl)
        ys = np.array([r[0] for r in reg]); xs = np.array([r[1] for r in reg])
        for s in BANDAS:
            f = f0 if s == "S0" else campos(rad, bt, co, px, deltas[s])
            bo = np.array([beta_op(rad, f, px, y, x) for y, x in zip(ys, xs)])
            ent = {k: f[k][ys, xs] for k in ("eps", "b_tot", "b73", "b85", "btd", "btclr")}
            ent.update(b_op=bo[:, 0], b85op=bo[:, 1], b_low=np.full(len(ys), np.nan), b_mid=np.full(len(ys), np.nan),
                       mu=MU[ys, xs])
            (p0, p1, p2), val = probabilidades(ent)
            dd = deltas[s] if np.isscalar(deltas[s]) else deltas[s][ys, xs]
            for i, r in enumerate(reg):
                filas.append(dict(cuadro=c, evento=ev[c], banda=s, rol=r[2], id_huella=f"{c}_{r[3]}", tol=r[4],
                                  n_ctrl=r[5], fila=int(r[0]), col=int(r[1]), bt11=round(float(bt[14][r[0], r[1]]), 3),
                                  zdem=round(float(ZDEM[r[0], r[1]]), 0), delta11=round(float(np.broadcast_to(dd, ys.shape)[i]), 2),
                                  eps=round(float(ent["eps"][i]), 5), e11_obl=round(float(f["e"][14][r[0], r[1]]), 5),
                                  b_tot=round(float(ent["b_tot"][i]), 4), b73=round(float(ent["b73"][i]), 4),
                                  b85=round(float(ent["b85"][i]), 4), b_op=round(float(bo[i, 0]), 4),
                                  tpw=round(float(px["tpw"][r[0], r[1]]), 3), valido=int(val[i]),
                                  p_v0=float(p0[i]), p_v1=float(p1[i]), p_v2=float(p2[i])))
        print(c, "ev", ev[c], "huella", int(hu.sum()), "evaluados", len(reg), flush=True)
    # Completo (con fila y columna) sólo fuera del repo: la posición de la huella sale de archivos de acceso
    # restringido. Al repo va sin posiciones y comprimido.
    with open(os.path.join(K.E3DIR, "e3_pixeles_completo.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, fieldnames=list(filas[0]))
        w.writeheader(); w.writerows(filas)
    publicar()
    g = np.array(geo)
    res = {"n": int(np.isfinite(g).sum()), "dif_bt11_mediana_K": round(float(np.nanmedian(g)), 3),
           "dif_abs_mediana_K": round(float(np.nanmedian(np.abs(g))), 3),
           "dif_p5_p95_K": [round(float(np.nanpercentile(g, 5)), 3), round(float(np.nanpercentile(g, 95)), 3)],
           "nota": "BT11 de nuestra L1b (coef. NOAA) menos BT11 del archivo de evento VOLCAT, en los pixeles de huella"}
    json.dump(res, open(os.path.join(K.RES, "e3_georef.json"), "w"), indent=1)
    print("georef", res)


if __name__ == "__main__":
    main()
