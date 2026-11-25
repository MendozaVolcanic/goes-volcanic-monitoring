r"""S28a, lecturas POST HOC (no están en el criterio; describen, no deciden).

1. Concentración de los disparos diurnos (12 a 24 UTC) de la unión por día en cada vecina y año: si pocos días ponen
   la mayoría, el intervalo por remuestreo de días es ancho y el R depende de esos días.
2. La vecina como placebo de Chillán: de los cuadros P de VOLCAT en Chillán (21-09 a 24-11-2026), qué fracción
   "alcanza" la unión puesta en Antuco o Longaví (disparo en el cuadro, el anterior o el siguiente, como
   s22b_medir.alcanzado). Un volcán sin pluma no debería seguir a VOLCAT de Chillán; si lo sigue tanto como Chillán,
   lo que la unión ve en esos cuadros es regional.

Lee D:\goes_notas\s26\s26a\tabla_2026.csv (clases de VOLCAT) y D:\goes_notas\s28\s28a\cuadros_<vecina>_<año>.csv.
Uso: python -I s28a_posthoc.py   (escribe resultados/s28a_posthoc.json)
"""
import collections
import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
TRAB = r"D:\goes_notas\s28\s28a"
TABLA_S26A = r"D:\goes_notas\s26\s26a\tabla_2026.csv"
VECINAS = ("antuco", "longavi")


def slot(h):
    return int(h[:2]) * 6 + int(h[3:5]) // 10


def leer(sitio, año):
    F, E, Fz, Fa = set(), set(), set(), set()
    with open(os.path.join(TRAB, f"cuadros_{sitio}_{año}.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["dia"], slot(r["hora"]))
            E.add(k)
            if r["F_u"] == "1":
                F.add(k)
            if r["F_z"] == "1":
                Fz.add(k)
            if r["F_a"] == "1":
                Fa.add(k)
    return F, E, Fz, Fa


def main():
    out = {"rotulo": "POST HOC: no estaba en el criterio; describe, no decide", "concentracion_dia": {},
           "placebo_de_chillan": {}}
    for s in VECINAS:
        for año in ("2025", "2026"):
            F, E, Fz, Fa = leer(s, año)
            c = collections.Counter(k[0] for k in F if k[1] >= 72)
            e = collections.Counter(k[0] for k in E if k[1] >= 72)
            tot = sum(c.values())
            top = c.most_common(5)
            out["concentracion_dia"][f"{s}_{año}"] = {
                "disparos": tot, "dias_con_disparo": len(c), "dias_evaluados": len(e),
                "fraccion_de_los_3_dias_mayores": round(sum(n for _, n in top[:3]) / tot, 3) if tot else None,
                "dias_mayores": [[d, n, int(sum(1 for k in Fz if k[0] == d and k[1] >= 72)),
                                  int(sum(1 for k in Fa if k[0] == d and k[1] >= 72)), e[d]] for d, n in top],
                "columnas_dias_mayores": ["dia", "disparos_union", "de_la_zona", "del_anillo", "evaluados_de_dia"]}
    with open(TABLA_S26A, encoding="utf-8") as f:
        ch = list(csv.DictReader(f))
    P = [(r["dia"], slot(r["hora"])) for r in ch if r["clase"] == "P"]
    Fch = {(r["dia"], slot(r["hora"])) for r in ch if r["F_a"] == "1" or r["F_z"] == "1"}
    Ech = {(r["dia"], slot(r["hora"])) for r in ch if r["ev_a"] == "1" or r["ev_z"] == "1"}

    def alcance(F, E):
        pe = [k for k in P if k in E]
        pa = [k for k in pe if any((k[0], k[1] + i) in F for i in (-1, 0, 1))]
        return pe, pa
    pe, pa = alcance(Fch, Ech)
    out["placebo_de_chillan"]["chillan"] = {"P_evaluados": len(pe), "P_alcanzados": len(pa)}
    for s in VECINAS:
        F, E, _, _ = leer(s, "2026")
        pe, pa = alcance(F, E)
        out["placebo_de_chillan"][s] = {"P_evaluados": len(pe), "P_alcanzados": len(pa),
                                        "por_dia": dict(collections.Counter(k[0] for k in pa))}
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "s28a_posthoc.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
