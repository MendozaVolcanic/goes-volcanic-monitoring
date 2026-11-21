"""Pruebas A (corrimiento de la huella) y B (8,5 um) segun criterio_corrimiento_y_8p5_2026-11-17.md.
Solo lectura sobre el estudio del detector."""
import sys, os
from datetime import timedelta
import numpy as np
D = r"C:\Users\nmend\AppData\Local\Temp\claude\d6ea8719dcf88502\536a0873-47fb-4b33-9ee5-de0197c3f321\scratchpad\det"
sys.path.insert(0, D)
import comun as C  # noqa
from variantes_mascara import referencia, get  # noqa

H = np.load(os.path.join(D, "volcat", "huellas.npz"))
NEGD = C.NEG_AJ_DIAS + C.NEG_PR_DIAS
S = 5


def anom(dt):
    s = get(dt)
    if s is None:
        return None
    r = referencia(dt, 10, 3)
    if r is None:
        return None
    return {"dT": s["b14"] - r["b14"],
            "dB": (s["b14"] - s["b15"]) - (r["b14"] - r["b15"]),
            "d85": (s["b11"] - s["b14"]) - (r["b11"] - r["b14"])}


def nulo_para(dt):
    for d in NEGD:
        t = dt.replace(day=d)
        # negativos estan a :00/:20/:40; tomar el slot de 20 min mas cercano
        t = t - timedelta(minutes=t.minute % 20)
        a = anom(t)
        if a is not None:
            return a, t
    return None, None


def shift(m, dy, dx):
    out = np.zeros_like(m)
    ys, xs = np.nonzero(m)
    ys2, xs2 = ys + dy, xs + dx
    ok = (ys2 >= 0) & (ys2 < m.shape[0]) & (xs2 >= 0) & (xs2 < m.shape[1])
    out[ys2[ok], xs2[ok]] = True
    return out


def auc(pos, neg):
    """P(pos < neg): anomalia mas negativa en la huella que en el nulo."""
    pos, neg = np.asarray(pos), np.asarray(neg)
    allv = np.concatenate([pos, neg]); r = allv.argsort().argsort() + 1
    rp = r[:len(pos)].sum()
    u = rp - len(pos) * (len(pos) + 1) / 2
    return 1 - u / (len(pos) * len(neg))


posiciones = C.POS_AJ + C.POS_PR
grid = {k: np.full((len(posiciones), 2 * S + 1, 2 * S + 1), np.nan) for k in ("pos", "nul")}
pix = {"pos": {"dT": [], "dB": [], "d85": []}, "nul": {"dT": [], "dB": [], "d85": []}}
usados = []
for i, dt in enumerate(posiciones):
    k = C.key(dt)
    if k not in H.files or not H[k].any():
        continue
    a = anom(dt); n, tn = nulo_para(dt)
    if a is None or n is None:
        continue
    m = H[k]; usados.append((dt, tn, int(m.sum())))
    for v in pix["pos"]:
        pix["pos"][v] += list(a[v][m]); pix["nul"][v] += list(n[v][m])
    for iy, dy in enumerate(range(-S, S + 1)):
        for ix, dx in enumerate(range(-S, S + 1)):
            ms = shift(m, dy, dx)
            if ms.sum() == 0:
                continue
            grid["pos"][i, iy, ix] = np.nanmean(a["dT"][ms])
            grid["nul"][i, iy, ix] = np.nanmean(n["dT"][ms])

print("cuadros usados", len(usados), "px huella", sum(u[2] for u in usados))
gp = np.nanmedian(grid["pos"], axis=0); gn = np.nanmedian(grid["nul"], axis=0); g = gp - gn
np.set_printoptions(precision=2, suppress=True, linewidth=200)
print("filas = dy (-5 norte .. +5 sur); columnas = dx (-5 oeste .. +5 este)")
print("mediana dBT11 positivos\n", gp)
print("mediana dBT11 nulo\n", gn)
print("positivos - nulo\n", g)
iy, ix = np.unravel_index(np.nanargmin(g), g.shape)
print("minimo en dy=%d dx=%d: %.2f K; en (0,0): %.2f K" % (iy - S, ix - S, g[iy, ix], g[S, S]))
# por dia
for dia in (8, 10, 11, 14):
    idx = [j for j, dt in enumerate(posiciones) if dt.day == dia]
    gd = np.nanmedian(grid["pos"][idx], 0) - np.nanmedian(grid["nul"][idx], 0)
    jy, jx = np.unravel_index(np.nanargmin(gd), gd.shape)
    print("dia %02d (n=%d): minimo dy=%d dx=%d %.2f K; (0,0) %.2f K; columna dx=0, dy=-2..+4: %s"
          % (dia, len(idx), jy - S, jx - S, gd[jy, jx], gd[S, S], np.round(gd[S - 2:S + 5, S], 2)))
print("\nPrueba B (huella sin corrimiento)")
for v in ("dB", "d85", "dT"):
    print(v, "AUC=%.3f" % auc(pix["pos"][v], pix["nul"][v]),
          "mediana pos %.2f nulo %.2f" % (np.nanmedian(pix["pos"][v]), np.nanmedian(pix["nul"][v])))
np.savez(os.path.join(os.path.dirname(os.path.abspath(__file__)), "prueba_AB.npz"), gp=gp, gn=gn,
         gpos=grid["pos"], gnul=grid["nul"])
