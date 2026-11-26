r"""V202/V204/V205 (verificador, S28b): nulos a nivel de día y de episodio para S25a (zona), S26a (unión a p*) y S23a
(anillo), sobre los disparos por cuadro reconstruidos por v202_cubos.py
(D:\goes_notas\s28\s28b\v202\cubos_v202.npz). No abre cuadros GOES: sólo las tablas booleanas F y evaluado.

Por qué: p25 y pN publicados tratan cada cuadro de 10 min como independiente. Aquí la unidad es el día (o el episodio):
cada patrón de cuadros P de un día de 2026 se compara con lo que ese mismo patrón de horas UTC da en días enteros de
referencia (2025 para p25; cuadros N de otros días de 2026 para pN), que conservan la dependencia dentro del día.

Uso: python -I -B v202_analisis.py   (escribe V202_204_205_salida.json en D: y texto en la salida estándar)
"""
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
SAL = r"D:\goes_notas\s28\s28b\v202"
T26, T25 = datetime(2026, 9, 21), datetime(2025, 9, 21)
W_AZAR, GAP_EP = 6, 6          # s23_medir.W_AZAR; s22a_medir.GAP_EP (leídos en esta sesión)
Zc = np.load(os.path.join(SAL, "cubos_v202.npz"))
CL = Zc["CL"]
ND = CL.shape[0]
assert ND == 65 and f"{T26 + timedelta(days=ND - 1):%Y-%m-%d}" == "2026-11-24"
OUT = {}


def f26(d):
    return f"{T26 + timedelta(days=int(d)):%m-%d}"


def f25(d):
    return f"{T25 + timedelta(days=int(d)):%m-%d}"


def hhmm(s):
    return f"{s // 6:02d}:{s % 6 * 10:02d}"


def dslot(a, b):
    x = abs(a - b) % 144
    return min(x, 144 - x)


def alc(F, ev):
    """Igual a s22b_medir.alcanzado: evaluado y F en el cuadro, el anterior o el siguiente, sin cruzar de día."""
    A = F.copy()
    A[:, 1:] |= F[:, :-1]
    A[:, :-1] |= F[:, 1:]
    return A & ev


def azar_por_hora(slots, al):
    slots, al = np.asarray(slots), np.asarray(al, float)
    r = np.full(144, np.nan)
    for s in range(144):
        dd = np.abs(slots - s) % 144
        dd = np.minimum(dd, 144 - dd)
        m = dd <= W_AZAR
        if m.any():
            r[s] = al[m].mean()
    return r


def pb_cola(ps, k):
    dist = np.array([1.0])
    for p in ps:
        dist = np.convolve(dist, [1.0 - p, p])
    return float(dist[k:].sum())


def episodios(slots):
    eps, cur = [], [slots[0]]
    for x in slots[1:]:
        if x - cur[-1] <= GAP_EP:
            cur.append(x)
        else:
            eps.append(cur)
            cur = [x]
    eps.append(cur)
    return eps


