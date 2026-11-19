"""H9: figura de lectura. Arriba, anomalia A (BT7 - BT14 crater contra anillo) en cuadros de noche y crepusculo con
crater visible, en Chillan y en los dos controles, con el umbral T99 y los cuadros VOLCAT positivos. Abajo, destellos
GLM por dia a <= 30 km del crater real y dias con positivos VOLCAT. Lee resultados/frames_calor.csv y
resultados/glm_destellos_chillan.csv. Salida: resultados/h9_serie.png
"""
import os, re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "resultados")
import analisis_calor as ac  # noqa: E402


def main():
    df = pd.read_csv(os.path.join(RES, "frames_calor.csv"), parse_dates=["dt"]).set_index("dt")
    txt = open(os.path.join(RES, "h9_calor_resultado.txt"), encoding="utf-8").read()
    T99 = float(re.search(r"= ([\d.]+) K ===", txt).group(1))
    N = df.sza >= 80
    vis = {s: ac.visibilidad(df, s, ac.VIS_K) & df.leido for s in ac.SITIOS}
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True, gridspec_kw=dict(height_ratios=[3, 1]))
    col = {"chillan": "#c0392b", "antuco": "#2c7fb8", "longavi": "#7fbf7b"}
    nom = {"chillan": "Nevados de Chillán", "antuco": "Antuco (control)", "longavi": "Nevado de Longaví (control)"}
    for s in ("antuco", "longavi", "chillan"):
        m = N & vis[s]
        a1.plot(df.index[m], df.loc[m, f"A_{s}"], ".", ms=3, color=col[s], label=f"{nom[s]} ({int(m.sum())} cuadros)", alpha=0.8)
    pn = (df.clase == "P") & N & vis["chillan"]
    a1.plot(df.index[pn], df.loc[pn, "A_chillan"], "o", mfc="none", mec="k", ms=7, label="cuadro con objeto VOLCAT anclado (noche)")
    a1.axhline(T99, color="0.4", ls="--", lw=1); a1.text(df.index.min(), T99 + 0.4, f"p99 de los controles = {T99:.1f} K", fontsize=8, color="0.3")
    a1.set_ylabel("A = (BT3,9 − BT11,2) cráter\nmenos anillo (K)")
    a1.set_title("Calor en el cráter de noche y crepúsculo (GOES-19 ABI, 2 km) y detecciones VOLCAT", fontsize=10)
    a1.legend(fontsize=7.5, loc="upper left"); a1.grid(alpha=0.3)
    g = pd.read_csv(os.path.join(RES, "glm_destellos_chillan.csv"), parse_dates=["desde", "hasta"])
    g = g[g.d_km <= 30]
    gd = g.groupby(g.desde.dt.floor("D")).size()
    a2.bar(gd.index + pd.Timedelta(hours=12), gd.values, width=0.8, color="#8856a7", label="destellos GLM a ≤ 30 km del cráter")
    dp = df.index[df.clase == "P"].floor("D").unique()
    for d in dp:
        a2.axvspan(d, d + pd.Timedelta(days=1), color="#f4a582", alpha=0.35, lw=0)
    a2.plot([], [], "s", color="#f4a582", alpha=0.6, label="día con objeto VOLCAT anclado")
    a2.set_ylabel("destellos / día"); a2.legend(fontsize=7.5, loc="upper right"); a2.grid(alpha=0.3)
    a2.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m")); a2.set_xlabel("fecha (UTC), 2026")
    fig.tight_layout(); fig.savefig(os.path.join(RES, "h9_serie.png"), dpi=130)
    print("ok", os.path.join(RES, "h9_serie.png"))


if __name__ == "__main__":
    main()
