r"""S22c, visualización lado a lado (no decide nada): VOLCAT tal como lo publica SSEC a la izquierda y, a la derecha,
los 8 píxeles que marca el detector S22a pintados con el color de su altura propia (método (a), altura por rumbo
contra el viento GFS), con la MISMA escala de bloques de la barra de VOLCAT (0 a 20 km).

Regla de pintado (criterio §5, fija antes de mirar): color del bloque de VOLCAT que contiene h*; si el cuadro no tiene
altura compatible, los píxeles van en blanco y el texto lo dice. Bajo el panel: h* y la banda de alturas compatibles.
Los píxeles se dibujan donde GOES-19 los ve (sin corregir paralaje), igual que el fondo y que S22a, para comparar con
el PNG de VOLCAT en la misma geometría; la altura sí se calculó con la posición corregida.

Los colores de la barra se leen en tiempo de ejecución desde el PNG de SSEC en D: (licencia restringida): no se
guardan en el repo, y los videos quedan fuera del repo.
Uso: python -I s22c_lado_a_lado.py 2026-11-08 [2026-11-14 ...]   (requiere resultados/s22c_resultado.json)
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
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
REPO = os.path.abspath(os.path.join(OV, "..", ".."))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(OV, "s22a_detector_sectores", "scripts"))
sys.path.insert(0, os.path.join(OV, "h24_pulsos_reav", "scripts"))
sys.path.insert(0, os.path.join(OV, "h29_pluma_0811", "scripts"))
import s22a_lado_a_lado as L  # noqa: E402
import s22a_mapas as G  # noqa: E402
import s22a_medir as M  # noqa: E402
import h29_comun as C29  # noqa: E402
from src.process import volcat_colorbar as vc  # noqa: E402

RES = os.path.join(os.path.dirname(AQUI), "resultados")
SALIDA = r"C:\Users\nmend\Downloads"
TRABAJO = r"D:\goes_notas\s22\s22c\lado_a_lado"


def barra_volcat(dia):
    """Bloques de la barra (lo_km, hi_km, rgb 0-1) leídos del primer PNG de VOLCAT del día que la tenga."""
    for d in G.PNG_DIRS:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.startswith(dia) and fn.endswith(".png") and "_annot" not in fn:
                a = np.asarray(Image.open(os.path.join(d, fn)).convert("RGB"), dtype="float64")
                b = vc.palette_bins(a[int(vc.MAP_FRAC * a.shape[0]):])
                if b:
                    return [(x["lo_km"], x["hi_km"], x["rgb"] / 255.0) for x in b]
    raise RuntimeError(f"sin barra de VOLCAT legible para {dia}")


def color_de(h, bins):
    for lo, hi, rgb in bins:
        if lo <= h < hi:
            return rgb
    return bins[-1][2] if h >= bins[-1][1] else bins[0][2]


def dibujar(dia, res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    import imageio.v2 as imageio

    bins = barra_volcat(dia)
    bordes = [bins[0][0]] + [b[1] for b in bins]
    cmap = ListedColormap([b[2] for b in bins])
    norm = BoundaryNorm(bordes, cmap.N)
    B = M.cargar_bt()
    d = M.dia_idx(dia)
    por_slot = {f["slot"]: f for f in res["dias"][dia]["cuadros"]}
    rs = res["dias"][dia]["resumen"]
    segs = L.lineas_geo()
    os.makedirs(TRABAJO, exist_ok=True)
    cuadros, n_f, n_v = [], 0, 0
    for s in range(G.S_INI, G.S_FIN + 1):
        fig = plt.figure(figsize=(12.4, 7.4), dpi=100, facecolor="#0b0f17")
        a1 = fig.add_axes([0.01, 0.15, 0.485, 0.75])
        a2 = fig.add_axes([0.505, 0.15, 0.485, 0.75])
        cax = fig.add_axes([0.56, 0.075, 0.38, 0.022])
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
        bt = B["bt11"][d, s].reshape(M.NY, M.NX)
        a2.pcolormesh(C29.LON, C29.LAT, bt, cmap="gray_r", vmin=210, vmax=320, shading="nearest")
        f = por_slot.get(s)
        if f is not None:
            n_f += 1
            p = f.get("principal", {})
            h = p.get("h")
            campo = np.full((M.NY, M.NX), np.nan)
            campo[np.array(f["filas"]), np.array(f["cols"])] = 1.0
            col = color_de(h, bins) if h is not None else (1.0, 1.0, 1.0)
            a2.pcolormesh(C29.LON, C29.LAT, campo, cmap=ListedColormap([col]), vmin=0, vmax=1, shading="nearest")
            if h is not None:
                td = (f"DETECTOR hacia {30 * f['tajada']}° a {30 * f['tajada'] + 30}°: altura por viento {h:.1f} km "
                      f"(compatibles {p['banda'][0]:.1f} a {p['banda'][1]:.1f} km)")
                cd = "#ffffff"
            else:
                td = f"DETECTOR hacia {30 * f['tajada']}° a {30 * f['tajada'] + 30}°: sin altura (el viento no calza)"
                cd = "#ff9f43"
        else:
            td = "Nuestro detector: no marca nada en este cuadro"
            cd = "#9aa4b2"
        x, y = L.anillo(40)
        a2.plot(x, y, ":", color="#ff9f43", lw=0.8)
        L.adornar(a2, segs)
        a2.set_title("Detector propio GOES-19 + altura por rumbo y viento GFS", color="white", fontsize=11)
        a2.text(0.01, -0.05, td, transform=a2.transAxes, color=cd, fontsize=8.5)
        sm = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
        cb = fig.colorbar(sm, cax=cax, orientation="horizontal", ticks=list(range(0, 21, 2)))
        cb.ax.tick_params(colors="white", labelsize=8)
        cb.set_label("altura sobre el mar (km), bloques de la barra de VOLCAT", color="white", fontsize=8.5)
        hl = datetime.strptime(dia, "%Y-%m-%d") + timedelta(minutes=10 * s) - timedelta(hours=3)
        fig.suptitle(f"Nevados de Chillán ±0,7°   {dia[8:10]}-{dia[5:7]}-{dia[:4]}   {M.hhmm(s)} UTC · "
                     f"{hl:%H:%M} hora de Chile (UTC-3)", color="white", fontsize=13)
        fig.text(0.5, 0.012, f"Prueba S22c, no operativa. Día: mediana {rs.get('h_mediana', '-')} km en "
                 f"{rs.get('n_con_altura', 0)} de {rs['n_disparos']} disparos; banda mediana {rs.get('ancho_mediano', '-')}"
                 f" km. Píxeles donde los ve GOES-19 (sin corregir paralaje).", color="#9aa4b2", fontsize=8, ha="center")
        fn = os.path.join(TRABAJO, f"{dia}_{s:03d}.png")
        fig.savefig(fn, facecolor=fig.get_facecolor())
        plt.close(fig)
        cuadros.append(imageio.imread(fn))
    out = os.path.join(SALIDA, f"s22c_lado_a_lado_altura_volcat_vs_detector_chillan_{dia}_10min.mp4")
    imageio.mimsave(out, cuadros, fps=2, macro_block_size=1)
    print(f"{dia}: {len(cuadros)} cuadros, detector con altura en {n_f}, VOLCAT dibuja en {n_v} -> {out}")


if __name__ == "__main__":
    res = json.load(open(os.path.join(RES, "s22c_resultado.json"), encoding="utf-8"))
    for dia in sys.argv[1:]:
        dibujar(dia, res)
