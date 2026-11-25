r"""S27a, video de noche lado a lado (no decide nada; criterio §5). Es el video de S26a (s26a_lado_a_lado.py, mismas
funciones) con dos agregados para comparar con las cámaras nocturnas del OVDAS:
- FLECHA del viento GFS de la capa de 3 a 6 km (hacia donde sopla), saliendo del cráter, con su rapidez.
- CRUZ donde GOES-19 ve algo que está a 4,5 km sobre el cráter (paralaje): una pluma sobre el cráter aparece ahí.
Rojo = anillo de 4 a 40 km; amarillo = zona de 0 a 4 km del cráter; celeste = nube que el anillo no usa.

Los PNG de VOLCAT son de SSEC (licencia restringida): se leen de D: y los videos quedan fuera del repo.
Uso: python -I s27a_lado_a_lado.py 2026-09-27 [2026-10-05@03:00-08:50 ...]   (por defecto 03:00 a 08:50 UTC)
"""
import json
import math
import os
import sys
import warnings
from datetime import datetime, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(OV, "s26a_combinado", "scripts"))
import s26a_lado_a_lado as V  # noqa: E402
import s27a_medir as T  # noqa: E402

B, M, C29, L, G = V.B, V.M, V.C29, V.L, V.G
SALIDA = r"C:\Users\nmend\Downloads"
TRABAJO = os.path.join(T.TRAB, "lado_a_lado")


