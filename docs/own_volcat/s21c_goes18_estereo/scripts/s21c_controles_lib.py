r"""S21c: fraccion despejada E1 por cuadro (la misma regla y los mismos cubos ACMF que s21c_controles.py)."""
from datetime import datetime, timedelta

import numpy as np

LATLON = r"D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\latlon.npz"
DEMV = r"D:\goes_cache\etapa3_chillan\dem_ventana.npz"
CUBOS = [(r"D:\goes_notas\s17\h23\acm_oct.npz", r"D:\goes_notas\s17\h23\cubo_oct.npz"),
         (r"D:\goes_notas\s18\h24\acm_oct.npz", r"D:\goes_notas\s18\h24\cubo_oct.npz")]


def frac_por_cuadro():
    lat, lon = (np.load(LATLON)[k] for k in ("lat", "lon"))
    zdem = np.load(DEMV)["zdem"]
    la, lo, h = -36.86, -71.38, 3212
    p1, p2 = np.radians(lat), np.radians(la - 0.93 * h / 1000.0 / 111.2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lo - lon) / 2) ** 2
    d = (2 * 6371.0 * np.arcsin(np.sqrt(a))).ravel()
    bajo = np.where((d >= 10.0) & (d <= 30.0) & (zdem.ravel() < 1300.0))[0]
    frac = {}
    for fa, fc in CUBOS:
        acm = np.load(fa)["acm"]
        t0 = datetime.strptime(str(np.load(fc)["t0"]), "%Y-%m-%d")
        clara = (acm[:, bajo] <= 1).mean(1)
        falta = (acm[:, bajo] > 3).all(1)
        for i in range(acm.shape[0]):
            frac[t0 + timedelta(minutes=10 * i)] = None if falta[i] else float(clara[i])
    return frac
