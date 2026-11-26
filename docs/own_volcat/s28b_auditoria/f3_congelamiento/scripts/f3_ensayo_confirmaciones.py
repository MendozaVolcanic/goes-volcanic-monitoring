r"""F3 (S28b): ensayo en seco de las tres confirmaciones congeladas sobre días YA MIRADOS (07 a 11-11-2026), sin tocar
días nuevos ni escribir fuera de D:\goes_notas\s28\s28b\f3\.

Por qué: la medida de S23b, S25a y S26a se corre una sola vez. Si su código no corre de punta a punta, o si sobre días
ya medidos no reproduce lo que el desarrollo dio con la misma regla, el día de la medida no hay vuelta. Aquí se importan
los módulos originales (sin copiarlos ni editarlos) y se les cambian, en memoria, sólo las rutas de entrada y de salida:
- s23b_confirmar.TRAB -> D:\goes_notas\s17\h23 (npz L1b y ACMF de H23, 01 a 21-11, ya mirados);
- s23b_confirmar.ARRANQUE -> 07-11-2026 (día de arranque), clases de VOLCAT de frames_calor.csv del 08 al 11-11;
- s23_medir.RES, s26a_medir.RES y RES_S25A -> D:\goes_notas\s28\s28b\f3\seco\ (nada se escribe en el repo).
El estado congelado estat_2026.npy se LEE del original (no se copia ni se toca), salvo en `mutacion`, que usa una copia.

Uso: python -I f3_ensayo_confirmaciones.py s23b | s25a | s26a | estat | mutacion
"""
import csv
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
OUT = r"D:\goes_notas\s28\s28b\f3\seco"
TRAB_VISTO = r"D:\goes_notas\s17\h23"
ARR = datetime(2026, 11, 7)
DIAS = ["2026-11-08", "2026-11-09", "2026-11-10", "2026-11-11"]
CORTE = datetime(2026, 11, 25)
CLASES_VISTAS = os.path.join(OUT, "clases_08a11nov.csv")
ESTAT_ORIG = r"D:\goes_notas\s23\s23b\estat_2026.npy"

sys.path.insert(0, os.path.join(OV, "s23_fondo_2025", "scripts"))
sys.path.insert(0, os.path.join(OV, "s26a_combinado", "scripts"))


def preparar():
    os.makedirs(OUT, exist_ok=True)
    src = os.path.join(OV, "calor_rayos", "resultados", "frames_calor.csv")
    n = 0
    with open(src, encoding="utf-8") as f, open(CLASES_VISTAS, "w", encoding="utf-8", newline="") as g:
        w = csv.writer(g)
        w.writerow(["dt", "clase"])
        for r in csv.DictReader(f):
            if r["dt"][:10] in DIAS:
                w.writerow([r["dt"][:16], r["clase"]])
                n += 1
    # guardas: nada de días nuevos
    with open(CLASES_VISTAS, encoding="utf-8") as f:
        fechas = {datetime.strptime(r["dt"][:10], "%Y-%m-%d") for r in csv.DictReader(f)}
    assert max(fechas) < CORTE, "clases con día nuevo"
    return n


def parchar():
    import s23b_confirmar as SB
    S = SB.S
    SB.TRAB = TRAB_VISTO
    SB.ARRANQUE = ARR
    SB.CLASES = CLASES_VISTAS
    S.RES = OUT
    assert SB.ESTAT == ESTAT_ORIG
    return SB, S


