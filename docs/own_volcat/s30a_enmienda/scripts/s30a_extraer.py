r"""S30a, paso 1: disparos y cuadros evaluados por día de las tres reglas congeladas (anillo S23b, zona S25a, unión
S26a) en los tres fondos que usa la calibración de la enmienda: 2025 (cada día sin sí mismo), 2024 (GOES-16, base y
umbral de los 62 días de 2025) y 2026 de 21-09 a 24-11 (base y umbral de 2025, costumbre de 2026 congelada).

Por qué: el nulo por días de la enmienda coloca las horas de los P sobre días de un año tranquilo, y su umbral se
calibra con placebos de los tres años. Todo sale de días ya vistos; ningún día posterior al 24-11-2026.

Código de las reglas: el de S26a y S25a SIN modificar (s26a_medir.Partes.seco y .blanco; s25a_medir.costumbre, nubes,
regional, tabla_S, umbral, disparos; s23_medir.disparos). 2024 se arma como en S25b (anillo: base y umbral de 2025,
nublado de costumbre de 2024) y S29b (zona: la BTD de 2024 leída con s25a_medir._leer desde la bajada de S25b).

Comprobaciones antes de escribir:
  * 2025 y 2026 iguales, arreglo por arreglo, a los de la verificación V201 de S28b (D:\goes_notas\s28\s28b\v201\
    disparos.npz), que reprodujo lo publicado de S23b, S25a y S26a.
  * 2024 anillo a percentil 5 igual al FA24 de S25b versión S23b (0,015 media por día).

Uso: python -I -B s30a_extraer.py      (unos 15 min; escribe D:\goes_notas\s30\s30a\disparos_s30a.npz)
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
sys.path.insert(0, os.path.join(OV, "s26a_combinado", "scripts"))
sys.path.insert(0, os.path.join(OV, "s25b_fondo_2024", "scripts"))
import s26a_medir as U  # noqa: E402

S, B, M, Z = U.S, U.B, U.M, U.Z
SAL = r"D:\goes_notas\s30\s30a"
V201 = r"D:\goes_notas\s28\s28b\v201\disparos.npz"
DATOS24 = r"D:\goes_notas\s25\s25b_2024"
CUBO24 = os.path.join(DATOS24, "cubo")
T024 = datetime(2024, 9, 21)
ND24 = 62
PCTS = (5.0, 4.75)


def costumbre_anillo(acm, m1):
    """Nublado de costumbre como s23_medir.Detector.__init__ (NULR = M1 finito), para un año blanco."""
    return Z.costumbre(acm, np.isfinite(m1).any(2))


def cubo24():
    """BTD de 2024 de todos los píxeles (lector de S25a sin cambios), cacheado en D:."""
    f = os.path.join(SAL, "r24_btd.npy")
    if not os.path.exists(f):
        t = time.time()
        btd, acm, inst = Z._leer(DATOS24, T024, ND24)
        np.save(f, btd)
        np.save(os.path.join(SAL, "r24_acm_zona.npy"), acm)
        json.dump(inst, open(os.path.join(SAL, "cubo_2024.json"), "w", encoding="utf-8"), indent=1)
        print("cubo 2024:", json.dumps(inst), f"{time.time() - t:.0f} s", flush=True)
    return np.load(f), np.load(os.path.join(SAL, "r24_acm_zona.npy"))


def main():
    assert B.ND == 65 and B.fecha(B.ND - 1) == "2026-11-24", (B.ND, B.fecha(B.ND - 1))
    os.makedirs(SAL, exist_ok=True)
    t = time.time()
    X = U.Partes()
    out = {"CL": np.array(X.CL, dtype="U4"), "dias26": np.array([B.fecha(d) for d in range(B.ND)])}
    # 2024
    acm24a = np.load(os.path.join(CUBO24, "r24_acm.npy"))
    m124 = np.load(os.path.join(CUBO24, "r24_m1.npy"))
    est24a = costumbre_anillo(acm24a, m124)
    btd24, acm24z = cubo24()
    hay24 = np.isfinite(btd24[:, :, Z.ZONA[0]])
    est24z = Z.costumbre(acm24z, hay24)
    FD24z, DIN24 = Z.nubes(acm24z, est24z)
    C24 = Z.regional(btd24, DIN24, X.bctrl)
    S24z, _ = Z.tabla_S(np.ascontiguousarray(btd24[:, :, Z.ZONA]), C24, X.bz, FD24z <= B.G_MAX)
    del btd24
    B0 = X.A.base(None)
    FD24a, mm24 = X.A._nubes(acm24a, m124, est24a)
    gate24 = FD24a <= B.G_MAX
    S24a = np.full((ND24, 144), np.nan)
    K24a = np.full((ND24, 144), -1, int)
    for d in range(ND24):
        for s in range(144):
            if gate24[d, s]:
                S24a[d, s], K24a[d, s], _ = M.estadistico(mm24[d, s] - B0[s])
    print(f"2024 listo en {time.time() - t:.0f} s", flush=True)
    resumen = {}
    for p in PCTS:
        sec = X.seco(p)
        res, Ua, Uz = X.blanco(p)
        r24 = []
        for d in range(ND24):
            Fa, eva = S.disparos(S24a, K24a, d, Ua)
            Fz, evz = Z.disparos(S24z, d, Uz)
            r24.append({"a": (Fa, eva), "z": (Fz, evz), "u": (Fa | Fz, eva | evz)})
        for k in ("a", "z", "u"):
            out[f"F25_{k}_{p}"] = np.array([F for F, _ in sec[k]])
            out[f"E25_{k}_{p}"] = np.array([ev for _, ev in sec[k]])
            out[f"F26_{k}_{p}"] = np.array([r[k][0] for r in res])
            out[f"E26_{k}_{p}"] = np.array([r[k][1] for r in res])
            out[f"F24_{k}_{p}"] = np.array([r[k][0] for r in r24])
            out[f"E24_{k}_{p}"] = np.array([r[k][1] for r in r24])
            m24 = U.medidas_seco([r[k] for r in r24])
            m25 = U.medidas_seco(sec[k])
            resumen[f"{k}_{p}"] = {"2025_global": m25["global"], "2025_media_dia": m25["media_por_dia"],
                                   "2024_global": m24["global"], "2024_media_dia": m24["media_por_dia"],
                                   "2024_disparos": m24["disparos"], "2024_evaluados": m24["evaluados"]}
            print(f"p {p} parte {k}: 2025 {m25['disparos']} de {m25['evaluados']} (media por día "
                  f"{m25['media_por_dia']:.5f}); 2024 {m24['disparos']} de {m24['evaluados']} (global "
                  f"{m24['global']:.5f}, media por día {m24['media_por_dia']:.5f})", flush=True)
    # comprobación contra V201 (2025 y 2026)
    v = np.load(V201)
    dif = [k for k in v.files if k.startswith(("F2", "E2")) and not np.array_equal(v[k], out[k])]
    assert not dif, f"no reproduce V201: {dif}"
    assert np.array_equal(v["CL"], out["CL"])
    print("2025 y 2026 idénticos a V201 de S28b:", len([k for k in v.files if k.startswith(('F2', 'E2'))]), "arreglos")
    # 2024 anillo a percentil 5 contra S25b (S23b, costumbre 2024): FA24 media por día 0,015
    pub = json.load(open(os.path.join(OV, "s25b_fondo_2024", "resultados", "s25b_resultado.json"), encoding="utf-8"))
    fa_pub = pub["b"]["S23b"]["FA24_media_por_dia"]
    fa_mio = resumen["a_5.0"]["2024_media_dia"]
    print(f"2024 anillo p5: media por día {fa_mio:.5f} contra S25b {fa_pub}")
    assert abs(fa_mio - fa_pub) < 5e-5, "no reproduce S25b"
    out["dias24"] = np.array([f"{T024 + timedelta(days=d):%Y-%m-%d}" for d in range(ND24)])
    np.savez_compressed(os.path.join(SAL, "disparos_s30a.npz"), **out)
    json.dump(resumen, open(os.path.join(SAL, "extraer_resumen.json"), "w", encoding="utf-8"), indent=1)
    print("escrito", os.path.join(SAL, "disparos_s30a.npz"), f"{time.time() - t:.0f} s", flush=True)


if __name__ == "__main__":
    main()
