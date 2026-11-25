r"""S25a, visualización lado a lado (no decide nada; criterio §6). A la izquierda VOLCAT tal como lo publica SSEC
(PNG de altura recortado a ±0,7° del cráter); a la derecha el IR de 11 µm en gris, mismo encuadre, frontera y anillos
de 10, 25 y 50 km (funciones de s22a_lado_a_lado.py sin cambios), con la zona de 0 a 4 km en línea punteada. Píxeles
llenos, como VOLCAT:
- ROJO: los dos píxeles de la zona que hacen S cuando la regla dispara (dos cuadros seguidos bajo el umbral).
- NARANJO: los mismos dos píxeles cuando S está bajo el umbral en un cuadro suelto (no es disparo).
Lee la tabla por cuadro que escribe `s25a_medir.py medir` (D:\goes_notas\s25\s25a\tabla_2026.csv).

Los PNG de VOLCAT son de SSEC (licencia restringida): se leen de D: y los videos quedan fuera del repo.
Uso: python -I s25a_lado_a_lado.py 2026-11-14 [2026-10-28@15:00-21:00 ...]
"""
import csv
import os
import sys
import warnings
from datetime import datetime, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s25a_medir as Z  # noqa: E402
B, M, C29 = Z.B, Z.M, Z.C29
sys.path.insert(0, os.path.join(Z.OV, "s22a_detector_sectores", "scripts"))
import s22a_mapas as G  # noqa: E402
import s22a_lado_a_lado as L  # noqa: E402

G.PNG_DIRS.append(r"D:\goes_notas\s22\s22b\volcat_png\frames")
G.PNG_DIRS.append(r"D:\goes_notas\s23\volcat_png\Chile_Central_2_km\frames")
SALIDA = r"C:\Users\nmend\Downloads"
TRABAJO = os.path.join(Z.TRAB, "lado_a_lado")


def tabla():
    T = {}
    with open(os.path.join(Z.TRAB, "tabla_2026.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            T[(r["dia"], r["hora"])] = r
    return T


def bt_dia(d):
    if d >= B.NDEV:
        return np.load(os.path.join(B.TRAB, "nuevo_bt11.npy"))[d - B.NDEV]
    return np.load(os.path.join(B.TRAB, "dev_bt11.npy"), mmap_mode="r")[d]


def dibujar(T, dia, s0=72, s1=143):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import imageio.v2 as imageio

    d = B.dia_idx(dia)
    bt = np.asarray(bt_dia(d))
    segs = L.lineas_geo()
    os.makedirs(TRABAJO, exist_ok=True)
    cuadros, n_f, n_v, n_bajo = [], 0, 0, 0
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
        r = T.get((dia, M.hhmm(s)))
        td, cd = "Zona del cráter: sin evaluar (nubes en el anillo, datos o umbral faltantes)", "white"
        if r and r["evaluado"] == "1":
            Sv, Uv = float(r["S"]), float(r["U"])
            marca = None
            if r["F"] == "1":
                marca, n_f = "#ff2a2a", n_f + 1
                td, cd = f"ZONA DEL CRÁTER: dispara (S {Sv:+.2f} K, umbral {Uv:+.2f} K), rojo", "#ff5a5a"
            elif Sv <= Uv:
                marca, n_bajo = "#ff9f1a", n_bajo + 1
                td, cd = f"Zona del cráter: bajo el umbral en un cuadro suelto (S {Sv:+.2f}, umbral {Uv:+.2f} K)", "#ffb347"
            else:
                td = f"Zona del cráter: no marca (S {Sv:+.2f} K, umbral {Uv:+.2f} K)"
            if marca:
                m = np.zeros(M.NY * M.NX, bool)
                m[Z.ZONA[[int(r["px1"]), int(r["px2"])]]] = True
                a2.pcolormesh(C29.LON, C29.LAT, np.where(m.reshape(M.NY, M.NX), 1.0, np.nan),
                              cmap=matplotlib.colors.ListedColormap([marca]), vmin=0, vmax=1, shading="nearest")
        x, y = L.anillo(4)
        a2.plot(x, y, ":", color="#ffd84d", lw=0.9)
        L.adornar(a2, segs)
        a2.set_title("Regla propia GOES-19 (11 − 12 µm), zona de 0 a 4 km del cráter", color="white", fontsize=11)
        a2.text(0.01, -0.05, td, transform=a2.transAxes, color=cd, fontsize=9)
        hl = datetime.strptime(dia, "%Y-%m-%d") + timedelta(minutes=10 * s) - timedelta(hours=3)
        fig.suptitle(f"Nevados de Chillán ±0,7°   {dia[8:10]}-{dia[5:7]}-{dia[:4]}   {M.hhmm(s)} UTC · "
                     f"{hl:%H:%M} hora de Chile (UTC-3)", color="white", fontsize=13)
        fig.text(0.5, 0.01, "Cada píxel del cráter contra sí mismo en oct-nov 2025 (año tranquilo). Punteado amarillo: "
                 "4 km. Prueba en curso, no operativa.", color="#9aa4b2", fontsize=8.5, ha="center")
        fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.08, wspace=0.03)
        fn = os.path.join(TRABAJO, f"s25a_{dia}_{s:03d}.png")
        fig.savefig(fn, facecolor=fig.get_facecolor())
        plt.close(fig)
        cuadros.append(imageio.imread(fn))
    out = os.path.join(SALIDA, f"s25a_lado_a_lado_volcat_vs_zona_crater_chillan_{dia}_10min.mp4")
    imageio.mimsave(out, cuadros, fps=2, macro_block_size=1)
    print(f"{dia}: {len(cuadros)} cuadros, dispara en {n_f}, bajo el umbral suelto {n_bajo}, VOLCAT dibuja en {n_v} "
          f"-> {out}", flush=True)


if __name__ == "__main__":
    T = tabla()
    for arg in sys.argv[1:]:
        dia, _, rango = arg.partition("@")
        s0, s1 = (72, 143) if not rango else (M.slot(rango.split("-")[0]), M.slot(rango.split("-")[1]))
        dibujar(T, dia, s0, s1)
