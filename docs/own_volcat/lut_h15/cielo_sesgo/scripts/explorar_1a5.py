r"""Cielo despejado de VOLCAT (H15 nivel B). EXPLORACIÓN en los cuadros 1 a 5 (no decide).

¿La diferencia entre nuestro εtot(11) y el de VOLCAT se comporta como un error del cielo despejado
(proporcional a 1-ε, domina en nube tenue) o de la nube negra de referencia (proporcional a ε, domina en
nube espesa)? Y, separando por régimen: cielo despejado implícito de VOLCAT en nube tenue (suponiendo nube negra
= tropopausa GFS) y nube negra implícita en nube espesa (suponiendo cielo despejado = geocatRTM).
"""
import os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "scripts"))
import lut_volcat as LV  # noqa: E402
import etapa2_validar as E  # noqa: E402

gfs = dict(np.load(os.path.join(E.ML, "gfs_ttropo.npz")))


def bt_de_rad(r, d, ch):
    k = ch - 1
    with np.errstate(all="ignore"):
        teff = d["fk2_planck"][k] / np.log1p(d["fk1_planck"][k] / r)
    return (teff - d["bc1_planck"][k]) / d["bc2_planck"][k]


def ttropo(h, d):
    g = lambda k: d[k].astype(float).ravel()  # noqa: E731
    hh = int(h[:2]) + int(h[2:4]) / 60.0; w = (hh - 6) / 6
    iy, ix = g("geocatRTM__nwp_y_index"), g("geocatRTM__nwp_x_index")
    ok = np.isfinite(iy) & np.isfinite(ix) & (iy >= 0)
    tt = np.full(iy.shape, np.nan)
    tt[ok] = (1 - w) * gfs["gfs.22112718_F012.hdf"][iy[ok].astype(int), ix[ok].astype(int)] + \
        w * gfs["gfs.22112800_F012.hdf"][iy[ok].astype(int), ix[ok].astype(int)]
    return tt


R = {k: [] for k in ("ev", "eo", "dclr14", "dclr15", "dclr10", "tcld", "tt", "btclr", "bto", "agua")}
for h in E.ELIGE:
    d = np.load(os.path.join(E.ML, f"ml_{h}.npz"))
    g = lambda k: d[k].astype(float).ravel()  # noqa: E731
    tt = ttropo(h, d)
    ev = g("geocatDIAGS1__cloud_emissivity_ch14_tot")
    b12 = g("geocatDIAGS1__cloud_beta_1112_tot"); b73 = g("geocatDIAGS1__cloud_beta_7311_tot")
    with np.errstate(all="ignore"):
        ev15 = 1 - (1 - ev) ** b12
        ev10 = 1 - (1 - ev) ** b73
    out = {}
    for ch, e in ((14, ev), (15, ev15), (10, ev10)):
        ro = E.rad(d, g(f"geocatL1__channel_{ch}_brightness_temperature"), ch)
        rc = E.rad(d, g(f"geocatRTM__channel_{ch}_brightness_temperature_clear"), ch)
        rb = E.rad(d, tt, ch)
        with np.errstate(all="ignore"):
            rclr_v = (ro - e * rb) / (1 - e)
        out[ch] = bt_de_rad(rclr_v, d, ch) - g(f"geocatRTM__channel_{ch}_brightness_temperature_clear")
        if ch == 14:
            eo = LV.emisividad(ro, rc, rb)
            with np.errstate(all="ignore"):
                tcld = bt_de_rad(rc + (ro - rc) / e, d, 14)
    c = np.load(os.path.join(E.C2B, f"c2b_{h}.npz"))
    sfc = c["geocatRTM__channel_14_surface_emissivity"].astype(float).ravel()
    vals, cnt = np.unique(np.round(sfc[np.isfinite(sfc)], 4), return_counts=True)
    R["agua"].append(np.isclose(sfc, vals[np.argmax(cnt)], atol=1e-4))
    R["ev"].append(ev); R["eo"].append(eo); R["dclr14"].append(out[14]); R["dclr15"].append(out[15])
    R["dclr10"].append(out[10]); R["tcld"].append(tcld); R["tt"].append(tt)
    R["btclr"].append(g("geocatRTM__channel_14_brightness_temperature_clear"))
    R["bto"].append(g("geocatL1__channel_14_brightness_temperature"))
R = {k: np.concatenate(v) for k, v in R.items()}
ev, eo = R["ev"], R["eo"]
ok = np.isfinite(ev) & np.isfinite(eo) & (ev > -1) & (ev < 2)
print("pixeles con eps VOLCAT valido:", ok.sum(), " agua:", R["agua"][ok].mean().round(4))
print("eps VOLCAT p1/5/50/95/99:", np.percentile(ev[ok], [1, 5, 50, 95, 99]).round(3))
print("\nDelta eps (nuestro - VOLCAT) por tramo de eps VOLCAT:")
for lo, hi in ((-1, 0), (0, .05), (.05, .1), (.1, .2), (.2, .3), (.3, .4), (.4, .5), (.5, .6), (.6, .7), (.7, .8), (.8, .9), (.9, .95), (.95, 1.0), (1.0, 2)):
    s = ok & (ev >= lo) & (ev < hi)
    if s.sum() < 20:
        continue
    dd = eo[s] - ev[s]
    print(f"  [{lo:5.2f},{hi:5.2f}) n={s.sum():7d}  med={np.median(dd):+.4f}  p5={np.percentile(dd,5):+.4f} p95={np.percentile(dd,95):+.4f}  med/(1-e)={np.median(dd/(1-ev[s])):+.4f}  med/e={np.median(dd/np.where(ev[s]!=0,ev[s],np.nan)):+.4f}")
print("\nCielo despejado implícito de VOLCAT (nube negra = tropopausa) menos geocatRTM, nube tenue 0.03<=eps<=0.2:")
s = ok & (ev >= 0.03) & (ev <= 0.2)
for ch in (14, 15, 10):
    x = R[f"dclr{ch}"][s]; x = x[np.isfinite(x)]
    print(f"  C{ch}: n={len(x)} p5/25/50/75/95 =", np.percentile(x, [5, 25, 50, 75, 95]).round(2))
print("\nNube negra implícita (cielo = geocatRTM) menos tropopausa, nube espesa 0.85<=eps<=0.98:")
s = ok & (ev >= 0.85) & (ev <= 0.98)
x = (R["tcld"] - R["tt"])[s]; nf = np.sum(~np.isfinite(x)); x = x[np.isfinite(x)]
print(f"  n={len(x)} sin solucion={nf}  p5/25/50/75/95 =", np.percentile(x, [5, 25, 50, 75, 95]).round(2))
print("  T tropopausa p5/50/95:", np.percentile(R["tt"][s], [5, 50, 95]).round(2), " BT11 obs p5/50/95:", np.percentile(R["bto"][s], [5, 50, 95]).round(2))
# píxeles con eps VOLCAT <= 0 ó muy chico: ¿obs más tibio que el cielo despejado?
s = ok & (np.abs(ev) < 0.01)
print("\n|eps VOLCAT|<0.01: n=", s.sum(), " BT11obs - BTclr p5/50/95:", np.percentile((R["bto"] - R["btclr"])[s], [5, 50, 95]).round(2))
s = np.isfinite(R["bto"]) & np.isfinite(R["btclr"]) & ~ok
print("eps VOLCAT indefinido: n=", s.sum(), " BT11obs - BTclr p5/50/95:", np.percentile((R["bto"] - R["btclr"])[s], [5, 50, 95]).round(2))
