r"""V104 (verificador de S28b): tabla cuadro por cuadro de un día, Chillán contra las dos vecinas, y aciertos por día.

Por qué: para decidir si "disparan las tres cumbres a la vez" hay que ver, en cada cuadro de 10 minutos, la clase de
VOLCAT en Chillán (P = VOLCAT dibuja la pluma, N = no la dibuja), si dispara la zona de Chillán y si dispara la unión en
cada vecina. No corre el detector: lee los CSV de S26a y S28a (días hasta el 24-11-2026).

Uso: python -I v104_lado_a_lado.py 2026-11-10 [hora_ini hora_fin]
     python -I v104_lado_a_lado.py aciertos        (P evaluados y alcanzados por día: zona, unión y cada vecina)
Leyenda de cada celda: '.' evaluado sin disparo, 'X' disparo, ' ' no evaluado.
"""
import collections
import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
S28A = r"D:\goes_notas\s28\s28a"
TABLA = r"D:\goes_notas\s26\s26a\tabla_2026.csv"
ULTIMO = "2026-11-24"


def slot(h):
    return int(h[:2]) * 6 + int(h[3:5]) // 10


def hhmm(s):
    return f"{s // 6:02d}:{(s % 6) * 10:02d}"


def chillan():
    out = {}
    with open(TABLA, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            assert r["dia"] <= ULTIMO
            out[(r["dia"], slot(r["hora"]))] = r
    return out


def vecina(sitio):
    out = {}
    with open(os.path.join(S28A, f"cuadros_{sitio}_2026.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            assert r["dia"] <= ULTIMO
            out[(r["dia"], slot(r["hora"]))] = r
    return out


def celda(ev, F):
    return "X" if F else ("." if ev else " ")


def lado_a_lado(dia, s0, s1):
    ch, an, lo = chillan(), vecina("antuco"), vecina("longavi")
    print(f"{dia}  horas UTC (Chile = UTC-3)")
    print("UTC   Chile clase  Ch_zona Ch_anillo  Antuco Longavi")
    for s in range(s0, s1 + 1):
        r = ch.get((dia, s))
        cl = (r["clase"] or "-") if r else "?"
        cz = celda(r and r["ev_z"] == "1", r and r["F_z"] == "1")
        ca = celda(r and r["ev_a"] == "1", r and r["F_a"] == "1")
        a, b = an.get((dia, s)), lo.get((dia, s))
        print(f"{hhmm(s)} {hhmm((s - 18) % 144)} {cl:5s}  {cz:^7s} {ca:^9s}  "
              f"{celda(a is not None, a and a['F_u'] == '1'):^6s} {celda(b is not None, b and b['F_u'] == '1'):^7s}")


def aciertos():
    """Por día: P evaluados y alcanzados (disparo en el cuadro, el anterior o el siguiente, como s28a_posthoc)."""
    ch = chillan()
    P = [k for k, r in ch.items() if r["clase"] == "P"]
    conj = {"zona": ({k for k, r in ch.items() if r["F_z"] == "1"}, {k for k, r in ch.items() if r["ev_z"] == "1"}),
            "union": ({k for k, r in ch.items() if r["F_a"] == "1" or r["F_z"] == "1"},
                      {k for k, r in ch.items() if r["ev_a"] == "1" or r["ev_z"] == "1"})}
    for s in ("antuco", "longavi"):
        v = vecina(s)
        conj[s] = ({k for k, r in v.items() if r["F_u"] == "1"}, set(v))
    dias = sorted({k[0] for k in P})
    print("dia         P   " + "  ".join(f"{n:>9s}" for n in conj))
    tot = collections.Counter()
    for d in dias:
        fila = []
        for n, (F, E) in conj.items():
            pe = [k for k in P if k[0] == d and k in E]
            pa = [k for k in pe if any((k[0], k[1] + i) in F for i in (-1, 0, 1))]
            fila.append(f"{len(pa):>3d} de {len(pe):<2d}")
            tot[n, "a"] += len(pa)
            tot[n, "e"] += len(pe)
        print(f"{d} {sum(1 for k in P if k[0] == d):3d}   " + "  ".join(fila))
    print(f"total      {len(P):3d}   " + "  ".join(f"{tot[n, 'a']:>3d} de {tot[n, 'e']:<2d}" for n in conj))


if __name__ == "__main__":
    if sys.argv[1] == "aciertos":
        aciertos()
    else:
        h0 = slot(sys.argv[2]) if len(sys.argv) > 2 else 0
        h1 = slot(sys.argv[3]) if len(sys.argv) > 3 else 143
        lado_a_lado(sys.argv[1], h0, h1)
