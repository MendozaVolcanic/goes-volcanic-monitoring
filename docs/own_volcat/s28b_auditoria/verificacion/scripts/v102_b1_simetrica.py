r"""V102 (auditoría S28b): la regla B1 de S24 con la selección de "noches comunes" aplicada a un año o a los dos.

Qué hace, en orden:
1. Importa s24_medir.py SIN modificarlo (y por él s23_medir.py y s22b_medir.py) y arma el mismo Detector que medir().
2. Corre pregunta_b() tal cual y compara su B1 con el de resultados/s24_resultado.json (¿el JSON commiteado sale del
   código de hoy?).
3. Repite el conteo por noche con las mismas llamadas (S.disparos, NOCHE, D.umbral) para tener evaluados y disparos
   por noche en los DOS años (pregunta_b sólo guarda el detalle de 2025) y comprueba que los totales coinciden.
4. Aplica la condición de B1 (frac_top5 >= 0,60 y Fisher bilateral p > 0,05) con varias selecciones.
5. Controles: la regla asimétrica aplicada a un año contra sí mismo, y a repartos al azar de las noches entre "años".

No abre ningún cuadro posterior al 24-11-2026: el blanco de s22b_medir termina en NUEVOS[-1] y se comprueba abajo.
No escribe en las carpetas auditadas (correr con -B para no dejar .pyc).

Uso: python -I -B v102_b1_simetrica.py <carpeta_de_salida>
"""
import hashlib
import json
import math
import os
import sys

import numpy as np
from scipy import stats

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))          # docs/own_volcat
S24 = os.path.join(OV, "s24_dia14_noche")
sys.path.insert(0, os.path.join(S24, "scripts"))
import s24_medir as X  # noqa: E402   (sin cambios)

S, B, M = X.S, X.B, X.M
SALIDA = sys.argv[1]
SEMILLA, N_PERM = 0, 10000


def sha(fn):
    return hashlib.sha256(open(fn, "rb").read()).hexdigest()


def fisher(f1, n1, f2, n2):
    """El mismo llamado que s24_medir.py:180."""
    return float(stats.fisher_exact([[f1, n1 - f1], [f2, n2 - f2]], alternative="two-sided")[1])


def b1(f25, n25, f26, n26, sel25, sel26, frac_top):
    """Condición de B1 con una selección de noches por año. sel = lista de claves de noche que ENTRAN."""
    fa, na = sum(f25[d] for d in sel25), sum(n25[d] for d in sel25)
    fb, nb = sum(f26[d] for d in sel26), sum(n26[d] for d in sel26)
    p = fisher(fa, na, fb, nb) if na and nb else None
    ta, tb = (fa / na if na else None), (fb / nb if nb else None)
    epis = bool(p is not None and frac_top >= X.TOP_FRAC and p > 0.05)
    return {"noches_2025": len(sel25), "disparos_2025": fa, "evaluados_2025": na, "tasa_2025": ta,
            "noches_2026": len(sel26), "disparos_2026": fb, "evaluados_2026": nb, "tasa_2026": tb,
            "razon_2026_sobre_2025": (tb / ta if ta else None), "p_fisher": p,
            "rotulo": None if p is None else ("EPISÓDICO" if epis else "NO EPISÓDICO")}


