r"""S31h post hoc (escrito después de ver la medida; no decide nada). Lee los cubos de la corona que dejó s31h_medir.py
en D:\goes_notas\s31\s31h\ y rearma sólo la referencia de 2025 (para el umbral). Responde tres cosas:

1. ¿Por qué 41 de los 100 cuadros P de VOLCAT quedaron sin evaluar por "tajadas"? Fracción de píxeles de la corona sin
   z, por tajada, en cuadros P y N de 2026 que pasan la compuerta.
2. ¿Dónde y cuándo dispara la corona en 2024 (falsa alarma NO AGUANTA)? Por día y noche, por día del año y por tajada.
3. La misma cuenta para 2026 sin VOLCAT (cuadros N).

Uso: python -I -B s31h_posthoc.py
"""
import json
import os
import sys
from collections import Counter

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s31h_medir as H  # noqa: E402

S, B, M, E31 = H.S, H.B, H.M, H.E31


def main():
    out = {"rotulo": "POST HOC: escrito después de ver la medida; no decide"}
    D = S.Detector(ref="2025", con_blanco=True, estat_blanco=np.load(H.A26.ESTAT26))
    CL = D.CLT
    for v in H.VARS:
        z = np.load(os.path.join(H.TRAB, f"corona_{v}.npz"))
        U = E31.umbral(D, z["S25"], 6.0, None)
        o = {}
        # 1. píxeles sin z en P y N de 2026 con compuerta
        Z26 = z["Z26"]
        for cl in ("P", "N"):
            sel = [(d, s) for d in range(B.ND) for s in range(144) if CL[d, s] == cl and D.GATET[d, s]]
            fr = np.array([np.isnan(Z26[d, s]).mean() for d, s in sel])
            taj = np.array([[np.isfinite(Z26[d, s][H.TAJ[k]]).sum() >= H.MIN_VAL for k in range(12)] for d, s in sel])
            o[f"2026_{cl}"] = {"cuadros_con_compuerta": len(sel),
                               "frac_px_sin_z_mediana": round(float(np.median(fr)), 3),
                               "evaluables": int(np.isfinite([z["S26"][d, s] for d, s in sel]).sum()),
                               "frac_tajada_valida": [round(float(x), 2) for x in taj.mean(0)]}
        # 2 y 3. disparos de 2024 y de 2026 (N) por noche/día, día del año y tajada
        for anio, SS, KK in (("2024", z["S24"], z["K24"]), ("2026", z["S26"], z["K26"])):
            disp = [(d, int(s)) for d in range(SS.shape[0]) for s in np.flatnonzero(S.disparos(SS, KK, d, U)[0])]
            if anio == "2026":
                disp = [(d, s) for d, s in disp if CL[d, s] == "N"]
            noche = [x for x in disp if x[1] < 72]
            o[f"disparos_{anio}"] = {
                "n": len(disp), "noche_00_12_UTC": len(noche),
                "tajadas_noche": np.bincount([KK[d, s] for d, s in noche], minlength=12).tolist(),
                "tajadas_dia": np.bincount([KK[d, s] for d, s in disp if s >= 72], minlength=12).tolist(),
                "dias_con_mas": Counter(d for d, _ in disp).most_common(5)}
        out[v] = o
        print(v, json.dumps(o, ensure_ascii=False), flush=True)
    json.dump(out, open(os.path.join(H.RES, "s31h_posthoc.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              default=lambda x: x.item() if hasattr(x, "item") else str(x))


if __name__ == "__main__":
    main()
