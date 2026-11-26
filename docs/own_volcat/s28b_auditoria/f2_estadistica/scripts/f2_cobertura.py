r"""F2 (S28b): cobertura pareja. Cuadros evaluados por año y franja de 3 h, y fracción de P evaluados contra la de N.

Por qué (§3b fila 2 de la guía): si el detector evalúa los P mucho más (o menos) que los N, o 2026 en otras horas que
2025, las tasas que se comparan no miran lo mismo. Lee cubos_f2.npz (f2_cubos.py) y, para 2024, s25b_resultado.json.
Uso: python -I f2_cobertura.py
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
OV = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
SAL = r"D:\goes_notas\s28\s28b\f2"


def main():
    Z = np.load(os.path.join(SAL, "cubos_f2.npz"))
    CL = Z["CL"]
    out = {}
    for nom, k25, k26 in (("S23a anillo (costumbre 2025)", "a500", "s23a"), ("S23b anillo", "a500", "a500"),
                          ("S25a zona", "z500", "z500"), ("S26a union p4.75", "u475", "u475")):
        ev25, ev26 = Z[f"ev25_{k25}"], Z[f"ev26_{k26}"]
        con_clase = CL != ""
        fr = {}
        for b in range(8):
            sl = slice(18 * b, 18 * b + 18)
            n25 = int(ev25[:, sl].sum())
            n26 = int(ev26[:, sl].sum())
            fr[f"{3 * b:02d}-{3 * b + 2:02d}"] = {"2025_eval": n25, "2025_frac": round(n25 / (62 * 18), 3),
                                                  "2026_eval": n26, "2026_frac": round(n26 / (65 * 18), 3),
                                                  "P": int((CL[:, sl] == "P").sum()),
                                                  "P_eval": int(((CL[:, sl] == "P") & ev26[:, sl]).sum()),
                                                  "N": int((CL[:, sl] == "N").sum()),
                                                  "N_eval": int(((CL[:, sl] == "N") & ev26[:, sl]).sum())}
        nP, nN = int((CL == "P").sum()), int((CL == "N").sum())
        eP, eN = int(((CL == "P") & ev26).sum()), int(((CL == "N") & ev26).sum())
        out[nom] = {"P_eval/P": [eP, nP, round(eP / nP, 3)], "N_eval/N": [eN, nN, round(eN / nN, 3)],
                    "2026_eval_con_clase": int((ev26 & con_clase).sum()), "2026_eval_sin_clase": int((ev26 & ~con_clase).sum()),
                    "dias_2026_con_clase": int(con_clase.any(1).sum()), "franjas": fr}
        print(nom, out[nom]["P_eval/P"], out[nom]["N_eval/N"])
        for k, v in fr.items():
            print("   ", k, v)
    J = json.load(open(os.path.join(OV, "s25b_fondo_2024", "resultados", "s25b_resultado.json"), encoding="utf-8"))
    out["2024_S25b"] = {v: {"evaluados": J["b"][v]["evaluados"],
                            "franjas_n": {k: x["n"] for k, x in J["b"][v]["por_franja_2024"].items()},
                            "frac_pasan_compuerta": J["b"][v]["frac_pasan_compuerta"]} for v in ("S23a", "S23b")}
    print("2024", json.dumps(out["2024_S25b"]))
    json.dump(out, open(os.path.join(SAL, "cobertura.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
