r"""H27, paso 0b (antes del criterio): conteo con las cumbres de control usando TODOS los dias (no tienen actividad
que excluir) y candidatas de cumbre extra elegidas por regla sobre el DEM (maximo local >= 2.800 m, anillo de 25 km
dentro de la ventana, a >= 35 km de Chillan, Antuco y Longavi y entre si). Solo cuenta escenas despejadas.
Salida: resultados\h27_conteo_fondo_2.json. Uso: python -I h27_contar2.py
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


def candidatas():
    Z = H.ZDEM.reshape(H.NY, H.NX)
    la, lo = H.LAT.reshape(H.NY, H.NX), H.LON.reshape(H.NY, H.NX)
    c = []
    for i in range(2, H.NY - 2):
        for j in range(2, H.NX - 2):
            v = Z[i, j]
            if not np.isfinite(v) or v < 2800 or v < np.nanmax(Z[i - 2:i + 3, j - 2:j + 3]):
                continue
            c.append((float(v), float(la[i, j]), float(lo[i, j])))
    c.sort(reverse=True)
    elegidas = []
    fijos = [H.SITIOS[s][:2] for s in H.SITIOS]
    for v, a, o in c:
        # anillo de 25 km (mas paralaje ~ 5 km hacia el S) dentro de la ventana
        if not (H.LAT.min() + 0.33 < a < H.LAT.max() - 0.28 and H.LON.min() + 0.36 < o < H.LON.max() - 0.36):
            continue
        if min(H.hav(np.array([a]), np.array([o]), *p)[0] for p in fijos + [e[1:] for e in elegidas]) < 35:
            continue
        elegidas.append((v, a, o))
    return elegidas


def main():
    cand = candidatas()
    print("candidatas:", [(round(v), round(a, 3), round(o, 3)) for v, a, o in cand])
    for k, (v, a, o) in enumerate(cand):
        H.SITIOS[f"c{k + 1}"] = (a, o, v)
    r14, r15, acm, co14, co15 = H.cargar()
    del r15
    hay = np.isfinite(r14).any(2)
    del r14
    F = {s: H.despejada(s, acm) & hay for s in H.SITIOS}
    ven = H.ventanas()
    libres = ~H.DIA_EXCL
    out = {"candidatas": cand, "por_episodio": {}}
    for eid in ("E9", "E10", "E11", "E12", "E13", "E14", "E1", "E6", "E7"):
        d0, slots = ven[eid]
        fila = {}
        for ancho in (0, 6, 12):
            ss = sorted({x for s in slots for x in range(s - ancho, s + ancho + 1) if 0 <= x < 144})
            todos = [d for d in range(H.NDIAS) if d != d0]
            c = {"chillan_libres": int(sum(F["chillan"][d, ss].any() for d in todos if libres[d]))}
            for s in H.SITIOS:
                if s != "chillan":
                    c[s] = int(sum(F[s][d, ss].any() for d in todos))
            ctl = [s for s in H.SITIOS if s != "chillan"]
            c["algun_control_dia_sitio"] = int(sum(F[s][d, ss].any() for d in todos for s in ctl))
            fila[f"ancho{ancho}"] = c
        fila["episodio_despejado"] = {s: int(F[s][d0, slots].sum()) for s in H.SITIOS}
        out["por_episodio"][eid] = fila
        print(eid, fila, flush=True)
    json.dump(out, open(os.path.join(RES, "h27_conteo_fondo_2.json"), "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
