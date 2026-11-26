r"""S30a, paso 2: calibración con placebo del nulo por días de la enmienda, y su poder.

Pregunta: con días SIN relación con VOLCAT haciendo de "días nuevos", ¿en qué fracción de los casos la regla nueva
entera escribe CONFIRMA? La enmienda exige 1 % o menos en cada regla (anillo S23b, zona S25a, unión S26a) y en cada
fondo de placebo: 2025 (cada día sin sí mismo; el nulo sin los dos días del placebo), 2024 (GOES-16) y 2026 de 21-09 a
24-11 sin ningún cuadro P de VOLCAT. El umbral alfa se elige DESPUÉS de esta tabla, con la regla de elección escrita en
la enmienda §5 antes de correrla.

Casos placebo (como V201 de S28b): las horas P de dos días reales de 2026 con P de VOLCAT (plantillas; 10 días, 18
pares que suman 20 P o más, el gatillo, en las dos orientaciones) se ponen sobre un par de días placebo. La máscara que
se coloca en el nulo son TODAS las horas P de la plantilla, evaluadas o no (enmienda §2.2): así el día observado es una
colocación más entre las del nulo y, con días intercambiables, p_día es válido por construcción. (Una primera corrida
exploratoria con la máscara "P evaluados del día observado" rompía esa simetría y daba 1,7 % de CONFIRMA falso a alfa
0,01 en el anillo: descartada, log en D:\goes_notas\s30\s30a\calibrar_exploratorio_v201_PLANTILLA_EVALUADA_DESCARTADO.log.)

Variantes que se miden (las dos con el mismo alfa y el mismo R mínimo de cada criterio):
  A  sólo el nulo de 2025 decide (la recomendación de S28b §4a).
  B  deciden el nulo de 2025 Y el de 2026 sin VOLCAT (días de 21-09 a 24-11-2026 sin P; en el placebo de 2026, sin los
     dos días del placebo). Por qué se mide: la zona dispara en 2026 fuera de VOLCAT 4 a 5 veces más que en 2025
     (V201: 23,1 % contra 5,1 %); un nulo sólo de 2025 premiaría "2026 no es 2025", que es justo lo que pN quería
     atajar y que la enmienda deja informativo.
El nulo de 2024 se calcula siempre y es informativo.

Poder: sobre los mismos casos placebo (2025 y 2026 sin P), se fuerza que en cada día una fracción q de los P evaluados
quede alcanzada (los alcanzados del placebo se conservan) y se cuenta la fracción de casos decidibles que la regla
escribe CONFIRMA.

Uso: python -I -B -u s30a_calibrar.py [npz]   (por omisión D:\goes_notas\s30\s30a\disparos_s30a.npz)
Salida: resultados/s30a_calibracion.json (cifras) y D:\goes_notas\s30\s30a\calibrar.log
"""
import json
import os
import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, AQUI)
import s30a_nulo as N  # noqa: E402

NPZ = sys.argv[1] if len(sys.argv) > 1 else r"D:\goes_notas\s30\s30a\disparos_s30a.npz"
REGLAS = {"S23b anillo": ("a", 5.0, 0.40), "S25a zona": ("z", 5.0, 0.25), "S26a unión": ("u", 4.75, 0.40)}
ALFAS = [0.0005, 0.001, 0.002, 0.0025, 0.005, 0.0075, 0.01, 0.02, 0.05]
QS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
MIN_P_GATILLO = 20
N_BOOT = 2000
rng = np.random.default_rng(20261126)


def cargar():
    Zf = np.load(NPZ)
    CL = Zf["CL"]
    dias26 = [str(x) for x in Zf["dias26"]]
    assert max(dias26) == "2026-11-24" and len(dias26) == 65, "sólo días hasta el 24-11-2026"
    return Zf, CL, dias26


def alc(F, E):
    return np.array([N.alcanzado_dia(F[d], E[d]) for d in range(len(F))])


class Fondo:
    """Un fondo para el nulo: EV y AL por día (nd, 144)."""

    def __init__(self, nombre, EV, AL):
        self.nombre, self.EV, self.AL = nombre, EV.astype(bool), AL.astype(bool)
        self.EA = (self.EV & self.AL).astype(float)
        self.nd = len(EV)


