r"""C3 (H15) etapa 2, diagnóstico POSTERIOR (no decide): ¿qué nube negra usa VOLCAT en su εtot(11)?

Despeja R_cld de la εtot que publica VOLCAT, R_cld = R_clr + (R_obs - R_clr)/ε, con R_clr de geocatRTM, y la
pasa a BT; la compara con la temperatura de tropopausa del GFS del paquete (la que usó nuestro nivel B) y con la
nada más del GFS (sólo la tropopausa). Píxeles con ε entre 0,3 y 0,9
(donde el despeje es estable). Cuadros 1 a 5.
"""
import os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lut_volcat as LV  # noqa: E402
import etapa2_validar as E  # noqa: E402

gfs = dict(np.load(os.path.join(E.ML, "gfs_ttropo.npz")))
TB, TT, CH = [], [], []
for h in E.ELIGE:
    d = np.load(os.path.join(E.ML, f"ml_{h}.npz"))
    g = lambda k: d[k].astype(float).ravel()  # noqa: E731
    k = 13
    f = lambda bt: LV.planck_rad(bt, d["fk1_planck"][k], d["fk2_planck"][k], d["bc1_planck"][k], d["bc2_planck"][k])  # noqa: E731
    ro, rc = f(g("geocatL1__channel_14_brightness_temperature")), f(g("geocatRTM__channel_14_brightness_temperature_clear"))
    e = g("geocatDIAGS1__cloud_emissivity_ch14_tot")
    rcld = rc + (ro - rc) / e
    teff = d["fk2_planck"][k] / np.log1p(d["fk1_planck"][k] / rcld)
    tb = (teff - d["bc1_planck"][k]) / d["bc2_planck"][k]
    hh = int(h[:2]) + int(h[2:4]) / 60.0; w = (hh - 6) / 6
    iy, ix = g("geocatRTM__nwp_y_index"), g("geocatRTM__nwp_x_index")
    ok = np.isfinite(iy) & np.isfinite(ix) & (e > 0.3) & (e < 0.9)
    tt = (1 - w) * gfs["gfs.22112718_F012.hdf"][iy[ok].astype(int), ix[ok].astype(int)] + \
        w * gfs["gfs.22112800_F012.hdf"][iy[ok].astype(int), ix[ok].astype(int)]
    TB.append(tb[ok]); TT.append(tt)
tb, tt = np.concatenate(TB), np.concatenate(TT)
dd = tb - tt
print("pixeles", len(tb), " con R_cld despejada <= 0 (BT indefinida):", int(np.sum(~np.isfinite(tb))))
print("BT de la nube negra de VOLCAT: p5/50/95", np.nanpercentile(tb, [5, 50, 95]).round(2))
print("T tropopausa GFS:               p5/50/95", np.percentile(tt, [5, 50, 95]).round(2))
print("diferencia (VOLCAT - tropopausa): p5/50/95", np.nanpercentile(dd, [5, 50, 95]).round(2))
