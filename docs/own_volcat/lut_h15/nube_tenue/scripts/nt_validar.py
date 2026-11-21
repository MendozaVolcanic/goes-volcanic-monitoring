r"""Nube tenue: VALIDACIÓN (decide). Cuadros 6 a 10 de Mauna Loa, nivel A, regla NT = R1 + R2 + R3 fijada en
../criterio_2026-11-21.md (commit f5f97d5, subido antes de este script).

Informa por tramo de εtot (< 0,2 y 0,2 a 0,5, los que deciden; >= 0,5 y conjunto, informativos) las tres métricas
del criterio, la fracción exacta, la base sin reglas, cada regla sola y el nivel B. Para la condición 3 con pocos
píxeles da el intervalo de Wilson al 95 %.
Salida: ../resultados/nt_validacion.json y ../resultados/nt_validacion.txt
Uso: python -I nt_validar.py
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_comun as N  # noqa: E402
import nt_regla as R  # noqa: E402

LV, E = N.LV, N.E
TRAMOS = (("eps<0,2", -np.inf, 0.2), ("eps 0,2-0,5", 0.2, 0.5), ("eps>=0,5", 0.5, np.inf), ("todo", -np.inf, np.inf))


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    f = k / n
    d = 1 + z * z / n
    c = (f + z * z / (2 * n)) / d
    h = z * np.sqrt(f * (1 - f) / n + z * z / (4 * n * n)) / d
    return (float(c - h), float(c + h))


def medir(L, ent, v, sat, lv):
    P = LV.prob(L)
    eps = ent["eps"]
    r = {}
    for tn, a, b in TRAMOS:
        s = np.isfinite(eps) & (eps >= a) & (eps < b) if np.isfinite(a) or np.isfinite(b) else np.ones(len(v), bool)
        m = E.metricas(P[s], v[s])
        k = int(((P >= 0.5) & (v >= 0.5) & s).sum())
        m["recuperados_k"] = k
        m["recuperados_ic95"] = wilson(k, m["n_volcat_ge05"])
        m["frac_exacta_no_saturados"] = float(np.mean(np.abs(L - lv)[s & sat] < 1e-3))
        m["cumple"] = E.cumple(m)
        r[tn] = m
    return r


def cond85(ent):
    return ~((ent["eps"] < 0.1) & (ent["b85"] > 1.05) & (ent["b85"] < 2.0))


def main():
    gfs = dict(np.load(os.path.join(E.ML, "gfs_ttropo.npz")))
    ent, agua, v, q = N.cargar(E.VALIDA)
    lv = N.logit(v)
    sat = N.no_saturado(v)
    C0 = R.contribuciones(ent, agua, r2=False)
    C2 = R.contribuciones(ent, agua, r2=True)
    var = {
        "NT (R1+R2+R3), decide": R.logit_regla(C2, ent, r1=True, cond85=cond85(ent)),
        "base (7 tablas)": R.logit_regla(C0, ent, r1=False),
        "sólo R1": R.logit_regla(C0, ent, r1=True),
        "sólo R2": R.logit_regla(C2, ent, r1=False),
        "R1+R2": R.logit_regla(C2, ent, r1=True),
    }
    out = {"cuadros": E.VALIDA, "n_pixeles": int(len(v)), "variantes_nivelA": {}}
    for nom, L in var.items():
        out["variantes_nivelA"][nom] = medir(L, ent, v, sat, lv)
    # nivel B: nuestro εtot, β(12/11) y β(7,3/11) con el cielo despejado de VOLCAT (como en la etapa 2); tramos
    # por el εtot de VOLCAT para que los píxeles sean los mismos
    Bs, vs = [], []
    for h in E.VALIDA:
        A, B, ag, vv = E.cuadro(h, gfs)
        Bs.append((B, ag)); vs.append(vv)
    entB = {k: np.concatenate([b[0][k] for b in Bs]) for k in Bs[0][0]}
    agB = np.concatenate([b[1] for b in Bs])
    C2B = R.contribuciones(entB, agB, r2=True)
    LB = R.logit_regla(C2B, entB, r1=True, cond85=cond85(entB))
    entB_tr = dict(entB); entB_tr["eps"] = ent["eps"]
    out["nivelB_NT_tramos_por_eps_VOLCAT"] = medir(LB, entB_tr, v, sat, lv)
    nt = out["variantes_nivelA"]["NT (R1+R2+R3), decide"]
    out["validada_eps<0,2"] = nt["eps<0,2"]["cumple"]
    out["validada_eps_0,2-0,5"] = nt["eps 0,2-0,5"]["cumple"]
    out["lectura_validada_en_nube_tenue"] = bool(out["validada_eps<0,2"] and out["validada_eps_0,2-0,5"])
    res = os.path.join(N.RES, "nt_validacion.json")
    with open(res, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    with open(os.path.join(N.RES, "nt_validacion.txt"), "w", encoding="utf-8") as f:
        def p(*a):
            print(*a); print(*a, file=f)
        p(f"Cuadros 6 a 10 ({', '.join(E.VALIDA)}), {len(v)} píxeles. Nivel A salvo indicación.")
        p("variante | tramo | n | n P_V>=0,5 | |dP|<=0,05 | κ | recuperados (IC95) | exacta | cumple")
        filas = list(out["variantes_nivelA"].items()) + [("nivel B, NT", out["nivelB_NT_tramos_por_eps_VOLCAT"])]
        for nom, r in filas:
            for tn, m in r.items():
                ic = m["recuperados_ic95"]
                p(f"{nom:24s} | {tn:11s} | {m['n']:6d} | {m['n_volcat_ge05']:5d} | {m['frac_dif_le_005']:.4f} | "
                  f"{m['kappa_05']:.4f} | {m['frac_ge05_recuperada']:.4f} ({ic[0]:.3f}-{ic[1]:.3f}) | "
                  f"{m['frac_exacta_no_saturados']:.4f} | {'sí' if m['cumple'] else 'no'}")
        p(f"\nVEREDICTO: eps<0,2 {'cumple' if out['validada_eps<0,2'] else 'NO cumple'}; "
          f"0,2-0,5 {'cumple' if out['validada_eps_0,2-0,5'] else 'NO cumple'}; "
          f"lectura validada en nube tenue: {'SÍ' if out['lectura_validada_en_nube_tenue'] else 'NO'}")


if __name__ == "__main__":
    main()
