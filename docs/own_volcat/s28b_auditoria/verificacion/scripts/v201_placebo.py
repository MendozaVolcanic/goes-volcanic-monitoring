r"""V201 (verificación de S28b): tamaño real del p25 de las tres confirmaciones congeladas (S23b anillo, S25a zona,
S26a unión) en un placebo de "dos días nuevos" armado con días ya vistos (2025 y 2026 hasta el 24-11-2026).

Qué hace la confirmación (criterios S23b §4, S25a confirmación §3, S26a §5; código s23b_confirmar.medir y
s26a_medir.confirmar/recuerdo): con los cuadros P de VOLCAT de los días nuevos que el detector evalúa, cuenta los
alcanzados y calcula p25 = P(X >= alcanzados) con X Poisson binomial de probabilidades r25[hora], el azar por hora de
2025 (fracción alcanzada de los cuadros evaluados de 2025 a +-60 min). Rótulo: NO CONFIRMA si p25 > 0,01; con
p25 <= 0,01, CONFIRMA si además R >= R_min y pN <= 0,05 (Fisher contra los N de esos días a +-60 min), si no PARCIAL.

Placebo: dos días sin relación con VOLCAT hacen de "días nuevos". Los cuadros "P" se ponen en las horas de dos días
reales con P de VOLCAT (plantillas: las horas P de un día real de 2026 pasan enteras a un día placebo, así se conserva
que los P vienen en episodios). Sólo pares de plantillas que suman 20 P o más (el gatillo). Los "N" del placebo son
todos los demás cuadros evaluados de esos dos días. Se aplica la regla entera, con las funciones originales
(s23_medir.poisson_binomial_cola, s23_medir.azar_por_hora, s22b_medir.alcanzado; el Fisher y el filtro de N cerca se
comprueban contra s26a_medir.recuerdo).

  placebo 2025: los 62 días del fondo, cada uno con base y umbral sin sí mismo (Partes.seco). Se informa con el r25
                congelado (62 días, el de la confirmación) y con el r25 sin los dos días del placebo.
  placebo 2026: los días de 21-09 a 24-11-2026 sin ningún cuadro P de VOLCAT, con base y umbral de los 62 días de 2025
                y la costumbre congelada (Partes.blanco), que es lo que la confirmación hará en los días nuevos.

Segundo esquema (camino 5 de los caminos de ruptura): "P" = bloque seguido de 2 h (12 cuadros) a la misma hora en los
dos días, para ver de qué horas sale el rechazo.

Entrada: D:\goes_notas\s28\s28b\v201\disparos.npz (v201_extraer.py). Ningún día posterior al 24-11-2026.
Salida: D:\goes_notas\s28\s28b\v201\v201_placebo.json y texto por pantalla.
"""
import json
import os
import sys

import numpy as np
from scipy import stats

AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s26a_combinado", "scripts"))
import s26a_medir as U  # noqa: E402

S, B, M = U.S, U.B, U.M
SAL = r"D:\goes_notas\s28\s28b\v201"
Zf = np.load(os.path.join(SAL, "disparos.npz"))
CL = Zf["CL"]
DIAS26 = [str(x) for x in Zf["dias26"]]
assert max(DIAS26) == "2026-11-24" and len(DIAS26) == 65
W = S.W_AZAR
MIN_P, MIN_P_EVAL, P25_MAX, PN_MAX = 20, 10, 0.01, 0.05
# regla: (parte, percentil, R mínimo)
REGLAS = {"S23b anillo": ("a", 5.0, 0.40), "S25a zona": ("z", 5.0, 0.25), "S26a unión": ("u", 4.75, 0.40)}
rng = np.random.default_rng(20261126)


def alc_dia(F, ev):
    """alcanzado por cuadro de un día, con la función original (s22b_medir.alcanzado)."""
    return np.array([B.alcanzado(F, ev, s)[1] for s in range(144)])


def ventana(x):
    """suma circular en +-W cuadros a lo largo del último eje."""
    return sum(np.roll(x, k, axis=-1) for k in range(-W, W + 1))


CERCA = np.array([[M.dslot(a, b) <= W for b in range(144)] for a in range(144)])


