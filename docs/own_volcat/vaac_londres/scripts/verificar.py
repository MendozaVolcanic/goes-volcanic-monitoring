"""Cotejo independiente de analisis.py para tres configuraciones (L0_C14, L2_C14_T255, L3_C14_T255).

Por que: un error de vectorizacion (eje equivocado, coherencia mal contada, beta con la banda cambiada)
daria un veredicto falso con apariencia de numero. Aqui todo se rehace a mano y por pixel, sin
ndimage, sin beta_ratios.py y sin las funciones de analisis.py: Planck propio, cielo despejado propio,
coherencia 3x3 y objetos 8-conexos con bucles. Compara deteccion y numero de pixeles por scan con
resultados/por_scan.csv. Lento a proposito (solo C14).

Uso: python verificar.py
"""
import os, sys, json
from datetime import datetime, timedelta
from collections import deque
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rutas as R  # noqa: E402

co = json.load(open(R.PLANCK_PREV))


def rad(bt, c):
    fk1, fk2, bc1, bc2 = c
    return fk1 / (np.exp(fk2 / (bc1 + bc2 * bt)) - 1.0)


ll = np.load(R.LATLON); LAT, LON = ll["lat"], ll["lon"]
H, W = LAT.shape
VLAT, VLON = -36.86, -71.38
p1 = np.radians(VLAT)
DIST = 2 * 6371.0 * np.arcsin(np.sqrt(np.sin((np.radians(LAT) - p1) / 2) ** 2 +
                                      np.cos(p1) * np.cos(np.radians(LAT)) * np.sin(np.radians(LON - VLON) / 2) ** 2))
SNAP = set(open(R.SNAPSHOT).read().split())
HAS13 = set(os.listdir(R.CACHE13))


def esc(dt):
    k = f"{dt:%Y%m%d_%H%M}.npz"
    if k not in SNAP or k not in HAS13:
        return None
    z = np.load(os.path.join(R.CACHE_PREV, k))
    return z["b11"].astype(float), z["b14"].astype(float), z["b15"].astype(float)


def ref(dt):
    c = []
    for d in range(1, 11):
        for m in (-10, 0, 10):
            e = esc(dt - timedelta(days=d) + timedelta(minutes=m))
            if e is not None:
                c.append(e)
    if len(c) < 3:
        return None
    out = [np.full((H, W), np.nan) for _ in range(3)]
    for i in range(H):
        for j in range(W):
            vals = [(e[1][i, j], e[0][i, j], e[2][i, j]) for e in c if np.isfinite(e[1][i, j])]
            vals.sort(key=lambda v: -v[0])
            top = vals[:3]
            if not top:
                continue
            out[1][i, j] = np.median([v[0] for v in top]); out[0][i, j] = np.median([v[1] for v in top])
            out[2][i, j] = np.median([v[2] for v in top])
    return out


def mask(e, r, modo, tref=255.0):
    b11, b14, b15 = e
    m = np.zeros((H, W), bool)
    for i in range(H):
        for j in range(W):
            a, b, c = b14[i, j], b11[i, j], b15[i, j]
            if not (np.isfinite(a) and np.isfinite(b) and np.isfinite(c)):
                continue
            btd = a - c
            if btd < -2.0:
                m[i, j] = True; continue
            tent = (btd + (a - b) < 1.5) or (-2.0 <= btd <= -0.7)
            if not tent:
                continue
            if modo == "L0":
                m[i, j] = True; continue
            medible = False; quita = False
            if r is not None:
                ra, rb, rc = r[1][i, j], r[0][i, j], r[2][i, j]
                if all(np.isfinite([ra, rb, rc])) and a < ra and b < rb and c < rc:
                    e10 = (rad(a, co["C14"]) - rad(ra, co["C14"])) / (rad(tref, co["C14"]) - rad(ra, co["C14"]))
                    e87 = (rad(b, co["C11"]) - rad(rb, co["C11"])) / (rad(tref, co["C11"]) - rad(rb, co["C11"]))
                    e12 = (rad(c, co["C15"]) - rad(rc, co["C15"])) / (rad(tref, co["C15"]) - rad(rc, co["C15"]))
                    e10, e87, e12 = [min(max(x, 1e-4), 1 - 1e-6) for x in (e10, e87, e12)]
                    if e10 >= 0.02:
                        medible = True
                        b87 = np.log(1 - e87) / np.log(1 - e10); b12 = np.log(1 - e12) / np.log(1 - e10)
                        quita = b87 <= 0.7 or b87 >= 1.2 or b12 > 4.2645 - 5.823 * b87 + 2.446 * b87 ** 2
            if modo == "L2":
                m[i, j] = medible and not quita
            else:
                m[i, j] = not (medible and quita)
    if modo == "L0":
        return m
    out = np.zeros((H, W), bool)
    for i in range(H):
        for j in range(W):
            if not m[i, j]:
                continue
            n = sum(m[y, x] for y in range(i - 1, i + 2) for x in range(j - 1, j + 2) if 0 <= y < H and 0 <= x < W)
            out[i, j] = n >= 6
    return out


def anclado(m):
    vis = np.zeros((H, W), bool)
    for i in range(H):
        for j in range(W):
            if not m[i, j] or vis[i, j]:
                continue
            q = deque([(i, j)]); vis[i, j] = True; px = []
            while q:
                y, x = q.popleft(); px.append((y, x))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < H and 0 <= xx < W and m[yy, xx] and not vis[yy, xx]:
                            vis[yy, xx] = True; q.append((yy, xx))
            if len(px) >= 2 and any(DIST[y, x] <= 10.0 for y, x in px):
                return True
    return False


if __name__ == "__main__":
    df = pd.read_csv(os.path.join(R.RESULTADOS, "por_scan.csv"))
    slots = sorted(df.slot.unique())
    # todos los positivos, y una muestra fija de negativos y 16-11 (cada 3er slot) para que no tarde horas
    grupos = df.drop_duplicates("slot").set_index("slot").grupo.to_dict()
    elegir = [s for s in slots if grupos[s].startswith("pos")] + \
             [s for i, s in enumerate(s_ for s_ in slots if not grupos[s_].startswith("pos")) if i % 3 == 0]
    dif = 0; n = 0
    for s in elegir:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M"); e = esc(dt); r = ref(dt)
        for modo, cfg in (("L0", "L0_C14"), ("L2", "L2_C14_T255"), ("L3", "L3_C14_T255")):
            m = mask(e, r, modo)
            row = df[(df.slot == s) & (df.cfg == cfg)].iloc[0]
            ok = (bool(row.det) == anclado(m)) and (int(row.npx) == int(m.sum()))
            n += 1
            if not ok:
                dif += 1
                print("DIFIERE", s, cfg, "analisis:", bool(row.det), int(row.npx), "verificar:", anclado(m), int(m.sum()), flush=True)
    print(f"cotejados {n} (scan x config) en {len(elegir)} scans; diferencias: {dif}", flush=True)
