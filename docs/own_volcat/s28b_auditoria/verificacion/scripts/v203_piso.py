r"""V203 (verificación de S28b): el piso del nulo por corrimiento de días de la prueba P de S27a y el rótulo que da
la tabla del criterio con cada umbral de poder.

Partes:
  A  aritmética del piso con las constantes del script (KMIN, días por año), sin datos.
  B  la tabla de veredictos de s27a_medir.py (líneas 359 a 371, copiada aquí con el umbral de poder como parámetro)
     aplicada a las cifras publicadas en resultados/s27a_resultado.json.
  C  (sólo con el argumento `recalcular`) vuelve a calcular poder, p de 2026 y p de 2025 con las funciones de
     s27a_medir.py SIN modificar (prueba_P, poder_P, viento_noche) y el detector de S26a (Partes), días de 2025 y de
     2026 hasta el 24-11. No llama a medir(): no escribe en las carpetas auditadas.

Uso: python -I -B v203_piso.py [recalcular]
"""
import json
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s27a_noche_causa", "scripts"))
import s27a_medir as Q  # noqa: E402

U, Z, B, M = Q.U, Q.Z, Q.B, Q.M
PUB = json.load(open(os.path.join(OV, "s27a_noche_causa", "resultados", "s27a_resultado.json"), encoding="utf-8"))


def tabla(pod, p26, p25, umbral_poder):
    """Copia de s27a_medir.py líneas 359 a 371; lo único que cambia es el 0.01 del poder, aquí parámetro."""
    if pod["p_corrimiento"] is None or pod["p_corrimiento"] > umbral_poder:
        return "SIN PODER (no decidible)"
    if p26["cuadros"] < Q.MIN_CUADROS_P or p26["noches"] < Q.MIN_NOCHES_P:
        return "NO DECIDIBLE (pocos cuadros)"
    if p26["p_corrimiento"] <= 0.05 and p25["p_corrimiento"] is not None and p25["p_corrimiento"] > 0.05 \
            and p26["giro_max_phi"] in (0, 30, 330):
        return "PLUMA SÍ"
    if p26["p_corrimiento"] <= 0.05 and p25["p_corrimiento"] is not None and p25["p_corrimiento"] <= 0.05:
        return "NO DECIDIBLE (el viento también ordena 2025)"
    if p26["p_corrimiento"] > 0.20:
        return "PLUMA NO"
    return "NO DECIDIBLE"


def parte_A():
    print("A. piso del nulo 1 (corrimiento de días)")
    for año, nd in (("2026", B.ND), ("2025", Z.NR)):
        ks = list(range(Q.KMIN, nd - Q.KMIN + 1))
        print(f"   {año}: {nd} días, k de {ks[0]} a {ks[-1]}: {len(ks)} corrimientos; p mínimo = 1/{len(ks) + 1} = "
              f"{1 / (len(ks) + 1):.6f}; ¿alcanza 0,01? {1 / (len(ks) + 1) <= 0.01}")
    print(f"   corrimientos que harían falta para alcanzar 0,01: 99 (p mínimo 1/100)")


def parte_B(P, origen):
    print(f"B. tabla del criterio con cada umbral de poder ({origen})")
    pod, p26, p25 = P["poder_pluma_ideal"], P["2026"], P["2025"]
    for k, v in (("poder", pod), ("2026", p26), ("2025", p25)):
        n = v["n_corrimientos"]
        print(f"   {k}: C {v['C']}, cuadros {v['cuadros']}, noches {v['noches']}, p {v['p_corrimiento']:.6f} "
              f"= {round(v['p_corrimiento'] * (n + 1))}/{n + 1}, giro máx {v['giro_max_phi']}")
    for thr in (0.01, 1 / 61, 0.02, 0.05):
        print(f"   umbral de poder {thr:.4f}: {tabla(pod, p26, p25, thr)}")
    for h, v in P.get("sensibilidad_h", {}).items():
        print(f"   sensibilidad h {h} km, umbral 0,05: {tabla(pod, v['2026'], v['2025'], 0.05)} "
              f"(p 2026 {v['2026']['p_corrimiento']:.4f}, p 2025 {v['2025']['p_corrimiento']:.4f})")


