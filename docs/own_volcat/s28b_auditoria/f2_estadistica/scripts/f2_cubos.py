r"""F2 (S28b): disparos (F) y evaluados (ev) por cuadro, 2025 (cada día sin sí mismo) y 2026, de las tres reglas que
deciden: anillo S23a (costumbre de 2025 en 2026), zona S25a (percentil 5) y unión S26a (p* = 4,75), más el anillo
S23b (costumbre de 2026 congelada) a percentil 5.

Por qué: los nulos de los criterios (p25, pN) tratan cada cuadro como independiente; para recomputarlos por día hace
falta la serie entera de F y ev de cada día de 2025 y 2026, que los resultados publicados no guardan.

Sólo importa las funciones auditadas (s26a_medir.Partes, s23_medir.Detector y disparos, s25a_medir); no escribe en sus
carpetas. Días: 2025 del 21-09 al 21-11; 2026 del 21-09 al 24-11 (nada posterior). Salida en D:\goes_notas\s28\s28b\f2\.
Comprobación (control de código): tiene que reproducir 8/30 (S23a), 44/93 (S25a), 63/93 (S26a), 25/54 (S23b).

Uso: python -I f2_cubos.py
"""
import os
import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s26a_combinado", "scripts"))
import s26a_medir as U  # noqa: E402

S, Z, B, M, H24 = U.S, U.Z, U.B, U.M, U.H24
SAL = r"D:\goes_notas\s28\s28b\f2"


def apila(lst):
    return np.array([x[0] for x in lst]), np.array([x[1] for x in lst])


def alc(F, ev):
    A = np.zeros(F.shape, bool)
    for d in range(F.shape[0]):
        for s in np.flatnonzero(ev[d]):
            A[d, s] = B.alcanzado(F[d], ev[d], s)[1]
    return A


def main():
    t = time.time()
    X = U.Partes()
    CL = X.CL
    out = {"CL": CL.astype("U5")}
    for p in (5.0, 4.75):
        sec = X.seco(p)
        res, _, _ = X.blanco(p)
        for k in ("a", "z", "u"):
            F25, ev25 = apila(sec[k])
            F26, ev26 = apila([r[k] for r in res])
            tag = f"{k}{int(p * 100)}"
            out[f"F25_{tag}"], out[f"ev25_{tag}"], out[f"A25_{tag}"] = F25, ev25, alc(F25, ev25)
            out[f"F26_{tag}"], out[f"ev26_{tag}"], out[f"A26_{tag}"] = F26, ev26, alc(F26, ev26)
        print(f"p {p} listo, {time.time() - t:.0f} s", flush=True)
    # anillo S23a: costumbre de 2025 también en 2026 (la regla del criterio S23a)
    U._pct(5.0)
    A = X.A
    A._U = {}
    bt26, acm26, m126 = B.cargar_dev()
    m1T = np.full((B.ND, 144, M.NA), np.nan, np.float32)
    m1T[:B.NDEV] = m126
    m1T[B.NDEV:] = np.load(os.path.join(B.TRAB, "nuevo_m1.npy"))
    FDT, mmT = A._nubes(A.acmT, m1T, A.ESTAT)
    GT = FDT <= B.G_MAX
    B0 = A.base(None)
    ST = np.full((B.ND, 144), np.nan)
    KT = np.full((B.ND, 144), -1, int)
    for d in range(B.ND):
        for s in range(144):
            if GT[d, s]:
                ST[d, s], KT[d, s], _ = M.estadistico(mmT[d, s] - B0[s])
    Ua, _ = A.umbral(None)
    F26, ev26 = apila([S.disparos(ST, KT, d, Ua) for d in range(B.ND)])
    out["F26_s23a"], out["ev26_s23a"], out["A26_s23a"] = F26, ev26, alc(F26, ev26)
    out["FD26_s23a"], out["FD26_est26"], out["GATE26_est26"] = FDT, A.FDT, A.GATET
    out["FD25_anillo"] = A.FDR
    # E1 de 2025 y 2026 (para cobertura)
    out["E1_25"] = A.E1R
    out["E1_26"] = A.E1T
    np.savez_compressed(os.path.join(SAL, "cubos_f2.npz"), **out)
    # control de código
    for nom, key, esperado in (("S23a anillo", "s23a", (8, 30)), ("S25a zona p5", "z500", (44, 93)),
                               ("S26a union p4.75", "u475", (63, 93)), ("S23b anillo p5", "a500", (25, 54))):
        ev, A_ = out[f"ev26_{key}"], out[f"A26_{key}"]
        mP = (CL == "P") & ev
        print(nom, "P alcanzados/evaluados:", int(A_[mP].sum()), int(mP.sum()), "esperado", esperado, flush=True)
    print(f"fin {time.time() - t:.0f} s")


if __name__ == "__main__":
    main()