def null_counts(Mi, Mj, fondo, excl):
    """Para cada caso (i, j) con máscaras Mi (n, 144) y Mj (n, 144): colocaciones válidas y e, a por día del fondo.
    Devuelve E1 (n, nd), A1, E2, A2 y la máscara de días permitidos por caso (n, nd)."""
    E1 = Mi.astype(float) @ fondo.EV.T.astype(float)
    A1 = Mi.astype(float) @ fondo.EA.T
    E2 = Mj.astype(float) @ fondo.EV.T.astype(float)
    A2 = Mj.astype(float) @ fondo.EA.T
    return E1, A1, E2, A2


def p_vectorizado(eo, ao, E1, A1, E2, A2, permitido, R_umbral=None):
    """p_día de n casos de k = 2 a la vez (la misma cuenta que s30a_nulo.p_dia, comprobada en comprobar()).
    eo, ao: (n, 2). permitido: (n, nd) bool, días del fondo que se pueden usar en cada caso.
    Devuelve p (n,), válidas (n,)."""
    n, nd = E1.shape
    R = ao.sum(1) / np.maximum(eo.sum(1), 1) if R_umbral is None else R_umbral
    Et = E1[:, :, None] + E2[:, None, :]                      # (n, nd, nd)
    At = A1[:, :, None] + A2[:, None, :]
    ok = (Et >= N.MIN_P_EVAL) & (E1[:, :, None] > 0) & (E2[:, None, :] > 0)
    ok &= ~np.eye(nd, dtype=bool)[None]
    ok &= permitido[:, :, None] & permitido[:, None, :]
    ge = ok & (At >= R[:, None, None] * Et - 1e-12)
    nv = ok.sum((1, 2))
    ng = ge.sum((1, 2))
    return (1 + ng) / (1 + nv), nv


def casos(T, pares, EVp, ALp):
    """Todos los casos de un fondo de placebo: pares de días i < j y pares ordenados de plantillas."""
    nd = len(EVp)
    out = []
    for i in range(nd):
        for j in range(i + 1, nd):
            for tA, tB in pares:
                out.append((i, j, tA, tB))
    c = np.array(out)
    Mi = T[c[:, 2]]                                      # todas las horas P de la plantilla (enmienda §2.2)
    Mj = T[c[:, 3]]
    eo = np.stack([(Mi & EVp[c[:, 0]]).sum(1), (Mj & EVp[c[:, 1]]).sum(1)], 1)
    ao = np.stack([(Mi & EVp[c[:, 0]] & ALp[c[:, 0]]).sum(1), (Mj & EVp[c[:, 1]] & ALp[c[:, 1]]).sum(1)], 1)
    return c, Mi, Mj, eo, ao


def evaluar(c, Mi, Mj, eo, ao, fondos, excl_de, bloque=400, q=None):
    """p y válidas de cada fondo para todos los casos. excl_de[nombre](c) -> (n, nd) permitido."""
    n = len(c)
    out = {}
    if q is not None:
        ao = np.maximum(ao, np.ceil(q * eo - 1e-9)).astype(int)
    for nom, fo in fondos.items():
        p = np.ones(n)
        nv = np.zeros(n, int)
        for b0 in range(0, n, bloque):
            sl = slice(b0, min(n, b0 + bloque))
            E1, A1, E2, A2 = null_counts(Mi[sl], Mj[sl], fo, None)
            perm = excl_de[nom](c[sl])
            p[sl], nv[sl] = p_vectorizado(eo[sl], ao[sl], E1, A1, E2, A2, perm)
        out[nom] = (p, nv)
    return out, ao


def rotulos(eo, ao, pv, alfa, r_min, variante):
    """Rótulo por caso con la regla de la enmienda (variante A: nulo 2025; B: nulo 2025 y nulo 2026 sin VOLCAT)."""
    dec = (eo.sum(1) >= N.MIN_P_EVAL) & ((eo > 0).sum(1) >= N.MIN_DIAS)
    p25, nv25 = pv["2025"]
    res = 1.0 / (1 + nv25) <= alfa
    ok_p = p25 <= alfa
    if variante == "B":
        p26, nv26 = pv["2026 sin VOLCAT"]
        res &= 1.0 / (1 + nv26) <= alfa
        ok_p &= p26 <= alfa
    R = ao.sum(1) / np.maximum(eo.sum(1), 1)
    conf = dec & res & ok_p & (R >= r_min)
    parc = dec & res & ok_p & (R < r_min)
    return dec, res, conf, parc