class Det:
    def __init__(self, nom):
        self.nom = nom
        self.F25, self.ev25 = Zc[nom + "_F25"], Zc[nom + "_ev25"]
        self.F26, self.ev26 = Zc[nom + "_F26"], Zc[nom + "_ev26"]
        self.A25, self.A26 = alc(self.F25, self.ev25), alc(self.F26, self.ev26)
        self.P = (CL == "P") & self.ev26
        self.N = (CL == "N") & self.ev26
        ds, ss = np.nonzero(self.ev25)
        self.r25 = azar_por_hora(ss, self.A25[ds, ss])

    def publicado(self):
        """R, p25 (Poisson binomial por cuadro) y pN (Fisher contra N cercanos) como los scripts auditados."""
        dP, sP = np.nonzero(self.P)
        te, th = len(sP), int(self.A26[dP, sP].sum())
        p25 = pb_cola([self.r25[s] for s in sP], th)
        psl = sorted(set(sP.tolist()))
        dN, sN = np.nonzero(self.N)
        cerca = np.array([any(dslot(s, x) <= W_AZAR for x in psl) for s in sN])
        nc, hc = int(cerca.sum()), int(self.A26[dN, sN][cerca].sum())
        pN = float(stats.fisher_exact([[th, te - th], [hc, nc - hc]], alternative="greater")[1])
        return {"P_evaluados": te, "P_alcanzados": th, "E25": float(sum(self.r25[s] for s in sP)), "p25": p25,
                "N_cerca": nc, "N_cerca_alcanzados": hc, "pN": pN}

    def patrones(self, unidad="dia"):
        """Lista de (día, slots P evaluados, alcanzados) por día o por episodio (episodio: P del día a <= 60 min)."""
        out = []
        for d in range(ND):
            Ps = np.flatnonzero(CL[d] == "P")
            if not len(Ps):
                continue
            grupos = [Ps] if unidad == "dia" else [np.array(e) for e in episodios(list(Ps))]
            for g in grupos:
                g = g[self.ev26[d, g]]
                if len(g):
                    out.append((d, g, int(self.A26[d, g].sum())))
        return out


def valores(Aref, evref, slots, modo, cob=0.5, excluir=None):
    """Lo que el patrón `slots` da en cada día de referencia. modo 'crudo': alcanzados (no evaluado cuenta 0), días
    con al menos un cuadro evaluado. modo 'escala': días con >= cob de los cuadros evaluados; fracción por n, al entero."""
    n = len(slots)
    vals, dias = [], []
    for d in range(Aref.shape[0]):
        if excluir is not None and d == excluir:
            continue
        ne = int(evref[d, slots].sum())
        h = int(Aref[d, slots].sum())
        if modo == "crudo":
            if ne > 0:
                vals.append(h)
                dias.append(d)
        else:
            if ne >= max(1, np.ceil(cob * n)):
                vals.append(int(round(h / ne * n)))
                dias.append(d)
    return np.array(vals), np.array(dias)


def conv_p(listas, obs):
    """P(suma >= obs) si cada patrón toma al azar, independiente, el valor de un día de referencia."""
    dist = np.array([1.0])
    for v in listas:
        if len(v) == 0:
            return None
        pm = np.bincount(v) / len(v)
        dist = np.convolve(dist, pm)
    return float(dist[obs:].sum()) if obs < len(dist) else 0.0


def nulo_unidad(D, ref, unidad, modo, cob=0.5, sin_dia=None):
    """p con la unidad día o episodio. ref '2025' (analogía de p25) o 'N2026' (analogía de pN: cuadros N evaluados de
    los otros días de 2026 en las mismas horas)."""
    pats = [p for p in D.patrones(unidad) if p[0] != sin_dia]
    obs = sum(a for *_, a in pats)
    listas, det = [], []
    for d, g, a in pats:
        if ref == "2025":
            v, dias = valores(D.A25, D.ev25, g, modo, cob)
        else:
            v, dias = valores(D.A26 & D.N, D.N, g, modo, cob, excluir=d)
        listas.append(v)
        n = len(g)
        det.append({"dia": f26(d), "horas": f"{hhmm(g[0])}-{hhmm(g[-1])}", "n": n, "alcanzados": a,
                    "dias_ref": int(len(v)), "ref_max": int(v.max()) if len(v) else None,
                    "ref_media": round(float(v.mean()), 3) if len(v) else None,
                    "ref_dias_ge_obs": int((v >= a).sum()) if len(v) else None,
                    "p_rango": round(float((1 + (v >= a).sum()) / (1 + len(v))), 4) if len(v) else None,
                    "sobre_p95": bool(a > np.percentile(v, 95)) if len(v) else None})
    return {"obs": obs, "p": conv_p(listas, obs), "unidades": len(pats), "detalle": det}


