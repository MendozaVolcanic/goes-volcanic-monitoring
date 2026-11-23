r"""S20c, post hoc (despues de medir, no decide nada): a que capa inyectada equivale la S observada. Para cada prueba
valida, mediana de S en 500 replicas del nulo con la capa de eps pintada (misma maquinaria que el poder), y la S sin
capa. Salida: resultados/posthoc_equivalencia.json."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = ["x"]
import s20c_medir as S
Dt = S.Datos(); QQ, _ = S.cuadros("principal")
EPS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]
out = {}
for modo in ("huella", "anillo"):
    M = S.Motor(Dt, modo, gate_x=True)
    for p in ("H3", "H13", "H11_H12"):
        us = [S.unidad(M, "btd", q["D"], q["s"], q["F"], q["R"], [e for e in EPS if e > 0], leer_x=False) for q in QQ[p]]
        ok, _ = S.cobertura(us)
        r = {}
        for e in EPS:
            Si = S.replicas(ok, 500, np.random.default_rng(S.SEMILLA + 99), iny=(e if e > 0 else None))
            r[str(e)] = float(np.nanmedian(Si))
        out[f"{modo}_{p}"] = r
        print(modo, p, {k: round(v, 3) for k, v in r.items()}, flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados", "posthoc_equivalencia.json"), "w"), indent=1)
