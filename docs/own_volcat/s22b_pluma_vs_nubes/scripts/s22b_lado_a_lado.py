r"""S22b, visualización lado a lado (no decide nada), igual a la de S22a pero con la regla S22b: a la izquierda VOLCAT
tal como lo publica SSEC (PNG de altura recortado a ±0,7° del cráter), a la derecha el detector propio sobre el IR de
11 µm en gris, con el mismo encuadre, frontera y anillos de 10, 25 y 50 km.

Regla de pintado (fija, escrita antes de mirar):
- ROJO lleno: cuando el detector dispara, los 8 píxeles de la cola de la tajada del mínimo (los que dieron Q_k*,
  después de restar la línea base y de borrar nubes y bordes).
- CELESTE translúcido: píxeles con nube dinámica (ACM 2 o 3 donde el píxel no está nublado de costumbre) y su borde
  de 3 × 3, que el detector no usa.
- Texto "no evaluable por nubes" cuando más de la mitad del anillo tiene nube dinámica: ahí el detector se calla.
Funciones de dibujo reusadas de s22a_lado_a_lado.py sin cambios.

Los PNG de VOLCAT son de SSEC (licencia restringida): se leen de D: y los videos quedan fuera del repo.
Uso: python -I s22b_lado_a_lado.py 2026-11-08 [2026-11-14 ...]
"""
import os
import sys
import warnings
from datetime import datetime, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s22b_medir as B  # noqa: E402
M = B.M
sys.path.insert(0, os.path.join(B.OV, "s22a_detector_sectores", "scripts"))
import s22a_mapas as G  # noqa: E402
import s22a_lado_a_lado as L  # noqa: E402

G.PNG_DIRS.append(r"D:\goes_notas\s22\s22b\volcat_png\frames")
SALIDA = r"C:\Users\nmend\Downloads"
TRABAJO = r"D:\goes_notas\s22\s22b\lado_a_lado"
C29 = L.C29