def excedencias(det):
    """Prueba de días (o episodios) excedentes: cuántas unidades superan el percentil 95 de su propia referencia."""
    ok = [x for x in det if x["sobre_p95"] is not None]
    k = sum(x["sobre_p95"] for x in ok)
    return {"unidades": len(ok), "sobre_p95": int(k), "p_binomial": float(stats.binom.sf(k - 1, len(ok), 0.05))}


def betabin_cola(h, n, k, N):
    """Cola P(X >= k | N) de una beta binomial ajustada por máxima verosimilitud a (h_d, n_d) de los días de 2025."""
    from scipy.optimize import minimize
    h, n = np.asarray(h), np.asarray(n)

    def nll(th):
        a, b = np.exp(th)
        return -stats.betabinom.logpmf(h, n, a, b).sum()
    r = minimize(nll, [0.0, 2.0], method="Nelder-Mead", options={"xatol": 1e-6, "fatol": 1e-9, "maxiter": 4000})
    a, b = np.exp(r.x)
    return float(stats.betabinom.sf(k - 1, N, a, b)), float(a), float(b)


def mh(tablas):
    """Razón de odds de Mantel-Haenszel, IC 95 % (Robins, Breslow, Greenland) y prueba CMH unilateral (sin corrección)."""
    R = S = PR = PSQR = QS = 0.0
    ea = va = sa = 0.0
    inf = 0
    for a, b, c, d in tablas:
        n = a + b + c + d
        if n < 2 or (a + b) == 0 or (c + d) == 0:
            continue
        inf += 1
        r, s = a * d / n, b * c / n
        p, q = (a + d) / n, (b + c) / n
        R += r
        S += s
        PR += p * r
        PSQR += p * s + q * r
        QS += q * s
        sa += a
        ea += (a + b) * (a + c) / n
        va += (a + b) * (c + d) * (a + c) * (b + d) / (n * n * (n - 1))
    if R == 0 or S == 0:
        return {"OR": (float("inf") if S == 0 and R > 0 else 0.0), "estratos": inf, "IC95": None,
                "p_CMH_mayor": float(stats.norm.sf((sa - ea) / np.sqrt(va))) if va > 0 else None}
    lor = np.log(R / S)
    var = PR / (2 * R * R) + PSQR / (2 * R * S) + QS / (2 * S * S)
    return {"OR": round(float(R / S), 3), "IC95": [round(float(np.exp(lor - 1.96 * np.sqrt(var))), 3),
                                                   round(float(np.exp(lor + 1.96 * np.sqrt(var))), 3)],
            "estratos": inf, "p_CMH_mayor": float(stats.norm.sf((sa - ea) / np.sqrt(va)))}


