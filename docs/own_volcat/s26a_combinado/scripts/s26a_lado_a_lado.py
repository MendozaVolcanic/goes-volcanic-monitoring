r"""S26a, visualización lado a lado (no decide nada; criterio §4). A la izquierda VOLCAT tal como lo publica SSEC
(PNG de altura recortado a ±0,7° del cráter); a la derecha el IR de 11 µm en gris, mismo encuadre, frontera y anillos
de 10, 25 y 50 km (funciones de s22a_lado_a_lado.py sin cambios). Píxeles llenos, como VOLCAT:
- ROJO: los 8 píxeles de la cola de la tajada cuando dispara el anillo (4 a 40 km).
- AMARILLO: los dos píxeles de la zona del cráter (0 a 4 km) cuando dispara la zona.
- Celeste translúcido: nube dinámica y su borde, que el anillo no usa.
Lee la tabla por cuadro que escribe `s26a_medir.py medir` (D:\goes_notas\s26\s26a\tabla_2026.csv).

Los PNG de VOLCAT son de SSEC (licencia restringida): se leen de D: y los videos quedan fuera del repo.
Uso: python -I s26a_lado_a_lado.py 2026-11-14 [2026-10-29@00:00-02:00 ...]
"""
import csv
import json
import os
import sys
import warnings
from datetime import datetime, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
sys.path.insert(0, os.path.join(OV, "s22b_pluma_vs_nubes", "scripts"))
import s22b_medir as B  # noqa: E402
M, C29 = B.M, B.C29
sys.path.insert(0, os.path.join(OV, "s22a_detector_sectores", "scripts"))
import s22a_mapas as G  # noqa: E402
import s22a_lado_a_lado as L  # noqa: E402

G.PNG_DIRS.append(r"D:\goes_notas\s22\s22b\volcat_png\frames")
G.PNG_DIRS.append(r"D:\goes_notas\s23\volcat_png\Chile_Central_2_km\frames")
TRAB = r"D:\goes_notas\s26\s26a"
ESTAT26 = r"D:\goes_notas\s23\s23b\estat_2026.npy"
SALIDA = r"C:\Users\nmend\Downloads"
TRABAJO = os.path.join(TRAB, "lado_a_lado")
ROJO, AMARILLO, CELESTE = "#ff2a2a", "#ffe14d", "#5ec8ff"


def tabla():
    with open(os.path.join(TRAB, "tabla_2026.csv"), encoding="utf-8") as f:
        return {(r["dia"], r["hora"]): r for r in csv.DictReader(f)}


def cargar(d):
    if d >= B.NDEV:
        bt = np.load(os.path.join(B.TRAB, "nuevo_bt11.npy"))[d - B.NDEV]
        acm = np.load(os.path.join(B.TRAB, "nuevo_acm.npy"))[d - B.NDEV]
    else:
        bt = np.asarray(np.load(os.path.join(B.TRAB, "dev_bt11.npy"), mmap_mode="r")[d])
        acm = np.asarray(np.load(os.path.join(B.TRAB, "dev_acm.npy"), mmap_mode="r")[d])
    return bt, acm


def capa(ax, idx, color, alpha=1.0):
    import matplotlib
    m = np.zeros(M.NY * M.NX, bool)
    m[idx] = True
    ax.pcolormesh(C29.LON, C29.LAT, np.where(m.reshape(M.NY, M.NX), 1.0, np.nan),
                  cmap=matplotlib.colors.ListedColormap([color]), vmin=0, vmax=1, shading="nearest", alpha=alpha)


