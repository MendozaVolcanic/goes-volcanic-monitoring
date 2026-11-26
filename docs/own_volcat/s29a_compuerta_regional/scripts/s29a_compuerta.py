r"""S29a parte 2: compuerta regional para el detector S26a (S26a+G). Implementa criterio_2026-11-25.md (commit
d5510a5, empujado antes de aplicar la compuerta a un solo disparo).

Por qué: si una cumbre sin pluma de la misma imagen (Antuco, Longaví) dispara a la vez que Chillán, lo más probable es
que el disparo de Chillán sea lo mismo que el de la vecina (sol, deshielo, nube o humedad de la región), no pluma. Un
disparo diurno de Chillán con una vecina disparando a ±1 cuadro se anula. La compuerta sólo vale si borra más falsas
alarmas que aciertos: eso es lo que se mide.

Qué se reutiliza sin cambios: la unión de Chillán (s26a_medir.Partes, percentil 4,75), la unión de las vecinas de
S28a (cuadros en D:\goes_notas\s28\s28a\cuadros_<vecina>_<año>.csv), s26a_medir.azar/recuerdo/medidas_seco,
s22b_medir.alcanzado y s28a_medir.razon/por_dia.

Uso: python -I s29a_compuerta.py pruebas | medir
"""
import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "s28a_vecinas", "scripts"))
import s28a_medir as T  # noqa: E402   (importa s27a, s26a, s25a, s23, s22b, s22a)

U, B, M = T.U, T.B, T.M
TRAB28 = T.TRAB
TRAB = r"D:\goes_notas\s29\s29a"
TABLA_S26A = T.TABLA_S26A
RES28 = os.path.join(OV, "s28a_vecinas", "resultados", "s28a_resultado.json")
# ---------- parámetros del criterio ----------
PSTAR = 4.75
W = 1                                   # ±1 cuadro
DIA, NOCHE, TODO = U.DIA, U.NOCHE, range(144)
VECINAS = ("antuco", "longavi")
N_BOOT, SEMILLA = 2000, 0
T0 = {"2025": T.T0_25, "2026": T.T0_26}
ND = {"2025": T.NR, "2026": T.ND26}
ESPERADO_CH = (269, 5499)


