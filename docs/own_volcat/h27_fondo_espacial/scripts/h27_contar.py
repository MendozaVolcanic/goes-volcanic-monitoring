r"""H27, paso 0 (antes de disenar el criterio): cuantos cuadros y dias de fondo de tarde hay.

No calcula ningun estadistico de deteccion: solo cuenta escenas despejadas (regla H23 E1 de h24_medir.despejada) por
sitio, por ventana horaria y por dia no excluido. Salida: resultados\h27_conteo_fondo.json.
Uso: python -I h27_contar.py
"""
import json
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "h24_pulsos_reav", "scripts"))
import h24_medir as H  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RES = os.path.join(os.path.dirname(AQUI), "resultados")


def main():
    r14, r15, acm, co14, co15 = H.cargar()
    del r15
    hay = np.isfinite(r14).any(2)                      # (dia, slot) con dato
    del r14
    F = {s: H.despejada(s, acm) & hay for s in H.SITIOS}
    ven = H.ventanas()
    libres = ~H.DIA_EXCL
    out = {"dias_no_excluidos": int(libres.sum()), "por_episodio": {}}
    for e in H.EPISODIOS:
        eid = e[0]
        d0, slots = ven[eid]
        fila = {"dia": int(d0), "slots": [int(s) for s in slots],
                "episodio_despejado": {s: int(F[s][d0, slots].sum()) for s in H.SITIOS}}
        for ancho in (0, 6, 12):                        # +-0, +-1 h, +-2 h alrededor de la ventana
            ss = sorted({x for s in slots for x in range(s - ancho, s + ancho + 1) if 0 <= x < 144})
            for alc, dias in (("pm21", [d for d in range(max(0, d0 - 21), min(H.NDIAS, d0 + 22)) if d != d0]),
                              ("todo", [d for d in range(H.NDIAS) if d != d0])):
                dias = [d for d in dias if libres[d]]
                c = {}
                for s in H.SITIOS:
                    c[f"dias_{s}"] = int(sum(F[s][d, ss].any() for d in dias))
                    c[f"cuadros_{s}"] = int(sum(F[s][d, ss].sum() for d in dias))
                for ctl in ("antuco", "longavi"):
                    j = [F["chillan"][d, ss] & F[ctl][d, ss] for d in dias]
                    c[f"dias_chillan_y_{ctl}"] = int(sum(x.any() for x in j))
                    c[f"cuadros_chillan_y_{ctl}"] = int(sum(x.sum() for x in j))
                j = [F["antuco"][d, ss] & F["longavi"][d, ss] for d in dias]
                c["dias_antuco_y_longavi"] = int(sum(x.any() for x in j))
                fila[f"ancho{ancho}_{alc}"] = c
        out["por_episodio"][eid] = fila
        print(eid, fila["episodio_despejado"], "+-2h todo:", fila["ancho12_todo"], flush=True)
    # tarde completa 14-24 UTC, todo el periodo
    ss = list(range(84, 144))
    out["tarde_14_24"] = {s: {"dias": int(sum(F[s][d, ss].any() for d in range(H.NDIAS) if libres[d])),
                              "cuadros": int(sum(F[s][d, ss].sum() for d in range(H.NDIAS) if libres[d]))}
                          for s in H.SITIOS}
    print("tarde 14-24:", out["tarde_14_24"])
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "h27_conteo_fondo.json"), "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
