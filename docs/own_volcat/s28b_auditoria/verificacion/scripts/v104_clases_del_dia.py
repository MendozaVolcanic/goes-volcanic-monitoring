r"""V104 (verificador de S28b): disparos de Chillán de un día por clase de VOLCAT, y cuántos coinciden con una vecina.

Por qué: si las tres cumbres disparan juntas, importa en qué clase de cuadro lo hace Chillán. En un cuadro P, VOLCAT
dibuja la pluma (un disparo ahí cuenta como acierto). En un cuadro N, VOLCAT no dibuja nada a 50 km en +-60 min (un
disparo ahí cuenta como falsa alarma en S26a). Sólo lee CSV ya escritos (días hasta el 24-11-2026).
Uso: python -I v104_clases_del_dia.py 2026-11-10 [2026-11-14 ...]
"""
import collections
import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
S28A = r"D:\goes_notas\s28\s28a"
TABLA = r"D:\goes_notas\s26\s26a\tabla_2026.csv"


def slot(h):
    return int(h[:2]) * 6 + int(h[3:5]) // 10


def main():
    ch = {}
    with open(TABLA, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            assert r["dia"] <= "2026-11-24"
            ch[r["dia"], slot(r["hora"])] = r
    vec = {}
    for s in ("antuco", "longavi"):
        with open(os.path.join(S28A, f"cuadros_{s}_2026.csv"), encoding="utf-8") as f:
            vec[s] = {(r["dia"], slot(r["hora"])) for r in csv.DictReader(f) if r["F_u"] == "1"}
    for d in sys.argv[1:]:
        ev, dis, con = collections.Counter(), collections.Counter(), collections.Counter()
        for (dd, s), r in ch.items():
            if dd != d or s < 72:
                continue
            cl = r["clase"] or "(sin clase)"
            if r["ev_a"] == "1" or r["ev_z"] == "1":
                ev[cl] += 1
            if r["F_a"] == "1" or r["F_z"] == "1":
                dis[cl] += 1
                for v in vec:
                    con[cl, v] += (d, s) in vec[v]
                con[cl, "las dos"] += (d, s) in vec["antuco"] and (d, s) in vec["longavi"]
        print(f"{d}, 12:00 a 23:50 UTC. Chillán (unión) por clase de VOLCAT:")
        for cl in sorted(ev):
            print(f"  {cl:12s} evaluados {ev[cl]:3d}  disparos {dis[cl]:3d}  de ellos con disparo de Antuco en el mismo "
                  f"cuadro {con[cl, 'antuco']:2d}, de Longaví {con[cl, 'longavi']:2d}, de las dos {con[cl, 'las dos']:2d}")
        for v in vec:
            n = collections.Counter((ch[k]["clase"] or "(sin clase)") if k in ch else "(sin fila)"
                                    for k in vec[v] if k[0] == d and k[1] >= 72)
            print(f"  disparos de {v} según la clase de VOLCAT de Chillán en ese cuadro: {dict(n)}")


if __name__ == "__main__":
    main()
