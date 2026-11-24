r"""S22a, visualización lado a lado (no decide nada): a la izquierda VOLCAT tal como lo publica SSEC (su PNG de altura,
recortado a ±0,7° del cráter), a la derecha lo que marca nuestro detector, pintado igual (píxeles llenos sobre el
infrarrojo de 11 µm en gris), con el mismo encuadre, la misma frontera y los mismos anillos de 10, 25 y 50 km.

Por qué: Nicolás compara a simple vista con los loops de VOLCAT que ya conoce; si nuestro panel muestra algo parecido,
él va a las cámaras del OVDAS. Regla de pintado (fija, escrita antes de mirar):
- ROJO lleno: cuando el detector dispara, los 8 píxeles de la cola de la tajada del mínimo (los que dieron Q_k*).
- Sin altura: este detector todavía no la calcula; el panel lo dice.
Fondo del panel propio: BT11 de GOES-19 en gris (frío = claro, 210 a 320 K), parecido al fondo de VOLCAT.

Los PNG de VOLCAT son de SSEC (licencia restringida): se leen de D: y los videos quedan fuera del repo.
Uso: python -I s22a_lado_a_lado.py 2026-11-08 [2026-11-14 ...]
"""
import json
import os
import sys
import warnings
from datetime import datetime, timedelta

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s22a_medir as M  # noqa: E402
import s22a_mapas as G  # noqa: E402
import h29_comun as C29  # noqa: E402

RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
GEO = os.path.join(RAIZ, "dashboard", "chile_geometry.json")
SALIDA = r"C:\Users\nmend\Downloads"
TRABAJO = r"D:\goes_notas\s22\lado_a_lado"
PAD = 0.7
CLAT, CLON = C29.CRATER
VOLCANES = [("Nevados de Chillán", CLAT, CLON), ("Antuco", -37.41, -71.35), ("Nevado de Longaví", -36.19, -71.16)]
HMAP_FRAC = 0.92


def png_volcat_rgb(dia, s):
    nombre = f"{dia}_{s // 6:02d}-{s % 6 * 10:02d}-30.png"
    for d in G.PNG_DIRS:
        fn = os.path.join(d, nombre)
        if os.path.exists(fn):
            a = np.asarray(Image.open(fn).convert("RGB"))
            return a[:int(HMAP_FRAC * a.shape[0])]
    return None


def recorte_volcat(a):
    """Recorte del mapa del PNG (rejilla lat/lon lineal de h29_comun) a ±PAD del cráter, con su extensión."""
    r0 = int(np.floor((C29.LAT0 - (CLAT + PAD)) / C29.DP))
    r1 = int(np.ceil((C29.LAT0 - (CLAT - PAD)) / C29.DP))
    c0 = int(np.floor(((CLON - PAD) - C29.LON0) / C29.DP))
    c1 = int(np.ceil(((CLON + PAD) - C29.LON0) / C29.DP))
    r0, c0 = max(r0, 0), max(c0, 0)
    sub = a[r0:r1 + 1, c0:c1 + 1]
    ext = (C29.LON0 + (c0 - 0.5) * C29.DP, C29.LON0 + (c0 + sub.shape[1] - 0.5) * C29.DP,
           C29.LAT0 - (r0 + sub.shape[0] - 0.5) * C29.DP, C29.LAT0 - (r0 - 0.5) * C29.DP)
    return sub, ext


def lineas_geo():
    g = json.load(open(GEO, encoding="utf-8"))
    segs = []
    for k in ("coast", "border"):
        cur = []
        for p in g[k]:
            if not p or p[0] is None:
                if len(cur) > 1:
                    segs.append(np.array(cur))
                cur = []
                continue
            cur.append((p[1], p[0]))
        if len(cur) > 1:
            segs.append(np.array(cur))
    return segs


def anillo(r_km):
    t = np.linspace(0, 2 * np.pi, 200)
    return (CLON + r_km * np.sin(t) / (111.32 * np.cos(np.radians(CLAT))), CLAT + r_km * np.cos(t) / 110.57)


def adornar(ax, segs):
    for sg in segs:
        ax.plot(sg[:, 0], sg[:, 1], color="white", lw=1.0)
    for r in (10, 25, 50):
        x, y = anillo(r)
        ax.plot(x, y, "--", color="#4fd3e8", lw=0.8)
        ax.text(CLON + r * 0.72 / (111.32 * np.cos(np.radians(CLAT))), CLAT + r * 0.72 / 110.57, f"{r} km",
                color="#4fd3e8", fontsize=8)
    for nom, la, lo in VOLCANES:
        ax.plot(lo, la, "^", ms=9, mfc="none", mec="#4fd3e8", mew=1.6)     # hueco: no tapa el cráter
        ax.text(lo - 0.03, la, nom, color="white", fontsize=8, ha="right", va="center",
                bbox=dict(facecolor="black", alpha=0.45, lw=0, pad=1))
    ax.set_xlim(CLON - PAD, CLON + PAD)
    ax.set_ylim(CLAT - PAD, CLAT + PAD)
    ax.set_aspect(1 / np.cos(np.radians(CLAT)))
    ax.set_xticks([])
    ax.set_yticks([])


