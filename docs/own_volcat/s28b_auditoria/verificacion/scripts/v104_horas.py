r"""V104 (verificador de S28b): horas de los disparos de cada cumbre y de los cuadros P de VOLCAT de Chillán.

Por qué: el INFORME y STATUS de S28a dicen que el 10-11-2026 "disparan las tres cumbres a la vez por la tarde".
Aquí se listan, cuadro por cuadro, las horas (UTC) de los disparos de la unión en Antuco y Longaví, los cuadros P
de Chillán y los disparos de Chillán, y se cuenta la coincidencia con varias ventanas. No corre el detector: sólo lee
los CSV que S28a y S26a ya escribieron (días hasta el 24-11-2026).

Lee (sólo lectura):
  D:\goes_notas\s28\s28a\cuadros_<vecina>_2026.csv   (S28a: ev_u, F_u, ev_a, F_a, ev_z, F_z por cuadro evaluado)
  D:\goes_notas\s26\s26a\tabla_2026.csv              (S26a: clase de VOLCAT y disparos de Chillán por cuadro)
Uso: python -I v104_horas.py [dia ...]     (por defecto 2026-11-10 y 2026-11-14)
Escribe D:\goes_notas\s28\s28b\v101\v104_horas.json
"""
import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
S28A = r"D:\goes_notas\s28\s28a"
TABLA = r"D:\goes_notas\s26\s26a\tabla_2026.csv"
SAL = r"D:\goes_notas\s28\s28b\v101"
ULTIMO = "2026-11-24"


def slot(h):
    return int(h[:2]) * 6 + int(h[3:5]) // 10


def hhmm(s):
    return f"{s // 6:02d}:{(s % 6) * 10:02d}"


def tramos(slots):
    """Rachas de cuadros consecutivos, como texto: 'inicio a fin (n)'."""
    out = []
    for x in sorted(slots):
        if out and x == out[-1][1] + 1:
            out[-1][1] = x
            out[-1][2] += 1
        else:
            out.append([x, x, 1])
    return [f"{hhmm(a)} a {hhmm(b)} ({n})" for a, b, n in out]


