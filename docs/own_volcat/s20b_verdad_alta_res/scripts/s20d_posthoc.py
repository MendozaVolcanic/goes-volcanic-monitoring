r"""S20d, controles POST HOC (escritos despues de ver el resultado de la prueba 2; no cambian el veredicto).

Lo que se vio: con la mascara erosionada 3 celdas (decide) T2 = -0,09 K, pero con erosion 2 da -0,85 K, y la BTD
cruda de la pluma (-1,94 K) queda 1,56 K bajo la mediana del control. La pregunta es por que el pareo por BT10 se
come esa diferencia en el nucleo de la pluma y no en su borde.

Hipotesis a mirar (las dos dejan T2 cerca de cero en el nucleo):
  (1) Control contaminado: la mascara solo ve la parte de la pluma que la regla de reflectancia marca. Las celdas
      frias del control podrian ser pluma no marcada (franja translucida al OSO, entre 3 y 9 km), y entonces el
      nucleo se compara con pluma.
  (2) Superficie: en la nieve fria (sombra, pendiente fuerte) la BTD es baja por si misma, y el nucleo de la pluma, al
      enfriarse 3 K, se compara con esa nieve.
  Las separa el dia sin pluma: si las celdas control que parean con el nucleo tienen BTD baja el 25-10 y normal el
  17-10, son pluma; si la tienen baja los dos dias, es la superficie.

(a) T1 y T2 por capa de la mascara (borde a nucleo).
(b) Donde estan las celdas control que parean con el nucleo, y su BTD el 25-10 y el 17-10.
(c) T2 con el control sin el sector de la pluma (azimut 200 a 290 grados, 2 a 12 km del crater).
(d) Curva BTD contra BT10 del control a la cota del nucleo, los dos dias.
(f) Landsat: area de nieve con BTD 1 K o mas bajo la mediana del control, en el sector de la pluma y fuera de el,
    los dos dias (cuanto mas ancha que la mascara es la mancha de BTD baja).
(e) ECOSTRESS 25-10 y 17-10: area de las regiones con BTD pareada < -1 K por sector de 30 grados (descriptivo).
Figuras: figuras/s20d_landsat_btd.png y figuras/s20d_ecostress_btd_pareada.png.

Uso: python -I s20d_posthoc.py
"""
import json
import os
import sys

import numpy as np
from rasterio.enums import Resampling
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s20b_comun as S  # noqa: E402
import s20d_ventana_partida as V  # noqa: E402

RES = os.path.join(os.path.dirname(AQUI), "resultados")
REF = os.path.join(V.DESC, "HLSL30_ref", "HLS.L30.T19HBV.2026290T143436.v2.0", "HLS.L30.T19HBV.2026290T143436.v2.0.{}.tif")
SECTOR = (200.0, 290.0, 2.0, 12.0)


def leer(fmt):
    a = S.leer(fmt.format("B10"), escala=0.01, suma=273.15, rs=Resampling.nearest, nodata=-9999)
    b = S.leer(fmt.format("B11"), escala=0.01, suma=273.15, rs=Resampling.nearest, nodata=-9999)
    return a, b


