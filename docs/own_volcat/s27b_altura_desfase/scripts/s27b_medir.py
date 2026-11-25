r"""S27b: altura de la pluma por la rapidez con que un pulso pasa de la zona del cráter (S25a) al anillo (S23b).
Implementa criterio_2026-11-25.md (empujado antes de bajar el viento de los días nuevos y de calcular una altura).

Datos: la tabla por cuadro del detector unión de S26a (D:\goes_notas\s26\s26a\tabla_2026.csv, percentil 4,75), sin
cambiar nada del detector. Por cuadro trae el estadístico y el umbral de la zona (S_z, U_z) y del anillo (S_a, U_a), la
tajada del anillo (k_a) y, cuando el anillo dispara, sus 8 píxeles (cola_a).

Uso: python -I s27b_medir.py pruebas | pares | horas_gfs | medir
  pares      lista pulsos, llegadas y pares (sin viento ni altura): resultados/s27b_pares.json
  horas_gfs  horas GFS que hacen falta (para s22c_viento.py)
  medir      alturas por rapidez y rumbo, veredictos: resultados/s27b_resultado.json
"""
import csv
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s27b_comun as K  # noqa: E402

C22 = K.C22
C29 = C22.C29
TABLA = r"D:\goes_notas\s26\s26a\tabla_2026.csv"
RES = os.path.join(os.path.dirname(AQUI), "resultados")
DIAS = ["2026-10-28", "2026-10-29", "2026-11-08", "2026-11-10", "2026-11-11", "2026-11-14"]   # ya mirados
# ---------- parámetros del criterio (§2) ----------
QUIETO = 2              # cuadros sin exceder antes de un pulso o de una llegada (20 min)
DT_MIN, DT_MAX = 10, 120
DECIDE_DIA, DECIDE_T0 = "2026-11-08", ("11:53", "17:53")    # sombra 14:53 más o menos 3 h
VAAC = {"2026-11-08": "19:30 SFC/FL150 (4,6 km) MOV SE 10KT", "2026-11-14": "17:00 SFC/FL120 (3,7 km) MOV S 15KT"}


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def cargar():
    with open(TABLA, encoding="utf-8") as f:
        r = list(csv.DictReader(f))
    t = [datetime.strptime(x["dia"] + " " + x["hora"], "%Y-%m-%d %H:%M") for x in r]
    assert all((b - a) == timedelta(minutes=10) for a, b in zip(t, t[1:])), "la tabla no es continua"
    Sz, Uz = np.array([_f(x["S_z"]) for x in r]), np.array([_f(x["U_z"]) for x in r])
    Sa, Ua = np.array([_f(x["S_a"]) for x in r]), np.array([_f(x["U_a"]) for x in r])
    return {"t": t, "clase": [x["clase"] for x in r],
            "ez": np.isfinite(Sz) & np.isfinite(Uz), "z": np.isfinite(Sz) & np.isfinite(Uz) & (Sz <= Uz),
            "ea": np.isfinite(Sa) & np.isfinite(Ua), "a": np.isfinite(Sa) & np.isfinite(Ua) & (Sa <= Ua),
            "Fa": np.array([x["F_a"] == "1" for x in r]), "k": np.array([int(x["k_a"]) for x in r]),
            "cola": [[int(c) for c in x["cola_a"].split(";")] if x["cola_a"] else [] for x in r]}


def quieto(ev, ex, i, n=QUIETO):
    """Los n cuadros antes de i están evaluados y sin exceder."""
    return i >= n and all(ev[i - j] and not ex[i - j] for j in range(1, n + 1))


def pulsos(T):
    """Inicio de cada racha de la zona (un cuadro basta: a 5 m/s un pulso sale de 4 km en un cuadro), con 20 min
    previos evaluados y sin exceder."""
    return [i for i in range(len(T["t"])) if T["z"][i] and quieto(T["ez"], T["z"], i)]


def llegadas(T):
    """Primer cuadro con disparo del anillo (F, dos cuadros seguidos) de una racha que empezó en el cuadro anterior,
    con 20 min previos a la racha evaluados y sin exceder. La posición son los 8 píxeles de ese cuadro."""
    out = []
    for i in range(1, len(T["t"])):
        if T["Fa"][i] and T["a"][i - 1] and quieto(T["ea"], T["a"], i - 1) and T["cola"][i]:
            out.append(i)
    return out