def caso(Pm, EV, AL, r, rmin):
    """Regla de la confirmación para un placebo. Pm, EV, AL: (2, 144) bool (P, evaluado, alcanzado)."""
    pe = Pm & EV
    te = int(pe.sum())
    dias_ev = int(pe.any(1).sum())
    if te < MIN_P_EVAL or dias_ev < 2:
        return {"ver": "NO DECIDIBLE", "te": te}
    th = int((pe & AL).sum())
    sl = np.concatenate([np.flatnonzero(pe[0]), np.flatnonzero(pe[1])])
    p25 = S.poisson_binomial_cola(list(r[sl]), th)
    R = th / te
    out = {"te": te, "th": th, "R": R, "p25": p25, "E": float(r[sl].sum())}
    if p25 > P25_MAX:
        out["ver"] = "NO CONFIRMA"
        return out
    cerca = CERCA[np.unique(sl)].any(0)
    ne = EV & ~Pm & cerca[None, :]
    nn, nh = int(ne.sum()), int((ne & AL).sum())
    pN = float(stats.fisher_exact([[th, te - th], [nh, nn - nh]], alternative="greater")[1]) if nn else None
    out.update(N=nn, Nh=nh, pN=pN)
    out["ver"] = "CONFIRMA" if (R >= rmin and pN is not None and pN <= PN_MAX) else "PARCIAL"
    return out


def comprobar_arnes():
    """El arnés tiene que dar, con los P y N reales de 2026, lo publicado por S26a y S25a (y lo de recuerdo())."""
    pub = json.load(open(os.path.join(OV, "s26a_combinado", "resultados", "s26a_desarrollo.json"), encoding="utf-8"))
    pz = json.load(open(os.path.join(OV, "s25a_crater", "resultados", "s25a_resultado.json"), encoding="utf-8"))
    for nom, (k, p, _) in REGLAS.items():
        F25, E25 = Zf[f"F25_{k}_{p}"], Zf[f"E25_{k}_{p}"]
        F26, E26 = Zf[f"F26_{k}_{p}"], Zf[f"E26_{k}_{p}"]
        r_orig = U.azar([(F25[d], E25[d]) for d in range(62)])
        A25 = np.array([alc_dia(F25[d], E25[d]) for d in range(62)])
        r_mio = ventana((A25 & E25).sum(0).astype(float)) / ventana(E25.sum(0).astype(float))
        assert np.allclose(r_orig, r_mio, equal_nan=True), "azar por hora: mi versión no coincide con la original"
        res = [{k: (F26[d], E26[d])} for d in range(65)]
        q = U.recuerdo(U.lista(res, CL, k), r_orig)
        print(f"   {nom} (p {p}): reales 2026 P {q['P_alcanzados']} de {q['P_evaluados']}, p25 {q['p25']:.4g}, "
              f"pN {q['pN']:.4g}; seco 2025 {int(F25.sum())} de {int(E25.sum())}")
        if k == "u":
            assert (q["P_alcanzados"], q["P_evaluados"]) == (pub["union"]["P_alcanzados"], pub["union"]["P_evaluados"])
            assert abs(q["p25"] / pub["union"]["p25"] - 1) < 1e-9 and abs(q["pN"] / pub["union"]["pN"] - 1) < 1e-9
            assert (int(F25.sum()), int(E25.sum())) == (269, 5499)
        if k == "z":
            assert (q["P_alcanzados"], q["P_evaluados"]) == (pz["P_alcanzados"], pz["P_evaluados"]) == (44, 93)
            assert abs(q["p25"] / pz["p25"] - 1) < 1e-9 and abs(q["pN"] / pz["pN"] - 1) < 1e-9
            assert (int(F25.sum()), int(E25.sum())) == (176, 5499)
        if k == "a":
            assert (q["P_alcanzados"], q["P_evaluados"]) == (25, 54)
    # mi caso() contra recuerdo() en 200 placebos al azar (zona, 2026)
    k, p, rmin = REGLAS["S25a zona"]
    F26, E26 = Zf[f"F26_{k}_{p}"], Zf[f"E26_{k}_{p}"]
    F25, E25 = Zf[f"F25_{k}_{p}"], Zf[f"E25_{k}_{p}"]
    r = U.azar([(F25[d], E25[d]) for d in range(62)])
    A26 = np.array([alc_dia(F26[d], E26[d]) for d in range(65)])
    n_ok = 0
    for _ in range(200):
        d1, d2 = rng.choice(65, 2, replace=False)
        Pm = rng.random((2, 144)) < 0.2
        c = caso(Pm, E26[[d1, d2]], A26[[d1, d2]], r, rmin)
        cl = np.where(Pm, "P", "N")
        q = U.recuerdo(U.lista([{k: (F26[d1], E26[d1])}, {k: (F26[d2], E26[d2])}], cl, k), r)
        if c["ver"] == "NO DECIDIBLE":
            n_ok += q["P_evaluados"] < MIN_P_EVAL or q["dias_P_evaluado"] < 2
            continue
        ok = (c["te"], c["th"]) == (q["P_evaluados"], q["P_alcanzados"]) and abs(c["p25"] - q["p25"]) < 1e-12
        if c["ver"] != "NO CONFIRMA":
            ok &= (c["N"], c["Nh"]) == (q["N_cerca"], q["N_cerca_alcanzados"]) and abs(c["pN"] - q["pN"]) < 1e-12
        n_ok += ok
    print(f"   caso() contra s26a_medir.recuerdo() en 200 placebos al azar: {n_ok} de 200 iguales")
    assert n_ok == 200


