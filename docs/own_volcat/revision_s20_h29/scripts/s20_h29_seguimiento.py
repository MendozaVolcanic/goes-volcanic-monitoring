r"""Revision S20 de H29: reproduce M1 con codigo propio y prueba si la BTD baja sigue a la huella cuadro a cuadro.

Criterio: docs/own_volcat/revision_s20_h29/criterio_2026-11-23.md (commit 1b430f0, antes de medir).
No importa nada de los scripts de H29. Lee de D: (solo lectura) y escribe numeros agregados en resultados/.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, REPO)
from src.process import volcat_colorbar as vc  # noqa: E402

RES = os.path.join(os.path.dirname(AQUI), "resultados")
os.makedirs(RES, exist_ok=True)
CUBO = r"D:\goes_notas\s17\h23\cubo_nov.npz"
HUELLA = r"D:\goes_notas\s19\h29\huella_0811.npz"
DEM = r"D:\goes_cache\etapa3_chillan\dem_ventana.npz"
LATLON = r"D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\latlon.npz"
FRAMES = r"D:\goes_notas\volcat_validacion_copia_2026-11-21\Chile_Central_2_km\frames"
DIA = 7            # 2026-11-08 en un cubo que empieza el 01-11
CRATER = (-36.863, -71.377)
rng = np.random.default_rng(20261123)

LAT, LON = (np.load(LATLON)[k] for k in ("lat", "lon"))
Z = np.load(DEM)["zdem"]
NY, NX = LAT.shape


def dist_km(la, lo):
    p1, p2 = math.radians(CRATER[0]), np.radians(la)
    a = np.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * np.cos(p2) * np.sin(np.radians(lo - CRATER[1]) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


DIST = dist_km(LAT, LON)


def bt(rad, co):
    fk1, fk2, bc1, bc2 = co
    with np.errstate(invalid="ignore", divide="ignore"):
        return (fk2 / np.log(fk1 / rad + 1.0) - bc1) / bc2


def rad(T, co):
    fk1, fk2, bc1, bc2 = co
    return fk1 / np.expm1(fk2 / (bc1 + bc2 * T))


# ---------- datos del dia ----------
cz = np.load(CUBO)
assert str(cz["t0"]) == "2026-11-01"
r14 = cz["rad14"][DIA * 144:(DIA + 1) * 144].astype("float64")
r15 = cz["rad15"][DIA * 144:(DIA + 1) * 144].astype("float64")
co14, co15 = cz["co14"], cz["co15"]
B11 = bt(r14, co14)
B12 = bt(r15, co15)

hz = np.load(HUELLA)
slots = sorted(int(k[4:6]) * 6 + int(k[6:8]) // 10 for k in hz.files if k.startswith("h14_"))
H = {s: hz[f"h14_{s // 6:02d}{(s % 6) * 10:02d}"] for s in slots}


def hhmm(s):
    return f"{s // 6:02d}:{(s % 6) * 10:02d}"


# ---------- comprobacion de la huella contra mi decodificacion del PNG ----------
DP = math.degrees(72.80000305175781 / 206264.796875)
LAT0 = -31.8007698059082 + 36 * DP
LON0 = 278.9210815429688 - 360.0
RR = np.rint((LAT0 - LAT) / DP).astype(int)
CC = np.rint((LON - LON0) / DP).astype(int)


def mi_huella(s):
    fn = os.path.join(FRAMES, f"2026-11-08_{s // 6:02d}-{(s % 6) * 10:02d}-00.png")
    if not os.path.exists(fn):
        cands = [f for f in os.listdir(FRAMES) if f.startswith(f"2026-11-08_{s // 6:02d}-{(s % 6) * 10:02d}")
                 and "_annot" not in f]
        fn = os.path.join(FRAMES, cands[0])
    a = np.asarray(Image.open(fn).convert("RGB"), dtype="float64")
    hmap = int(vc.MAP_FRAC * a.shape[0])
    bins = vc.palette_bins(a[hmap:])
    m = a[:hmap]
    sat = vc._saturation(m) >= 0.2
    ok = np.zeros(sat.shape, bool)
    c = vc.classify_pixels(m[sat], bins)
    ok[sat] = c["ok"]
    nom = np.zeros((NY, NX), bool)
    ins = (RR >= 0) & (RR < hmap) & (CC >= 0) & (CC < ok.shape[1])
    nom[ins] = ok[RR[ins], CC[ins]]
    # corrimiento H14: 1 fila al N (fila - 1) y 1 columna al O (columna - 1)
    out = np.zeros_like(nom)
    out[:-1, :-1] = nom[1:, 1:]
    return out


chequeo = {}
for s in (121, 129):   # 20:10 y 21:30
    mine = mi_huella(s)
    lej = DIST > 30
    chequeo[hhmm(s)] = {"mia_lejos": int((mine & lej).sum()), "h29_lejos": int((H[s] & lej).sum()),
                        "iguales_en_ventana": bool(np.array_equal(mine[2:-2, 2:-2], H[s][2:-2, 2:-2]))}
print("chequeo huella:", chequeo)

# ---------- M1 propio ----------
FOOT = {}  # union de huellas a +-20 min, dilatada 4 px (Chebyshev)
est = np.ones((9, 9), bool)
for s in range(144):
    u = np.zeros((NY, NX), bool)
    for q in range(s - 2, s + 3):
        if q in H:
            u |= H[q]
    FOOT[s] = binary_dilation(u, structure=est) if u.any() else u


def m1_cuadro(s, b11, b12, pos):
    """M1 de las posiciones pos (lista de (r, c)) en el cuadro s."""
    btd = b11 - b12
    cand = ~FOOT[s] & np.isfinite(btd)
    cb11, cz, cbtd = b11[cand], Z[cand], btd[cand]
    out = []
    for r, c in pos:
        if not np.isfinite(btd[r, c]):
            out.append(np.nan)
            continue
        k = (np.abs(cb11 - b11[r, c]) <= 0.5) & (np.abs(cz - Z[r, c]) <= 300)
        out.append(btd[r, c] - np.median(cbtd[k]) if k.sum() >= 10 else np.nan)
    return np.array(out)


def poblacion(dmin, s0, s1):
    return {s: [tuple(p) for p in np.argwhere(H[s] & (DIST > dmin))] for s in slots if s0 <= s <= s1}


lejos = poblacion(30, 121, 132)
vals = np.concatenate([m1_cuadro(s, B11[s], B12[s], p) for s, p in lejos.items() if p])
paso1 = {"n_pixel_cuadro": int(np.isfinite(vals).sum()), "mediana_M1": float(np.nanmedian(vals)),
         "h29": -0.372}
paso1["reproducido"] = abs(paso1["mediana_M1"] - paso1["h29"]) <= 0.05
print("paso 1:", paso1)


# ---------- paso 2: seguimiento ----------
def prueba(pob, delta_btd=0.0, nperm=10000):
    F = [s for s, p in pob.items() if p]
    U = sorted({p for s in F for p in pob[s]})
    M = {}
    for s in F:
        b12 = B12[s].copy()
        if delta_btd:
            for r, c in pob[s]:
                b12[r, c] += delta_btd
        M[s] = dict(zip(U, m1_cuadro(s, B11[s], b12, U)))

    def D(t, S):
        S = set(S)
        a = [M[t][p] for p in U if p in S and np.isfinite(M[t][p])]
        b = [M[t][p] for p in U if p not in S and np.isfinite(M[t][p])]
        return np.median(a) - np.median(b) if a and b else np.nan

    tabla = np.array([[D(t, pob[u]) for u in F] for t in F])   # fila = cuadro, columna = huella de que cuadro
    obs = np.nanmedian(np.diag(tabla))
    idx = np.arange(len(F))
    null = np.array([np.nanmedian(tabla[idx, rng.permutation(idx)]) for _ in range(nperm)])
    return {"cuadros": len(F), "posiciones_U": len(U), "T": float(obs), "p": float((null <= obs).mean()),
            "D_por_cuadro": {hhmm(t): (None if not np.isfinite(tabla[i, i]) else round(float(tabla[i, i]), 3))
                             for i, t in enumerate(F)}}


principal = prueba(lejos)
print("paso 2 principal:", principal)
pos = [prueba(lejos, delta_btd=0.33, nperm=2000)["p"] for _ in range(200)]
potencia = float(np.mean(np.array(pos) <= 0.05))
print("potencia (BTD -0,33 K en S_t):", potencia, "p mediana inyectada", float(np.median(pos)))
sens15 = prueba(poblacion(15, 92, 132))
print("sensibilidad > 15 km:", {k: v for k, v in sens15.items() if k != "D_por_cuadro"})

p = principal["p"]
if p <= 0.05:
    ver = "SIGUE A LA HUELLA"
elif p > 0.20:
    ver = "NO SIGUE A LA HUELLA" if potencia >= 0.5 else "SIN PODER"
else:
    ver = "NO CONCLUYENTE"
print("VEREDICTO:", ver)
json.dump({"chequeo_huella": chequeo, "paso1": paso1, "paso2": principal, "potencia": potencia,
           "p_inyectado_mediana": float(np.median(pos)), "sensibilidad_15km": sens15, "veredicto": ver},
          open(os.path.join(RES, "s20_h29_seguimiento.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
