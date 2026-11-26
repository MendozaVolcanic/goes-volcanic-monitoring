r"""S31b: el gatillo v2 de la enmienda (`enmienda_v2_2026-11-26.md` §3) medido SÓLO en placebo.

Pregunta: si la medida única espera a 20 P evaluables con al menos 2 días de 5 P evaluables o más, ¿la regla de S30a
(alfa 0,001, variante A, nulo por días sin condicionar al gatillo) sigue dando 1 % o menos de CONFIRMA falso dentro de
los casos que cumplen ese gatillo? ¿Y cuánto poder se gana?

Reutiliza, sin copiarlas, las funciones de s30a_calibrar.py (casos, evaluar, rotulos, ic_por_dias, comprobar) y el
mismo fondo congelado (SHA-256 de la enmienda v1 §2.5). Ningún día posterior al 24-11-2026 (aserción de cargar()).

P evaluables en placebo (enmienda v2 §3): los P de la plantilla evaluados por la UNIÓN (S26a, p* = 4,75) en el día
placebo, el mismo subconjunto de casos para las tres reglas. Contraste: los P evaluados de cada regla (el `menor>=5` de
S30a).

Uso: python -I -B -u s31b_gatillo.py a|z|u
Salida: resultados/s31b_gatillo_<parte>.json; log a mano en D:\goes_notas\s31\s31b\.
"""
import hashlib
import json
import os
import sys
import time

import numpy as np

PARTE = sys.argv[1]
assert PARTE in ("a", "z", "u")
sys.argv = [sys.argv[0], "-", PARTE]                     # s30a_calibrar lee NPZ y SOLO de argv al importarse
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s30a_calibrar as K  # noqa: E402
import s30a_nulo as N  # noqa: E402

RES = os.path.join(os.path.dirname(AQUI), "resultados")
SHA_FONDO = "62b5fba795234f40a11c44f22dcbf6c79298d2d3de18d2a95282098615511cd1"
ALFA, VAR = 0.001, "A"
MIN_TOTAL, MIN_POR_DIA = 20, 5
NOM = {"a": "S23b anillo", "z": "S25a zona", "u": "S26a unión"}[PARTE]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(2**22), b""):
            h.update(b)
    return h.hexdigest()


def frac(conf, sel):
    n = int(sel.sum())
    return (float((conf & sel).sum() / n) if n else None), n


