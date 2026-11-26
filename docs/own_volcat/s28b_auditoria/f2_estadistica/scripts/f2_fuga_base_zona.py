r"""F2 (S28b): ¿el umbral "sin el día d" de la zona (S25a, S26a) depende del día d a través de las bases de los otros días?

Por qué: en el ensayo en seco de la zona, el umbral del día d es el percentil de S de los otros días, pero el S de cada
otro día d'' se calculó con una línea base que excluye d'' y SÍ incluye d. El día evaluado entra así, de segunda mano,
al umbral con que se lo juzga. El margen de p* en S26a es chico (unión 0,0515 a percentil 5 contra el tope 0,05): un
corrimiento de una milésima en el seco puede cambiar p*. Aquí se rehace el seco de la zona con el día fuera de verdad:
para cada d, la base de cada d'' excluye {d, d''} y el umbral sale de esos S.
Control: con la base de la regla (sólo sin d'') tiene que dar el seco publicado (176 de 5.499 a percentil 5).
Uso: python -I f2_fuga_base_zona.py
"""
import json
import os
import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s25a_crater", "scripts"))
import s25a_medir as Z  # noqa: E402

B, H24 = Z.B, Z.H24
SAL = r"D:\goes_notas\s28\s28b\f2"


def seco(SR_por_d, ULs):
    nF = nE = 0
    fr = []
    for d in range(Z.NR):
        F, ev = Z.disparos(SR_por_d[d], d, ULs[d], ULs[d - 1] if d else None)
        nF += int(F.sum())
        nE += int(ev.sum())
        if ev.sum():
            fr.append(F.sum() / ev.sum())
    return {"disparos": nF, "evaluados": nE, "global": round(nF / nE, 5), "media_por_dia": round(float(np.mean(fr)), 5)}


def main():
    t = time.time()
    btd25 = np.load(Z._npy("r25_btd"), mmap_mode="r")
    acm25 = np.load(Z._npy("r25_acm"))
    hay25 = np.isfinite(btd25[:, :, Z.ZONA[0]])
    est25 = Z.costumbre(acm25, hay25)
    FD25, DIN25 = Z.nubes(acm25, est25)
    G25 = FD25 <= B.G_MAX
    USA25 = G25 & H24.despejada("chillan", acm25) & hay25
    btd25 = np.asarray(btd25)
    bctrl = Z.base(btd25, USA25, Z.CTRL)
    C25 = Z.regional(btd25, DIN25, bctrl)
    IZ = np.arange(len(Z.ZONA))
    Z25 = np.ascontiguousarray(btd25[:, :, Z.ZONA])
    del btd25
    BZ = np.array([Z.base(Z25, USA25, IZ, excl=d) for d in range(Z.NR)])
    SR, _ = Z.tabla_S(Z25, C25, BZ, G25)
    print(f"zona 2025 lista, {time.time() - t:.0f} s", flush=True)
    # S de cada día d'' con la base sin {d, d''}, para cada d
    SRd = np.empty((Z.NR, Z.NR, 144))
    for d in range(Z.NR):
        usar = USA25.copy()
        usar[d] = False
        Bd = np.array([Z.base(Z25, usar, IZ, excl=x) if x != d else BZ[d] for x in range(Z.NR)])
        SRd[d], _ = Z.tabla_S(Z25, C25, Bd, G25)
        SRd[d, d] = SR[d]
        if d % 10 == 0:
            print(f"  d={d}, {time.time() - t:.0f} s", flush=True)
    out = {}
    for p in (5.0, 4.75, 4.5):
        B.PCT_U = p
        UL = [Z.umbral(SR, excl=d) for d in range(Z.NR)]
        UL2 = [Z.umbral(SRd[d], excl=d) for d in range(Z.NR)]
        # para la persistencia de las 00:00 el día previo se juzga con su propio umbral, como en la regla
        out[str(p)] = {"publicado_regla": seco([SR] * Z.NR, UL),
                       "dia_fuera_de_verdad": seco([SRd[d] for d in range(Z.NR)], UL2)}
        print(p, json.dumps(out[str(p)]), flush=True)
    json.dump(out, open(os.path.join(SAL, "fuga_base_zona.json"), "w", encoding="utf-8"), indent=1)
    print(f"fin {time.time() - t:.0f} s")


if __name__ == "__main__":
    main()
