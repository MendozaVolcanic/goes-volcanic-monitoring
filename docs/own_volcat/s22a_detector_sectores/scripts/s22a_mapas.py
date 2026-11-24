r"""S22a, visualización (no decide nada): qué píxeles marca el detector por sectores, cuadro a cuadro, al lado de la
huella que publicó VOLCAT, en la misma grilla ABI de 2 km.

Por qué: Nicolás quiere ver, como en un loop de VOLCAT, si lo que marca el detector se parece a lo que mostró VOLCAT;
si se parece, él va a las cámaras del OVDAS a comprobarlo. El detector decide por tajada (criterio S22a); para pintar
píxeles se usa una regla de dibujo fija, escrita aquí antes de mirar los mapas:
- ROJO: cuando el detector dispara (F), los 8 píxeles de la cola de la tajada del mínimo (los que dieron Q_k*).
- MORADO: cualquier píxel del anillo con M1 <= -1,0 K (diferencia 11 - 12 um 1 K más baja que sus pares del mismo
  cuadro con igual BT11 y cota); es contexto, no detección.
- NARANJA (borde): píxeles que el PNG de VOLCAT marca con ceniza, llevados a la grilla ABI con la georreferencia de H14
  (h29_comun.a_abi, corrimiento (-1, -1)).
Fondo: BT11 en gris (frío = claro), para ver nubes y terreno.

Los PNG de VOLCAT son de SSEC (licencia restringida): leer de D:, y los videos quedan fuera del repo.

Uso: python -I s22a_mapas.py 2026-11-08 [2026-11-15 ...]
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
import s22a_medir as M  # noqa: E402
import h29_comun as C29  # noqa: E402

PNG_DIRS = [C29.FRAMES, r"D:\goes_notas\s22\volcat_png\Chile_Central_2_km\frames"]
SALIDA = r"C:\Users\nmend\Downloads"
TRABAJO = r"D:\goes_notas\s22\mapas"
UMBRAL_MORADO = -1.0
LIM_KM = 60.0
S_INI, S_FIN = 12 * 6, 23 * 6 + 5          # 12:00 a 23:50 UTC


def png_volcat(dia, s):
    nombre = f"{dia}_{s // 6:02d}-{s % 6 * 10:02d}-30.png"
    for d in PNG_DIRS:
        fn = os.path.join(d, nombre)
        if os.path.exists(fn):
            ok, mid, bok = C29.decodifica_png(fn)
            if ok is None:
                return None, "PNG sin barra"
            ash, _ = C29.a_abi(ok, mid)
            return ash, None
    return None, "sin PNG"


def tablas(dia):
    d = M.dia_idx(dia)
    m1p = M.m1_dias(M.PLACEBO, "placebo")
    Sp, Kp = M.tabla_S(m1p)
    if d in M.PLACEBO:
        j = M.PLACEBO.index(d)
        U, _ = M.umbrales(Sp, excl=j)           # como en el ensayo en seco: el umbral no usa el propio día
        S, K = Sp[j:j + 1], Kp[j:j + 1]
        m1 = m1p[j]
        F, _ = M.disparos(S, K, U)
        return m1, S[0], K[0], F[0], U, "placebo (umbral sin este día)"
    za = np.load(os.path.join(M.CACHE, "m1_actividad.npz"))
    dias = list(za["dias"])
    m1a = za["m1"]
    Sa, Ka = M.tabla_S(m1a)
    U, _ = M.umbrales(Sp)
    F, _ = M.disparos_continuos(Sa, Ka, U, dias)
    j = dias.index(d)
    return m1a[j], Sa[j], Ka[j], F[j], U, "día con actividad"


def dibujar(dia):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    import imageio.v2 as imageio

    B = M.cargar_bt()
    d = M.dia_idx(dia)
    m1, S, K, F, U, rol = tablas(dia)
    X, Y = M._x, M._y
    os.makedirs(TRABAJO, exist_ok=True)
    cuadros = []
    n_f = n_v = 0
    for s in range(S_INI, S_FIN + 1):
        bt = B["bt11"][d, s].reshape(M.NY, M.NX)
        fig, ax = plt.subplots(figsize=(7.2, 7.6), dpi=100)
        ax.pcolormesh(X, Y, bt, cmap="gray_r", vmin=235, vmax=300, shading="nearest")
        # contexto: M1 <= -1 K en el anillo
        mor = np.zeros(M.NY * M.NX, bool)
        ok = np.isfinite(m1[s])
        mor[M.AP[ok & (m1[s] <= UMBRAL_MORADO)]] = True
        mor = mor.reshape(M.NY, M.NX)
        ax.pcolormesh(X, Y, np.where(mor, 1.0, np.nan), cmap="Purples", vmin=0, vmax=1.4, shading="nearest",
                      alpha=0.75)
        # detector: cola de la tajada del mínimo si dispara
        if F[s]:
            n_f += 1
            idx = np.flatnonzero(M.SEC == K[s])
            v = m1[s][idx]
            o = np.argsort(np.where(np.isfinite(v), v, np.inf))[:M.NCOLA]
            roj = np.zeros(M.NY * M.NX, bool)
            roj[M.AP[idx[o]]] = True
            ax.pcolormesh(X, Y, np.where(roj.reshape(M.NY, M.NX), 1.0, np.nan), cmap="Reds", vmin=0, vmax=1.0,
                          shading="nearest")
            a0 = 30 * K[s]
            txt_det = f"DISPARA: tajada {a0}° a {a0 + 30}°"
            col_det = "red"
        else:
            txt_det = "no dispara" if np.isfinite(S[s]) else "sin evaluar (faltan sectores)"
            col_det = "black"
        # VOLCAT
        ash, err = png_volcat(dia, s)
        if ash is not None and ash.any():
            n_v += 1
            ax.contour(X, Y, ash.astype(float), levels=[0.5], colors="darkorange", linewidths=2.0)
            txt_v = f"VOLCAT: {int(ash.sum())} píxeles con ceniza"
            col_v = "darkorange"
        else:
            txt_v = "VOLCAT: nada" if err is None else f"VOLCAT: {err}"
            col_v = "black"
        for r in (M.R_IN, M.R_OUT):
            ax.add_patch(Circle((0, 0), r, fill=False, ls="--", lw=0.8, color="tab:blue"))
        ax.plot(0, 0, "^", ms=11, mfc="none", mec="cyan", mew=2)      # cráter, hueco a propósito
        for az in range(0, 360, 30):
            ax.plot([4 * np.sin(np.radians(az)), 40 * np.sin(np.radians(az))],
                    [4 * np.cos(np.radians(az)), 40 * np.cos(np.radians(az))], color="tab:blue", lw=0.3)
        ax.set_xlim(-LIM_KM, LIM_KM)
        ax.set_ylim(-LIM_KM, LIM_KM)
        ax.set_aspect("equal")
        ax.set_xlabel("km al este del cráter")
        ax.set_ylabel("km al norte del cráter")
        hl = datetime.strptime(dia, "%Y-%m-%d") + timedelta(minutes=10 * s) - timedelta(hours=3)
        ax.set_title(f"Nevados de Chillán {dia[8:10]}-{dia[5:7]}  {M.hhmm(s)} UTC ({hl:%H:%M} Chile, UTC-3)",
                     fontsize=11)
        sv = "" if not np.isfinite(S[s]) else f"   S {S[s]:+.2f} K (umbral {U[s]:+.2f})"
        fig.text(0.02, 0.045, f"Detector S22a: {txt_det}{sv}", color=col_det, fontsize=9)
        fig.text(0.02, 0.015, txt_v + f"   |   morado: M1 ≤ {UMBRAL_MORADO:.0f} K   |   {rol}", color=col_v,
                 fontsize=9)
        fig.tight_layout(rect=(0, 0.06, 1, 1))
        fn = os.path.join(TRABAJO, f"{dia}_{s:03d}.png")
        fig.savefig(fn)
        plt.close(fig)
        cuadros.append(imageio.imread(fn))
    out = os.path.join(SALIDA, f"s22a_detector_propio_vs_volcat_chillan_{dia}_10min.mp4")
    imageio.mimsave(out, cuadros, fps=3, macro_block_size=1)
    print(f"{dia}: {len(cuadros)} cuadros, detector dispara en {n_f}, VOLCAT con píxeles en {n_v} -> {out}")


if __name__ == "__main__":
    for dia in sys.argv[1:]:
        dibujar(dia)