def dibujar(Tb, dia, s0, s1, est):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import imageio.v2 as imageio

    d = B.dia_idx(dia)
    bt, acm = V.cargar(d)
    segs = L.lineas_geo()
    la_c, lo_c = T.parallax_shift(T.CLAT, T.CLON, -T.H_REF * 1000.0, sat_lon=T.SAT_LON)   # aparente a 4,5 km
    os.makedirs(TRABAJO, exist_ok=True)
    cuadros, n = [], {"anillo": 0, "zona": 0, "volcat": 0}
    for s in range(s0, s1 + 1):
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.4, 6.9), dpi=100, facecolor="#0b0f17")
        a = L.png_volcat_rgb(dia, s)
        if a is not None:
            sub, ext = L.recorte_volcat(a)
            a1.imshow(sub, extent=ext, interpolation="nearest")
            ash, _ = G.png_volcat(dia, s)
            hay_v = ash is not None and ash.any()
            n["volcat"] += int(hay_v)
            tv = "VOLCAT: ceniza (color = altura)" if hay_v else "VOLCAT: sin dibujo en este cuadro"
        else:
            a1.set_facecolor("black")
            tv = "VOLCAT: no hay imagen guardada de este cuadro"
        L.adornar(a1, segs)
        a1.set_title("VOLCAT (SSEC), altura de pluma", color="white", fontsize=11)
        a1.text(0.01, -0.05, tv, transform=a1.transAxes, color="#ffb347", fontsize=9)
        b = bt[s].reshape(M.NY, M.NX)
        if np.isfinite(b).any():
            a2.pcolormesh(C29.LON, C29.LAT, b, cmap="gray_r", vmin=210, vmax=300, shading="nearest")
        if (acm[s] != 255).any():
            nub = B.borde(B.dinamica(acm[s], est[s]))
            V.capa(a2, np.flatnonzero(nub), V.CELESTE, 0.35)
        r = Tb.get((dia, M.hhmm(s)))
        partes = []
        if r is None or (r["ev_a"] == "0" and r["ev_z"] == "0"):
            td, cd = "Detector: sin evaluar (nube o datos faltantes)", V.CELESTE
        else:
            if r["F_a"] == "1":
                V.capa(a2, [int(x) for x in r["cola_a"].split(";")], V.ROJO)
                partes.append("anillo (rojo)")
                n["anillo"] += 1
            if r["F_z"] == "1":
                V.capa(a2, [int(r["px1"]), int(r["px2"])], V.AMARILLO)
                partes.append("zona del cráter (amarillo)")
                n["zona"] += 1
            td, cd = (("DETECTOR MARCA: " + " y ".join(partes), "#ff5a5a") if partes
                      else ("Detector: no marca nada", "white"))
        x, y = L.anillo(4)
        a2.plot(x, y, ":", color="white", lw=0.9)
        x, y = L.anillo(40)
        a2.plot(x, y, ":", color="#ff9f43", lw=0.8)
        L.adornar(a2, segs)
        a2.plot(lo_c, la_c, "+", color="#ff66ff", ms=12, mew=2)
        w = T.viento(datetime.strptime(dia, "%Y-%m-%d") + timedelta(minutes=10 * s), (3, 6, 9))
        if w is not None:
            tw, vv, _ = w
            k = 0.01 * min(vv, 40.0)                              # 10 m/s = 0,1 grados de flecha
            dx = k * math.sin(math.radians(tw)) / math.cos(math.radians(T.CLAT))
            dy = k * math.cos(math.radians(tw))
            a2.annotate("", xy=(T.CLON + dx, T.CLAT + dy), xytext=(T.CLON, T.CLAT),
                        arrowprops=dict(arrowstyle="-|>", color="#7CFC00", lw=2.2))
            tw_txt = f"viento GFS 3 a 6 km: hacia {tw:.0f}°, {vv:.0f} m/s (flecha verde)"
        else:
            tw_txt = "viento GFS: sin dato"
        a2.set_title("Detector propio GOES-19 (11 − 12 µm), IR 11 µm de noche", color="white", fontsize=11)
        a2.text(0.01, -0.05, td, transform=a2.transAxes, color=cd, fontsize=9)
        a2.text(0.01, -0.09, tw_txt, transform=a2.transAxes, color="#7CFC00", fontsize=9)
        hl = datetime.strptime(dia, "%Y-%m-%d") + timedelta(minutes=10 * s) - timedelta(hours=3)
        fig.suptitle(f"Nevados de Chillán ±0,7°   {dia[8:10]}-{dia[5:7]}-{dia[:4]}   {M.hhmm(s)} UTC · "
                     f"{hl:%H:%M} hora de Chile (UTC-3)", color="white", fontsize=13)
        fig.text(0.5, 0.01, "Rojo: anillo 4 a 40 km. Amarillo: zona 0 a 4 km. Celeste: nube. Cruz rosada: donde GOES "
                 "ve algo a 4,5 km sobre el cráter. Base y umbral de oct-nov 2025. Prueba, no operativa.",
                 color="#9aa4b2", fontsize=8.5, ha="center")
        fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.11, wspace=0.03)
        fn = os.path.join(TRABAJO, f"s27a_{dia}_{s:03d}.png")
        fig.savefig(fn, facecolor=fig.get_facecolor())
        plt.close(fig)
        cuadros.append(imageio.imread(fn))
    out = os.path.join(SALIDA, f"s27a_noche_detector_y_viento_chillan_{dia}_"
                       f"{M.hhmm(s0).replace(':', '')}-{M.hhmm(s1).replace(':', '')}UTC_10min.mp4")
    imageio.mimsave(out, cuadros, fps=2, macro_block_size=1)
    print(f"{dia}: {len(cuadros)} cuadros, anillo {n['anillo']}, zona {n['zona']}, VOLCAT {n['volcat']} -> {out}",
          flush=True)
    return {"dia": dia, "cuadros": len(cuadros), **n, "video": out}


if __name__ == "__main__":
    Tb = V.tabla()
    est = np.load(V.ESTAT26)
    res = []
    for arg in sys.argv[1:]:
        dia, _, rango = arg.partition("@")
        s0, s1 = (18, 53) if not rango else (M.slot(rango.split("-")[0]), M.slot(rango.split("-")[1]))
        res.append(dibujar(Tb, dia, s0, s1, est))
    print(json.dumps(res, ensure_ascii=False))