# ---------- vecinas ----------
def vecina(sitio, año):
    """(F, ev) por día como arreglos [nd, 144] desde los cuadros de S28a."""
    F = np.zeros((ND[año], 144), bool)
    ev = np.zeros((ND[año], 144), bool)
    with open(os.path.join(TRAB28, f"cuadros_{sitio}_{año}.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d = (datetime.strptime(r["dia"], "%Y-%m-%d") - T0[año]).days
            s = M.slot(r["hora"])
            ev[d, s] = r["ev_u"] == "1"
            F[d, s] = r["F_u"] == "1"
    return F, ev


def comprobar_vecinas(V):
    """Los totales de noche y de día de la unión de cada vecina tienen que ser los de s28a_resultado.json."""
    r28 = json.load(open(RES28, encoding="utf-8"))["vecinas"]
    out, ok = {}, True
    for s in VECINAS:
        for per, rg in (("noche", NOCHE), ("dia", DIA)):
            esp = r28[s]["principal"][per]["union"]
            mio = {a: [int(V[s, a][0][:, list(rg)].sum()), int(V[s, a][1][:, list(rg)].sum())] for a in ("2025", "2026")}
            igual = mio["2025"] == esp["2025"] and mio["2026"] == esp["2026"]
            out[f"{s}_{per}"] = {"mio": mio, "s28a": [esp["2025"], esp["2026"]], "igual": igual}
            ok &= igual
    return ok, out


# ---------- la compuerta ----------
def mascara(G, rango, w=W):
    """True en los cuadros s del rango con algún disparo de G (vecina o unión de vecinas) en s - w a s + w."""
    m = np.zeros(G.shape, bool)
    r = np.zeros(144, bool)
    r[list(rango)] = True
    for k in range(-w, w + 1):
        sh = np.zeros_like(G)
        if k >= 0:
            sh[:, :144 - k] = G[:, k:]
        else:
            sh[:, -k:] = G[:, :144 + k]
        m |= sh
    return m & r


def aplicar(F, gate):
    return F & ~gate


def compuerta_de(V, año, quien, rango=DIA, w=W, modo="o"):
    """Máscara de compuerta [nd, 144] con las vecinas `quien` ("o": basta una; "y": las dos a ±w)."""
    ms = [mascara(V[s, año][0], rango, w) for s in quien]
    if modo == "y":
        return np.logical_and.reduce(ms)
    return np.logical_or.reduce(ms)


# ---------- medidas ----------
def lista_dias(F, ev):
    return [(F[d], ev[d]) for d in range(F.shape[0])]


def alcanzados_P(F, ev, CL):
    """{(d, s): alcanzado} de los P evaluados."""
    return {(d, s): B.alcanzado(F[d], ev[d], s)[1] for d in range(F.shape[0]) for s in np.flatnonzero(CL[d] == "P")
            if ev[d, s]}


def medir_regla(ch25, ch26, CL, g25, g26):
    """M1 y M2 de Chillán con las máscaras g25 y g26."""
    F25, e25 = ch25
    F26, e26 = ch26
    F25g, F26g = aplicar(F25, g25), aplicar(F26, g26)
    sec = lista_dias(F25g, e25)
    m1 = U.medidas_seco(sec)
    r25 = U.azar(sec)
    res = [{"u": (F26g[d], e26[d])} for d in range(F26.shape[0])]
    m2 = U.recuerdo(U.lista(res, CL, "u"), r25)
    if m2["p25"] <= U.P25_MAX and m2["pN"] is not None and m2["pN"] <= U.PN_MAX and m2["R"] >= U.R_MIN \
            and m2["dias_P_alcanzado"] >= U.MIN_DIAS_ALC:
        rot = "ALCANZA (desarrollo)"
    elif m2["p25"] <= U.P25_MAX:
        rot = "PARCIAL (desarrollo)"
    else:
        rot = "NO ALCANZA (desarrollo)"
    antes = alcanzados_P(F26, e26, CL)
    despues = alcanzados_P(F26g, e26, CL)
    hit = [k for k, a in antes.items() if a]
    perdidos = [k for k in hit if not despues[k]]
    dia_anul25 = int((F25 & g25).sum())
    m1["dia_disparos_antes"] = int(F25[:, list(DIA)].sum())
    m1["dia_anulados"] = dia_anul25
    m1["f_FA25"] = dia_anul25 / m1["dia_disparos_antes"] if m1["dia_disparos_antes"] else None
    Ndia = [(F26g[d][s], F26[d][s]) for d in range(F26.shape[0]) for s in DIA if e26[d, s] and CL[d, s] == "N"]
    return {"M1_seco_2025": m1, "M2_alcance_2026": m2, "rotulo": rot, "P_alcanzados_antes": len(hit),
            "P_perdidos": len(perdidos), "f_P": len(perdidos) / len(hit) if hit else None,
            "perdidos_por_dia": _cuenta(B.fecha(d) for d, _ in perdidos),
            "N_2026_dia": {"n": len(Ndia), "con_disparo_antes": int(sum(b for _, b in Ndia)),
                           "con_disparo_despues": int(sum(a for a, _ in Ndia))},
            "_por_dia_P": {d: (sum(1 for k in hit if k[0] == d), sum(1 for k in perdidos if k[0] == d))
                           for d in sorted({k[0] for k in hit})}}


def _cuenta(it):
    out = {}
    for x in it:
        out[x] = out.get(x, 0) + 1
    return out


def placebo(V, año, rango=DIA, w=W):
    """M3: cada vecina con la otra como compuerta. Devuelve por vecina (F, ev, F con compuerta)."""
    out = {}
    for s, otra in (("antuco", "longavi"), ("longavi", "antuco")):
        F, ev = V[s, año]
        g = compuerta_de(V, año, (otra,), rango, w)
        out[s] = (F, ev, aplicar(F, g))
    return out


def f_FA26(pl, rango=DIA):
    r = list(rango)
    tot = sum(int(pl[s][0][:, r].sum()) for s in VECINAS)
    anul = sum(int((pl[s][0] & ~pl[s][2])[:, r].sum()) for s in VECINAS)
    return anul / tot if tot else None, anul, tot


def sincronia(Fa, Fb, rango=DIA, w=W):
    """Cuadros del rango en que dispara a y b dispara a ±w."""
    return int((Fa & mascara(Fb, rango, w)).sum())


def _r(x):
    return None if (x is None or not np.isfinite(x)) else round(float(x), 5)


# ---------- medir ----------
def medir():
    os.makedirs(RES, exist_ok=True)
    os.makedirs(TRAB, exist_ok=True)
    t = time.time()
    V = {(s, a): vecina(s, a) for s in VECINAS for a in ("2025", "2026")}
    ok_v, comp_v = comprobar_vecinas(V)
    print("vecinas contra S28a:", "OK" if ok_v else "NO REPRODUCE", flush=True)
    if not ok_v:
        json.dump(comp_v, open(os.path.join(RES, "s29a_reproduccion_FALLA.json"), "w"), indent=1)
        sys.exit("los cuadros de las vecinas no dan los totales de S28a")
    # Chillán: 2025 seco y 2026 blanco a 4,75
    X = U.Partes()
    sec = X.seco(PSTAR)
    res, _, _ = X.blanco(PSTAR)
    CL = X.CL
    F25 = np.array([f for f, _ in sec["u"]])
    e25 = np.array([e for _, e in sec["u"]])
    F26 = np.array([r["u"][0] for r in res])
    e26 = np.array([r["u"][1] for r in res])
    m = U.medidas_seco(sec["u"])
    dif = 0
    with open(TABLA_S26A, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d = (datetime.strptime(r["dia"], "%Y-%m-%d") - T.T0_26).days
            s = M.slot(r["hora"])
            dif += (int(F26[d, s]) != int(r["F_a"] == "1" or r["F_z"] == "1")) \
                + (int(e26[d, s]) != int(r["ev_a"] == "1" or r["ev_z"] == "1")) + (CL[d, s] != r["clase"])
    comp_ch = {"seco_2025": [m["disparos"], m["evaluados"]], "diferencias_tabla_2026": dif}
    ok_ch = (m["disparos"], m["evaluados"]) == ESPERADO_CH and dif == 0
    print("Chillán:", comp_ch, "OK" if ok_ch else "NO REPRODUCE", flush=True)
    if not ok_ch:
        json.dump(comp_ch, open(os.path.join(RES, "s29a_reproduccion_FALLA.json"), "w"), indent=1)
        sys.exit("Chillán no reproduce S26a")
    del X
    ch25, ch26 = (F25, e25), (F26, e26)
    np.savez_compressed(os.path.join(TRAB, "chillan_union.npz"), F25=F25, e25=e25, F26=F26, e26=e26,
                        CL=CL.astype(str))
    sin = medir_regla(ch25, ch26, CL, np.zeros_like(F25), np.zeros_like(F26))
    principal = medir_regla(ch25, ch26, CL, compuerta_de(V, "2025", VECINAS), compuerta_de(V, "2026", VECINAS))
    # M3
    m3 = {}
    pl = {a: placebo(V, a) for a in ("2025", "2026")}
    for s in VECINAS:
        c25a = T.por_dia(lista_dias(*pl["2025"][s][:2]), DIA)
        c26a = T.por_dia(lista_dias(*pl["2026"][s][:2]), DIA)
        c25d = T.por_dia(lista_dias(pl["2025"][s][2], pl["2025"][s][1]), DIA)
        c26d = T.por_dia(lista_dias(pl["2026"][s][2], pl["2026"][s][1]), DIA)
        m3[s] = {"antes": T.razon(c25a, c26a), "con_compuerta": T.razon(c25d, c26d)}
    fa26, anul26, tot26 = f_FA26(pl["2026"])
    fa25v, anul25v, tot25v = f_FA26(pl["2025"])
    # M4: nulo por corrimiento de días
    m4 = {}
    for año in ("2025", "2026"):
        Fa, Fl = V["antuco", año][0], V["longavi", año][0]
        obs = sincronia(Fa, Fl)
        n = ND[año]
        reps = [sincronia(Fa, np.roll(Fl, k, axis=0)) for k in range(1, n)]
        m4[año] = {"observado": obs, "replicas": len(reps), "p_minimo": _r(1 / (len(reps) + 1)),
                   "p": _r((1 + sum(x >= obs for x in reps)) / (len(reps) + 1)),
                   "replicas_media": _r(np.mean(reps)), "replicas_max": int(max(reps))}
    # Chillán: P perdidos con las vecinas de otro día (informativo)
    gl = []
    for k in range(1, ND["2026"]):
        Vk = {key: ((np.roll(v[0], k, axis=0), v[1]) if key[1] == "2026" else v) for key, v in V.items()}
        g = compuerta_de(Vk, "2026", VECINAS)
        F26g = aplicar(F26, g)
        d = alcanzados_P(F26g, e26, CL)
        gl.append(sum(1 for kk, a in alcanzados_P(F26, e26, CL).items() if a and not d[kk]))
    m4["P_perdidos_chillan"] = {"observado": principal["P_perdidos"], "replicas": len(gl),
                                "p_mas_perdidos": _r((1 + sum(x >= principal["P_perdidos"] for x in gl)) / (len(gl) + 1)),
                                "replicas_media": _r(np.mean(gl)), "replicas_min": int(min(gl)),
                                "replicas_max": int(max(gl))}
    # M5: d = f_FA26 - f_P, remuestreo de días
    rng = np.random.default_rng(SEMILLA)
    r = list(DIA)
    pv = np.array([[sum(int((pl["2026"][s][0][d] & ~pl["2026"][s][2][d])[r].sum()) for s in VECINAS),
                    sum(int(pl["2026"][s][0][d][r].sum()) for s in VECINAS)] for d in range(ND["2026"])], float)
    pc = np.array([[b, a] for a, b in principal["_por_dia_P"].values()], float)     # (perdidos, alcanzados)
    fP = principal["f_P"]
    dobs = fa26 - fP
    ds = []
    for _ in range(N_BOOT):
        a = pv[rng.integers(0, len(pv), len(pv))].sum(0)
        b = pc[rng.integers(0, len(pc), len(pc))].sum(0)
        if a[1] and b[1]:
            ds.append(a[0] / a[1] - b[0] / b[1])
    m5 = {"f_FA26": _r(fa26), "f_P": _r(fP), "d": _r(dobs), "IC95": [_r(x) for x in np.percentile(ds, [2.5, 97.5])],
          "replicas_validas": len(ds), "dias_vecinas": len(pv), "dias_chillan_con_alcance": len(pc)}
    # veredicto (§4)
    if principal["rotulo"] != "ALCANZA (desarrollo)" or fP >= fa26:
        ver = "NO SIRVE"
    elif m4["2026"]["p"] > 0.05:
        ver = "SIN BASE"
    elif m5["IC95"][0] > 0:
        ver = "CANDIDATA"
    else:
        ver = "NO CONCLUYENTE"
    # sensibilidades (§5)
    sens = {}
    for nom, quien, rango, w, modo in (("ventana_0", VECINAS, DIA, 0, "o"), ("ventana_3", VECINAS, DIA, 3, "o"),
                                       ("las_dos", VECINAS, DIA, W, "y"), ("todo_el_dia", VECINAS, TODO, W, "o"),
                                       ("solo_antuco", ("antuco",), DIA, W, "o"),
                                       ("solo_longavi", ("longavi",), DIA, W, "o")):
        q = medir_regla(ch25, ch26, CL, compuerta_de(V, "2025", quien, rango, w, modo),
                        compuerta_de(V, "2026", quien, rango, w, modo))
        f26 = f_FA26(placebo(V, "2026", rango, w), rango)[0] if modo == "o" else None
        sens[nom] = {"rotulo": q["rotulo"], "R": _r(q["M2_alcance_2026"]["R"]),
                     "P": [q["M2_alcance_2026"]["P_alcanzados"], q["M2_alcance_2026"]["P_evaluados"]],
                     "p25": q["M2_alcance_2026"]["p25"], "pN": q["M2_alcance_2026"]["pN"], "f_P": _r(q["f_P"]),
                     "f_FA26_vecinas": _r(f26), "seco_2025_global": _r(q["M1_seco_2025"]["global"]),
                     "seco_2025_dia": q["M1_seco_2025"]["dia_12_24"], "perdidos_por_dia": q["perdidos_por_dia"]}
    for q in (sin, principal):
        q["por_dia_P"] = {B.fecha(d): {"alcanzados_antes": a, "perdidos": b} for d, (a, b) in q.pop("_por_dia_P").items()}
    out = {"criterio": "criterio_2026-11-25.md (d5510a5)", "percentil": PSTAR, "regla": "S26a+G: disparo diurno de "
           "Chillán anulado si Antuco o Longaví disparan a ±1 cuadro",
           "dias": {"2025": "21-09 a 21-11-2025 (62, seco)", "2026": "21-09 a 24-11-2026 (65)"},
           "comprobacion": {"vecinas": comp_v, "chillan": comp_ch}, "S26a_sin_compuerta": sin,
           "S26a_G": principal, "M3_placebo_vecinas": m3,
           "M3_f_FA26": {"f": _r(fa26), "anulados": anul26, "disparos_dia": tot26},
           "M3_f_FA25_vecinas_informativo": {"f": _r(fa25v), "anulados": anul25v, "disparos_dia": tot25v},
           "M4_nulo_corrimiento": m4, "M5_selectividad": m5, "veredicto": ver, "sensibilidades": sens,
           "segundos": round(time.time() - t)}
    json.dump(out, open(os.path.join(RES, "s29a_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print(json.dumps({k: out[k] for k in ("veredicto", "M4_nulo_corrimiento", "M5_selectividad", "M3_f_FA26")},
                     ensure_ascii=False, indent=1, default=str))
    print("S26a+G:", principal["rotulo"], principal["M2_alcance_2026"]["P_alcanzados"], "de",
          principal["M2_alcance_2026"]["P_evaluados"], "perdidos", principal["perdidos_por_dia"], flush=True)


# ---------- pruebas ----------
def pruebas():
    G = np.zeros((1, 144), bool)
    G[0, 80] = True
    m = mascara(G, DIA, 1)
    assert m[0, 79:82].all() and m.sum() == 3
    assert mascara(G, NOCHE, 1).sum() == 0                 # sólo de día
    G[0, 143] = True
    assert mascara(G, DIA, 1)[0, 142:144].all()            # sin cruzar al día siguiente
    G2 = np.zeros((1, 144), bool)
    G2[0, 100] = True
    V = {("antuco", "x"): (G, None), ("longavi", "x"): (G2, None)}
    assert compuerta_de(V, "x", VECINAS)[0, [79, 80, 81, 99, 100, 101]].all()
    assert compuerta_de(V, "x", VECINAS, modo="y").sum() == 0
    F = np.zeros((1, 144), bool)
    F[0, [80, 90]] = True
    assert aplicar(F, compuerta_de(V, "x", VECINAS)).sum() == 1
    a = np.zeros((2, 144), bool)
    b = np.zeros((2, 144), bool)
    a[0, 90] = a[1, 95] = True
    b[0, 91] = True
    assert sincronia(a, b) == 1 and sincronia(a, np.roll(b, 1, axis=0)) == 0
    print("pruebas OK")


if __name__ == "__main__":
    {"pruebas": pruebas, "medir": medir}[sys.argv[1]]()