def parte_C():
    """Los mismos pasos de s27a_medir.medir() hasta la prueba P (líneas 281 a 358), sin escribir nada."""
    capt = []
    orig = Z.tabla_S

    def tabla_S_capt(*a, **k):
        r = orig(*a, **k)
        capt.append(r)
        return r
    Z.tabla_S = tabla_S_capt
    X = U.Partes()
    Z.tabla_S = orig
    PR25 = capt[0][1]
    sec = X.seco(Q.PSTAR)
    res, Ua, Uz = X.blanco(Q.PSTAR)
    CL = X.CL
    seco_u = U.medidas_seco(sec["u"])
    print("   seco de la unión 2025:", seco_u["disparos"], "de", seco_u["evaluados"], flush=True)
    ND26, ND25 = B.ND, Z.NR
    assert B.fecha(ND26 - 1) == "2026-11-24"

    def eventos(año):
        ev, evaluados = [], []
        for d in range(ND26 if año == 2026 else ND25):
            if año == 2026:
                (Fa, eva), (Fz, evz) = res[d]["a"], res[d]["z"]
            else:
                (Fa, eva), (Fz, evz) = sec["a"][d], sec["z"][d]
            for j, s in enumerate(Q.NOCHE):
                if evz[s]:
                    evaluados.append((d, j))
                if año == 2026 and CL[d, s] == "P":
                    continue
                pix = []
                if Fz[s]:
                    pp = X.PTz[d, s] if año == 2026 else PR25[d, s]
                    pix += [int(Z.ZONA[q]) for q in pp if q >= 0]
                if Fa[s]:
                    if año == 2026:
                        pix += [int(q) for q in U.cola_anillo(X.A, d, s)]
                    else:
                        idx = np.flatnonzero(M.SEC == X.A.KR[d, s])
                        v = (X.A.mmR[d, s] - X.A.base(d)[s])[idx]
                        o = np.argsort(np.where(np.isfinite(v), v, np.inf))[:M.NCOLA]
                        pix += [int(q) for q in M.AP[idx[o]]]
                if pix:
                    ev.append((d, j, pix, bool(Fz[s]), bool(Fa[s])))
        return ev, evaluados
    ev26, eval26 = eventos(2026)
    ev25, eval25 = eventos(2025)
    print(f"   eventos nocturnos: 2026 {len(ev26)}, 2025 {len(ev25)}", flush=True)
    W26, W25 = Q.viento_noche(Q.T0_26, ND26), Q.viento_noche(Q.T0_25, ND25)
    print("   cuadros nocturnos sin viento:", int(np.isnan(W26[..., 0]).sum()), int(np.isnan(W25[..., 0]).sum()))
    e26 = [(d, j, p) for d, j, p, *_ in ev26]
    e25 = [(d, j, p) for d, j, p, *_ in ev25]
    P = {"poder_pluma_ideal": Q.poder_P(eval26, W26), "2026": Q.prueba_P(e26, W26), "2025": Q.prueba_P(e25, W25)}
    for k in P:
        igual = all(P[k][c] == PUB["P"][k][c] for c in ("C", "cuadros", "noches", "p_corrimiento", "n_corrimientos",
                                                         "giro_max_phi"))
        print(f"   {k}: recalculado igual al publicado: {igual}")
    return P


if __name__ == "__main__":
    parte_A()
    parte_B(PUB["P"], "cifras publicadas en s27a_resultado.json")
    print("   veredicto publicado:", PUB["P"]["veredicto"])
    if "recalcular" in sys.argv:
        print("C. recálculo con el código de hoy")
        parte_B(parte_C(), "cifras recalculadas hoy")
