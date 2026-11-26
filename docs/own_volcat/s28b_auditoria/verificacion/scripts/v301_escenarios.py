r"""V301: ensayos de las tres confirmaciones (S23b, S25a, S26a) sobre la COPIA apuntada a días ya vistos (08 a 11-11-2026,
arranque 07-11). Ver v301_preparar.py. Nada de esto toca el repo, `D:\goes_notas\s23` ni días posteriores al 24-11.

Corre el código de la copia tal cual (`s23b_confirmar.medir`, `s26a_medir.confirmar`), cambiando entre escenarios sólo
tres rutas de entrada (carpeta del cubo, copia del estat, CSV de clases). Para no rehacer en cada escenario la
referencia de 2025 (4 a 7 min), `S.Detector` y `Partes` se construyen una vez y se reutilizan: son objetos de sólo
lectura para los días nuevos. Antes de cada paso se repone el percentil 5 (en la línea de comandos cada paso es un
proceso aparte y parte en 5; aquí comparten proceso).

Escenarios (todos con las clases reales de VOLCAT de esos días):
  A  base: GOES y ACMF completos, clases 08 a 11-11 (28 P en 3 días).
  B  al último día (11-11) le falta todo el GOES; las clases llegan al 11-11.
  B2 GOES sólo hasta el 09-11; clases 08 a 10-11 (25 P en 2 días: el gatillo se cumple con P del 10-11 sin GOES).
  B3 al 11-11 le falta GOES desde las 12:00 UTC (sus 3 P son de 17:50 a 18:10).
  C  falta el GOES de un día del medio (09-11, que no tiene ningún P).
  D  falta ACMF todo el 08-11 (L1b completo).
  E  "mismos datos": S23b con clases 08 a 10-11 y después S25a y S26a con clases 08 a 11-11.
  G  faltan 6 horas seguidas de L1b el 08-11 (17:00 a 22:50 UTC, donde están sus 13 P): cobertura 684/720 = 0,95.
  F  "una sola vez" y vistazo: vistazo con el gatillo sin cumplir (clases 08 a 09-11), después medir con 08 a 10-11
     (un solo día nuevo más con P), después medir otra vez con 08 a 11-11.

Uso: python -I -B v301_escenarios.py [A B B2 ...]   (sin argumentos: todos)
Salidas: D:\goes_notas\s28\s28b\v301\salidas\<escenario>_<paso>.json y resumen.json
"""
import io
import json
import os
import shutil
import sys
import time
from contextlib import redirect_stdout

sys.stdout.reconfigure(encoding="utf-8")
V = r"D:\goes_notas\s28\s28b\v301"
SAL = os.path.join(V, "salidas")
OVC = os.path.join(V, "repo", "docs", "own_volcat")
os.environ.setdefault("V301_TRAB", os.path.join(V, "trab_base"))
os.environ.setdefault("V301_ARRANQUE", "2026-11-07")
os.environ.setdefault("V301_CLASES", os.path.join(V, "clases_08a11.csv"))
sys.path.insert(0, os.path.join(OVC, "s23_fondo_2025", "scripts"))
sys.path.insert(0, os.path.join(OVC, "s26a_combinado", "scripts"))
import s23b_confirmar as SB  # noqa: E402
import s26a_medir as U  # noqa: E402
S, B = SB.S, SB.S.B
for mod in (SB, U, S, B):
    assert mod.__file__.startswith(V), mod.__file__      # todo lo importado es la copia
assert S.RES.startswith(V) and U.RES.startswith(V) and U.RES_S25A.startswith(V)

_memo = {}
_Detector, _Partes = S.Detector, U.Partes


def Detector(ref="2025", con_blanco=True, estat_blanco=None):
    if estat_blanco is not None:
        return _Detector(ref=ref, con_blanco=con_blanco, estat_blanco=estat_blanco)
    k = (ref, con_blanco)
    if k not in _memo:
        _memo[k] = _Detector(ref=ref, con_blanco=con_blanco)
    return _memo[k]


