r"""S30a: ensayo de punta a punta del envoltorio s30a_confirmar.py con días YA VISTOS, y mutaciones que deben hacerlo
fallar. Ningún día posterior al 24-11-2026 (aserción en s30a_confirmar.medir).

Haciendo de cuenta: arranque 07-11-2026 y días "nuevos" 08 a 14-11, con las clases reales de VOLCAT SÓLO del 08-11 (13 P)
y del 14-11 (33 P); los días 09 a 13 entran al cubo sin clases. L1b y ACMF por cuadro de la bajada de H23
(D:\goes_notas\s17\h23), enlazados (no copiados) en D:\goes_notas\s30\s30a\ensayo\.

Escenarios (cuenta como atrapada sólo una mutación que falla por AssertionError con el mensaje esperado):
  control       sin mutación: tiene que llegar al final y reproducir, día por día, el desarrollo publicado de las tres
                reglas (anillo a percentil 5, zona a 5, unión a p*).
  repetida      volver a medir en la misma carpeta después del control           -> "ya hay una medida iniciada"
  resultado     un s23b_resultado.json ya existe (sin registro)                     -> "ya existe un resultado"
  vistazo       un vistazo previo hasta el 14-11, sin 2 días con P después          -> "hubo un vistazo"
  sin_acmf      falta toda la ACMF del 08-11 (306)                                   -> "comprobación previa"
  sin_goes_fin  falta todo el L1b del 14-11, el último día (301)                    -> "comprobación previa"
  gatillo       clases sólo del 14-11: 33 P de un solo día (307 y gatillo)          -> "gatillo"
  csv_cambia    el CSV de la medida cambia entre S23b y S25a (302)                   -> "manifiesto distinto después de S23b"
  acm_cambia    un byte de una ACMF del 08-11 cambia entre S23b y S25a (305)        -> "manifiesto distinto después de S23b"

Uso: python -I -B -u s30a_confirmar.py ensayo [escenario ...]   (sin argumentos: todos)
Salida: D:\goes_notas\s30\s30a\ensayo\resumen.json
"""
import csv
import json
import os
import shutil

import traceback
from datetime import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
import s30a_confirmar as C  # noqa: E402

ENS = r"D:\goes_notas\s30\s30a\ensayo"
H23 = r"D:\goes_notas\s17\h23"
DIAS = [f"202611{d:02d}" for d in range(7, 15)]
ARR = datetime(2026, 11, 7)
_memo = {}


def base_trab(nombre, sin=()):
    """Carpeta de cubo para un escenario: enlaces duros a la bajada de H23, menos los (tipo, día) de `sin`."""
    t = os.path.join(ENS, "trab", nombre)
    if os.path.exists(t):
        shutil.rmtree(t)
    for k in ("l1b", "acm"):
        os.makedirs(os.path.join(t, k))
        for f in os.listdir(os.path.join(H23, k)):
            if f[:8] in DIAS and f.endswith(".npz") and ".tmp" not in f and (k, f[:8]) not in sin:
                try:
                    os.link(os.path.join(H23, k, f), os.path.join(t, k, f))
                except OSError:
                    shutil.copyfile(os.path.join(H23, k, f), os.path.join(t, k, f))
    return t