def ic_por_dias(c, dec, rech, nd):
    """Intervalo de 95 % de la fracción rech/dec remuestreando días (los casos comparten días)."""
    Mr = np.zeros((nd, nd))
    Md = np.zeros((nd, nd))
    np.add.at(Mr, (c[rech, 0], c[rech, 1]), 1)
    np.add.at(Md, (c[dec, 0], c[dec, 1]), 1)
    Mr, Md = Mr + Mr.T, Md + Md.T
    bs = []
    for _ in range(N_BOOT):
        x = rng.integers(0, nd, nd)
        cx = np.bincount(x, minlength=nd).astype(float)
        den = cx @ Md @ cx
        if den > 0:
            bs.append((cx @ Mr @ cx) / den)
    return [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))] if bs else [None, None]


def comprobar(c, Mi, Mj, eo, ao, fondos, excl_de, pv):
    """La cuenta vectorizada tiene que dar lo mismo que s30a_nulo.p_dia (la que usa la medida) en 300 casos al azar."""
    idx = rng.choice(len(c), min(300, len(c)), replace=False)
    malos = 0
    for x in idx:
        for nom, fo in fondos.items():
            perm = excl_de[nom](c[x:x + 1])[0]
            if not N.decidible(eo[x]):
                continue
            ef, af = N.tabla_fondo(np.stack([Mi[x], Mj[x]]), fo.EV, fo.AL)
            p, R, nv, ng, ntot = N.p_dia(eo[x], ao[x], ef, af, np.flatnonzero(perm))
            if abs(p - pv[nom][0][x]) > 1e-12 or nv != pv[nom][1][x]:
                malos += 1
    assert malos == 0, f"vectorizado y s30a_nulo.p_dia difieren en {malos} casos"
    return len(idx)