def Partes():
    if "partes" not in _memo:
        _memo["partes"] = _Partes()
    return _memo["partes"]


S.Detector, U.Partes = Detector, Partes
RESUMEN = {}


def _guardar(nombre, paso, origen, texto):
    info = {"salida_impresa": texto.strip().splitlines()[0][:200] if texto.strip() else ""}
    if os.path.exists(origen) and os.path.getmtime(origen) >= _t0:
        shutil.copyfile(origen, os.path.join(SAL, f"{nombre}_{paso}.json"))
        r = json.load(open(origen, encoding="utf-8"))
        m = r.get("medida", r)
        info.update({"veredicto": r["veredicto"], "instrumento": r["instrumento"], "P_total": r["P_total"],
                     "dias_con_P": r["dias_con_P"], "P_evaluados": m["P_evaluados"], "P_alcanzados": m["P_alcanzados"],
                     "dias_P_evaluado": m.get("dias_con_P_evaluado", m.get("dias_P_evaluado")),
                     "R": m["R"], "p25": m["p25"], "pN": m["pN"],
                     "por_dia": [{k: x[k] for k in x if k in ("dia", "P", "P_evaluados", "P_alcanzados", "a", "z", "u")}
                                 for x in r["por_dia"]]})
    else:
        info["veredicto"] = "(no escribió resultado)"
    RESUMEN[f"{nombre}_{paso}"] = info
    print(f"[{nombre} {paso}] {info.get('veredicto')} | P_total {info.get('P_total')} | evaluados "
          f"{info.get('P_evaluados')} en {info.get('dias_P_evaluado')} d | alcanzados {info.get('P_alcanzados')} | "
          f"inst {info.get('instrumento')} | {info['salida_impresa'] if 'P_total' not in info else ''}", flush=True)
    json.dump(RESUMEN, open(os.path.join(SAL, "resumen.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


_t0 = 0.0


def paso(nombre, cual, trab, clases, vistazo=False):
    """cual: s23b | s25a | s26a. Corre el paso de la copia con esas entradas y guarda una copia de su resultado."""
    global _t0
    SB.TRAB = os.path.join(V, trab)
    SB.ESTAT = os.path.join(SB.TRAB, "estat_2026.npy")
    SB.CLASES = os.path.join(V, clases)
    B.PCT_U = 5.0
    for k in ("2025", ):
        if (k, False) in _memo:
            _memo[(k, False)]._U = {}
    _t0 = time.time() - 1
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            if cual == "s23b":
                SB.medir(vistazo=vistazo)
                origen = os.path.join(S.RES, "s23b_vistazo.json" if vistazo else "s23b_resultado.json")
            elif cual == "s25a":
                U.confirmar(vistazo=vistazo, s25a=True)
                origen = U.RES_S25A.replace(".json", "_vistazo.json") if vistazo else U.RES_S25A
            else:
                U.confirmar(vistazo=vistazo)
                origen = os.path.join(U.RES, "s26a_confirmacion_vistazo.json" if vistazo else "s26a_confirmacion.json")
    except SystemExit as e:
        RESUMEN[f"{nombre}_{cual}"] = {"veredicto": f"sys.exit: {e}"}
        print(f"[{nombre} {cual}] sys.exit: {e}", flush=True)
        return
    except Exception as e:  # noqa: BLE001
        RESUMEN[f"{nombre}_{cual}"] = {"veredicto": f"EXCEPCION {e!r}"[:300]}
        print(f"[{nombre} {cual}] EXCEPCION {e!r}"[:300], flush=True)
        return
    _guardar(nombre, cual + ("_vistazo" if vistazo else ""), origen, buf.getvalue())


def limpiar():
    for f in (os.path.join(S.RES, "s23b_resultado.json"), os.path.join(S.RES, "s23b_vistazo.json"), U.RES_S25A,
              U.RES_S25A.replace(".json", "_vistazo.json"), os.path.join(U.RES, "s26a_confirmacion.json"),
              os.path.join(U.RES, "s26a_confirmacion_vistazo.json")):
        if os.path.exists(f):
            os.remove(f)


def tres(nombre, trab, clases):
    limpiar()
    for cual in ("s23b", "s25a", "s26a"):
        paso(nombre, cual, trab, clases)


ESC = {
    "A": lambda: tres("A", "trab_base", "clases_08a11.csv"),
    "B": lambda: tres("B", "trab_ultimo_sin_goes", "clases_08a11.csv"),
    "B2": lambda: tres("B2", "trab_goes_hasta_0911", "clases_08a10.csv"),
    "B3": lambda: tres("B3", "trab_1111_hasta_mediodia", "clases_08a11.csv"),
    "C": lambda: tres("C", "trab_medio_sin_goes", "clases_08a11.csv"),
    "D": lambda: tres("D", "trab_sin_acm_0811", "clases_08a11.csv"),
}


def esc_E():
    limpiar()
    paso("E", "s23b", "trab_base", "clases_08a10.csv")
    paso("E", "s25a", "trab_base", "clases_08a11.csv")
    paso("E", "s26a", "trab_base", "clases_08a11.csv")


def esc_F():
    limpiar()
    paso("F1_sin_gatillo", "s23b", "trab_base", "clases_08a09.csv")                 # debe negarse
    paso("F2", "s23b", "trab_base", "clases_08a09.csv", vistazo=True)               # vistazo
    paso("F3_medir_tras_vistazo", "s23b", "trab_base", "clases_08a10.csv")          # sólo 1 día nuevo más con P
    f = os.path.join(S.RES, "s23b_resultado.json")
    m1 = os.path.getmtime(f) if os.path.exists(f) else None
    time.sleep(2)
    paso("F4_medir_otra_vez", "s23b", "trab_base", "clases_08a11.csv")              # segunda medida
    m2 = os.path.getmtime(f) if os.path.exists(f) else None
    RESUMEN["F_reescritura"] = {"mtime_primera": m1, "mtime_segunda": m2, "reescrito_sin_aviso": bool(m1 and m2 and m2 > m1),
                                "vistazo_sigue_en_disco": os.path.exists(os.path.join(S.RES, "s23b_vistazo.json"))}
    print("[F] ", RESUMEN["F_reescritura"], flush=True)
    # S25a y S26a con --vistazo saltan la comprobación del orden (falta el resultado de S25a)
    limpiar()
    paso("F5_s26a_sin_previos", "s26a", "trab_base", "clases_08a11.csv")            # debe salir por sys.exit
    paso("F6_s26a_sin_previos", "s26a", "trab_base", "clases_08a11.csv", vistazo=True)


def esc_N():
    """Diagnóstico del pozo de pN en el escenario A: a qué horas hay cuadros N evaluados por el anillo y cuántos quedan
    a ±60 min de un P evaluado. Repite las líneas 147 a 199 de s23b_confirmar.medir (sin veredicto) para poder listar
    horas; el conteo se compara con el JSON del escenario A (N_evaluados y N_cerca_de_P)."""
    import csv
    from datetime import datetime, timedelta
    import numpy as np
    M = SB.M
    SB.TRAB = os.path.join(V, "trab_base")
    SB.ESTAT = os.path.join(SB.TRAB, "estat_2026.npy")
    SB.CLASES = os.path.join(V, "clases_08a11.csv")
    B.PCT_U = 5.0
    filas = list(csv.DictReader(open(SB.CLASES, encoding="utf-8")))
    ult = max(datetime.strptime(x["dt"][:10], "%Y-%m-%d") for x in filas)
    dias = [SB.ARRANQUE + timedelta(days=i) for i in range((ult - SB.ARRANQUE).days + 1)]
    CL = np.full((len(dias), 144), "", object)
    for x in filas:
        CL[(datetime.strptime(x["dt"][:10], "%Y-%m-%d") - SB.ARRANQUE).days, M.slot(x["dt"][11:16])] = x["clase"]
    estat = np.load(SB.ESTAT)
    with redirect_stdout(io.StringIO()):
        bt, acm, m1, inst = SB._cubo(dias)
        D = S.Detector(ref="2025", con_blanco=False)
    D._U = {}
    FD, mm = D._nubes(acm, m1, estat)
    GATE = FD <= B.G_MAX
    B0 = D.base(None)
    Uu, _ = D.umbral(None)
    Sx = np.full(CL.shape, np.nan)
    Kx = np.full(CL.shape, -1, int)
    for d in range(len(dias)):
        for s in range(144):
            if GATE[d, s]:
                Sx[d, s], Kx[d, s], _ = M.estadistico(mm[d, s] - B0[s])
    P, N = [], []
    out = {"por_dia": []}
    for d in range(1, len(dias)):
        F, ev = S.disparos(Sx, Kx, d, Uu)
        for s in np.flatnonzero(ev):
            if CL[d, s] == "P":
                P.append((d, s))
            elif CL[d, s] == "N":
                N.append((d, s))
        cl = CL[d]
        out["por_dia"].append({
            "dia": f"{dias[d]:%Y-%m-%d}",
            "clases_15a24": {c: int(((cl[90:] == c)).sum()) for c in ("P", "N", "otro", "")},
            "N_15a24_con_compuerta": int(((cl[90:] == "N") & GATE[d, 90:]).sum()),
            "N_15a24_con_S_finito": int(((cl[90:] == "N") & np.isfinite(Sx[d, 90:])).sum()),
            "N_15a24_evaluados": int(((cl[90:] == "N") & ev[90:]).sum()),
            "N_evaluados_por_franja_3h": [int(((cl[b * 18:(b + 1) * 18] == "N") & ev[b * 18:(b + 1) * 18]).sum())
                                          for b in range(8)]})
    psl = {s for _, s in P}
    cerca = [(d, s) for d, s in N if any(M.dslot(s, x) <= S.W_AZAR for x in psl)]
    out.update({"P_evaluados": len(P), "N_evaluados": len(N), "N_cerca_de_P": len(cerca),
                "horas_P_evaluados": sorted({M.hhmm(s) for s in psl}),
                "N_cerca": [f"{dias[d]:%m-%d} {M.hhmm(s)}" for d, s in cerca]})
    # r25 del anillo: horas sin azar definido y horas con umbral pero sin azar (p25 saldría NaN)
    _, sl25, al25, _ = S._seco_2025(D)
    r25 = S.azar_por_hora(sl25, al25)
    out["r25_horas_NaN"] = [M.hhmm(s) for s in range(144) if not np.isfinite(r25[s])]
    out["horas_con_umbral_y_r25_NaN"] = [M.hhmm(s) for s in range(144) if Uu[s] is not None and not np.isfinite(r25[s])]
    out["horas_sin_umbral"] = [M.hhmm(s) for s in range(144) if Uu[s] is None]
    json.dump(out, open(os.path.join(SAL, "N_pozo_pN.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False), flush=True)


ESC["E"], ESC["F"], ESC["N"] = esc_E, esc_F, esc_N
# G: faltan 36 cuadros L1b seguidos (08-11 de 17:00 a 22:50 UTC, donde están los 13 P de ese día); 684 de 720 = 0,95
ESC["G"] = lambda: tres("G", "trab_hueco_6h", "clases_08a11.csv")

if __name__ == "__main__":
    os.makedirs(SAL, exist_ok=True)
    if os.path.exists(os.path.join(SAL, "resumen.json")):
        RESUMEN.update(json.load(open(os.path.join(SAL, "resumen.json"), encoding="utf-8")))
    cuales = sys.argv[1:] or list(ESC)
    t = time.time()
    for c in cuales:
        ESC[c]()
        print(f"--- escenario {c} listo a los {time.time() - t:.0f} s", flush=True)
    json.dump(RESUMEN, open(os.path.join(SAL, "resumen.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
