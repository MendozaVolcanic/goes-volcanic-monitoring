r"""S30a, informativo y POST HOC: qué escribiría la regla de la enmienda si dos días ya vistos de 2026 con P de VOLCAT
fueran los "días nuevos". No decide nada (esos días eligieron las reglas); sirve para leer el poder con plumas reales y
como referencia del ensayo del envoltorio (08-11 y 14-11).

Para cada regla y cada par ordenado de días reales con P (sólo pares que suman 20 P o más, el gatillo): R observado, p
del nulo de 2025 (referencia = 62 días de 2025 + los dos días), p del de 2026 sin VOLCAT y p del de 2024, y el rótulo
con el alfa y las variantes de la enmienda §5.3.

Uso: python -I -B s30a_desarrollo.py      Salida: resultados/s30a_desarrollo_pares.json
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, AQUI)
import s30a_confirmar as C  # noqa: E402
import s30a_nulo as N  # noqa: E402


def main():
    Zf = np.load(C.FONDO_NPZ)
    CL = Zf["CL"]
    dias26 = [str(x) for x in Zf["dias26"]]
    assert max(dias26) == "2026-11-24"
    sinP = [d for d in range(65) if not (CL[d] == "P").any()]
    conP = [d for d in range(65) if (CL[d] == "P").any()]
    out = {"alfa": C.ALFA, "variantes": {k: v["deciden"] for k, v in C.REGLAS.items()}, "pares": []}
    for nom, rg in C.REGLAS.items():
        k, p = rg["parte"], rg["pct"]
        F26, E26 = Zf[f"F26_{k}_{p}"], Zf[f"E26_{k}_{p}"]
        AL26 = np.array([N.alcanzado_dia(F26[d], E26[d]) for d in range(65)])
        fondos = {}
        for nf, (E, F, pool) in {"2025": (Zf[f"E25_{k}_{p}"], Zf[f"F25_{k}_{p}"], None),
                                 "2026 sin VOLCAT": (Zf[f"E26_{k}_{p}"], Zf[f"F26_{k}_{p}"], sinP),
                                 "2024": (Zf[f"E24_{k}_{p}"], Zf[f"F24_{k}_{p}"], None)}.items():
            AL = np.array([N.alcanzado_dia(F[d], E[d]) for d in range(len(E))])
            fondos[nf] = (np.asarray(E, bool), AL, list(range(len(E))) if pool is None else list(pool))
        for a in conP:
            for b in conP:
                if a >= b or (CL[a] == "P").sum() + (CL[b] == "P").sum() < 20:
                    continue
                dd = [a, b]
                masc = np.array([CL[d] == "P" for d in dd])
                e_obs = np.array([int((masc[i] & E26[d]).sum()) for i, d in enumerate(dd)])
                a_obs = np.array([int((masc[i] & E26[d] & AL26[d]).sum()) for i, d in enumerate(dd)])
                fila = {"regla": nom, "dias": [dias26[d] for d in dd], "P": [int(m.sum()) for m in masc],
                        "P_evaluados": e_obs.tolist(), "P_alcanzados": a_obs.tolist(),
                        "R": float(a_obs.sum() / e_obs.sum()) if e_obs.sum() else None, "p": {}}
                if N.decidible(e_obs):
                    for nf, (E, AL, pool) in fondos.items():
                        if nf == "2026 sin VOLCAT":
                            pool = [x for x in pool if x not in dd]
                        nd = len(E)
                        EVr = np.concatenate([E, E26[dd]])
                        ALr = np.concatenate([AL, AL26[dd]])
                        ef, af = N.tabla_fondo(masc, EVr, ALr)
                        pv, R, nv, ng, nt = N.p_dia(e_obs, a_obs, ef, af, pool + [nd, nd + 1], obs=[nd, nd + 1])
                        fila["p"][nf] = {"p_dia": pv, "validas": nv}
                    ps = [fila["p"][f]["p_dia"] for f in rg["deciden"]]
                    nvs = [fila["p"][f]["validas"] for f in rg["deciden"]]
                    fila["veredicto_enmienda"] = N.veredicto(e_obs, a_obs, max(ps), min(nvs), C.ALFA, rg["r_min"])
                else:
                    fila["veredicto_enmienda"] = "NO DECIDIBLE"
                out["pares"].append(fila)
                print(nom, fila["dias"], fila["P_evaluados"], fila["P_alcanzados"], round(fila["R"] or 0, 3),
                      {f: round(x["p_dia"], 5) for f, x in fila["p"].items()}, fila["veredicto_enmienda"], flush=True)
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "s30a_desarrollo_pares.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)


if __name__ == "__main__":
    main()