def leer_vecina(sitio):
    ev, F, Fz, Fa = {}, {}, {}, {}
    with open(os.path.join(S28A, f"cuadros_{sitio}_2026.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            assert r["dia"] <= ULTIMO, r["dia"]
            d, s = r["dia"], slot(r["hora"])
            ev.setdefault(d, set()).add(s)
            for col, dic in (("F_u", F), ("F_z", Fz), ("F_a", Fa)):
                if r[col] == "1":
                    dic.setdefault(d, set()).add(s)
    return ev, F, Fz, Fa


def leer_chillan():
    P, ev, F, Fz, Fa, clases = {}, {}, {}, {}, {}, {}
    with open(TABLA, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            assert r["dia"] <= ULTIMO, r["dia"]
            d, s = r["dia"], slot(r["hora"])
            clases.setdefault(d, {}).setdefault(r["clase"], set()).add(s)
            if r["clase"] == "P":
                P.setdefault(d, set()).add(s)
            if r["ev_a"] == "1" or r["ev_z"] == "1":
                ev.setdefault(d, set()).add(s)
            if r["F_a"] == "1" or r["F_z"] == "1":
                F.setdefault(d, set()).add(s)
            if r["F_z"] == "1":
                Fz.setdefault(d, set()).add(s)
            if r["F_a"] == "1":
                Fa.setdefault(d, set()).add(s)
    return P, ev, F, Fz, Fa, clases


def main():
    dias = sys.argv[1:] or ["2026-11-10", "2026-11-14"]
    P, evc, Fc, Fzc, Fac, clases = leer_chillan()
    vec = {s: leer_vecina(s) for s in ("antuco", "longavi")}
    out = {}
    for d in dias:
        p = P.get(d, set())
        fc, fzc, fac, ec = Fc.get(d, set()), Fzc.get(d, set()), Fac.get(d, set()), evc.get(d, set())
        o = {"chillan": {"clases": {k or "(sin clase)": len(v) for k, v in clases.get(d, {}).items()},
                         "P": [hhmm(s) for s in sorted(p)], "P_tramos": tramos(p),
                         "P_evaluados_por_chillan": len(p & ec),
                         "disparos_union": tramos(fc), "n_disparos_union": len(fc),
                         "disparos_zona": tramos(fzc), "disparos_anillo": tramos(fac),
                         "P_con_disparo_en_el_cuadro": len(p & fc),
                         "P_con_disparo_de_zona_en_el_cuadro": len(p & fzc),
                         "evaluados": tramos(ec)}}
        print(f"\n===== {d} (horas UTC; Chile = UTC-3) =====")
        print("Chillán clases:", o["chillan"]["clases"])
        print("Chillán P:", o["chillan"]["P_tramos"], "| lista:", " ".join(o["chillan"]["P"]))
        print("Chillán evaluados:", o["chillan"]["evaluados"])
        print("Chillán disparos unión:", o["chillan"]["disparos_union"])
        print("Chillán disparos zona:", o["chillan"]["disparos_zona"], "| anillo:", o["chillan"]["disparos_anillo"])
        print("Chillán: P evaluados", len(p & ec), "| P con disparo en el cuadro", len(p & fc), "| de zona",
              len(p & fzc))
        for s, (ev, F, Fz, Fa) in vec.items():
            f, e = F.get(d, set()), ev.get(d, set())
            fd = {x for x in f if x >= 72}                      # día del criterio: 12:00 a 23:50 UTC
            v = {"n_disparos_union_24h": len(f), "n_disparos_union_12a24utc": len(fd),
                 "disparos_union": tramos(f), "disparos_zona": tramos(Fz.get(d, set())),
                 "disparos_anillo": tramos(Fa.get(d, set())), "evaluados": tramos(e),
                 "primer_disparo_12a24": hhmm(min(fd)) if fd else None,
                 "ultimo_disparo_12a24": hhmm(max(fd)) if fd else None,
                 "P_de_chillan_evaluados_por_la_vecina": len(p & e),
                 "P_de_chillan_no_evaluados_por_la_vecina": [hhmm(x) for x in sorted(p - e)],
                 "coincidencia_con_P": {}}
            for w in (0, 1, 3, 6):                              # mismo cuadro, +-10, +-30, +-60 min
                pe = [k for k in p if k in e]
                pa = [k for k in pe if any((k + i) in f for i in range(-w, w + 1))]
                v["coincidencia_con_P"][f"+-{w * 10} min"] = [len(pa), len(pe)]
            # al revés: de los disparos de la vecina, cuántos caen en un cuadro P de Chillán
            v["disparos_en_cuadro_P_de_chillan"] = [len(f & p), len(f)]
            v["disparos_en_cuadro_con_disparo_de_chillan"] = [len(f & fc), len(f)]
            v["disparos_en_cuadro_con_disparo_de_zona_de_chillan"] = [len(f & fzc), len(f)]
            v["disparos_antes_del_primer_P"] = len([x for x in f if p and x < min(p)])
            v["disparos_despues_del_ultimo_P"] = len([x for x in f if p and x > max(p)])
            o[s] = v
            print(f"{s}: disparos unión {v['disparos_union']} (24 h {len(f)}, de 12 a 24 UTC {len(fd)})")
            print(f"   zona {v['disparos_zona']} | anillo {v['disparos_anillo']}")
            print(f"   evaluados {v['evaluados']}")
            print(f"   P de Chillán evaluados por {s}: {len(p & e)} de {len(p)}; no evaluados: "
                  f"{' '.join(v['P_de_chillan_no_evaluados_por_la_vecina'])}")
            print(f"   P alcanzados / P evaluados por ventana: {v['coincidencia_con_P']}")
            print(f"   disparos en cuadro P de Chillán: {v['disparos_en_cuadro_P_de_chillan']}; en cuadro con disparo "
                  f"de Chillán: {v['disparos_en_cuadro_con_disparo_de_chillan']}; con disparo de la zona de Chillán: "
                  f"{v['disparos_en_cuadro_con_disparo_de_zona_de_chillan']}; antes del primer P: "
                  f"{v['disparos_antes_del_primer_P']}; después del último P: {v['disparos_despues_del_ultimo_P']}")
        out[d] = o
    os.makedirs(SAL, exist_ok=True)
    json.dump(out, open(os.path.join(SAL, "v104_horas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
