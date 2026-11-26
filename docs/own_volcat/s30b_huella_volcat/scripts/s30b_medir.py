r"""S30b: ¿los disparos del detector S26a caen donde VOLCAT dibuja la pluma? Implementa criterio_2026-11-26.md
(commit eef0b0f, empujado antes de cruzar un disparo con una huella).

Por qué: S26a "alcanza" 63 de 93 cuadros P sólo por la hora; aquí se mira la posición (tajada del anillo, 11 píxeles de
la zona, píxeles y rumbo) contra la huella de VOLCAT del mismo cuadro, con nulos que mueven días enteros (rumbo rotado
y huella de otro día), porque los disparos vienen en rachas por día (S28b).

Lee la tabla por cuadro de S26a (D:\goes_notas\s26\s26a\tabla_2026.csv, p* 4,75, hasta el 24-11) y los PNG de VOLCAT
de D: (licencia SSEC: nada de eso va al repo). Escribe resultados/s30b_resultado.json y resultados/s30b_por_cuadro.csv
(sólo cifras), y en D:\goes_notas\s30\s30b\huellas.npz las huellas en la grilla ABI (no van al repo).

Uso: python -I -B s30b_medir.py
"""
import csv
import json
import os
import sys
import warnings
from collections import defaultdict

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "h29_pluma_0811", "scripts"))
sys.path.insert(0, os.path.join(OV, "s22a_detector_sectores", "scripts"))
import h29_comun as C29  # noqa: E402
import s22a_medir as M  # noqa: E402
import s22a_mapas as G  # noqa: E402

G.PNG_DIRS.append(r"D:\goes_notas\s22\s22b\volcat_png\frames")
G.PNG_DIRS.append(r"D:\goes_notas\s23\volcat_png\Chile_Central_2_km\frames")
TABLA = r"D:\goes_notas\s26\s26a\tabla_2026.csv"
TRAB = r"D:\goes_notas\s30\s30b"
ULTIMO_DIA = "2026-11-24"

# ---------- parámetros del criterio ----------
ANCLA_KM = 10.0          # §1: objeto anclado si toca 10 km del cráter
TOL_RUMBO = 30.0         # §2 secundaria
B_MC, SEMILLA = 9999, 0  # §3
ENUM_MAX = 20000         # §3: nulo R exacto si 12^n <= 20.000
MIN_CONF = 1000          # §3: configuraciones mínimas para que un nulo decida
P_MAX = 0.01
MIN_P, MIN_DIAS, MIN_FRAC = 10, 3, 0.5
DIF_NEG = 0.15           # §4 control negativo
REPRO = {"u": (63, 93), "a": (23, 54), "z": (42, 93)}

NPIX = M.NY * M.NX
AMASK = M.AMASK.ravel()
SECF = np.full(NPIX, -1, int)
SECF[M.AP] = M.SEC
ZONA = np.flatnonzero(((C29.DIST < 4.0) | M.BLOQUE).ravel())
ZSET = np.zeros(NPIX, bool)
ZSET[ZONA] = True
AZF = M.AZ.ravel()
XK, YK = M._x.ravel(), M._y.ravel()
ARBOL = cKDTree(np.c_[XK, YK])
DISTF = C29.DIST.ravel()


