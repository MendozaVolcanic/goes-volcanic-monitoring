r"""S27b, video lado a lado (no decide nada). Igual al de S26a (izquierda VOLCAT tal cual, derecha IR 11 µm con rojo
= anillo y amarillo = zona del cráter), más la altura por rapidez anotada: en el cuadro del pulso y en el de la llegada
se escribe Δt, la distancia, la banda de alturas compatible (rapidez y rumbo) y h*, leídos de
resultados/s27b_resultado.json. Los PNG de VOLCAT son de SSEC (licencia restringida): el video va a Downloads.

Uso: python -I s27b_lado_a_lado.py 2026-10-28@17:30-20:30 2026-11-08@15:30-18:30
"""
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
sys.path.insert(0, os.path.join(OV, "s26a_combinado", "scripts"))
import s26a_lado_a_lado as L26  # noqa: E402

B, M, C29, L = L26.B, L26.M, L26.C29, L26.L
RES = os.path.join(os.path.dirname(AQUI), "resultados")
SALIDA = r"C:\Users\nmend\Downloads"
TRABAJO = r"D:\goes_notas\s27\s27b\lado_a_lado"


def notas_por_cuadro():
    """{(dia, hh:mm): [líneas]} con lo que el método dice en el cuadro del pulso y en el de la llegada."""
    r = json.load(open(os.path.join(RES, "s27b_resultado.json"), encoding="utf-8"))
    out = {}
    for f in r["llegadas"]:
        if not f["candidatos"]:
            continue
        dia, ha = f["llegada"][:10], f["llegada"][11:]
        lin = []
        for j, c in enumerate(f["candidatos"]):
            b = c["rapidez_y_rumbo"]["banda"]
            elegido = "" if f["elegido"] is None else (" (par)" if j == f["elegido"] else " (descartado)")
            lin.append(f"pulso {c['pulso'][11:]} UTC{elegido}: Δt {c['dt_min']} min, a {c['d_km_3p2_4p7_10'][1]:.0f} km"
                       f" (si está a 4,7 km); rapidez {c['v_obs_4p7'][0]:.1f} a {c['v_obs_4p7'][1]:.1f} m/s; alturas"
                       f" compatibles {b[0]:.1f} a {b[1]:.1f} km, h* {c['h_estrella']:.1f} km"
                       if b else f"pulso {c['pulso'][11:]} UTC: sin altura compatible")
        if f["elegido"] is None:
            lect = "los dos pulsos candidatos dan altura, no se evalúa"
        else:
            bb = f["candidatos"][f["elegido"]]["rapidez_y_rumbo"]
            lect = ("restringe por la regla, sin verdad este día (informativo)" if bb["restringe"]
                    else "no restringe")
        cab = f"LLEGADA AL ANILLO {ha} UTC ({f['tipo']}; {lect})"
        out.setdefault((dia, ha), []).extend([cab] + lin)
        for c in f["candidatos"]:
            out.setdefault((dia, c["pulso"][11:]), []).append(
                f"PULSO EN EL CRÁTER {c['pulso'][11:]} UTC, candidato de la llegada de las {ha} UTC")
    return out


def dibujar(T, notas, dia, s0, s1, est):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import imageio.v2 as imageio

    d = B.dia_idx(dia)
    bt, acm = L26.cargar(d)
    segs = L.lineas_geo()
    os.makedirs(TRABAJO, exist_ok=True)
    cuadros = []
    for s in range(s0, s1 + 1):
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.4, 7.4), dpi=100, facecolor="#0b0f17")
        a = L.png_volcat_rgb(dia, s)
        if a is not None:
            sub, ext = L.recorte_volcat(a)
            a1.imshow(sub, extent=ext, interpolation="nearest")
            ash, _ = L26.G.png_volcat(dia, s)
            tv = ("VOLCAT: ceniza (color = altura, km sobre el mar)" if ash is not None and ash.any()
                  else "VOLCAT: sin dibujo en este cuadro")
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
            L26.capa(a2, np.flatnonzero(B.borde(B.dinamica(acm[s], est[s]))), L26.CELESTE, 0.35)
        r = T.get((dia, M.hhmm(s)))
        partes = []
        if r is not None and r["F_a"] == "1":
            L26.capa(a2, [int(x) for x in r["cola_a"].split(";")], L26.ROJO)
            partes.append(f"anillo hacia {30 * int(r['k_a'])}° a {30 * int(r['k_a']) + 30}° (rojo)")
        if r is not None and r["F_z"] == "1":
            L26.capa(a2, [int(r["px1"]), int(r["px2"])], L26.AMARILLO)
            partes.append("zona del cráter (amarillo)")
        td = "DETECTOR MARCA PLUMA: " + " y ".join(partes) if partes else "Detector: no marca nada"
        for rad, est_l, col in ((4, ":", "white"), (40, ":", "#ff9f43")):
            x, y = L.anillo(rad)
            a2.plot(x, y, est_l, color=col, lw=0.9)
        L.adornar(a2, segs)
        a2.set_title("Detector propio GOES-19: cráter + anillo (S26a)", color="white", fontsize=11)
        a2.text(0.01, -0.05, td, transform=a2.transAxes, color="#ff5a5a" if partes else "white", fontsize=9)
        hl = datetime.strptime(dia, "%Y-%m-%d") + timedelta(minutes=10 * s) - timedelta(hours=3)
        fig.suptitle(f"Nevados de Chillán ±0,7°   {dia[8:10]}-{dia[5:7]}-{dia[:4]}   {M.hhmm(s)} UTC · "
                     f"{hl:%H:%M} hora de Chile (UTC-3)", color="white", fontsize=13)
        nota = notas.get((dia, M.hhmm(s)), [])
        for i, t in enumerate(nota[:4]):
            fig.text(0.5, 0.135 - 0.028 * i, t, color="#7CFC00" if i == 0 else "#e6edf3", fontsize=9, ha="center")
        fig.text(0.5, 0.012, "Altura por rapidez (S27b): banda de alturas donde la rapidez y el rumbo del viento GFS "
                 "calzan con el viaje del pulso. Desarrollo, no operativo; la prueba que decide quedó NO DECIDIBLE.",
                 color="#9aa4b2", fontsize=8.5, ha="center")
        fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.2, wspace=0.03)
        fn = os.path.join(TRABAJO, f"s27b_{dia}_{s:03d}.png")
        fig.savefig(fn, facecolor=fig.get_facecolor())
        plt.close(fig)
        img = imageio.imread(fn)
        cuadros.extend([img] * (3 if nota else 1))         # los cuadros anotados quedan 1,5 s
    out = os.path.join(SALIDA, f"s27b_lado_a_lado_altura_por_rapidez_chillan_{dia}_"
                               f"{M.hhmm(s0).replace(':', '')}-{M.hhmm(s1).replace(':', '')}UTC_10min.mp4")
    imageio.mimsave(out, cuadros, fps=2, macro_block_size=1)
    print(f"{dia}: {s1 - s0 + 1} cuadros -> {out}", flush=True)
    return out


if __name__ == "__main__":
    T = L26.tabla()
    est = np.load(L26.ESTAT26)
    notas = notas_por_cuadro()
    for arg in sys.argv[1:]:
        dia, _, rango = arg.partition("@")
        a, b = rango.split("-")
        dibujar(T, notas, dia, M.slot(a), M.slot(b), est)
