r"""S30b, figuras (no deciden). Cuadros P donde el detector coincide y donde no, con la huella de VOLCAT y los píxeles
disparados en la misma grilla ABI de 2 km. Llevan material de SSEC: se escriben en D:\goes_notas\s30\s30b\ y NO van
al repo.

Uso: python -I -B s30b_figuras.py
"""
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s30b_medir as S30  # noqa: E402

M, C29 = S30.M, S30.C29
CASOS = [("2026-10-28", "20:20", "28-10: el anillo marca la tajada SE por donde VOLCAT dibuja la pluma (coincide)"),
         ("2026-11-08", "19:30", "08-11: VOLCAT dibuja un píxel al NO; el anillo marca el SE (no coincide)"),
         ("2026-11-14", "17:00", "14-11: la zona marca el cráter y la huella toca la zona (coincide, sin poder)"),
         ("2026-11-11", "18:00", "11-11: el anillo marca el SE; VOLCAT, pegado al cráter y al NO (no coincide)")]


def anillo(r):
    t = np.linspace(0, 2 * np.pi, 200)
    x, y = r * np.sin(t), r * np.cos(t)
    lat = C29.CRATER[0] + y / 110.57
    lon = C29.CRATER[1] + x / (111.32 * np.cos(np.radians(C29.CRATER[0])))
    return lon, lat


def rayo(az, r0=4, r1=40):
    a = np.radians(az)
    x, y = np.array([r0, r1]) * np.sin(a), np.array([r0, r1]) * np.cos(a)
    return (C29.CRATER[1] + x / (111.32 * np.cos(np.radians(C29.CRATER[0]))), C29.CRATER[0] + y / 110.57)


def figura(dia, hora, titulo, T):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    s = M.slot(hora)
    st, h = S30.huella(dia, s)
    di = S30.disparos(T[dia], s)
    fig, ax = plt.subplots(figsize=(6.2, 6.0), dpi=90)

    def capa(idx, color, alpha=1.0):
        m = np.zeros(S30.NPIX, bool)
        m[np.asarray(idx, int)] = True
        ax.pcolormesh(C29.LON, C29.LAT, np.where(m.reshape(M.NY, M.NX), 1.0, np.nan),
                      cmap=ListedColormap([color]), vmin=0, vmax=1, shading="nearest", alpha=alpha)

    capa(S30.ZONA, "#dddddd")
    if di["Fa"]:
        for k in di["Ka"]:
            capa(np.flatnonzero((S30.SECF == k)), "#ffd6d6")
        capa(di["Ca"], "#d62728")
    if di["Fz"]:
        capa(di["Cz"], "#e6b800")
    if h is not None and len(h):
        capa(h, "#1f77b4", 0.75)
    for r, ls in ((4, ":"), (40, "--")):
        ax.plot(*anillo(r), ls, color="0.3", lw=0.8)
    for az in range(0, 360, 30):
        ax.plot(*rayo(az), color="0.75", lw=0.5)
    ax.plot(C29.CRATER[1], C29.CRATER[0], "^", mfc="none", mec="k", ms=9)
    ax.set_xlim(C29.CRATER[1] - 0.55, C29.CRATER[1] + 0.55)
    ax.set_ylim(C29.CRATER[0] - 0.45, C29.CRATER[0] + 0.45)
    ax.set_aspect(1 / np.cos(np.radians(C29.CRATER[0])))
    ax.set_title(f"{titulo}\n{dia} {hora} UTC", fontsize=9)
    ax.set_xlabel("longitud", fontsize=8)
    ax.set_ylabel("latitud", fontsize=8)
    ax.tick_params(labelsize=7)
    fig.text(0.5, 0.01, "Azul: huella VOLCAT (SSEC) anclada. Rojo: 8 píxeles del anillo que disparó; rosado: su tajada. "
             "Amarillo: zona que disparó.\nGris: los 11 píxeles de la zona. Punteado 4 km, segmentado 40 km, rayos cada "
             "30°. Disparos de s-1 a s+1.", ha="center", fontsize=6.5)
    fig.subplots_adjust(bottom=0.14)
    fn = os.path.join(S30.TRAB, f"s30b_{dia}_{hora.replace(':', '')}.png")
    fig.savefig(fn)
    plt.close(fig)
    return fn, os.path.getsize(fn)


if __name__ == "__main__":
    T = S30.leer_tabla()
    for dia, hora, tit in CASOS:
        print(figura(dia, hora, tit, T), flush=True)