# ---------- tabla y comprobación de código ----------
def leer_tabla():
    T = defaultdict(dict)
    with open(TABLA, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            assert r["dia"] <= ULTIMO_DIA, "la tabla trae días posteriores al 24-11: no se mira"
            T[r["dia"]][M.slot(r["hora"])] = r
    return T


def comprobar(T):
    out = {}
    for k, ev, F in (("a", ("ev_a",), ("F_a",)), ("z", ("ev_z",), ("F_z",)), ("u", ("ev_a", "ev_z"), ("F_a", "F_z"))):
        ne = na = 0
        for dia, filas in T.items():
            for s, r in filas.items():
                if r["clase"] != "P" or not any(r[e] == "1" for e in ev):
                    continue
                ne += 1
                na += any(filas.get(t, {}).get(x) == "1" for t in (s - 1, s, s + 1) for x in F)
        out[k] = (na, ne)
    ok = all(out[k] == REPRO[k] for k in REPRO)
    print("comprobación de código:", out, "OK" if ok else "NO REPRODUCE", flush=True)
    if not ok:
        sys.exit("no reproduce S26a: se para")
    return out


# ---------- huellas ----------
def huella(dia, s):
    """(estado, índices planos de la huella anclada en la grilla ABI)."""
    ash, err = G.png_volcat(dia, s)
    if ash is None:
        return err, None
    lab, n = ndimage.label(ash, structure=np.ones((3, 3), int))
    if n == 0:
        return "vacía", np.array([], int)
    cerca = np.unique(lab[(C29.DIST <= ANCLA_KM) & (lab > 0)])
    h = np.flatnonzero(np.isin(lab, cerca[cerca > 0]).ravel())
    return ("ok" if len(h) else "vacía"), h


def rotar(h, j):
    if j == 0 or not len(h):
        return h
    th = np.radians(30.0 * j)
    x, y = XK[h], YK[h]
    xr = x * np.cos(th) + y * np.sin(th)      # acimut + th (horario desde el norte)
    yr = -x * np.sin(th) + y * np.cos(th)
    _, i = ARBOL.query(np.c_[xr, yr])
    return np.unique(i)


def dilatar(h):
    m = np.zeros((M.NY, M.NX), bool)
    m.flat[h] = True
    return ndimage.binary_dilation(m, np.ones((3, 3), bool)).ravel()


def rumbo_circ(az):
    if not len(az):
        return None
    a = np.radians(az)
    return float(np.degrees(np.arctan2(np.sin(a).mean(), np.cos(a).mean())) % 360)


def angdif(a, b):
    x = abs(a - b) % 360
    return min(x, 360 - x)


class Huella:
    """Descriptor de una huella, con sus 12 giros precalculados."""

    def __init__(self, h):
        self.h = h
        ring = h[AMASK[h]]
        self.secs = set(int(x) for x in SECF[ring])
        self.rumbo = rumbo_circ(AZF[ring])
        self.zona = bool(ZSET[h].any())
        self.npix, self.nring = len(h), len(ring)
        self.dil = [dilatar(rotar(h, j)) for j in range(12)]


# ---------- coincidencias ----------
def coincide(hu, dis, j=0):
    """dict de coincidencias para una huella (girada j·30°) y los disparos del cuadro."""
    c = {}
    if dis["Fa"]:
        secs = {(x + j) % 12 for x in hu.secs}
        c["a"] = any(k in secs for k in dis["Ka"])
        c["a_px"] = bool(hu.dil[j][dis["Ca"]].any()) if len(dis["Ca"]) else False
        c["a_rumbo"] = hu.rumbo is not None and any(
            angdif(30 * k + 15, (hu.rumbo + 30 * j) % 360) <= TOL_RUMBO for k in dis["Ka"])
    if dis["Fz"]:
        c["z"] = hu.zona                         # la zona no gira (criterio §3)
        c["z_px"] = bool(hu.dil[j][dis["Cz"]].any())
    if dis["Fa"] or dis["Fz"]:
        c["u"] = bool(c.get("a")) or bool(c.get("z"))
        c["u_px"] = bool(c.get("a_px")) or bool(c.get("z_px"))
    return c


def disparos(filas, s, ventana=(-1, 0, 1)):
    Ka, Ca, Cz, Fa, Fz = [], [], [], False, False
    for t in (s + v for v in ventana):
        r = filas.get(t)
        if r is None:
            continue
        if r["F_a"] == "1":
            Fa = True
            Ka.append(int(r["k_a"]))
            Ca += [int(x) for x in r["cola_a"].split(";") if x]
        if r["F_z"] == "1":
            Fz = True
            Cz += [int(r["px1"]), int(r["px2"])]
    return {"Fa": Fa, "Fz": Fz, "Ka": sorted(set(Ka)), "Ca": np.array(sorted(set(Ca)), int),
            "Cz": np.array(sorted(set(Cz)), int)}


# ---------- nulos ----------
def prueba(items, clave, donantes, rng, usar_R=True, usar_D=True):
    """items: lista de (dia, Huella, disparos). Devuelve T, n, días y los dos nulos."""
    ev = [(d, hu, di) for d, hu, di in items if clave in coincide(hu, di)]
    n = len(ev)
    T = sum(coincide(hu, di)[clave] for _, hu, di in ev)
    dias = sorted({d for d, _, _ in ev})
    nd = len(dias)
    out = {"n": n, "T": int(T), "frac": T / n if n else None, "dias": dias}
    if not n:
        return out
    idx = {d: i for i, d in enumerate(dias)}
    # tabla por día y giro: coincidencias con giro j
    if usar_R:
        tab = np.zeros((nd, 12), int)
        for d, hu, di in ev:
            for j in range(12):
                tab[idx[d], j] += coincide(hu, di, j)[clave]
        conf = 12 ** nd
        if conf <= ENUM_MAX:
            tot = np.zeros(1, int)
            for i in range(nd):
                tot = (tot[:, None] + tab[i][None, :]).ravel()
            pR, media, metodo = float((tot >= T).mean()), float(tot.mean()), f"exacto ({conf} combinaciones)"
        else:
            J = rng.integers(0, 12, size=(B_MC, nd))
            tot = tab[np.arange(nd)[None, :], J].sum(1)
            pR = float((1 + (tot >= T).sum()) / (B_MC + 1))
            media, metodo = float(tot.mean()), f"Monte Carlo B={B_MC}"
        out["R"] = {"p": pR, "esperado": media, "frac_esperada": media / n, "configuraciones": conf,
                    "decide": conf >= MIN_CONF, "metodo": metodo}
    if usar_D:
        pool = {d: [hu for hu in v] for d, v in donantes.items()}
        cand = {d: [x for x in pool if x != d] for d in dias}
        conf = int(np.prod([len(cand[d]) for d in dias], dtype=float))
        tot = np.zeros(B_MC, int)
        for b in range(B_MC):
            t = 0
            don = {d: cand[d][rng.integers(len(cand[d]))] for d in dias}
            for d, hu, di in ev:
                lst = pool[don[d]]
                t += coincide(lst[rng.integers(len(lst))], di).get(clave, False)
            tot[b] = t
        pD = float((1 + (tot >= T).sum()) / (B_MC + 1))
        out["D"] = {"p": pD, "esperado": float(tot.mean()), "frac_esperada": float(tot.mean()) / n,
                    "configuraciones_dia": conf, "decide": conf >= MIN_CONF, "metodo": f"Monte Carlo B={B_MC}"}
    return out


def veredicto(r, orc, parte):
    """Criterio §5."""
    if r["n"] < MIN_P or len(r["dias"]) < MIN_DIAS:
        return "NO DECIDIBLE (pocos cuadros o días)"
    if parte == "z":
        if not r["D"]["decide"] or orc["D"]["p"] > P_MAX:
            return "NO DECIDIBLE (el oráculo no separa contra el nulo D)"
        if r["D"]["p"] <= P_MAX:
            return "MISMA PLUMA" if r["frac"] >= MIN_FRAC else "MISMA PLUMA, PARCIAL"
        return "MISMO MOMENTO"
    if not r["R"]["decide"] or orc["R"]["p"] > P_MAX:
        return "NO DECIDIBLE (el oráculo no separa contra el nulo R)"
    pR, pD = r["R"]["p"], r["D"]["p"]
    d_ok = r["D"]["decide"] and orc["D"]["p"] <= P_MAX
    if pR <= P_MAX and pD <= P_MAX and r["D"]["decide"]:
        return "MISMA PLUMA" if r["frac"] >= MIN_FRAC else "MISMA PLUMA, PARCIAL"
    if pR <= P_MAX and not d_ok:
        return "MISMO RUMBO, NO SEPARABLE"
    if pR <= P_MAX:
        return "MISMO RUMBO HABITUAL"
    return "MISMO MOMENTO"


def oraculo_disparos(hn):
    """Disparos del oráculo a partir de la huella vecina (criterio §4)."""
    ring = hn.h[AMASK[hn.h]]
    Ka = []
    if len(ring):
        cnt = np.bincount(SECF[ring], minlength=12)
        Ka = [int(np.argmax(cnt))]
    return {"Fa": bool(Ka), "Fz": hn.zona, "Ka": Ka, "Ca": np.array([], int), "Cz": np.array([], int)}


# ---------- medir ----------
def medir():
    os.makedirs(RES, exist_ok=True)
    os.makedirs(TRAB, exist_ok=True)
    T = leer_tabla()
    repro = comprobar(T)
    # huellas de todos los P y de sus vecinos
    cache, estados = {}, defaultdict(int)

    def H(dia, s):
        if (dia, s) not in cache:
            st, h = huella(dia, s) if 0 <= s < 144 else ("fuera", None)
            cache[(dia, s)] = (st, Huella(h) if st == "ok" else None)
        return cache[(dia, s)]

    P = [(dia, s) for dia in sorted(T) for s in sorted(T[dia]) if T[dia][s]["clase"] == "P"]
    hP = {}
    for dia, s in P:
        st, hu = H(dia, s)
        estados[st] += 1
        if hu is not None:
            hP[(dia, s)] = hu
    print("estado de las huellas P:", dict(estados), flush=True)
    donantes = defaultdict(list)
    for (dia, s), hu in hP.items():
        donantes[dia].append(hu)
    np.savez_compressed(os.path.join(TRAB, "huellas.npz"),
                        **{f"{d}_{s:03d}": hu.h for (d, s), hu in hP.items()})

    items, filas_csv, orc_items = [], [], []
    for (dia, s), hu in hP.items():
        di = disparos(T[dia], s)
        items.append((dia, hu, di, s))
        c = coincide(hu, di)
        filas_csv.append({"dia": dia, "hora": M.hhmm(s), "periodo": "noche" if s < 72 else "dia",
                          "huella_px": hu.npix, "huella_px_anillo": hu.nring,
                          "huella_tajadas": " ".join(str(x) for x in sorted(hu.secs)),
                          "huella_rumbo": None if hu.rumbo is None else round(hu.rumbo, 1),
                          "huella_toca_zona": int(hu.zona), "F_anillo": int(di["Fa"]),
                          "tajadas_disparo": " ".join(str(x) for x in di["Ka"]), "F_zona": int(di["Fz"]),
                          **{f"coincide_{k}": (int(v) if v is not None else "") for k, v in
                             ((k, c.get(k)) for k in ("u", "a", "z", "u_px", "a_px", "z_px", "a_rumbo"))}})
        # oráculo: huella vecina s-1, si no s+1
        hn = None
        for t in (s - 1, s + 1):
            st, x = H(dia, t)
            if x is not None:
                hn = x
                break
        if hn is not None:
            orc_items.append((dia, hu, oraculo_disparos(hn), s))

    rng = np.random.default_rng(SEMILLA)
    sel = {"todo": lambda s: True, "dia": lambda s: s >= 72, "noche": lambda s: s < 72}
    out = {"criterio": "criterio_2026-11-26.md (eef0b0f)", "comprobacion_codigo": repro,
           "huellas_P": dict(estados), "P_con_huella": len(hP), "resultados": {}, "oraculo": {}}
    for per, f in sel.items():
        its = [(d, hu, di) for d, hu, di, s in items if f(s)]
        ois = [(d, hu, di) for d, hu, di, s in orc_items if f(s)]
        bloque, borc = {}, {}
        for clave, usaR in (("u", True), ("a", True), ("z", False), ("u_px", True), ("a_px", True),
                            ("z_px", True), ("a_rumbo", True)):
            bloque[clave] = prueba(its, clave, donantes, rng, usar_R=usaR)
            if clave in ("u", "a", "z"):
                borc[clave] = prueba(ois, clave, donantes, rng, usar_R=usaR)
        for clave in ("u", "a", "z"):
            bloque[clave]["veredicto"] = veredicto(bloque[clave], borc[clave], clave[0])
        out["resultados"][per] = bloque
        out["oraculo"][per] = borc
        print(per, {k: (v["T"], v["n"], v.get("R", {}).get("p"), v.get("D", {}).get("p"), v.get("veredicto"))
                    for k, v in bloque.items()}, flush=True)
        print("  oráculo", {k: (v["T"], v["n"], v.get("R", {}).get("p"), v.get("D", {}).get("p"))
                            for k, v in borc.items()}, flush=True)

    # control negativo: disparos en cuadros N de los días con P evaluado, contra la huella P evaluada más cercana
    neg = {}
    for clave, Fk in (("a", "F_a"), ("z", "F_z"), ("u", None)):
        evP = defaultdict(list)
        for d, hu, di, s in items:
            if clave in coincide(hu, di):
                evP[d].append((s, hu))
        n = t = 0
        por_dia = {}
        for d, lst in evP.items():
            nd = td = 0
            for s, r in T[d].items():
                if r["clase"] != "N":
                    continue
                fired = (r["F_a"] == "1" or r["F_z"] == "1") if Fk is None else r[Fk] == "1"
                if not fired:
                    continue
                di = disparos(T[d], s, ventana=(0,))
                hu = min(lst, key=lambda x: abs(x[0] - s))[1]
                c = coincide(hu, di).get(clave)
                if c is None:
                    continue
                nd += 1
                td += int(c)
            por_dia[d] = (td, nd)
            n += nd
            t += td
        fP = out["resultados"]["todo"][clave]["frac"]
        fN = t / n if n else None
        lect = None
        if fN is not None and fP is not None:
            lect = "rumbo del día (parecida)" if abs(fP - fN) < DIF_NEG else (
                "sigue al cuadro (N claramente menor)" if fN < fP else "N mayor que P")
        neg[clave] = {"N_con_disparo": n, "coinciden": t, "frac_N": fN, "frac_P": fP, "lectura": lect,
                      "por_dia": por_dia}
    out["control_negativo"] = neg
    print("control negativo:", {k: (v["coinciden"], v["N_con_disparo"], v["lectura"]) for k, v in neg.items()},
          flush=True)

    # por día
    pd_ = defaultdict(lambda: defaultdict(int))
    for fila in filas_csv:
        q = pd_[fila["dia"]]
        q["P_con_huella"] += 1
        for k in ("u", "a", "z"):
            v = fila[f"coincide_{k}"]
            if v != "":
                q[f"{k}_eval"] += 1
                q[f"{k}_coincide"] += v
    out["por_dia"] = {d: dict(v) for d, v in sorted(pd_.items())}
    json.dump(out, open(os.path.join(RES, "s30b_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))
    with open(os.path.join(RES, "s30b_por_cuadro.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas_csv[0]))
        w.writeheader()
        w.writerows(filas_csv)
    print("listo:", os.path.join(RES, "s30b_resultado.json"), flush=True)


if __name__ == "__main__":
    medir()