def pares(T):
    """Cada llegada con sus pulsos candidatos (criterio §2.4): la racha del anillo empieza DESPUÉS del pulso (si
    empiezan en el mismo cuadro no hay tránsito que medir), Δt hasta el cuadro de la llegada de 20 a 120 min, y un
    pulso sirve sólo para la primera llegada que lo tiene como candidato (un pulso, una llegada)."""
    P = pulsos(T)
    out, usados = [], set()
    for ia in llegadas(T):
        cand = [ip for ip in P if ip < ia - 1 and (ia - ip) * 10 <= DT_MAX and ip not in usados]
        usados |= set(cand)
        out.append({"ia": ia, "cand": cand})
    return P, out


def _hh(T, i):
    return f"{T['t'][i]:%Y-%m-%d %H:%M}"


def lista_pares(T):
    P, pr = pares(T)
    dias = set(DIAS)
    sel = [p for p in pr if f"{T['t'][p['ia']]:%Y-%m-%d}" in dias]
    return [{"llegada": _hh(T, p["ia"]), "tajada": int(T["k"][p["ia"]]), "clase_llegada": T["clase"][p["ia"]],
             "pulsos_candidatos": [_hh(T, i) for i in p["cand"]],
             "dt_min": [(p["ia"] - i) * 10 for i in p["cand"]],
             "tipo": "único" if len(p["cand"]) == 1 else ("sin pulso" if not p["cand"] else "ambiguo")}
            for p in sel], len(P)


def centro(dt):
    return dt + timedelta(minutes=5)          # centro del barrido de 10 min, como S22c


def viento_viaje(T, ip, ia):
    """Viento en el punto medio del viaje (entre los centros de los dos cuadros)."""
    t0, ta = centro(T["t"][ip]), centro(T["t"][ia])
    return C22.viento(t0 + (ta - t0) / 2)


def latlon_cola(T, ia):
    idx = np.array(T["cola"][ia])
    return C29.LAT.ravel()[idx], C29.LON.ravel()[idx]


def avance_en_anillo(T, ia):
    """Informativo (método B): distancia aparente mediana de los 8 píxeles en los cuadros con disparo seguidos desde la
    llegada (hasta 6). Una pluma continua no avanza; un pulso sí."""
    serie = []
    i = ia
    while i < len(T["t"]) and T["Fa"][i] and T["cola"][i] and len(serie) < 6:
        la, lo = latlon_cola(T, i)
        serie.append(round(float(np.median(C22.az_dist(la, lo)[1])), 1))
        i += 1
    if len(serie) >= 3:
        pend = float(np.polyfit(np.arange(len(serie)) * 600.0, np.array(serie) * 1000.0, 1)[0])
    else:
        pend = None
    return {"dist_aparente_km": serie, "rapidez_aparente_ms": None if pend is None else round(pend, 1)}


def medir_par(T, ip, ia):
    vw = viento_viaje(T, ip, ia)
    if vw is None:
        return {"error": "falta viento"}
    la, lo = latlon_cola(T, ia)
    r = K.alturas(la, lo, (ia - ip) * 10, vw)
    r["pulso"] = _hh(T, ip)
    r["perfil_V_cada_km"] = {f"{z:.1f}": round(float(vw[1][i]), 1) for i, z in enumerate(K.ZS)
                             if abs(z - round(z)) < 1e-6 or abs(z - 3.2) < 1e-6}
    r["perfil_hacia_cada_km"] = {f"{z:.1f}": round(float(vw[0][i])) for i, z in enumerate(K.ZS)
                                 if abs(z - round(z)) < 1e-6 or abs(z - 3.2) < 1e-6}
    return r


