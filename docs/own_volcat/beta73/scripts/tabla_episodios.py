"""beta73: tabla por episodio (dia y estrato) y por par del estrato N, para el informe. Solo lee senales_b73.pkl."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import os, pickle
import numpy as np
import comun_b73 as C
from metricas_b73 import auc, pool

S = [p for p in pickle.load(open(os.path.join(C.HERE, "senales_b73.pkl"), "rb")) if p.get("E_ok")]
f = lambda a: "nm" if not np.isfinite(a) else f"{a:.2f}"   # noqa: E731
print("Por par, estrato N: positivo | control | dBT11 | px | AUC beta73 E | AUC dtau73 E | AUC anillo beta73 E | AUC beta73 M")
for p in S:
    if p["estrato"] != "N":
        continue
    q = [p]
    print(p["pos"], p["ctrl"], f"{p['dbt11']:+.2f}", p["n_px"], f(auc(*pool(q, "E", "beta", "h"))), f(auc(*pool(q, "E", "dtau", "h"))),
          f(auc(*pool(q, "E", "beta", "r"))), f(auc(*pool(q, "M", "beta", "h"))))
print("\nPor episodio (dia, estrato): pares | px | AUC beta73 E (n px pos/ctrl) | AUC anillo E | AUC dtau73 E | AUC beta73 M | AUC anillo M")
for est in ("N", "D"):
    for d in sorted({p["dia"] for p in S if p["estrato"] == est}):
        q = [p for p in S if p["estrato"] == est and p["dia"] == d]
        x, y = pool(q, "E", "beta", "h")
        print(est, d, len(q), sum(p["n_px"] for p in q), f(auc(x, y)), f"({np.isfinite(x).sum()}/{np.isfinite(y).sum()})",
              f(auc(*pool(q, "E", "beta", "r"))), f(auc(*pool(q, "E", "dtau", "h"))), f(auc(*pool(q, "M", "beta", "h"))), f(auc(*pool(q, "M", "beta", "r"))))