def main():
    t0 = time.time()
    Zf, CL, dias26 = cargar()
    hay24 = "E24_a_5.0" in Zf.files
    T_dias = [d for d in range(65) if (CL[d] == "P").any()]
    T = np.array([CL[d] == "P" for d in T_dias])
    nP = T.sum(1)
    pares = []
    for a in range(len(T)):
        for b in range(len(T)):
            if a != b and nP[a] + nP[b] >= MIN_P_GATILLO:
                pares.append((a, b))
    sinP = [d for d in range(65) if not (CL[d] == "P").any()]
    print(f"plantillas: {dict(zip([dias26[d] for d in T_dias], nP.tolist()))}; pares ordenados: {len(pares)}; "
          f"días de 2026 sin P: {len(sinP)}; 2024 disponible: {hay24}", flush=True)
    salida = {"npz": NPZ, "plantillas": {dias26[d]: int(n) for d, n in zip(T_dias, nP)},
              "pares_ordenados_de_plantillas": len(pares), "dias_2026_sin_P": [dias26[d] for d in sinP],
              "alfas": ALFAS, "reglas": {}}
    for nom, (k, pct, rmin) in REGLAS.items():
        F25, E25 = Zf[f"F25_{k}_{pct}"], Zf[f"E25_{k}_{pct}"]
        F26, E26 = Zf[f"F26_{k}_{pct}"], Zf[f"E26_{k}_{pct}"]
        A25, A26 = alc(F25, E25), alc(F26, E26)
        fondos = {"2025": Fondo("2025", E25, A25), "2026 sin VOLCAT": Fondo("2026", E26[sinP], A26[sinP])}
        placebos = {"2025": (E25, A25), "2026 sin VOLCAT": (E26[sinP], A26[sinP])}
        if hay24:
            F24, E24 = Zf[f"F24_{k}_{pct}"], Zf[f"E24_{k}_{pct}"]
            A24 = alc(F24, E24)
            fondos["2024"] = Fondo("2024", E24, A24)
            placebos["2024"] = (E24, A24)
        tasas = {f: float((placebos[f][0] & placebos[f][1]).sum() / placebos[f][0].sum()) for f in placebos}
        print(f"\n== {nom} (percentil {pct}, R mínimo {rmin}); fracción alcanzada de los cuadros evaluados: "
              + ", ".join(f"{f} {v:.4f}" for f, v in tasas.items()), flush=True)
        salida["reglas"][nom] = {"percentil": pct, "R_min": rmin, "tasa_alcanzada": tasas, "placebos": {}}
        for pl, (EVp, ALp) in placebos.items():
            c, Mi, Mj, eo, ao = casos(T, pares, EVp, ALp)
            nd_pl = len(EVp)

            def excl_de_factory(pl=pl, fondos=fondos):
                def mk(nomf):
                    nd = fondos[nomf].nd
                    if nomf == pl:                      # mismo fondo que el placebo: sin los dos días del placebo
                        def f(cc):
                            perm = np.ones((len(cc), nd), bool)
                            perm[np.arange(len(cc)), cc[:, 0]] = False
                            perm[np.arange(len(cc)), cc[:, 1]] = False
                            return perm
                    else:
                        def f(cc):
                            return np.ones((len(cc), nd), bool)
                    return f
                return {nomf: mk(nomf) for nomf in fondos}
            excl_de = excl_de_factory()
            pv, _ = evaluar(c, Mi, Mj, eo, ao, fondos, excl_de)
            ncomp = comprobar(c, Mi, Mj, eo, ao, fondos, excl_de, pv)
            dec = (eo.sum(1) >= N.MIN_P_EVAL) & ((eo > 0).sum(1) >= N.MIN_DIAS)
            nd_ = int(dec.sum())
            bloque = {"dias_placebo": nd_pl, "casos": len(c), "decidibles": nd_,
                      "comprobados_contra_p_dia": ncomp}
            if nd_ == 0:
                print(f"   placebo {pl}: ningún caso decidible")
                salida["reglas"][nom]["placebos"][pl] = bloque
                continue
            tabla = {}
            for var in ("A", "B"):
                for alfa in ALFAS:
                    d, r, conf, parc = rotulos(eo, ao, pv, alfa, rmin, var)
                    tabla[f"{var}|{alfa}"] = {"confirma": float(conf.sum() / nd_), "parcial": float(parc.sum() / nd_),
                                             "sin_resolucion": float((d & ~r).sum() / nd_)}
            # informativo: p del nulo de cada fondo <= 0,01 por cuadro de nulo
            bloque["p_menor_igual_0_01_por_fondo"] = {f: float(((pv[f][0] <= 0.01) & dec).sum() / nd_) for f in pv}
            bloque["mediana_colocaciones_validas"] = {f: float(np.median(pv[f][1][dec])) for f in pv}
            bloque["tabla"] = tabla
            # intervalos por días al alfa 0,01 y al 0,005, variantes A y B
            bloque["IC95_confirma_por_dias"] = {}
            for var in ("A", "B"):
                for alfa in (0.005, 0.01):
                    d, r, conf, parc = rotulos(eo, ao, pv, alfa, rmin, var)
                    bloque["IC95_confirma_por_dias"][f"{var}|{alfa}"] = ic_por_dias(c, dec, conf, nd_pl)
            # poder: fracción q de P evaluados alcanzados por día
            if pl in ("2025", "2026 sin VOLCAT"):
                pod = {}
                for q in QS:
                    pvq, aoq = evaluar(c, Mi, Mj, eo, ao, fondos, excl_de, q=q)
                    for var in ("A", "B"):
                        for alfa in (0.005, 0.01):
                            d, r, conf, parc = rotulos(eo, aoq, pvq, alfa, rmin, var)
                            pod[f"{var}|{alfa}|q={q}"] = float(conf.sum() / nd_)
                bloque["poder"] = pod
            salida["reglas"][nom]["placebos"][pl] = bloque
            lin = ", ".join(f"{a}: A {tabla[f'A|{a}']['confirma']:.4f} B {tabla[f'B|{a}']['confirma']:.4f}"
                            for a in (0.002, 0.005, 0.01, 0.05))
            print(f"   placebo {pl}: {nd_} decidibles de {len(c)}; CONFIRMA falso {lin}; sin resolución a 0,005 A "
                  f"{tabla['A|0.005']['sin_resolucion']:.3f}; IC95 por días (A, 0,01) "
                  f"{bloque['IC95_confirma_por_dias']['A|0.01']}, (B, 0,01) {bloque['IC95_confirma_por_dias']['B|0.01']}"
                  f"; {time.time() - t0:.0f} s", flush=True)
            if "poder" in bloque:
                print("      poder (B, 0,005):", {q: round(bloque['poder'][f'B|0.005|q={q}'], 3) for q in QS})
                print("      poder (A, 0,005):", {q: round(bloque['poder'][f'A|0.005|q={q}'], 3) for q in QS})
    os.makedirs(RES, exist_ok=True)
    destino = os.path.join(RES, "s30a_calibracion.json")
    json.dump(salida, open(destino, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("escrito", destino, f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
