r"""V202/V204/V205 (verificador, S28b): reconstruye los disparos por cuadro de S25a (zona), S26a (unión a p*) y S23a
(anillo con el nublado de costumbre de 2025) con las funciones de los scripts auditados, sin modificarlas, y los guarda
en D:\goes_notas\s28\s28b\v202\cubos_v202.npz. Primero comprueba que reproduce los conteos publicados:
S25a 44 de 93, S26a 63 de 93, S23a 8 de 30. Si no reproduce, sale con error.

Sólo días hasta el 24-11-2026 (B.ND = 65 días: 21-09 a 24-11-2026). No importa ni corre s23b_confirmar.py.
Uso: python -I -B v202_cubos.py
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s26a_combinado", "scripts"))
import s26a_medir as U  # noqa: E402

S, Z, B, M = U.S, U.Z, U.B, U.M
SAL = r"D:\goes_notas\s28\s28b\v202"
assert B.ND == 65 and B.fecha(B.ND - 1) == "2026-11-24", (B.ND, B.fecha(B.ND - 1))


def pila(dias, k=None):
    F = np.array([(x[k] if k else x)[0] for x in dias])
    ev = np.array([(x[k] if k else x)[1] for x in dias])
    return F, ev


def main():
    os.makedirs(SAL, exist_ok=True)
    out, rep = {}, {}
    X = U.Partes()
    CL = X.CL
    assert CL.shape == (65, 144)
    out["CL"] = CL.astype(str)
    # ---- percentil 5: zona = S25a; anillo = candidata S23b ----
    sec5 = X.seco(5.0)
    res5, _, _ = X.blanco(5.0)
    for k, nom in (("z", "z5"), ("a", "a5"), ("u", "u5")):
        out[nom + "_F25"], out[nom + "_ev25"] = pila(sec5[k])
        out[nom + "_F26"], out[nom + "_ev26"] = pila(res5, k)
    rz = U.recuerdo(U.lista(res5, CL, "z"), U.azar(sec5["z"]))
    rep["S25a_zona_pct5"] = rz
    # ---- p* = 4,75: la unión de S26a ----
    seco_pub = json.load(open(os.path.join(OV, "s26a_combinado", "resultados", "s26a_seco.json"), encoding="utf-8"))
    pstar = seco_pub["p_estrella"]
    assert pstar == 4.75, pstar
    sec = X.seco(pstar)
    res, _, _ = X.blanco(pstar)
    for k, nom in (("z", "zp"), ("a", "ap"), ("u", "up")):
        out[nom + "_F25"], out[nom + "_ev25"] = pila(sec[k])
        out[nom + "_F26"], out[nom + "_ev26"] = pila(res, k)
    ru = U.recuerdo(U.lista(res, CL, "u"), U.azar(sec["u"]))
    rep["S26a_union_pstar"] = ru
    rep["S26a_anillo_pstar"] = U.recuerdo(U.lista(res, CL, "a"), U.azar(sec["a"]))
    rep["S26a_zona_pstar"] = U.recuerdo(U.lista(res, CL, "z"), U.azar(sec["z"]))
    del X
    # ---- S23a publicado: anillo, percentil 5, nublado de costumbre de 2025 también para 2026 ----
    U._pct(5.0)
    D = S.Detector(ref="2025", con_blanco=True)
    F25, ev25 = [], []
    for d in D.DIASR:
        Ud, _ = D.umbral(d)
        F, ev = S.disparos(D.SR, D.KR, d, Ud)
        F25.append(F)
        ev25.append(ev)
    U0, _ = D.umbral(None)
    FF = [S.disparos(D.ST, D.KT, d, U0) for d in range(B.ND)]
    out["s23a_F25"], out["s23a_ev25"] = np.array(F25), np.array(ev25)
    out["s23a_F26"], out["s23a_ev26"] = pila(FF)
    out["s23a_K26"] = D.KT
    out["s23a_K25"] = D.KR
    res23 = [{"a": x} for x in FF]
    sec23 = list(zip(F25, ev25))
    rep["S23a_anillo_pct5_estat2025"] = U.recuerdo(U.lista(res23, CL, "a"), U.azar(sec23))
    np.savez_compressed(os.path.join(SAL, "cubos_v202.npz"), **out)
    json.dump(rep, open(os.path.join(SAL, "reproduccion.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    ok = ((rz["P_alcanzados"], rz["P_evaluados"]) == (44, 93) and (ru["P_alcanzados"], ru["P_evaluados"]) == (63, 93)
          and (rep["S23a_anillo_pct5_estat2025"]["P_alcanzados"], rep["S23a_anillo_pct5_estat2025"]["P_evaluados"]) == (8, 30))
    print("REPRODUCE los conteos publicados (44/93, 63/93, 8/30):", "SÍ" if ok else "NO")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