def main():
    os.makedirs(SALIDA, exist_ok=True)
    out = {"entradas": {
        "s24_medir.py": sha(os.path.join(S24, "scripts", "s24_medir.py")),
        "criterio_2026-11-25.md": sha(os.path.join(S24, "criterio_2026-11-25.md")),
        "s24_resultado.json": sha(os.path.join(S24, "resultados", "s24_resultado.json")),
        "s23_medir.py": sha(os.path.join(OV, "s23_fondo_2025", "scripts", "s23_medir.py")),
        "s22b_medir.py": sha(os.path.join(OV, "s22b_pluma_vs_nubes", "scripts", "s22b_medir.py")),
        "estat_2026.npy": sha(X.ESTAT)}}
    # guarda de fechas: el blanco termina el 24-11-2026
    assert B.NUEVOS[-1] == "2026-11-24" and B.fecha(B.ND - 1) == "2026-11-24", (B.NUEVOS, B.fecha(B.ND - 1))
    out["blanco_2026"] = {"primer_dia": B.fecha(0), "ultimo_dia": B.fecha(B.ND - 1), "dias": int(B.ND)}
    out["constantes_s24"] = {"NOCHE": [X.NOCHE.start, X.NOCHE.stop], "COMUN_MAX": X.COMUN_MAX, "TOP": X.TOP,
                             "TOP_FRAC": X.TOP_FRAC}

    estat = np.load(X.ESTAT)
    assert hashlib.sha256(estat.tobytes()).hexdigest()[:16] == X.SHA_ESTAT, "estat_2026 cambió"
    D = S.Detector(ref="2025", con_blanco=True, estat_blanco=estat)
    U0, _ = D.umbral(None)

    # 2. pregunta_b tal cual, contra el JSON commiteado
    hoy = X.pregunta_b(D, U0)
    viejo = json.load(open(os.path.join(S24, "resultados", "s24_resultado.json"), encoding="utf-8"))["B"]
    hoy_rt = json.loads(json.dumps(hoy, ensure_ascii=False))
    out["reproduce_json"] = {k: hoy_rt[k] == viejo[k] for k in ("B1", "B2", "B2_tajadas", "B3")}
    out["B1_de_hoy"] = hoy_rt["B1"]

    # 3. conteo por noche en los dos años, con las mismas llamadas que pregunta_b
    n25, f25 = {}, {}
    for d in D.DIASR:
        Ud, _ = D.umbral(d)
        F, ev = S.disparos(D.SR, D.KR, d, Ud)
        sl = [s for s in X.NOCHE if ev[s]]
        k = f"{S.T0R + S.timedelta(days=d):%Y-%m-%d}"
        n25[k], f25[k] = len(sl), int(sum(F[s] for s in sl))
    n26, f26 = {}, {}
    for d in range(B.ND):
        F, ev = S.disparos(D.ST, D.KT, d, U0)
        sl = [s for s in X.NOCHE if ev[s]]
        n26[B.fecha(d)], f26[B.fecha(d)] = len(sl), int(sum(F[s] for s in sl))
    assert max(n26) <= "2026-11-24"
    b = hoy["B1"]
    assert sum(f25.values()) == b["disparos_noche_2025"] and sum(n25.values()) == b["evaluados_noche_2025"]
    assert sum(f26.values()) == b["disparos_noche_2026"] and sum(n26.values()) == b["evaluados_noche_2026"]
    out["por_noche_2025"] = {k: [f25[k], n25[k]] for k in sorted(n25)}
    out["por_noche_2026"] = {k: [f26[k], n26[k]] for k in sorted(n26)}
    out["noches_con_evaluados"] = {"2025": sum(1 for k in n25 if n25[k]), "2026": sum(1 for k in n26 if n26[k])}
    out["noches_con_3_o_mas"] = {"2025": {k: [f25[k], n25[k]] for k in sorted(n25) if f25[k] >= X.COMUN_MAX},
                                 "2026": {k: [f26[k], n26[k]] for k in sorted(n26) if f26[k] >= X.COMUN_MAX}}
    out["noches_con_disparo"] = {"2025": {k: [f25[k], n25[k]] for k in sorted(n25) if f25[k]},
                                 "2026": {k: [f26[k], n26[k]] for k in sorted(n26) if f26[k]}}

    tot25, tot26 = sum(f25.values()), sum(f26.values())
    ft25 = sum(sorted(f25.values(), reverse=True)[:X.TOP]) / tot25
    ft26 = sum(sorted(f26.values(), reverse=True)[:X.TOP]) / tot26 if tot26 else None
    out["frac_top5"] = {"2025": ft25, "2026": ft26}
    todo25, todo26 = list(n25), list(n26)
    com25 = [k for k in n25 if f25[k] < X.COMUN_MAX]
    com26 = [k for k in n26 if f26[k] < X.COMUN_MAX]

    # 4. variantes de la selección
    V = {}
    V["0_regla_escrita (2025 comunes vs 2026 entero)"] = b1(f25, n25, f26, n26, com25, todo26, ft25)
    assert abs(V["0_regla_escrita (2025 comunes vs 2026 entero)"]["p_fisher"] - b["p_fisher_comunes_vs_2026"]) < 1e-15
    V["a_simetrica (comunes vs comunes, umbral 3 del criterio)"] = b1(f25, n25, f26, n26, com25, com26, ft25)
    V["b_sin_seleccion (entero vs entero)"] = b1(f25, n25, f26, n26, todo25, todo26, ft25)
    V["espejo (2025 entero vs 2026 comunes)"] = b1(f25, n25, f26, n26, todo25, com26, ft25)
    # c: quitar la misma FRACCIÓN de noches (las de más disparos) en cada año
    for nom, base in (("todas las noches", lambda n: list(n)), ("noches con evaluados", lambda n: [k for k in n if n[k]])):
        b25, b26 = base(n25), base(n26)
        frac = (len(n25) - len(com25)) / len(b25)
        q26 = int(round(frac * len(b26)))
        orden26 = sorted(b26, key=lambda k: (-f26[k], k))
        quita = orden26[:q26]
        r = b1(f25, n25, f26, n26, com25, [k for k in n26 if k not in quita], ft25)
        r["fraccion_quitada"], r["quitadas_2026"] = frac, {k: f26[k] for k in quita}
        V[f"c_misma_fraccion_de_noches (base: {nom})"] = r
    # d: selección por TASA de la noche (la cuenta absoluta depende de cuántos cuadros pasan la compuerta)
    tmin = min(f25[k] / n25[k] for k in n25 if f25[k] >= X.COMUN_MAX)
    r = b1(f25, n25, f26, n26, [k for k in n25 if not n25[k] or f25[k] / n25[k] < tmin],
           [k for k in n26 if not n26[k] or f26[k] / n26[k] < tmin], ft25)
    r["tasa_minima_de_noche_quitada_en_2025"] = tmin
    V["d_simetrica_por_tasa_de_la_noche (sensibilidad mía, post hoc)"] = r
    out["variantes"] = V

    # sensibilidad al umbral, simétrica y asimétrica
    out["umbral"] = {}
    for T in range(1, 9):
        c25, c26 = [k for k in n25 if f25[k] < T], [k for k in n26 if f26[k] < T]
        out["umbral"][str(T)] = {"asimetrica": b1(f25, n25, f26, n26, c25, todo26, ft25),
                                 "simetrica": b1(f25, n25, f26, n26, c25, c26, ft25)}

    # sin una noche de 2026 (la regla escrita, 2026 entero menos esa noche)
    out["sin_una_noche_2026"] = {k: b1(f25, n25, f26, n26, com25, [x for x in n26 if x != k], ft25)
                                 for k in sorted(n26) if f26[k]}

    # unidad = noche (los cuadros de una noche no son independientes; criterio §4)
    def noches(f, n, sel):
        ev = [k for k in sel if n[k]]
        return sum(1 for k in ev if f[k]), len(ev)
    un = {}
    for nom, s25, s26 in (("regla escrita", com25, todo26), ("simétrica", com25, com26), ("sin selección", todo25, todo26)):
        a, na = noches(f25, n25, s25)
        c, nc = noches(f26, n26, s26)
        un[nom] = {"noches_con_disparo_2025": a, "noches_2025": na, "noches_con_disparo_2026": c, "noches_2026": nc,
                   "p_fisher": fisher(a, na, c, nc)}
    out["unidad_noche"] = un

    # 5a. control: la regla asimétrica aplicada a un año contra sí mismo
    out["control_mismo_ano"] = {
        "2025 comunes vs 2025 entero": b1(f25, n25, f25, n25, com25, todo25, ft25),
        "2026 comunes vs 2026 entero": b1(f26, n26, f26, n26, com26, todo26, ft26)}

    # 5b. control: noches repartidas al azar entre dos "años" (62 y 65), regla asimétrica y simétrica
    rng = np.random.default_rng(SEMILLA)
    pool = [(f25[k], n25[k]) for k in sorted(n25)] + [(f26[k], n26[k]) for k in sorted(n26)]
    pf, pn = np.array([x[0] for x in pool]), np.array([x[1] for x in pool])
    na_ = len(n25)
    obs_razon = V["0_regla_escrita (2025 comunes vs 2026 entero)"]["razon_2026_sobre_2025"]
    cuenta = {"asim_p_le_0.05": 0, "asim_p_le_0.05_y_B_mayor": 0, "asim_razon_ge_obs": 0, "asim_p_le_obs": 0,
              "sim_p_le_0.05": 0, "sin_sel_p_le_0.05": 0, "asim_tasa_comun_cero": 0}
    p_obs = b["p_fisher_comunes_vs_2026"]
    for _ in range(N_PERM):
        idx = rng.permutation(len(pool))
        A, Bq = idx[:na_], idx[na_:]
        ca = A[pf[A] < X.COMUN_MAX]
        cb = Bq[pf[Bq] < X.COMUN_MAX]
        fa, nA, fb, nB = pf[ca].sum(), pn[ca].sum(), pf[Bq].sum(), pn[Bq].sum()
        p = fisher(int(fa), int(nA), int(fb), int(nB))
        ta, tb = fa / nA, fb / nB
        cuenta["asim_p_le_0.05"] += p <= 0.05
        cuenta["asim_p_le_0.05_y_B_mayor"] += (p <= 0.05) and (tb > ta)
        cuenta["asim_p_le_obs"] += p <= p_obs
        cuenta["asim_tasa_comun_cero"] += fa == 0
        cuenta["asim_razon_ge_obs"] += (fa == 0 and fb > 0) or (fa > 0 and tb / ta >= obs_razon)
        cuenta["sim_p_le_0.05"] += fisher(int(fa), int(nA), int(pf[cb].sum()), int(pn[cb].sum())) <= 0.05
        cuenta["sin_sel_p_le_0.05"] += fisher(int(pf[A].sum()), int(pn[A].sum()), int(fb), int(nB)) <= 0.05
    out["control_reparto_al_azar"] = {"n_perm": N_PERM, "semilla": SEMILLA, "razon_observada": obs_razon,
                                      "p_observado": p_obs, **{k: int(v) for k, v in cuenta.items()},
                                      "fraccion": {k: float(v) / N_PERM for k, v in cuenta.items()}}

    def limpia(o):
        if isinstance(o, dict):
            return {k: limpia(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [limpia(v) for v in o]
        if isinstance(o, (np.floating, float)):
            return None if not math.isfinite(float(o)) else float(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, np.bool_):
            return bool(o)
        return o
    out = limpia(out)
    json.dump(out, open(os.path.join(SALIDA, "v102_salida.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("por_noche_2025", "por_noche_2026")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
