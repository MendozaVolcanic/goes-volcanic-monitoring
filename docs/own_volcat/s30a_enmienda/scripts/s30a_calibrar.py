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

Conjunto de referencia: los días del fondo MÁS los dos días observados (prueba de permutación exacta). Una segunda
corrida que los sacaba del conjunto (lo que proponía S28b §4a.2) dio en el anillo CONFIRMA falso de 3,5 % a alfa 0,01 y
1,9 % a 0,002: si un solo día placebo está "encendido" a esas horas y no está en la referencia, ninguna colocación lo
iguala y el p cae al piso. Log: D:\goes_notas\s30\s30a\calibrar_v2_SIN_DIAS_OBSERVADOS_EN_LA_REFERENCIA_DESCARTADO.log.

Variantes que se miden (las dos con el mismo alfa y el mismo R mínimo de cada criterio):
  A  sólo el nulo de 2025 decide (la recomendación de S28b §4a).
  B  deciden el nulo de 2025 Y el de 2026 sin VOLCAT (días de 21-09 a 24-11-2026 sin P; en el placebo de 2026 los dos
     días del placebo van una sola vez, como días observados). Por qué se mide: la zona dispara en 2026 fuera de VOLCAT 4 a 5 veces más que en 2025
     (V201: 23,1 % contra 5,1 %); un nulo sólo de 2025 premiaría "2026 no es 2025", que es justo lo que pN quería
     atajar y que la enmienda deja informativo.
El nulo de 2024 se calcula siempre y es informativo.

Poder: sobre los mismos casos placebo (2025 y 2026 sin P), se fuerza que en cada día una fracción q de los P evaluados
quede alcanzada (los alcanzados del placebo se conservan) y se cuenta la fracción de casos decidibles que la regla
escribe CONFIRMA.

Uso: python -I -B -u s30a_calibrar.py [npz|-] [a|z|u]   (por omisión D:\goes_notas\s30\s30a\disparos_s30a.npz y las
     tres reglas; con a, z o u, una sola regla y salida resultados/s30a_calibracion_<parte>.json)
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

NPZ = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else r"D:\goes_notas\s30\s30a\disparos_s30a.npz"
SOLO = sys.argv[2] if len(sys.argv) > 2 else None        # "a", "z" o "u": una sola regla (para correr en paralelo)
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


def p_vectorizado(eo, ao, E1, A1, E2, A2, permitido):
    """p_día de n casos de k = 2 a la vez (la misma cuenta que s30a_nulo.p_dia, comprobada en comprobar()).
    E1, A1, E2, A2: (n, nd + 2), las dos últimas columnas son los dos días observados (prueba de permutación exacta:
    el conjunto de referencia incluye los días observados). permitido: (n, nd + 2). La colocación observada
    (columna nd - 2 para la plantilla 1, nd - 1 para la 2) no se cuenta: es el "1 +".
    Devuelve p (n,), válidas (n,)."""
    n, nd = E1.shape
    R = ao.sum(1) / np.maximum(eo.sum(1), 1)
    Et = E1[:, :, None] + E2[:, None, :]                      # (n, nd, nd)
    At = A1[:, :, None] + A2[:, None, :]
    ok = (Et >= N.MIN_P_EVAL) & (E1[:, :, None] > 0) & (E2[:, None, :] > 0)
    ok &= ~np.eye(nd, dtype=bool)[None]
    ok &= permitido[:, :, None] & permitido[:, None, :]
    ok[:, nd - 2, nd - 1] = False
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


def aumentado(Mi, Mj, eo, ao, c, EVp, ALp, fo, mismo):
    """Cuentas del fondo más los dos días observados como columnas finales. ao trae los alcanzados (con inyección si la
    hay) de cada plantilla sobre su propio día; la plantilla sobre el OTRO día observado usa sus alcanzados reales (la
    inyección es pluma en las horas P de ese día, no en las de la otra plantilla)."""
    Mi_f, Mj_f = Mi.astype(float), Mj.astype(float)
    E1, A1 = Mi_f @ fo.EV.T.astype(float), Mi_f @ fo.EA.T
    E2, A2 = Mj_f @ fo.EV.T.astype(float), Mj_f @ fo.EA.T
    EVi, EVj = EVp[c[:, 0]], EVp[c[:, 1]]
    ALi, ALj = ALp[c[:, 0]], ALp[c[:, 1]]
    e1j, a1j = (Mi & EVj).sum(1), (Mi & EVj & ALj).sum(1)
    e2i, a2i = (Mj & EVi).sum(1), (Mj & EVi & ALi).sum(1)
    E1 = np.column_stack([E1, eo[:, 0], e1j])
    A1 = np.column_stack([A1, ao[:, 0], a1j])
    E2 = np.column_stack([E2, e2i, eo[:, 1]])
    A2 = np.column_stack([A2, a2i, ao[:, 1]])
    perm = np.ones(E1.shape, bool)
    if mismo:                                   # el placebo sale del mismo fondo: sus días no van dos veces
        perm[np.arange(len(c)), c[:, 0]] = False
        perm[np.arange(len(c)), c[:, 1]] = False
    return E1, A1, E2, A2, perm


def evaluar(c, Mi, Mj, eo, ao, fondos, pl, EVp, ALp, bloque=300, q=None):
    """p y válidas de cada fondo para todos los casos del placebo pl."""
    n = len(c)
    out = {}
    if q is not None:
        ao = np.maximum(ao, np.ceil(q * eo - 1e-9)).astype(int)
    for nom, fo in fondos.items():
        p = np.ones(n)
        nv = np.zeros(n, int)
        for b0 in range(0, n, bloque):
            sl = slice(b0, min(n, b0 + bloque))
            E1, A1, E2, A2, perm = aumentado(Mi[sl], Mj[sl], eo[sl], ao[sl], c[sl], EVp, ALp, fo, nom == pl)
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


def comprobar(c, Mi, Mj, eo, ao, fondos, pl, EVp, ALp, pv):
    """La cuenta vectorizada tiene que dar lo mismo que s30a_nulo.p_dia (la que usa la medida) en 300 casos al azar."""
    idx = rng.choice(len(c), min(300, len(c)), replace=False)
    malos = 0
    for x in idx:
        if not N.decidible(eo[x]):
            continue
        i, j = c[x, 0], c[x, 1]
        for nom, fo in fondos.items():
            EV = np.concatenate([fo.EV, EVp[[i, j]]])
            AL = np.concatenate([fo.AL, ALp[[i, j]]])
            ef, af = N.tabla_fondo(np.stack([Mi[x], Mj[x]]), EV, AL)
            nd = fo.nd
            pool = [d for d in range(nd) if not (nom == pl and d in (i, j))] + [nd, nd + 1]
            p, R, nv, ng, ntot = N.p_dia(eo[x], ao[x], ef, af, pool, obs=(nd, nd + 1))
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
        if SOLO and k != SOLO:
            continue
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

            pv, _ = evaluar(c, Mi, Mj, eo, ao, fondos, pl, EVp, ALp)
            ncomp = comprobar(c, Mi, Mj, eo, ao, fondos, pl, EVp, ALp, pv)
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
                    pvq, aoq = evaluar(c, Mi, Mj, eo, ao, fondos, pl, EVp, ALp, q=q)
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
    destino = os.path.join(RES, f"s30a_calibracion{'_' + SOLO if SOLO else ''}.json")
    json.dump(salida, open(destino, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("escrito", destino, f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