def dibujar(dia):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import imageio.v2 as imageio

    B = M.cargar_bt()
    d = M.dia_idx(dia)
    m1, S, K, F, U, rol = G.tablas(dia)
    segs = lineas_geo()
    os.makedirs(TRABAJO, exist_ok=True)
    cuadros, n_f, n_v = [], 0, 0
    for s in range(G.S_INI, G.S_FIN + 1):
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.4, 6.9), dpi=100, facecolor="#0b0f17")
        # izquierda: VOLCAT tal cual
        a = png_volcat_rgb(dia, s)
        if a is not None:
            sub, ext = recorte_volcat(a)
            a1.imshow(sub, extent=ext, interpolation="nearest")
            ash, _ = G.png_volcat(dia, s)
            hay_v = ash is not None and ash.any()
            n_v += int(hay_v)
            tv = "VOLCAT: ceniza (color = altura, km sobre el mar)" if hay_v else "VOLCAT: sin dibujo en este cuadro"
        else:
            a1.set_facecolor("black")
            tv = "VOLCAT: no hay imagen guardada de este cuadro"
        adornar(a1, segs)
        a1.set_title("VOLCAT (SSEC), altura de pluma", color="white", fontsize=11)
        a1.text(0.01, -0.05, tv, transform=a1.transAxes, color="#ffb347", fontsize=9)
        # derecha: nuestro detector
        bt = B["bt11"][d, s].reshape(M.NY, M.NX)
        a2.pcolormesh(C29.LON, C29.LAT, bt, cmap="gray_r", vmin=210, vmax=320, shading="nearest")
        if F[s]:
            n_f += 1
            idx = np.flatnonzero(M.SEC == K[s])
            v = m1[s][idx]
            o = np.argsort(np.where(np.isfinite(v), v, np.inf))[:M.NCOLA]
            roj = np.zeros(M.NY * M.NX, bool)
            roj[M.AP[idx[o]]] = True
            a2.pcolormesh(C29.LON, C29.LAT, np.where(roj.reshape(M.NY, M.NX), 1.0, np.nan), cmap=matplotlib.colors.ListedColormap(["#ff2a2a"]),
                          vmin=0, vmax=1, shading="nearest")
            a0 = 30 * K[s]
            td = f"DETECTOR: marca pluma hacia {a0}° a {a0 + 30}° (rojo). Sin altura todavía"
            cd = "#ff5a5a"
        else:
            td = ("Nuestro detector: no marca nada" if np.isfinite(S[s])
                  else "Nuestro detector: sin evaluar (nubes o datos faltantes)")
            cd = "white"
        x, y = anillo(40)
        a2.plot(x, y, ":", color="#ff9f43", lw=0.8)           # hasta donde busca el detector
        adornar(a2, segs)
        a2.set_title("Detector propio GOES-19 (11 − 12 µm), 4 a 40 km", color="white", fontsize=11)
        a2.text(0.01, -0.05, td, transform=a2.transAxes, color=cd, fontsize=9)
        hl = datetime.strptime(dia, "%Y-%m-%d") + timedelta(minutes=10 * s) - timedelta(hours=3)
        fig.suptitle(f"Nevados de Chillán ±0,7°   {dia[8:10]}-{dia[5:7]}-{dia[:4]}   {M.hhmm(s)} UTC · "
                     f"{hl:%H:%M} hora de Chile (UTC-3)", color="white", fontsize=13)
        fig.text(0.5, 0.01, f"Día: {rol}. Prueba en curso, no operativa: el detector todavía no separa pluma de nubes.",
                 color="#9aa4b2", fontsize=8.5, ha="center")
        fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.08, wspace=0.03)
        fn = os.path.join(TRABAJO, f"{dia}_{s:03d}.png")
        fig.savefig(fn, facecolor=fig.get_facecolor())
        plt.close(fig)
        cuadros.append(imageio.imread(fn))
    out = os.path.join(SALIDA, f"s22a_lado_a_lado_volcat_vs_detector_chillan_{dia}_10min.mp4")
    imageio.mimsave(out, cuadros, fps=2, macro_block_size=1)
    print(f"{dia}: {len(cuadros)} cuadros, detector marca en {n_f}, VOLCAT dibuja en {n_v} -> {out}")


if __name__ == "__main__":
    for dia in sys.argv[1:]:
        dibujar(dia)
