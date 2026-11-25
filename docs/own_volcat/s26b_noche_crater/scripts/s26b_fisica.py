r"""S26b, paso 1 (física, antes de mirar un solo disparo): qué le hace a la BTD (11,2 menos 12,3 µm) de un píxel ABI
de 2 km una fuente caliente que cubre una fracción del píxel, sobre fondo nocturno frío.

Modelo de mezcla lineal de radiancias (Dozier 1981, el mismo de la VRP por infrarrojo medio):
    L_lambda = f * eps_h,lambda * B_lambda(T_h) + (1 - f) * B_lambda(T_b)
y, opcionalmente, una capa de atmósfera encima:
    L_obs = tau_lambda * L_lambda + (1 - tau_lambda) * B_lambda(T_a)
BT se invierte con los coeficientes de Planck del NetCDF L1B (planck_fk1, fk2, bc1, bc2 de C14 y C15), leídos del
npz guardado de 2025 (D:\goes_notas\s22\s22d_2025\l1b\20251101_0300.npz). La fracción f sale de la potencia:
    f = VRP / (eps * sigma * T_h^4 * A_pix)
con A_pix de 4,5 a 7,5 km² en Chillán (vrp_nocturno/INFORME.md).

Salida: resultados/s26b_fisica.json y una tabla impresa.
Uso: python -I s26b_fisica.py
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
NPZ = r"D:\goes_notas\s22\s22d_2025\l1b\20251101_0300.npz"
SIGMA = 5.670374419e-8

z = np.load(NPZ)
CO = {"11": tuple(float(x) for x in z["co14"]), "12": tuple(float(x) for x in z["co15"])}


def B(T, b):
    fk1, fk2, bc1, bc2 = CO[b]
    return fk1 / np.expm1(fk2 / (bc1 + bc2 * np.asarray(T, float)))


def Binv(L, b):
    fk1, fk2, bc1, bc2 = CO[b]
    return (fk2 / np.log(fk1 / L + 1.0) - bc1) / bc2


def btd(f, Th, Tb, eps11=1.0, eps12=1.0, tau=(1.0, 1.0), Ta=None):
    out = {}
    for b, e, t in (("11", eps11, tau[0]), ("12", eps12, tau[1])):
        L = f * e * B(Th, b) + (1 - f) * B(Tb, b)
        if Ta is not None:
            L = t * L + (1 - t) * B(Ta, b)
        out[b] = Binv(L, b)
    return out["11"] - out["12"], out["11"]


def delta(f, Th, Tb, **kw):
    """Cambio de BTD y de BT11 respecto del mismo píxel sin fuente (f = 0), con la misma atmósfera."""
    d1, t1 = btd(f, Th, Tb, **kw)
    kw0 = dict(kw)
    kw0.pop("eps11", None)
    kw0.pop("eps12", None)
    d0, t0 = btd(0.0, Th, Tb, **kw0)
    return float(d1 - d0), float(t1 - t0)


def main():
    out = {"coeficientes": {"C14": CO["11"], "C15": CO["12"], "fuente": os.path.basename(NPZ)}, "casos": []}
    filas = []
    # 1. Material incandescente (domo, boca, lava): fracción desde la potencia.
    for A_km2 in (4.5, 7.5):
        for Th in (600.0, 800.0, 1000.0, 1200.0):
            for vrp in (1.0, 10.0, 40.0, 80.0):
                f = vrp * 1e6 / (SIGMA * Th ** 4 * A_km2 * 1e6)
                for Tb in (250.0, 270.0):
                    dB, dT = delta(f, Th, Tb)
                    filas.append(("incandescente", A_km2, Th, vrp, f, Tb, 1.0, 1.0, dB, dT))
    # 2. Suelo tibio (fumarolas, suelo alterado, depósito caliente): fracciones grandes, temperaturas bajas.
    for Th in (280.0, 300.0, 330.0, 370.0):
        for f in (0.01, 0.05, 0.2, 0.5):
            for Tb in (250.0, 270.0):
                dB, dT = delta(f, Th, Tb)
                filas.append(("tibio", None, Th, None, f, Tb, 1.0, 1.0, dB, dT))
    # 3. Sensibilidad: la fuente caliente emite menos a 11 que a 12 µm (vidrio silicatado), eps11 < eps12.
    #    Se barre la diferencia sin afirmar un valor medido para Chillán.
    sens = []
    for Th, f, Tb in ((1000.0, 40e6 / (SIGMA * 1000.0 ** 4 * 6e6), 260.0), (330.0, 0.2, 260.0), (300.0, 0.5, 260.0)):
        for de in (0.0, 0.02, 0.05, 0.10, 0.20):
            dB, dT = delta(f, Th, Tb, eps11=0.97 - de, eps12=0.97)
            sens.append({"Th": Th, "f": f, "Tb": Tb, "eps11": round(0.97 - de, 3), "eps12": 0.97,
                         "dBTD_K": round(dB, 4), "dBT11_K": round(dT, 4)})
            # punto en que la BTD cambia de signo, si existe: buscar eps11 mínimo con dBTD >= 0
    # 4. Con atmósfera: tau11 > tau12 (más vapor absorbe a 12 µm), atmósfera más fría que la superficie.
    atm = []
    for tau in ((0.97, 0.94), (0.90, 0.80)):
        for Ta in (240.0, 255.0):
            for Th, f in ((1000.0, 40e6 / (SIGMA * 1000.0 ** 4 * 6e6)), (330.0, 0.2)):
                dB, dT = delta(f, Th, 260.0, tau=tau, Ta=Ta)
                atm.append({"tau11": tau[0], "tau12": tau[1], "Ta": Ta, "Th": Th, "f": f,
                            "dBTD_K": round(dB, 4), "dBT11_K": round(dT, 4)})
    # 5. Diferencia de emisividad que haría falta para que la fuente BAJE la BTD (cruce por cero), por caso.
    cruce = []
    for Th, f in ((1000.0, 40e6 / (SIGMA * 1000.0 ** 4 * 6e6)), (800.0, 10e6 / (SIGMA * 800.0 ** 4 * 6e6)),
                  (330.0, 0.2), (300.0, 0.5), (290.0, 0.5)):
        lo, hi = 0.0, 0.96
        if delta(f, Th, 260.0, eps11=0.97 - hi, eps12=0.97)[0] > 0:
            cruce.append({"Th": Th, "f": f, "delta_eps_cruce": None})
            continue
        for _ in range(60):
            m = (lo + hi) / 2
            if delta(f, Th, 260.0, eps11=0.97 - m, eps12=0.97)[0] > 0:
                lo = m
            else:
                hi = m
        cruce.append({"Th": Th, "f": f, "delta_eps_cruce": round(hi, 4)})
    # 6. Sólo calor, misma superficie: el parche (fracción f, emisividad eps11 < eps12) a T_h contra el MISMO parche
    #    a T_b. Separa el calor del efecto del material (depósito), que ya existe en frío. El resto del píxel, cuerpo
    #    negro a T_b. Se ignora el cielo reflejado (de noche, despejado, la cumbre lo ve frío: ese término es chico).
    solo_calor = []
    for de in (0.01, 0.02, 0.05):
        for f in (0.05, 0.2, 0.5, 1.0):
            for Th in (280.0, 300.0, 330.0):
                e = {"eps11": 0.97 - de, "eps12": 0.97}
                d1, t1 = btd(f, Th, 260.0, **e)
                d0, t0 = btd(f, 260.0, 260.0, **e)
                solo_calor.append({"delta_eps": de, "f": f, "Th": Th, "Tb": 260.0,
                                   "BTD_parche_frio_K": round(float(d0), 4), "dBTD_por_calor_K": round(float(d1 - d0), 4),
                                   "dBT11_por_calor_K": round(float(t1 - t0), 3)})
    out["solo_calor_misma_superficie"] = solo_calor
    cols = ["tipo", "A_km2", "Th_K", "VRP_MW", "f", "Tb_K", "eps11", "eps12", "dBTD_K", "dBT11_K"]
    out["casos"] = [dict(zip(cols, r)) for r in filas]
    out["sensibilidad_emisividad"] = sens
    out["con_atmosfera"] = atm
    out["delta_eps_para_cruzar_cero"] = cruce
    out["minimo_dBTD_sin_emisividad"] = float(min(r[8] for r in filas))
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "s26b_fisica.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{'tipo':13s} {'A':>4s} {'Th':>5s} {'VRP':>5s} {'f':>9s} {'Tb':>4s} {'dBTD':>7s} {'dBT11':>7s}")
    for r in filas:
        print(f"{r[0]:13s} {r[1] or '':>4} {r[2]:5.0f} {r[3] or '':>5} {r[4]:9.2e} {r[5]:4.0f} {r[8]:7.3f} {r[9]:7.3f}")
    print("min dBTD (eps iguales):", out["minimo_dBTD_sin_emisividad"])
    print("sensibilidad emisividad:")
    for s in sens:
        print(" ", s)
    print("con atmósfera:")
    for s in atm:
        print(" ", s)
    print("delta eps (eps12 - eps11) para que la fuente baje la BTD:")
    for s in cruce:
        print(" ", s)
    print("sólo calor, misma superficie (parche a Th contra el mismo parche a 260 K):")
    for s in solo_calor:
        print(" ", s)


if __name__ == "__main__":
    main()