def clases(destino, dias):
    with open(os.path.join(OV, "calor_rayos", "resultados", "frames_calor.csv"), encoding="utf-8") as f:
        filas = [r for r in csv.DictReader(f) if r["dt"][:10] in dias]
    with open(destino, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dt", "clase"])
        for r in filas:
            w.writerow([r["dt"][:16], r["clase"]])
    return len(filas)


def memo(SB, U, S):
    """Construye una vez la referencia de 2025 (S.Detector) y las partes (U.Partes) y las reutiliza entre escenarios:
    son de sólo lectura para los días nuevos (lo mismo que hizo V301 de S28b)."""
    if "Detector" not in _memo:
        _memo["Detector"], _memo["Partes"] = S.Detector, U.Partes

        def Detector(ref="2025", con_blanco=True, estat_blanco=None):
            k = ("D", ref, con_blanco, estat_blanco is None)
            if k not in _memo:
                _memo[k] = _memo["Detector"](ref=ref, con_blanco=con_blanco, estat_blanco=estat_blanco)
            return _memo[k]

        def Partes():
            if "P" not in _memo:
                _memo["P"] = _memo["Partes"]()
            return _memo["P"]
        S.Detector, U.Partes = Detector, Partes
    for k, v in list(_memo.items()):
        if isinstance(k, tuple):
            v._U = {}                                    # umbral recalculado al percentil del paso


def cfg_de(nombre, trab, dias_clases):
    carpeta = os.path.join(ENS, nombre)
    if os.path.exists(carpeta):
        shutil.rmtree(carpeta)
    os.makedirs(carpeta)
    cfg = C.Cfg(ensayo=carpeta, arranque=ARR, trab=trab)
    clases(cfg.clases, dias_clases)
    return cfg


def comparar_con_desarrollo(out):
    """El control tiene que dar, día por día, lo publicado del desarrollo."""
    pub_a = json.load(open(os.path.join(OV, "s23_fondo_2025", "resultados", "sensibilidad_costumbre_2026.json"),
                           encoding="utf-8"))
    pub_z = json.load(open(os.path.join(OV, "s25a_crater", "resultados", "s25a_resultado.json"), encoding="utf-8"))
    pub_u = json.load(open(os.path.join(OV, "s26a_combinado", "resultados", "s26a_desarrollo.json"), encoding="utf-8"))
    filas = []
    for dia in ("2026-11-08", "2026-11-14"):
        m = {k: [x for x in out["reglas"][k]["por_dia"] if x["dia"] == dia][0] for k in ("S23b", "S25a", "S26a")}
        u = [x for x in pub_u["por_dia"] if x["dia"] == dia][0]["union"]
        z = [x for x in pub_z["por_dia"] if x["dia"] == dia][0]
        filas.append({"dia": dia, "S23b": (m["S23b"]["P_evaluados"], m["S23b"]["P_alcanzados"]),
                      "S25a": (m["S25a"]["P_evaluados"], m["S25a"]["P_alcanzados"]),
                      "S26a": (m["S26a"]["P_evaluados"], m["S26a"]["P_alcanzados"]),
                      "pub_zona": (z.get("P_evaluados"), z.get("P_alcanzados")),
                      "pub_union": (u["P_evaluados"], u["P_alcanzados"])})
    return filas, pub_a


def correr(nombre, fn, espera):
    print(f"\n===== {nombre} (espera: {espera or 'terminar sin error'})", flush=True)
    try:
        r = fn()
        if espera:
            return {"escenario": nombre, "resultado": "NO ATRAPADA: terminó sin error", "espera": espera}
        return {"escenario": nombre, "resultado": "TERMINA", "salida": r}
    except AssertionError as e:
        msg = str(e)
        ok = bool(espera) and espera in msg
        print("AssertionError:", msg[:300], flush=True)
        return {"escenario": nombre, "resultado": ("ATRAPADA POR ASERCIÓN" if ok else
                                                   ("FALLA INESPERADA" if not espera else "ASERCIÓN CON OTRO MENSAJE")),
                "mensaje": msg[:500], "espera": espera}
    except BaseException as e:  # noqa: BLE001
        traceback.print_exc()
        return {"escenario": nombre, "resultado": f"NO ATRAPADA: {type(e).__name__}", "mensaje": str(e)[:500],
                "espera": espera}


def main(pedidos):
    os.makedirs(ENS, exist_ok=True)
    todos = ["control", "repetida", "resultado", "vistazo", "sin_acmf", "sin_goes_fin", "gatillo", "csv_cambia",
             "acm_cambia"]
    pedidos = pedidos or todos
    trab0 = base_trab("base")
    dias_ok = {"2026-11-08", "2026-11-14"}
    res = []
    if "control" in pedidos or "repetida" in pedidos:
        cfg = cfg_de("control", trab0, dias_ok)

        def control():
            out = C.medir(cfg, memo=memo)
            filas, _ = comparar_con_desarrollo(out)
            print("control contra desarrollo:", json.dumps(filas, ensure_ascii=False), flush=True)
            for f in filas:
                assert f["S25a"] == tuple(f["pub_zona"]), f"zona no reproduce el desarrollo el {f['dia']}"
                assert f["S26a"] == tuple(f["pub_union"]), f"unión no reproduce el desarrollo el {f['dia']}"
            return {"por_dia_vs_desarrollo": filas,
                    "veredictos": {k: (v["veredicto_enmienda"], v["regla_congelada_ROTULADA"]["veredicto"], v["R"],
                                       {f: (None if x is None else x["p_dia"]) for f, x in v["nulos"].items()})
                                   for k, v in out["reglas"].items()}}
        res.append(correr("control", control, None))
        if "repetida" in pedidos:
            res.append(correr("repetida", lambda: C.medir(cfg, memo=memo), "ya hay una medida iniciada"))
    if "resultado" in pedidos:
        cfg = cfg_de("resultado", trab0, dias_ok)
        C.importar(cfg)
        json.dump({"veredicto": "x"}, open(os.path.join(cfg.res["S"], "s23b_resultado.json"), "w"))
        res.append(correr("resultado", lambda: C.medir(cfg, memo=memo), "ya existe un resultado"))
    if "vistazo" in pedidos:
        cfg = cfg_de("vistazo", trab0, dias_ok)
        C.importar(cfg)
        json.dump({"veredicto": "VISTAZO", "por_dia": [{"dia": "2026-11-14"}]},
                  open(os.path.join(cfg.res["S"], "s23b_vistazo.json"), "w"))
        res.append(correr("vistazo", lambda: C.medir(cfg, memo=memo), "hubo un vistazo"))
    if "sin_acmf" in pedidos:
        cfg = cfg_de("sin_acmf", base_trab("sin_acmf", {("acm", "20261108")}), dias_ok)
        res.append(correr("sin_acmf", lambda: C.medir(cfg, memo=memo), "comprobación previa"))
    if "sin_goes_fin" in pedidos:
        cfg = cfg_de("sin_goes_fin", base_trab("sin_goes_fin", {("l1b", "20261114")}), dias_ok)
        res.append(correr("sin_goes_fin", lambda: C.medir(cfg, memo=memo), "comprobación previa"))
    if "gatillo" in pedidos:
        cfg = cfg_de("gatillo", trab0, {"2026-11-14"})
        res.append(correr("gatillo", lambda: C.medir(cfg, memo=memo), "gatillo"))
    if "csv_cambia" in pedidos:
        cfg = cfg_de("csv_cambia", trab0, dias_ok)

        def mutar_csv(paso, cfg_):
            if paso == "S23b":
                with open(os.path.join(cfg_.medida, "clases_medida.csv"), "a", encoding="utf-8", newline="") as f:
                    csv.writer(f).writerow(["2026-11-09 18:00", "P"])
        res.append(correr("csv_cambia", lambda: C.medir(cfg, entre_pasos=mutar_csv, memo=memo),
                          "manifiesto distinto después de S23b"))
    if "acm_cambia" in pedidos:
        trab = base_trab("acm_cambia")
        cfg = cfg_de("acm_cambia", trab, dias_ok)

        def mutar_acm(paso, cfg_):
            if paso == "S23b":
                f = os.path.join(cfg_.trab, "acm", "20261108_1800.npz")
                b = bytearray(open(f, "rb").read())
                os.remove(f)                             # rompe el enlace duro: la bajada de H23 no se toca
                b[len(b) // 2] ^= 0x01
                open(f, "wb").write(bytes(b))
        res.append(correr("acm_cambia", lambda: C.medir(cfg, entre_pasos=mutar_acm, memo=memo),
                          "manifiesto distinto después de S23b"))
    print("\n===== RESUMEN")
    for r in res:
        print(f"{r['escenario']:14s} {r['resultado']}")
    json.dump(res, open(os.path.join(ENS, "resumen.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              default=str)
    print("escrito", os.path.join(ENS, "resumen.json"))