def horas_gfs():
    T = cargar()
    _, pr = pares(T)
    hs = set()
    for p in pr:
        if f"{T['t'][p['ia']]:%Y-%m-%d}" not in DIAS:
            continue
        for ip in p["cand"]:
            m = centro(T["t"][ip]) + (centro(T["t"][p["ia"]]) - centro(T["t"][ip])) / 2
            h0 = m.replace(minute=0, second=0, microsecond=0)
            hs |= {h0, h0 + timedelta(hours=1)}
    falt = [h for h in sorted(hs) if not os.path.exists(os.path.join(C22.GFS_DIR, f"gfsv_{h:%Y%m%d%H}.npz"))]
    print(" ".join(f"{h:%Y%m%d%H}" for h in falt))


def medir():
    T = cargar()
    P, pr = pares(T)
    out = {"criterio": "criterio_2026-11-25.md", "rotulo": "DESARROLLO: días ya mirados", "llegadas": []}
    for p in pr:
        ia = p["ia"]
        dia = f"{T['t'][ia]:%Y-%m-%d}"
        if dia not in DIAS:
            continue
        s = T["t"][ia].hour * 6 + T["t"][ia].minute // 10
        fila = {"llegada": _hh(T, ia), "tajada": int(T["k"][ia]), "clase_llegada": T["clase"][ia],
                "volcat": C22.volcat_cuadro(dia, s), "avance_en_anillo": avance_en_anillo(T, ia),
                "candidatos": [medir_par(T, ip, ia) for ip in p["cand"]]}
        con = [c for c in fila["candidatos"] if c.get("rapidez_y_rumbo", {}).get("banda") is not None]
        if len(p["cand"]) == 1:
            fila["tipo"], fila["elegido"] = "único", 0
        elif len(p["cand"]) > 1 and len(con) == 1:
            fila["tipo"] = "ambiguo resuelto"
            fila["elegido"] = next(j for j, c in enumerate(fila["candidatos"]) if c is con[0])
        else:
            fila["tipo"] = "sin pulso" if not p["cand"] else "ambiguo"
            fila["elegido"] = None
        if fila["elegido"] is not None:
            c = fila["candidatos"][fila["elegido"]]
            fila["veredicto_caso"] = K.veredicto_caso(c["rapidez_y_rumbo"]) if "rapidez_y_rumbo" in c else "falta viento"
        out["llegadas"].append(fila)
        el = fila["candidatos"][fila["elegido"]] if fila["elegido"] is not None else None
        print(fila["llegada"], fila["tipo"], "k", fila["tajada"],
              "" if el is None else f"pulso {el['pulso']} Δt {el['dt_min']} d {el['d_km_3p2_4p7_10']} "
              f"v(4,7) {el['v_obs_4p7']} rapidez {el['rapidez']['banda']} rumbo {el['rumbo']['banda']} "
              f"ambas {el['rapidez_y_rumbo']['banda']} h* {el['h_estrella']} -> {fila.get('veredicto_caso')}",
              flush=True)
    # prueba que decide (§4)
    dec = [f for f in out["llegadas"] if f["llegada"][:10] == DECIDE_DIA and f["elegido"] is not None
           and DECIDE_T0[0] <= f["candidatos"][f["elegido"]]["pulso"][11:] <= DECIDE_T0[1]]
    amb = [f for f in out["llegadas"] if f["llegada"][:10] == DECIDE_DIA and f["elegido"] is None
           and any(DECIDE_T0[0] <= c["pulso"][11:] <= DECIDE_T0[1] for c in f["candidatos"])]
    if not dec:
        v = "NO DECIDIBLE"
    else:
        vs = [f["veredicto_caso"] for f in dec]
        if "FALLA" in vs and "ACIERTA" not in vs:
            v = "FALLA"
        elif vs.count("ACIERTA") > len(vs) / 2:
            v = "ACIERTA"
        elif "SIN SOLUCIÓN" in vs and all(x in ("SIN SOLUCIÓN",) for x in vs):
            v = "SIN SOLUCIÓN"
        else:
            v = "NO RESTRINGE"
    sep = [f["candidatos"][f["elegido"]]["rapidez_y_rumbo"] for f in dec]
    separa = bool(sep) and all(b["banda"] is not None and b["separa_capas"] and b["toca_sombra"] for b in sep)
    conj = {"ACIERTA": "SIRVE EN UN CASO", "FALLA": "NO SIRVE", "NO DECIDIBLE": "NO DECIDIBLE",
            "SIN SOLUCIÓN": "NO SIRVE"}.get(v, "SÓLO SEPARA CAPAS" if separa else "NO RESTRINGE")
    out["prueba_decide"] = {"dia": DECIDE_DIA, "ventana_t0": DECIDE_T0, "llegadas": [f["llegada"] for f in dec],
                            "ambiguas_sin_resolver": [f["llegada"] for f in amb], "veredicto": v,
                            "separa_capas_y_toca_sombra": separa}
    out["veredicto_conjunto"] = conj
    ev = [f for f in out["llegadas"] if f["elegido"] is not None]
    out["resumen_informativo"] = {
        "llegadas": len(out["llegadas"]), "con_par": len(ev),
        "restringen": sum(f["candidatos"][f["elegido"]]["rapidez_y_rumbo"]["restringe"] for f in ev),
        "separan_capas": sum(bool(f["candidatos"][f["elegido"]]["rapidez_y_rumbo"].get("separa_capas")) for f in ev),
        "tipos": {t: sum(f["tipo"] == t for f in out["llegadas"]) for t in
                  ("único", "ambiguo resuelto", "ambiguo", "sin pulso")},
        "vaac": VAAC}
    print("PRUEBA QUE DECIDE:", json.dumps(out["prueba_decide"], ensure_ascii=False))
    print("VEREDICTO CONJUNTO:", conj)
    print(json.dumps(out["resumen_informativo"], ensure_ascii=False))
    with open(os.path.join(RES, "s27b_resultado.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)


def pruebas():
    K.pruebas()
    t0 = datetime(2026, 11, 8)
    n = 30
    T = {"t": [t0 + timedelta(minutes=10 * i) for i in range(n)], "clase": [""] * n,
         "ez": np.ones(n, bool), "z": np.zeros(n, bool), "ea": np.ones(n, bool), "a": np.zeros(n, bool),
         "Fa": np.zeros(n, bool), "k": np.full(n, 5), "cola": [[] for _ in range(n)]}
    T["z"][[5, 6, 14]] = True           # pulsos: 5 (14 no: 6 frames quietos antes sí -> también pulso)
    T["a"][[11, 12, 13]] = True
    T["Fa"][[12, 13]] = True
    T["cola"][12] = [100] * 8
    T["cola"][13] = [100] * 8
    assert pulsos(T) == [5, 14], pulsos(T)
    assert llegadas(T) == [12], llegadas(T)
    P, pr = pares(T)
    assert pr[0]["cand"] == [5], pr                     # Δt 70 min; 14 queda después
    T["z"][9] = True                                    # otro pulso a 30 min: ambiguo
    P, pr = pares(T)
    assert pr[0]["cand"] == [5, 9], pr
    T["z"][9] = False
    T["z"][11] = True                                   # pulso en el mismo cuadro en que empieza la racha: no cuenta
    P, pr = pares(T)
    assert 11 in P and pr[0]["cand"] == [5], pr
    # segunda llegada: el pulso 5 ya se usó
    T["a"][[20, 21]] = True
    T["Fa"][21] = True
    T["cola"][21] = [100] * 8
    P, pr = pares(T)
    assert [p["ia"] for p in pr] == [12, 21] and pr[1]["cand"] == [11, 14], pr
    T["ez"][3] = False                                  # un cuadro sin evaluar antes del pulso 5 lo anula
    assert 5 not in pulsos(T)
    print("s27b_medir pruebas OK")


if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    if c == "pares":
        T = cargar()
        lp, npul = lista_pares(T)
        for x in lp:
            print(x)
        os.makedirs(RES, exist_ok=True)
        json.dump({"nota": "sin viento ni altura; sólo la tabla de disparos de S26a", "pulsos_totales_tabla": npul,
                   "llegadas_dias_mirados": lp}, open(os.path.join(RES, "s27b_pares.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    elif c in ("pruebas", "horas_gfs", "medir"):
        {"pruebas": pruebas, "horas_gfs": horas_gfs, "medir": medir}[c]()
    else:
        print(__doc__)
