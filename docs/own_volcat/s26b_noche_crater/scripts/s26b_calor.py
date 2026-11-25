r"""S26b: serie de calor nocturno de Nevados de Chillán, noche a noche, del 14-09 al 24-11-2026, con la regla validada
TAL CUAL (src/process/vrp_nocturno.py vía scripts/build_calor_nocturno.procesar y src/process/calor_nocturno). Sólo
cuadros de :00 y :30 (la cadencia validada). Las noches 14 a 20-09 sólo dan la referencia de cielo despejado de las
primeras noches del periodo medido (21-09 en adelante).

Guarda D:\goes_notas\s26\s26b\calor_chillan_serie.json (mismo esquema que data/calor_nocturno.json, sólo Chillán).
Reanudable. No escribe en data/ del repo.

Uso: python s26b_calor.py bajar [nproc]   |   python s26b_calor.py noches
(sin -I: necesita importar src/ y scripts/ del repo)
"""
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
import build_calor_nocturno as BC  # noqa: E402
from src.process import calor_nocturno as C  # noqa: E402
from src.process import vrp_nocturno as V  # noqa: E402

TRAB = r"D:\goes_notas\s26\s26b"
SERIE = os.path.join(TRAB, "calor_chillan_serie.json")
NOMBRE = "Nevados de Chillan"
N0, N1 = date(2026, 9, 14), date(2026, 11, 24)


def volcan():
    return [v for v in BC.volcanes_catalogo() if v.name == NOMBRE]


def cuadros():
    v = volcan()[0]
    out, n = [], N0
    while n <= N1:
        for t in C.grilla(C.inicio_noche(n), C.inicio_noche(n) + timedelta(hours=18)):
            if V.es_nocturno(t, v.lat, v.lon) and V.clave_noche(t) == n:
                out.append(t)
        n += timedelta(days=1)
    return out


def _tarea(t):
    vols = volcan()
    return t, BC.procesar(t, vols, BC.sitios_de(vols), BC.leer_s3)


def cargar():
    if os.path.exists(SERIE):
        return json.load(open(SERIE, encoding="utf-8"))
    return {"version": 1, "cadencia_min": 30, "cuadros": {}, "sin_granulo": [], "error": []}


def guardar(s):
    tmp = SERIE + ".tmp"
    json.dump(s, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, SERIE)


def bajar(nproc=6):
    os.makedirs(TRAB, exist_ok=True)
    s = cargar()
    hechos = set(s["cuadros"]) | set(s["sin_granulo"])
    lote = [t for t in cuadros() if t.strftime(C.ISO) not in hechos]
    s["error"] = []
    print(f"cuadros nocturnos {len(cuadros())}, pendientes {len(lote)}", flush=True)
    t0, k = time.time(), 0
    with ProcessPoolExecutor(nproc) as ex:
        fut = [ex.submit(_tarea, t) for t in lote]
        for f in as_completed(fut):
            t, (estado, fila) = f.result()
            iso = t.strftime(C.ISO)
            if estado == "ok":
                s["cuadros"][iso] = fila
            elif estado == "sin_granulo":
                s["sin_granulo"].append(iso)
            else:
                s["error"].append(iso)
            k += 1
            if k % 50 == 0:
                guardar(s)
                print(f"{k}/{len(lote)} en {time.time() - t0:.0f} s", flush=True)
    guardar(s)
    print(f"listo: {len(s['cuadros'])} cuadros, sin gránulo {len(s['sin_granulo'])}, error {len(s['error'])}", flush=True)


def noches():
    """Estado de cada noche con la regla validada (referencia de las 7 noches previas) y VRP por cuadro."""
    s = cargar()
    por = C.cuadros_por_noche(s, NOMBRE)
    out = {}
    n = N0 + timedelta(days=7)
    while n <= N1:
        e = C.evaluar_noche(por, n)
        out[n.isoformat()] = {k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v))
                              for k, v in e.items()}
        out[n.isoformat()]["cuadros"] = {t.strftime(C.ISO): [c.vrp_mw, c.bt14_zona_k]
                                         for t, c in por.get(n, [])}
        n += timedelta(days=1)
    json.dump(out, open(os.path.join(TRAB, "calor_chillan_noches.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0, default=str)
    for k, v in out.items():
        print(k, v.get("estado"), v.get("n_visibles"), v.get("n_sobre_umbral"), v.get("vrp_max_mw", ""))


if __name__ == "__main__":
    if sys.argv[1] == "bajar":
        bajar(int(sys.argv[2]) if len(sys.argv) > 2 else 6)
    else:
        noches()
