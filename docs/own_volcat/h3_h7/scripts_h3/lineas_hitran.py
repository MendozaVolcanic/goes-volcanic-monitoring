"""H3: baja lineas HITRAN (via HAPI, hitran.org/lbl/api, sin cuenta) para H2O, CO2, O3, N2O y CH4 en los
rangos espectrales de C10, C11, C14 y C15 del ABI FM4 (+25 cm-1 de margen para las alas), y las guarda en
un npz compacto (nu, sw, gamma_air, gamma_self, n_air, delta_air, elower, molec, iso, masa molar).
Los datos crudos quedan en h3/dl/hitran (directorio de descargas). Ejecutar con python -I.
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DL = os.path.join(HERE, "dl", "hitran"); os.makedirs(DL, exist_ok=True)
import hapi  # noqa: E402

RANGOS = [(729.0, 981.0), (1094.0, 1271.0), (1300.0, 1435.0)]
# (molecula HITRAN, isotopologos locales) ; abundancias naturales ya van en la intensidad HITRAN
ISOS = {1: (1, 2, 3, 4), 2: (1, 2, 3, 4), 3: (1,), 4: (1,), 6: (1, 2)}
SMIN = 1e-27   # cm-1/(molec cm-2) a 296 K: corte de intensidad (declarado)

hapi.db_begin(DL)
cols = {k: [] for k in ("nu", "sw", "gamma_air", "gamma_self", "n_air", "delta_air", "elower", "M", "I", "molmass")}
for M, Is in ISOS.items():
    for I in Is:
        for a, b in RANGOS:
            name = f"M{M}_I{I}_{int(a)}_{int(b)}"
            if os.path.exists(os.path.join(DL, name + ".vacio")):
                continue
            if not os.path.exists(os.path.join(DL, name + ".data")):
                try:
                    hapi.fetch(name, M, I, a, b)
                except Exception as e:   # HITRAN responde error cuando el rango no tiene lineas
                    print(name, "sin lineas / error:", e, flush=True)
                    open(os.path.join(DL, name + ".vacio"), "w").write(str(e)); continue
            else:
                hapi.storage2cache(name)
            nu, sw, ga, gs, na, da, el = hapi.getColumns(name, ["nu", "sw", "gamma_air", "gamma_self", "n_air", "delta_air", "elower"])
            nu = np.asarray(nu); sw = np.asarray(sw)
            k = sw >= SMIN
            mm = hapi.molecularMass(M, I)
            for key, v in zip(("nu", "sw", "gamma_air", "gamma_self", "n_air", "delta_air", "elower"), (nu, sw, ga, gs, na, da, el)):
                cols[key].append(np.asarray(v, dtype="float64")[k])
            cols["M"].append(np.full(k.sum(), M)); cols["I"].append(np.full(k.sum(), I)); cols["molmass"].append(np.full(k.sum(), mm))
            print(name, "lineas", len(nu), "con S>=%.0e:" % SMIN, int(k.sum()), flush=True)
out = {k: np.concatenate(v) for k, v in cols.items()}
np.savez_compressed(os.path.join(HERE, "lbl", "lineas.npz"), **out)
print("total", len(out["nu"]))