def plantillas():
    """Horas P de cada día real con P (2026), y los pares de plantillas que suman 20 P o más."""
    T = {DIAS26[d]: CL[d] == "P" for d in range(65) if (CL[d] == "P").any()}
    nombres = sorted(T)
    pares = [(a, b) for i, a in enumerate(nombres) for b in nombres[i + 1:] if T[a].sum() + T[b].sum() >= MIN_P]
    return T, pares


def correr(nom, EV, AL, dias, r_de, plant, rotulo):
    """Todos los pares de días placebo x pares de plantillas x 2 orientaciones. r_de(d1, d2) da el r25 a usar."""
    k, p, rmin = REGLAS[nom]
    nd = len(dias)
    filas = []
    for i in range(nd):
        for j in range(i + 1, nd):
            r = r_de(i, j)
            for t, Pm2 in enumerate(plant):
                for o in (0, 1):
                    Pm = Pm2 if o == 0 else Pm2[::-1]
                    c = caso(Pm, EV[[i, j]], AL[[i, j]], r, rmin)
                    filas.append((i, j, t, o, c["ver"], c.get("p25", np.nan), c.get("R", np.nan),
                                  c.get("te", 0), c.get("th", 0), c.get("E", np.nan)))
    ver = np.array([f[4] for f in filas])
    p25 = np.array([f[5] for f in filas], float)
    dec = ver != "NO DECIDIBLE"
    n = int(dec.sum())
    rech = dec & (p25 <= P25_MAX)
    out = {"esquema": rotulo, "regla": nom, "dias_placebo": nd, "casos": len(filas), "decidibles": n}
    if n == 0:
        print(f"   {nom} | {rotulo}: ningún caso decidible")
        return out, filas
    I = np.array([f[0] for f in filas])
    J = np.array([f[1] for f in filas])
    out.update(rechazo_p25=float(rech.sum() / n), confirma=float((ver == "CONFIRMA").sum() / n),
               parcial=float((ver == "PARCIAL").sum() / n),
               p25_cuantiles={q: float(np.quantile(p25[dec], q)) for q in (0.001, 0.01, 0.05, 0.5)},
               rechazo_a_0_0033=float((dec & (p25 <= 0.01 / 3)).sum() / n),
               mediana_E=float(np.nanmedian([f[9] for f, d in zip(filas, dec) if d])),
               mediana_P_evaluados=float(np.median([f[7] for f, d in zip(filas, dec) if d])))
    # pares de días (la unidad que de verdad se repite): fracción de pares con algún rechazo, y con rechazo en la
    # mitad o más de sus plantillas
    par = {}
    for a, b, d_, r_ in zip(I, J, dec, rech):
        if d_:
            x = par.setdefault((a, b), [0, 0])
            x[0] += 1
            x[1] += int(r_)
    fr = np.array([v[1] / v[0] for v in par.values()])
    out["pares_de_dias_decidibles"] = len(par)
    out["pares_con_algun_rechazo"] = float((fr > 0).mean())
    # días que ponen los rechazos
    cnt = np.zeros(nd)
    for a, b in zip(I[rech], J[rech]):
        cnt[a] += 1
        cnt[b] += 1
    orden = np.argsort(-cnt)[:5]
    out["dias_que_mas_rechazan"] = [(dias[x], int(cnt[x])) for x in orden if cnt[x] > 0]
    # intervalo por remuestreo de días (los casos comparten días: no son independientes)
    Mr = np.zeros((nd, nd))
    Md = np.zeros((nd, nd))
    np.add.at(Mr, (I[rech], J[rech]), 1)
    np.add.at(Md, (I[dec], J[dec]), 1)
    Mr, Md = Mr + Mr.T, Md + Md.T
    bs = []
    for _ in range(2000):
        x = rng.integers(0, nd, nd)
        cx = np.bincount(x, minlength=nd).astype(float)
        den = cx @ Md @ cx
        if den > 0:
            bs.append((cx @ Mr @ cx) / den)
    out["rechazo_IC95_remuestreo_de_dias"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    print(f"   {nom} | {rotulo}: {nd} días, {n} casos decidibles de {len(filas)}; p25 <= 0,01 en "
          f"{out['rechazo_p25']:.4f} (IC95 por días {out['rechazo_IC95_remuestreo_de_dias'][0]:.4f} a "
          f"{out['rechazo_IC95_remuestreo_de_dias'][1]:.4f}); p25 <= 0,0033 en {out['rechazo_a_0_0033']:.4f}; "
          f"CONFIRMA {out['confirma']:.4f}, PARCIAL {out['parcial']:.4f}; pares de días con algún rechazo "
          f"{out['pares_con_algun_rechazo']:.3f}; cuantil 1 % del p25 {out['p25_cuantiles'][0.01]:.3g}; "
          f"días que más rechazan {out['dias_que_mas_rechazan'][:3]}", flush=True)
    return out, filas


def main():
    print("0. comprobación del arnés contra lo publicado")
    comprobar_arnes()
    T, pares_t = plantillas()
    print("1. plantillas de horas P (días reales con P de VOLCAT, 2026):",
          {k: int(v.sum()) for k, v in T.items()}, "| pares que suman 20 o más:", len(pares_t))
    plant = [np.array([T[a], T[b]]) for a, b in pares_t]
    bloques = []
    for h in range(24):
        m = np.zeros(144, bool)
        m[6 * h:6 * h + 12] = True if h < 23 else False
        if h == 23:
            m[138:144] = True
            m[0:6] = True
        bloques.append(np.array([m, m]))
    sinP26 = [d for d in range(65) if not (CL[d] == "P").any()]
    conPNG = [d for d in sinP26 if (CL[d] == "N").sum() >= 72]
    print(f"   días de 2026 sin ningún P: {len(sinP26)} de 65; de ellos con 72 o más cuadros N de VOLCAT (PNG medio día "
          f"o más): {len(conPNG)}")
    salida = []
    por_hora = {}
    for nom, (k, p, rmin) in REGLAS.items():
        F25, E25 = Zf[f"F25_{k}_{p}"], Zf[f"E25_{k}_{p}"]
        F26, E26 = Zf[f"F26_{k}_{p}"], Zf[f"E26_{k}_{p}"]
        A25 = np.array([alc_dia(F25[d], E25[d]) for d in range(62)])
        A26 = np.array([alc_dia(F26[d], E26[d]) for d in range(65)])
        r62 = U.azar([(F25[d], E25[d]) for d in range(62)])
        nA, nE = ventana((A25 & E25).astype(float)), ventana(E25.astype(float))      # (62, 144)
        tA, tE = nA.sum(0), nE.sum(0)

        def r_sin(i, j):
            return (tA - nA[i] - nA[j]) / (tE - nE[i] - nE[j])
        d25 = [f"{S.T0R + U.timedelta(days=d):%Y-%m-%d}" for d in range(62)]
        print(f"2. {nom} (percentil {p}, R mínimo {rmin}); tasa alcanzada global 2025 "
              f"{(A25 & E25).sum() / E25.sum():.4f}, 2026 sin P {(A26 & E26)[sinP26].sum() / E26[sinP26].sum():.4f}")
        for rot, EV, AL, dias, rf, pl in (
                ("2025, r25 congelado (62 días), plantillas reales", E25, A25, d25, lambda i, j: r62, plant),
                ("2025, r25 sin los dos días, plantillas reales", E25, A25, d25, r_sin, plant),
                ("2026 sin P, r25 congelado, plantillas reales", E26[sinP26], A26[sinP26],
                 [DIAS26[d] for d in sinP26], lambda i, j: r62, plant),
                ("2026 sin P y con PNG de VOLCAT medio día o más, r25 congelado, plantillas reales", E26[conPNG],
                 A26[conPNG], [DIAS26[d] for d in conPNG], lambda i, j: r62, plant),
                ("2025, r25 sin los dos días, bloques de 2 h", E25, A25, d25, r_sin, bloques),
                ("2026 sin P, r25 congelado, bloques de 2 h", E26[sinP26], A26[sinP26],
                 [DIAS26[d] for d in sinP26], lambda i, j: r62, bloques)):
            o, filas = correr(nom, EV, AL, dias, rf, pl, rot)
            salida.append(o)
            if "bloques" in rot:
                h = {}
                for f in filas:
                    if f[4] != "NO DECIDIBLE":
                        x = h.setdefault(f[2], [0, 0])
                        x[0] += 1
                        x[1] += int(f[5] <= P25_MAX)
                por_hora[f"{nom} | {rot}"] = {f"{t:02d} UTC": [v[1], v[0]] for t, v in sorted(h.items())}
    print("3. bloques de 2 h: rechazos de p25 / casos decidibles por hora de inicio (UTC)")
    for kk, v in por_hora.items():
        print("   " + kk + ": " + ", ".join(f"{h[:2]}h {a}/{b}" for h, (a, b) in v.items()))
    json.dump({"placebos": salida, "bloques_por_hora": por_hora,
               "plantillas": {k: int(v.sum()) for k, v in T.items()}, "pares_de_plantillas": pares_t},
              open(os.path.join(SAL, "v201_placebo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("escrito", os.path.join(SAL, "v201_placebo.json"))


if __name__ == "__main__":
    main()
