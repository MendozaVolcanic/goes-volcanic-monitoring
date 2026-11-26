r"""V101 (verificador de S28b): qué rótulo da la regla escrita de S28a, de día y de noche, y cuán firme es.

Por qué: el hallazgo 101 dice que el rótulo de día es MIXTO por su regla y que el texto lo lee como otro rótulo.
Antes de mirar el texto hay que saber, sin fiarse del campo "veredicto" del JSON, qué rótulo sale de las cifras.

Pasos:
 A. Rótulo con la función `veredicto` de S28a, sacada SIN MODIFICAR del fuente (por AST, sin importar el módulo, que
    carga cubos GOES), aplicada a las cifras de resultados/s28a_resultado.json.
 B. Rótulo con una segunda implementación, escrita aquí leyendo sólo la tabla de §5 del criterio.
 C. Las cifras del JSON, ¿salen del caché? Se reconstruyen los conteos por día desde
    D:\goes_notas\s28\s28a\cuadros_<vecina>_<año>.csv y se corre la función `razon` de S28a (semilla 0, 2.000
    réplicas). Tiene que dar el mismo R y el mismo intervalo.
 D. Firmeza (NO está en el criterio, es lectura del verificador): el mismo remuestreo con otras 200 semillas, y sin el
    día de más disparos de cada año. Dice cuántas veces el límite inferior de Antuco de día queda sobre 1.

No corre el detector ni abre cuadros GOES: sólo lee JSON y CSV ya escritos (días hasta el 24-11-2026).
Uso: python -I v101_rotulo.py     (escribe D:\goes_notas\s28\s28b\v101\v101_rotulo.json)
"""
import ast
import csv
import json
import math
import os
import sys
from datetime import datetime, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
S28A = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "s28a_vecinas"))
FUENTE = os.path.join(S28A, "scripts", "s28a_medir.py")
RESULTADO = os.path.join(S28A, "resultados", "s28a_resultado.json")
CACHE = r"D:\goes_notas\s28\s28a"
SAL = r"D:\goes_notas\s28\s28b\v101"
DIAS = {"2025": (datetime(2025, 9, 21), 62), "2026": (datetime(2026, 9, 21), 65)}
RANGO = {"noche": range(18, 54), "dia": range(72, 144)}          # criterio §2: 03:00 a 08:50 y 12:00 a 23:50 UTC


def funciones_de_s28a():
    """Compila `razon`, `_r` y `veredicto` tal como están en s28a_medir.py, con sus constantes."""
    arbol = ast.parse(open(FUENTE, encoding="utf-8").read())
    ns = {"np": np, "math": math}
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign):
            nombres = [n.id for t in nodo.targets for n in ast.walk(t) if isinstance(n, ast.Name)]
            if set(nombres) & {"N_BOOT", "SEMILLA", "MIN_EVAL", "R_SOSTIENE"}:
                exec(compile(ast.Module([nodo], []), FUENTE, "exec"), ns)
        if isinstance(nodo, ast.FunctionDef) and nodo.name in ("razon", "_r", "veredicto"):
            exec(compile(ast.Module([nodo], []), FUENTE, "exec"), ns)
    return ns


def regla_del_criterio(vec, r_ch):
    """Segunda implementación, leída de la tabla de §5 del criterio, en su orden."""
    if any(v[a][1] < 300 for v in vec.values() for a in ("2025", "2026")):
        return "NO DECIDIBLE"
    if all(v["R"] <= 1.5 and v["IC95"][1] < r_ch for v in vec.values()):
        return "SE SOSTIENE"
    if all(v["R"] >= 1.5 and v["IC95"][0] > 1 for v in vec.values()):
        return "NO SE SOSTIENE"
    sube = [s for s, v in vec.items() if v["R"] >= 1.5 and v["IC95"][0] > 1]
    otra = [s for s, v in vec.items() if s not in sube and v["R"] <= 1.5]
    if len(sube) == 1 and len(otra) == 1:
        return "MIXTO (sube " + sube[0] + ")"
    return "NO CONCLUYENTE"