def main():
    pl, _, nieve, disco, dem = V.geom_landsat()
    d = S.hav(S.GLAT, S.GLON, *S.CRATER)
    az = np.degrees(np.arctan2(S.GX - S.CX, S.GY - S.CY)) % 360
    ev = leer(V.HLS)
    rf = leer(REF)
    ok = np.isfinite(ev[0]) & np.isfinite(ev[1]) & np.isfinite(rf[0]) & np.isfinite(rf[1]) & np.isfinite(dem)
    dt_real = ndimage.distance_transform_edt(~pl) * 30.0
    ctrl = ok & disco & nieve & (dt_real > V.EXCL_CTRL)
    out = {"nota": "POST HOC: escrito despues de ver el resultado; no cambia el veredicto"}

    # (a) por capa
    capas = {}
    prev = pl.copy()
    for e in range(1, 6):
        cur = ndimage.binary_erosion(pl, iterations=e)
        capas[f"erosion_{e - 1}_a_{e}"] = prev & ~cur
        prev = cur
    capas["nucleo_erosion_5"] = prev
    par = {k: V.Pareo(x[0], x[0] - x[1], dem, ctrl) for k, x in (("ev", ev), ("rf", rf))}
    A = {}
    for k, m in capas.items():
        idx = np.nonzero(m & ok)
        fila = {"celdas": int(len(idx[0]))}
        for dia, x in (("25-10", ev), ("17-10", rf)):
            btd = (x[0] - x[1])[idx]
            pm = par["ev" if dia == "25-10" else "rf"].valor(x[0][idx], dem[idx])
            fila[dia] = {"BT10_med": V.rnd(float(np.median(x[0][idx]))), "BTD_cruda_med": V.rnd(float(np.median(btd))),
                         "T2_capa": V.rnd(float(np.nanmedian(btd - pm)))}
        A[k] = fila
        print("(a)", k, json.dumps(fila, ensure_ascii=False), flush=True)
    out["a_por_capa"] = A

    # (b) controles que parean con el nucleo (erosion 3)
    nuc = ndimage.binary_erosion(pl, iterations=3) & ok
    bt_n, z_n = ev[0][nuc], dem[nuc]
    cr = np.nonzero(ctrl)
    bt_c, z_c = ev[0][cr], dem[cr]
    usados = np.zeros(len(bt_c), bool)
    for b, z in zip(bt_n, z_n):
        usados |= (np.abs(bt_c - b) <= V.DBT) & (np.abs(z_c - z) <= V.DZ)
    ui = (cr[0][usados], cr[1][usados])
    en_sector = (az[ui] >= SECTOR[0]) & (az[ui] <= SECTOR[1]) & (d[ui] >= SECTOR[2]) & (d[ui] <= SECTOR[3])
    B = {"celdas_control_usadas": int(usados.sum()),
         "frac_en_sector_pluma": V.pfr(en_sector),
         "frac_del_control_total_en_sector": V.pfr(((az[cr] >= SECTOR[0]) & (az[cr] <= SECTOR[1]) & (d[cr] >= SECTOR[2])
                                                   & (d[cr] <= SECTOR[3]))),
         "dist_a_mascara_km_p10_p50_p90": V.rnd(np.percentile(dt_real[ui] / 1000, [10, 50, 90])),
         "BTD_usadas_25-10_med": V.rnd(float(np.median((ev[0] - ev[1])[ui]))),
         "BTD_usadas_17-10_med": V.rnd(float(np.median((rf[0] - rf[1])[ui]))),
         "BTD_control_todo_25-10_med": V.rnd(float(np.median((ev[0] - ev[1])[cr]))),
         "BTD_control_todo_17-10_med": V.rnd(float(np.median((rf[0] - rf[1])[cr]))),
         "BT10_usadas_17-10_menos_control_17-10": V.rnd(float(np.median(rf[0][ui]) - np.median(rf[0][cr])))}
    for nom, sel in (("en_sector", en_sector), ("fuera_sector", ~en_sector)):
        ii = (ui[0][sel], ui[1][sel])
        if len(ii[0]):
            B[f"{nom}_celdas"] = int(len(ii[0]))
            B[f"{nom}_BTD_25-10_med"] = V.rnd(float(np.median((ev[0] - ev[1])[ii])))
            B[f"{nom}_BTD_17-10_med"] = V.rnd(float(np.median((rf[0] - rf[1])[ii])))
    print("(b)", json.dumps(B, ensure_ascii=False), flush=True)
    out["b_pares_del_nucleo"] = B

    # (c) T2 sin el sector de la pluma en el control
    sect = (az >= SECTOR[0]) & (az <= SECTOR[1]) & (d >= SECTOR[2]) & (d <= SECTOR[3])
    nieve_c = nieve & ~sect
    C = {}
    for e in (3, 2):
        u = ndimage.binary_erosion(pl, iterations=e)
        r, _, _, _ = V.prueba(ev[0], ev[1], dem, ok, u, disco, nieve_c, 30.0, 10, 1000.0, pl)
        r2, _, _, _ = V.prueba(rf[0], rf[1], dem, ok, u, disco, nieve_c, 30.0, 10, 1000.0, pl)
        C[f"erosion_{e}"] = {"25-10": {k: r[k] for k in ("T1_K", "T2_K", "celdas_T2", "corrimientos", "p_bajo_T1",
                                                          "p_bajo_T2", "nulo_T2_p5_p50_p95")},
                             "17-10": {k: r2[k] for k in ("T1_K", "T2_K", "celdas_T2", "corrimientos", "p_bajo_T2")}}
        print("(c)", e, json.dumps(C[f"erosion_{e}"], ensure_ascii=False), flush=True)
    out["c_control_sin_sector"] = C

    # (d) curva BTD contra BT10 en el control a la cota del nucleo (mediana +-150 m)
    zc = float(np.median(z_n))
    selz = ctrl & (np.abs(dem - zc) <= V.DZ)
    Dd = {"cota_nucleo_m": round(zc)}
    for dia, x in (("25-10", ev), ("17-10", rf)):
        filas = []
        for lo in np.arange(262.0, 286.0, 2.0):
            m = selz & (x[0] >= lo) & (x[0] < lo + 2)
            ms = m & sect
            if m.sum() >= 50:
                filas.append([lo + 1, int(m.sum()), V.rnd(float(np.median((x[0] - x[1])[m]))),
                              V.pfr(ms[m]) if m.any() else None])
        Dd[dia] = filas
        print("(d)", dia, "[BT10 centro, celdas, BTD mediana, fraccion en sector]", filas, flush=True)
    Dd["nucleo_BT10_p10_p50_p90"] = V.rnd(np.percentile(bt_n, [10, 50, 90]))
    out["d_curva_btd_bt10"] = Dd
    F = {}
    zona = ok & disco & nieve
    for dia, x in (("25-10", ev), ("17-10", rf)):
        btd = x[0] - x[1]
        baja = zona & (btd - np.median(btd[ctrl]) <= -1.0)
        F[dia] = {"km2_en_sector": round(float((baja & sect).sum() * 0.0009), 2),
                  "km2_fuera_sector": round(float((baja & ~sect).sum() * 0.0009), 2),
                  "frac_nieve_sector": V.pfr(baja[zona & sect]), "frac_nieve_fuera": V.pfr(baja[zona & ~sect])}
    F["mascara_reflectancia_km2"] = round(float(pl.sum() * 0.0009), 2)
    print("(f)", json.dumps(F, ensure_ascii=False), flush=True)
    out["f_area_btd_baja"] = F
    out["e_ecostress_sectores"], mapas = ecostress_sectores()
    figuras(ev, rf, pl, nieve, sect, mapas)
    with open(os.path.join(RES, "s20d_posthoc.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)


def ecostress_sectores():
    g = V.eco_grilla("2026-10-25", 27000.0)
    z = V.eco_cota(g)
    disco = (g["dist"] <= 25) & (g["dist"] >= 2)
    E, mapas = {}, {}
    for dia in ("2026-10-25", "2026-10-17"):
        a, b, ok, _ = V.eco_leer(V.ECO[dia], g)
        ctrl = ok & disco & np.isfinite(z)
        par = V.Pareo(a, a - b, z, ctrl)
        bpm = np.full(a.shape, np.nan)
        idx = np.nonzero(ctrl)
        bpm[idx] = (a - b)[idx] - par.valor(a[idx], z[idx])
        m = ctrl & np.isfinite(bpm) & (bpm < V.BTD_REG)
        lab, n = ndimage.label(m, structure=np.ones((3, 3)))
        cnt = np.bincount(lab.ravel())
        grandes = np.isin(lab, np.nonzero(cnt * 0.0049 >= V.AREA_REG)[0]) & (lab > 0)
        sect = {}
        for s0 in range(0, 360, 30):
            ss = grandes & (g["az"] >= s0) & (g["az"] < s0 + 30)
            sect[f"{s0}-{s0 + 30}"] = round(float(ss.sum() * 0.0049), 2)
        E[dia] = {"km2_por_sector": sect, "celdas_validas_disco": int(ctrl.sum())}
        print("(e)", dia, json.dumps(E[dia], ensure_ascii=False), flush=True)
        mapas[dia] = (bpm, g)
    return E, mapas


def figuras(ev, rf, pl, nieve, sect, mapas):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig_dir = os.path.join(os.path.dirname(AQUI), "figuras")
    c = S.N // 2
    w = 400                                   # 12 km a cada lado
    sl = (slice(c - w, c + w), slice(c - w, c + w))
    ext = [-12, 12, -12, 12]
    fig, ax = plt.subplots(2, 2, figsize=(11, 10), constrained_layout=True)
    for j, (dia, x) in enumerate((("25-10 14:34 (Landsat 8)", ev), ("17-10 14:34 (Landsat 9, sin pluma)", rf))):
        im = ax[0, j].imshow(x[0][sl], extent=ext, cmap="magma", vmin=262, vmax=290)
        plt.colorbar(im, ax=ax[0, j], label="BT10 (K)")
        im = ax[1, j].imshow((x[0] - x[1])[sl], extent=ext, cmap="RdBu", vmin=-3, vmax=3)
        plt.colorbar(im, ax=ax[1, j], label="BT10 - BT11 (K)")
        ax[0, j].set_title(f"{dia}: BT 10,9 um")
        ax[1, j].set_title(f"{dia}: BTD 10,9 - 12,0 um")
        for a in ax[:, j]:
            a.contour(pl[sl][::-1], levels=[0.5], colors="lime", linewidths=0.8, extent=ext)
            a.contour(sect[sl][::-1], levels=[0.5], colors="k", linewidths=0.6, linestyles="--", extent=ext)
            a.plot(0, 0, "^", mfc="none", mec="w", ms=9)
            a.set_xlabel("km al E del crater")
            a.set_ylabel("km al N")
    fig.suptitle("Nevados de Chillan, HLS L30: verde = mascara de pluma (reflectancia); trazos = sector excluido en (c)")
    fig.savefig(os.path.join(fig_dir, "s20d_landsat_btd.png"), dpi=100)
    plt.close(fig)
    fig, ax = plt.subplots(1, 2, figsize=(13, 6), constrained_layout=True)
    for j, (dia, tit) in enumerate((("2026-10-25", "25-10 17:35"), ("2026-10-17", "17-10 20:42 (referencia)"))):
        bpm, g = mapas[dia]
        e = [(g["X"][0, 0] - g["x0"]) / 1000, (g["X"][0, -1] - g["x0"]) / 1000,
             (g["Y"][-1, 0] - g["y0"]) / 1000, (g["Y"][0, 0] - g["y0"]) / 1000]
        im = ax[j].imshow(bpm, extent=e, cmap="RdBu", vmin=-2, vmax=2)
        ax[j].plot(0, 0, "^", mfc="none", mec="k", ms=9)
        for r in (2, 25):
            t = np.linspace(0, 2 * np.pi, 200)
            ax[j].plot(r * np.sin(t), r * np.cos(t), "k:", lw=0.6)
        ax[j].set_title(f"ECOSTRESS {tit}: BTD pareada 10,5 - 12,0 um")
        ax[j].set_xlabel("km al E del crater")
        ax[j].set_ylabel("km al N")
        plt.colorbar(im, ax=ax[j], label="K")
    fig.savefig(os.path.join(fig_dir, "s20d_ecostress_btd_pareada.png"), dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    main()
