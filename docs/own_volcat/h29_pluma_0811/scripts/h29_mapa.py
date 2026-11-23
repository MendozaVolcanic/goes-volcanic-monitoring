r"""H29, POST HOC: mapa de la anomalia de BTD pareada por BT11 en toda la ventana, 08-11 contra dias nulos.

Por que: la serie de tiempo mostro BTD baja en las posiciones lejanas desde 19:20, antes de que VOLCAT ponga pixeles
ahi. Si la anomalia dibuja una franja que sale del crater a favor del viento, apunta a una pluma mas ancha o mas
temprana que la huella publicada; si es un parche sin relacion con el crater, a un fenomeno meteorologico.

Residuo por cuadro: R = BTD - mediana de BTD de los pixeles del mismo cuadro con BT11 a +-0,5 K y cota a +-300 m
(la misma vara que M1, por casillas de 0,5 K y 150 m con vecindad de +-1 y +-2 casillas). Anomalia = media de R en
el tramo horario del 08-11 menos la mediana sobre los dias nulos de la misma media. Sin huella VOLCAT en la figura
del repo (la huella es derivada de SSEC y queda en D:).
Uso: python -I h29_mapa.py
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import h29_comun as C  # noqa: E402
import h29_medir as X  # noqa: E402

TRAMOS = {"antes 15:00-17:00": (15 * 6, 17 * 6), "19:20-21:40": (19 * 6 + 2, 21 * 6 + 5)}
Z = C.ZDEM.ravel()


def residuo(bt, bd):
    ok = np.isfinite(bt) & np.isfinite(bd)
    ib = np.floor(bt / 0.5).astype(int)
    iz = np.floor(Z / 150.0).astype(int)
    R = np.full(bt.shape, np.nan)
    # mediana por vecindad de casillas (BT11 +-1 casilla = +-0,5 K aprox, cota +-2 casillas = +-300 m)
    claves = {}
    for i in np.flatnonzero(ok):
        claves.setdefault((ib[i], iz[i]), []).append(i)
    cache = {}
    for (b, z), idx in claves.items():
        if (b, z) not in cache:
            vec = []
            for db in (-1, 0, 1):
                for dz in (-2, -1, 0, 1, 2):
                    vec += claves.get((b + db, z + dz), [])
            cache[(b, z)] = np.median(bd[vec]) if len(vec) >= 10 else np.nan
        R[idx] = bd[idx] - cache[(b, z)]
    return R


def media_tramo(M, d, s0, s1):
    acc = []
    for s in range(s0, s1 + 1):
        acc.append(residuo(M.bt11[d, s].astype(float), M.btd[d, s].astype(float)))
    acc = np.array(acc)
    with np.errstate(invalid="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            return np.nanmean(acc, 0)


def main():
    r14, r15, acm, co14, co15 = X.H24.cargar()
    M = X.Medidor(r14, r15, co14, co15, None, [])
    d0 = X.DIA["2026-11-08"]
    out, mapas = {}, {}
    for nombre, (s0, s1) in TRAMOS.items():
        ev = media_tramo(M, d0, s0, s1)
        nu = np.array([media_tramo(M, d, s0, s1) for d in X.NULOS])
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            med = np.nanmedian(nu, 0)
            q05 = np.nanpercentile(nu, 5, 0)
        an = (ev - med).reshape(C.NY, C.NX)
        bajo = (ev < q05).reshape(C.NY, C.NX)
        mapas[nombre] = an
        # resumen por sector respecto del crater: azimut y distancia
        x = (C.LON - C.CRATER[1]) * np.cos(np.radians(C.CRATER[0])) * 111.32
        y = (C.LAT - C.CRATER[0]) * 110.57
        az = np.degrees(np.arctan2(x, y)) % 360
        r = np.hypot(x, y)
        sect = {}
        for sn, (a0, a1) in {"N": (315, 45), "E": (45, 100), "SE": (100, 170), "S-SO": (170, 260), "O-NO": (260, 315)}.items():
            m = ((az >= a0) | (az < a1)) if a0 > a1 else ((az >= a0) & (az < a1))
            for rn, (r0, r1) in {"10-30km": (10, 30), "30-60km": (30, 60)}.items():
                mm = m & (r >= r0) & (r < r1) & np.isfinite(an)
                sect[f"{sn}_{rn}"] = {"anomalia_media_K": round(float(np.mean(an[mm])), 3) if mm.any() else None,
                                      "frac_bajo_p5_nulo": round(float(np.mean(bajo[mm])), 3) if mm.any() else None,
                                      "n": int(mm.sum())}
        out[nombre] = sect
        print(nombre, json.dumps(sect, ensure_ascii=False), flush=True)
    json.dump(out, open(os.path.join(C.RES, "mapa_sectores.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    np.savez_compressed(os.path.join(C.TRABAJO, "mapa_anomalia.npz"), **{k.replace(" ", "_"): v for k, v in mapas.items()})
    fig, ax = plt.subplots(1, 2, figsize=(11, 5), constrained_layout=True)
    ext = [C.LON.min(), C.LON.max(), C.LAT.min(), C.LAT.max()]
    for a, (nombre, an) in zip(ax, mapas.items()):
        im = a.imshow(an, extent=ext, origin="upper", cmap="RdBu", vmin=-0.6, vmax=0.6, aspect=1 / np.cos(np.radians(-36.9)))
        a.plot(C.CRATER[1], C.CRATER[0], "^", mfc="none", mec="k", ms=9, mew=1.5)
        for rr in (30, 60):
            t = np.linspace(0, 2 * np.pi, 200)
            a.plot(C.CRATER[1] + rr / (111.32 * np.cos(np.radians(C.CRATER[0]))) * np.sin(t),
                   C.CRATER[0] + rr / 110.57 * np.cos(t), "k:", lw=0.7)
        a.set_title(f"08-11, {nombre} UTC")
        a.set_xlabel("longitud")
        a.set_ylabel("latitud")
    fig.colorbar(im, ax=ax, shrink=0.8, label="BTD pareada por BT11 y cota: 08-11 menos mediana de 18 días nulos (K)")
    os.makedirs(os.path.join(os.path.dirname(AQUI), "figuras"), exist_ok=True)
    fig.savefig(os.path.join(os.path.dirname(AQUI), "figuras", "mapa_anomalia_btd.png"), dpi=110)


if __name__ == "__main__":
    main()
