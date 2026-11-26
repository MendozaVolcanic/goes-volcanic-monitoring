r"""V201 (verificación de S28b): extrae, con el código de S26a SIN modificar, los disparos y los cuadros evaluados
por día de las tres reglas (anillo, zona, unión) en 2025 (cada día sin sí mismo) y en 2026 hasta el 24-11-2026.

No corre nada sobre días posteriores al 24-11-2026: sólo instancia s26a_medir.Partes (cubos de 2025 y de 2026 de
21-09 a 24-11) y llama a Partes.seco(p) y Partes.blanco(p). No llama a medir() ni a confirmar(): no escribe en las
carpetas auditadas. Salida: D:\goes_notas\s28\s28b\v201\disparos.npz
"""
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s26a_combinado", "scripts"))
import s26a_medir as U  # noqa: E402

SAL = r"D:\goes_notas\s28\s28b\v201"
B, M = U.B, U.M


def main():
    assert B.ND == 65 and B.fecha(B.ND - 1) == "2026-11-24", (B.ND, B.fecha(B.ND - 1))
    X = U.Partes()
    out = {"CL": np.array(X.CL, dtype="U4")}
    for p in (5.0, 4.75):
        sec = X.seco(p)
        res, _, _ = X.blanco(p)
        for k in ("a", "z", "u"):
            out[f"F25_{k}_{p}"] = np.array([F for F, _ in sec[k]])
            out[f"E25_{k}_{p}"] = np.array([ev for _, ev in sec[k]])
            out[f"F26_{k}_{p}"] = np.array([r[k][0] for r in res])
            out[f"E26_{k}_{p}"] = np.array([r[k][1] for r in res])
            m = U.medidas_seco(sec[k])
            rr = U.recuerdo(U.lista(res, X.CL, k), U.azar(sec[k]))
            print(f"p {p} parte {k}: seco global {m['global']:.6f} media por dia {m['media_por_dia']:.6f} "
                  f"({m['disparos']} de {m['evaluados']}); 2026: P {rr['P_alcanzados']} de {rr['P_evaluados']}, "
                  f"p25 {rr['p25']:.4g}, pN {rr['pN']:.4g}, N cerca {rr['N_cerca_alcanzados']} de {rr['N_cerca']}",
                  flush=True)
    out["dias26"] = np.array([B.fecha(d) for d in range(B.ND)])
    os.makedirs(SAL, exist_ok=True)
    np.savez_compressed(os.path.join(SAL, "disparos.npz"), **out)
    print("escrito", os.path.join(SAL, "disparos.npz"), flush=True)


if __name__ == "__main__":
    main()