def dibujar(D, dia, s0=72, s1=143):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import imageio.v2 as imageio

    d = B.dia_idx(dia)
    nuevo = d >= B.NDEV
    excl = d if d in D.DEV else None
    U, _ = D.umbral(None if nuevo else excl)
    F, ev = D.disparos(d, U)
    base = D.base(None if nuevo else excl)
    bt = np.load(os.path.join(B.TRAB, "nuevo_bt11.npy"))[d - B.NDEV] if nuevo else np.asarray(D.bt_dev[d])
    rol = ("día nuevo, no mirado al elegir la regla" if nuevo else
           ("desarrollo, día ya mirado (umbral y base sin este día)" if excl is not None else "desarrollo"))
    segs = L.lineas_geo()
    os.makedirs(TRABAJO, exist_ok=True)
    cuadros, n_f, n_v, n_nub = [], 0, 0, 0
    for s in range(s0, s1 + 1):
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.4, 6.9), dpi=100, facecolor="#0b0f17")
        a = L.png_volcat_rgb(dia, s)
        if a is not None:
            sub, ext = L.recorte_volcat(a)
            a1.imshow(sub, extent=ext, interpolation="nearest")
            ash, _ = G.png_volcat(dia, s)
            hay_v = ash is not None and ash.any()
            n_v += int(hay_v)
            tv = "VOLCAT: ceniza (color = altura, km sobre el mar)" if hay_v else "VOLCAT: sin dibujo en este cuadro"
        else:
            a1.set_facecolor("black")
            tv = "VOLCAT: no hay imagen guardada de este cuadro"
        L.adornar(a1, segs)
        a1.set_title("VOLCAT (SSEC), altura de pluma", color="white", fontsize=11)
        a1.text(0.01, -0.05, tv, transform=a1.transAxes, color="#ffb347", fontsize=9)
        b = bt[s].reshape(M.NY, M.NX)
        if np.isfinite(b).any():
            a2.pcolormesh(C29.LON, C29.LAT, b, cmap="gray_r", vmin=210, vmax=320, shading="nearest")
        nd = B.dinamica(D.acm[d, s], D.ESTAT)
        nub = B.borde(nd).reshape(M.NY, M.NX)
        a2.pcolormesh(C29.LON, C29.LAT, np.where(nub, 1.0, np.nan),
                      cmap=matplotlib.colors.ListedColormap(["#5ec8ff"]), vmin=0, vmax=1, shading="nearest", alpha=0.35)
        if F[s]:
            n_f += 1
            idx = np.flatnonzero(M.SEC == D.K[d, s])
            v = (D.mm[d, s] - base[s])[idx]
            o = np.argsort(np.where(np.isfinite(v), v, np.inf))[:M.NCOLA]
            roj = np.zeros(M.NY * M.NX, bool)
            roj[M.AP[idx[o]]] = True
            a2.pcolormesh(C29.LON, C29.LAT, np.where(roj.reshape(M.NY, M.NX), 1.0, np.nan),
                          cmap=matplotlib.colors.ListedColormap(["#ff2a2a"]), vmin=0, vmax=1, shading="nearest")
            a0 = 30 * int(D.K[d, s])
            td, cd = f"DETECTOR: marca pluma hacia {a0}° a {a0 + 30}° (rojo). Sin altura todavía", "#ff5a5a"
        elif not D.GATE[d, s]:
            n_nub += 1
            td, cd = "Detector: no evaluable por nubes (más de la mitad del anillo nublado)", "#5ec8ff"
        elif ev[s]:
            td, cd = "Detector: no marca nada", "white"
        else:
            td, cd = "Detector: sin evaluar (datos o umbral faltantes)", "white"
        x, y = L.anillo(40)
        a2.plot(x, y, ":", color="#ff9f43", lw=0.8)
        L.adornar(a2, segs)
        a2.set_title("Detector propio GOES-19 S22b (11 − 12 µm, sin nubes), 4 a 40 km", color="white", fontsize=11)
        a2.text(0.01, -0.05, td, transform=a2.transAxes, color=cd, fontsize=9)
        hl = datetime.strptime(dia, "%Y-%m-%d") + timedelta(minutes=10 * s) - timedelta(hours=3)
        fig.suptitle(f"Nevados de Chillán ±0,7°   {dia[8:10]}-{dia[5:7]}-{dia[:4]}   {M.hhmm(s)} UTC · "
                     f"{hl:%H:%M} hora de Chile (UTC-3)", color="white", fontsize=13)
        fig.text(0.5, 0.01, f"Día: {rol}. Celeste: nube y borde que el detector no usa. Prueba en curso, no operativa.",
                 color="#9aa4b2", fontsize=8.5, ha="center")
        fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.08, wspace=0.03)
        fn = os.path.join(TRABAJO, f"{dia}_{s:03d}.png")
        fig.savefig(fn, facecolor=fig.get_facecolor())
        plt.close(fig)
        cuadros.append(imageio.imread(fn))
    out = os.path.join(SALIDA, f"s22b_lado_a_lado_volcat_vs_detector_chillan_{dia}_10min.mp4")
    imageio.mimsave(out, cuadros, fps=2, macro_block_size=1)
    print(f"{dia}: {len(cuadros)} cuadros, detector marca en {n_f}, no evaluable por nubes {n_nub}, "
          f"VOLCAT dibuja en {n_v} -> {out}", flush=True)


if __name__ == "__main__":
    D = B.Datos(con_nuevos=os.path.exists(os.path.join(B.TRAB, "nuevo_m1.npy")))
    for arg in sys.argv[1:]:
        dia, _, rango = arg.partition("@")
        s0, s1 = (72, 143) if not rango else (M.slot(rango.split("-")[0]), M.slot(rango.split("-")[1]))
        dibujar(D, dia, s0, s1)