def tablas_dia(D, variante, franja=False, sin_dia=None):
    """Tablas 2x2 por día (o por día y franja de 3 h): P alcanzado, P no, N alcanzado, N no. Variantes de N:
    'todos' los N evaluados del día; 'cerca' a <= 60 min de un P evaluado de ESE día; con '_sin_vecinos' se quitan los N
    a 1 cuadro o menos de un cuadro P del día (comparten la ventana de 'alcanzado' con el P)."""
    T, filas = [], []
    for d in range(ND):
        if d == sin_dia:
            continue
        Ps = np.flatnonzero(D.P[d])
        if not len(Ps):
            continue
        Pt = np.flatnonzero(CL[d] == "P")
        Ns = np.flatnonzero(D.N[d])
        if variante.startswith("cerca"):
            Ns = np.array([s for s in Ns if any(dslot(s, x) <= W_AZAR for x in Ps)], int)
        if variante.endswith("sin_vecinos"):
            Ns = np.array([s for s in Ns if all(abs(s - x) > 1 for x in Pt)], int)
        grupos = [(Ps, Ns)] if not franja else [(Ps[Ps // 18 == b], Ns[Ns // 18 == b]) for b in range(8)]
        fa = fb = fc = fd = 0
        for p_, n_ in grupos:
            a = int(D.A26[d, p_].sum())
            c = int(D.A26[d, n_].sum()) if len(n_) else 0
            T.append((a, len(p_) - a, c, len(n_) - c))
            fa, fb, fc, fd = fa + a, fb + len(p_) - a, fc + c, fd + len(n_) - c
        filas.append({"dia": f26(d), "P": f"{fa}/{fa + fb}", "N": f"{fc}/{fc + fd}"})
    return T, filas


def desplazamiento(D, max_k=None, cob=0.5):
    """Nulo dentro del día: el patrón P de cada día corrido k cuadros en el mismo día (circular), k != 0. Conserva la
    estructura temporal de P y de los disparos. max_k limita el corrimiento (36 = +-6 h)."""
    listas, obs = [], 0
    for d, g, a in D.patrones("dia"):
        n = len(g)
        vals = []
        ks = [k for k in range(-71, 73) if k != 0 and (max_k is None or abs(k) <= max_k)]
        for k in ks:
            sl = (g + k) % 144
            ne = int(D.ev26[d, sl].sum())
            if ne >= max(1, np.ceil(cob * n)):
                vals.append(int(round(D.A26[d, sl].sum() / ne * n)))
        listas.append(np.array(vals, int))
        obs += a
    return {"obs": obs, "p": conv_p(listas, obs), "corrimientos_por_dia": [int(len(v)) for v in listas]}


def rachas(F):
    """Largos de las rachas de F seguidas (por día)."""
    out = []
    for d in range(F.shape[0]):
        c = 0
        for s in range(144):
            if F[d, s]:
                c += 1
            elif c:
                out.append(c)
                c = 0
        if c:
            out.append(c)
    return out


def imprimir(t, x):
    print(f"\n=== {t} ===")
    print(json.dumps(x, ensure_ascii=False, indent=1, default=float))


# ------------------------------------------------------------------ pruebas de mi propio código
def pruebas():
    # alcanzado: vecino anterior y siguiente, sin cruzar de día
    F = np.zeros((2, 144), bool)
    ev = np.ones((2, 144), bool)
    F[0, 143] = F[1, 10] = True
    A = alc(F, ev)
    assert A[0, 142] and A[0, 143] and not A[1, 0] and A[1, 9] and A[1, 10] and A[1, 11] and A.sum() == 5
    # Poisson binomial y convolución de días
    assert abs(pb_cola([0.5, 0.5], 1) - 0.75) < 1e-12
    assert abs(conv_p([np.array([0, 0, 0, 5]), np.array([0, 5])], 10) - 0.125) < 1e-12
    assert abs(conv_p([np.array([0, 0, 0, 5]), np.array([0, 5])], 5) - (1 - 0.75 * 0.5)) < 1e-12
    # Mantel-Haenszel contra statsmodels (si está instalado)
    T = [(15, 11, 3, 72), (0, 13, 52, 30), (8, 0, 20, 12), (20, 11, 28, 32)]
    r = mh(T)
    try:
        from statsmodels.stats.contingency_tables import StratifiedTable
        st = StratifiedTable([np.array([[a, b], [c, d]]) for a, b, c, d in T])
        assert abs(st.oddsratio_pooled - r["OR"]) < 2e-3, (st.oddsratio_pooled, r["OR"])
        lo, hi = st.oddsratio_pooled_confint()
        assert abs(lo - r["IC95"][0]) < 2e-3 and abs(hi - r["IC95"][1]) < 2e-3, ((lo, hi), r["IC95"])
        print("pruebas OK (MH igual a statsmodels)")
    except ImportError:
        print("pruebas OK (statsmodels no está: MH sin contraste externo)")
    # episodios: corte a más de 60 min
    assert episodios([1, 2, 8, 15, 16]) == [[1, 2, 8], [15, 16]]


pruebas()

# ------------------------------------------------------------------ 0. reproducción
DETS = {"S25a zona (pct 5)": Det("z5"), "S26a unión (p* 4,75)": Det("up"), "S26a anillo a p*": Det("ap"),
        "S26a zona a p*": Det("zp"), "S23a anillo (pct 5, costumbre 2025)": Det("s23a"),
        "anillo S23b post hoc (pct 5, costumbre 2026)": Det("a5")}
OUT["0_reproduccion"] = {k: D.publicado() for k, D in DETS.items()}
imprimir("0. Reproducción de lo publicado (mi propia implementación de alcanzado, r25, Poisson binomial y Fisher)",
         OUT["0_reproduccion"])
print("Nota: el pN publicado de S23a no es Fisher sino Poisson binomial con rN por hora (dio 0,0); aquí sólo vale su p25.")
Zo, Un, An, S23 = DETS["S25a zona (pct 5)"], DETS["S26a unión (p* 4,75)"], DETS["S26a anillo a p*"], \
    DETS["S23a anillo (pct 5, costumbre 2025)"]

# 0b. cuadro a cuadro contra las tablas que dejaron las corridas publicadas (camino C7: ¿los cachés de hoy son los de la medida?)
import csv  # noqa: E402


def contra_tabla(ruta, pares):
    dif = {k: 0 for k, *_ in pares}
    n = 0
    with open(ruta, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d = (datetime.strptime(r["dia"], "%Y-%m-%d") - T26).days
            s = int(r["hora"][:2]) * 6 + int(r["hora"][3:]) // 10
            n += 1
            for k, col, arr in pares:
                dif[k] += int(int(r[col]) != int(arr[d, s]))
    return {"filas": n, "diferencias": dif}


OUT["0b_cuadro_a_cuadro"] = {
    "S25a tabla_2026.csv (zona pct 5)": contra_tabla(r"D:\goes_notas\s25\s25a\tabla_2026.csv",
                                                     [("F", "F", Zo.F26), ("evaluado", "evaluado", Zo.ev26)]),
    "S26a tabla_2026.csv (p*)": contra_tabla(r"D:\goes_notas\s26\s26a\tabla_2026.csv",
                                             [("F_a", "F_a", An.F26), ("ev_a", "ev_a", An.ev26),
                                              ("F_z", "F_z", DETS["S26a zona a p*"].F26), ("ev_z", "ev_z", DETS["S26a zona a p*"].ev26)])}
imprimir("0b. Mis disparos cuadro a cuadro contra las tablas de las corridas publicadas (0 diferencias = idénticos)",
         OUT["0b_cuadro_a_cuadro"])

# ------------------------------------------------------------------ 1. dependencia dentro del día (¿es el día la unidad?)
dep = {}
for k, D in (("zona_2025", Zo), ("anillo_2025", S23)):
    tot = D.F25.sum(1)
    ev = D.ev25.sum(1)
    o = np.sort(tot)[::-1]
    r = rachas(D.F25)
    A = D.A25
    x, y = A[:, :-1][D.ev25[:, :-1] & D.ev25[:, 1:]], A[:, 1:][D.ev25[:, :-1] & D.ev25[:, 1:]]
    fr = np.array([A[d][D.ev25[d]].mean() for d in range(62) if D.ev25[d].sum() >= 20])
    nn = np.array([D.ev25[d].sum() for d in range(62) if D.ev25[d].sum() >= 20])
    pbar = A[D.ev25].mean()
    dep[k] = {"disparos": int(tot.sum()), "dias_con_evaluados": int((ev > 0).sum()), "dias_sin_disparo": int(((tot == 0) & (ev > 0)).sum()),
              "dias_que_juntan_la_mitad_de_los_disparos": int(np.searchsorted(np.cumsum(o), tot.sum() / 2) + 1),
              "max_disparos_en_un_dia": int(o[0]), "dia_del_max": f25(int(np.argmax(tot))),
              "rachas": len(r), "racha_mediana": float(np.median(r)), "racha_max": int(max(r)),
              "autocorr_alcanzado_10min": round(float(np.corrcoef(x, y)[0, 1]), 3),
              "sobredispersion_diaria": round(float(np.var(fr * nn, ddof=1) / np.mean(nn * pbar * (1 - pbar))), 1),
              "autocorr_dia_a_dia_de_la_fraccion": round(float(np.corrcoef(fr[:-1], fr[1:])[0, 1]), 3)}
for k, D in (("zona_2026", Zo), ("union_2026", Un)):
    tot = D.F26.sum(1)
    r = rachas(D.F26)
    dep[k] = {"disparos": int(tot.sum()), "max_disparos_en_un_dia": int(tot.max()), "dia_del_max": f26(int(np.argmax(tot))),
              "dias_con_25_disparos_o_mas": int((tot >= 25).sum()), "rachas": len(r), "racha_mediana": float(np.median(r)),
              "racha_max": int(max(r))}
OUT["1_dependencia"] = dep
imprimir("1. Dependencia dentro del día (sobredispersión = varianza del conteo diario de alcanzados / varianza binomial)", dep)

# ------------------------------------------------------------------ 2. Hallazgo 202: el 14-11 en la zona
d14 = (datetime(2026, 11, 14) - T26).days
g14 = np.flatnonzero(Zo.P[d14])
h14 = int(Zo.A26[d14, g14].sum())
p14_cuadros = pb_cola([Zo.r25[s] for s in g14], h14)
h202 = {"P_evaluados": int(len(g14)), "P_alcanzados": h14, "p25_por_cuadro": p14_cuadros,
        "horas_P": f"{hhmm(g14[0])} a {hhmm(g14[-1])} UTC", "episodios_P_del_dia": len(episodios(list(np.flatnonzero(CL[d14] == 'P')))),
        "rachas_de_disparo_que_tocan_P": None}
F14 = Zo.F26[d14]
toc, c0 = 0, None
for s in range(145):
    on = s < 144 and F14[s]
    if on and c0 is None:
        c0 = s
    if not on and c0 is not None:
        if any(c0 - 1 <= x <= s for x in g14):
            toc += 1
        c0 = None
h202["rachas_de_disparo_que_tocan_P"] = toc
h202["horas_disparo_14_11"] = [hhmm(s) for s in np.flatnonzero(F14)]
ne25 = Zo.ev25[:, g14].sum(1)
hh25 = Zo.A25[:, g14].sum(1)
h202["dias_2025_total"] = 62
h202["dias_2025_con_algun_cuadro_evaluado_en_esas_horas"] = int((ne25 > 0).sum())
h202["dias_2025_con_los_31_evaluados"] = int((ne25 == len(g14)).sum())
h202["dias_2025_con_16_o_mas_evaluados"] = int((ne25 >= 16).sum())
orden = np.argsort(-hh25)[:6]
h202["top_2025_alcanzados_en_esas_horas"] = [{"dia": f25(d), "alcanzados": int(hh25[d]), "evaluados": int(ne25[d])} for d in orden]
h202["max_2025"] = int(hh25.max())
h202["dias_2025_con_20_o_mas"] = int((hh25 >= h14).sum())
h202["dias_2025_con_fraccion_ge_20_31"] = int(((hh25 / np.maximum(ne25, 1) >= h14 / len(g14)) & (ne25 >= 16)).sum())
for modo, cob in (("crudo", None), ("escala", 0.5), ("escala", 0.8), ("escala", 1.0)):
    v, _ = valores(Zo.A25, Zo.ev25, g14, modo, cob or 0.5)
    h202[f"p_rango_dia_{modo}{'' if cob is None else '_cob' + str(cob)}"] = {
        "dias": int(len(v)), "dias_ge_20": int((v >= h14).sum()), "max": int(v.max()),
        "p": float((1 + (v >= h14).sum()) / (1 + len(v))), "piso": float(1 / (1 + len(v)))}
m = ne25 >= 16
h202["beta_binomial_2025"] = dict(zip(("p_cola_20_de_31", "a", "b"), betabin_cola(hh25[m], ne25[m], h14, len(g14))))
# corrimientos del patrón del 14-11 dentro de +-60 min en 2025 (más réplicas, no independientes)
mx = []
for k in range(-6, 7):
    sl = g14 + k
    sl = sl[(sl >= 0) & (sl < 144)]
    mx.append(int(Zo.A25[:, sl].sum(1).max()))
h202["max_2025_con_el_patron_corrido_hasta_60_min"] = int(max(mx))
# el mismo patrón en los otros días de 2026 (todos los cuadros evaluados, con o sin clase)
ne26 = Zo.ev26[:, g14].sum(1)
hh26 = Zo.A26[:, g14].sum(1)
otros = [d for d in range(ND) if d != d14 and ne26[d] >= 16]
h202["otros_dias_2026_en_esas_horas"] = {
    "dias_con_16_o_mas_evaluados": len(otros),
    "dias_con_fraccion_ge_20_31": [f26(d) + f" {int(hh26[d])}/{int(ne26[d])}" for d in otros if hh26[d] / ne26[d] >= h14 / len(g14)],
    "top": [f26(d) + f" {int(hh26[d])}/{int(ne26[d])}" for d in sorted(otros, key=lambda d: -hh26[d] / ne26[d])[:8]]}
OUT["2_hallazgo_202"] = h202
imprimir("2. Hallazgo 202: el 14-11 de S25a con el día como unidad", h202)

# ------------------------------------------------------------------ 3. Hallazgo 204: P contra N dentro del mismo día
h204 = {}
for nom, D in (("S25a zona (pct 5)", Zo), ("S26a zona a p*", DETS["S26a zona a p*"]), ("S26a unión (p* 4,75)", Un),
               ("S26a anillo a p*", An), ("anillo S23b post hoc (pct 5, costumbre 2026)", DETS["anillo S23b post hoc (pct 5, costumbre 2026)"])):
    x = {}
    for var in ("todos", "cerca", "todos_sin_vecinos", "cerca_sin_vecinos"):
        T, filas = tablas_dia(D, var)
        x[var] = mh(T)
        a, b, c, d = (sum(t[i] for t in T) for i in range(4))
        x[var]["agrupado_sin_estratificar"] = f"P {a}/{a + b}, N {c}/{c + d}"
        if var == "todos":
            x["por_dia_todos"] = filas
        if var == "cerca":
            x["por_dia_cerca"] = filas
    T, _ = tablas_dia(D, "todos", franja=True)
    x["todos_por_dia_y_franja_3h"] = mh(T)
    x["sin_cada_dia_OR_todos"] = {}
    for d in range(ND):
        if D.P[d].any():
            r = mh(tablas_dia(D, "todos", sin_dia=d)[0])
            x["sin_cada_dia_OR_todos"][f26(d)] = [r["OR"], r["IC95"]]
    x["corrimiento_dentro_del_dia_todo"] = desplazamiento(D)
    x["corrimiento_dentro_del_dia_6h"] = desplazamiento(D, 36)
    # entre días: N de días con P contra N de días sin P (¿mide 'día con disparos'?)
    conP = np.array([D.P[d].any() for d in range(ND)])
    nP, nS = D.N[conP], D.N[~conP]
    x["N_en_dias_con_P"] = f"{int((D.A26[conP] & nP).sum())}/{int(nP.sum())}"
    x["N_en_dias_sin_P"] = f"{int((D.A26[~conP] & nS).sum())}/{int(nS.sum())}"
    # lo mismo sólo de tarde (12 a 24 UTC), donde están casi todos los P
    tarde = np.zeros(144, bool)
    tarde[72:] = True
    x["N_tarde_en_dias_con_P"] = f"{int((D.A26[conP] & nP)[:, tarde].sum())}/{int(nP[:, tarde].sum())}"
    x["N_tarde_en_dias_sin_P"] = f"{int((D.A26[~conP] & nS)[:, tarde].sum())}/{int(nS[:, tarde].sum())}"
    x["P_tarde"] = f"{int((D.A26 & D.P)[:, tarde].sum())}/{int(D.P[:, tarde].sum())}"
    h204[nom] = x
OUT["3_hallazgo_204"] = h204
imprimir("3. Hallazgo 204: razón de odds P contra N estratificada por día (Mantel-Haenszel)", h204)

# ------------------------------------------------------------------ 4. Hallazgo 205: p25 y pN con el día o el episodio como unidad
h205 = {}
for nom, D in (("S23a anillo (pct 5, costumbre 2025)", S23), ("S25a zona (pct 5)", Zo), ("S26a unión (p* 4,75)", Un)):
    x = {"publicado_por_cuadro": D.publicado()}
    for ref in ("2025", "N2026"):
        for unidad in ("dia", "episodio"):
            for modo, cob in (("crudo", 0.5), ("escala", 0.5), ("escala", 0.8)):
                r = nulo_unidad(D, ref, unidad, modo, cob)
                clave = f"ref_{ref}_{unidad}_{modo}" + (f"_cob{cob}" if modo == "escala" else "")
                x[clave] = {"obs": r["obs"], "unidades": r["unidades"], "p": r["p"], "excedencias_p95": excedencias(r["detalle"])}
                if modo == "escala" and cob == 0.5:
                    x[clave]["detalle"] = r["detalle"]
    # episodio con la definición publicada: alcanzado si hay F en el episodio +-30 min (s23_medir.py líneas 434 a 438)
    eps = []
    for d in range(ND):
        Ps = np.flatnonzero(CL[d] == "P")
        for ep in (episodios(list(Ps)) if len(Ps) else []):
            ep = np.array(ep)
            if not D.ev26[d, ep].any():
                continue
            w = slice(max(0, ep[0] - 3), min(144, ep[-1] + 4))
            e25 = [bool(D.F25[r, w].any()) for r in range(62) if D.ev25[r, ep].any()]
            eN = [bool(D.F26[r, w].any()) for r in range(ND) if r != d and D.N[r, ep].any() and not (CL[r, w] == "P").any()]
            eps.append({"dia": f26(d), "horas": f"{hhmm(ep[0])}-{hhmm(ep[-1])}", "alcanzado": bool(D.F26[d, w].any()),
                        "q_2025": round(float(np.mean(e25)), 4), "dias_2025": len(e25),
                        "q_N2026": round(float(np.mean(eN)), 4) if eN else None, "dias_N2026": len(eN)})
    k = sum(e["alcanzado"] for e in eps)
    x["episodios_definicion_publicada"] = {
        "episodios": len(eps), "alcanzados": k, "esperados_2025": round(sum(e["q_2025"] for e in eps), 2),
        "p_2025": pb_cola([e["q_2025"] for e in eps], k),
        "esperados_N2026": round(sum(e["q_N2026"] for e in eps if e["q_N2026"] is not None), 2),
        "p_N2026": pb_cola([e["q_N2026"] for e in eps if e["q_N2026"] is not None],
                           sum(e["alcanzado"] for e in eps if e["q_N2026"] is not None)), "detalle": eps}
    # sin cada día (¿descansa en un solo día?)
    x["sin_cada_dia"] = {}
    for d in range(ND):
        if D.P[d].any():
            x["sin_cada_dia"][f26(d)] = {f"ref_{ref}_dia_escala_cob0.5": nulo_unidad(D, ref, "dia", "escala", 0.5, sin_dia=d)["p"]
                                         for ref in ("2025", "N2026")}
            x["sin_cada_dia"][f26(d)]["P_alcanzados_restantes"] = nulo_unidad(D, "2025", "dia", "escala", 0.5, sin_dia=d)["obs"]
    h205[nom] = x
OUT["4_hallazgo_205"] = h205
imprimir("4. Hallazgo 205: p con el día o el episodio como unidad", h205)

json.dump(OUT, open(os.path.join(SAL, "V202_204_205_salida.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
          default=float)
print("\nescrito", os.path.join(SAL, "V202_204_205_salida.json"))