def dibujar(T, dia, s0=72, s1=143, est=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import imageio.v2 as imageio

    d = B.dia_idx(dia)
    bt, acm = cargar(d)
    segs = L.lineas_geo()
    os.makedirs(TRABAJO, exist_ok=True)
    cuadros, n = [], {"anillo": 0, "zona": 0, "volcat": 0, "P": 0}
    for s in range(s0, s1 + 1):
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.4, 6.9), dpi=100, facecolor="#0b0f17")
        a = L.png_volcat_rgb(dia, s)
        if a is not None:
            sub, ext = L.recorte_volcat(a)
            a1.imshow(sub, extent=ext, interpolation="nearest")
            ash, _ = G.png_volcat(dia, s)
            hay_v = ash is not None and ash.any()
            n["volcat"] += int(hay_v)
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
        if (acm[s] != 255).any():
            nub = B.borde(B.dinamica(acm[s], est[s]))
            capa(a2, np.flatnonzero(nub), CELESTE, 0.35)
        r = T.get((dia, M.hhmm(s)))
        partes = []
        if r is None or (r["ev_a"] == "0" and r["ev_z"] == "0"):
            td, cd = "Detector: sin evaluar (más de la mitad del anillo nublado, o datos o umbral faltantes)", CELESTE
        else:
            if r["F_a"] == "1":
                capa(a2, [int(x) for x in r["cola_a"].split(";")], ROJO)
                a0 = 30 * int(r["k_a"])
                partes.append(f"anillo hacia {a0}° a {a0 + 30}° (rojo)")
                n["anillo"] += 1
            if r["F_z"] == "1":
                capa(a2, [int(r["px1"]), int(r["px2"])], AMARILLO)
                partes.append("zona del cráter (amarillo)")
                n["zona"] += 1
            if partes:
                td, cd = "DETECTOR MARCA PLUMA: " + " y ".join(partes), "#ff5a5a"
            else:
                td, cd = "Detector: no marca nada", "white"
        if r is not None and r["clase"] == "P":
            n["P"] += 1
        x, y = L.anillo(4)
        a2.plot(x, y, ":", color="white", lw=0.9)
        x, y = L.anillo(40)
        a2.plot(x, y, ":", color="#ff9f43", lw=0.8)
        L.adornar(a2, segs)
        a2.set_title("Detector propio GOES-19 (11 − 12 µm): cráter + anillo, fondo 2025", color="white", fontsize=11)
        a2.text(0.01, -0.05, td, transform=a2.transAxes, color=cd, fontsize=9)
        hl = datetime.strptime(dia, "%Y-%m-%d") + timedelta(minutes=10 * s) - timedelta(hours=3)
        fig.suptitle(f"Nevados de Chillán ±0,7°   {dia[8:10]}-{dia[5:7]}-{dia[:4]}   {M.hhmm(s)} UTC · "
                     f"{hl:%H:%M} hora de Chile (UTC-3)", color="white", fontsize=13)
        fig.text(0.5, 0.01, "Rojo: anillo de 4 a 40 km (naranjo punteado). Amarillo: zona de 0 a 4 km (blanco "
                 "punteado). Celeste: nube. Base y umbral de oct-nov 2025. Prueba en curso, no operativa.",
                 color="#9aa4b2", fontsize=8.5, ha="center")
        fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.08, wspace=0.03)
        fn = os.path.join(TRABAJO, f"s26a_{dia}_{s:03d}.png")
        fig.savefig(fn, facecolor=fig.get_facecolor())
        plt.close(fig)
        cuadros.append(imageio.imread(fn))
    sufijo = "" if (s0, s1) == (72, 143) else f"_{M.hhmm(s0).replace(':', '')}-{M.hhmm(s1).replace(':', '')}UTC"
    out = os.path.join(SALIDA, f"s26a_lado_a_lado_volcat_vs_crater_y_anillo_chillan_{dia}{sufijo}_10min.mp4")
    imageio.mimsave(out, cuadros, fps=2, macro_block_size=1)
    print(f"{dia}: {len(cuadros)} cuadros, anillo marca {n['anillo']}, zona marca {n['zona']}, VOLCAT dibuja "
          f"{n['volcat']} -> {out}", flush=True)
    return {"dia": dia, "cuadros": len(cuadros), **n, "video": out}


if __name__ == "__main__":
    T = tabla()
    est = np.load(ESTAT26)
    res = []
    for arg in sys.argv[1:]:
        dia, _, rango = arg.partition("@")
        s0, s1 = (72, 143) if not rango else (M.slot(rango.split("-")[0]), M.slot(rango.split("-")[1]))
        res.append(dibujar(T, dia, s0, s1, est))
    print(json.dumps(res, ensure_ascii=False))