def s23b():
    n = preparar()
    SB, S = parchar()
    print("clases vistas:", n, "cuadros; TRAB", SB.TRAB, "ARRANQUE", SB.ARRANQUE, flush=True)
    SB.medir(vistazo=True)
    got = json.load(open(os.path.join(OUT, "s23b_vistazo.json"), encoding="utf-8"))
    ref = json.load(open(os.path.join(OV, "s23_fondo_2025", "resultados", "sensibilidad_costumbre_2026.json"),
                         encoding="utf-8"))
    rd = {x["dia"]: x for x in ref["por_dia"]}
    comp = []
    for x in got["por_dia"]:
        r = rd.get(x["dia"])
        comp.append({"dia": x["dia"], "confirmador": [x["P"], x["P_evaluados"], x["P_alcanzados"], x["disparos"],
                                                      x["tajadas"]],
                     "desarrollo": None if r is None else [r["P"], r["P_evaluados"], r["P_alcanzados"],
                                                           r["disparos_del_dia"], r["tajadas"]]})
    json.dump(comp, open(os.path.join(OUT, "s23b_comparacion.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    print(json.dumps(comp, ensure_ascii=False))


def s26a(s25a):
    preparar()
    SB, S = parchar()
    import s26a_medir as U
    U.RES = OUT
    U.RES_S25A = os.path.join(OUT, "s25a_confirmacion.json")
    shutil.copy2(os.path.join(OV, "s26a_combinado", "resultados", "s26a_seco.json"), os.path.join(OUT, "s26a_seco.json"))
    U.confirmar(vistazo=True, s25a=s25a)
    if s25a:
        got = json.load(open(os.path.join(OUT, "s25a_confirmacion_vistazo.json"), encoding="utf-8"))
        ref = json.load(open(os.path.join(OV, "s25a_crater", "resultados", "s25a_resultado.json"), encoding="utf-8"))
        rd = {x["dia"]: [x["P"], x["P_evaluados"], x["P_alcanzados"], x["disparos"]] for x in ref["por_dia"]}
        comp = [{"dia": x["dia"], "confirmador": [x["P"], x["z"]["P_evaluados"], x["z"]["P_alcanzados"],
                                                  x["z"]["disparos"]], "desarrollo": rd.get(x["dia"])}
                for x in got["por_dia"]]
        nombre = "s25a_comparacion.json"
    else:
        got = json.load(open(os.path.join(OUT, "s26a_confirmacion_vistazo.json"), encoding="utf-8"))
        ref = json.load(open(os.path.join(OV, "s26a_combinado", "resultados", "s26a_desarrollo.json"),
                             encoding="utf-8"))
        rd = {x["dia"]: x for x in ref["por_dia"]}
        comp = []
        for x in got["por_dia"]:
            r = rd.get(x["dia"])
            comp.append({"dia": x["dia"],
                         "confirmador": {k: x[k] for k in ("a", "z", "u")},
                         "desarrollo": None if r is None else {k: r[n] for k, n in (("a", "anillo"), ("z", "zona"),
                                                                                    ("u", "union"))}})
        nombre = "s26a_comparacion.json"
    json.dump(comp, open(os.path.join(OUT, nombre), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(comp, ensure_ascii=False))


def estat():
    """¿El congelado es el nublado de costumbre de S22b (cuadros N despejados por E1, 21-09 a 21-11-2026)?"""
    import s23_medir as S
    e = np.load(ESTAT_ORIG)
    D26 = S.Detector(ref="2026N", con_blanco=False)
    igual = bool(np.array_equal(D26.ESTAT, e))
    out = {"igual": igual, "dif_pixeles_hora": int((D26.ESTAT != e).sum()), "suma_recalculado": int(D26.ESTAT.sum()),
           "suma_congelado": int(e.sum()), "sha_tobytes_recalculado": hashlib.sha256(D26.ESTAT.tobytes()).hexdigest(),
           "sha_tobytes_congelado": hashlib.sha256(e.tobytes()).hexdigest(),
           "n_costumbre_min_max": [int(D26.n_costumbre.min()), int(D26.n_costumbre.max())]}
    json.dump(out, open(os.path.join(OUT, "estat_recalculo.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(out, indent=1))


def mutacion():
    """Línea base roja F3 (1): la guarda de s23b_confirmar.medir tiene que fallar POR ASERCIÓN con un byte cambiado."""
    preparar()
    SB, S = parchar()
    os.makedirs(r"D:\goes_notas\s28\s28b\f3", exist_ok=True)
    copia = r"D:\goes_notas\s28\s28b\f3\estat_2026_mutado.npy"
    shutil.copy2(ESTAT_ORIG, copia)
    b = bytearray(open(copia, "rb").read())
    i = 128 + 5000                        # un byte de datos (cabecera de 128 bytes)
    antes = b[i]
    b[i] = 1 - antes                      # bool: 0 <-> 1
    open(copia, "wb").write(bytes(b))
    res = {"byte": i, "antes": antes, "despues": b[i],
           "sha_tobytes_copia": hashlib.sha256(np.load(copia).tobytes()).hexdigest()[:16]}

    class LlegoAlCubo(Exception):
        """La línea siguiente a la guarda es _cubo(dias): si se llega, la guarda pasó."""

    def _cubo_corta(dias):
        raise LlegoAlCubo()

    cubo_real = SB._cubo
    SB._cubo = _cubo_corta                # medir corre hasta la guarda y se corta en la línea siguiente
    for nombre, ruta in (("mutado", copia), ("original", ESTAT_ORIG)):
        SB.ESTAT = ruta
        try:
            SB.medir(vistazo=True)
            res[nombre] = "SIN EXCEPCIÓN (no debería: _cubo está cortado)"
        except LlegoAlCubo:
            res[nombre] = "pasa la guarda (llega a _cubo)"
        except AssertionError as e:
            res[nombre] = f"AssertionError: {e}"
        except Exception as e:  # noqa: BLE001
            res[nombre] = f"OTRA EXCEPCIÓN (no cuenta): {e!r}"
    SB.ESTAT = ESTAT_ORIG
    SB._cubo = cubo_real
    json.dump(res, open(r"D:\goes_notas\s28\s28b\f3\mutacion.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


def hueco(cual):
    r"""¿Qué hace medir si a los días con clase de VOLCAT les falta GOES? Copia (sólo días ya vistos) los npz de H23 a
    D:\goes_notas\s28\s28b\f3\hueco_<cual>\ sin algunos días y corre medir como vistazo.
    final: falta el último día (11-11), como si `bajar` hubiera quedado antes que `contar`.
    medio: falta un día del medio (10-11)."""
    preparar()
    SB, S = parchar()
    falta = {"final": "20261111", "medio": "20261110"}[cual]
    dst = rf"D:\goes_notas\s28\s28b\f3\hueco_{cual}"
    for sub in ("l1b", "acm"):
        os.makedirs(os.path.join(dst, sub), exist_ok=True)
        for f in os.listdir(os.path.join(TRAB_VISTO, sub)):
            if f[:8] in ("20261107", "20261108", "20261109", "20261110", "20261111") and f[:8] != falta \
                    and f.endswith(".npz"):
                if not os.path.exists(os.path.join(dst, sub, f)):
                    shutil.copy2(os.path.join(TRAB_VISTO, sub, f), os.path.join(dst, sub, f))
    SB.TRAB = dst
    S.RES = os.path.join(OUT, f"hueco_{cual}")
    os.makedirs(S.RES, exist_ok=True)
    SB.medir(vistazo=True)
    got = json.load(open(os.path.join(S.RES, "s23b_vistazo.json"), encoding="utf-8"))
    print(json.dumps({k: got[k] for k in ("veredicto", "instrumento", "P_total", "dias_con_P", "P_evaluados",
                                          "dias_con_P_evaluado")}, ensure_ascii=False))
    for x in got["por_dia"]:
        print(x["dia"], "P", x["P"], "P_eval", x["P_evaluados"], "P_alc", x["P_alcanzados"], "disparos", x["disparos"])


if __name__ == "__main__":
    c = sys.argv[1]
    {"s23b": s23b, "s25a": lambda: s26a(True), "s26a": lambda: s26a(False), "estat": estat,
     "mutacion": mutacion, "hueco_final": lambda: hueco("final"), "hueco_medio": lambda: hueco("medio")}[c]()
