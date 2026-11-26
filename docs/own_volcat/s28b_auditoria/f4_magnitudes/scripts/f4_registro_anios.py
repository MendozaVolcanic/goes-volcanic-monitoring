r"""S28b F4: ¿la ventana de 2024 (GOES-16), 2025 y 2026 (GOES-19) cae sobre el mismo terreno, píxel por píxel?

Por qué: I4 de S23/S25b correlaciona la BT11 media de noches despejadas entre años (0,99), pero un campo suave
correlaciona alto aunque esté corrido un píxel. Aquí se busca el corrimiento (filas, columnas) de -2 a +2 que maximiza
la correlación del campo de noche despejada SIN su parte suave (resta de un promedio móvil de 7 x 7: queda el relieve
fino, que no se mueve entre años). Si el máximo no está en (0, 0), las grillas no coinciden.
Sólo lee cubos ya armados (21-09 a 21-11 de 2024 y 2025; 21-09 a 21-11-2026). Nada posterior al 24-11-2026.

Uso: python -I f4_registro_anios.py
"""
import json
import os
import sys

import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s23_fondo_2025", "scripts"))
import s23_medir as S  # noqa: E402

B, M, H24 = S.B, S.M, S.H24
NY, NX = M.NY, M.NX
OUT = r"D:\goes_notas\s28\s28b\f4"
NOCHE = range(18, 54)


def media_noche(bt, acm):
    e1 = H24.despejada("chillan", acm)
    sel = [(d, s) for d in range(bt.shape[0]) for s in NOCHE if e1[d, s] and np.isfinite(bt[d, s]).any()]
    m = np.nanmean(np.array([np.asarray(bt[d, s]) for d, s in sel]), 0).reshape(NY, NX)
    return m, len(sel)


def fino(m):
    return m - ndimage.uniform_filter(m, 7, mode="nearest")


def mejor(a, b):
    out = {}
    for di in range(-2, 3):
        for dj in range(-2, 3):
            x = a[2 + di:NY - 2 + di, 2 + dj:NX - 2 + dj]
            y = b[2:NY - 2, 2:NX - 2]
            ok = np.isfinite(x) & np.isfinite(y)
            out[(di, dj)] = float(np.corrcoef(x[ok], y[ok])[0, 1])
    k = max(out, key=out.get)
    return {"mejor_corrimiento_filas_cols": list(k), "corr_mejor": round(out[k], 4), "corr_0_0": round(out[(0, 0)], 4),
            "corr_vecinos": {f"{a_},{b_}": round(v, 4) for (a_, b_), v in out.items() if abs(a_) + abs(b_) == 1}}


def main():
    bt25 = np.load(os.path.join(S.TRAB, "r25_bt11.npy"), mmap_mode="r")
    acm25 = np.load(S._npy("acm"))
    bt26 = np.load(os.path.join(B.TRAB, "dev_bt11.npy"), mmap_mode="r")
    acm26 = np.load(os.path.join(B.TRAB, "dev_acm.npy"))
    bt24 = np.load(r"D:\goes_notas\s25\s25b_2024\cubo\r24_bt11.npy", mmap_mode="r")
    acm24 = np.load(r"D:\goes_notas\s25\s25b_2024\cubo\r24_acm.npy")
    m24, n24 = media_noche(bt24, acm24)
    m25, n25 = media_noche(bt25, acm25)
    m26, n26 = media_noche(bt26, acm26)
    f24, f25, f26 = fino(m24), fino(m25), fino(m26)
    res = {"cuadros_noche_despejada": {"2024": n24, "2025": n25, "2026": n26},
           "2024_vs_2025": mejor(f24, f25), "2026_vs_2025": mejor(f26, f25), "2024_vs_2026": mejor(f24, f26)}
    # control positivo del instrumento: 2025 contra sí mismo corrido una fila tiene que dar mejor corrimiento (1, 0)
    sh = np.full_like(f25, np.nan)
    sh[1:] = f25[:-1]
    res["control_positivo_2025_corrido_1_fila"] = mejor(sh, f25)
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "f4_registro_anios.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