def conteos(sitio, año, per):
    """(disparos, evaluados) de la unión por día, en el orden de días de S28a; día sin cuadros = (0, 0)."""
    t0, nd = DIAS[año]
    idx = {f"{t0 + timedelta(days=d):%Y-%m-%d}": d for d in range(nd)}
    c = np.zeros((nd, 2), float)
    with open(os.path.join(CACHE, f"cuadros_{sitio}_{año}.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            assert r["dia"] <= "2026-11-24" and r["ev_u"] == "1", r
            s = int(r["hora"][:2]) * 6 + int(r["hora"][3:5]) // 10
            if s in RANGO[per]:
                c[idx[r["dia"]], 1] += 1
                c[idx[r["dia"]], 0] += r["F_u"] == "1"
    return c


def main():
    ns = funciones_de_s28a()
    print("constantes de s28a_medir.py:", {k: ns[k] for k in ("N_BOOT", "SEMILLA", "MIN_EVAL", "R_SOSTIENE")})
    res = json.load(open(RESULTADO, encoding="utf-8"))
    out = {"A_B": {}, "C": {}, "D": {}}
    print("\nA y B. Rótulo por la regla, con las cifras del JSON")
    for per in ("noche", "dia"):
        vec = {s: res["vecinas"][s]["principal"][per]["union"] for s in ("antuco", "longavi")}
        r_ch = res["chillan"][per]["todos"]["R"]
        a, b = ns["veredicto"](vec, r_ch), regla_del_criterio(vec, r_ch)
        out["A_B"][per] = {"funcion_de_s28a": a, "regla_releida": b, "json": res["veredicto"][per], "R_chillan": r_ch,
                           "vecinas": {s: [v["R"], v["IC95"], v["2025"], v["2026"]] for s, v in vec.items()}}
        print(f"  {per}: función de S28a = {a} | regla releída = {b} | JSON = {res['veredicto'][per]} | "
              f"R Chillán {r_ch}")
        for s, v in vec.items():
            print(f"     {s}: R {v['R']} IC {v['IC95']} 2025 {v['2025']} 2026 {v['2026']}")

    print("\nC. Las cifras del JSON contra el caché de cuadros (misma función `razon`, semilla 0)")
    cc = {}
    for s in ("antuco", "longavi"):
        for per in ("noche", "dia"):
            cc[s, per] = (conteos(s, "2025", per), conteos(s, "2026", per))
            mio = ns["razon"](*cc[s, per])
            suyo = res["vecinas"][s]["principal"][per]["union"]
            igual = all(mio[k] == suyo[k] for k in ("2025", "2026", "R", "IC95"))
            out["C"][f"{s}_{per}"] = {"recalculado": mio, "igual_al_json": igual}
            print(f"  {s} {per}: {mio['2025']} {mio['2026']} R {mio['R']} IC {mio['IC95']} | igual al JSON: {igual}")
    vec = {s: ns["razon"](*cc[s, "dia"]) for s in ("antuco", "longavi")}
    print("  rótulo de día con lo recalculado:", ns["veredicto"](vec, res["chillan"]["dia"]["todos"]["R"]))

    print("\nD. Firmeza del rótulo de día (lectura del verificador, fuera del criterio)")
    c25, c26 = cc["antuco", "dia"]
    los = np.array([ns["razon"](c25, c26, semilla=k)["IC95"][0] for k in range(200)])
    out["D"]["antuco_dia_200_semillas"] = {"lim_inf_min": float(los.min()), "lim_inf_mediana": float(np.median(los)),
                                           "lim_inf_max": float(los.max()), "fraccion_sobre_1": float((los > 1).mean())}
    print(f"  Antuco de día, límite inferior con semillas 0 a 199: mín {los.min():.3f}, mediana {np.median(los):.3f}, "
          f"máx {los.max():.3f}; sobre 1 en {(los > 1).sum()} de 200")
    r_ch = res["chillan"]["dia"]["todos"]["R"]
    for nombre, quita in (("sin el día de más disparos de 2026", ("2026", 1)),
                          ("sin el día de más disparos de 2025", ("2025", 0)),
                          ("sin el día de más disparos de cada año", None)):
        a, b = c25.copy(), c26.copy()
        dias = {}
        for año, arr in (("2025", a), ("2026", b)):
            if quita is None or quita[0] == año:
                d = int(arr[:, 0].argmax())
                dias[año] = f"{DIAS[año][0] + timedelta(days=d):%Y-%m-%d} ({int(arr[d, 0])} de {int(arr[d, 1])})"
        if quita is None or quita[0] == "2025":
            a = np.delete(a, int(a[:, 0].argmax()), 0)
        if quita is None or quita[0] == "2026":
            b = np.delete(b, int(b[:, 0].argmax()), 0)
        v = {"antuco": ns["razon"](a, b), "longavi": ns["razon"](*cc["longavi", "dia"])}
        rot = ns["veredicto"](v, r_ch)
        out["D"][nombre] = {"dias_quitados": dias, "antuco": v["antuco"], "rotulo": rot}
        print(f"  Antuco {nombre} {dias}: {v['antuco']['2025']} {v['antuco']['2026']} R {v['antuco']['R']} "
              f"IC {v['antuco']['IC95']} -> {rot}")
    os.makedirs(SAL, exist_ok=True)
    json.dump(out, open(os.path.join(SAL, "v101_rotulo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