def main():
    t0 = time.time()
    assert sha(K.NPZ) == SHA_FONDO, "el fondo no es el congelado de la enmienda v1"
    Zf, CL, dias26 = K.cargar()
    _, pct, rmin = K.REGLAS[NOM]
    s30a = json.load(open(os.path.join(RES, f"s30a_calibracion_{PARTE}.json"), encoding="utf-8"))["reglas"][NOM]
    T_dias = [d for d in range(65) if (CL[d] == "P").any()]
    T = np.array([CL[d] == "P" for d in T_dias])
    nP = T.sum(1)
    pares = [(a, b) for a in range(len(T)) for b in range(len(T)) if a != b and nP[a] + nP[b] >= K.MIN_P_GATILLO]
    assert len(pares) == 36
    sinP = [d for d in range(65) if not (CL[d] == "P").any()]
    F25, E25 = Zf[f"F25_{PARTE}_{pct}"], Zf[f"E25_{PARTE}_{pct}"]
    A25 = K.alc(F25, E25)
    fondos = {"2025": K.Fondo("2025", E25, A25)}            # variante A: sólo decide el nulo de 2025
    placebos = {"2025": (E25, A25, Zf["E25_u_4.75"])}
    F26, E26 = Zf[f"F26_{PARTE}_{pct}"], Zf[f"E26_{PARTE}_{pct}"]
    A26 = K.alc(F26, E26)
    placebos["2026 sin VOLCAT"] = (E26[sinP], A26[sinP], Zf["E26_u_4.75"][sinP])
    F24, E24 = Zf[f"F24_{PARTE}_{pct}"], Zf[f"E24_{PARTE}_{pct}"]
    placebos["2024"] = (E24, K.alc(F24, E24), Zf["E24_u_4.75"])
    salida = {"enmienda": "s30a_enmienda/enmienda_v2_2026-11-26.md §3", "regla": NOM, "percentil": pct, "R_min": rmin,
              "alfa": ALFA, "variante": VAR, "npz": K.NPZ, "sha_npz": SHA_FONDO,
              "evaluables_placebo": "P de la plantilla evaluados por la unión (E_u a p* 4,75) en el día placebo",
              "placebos": {}}
    print(f"== {NOM} (percentil {pct}, R mínimo {rmin}); alfa {ALFA}, variante {VAR}", flush=True)
    for pl, (EVp, ALp, EUp) in placebos.items():
        c, Mi, Mj, eo, ao = K.casos(T, pares, EVp, ALp)
        eu = np.stack([(Mi & EUp[c[:, 0]]).sum(1), (Mj & EUp[c[:, 1]]).sum(1)], 1)
        dec = (eo.sum(1) >= N.MIN_P_EVAL) & ((eo > 0).sum(1) >= N.MIN_DIAS)
        sub = {"todos los decidibles (S30a)": dec,
               "gatillo S30a en evaluables (suma >= 20, los 2 días >= 1)":
                   dec & (eu.sum(1) >= MIN_TOTAL) & (eu.min(1) >= 1),
               "GATILLO v2 (suma >= 20, los 2 días >= 5)": dec & (eu.sum(1) >= MIN_TOTAL) & (eu.min(1) >= MIN_POR_DIA),
               "contraste: evaluados de la regla, los 2 días >= 5 (menor>=5 de S30a)": dec & (eo.min(1) >= 5),
               "contraste: evaluados de la regla, suma >= 20 y los 2 días >= 5":
                   dec & (eo.sum(1) >= MIN_TOTAL) & (eo.min(1) >= MIN_POR_DIA)}
        g2 = sub["GATILLO v2 (suma >= 20, los 2 días >= 5)"]
        # p del nulo de 2025 sólo donde hace falta (casos decidibles)
        idx = np.flatnonzero(dec)
        pv_s, _ = K.evaluar(c[idx], Mi[idx], Mj[idx], eo[idx], ao[idx], fondos, pl, EVp, ALp)
        p = np.ones(len(c))
        nv = np.zeros(len(c), int)
        p[idx], nv[idx] = pv_s["2025"]
        pv = {"2025": (p, nv)}
        # comprobación contra s30a_nulo.p_dia (la cuenta de la medida), casos al azar del subconjunto del gatillo v2
        ig = np.flatnonzero(g2)
        ncomp = 0
        if len(ig):
            ncomp = K.comprobar(c[ig], Mi[ig], Mj[ig], eo[ig], ao[ig], fondos, pl, EVp, ALp,
                                {"2025": (p[ig], nv[ig])})
        _, _, conf, parc = K.rotulos(eo, ao, pv, ALFA, rmin, VAR)
        bloque = {"casos": len(c), "comprobados_contra_p_dia": ncomp, "confirma_falso": {}}
        for nom_s, sel in sub.items():
            f, n = frac(conf, sel)
            ic = K.ic_por_dias(c, sel, conf & sel, len(EVp)) if n else [None, None]
            bloque["confirma_falso"][nom_s] = {"fraccion": f, "casos": n, "confirma": int((conf & sel).sum()),
                                               "IC95_por_dias": ic}
        # tiene que reproducir S30a §5.3
        ref = s30a["placebos"][pl]
        assert ref["decidibles"] == int(dec.sum()), (ref["decidibles"], int(dec.sum()))
        assert ref["tabla"][f"{VAR}|{ALFA}"]["confirma"] == bloque["confirma_falso"]["todos los decidibles (S30a)"][
            "fraccion"], "no reproduce el CONFIRMA falso de S30a"
        # poder (enmienda v2 §3b): sólo 2025 y 2026 sin VOLCAT, como S30a
        if pl in ("2025", "2026 sin VOLCAT"):
            m5 = sub["contraste: evaluados de la regla, los 2 días >= 5 (menor>=5 de S30a)"]
            iq = np.flatnonzero(g2 | m5)
            pod = {}
            for q in K.QS:
                pvq_s, aoq_s = K.evaluar(c[iq], Mi[iq], Mj[iq], eo[iq], ao[iq], fondos, pl, EVp, ALp, q=q)
                _, _, cq, _ = K.rotulos(eo[iq], aoq_s, pvq_s, ALFA, rmin, VAR)
                cg = np.zeros(len(c), bool)
                cg[iq] = cq
                fg, ng = frac(cg, g2)
                fm, nm = frac(cg, m5)
                r30 = ref["poder_por_dia_menor"].get(f"{VAR}|{ALFA}|q={q}|menor>=5")
                if r30 is not None:
                    assert abs(r30[0] - fm) < 1e-12 and r30[1] == nm, f"no reproduce el poder menor>=5 de S30a a q={q}"
                pod[f"q={q}"] = {"gatillo_v2": [fg, ng], "menor>=5_S30a_reproducido": [fm, nm],
                                 "todos_los_decidibles_S30a": ref["poder"][f"{VAR}|{ALFA}|q={q}"]}
            bloque["poder"] = pod
        salida["placebos"][pl] = bloque
        cf = bloque["confirma_falso"]
        print(f"   placebo {pl}: " + "; ".join(f"{k[:40]}: {v['confirma']}/{v['casos']} = "
                                               f"{(v['fraccion'] or 0) * 100:.3f} % IC {v['IC95_por_dias']}"
                                               for k, v in cf.items()) + f"; {time.time() - t0:.0f} s", flush=True)
        if "poder" in bloque:
            print("      poder gatillo v2:", {k: (None if v["gatillo_v2"][0] is None else round(v["gatillo_v2"][0], 3))
                                              for k, v in bloque["poder"].items()}, flush=True)
    os.makedirs(RES, exist_ok=True)
    destino = os.path.join(RES, f"s31b_gatillo_{PARTE}.json")
    json.dump(salida, open(destino, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("escrito", destino, f"{time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
