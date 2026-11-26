r"""S30a: envoltorio de la medida única de las tres confirmaciones congeladas (S23b anillo, S25a zona, S26a unión) con la
enmienda `s30a_enmienda/enmienda_2026-11-26.md`. NO modifica ningún script congelado: los importa y, para la medida,
sólo redirige rutas de entrada (atributos de módulo) y registra lo que esos scripts calculan.

Por qué existe (auditoría S28b, INFORME §1a y §4b): la medida congelada tiene cuatro fallas de ejecución que tuercen el
rótulo en silencio (301: un día sin GOES al final pasa; 306: un día sin ACMF pasa; 302: S25a y S26a pueden medir otros
días que S23b; 307: el gatillo cuenta P no evaluables), no se niega a medir dos veces (303) y su p25 por cuadro no tiene
tamaño (201). El envoltorio:
  1. lee las clases de VOLCAT de UNA sola carpeta en D: (983);
  2. antes de medir comprueba la cobertura de L1b C14 y C15 (mismo scan) y ACMF de cada cuadro, día por día (301, 306);
  3. cuenta para el gatillo los P evaluables, no los P (307);
  4. se niega si ya existe un resultado, un vistazo o un registro de medida iniciada (303);
  5. congela una copia del CSV y un manifiesto sha256 de todas las entradas, y lo compara después de S23b y de S25a
     (302, 305): si algo cambió entre las tres, la medida se detiene por aserción;
  6. corre los tres scripts congelados en el orden de S26a §5 y, con lo que ellos calculan, la regla de la enmienda
     (nulo por días, s30a_nulo.py), y deja los dos rótulos lado a lado.

Subcomandos (en este orden en la vida real):
  contar AAAA-MM-DD      = s23b_confirmar.contar, escribiendo el CSV en CLASES_CANON (una sola carpeta). No usa el detector.
  bajar AAAA-MM-DDTHH    = s23b_confirmar.bajar (sin cambio).
  cobertura              comprobación previa y gatillo de P evaluables; no usa el detector, sólo existencia de archivos,
                         scan y la máscara de nubes ACMF.
  medir [--hasta DIA]    la medida única (corta el CSV en DIA si la comprobación previa obliga).
  ensayo                 pruebas de punta a punta con días YA VISTOS (07 a 14-11-2026) y mutaciones que deben fallar.

Lo grande va a D:\goes_notas\s30\. Ningún día posterior al 24-11-2026 se toca en el modo ensayo (aserciones).
"""
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
REPO = os.path.abspath(os.path.join(OV, "..", ".."))
RES30 = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(OV, "s23_fondo_2025", "scripts"))
sys.path.insert(0, os.path.join(OV, "s26a_combinado", "scripts"))
import s30a_nulo as N  # noqa: E402

# ---------- parámetros de la enmienda (enmienda_2026-11-26.md §3 y §5; fijados tras la calibración) ----------
ALFA = None                                   # se escribe tras la calibración (enmienda §5)
REGLAS = {                                    # parte, percentil, R mínimo, fondos que deciden
    "S23b": {"parte": "a", "pct": 5.0, "r_min": 0.40, "deciden": None},
    "S25a": {"parte": "z", "pct": 5.0, "r_min": 0.25, "deciden": None},
    "S26a": {"parte": "u", "pct": 4.75, "r_min": 0.40, "deciden": None},
}
COB_MIN = 0.95                                # cobertura por día de L1b (mismo scan) y de ACMF
MIN_P_GATILLO, MIN_DIAS_GATILLO = 20, 2       # P evaluables, días con P evaluables
FONDO_NPZ = r"D:\goes_notas\s30\s30a\disparos_s30a.npz"
SHA_FONDO = None                              # sha256 del fondo congelado (enmienda §5)
CANON = r"D:\goes_notas\s30\confirmacion"     # la única carpeta de trabajo de la medida real
CLASES_CANON = os.path.join(CANON, "volcat_clases_desde_25nov.csv")
ULTIMO_VISTO = datetime(2026, 11, 24)         # el modo ensayo no puede pasar de aquí
ENTRADAS_FIJAS = [                            # anexo A del informe F3 de S28b (lo que la regla lee sin guarda)
    r"D:\goes_notas\s23\s23b\estat_2026.npy",
    r"D:\goes_notas\s23\s23a\r25_acm.npy", r"D:\goes_notas\s23\s23a\r25_m1.npy", r"D:\goes_notas\s23\s23a\r25_bt11.npy",
    r"D:\goes_notas\s25\s25a\r25_acm.npy", r"D:\goes_notas\s25\s25a\r25_btd.npy", r"D:\goes_notas\s25\s25a\n26_btd.npy",
    r"D:\goes_notas\s22\s22b\dev_acm.npy", r"D:\goes_notas\s22\s22b\dev_bt11.npy", r"D:\goes_notas\s22\s22b\dev_btd.npy",
    r"D:\goes_notas\s22\s22b\dev_co.npy", r"D:\goes_notas\s22\s22b\dev_m1.npy",
    r"D:\goes_notas\s22\s22b\nuevo_acm.npy", r"D:\goes_notas\s22\s22b\nuevo_bt11.npy", r"D:\goes_notas\s22\s22b\nuevo_m1.npy",
    r"D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\latlon.npz",
    r"D:\goes_cache\etapa3_chillan\dem_ventana.npz",
    os.path.join(OV, "s26a_combinado", "resultados", "s26a_seco.json"),
    os.path.join(OV, "calor_rayos", "resultados", "frames_calor.csv"),
    os.path.join(OV, "s22b_pluma_vs_nubes", "resultados", "volcat_clases_22a24nov.csv"),
    os.path.join(OV, "s22b_pluma_vs_nubes", "resultados", "seco.json"),
    FONDO_NPZ,
]
SCRIPTS = [os.path.join(OV, c, "scripts", f) for c, f in (
    ("s23_fondo_2025", "s23b_confirmar.py"), ("s23_fondo_2025", "s23_medir.py"), ("s25a_crater", "s25a_medir.py"),
    ("s26a_combinado", "s26a_medir.py"), ("s22b_pluma_vs_nubes", "s22b_medir.py"),
    ("s22a_detector_sectores", "s22a_medir.py"), ("s30a_enmienda", "s30a_nulo.py"),
    ("s30a_enmienda", "s30a_confirmar.py"))]
# resultados de la medida congelada (cualquiera de ellos, en el checkout o en origin/main, bloquea una medida nueva)
RESULTADOS_CONGELADOS = [("s23_fondo_2025", "s23b_resultado.json"), ("s23_fondo_2025", "s23b_vistazo.json"),
                         ("s25a_crater", "s25a_confirmacion.json"), ("s25a_crater", "s25a_confirmacion_vistazo.json"),
                         ("s26a_combinado", "s26a_confirmacion.json"),
                         ("s26a_combinado", "s26a_confirmacion_vistazo.json"),
                         ("s30a_enmienda", "s30a_confirmacion.json")]


def sha_archivo(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(2**22), b""):
            h.update(b)
    return h.hexdigest()


# ---------- configuración: real o ensayo ----------
class Cfg:
    """Rutas de una medida. Real: las de los scripts congelados más CANON. Ensayo: todo bajo una carpeta de D:."""

    def __init__(self, ensayo=None, arranque=datetime(2026, 11, 24), trab=r"D:\goes_notas\s23\s23b"):
        self.ensayo = ensayo
        self.arranque = arranque
        self.trab = trab
        if ensayo is None:
            self.canon = CANON
            self.clases = CLASES_CANON
            self.res = {"S": None, "U": None}                     # los de los scripts congelados
        else:
            self.canon = ensayo
            self.clases = os.path.join(ensayo, "clases.csv")
            self.res = {"S": os.path.join(ensayo, "res_s23"), "U": os.path.join(ensayo, "res_s26a")}
        self.medida = os.path.join(self.canon, "medida")
        self.registro = os.path.join(self.canon, "MEDIDA_INICIADA.json")


def importar(cfg):
    """Importa los scripts congelados y redirige SÓLO rutas de entrada y de salida (atributos de módulo)."""
    import s23b_confirmar as SB
    import s26a_medir as U
    S = SB.S
    SB.TRAB = cfg.trab
    SB.ARRANQUE = cfg.arranque
    SB.NUEVO0 = cfg.arranque + timedelta(days=1)
    SB.ESTAT = U.ESTAT26                                          # el congelado (su hash lo comprueban los dos scripts)
    SB.CLASES = cfg.clases
    if cfg.ensayo is not None:
        for k in ("S", "U"):
            os.makedirs(cfg.res[k], exist_ok=True)
        S.RES = cfg.res["S"]
        U.RES = cfg.res["U"]
        U.RES_S25A = os.path.join(cfg.res["U"], "s25a_confirmacion.json")
        seco = os.path.join(OV, "s26a_combinado", "resultados", "s26a_seco.json")
        shutil.copyfile(seco, os.path.join(U.RES, "s26a_seco.json"))
    return SB, U, S


def rutas_resultado(SB, U, S):
    return {"S23b": os.path.join(S.RES, "s23b_resultado.json"), "S23b_vistazo": os.path.join(S.RES, "s23b_vistazo.json"),
            "S25a": U.RES_S25A, "S25a_vistazo": U.RES_S25A.replace(".json", "_vistazo.json"),
            "S26a": os.path.join(U.RES, "s26a_confirmacion.json"),
            "S26a_vistazo": os.path.join(U.RES, "s26a_confirmacion_vistazo.json")}


# ---------- clases ----------
def leer_clases(path):
    with open(path, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    assert filas, f"{path} está vacío"
    return filas


def matriz_clases(filas, arranque, hasta=None):
    ult = max(datetime.strptime(x["dt"][:10], "%Y-%m-%d") for x in filas)
    if hasta is not None:
        ult = min(ult, hasta)
    nd = (ult - arranque).days + 1
    CL = np.full((nd, 144), "", object)
    for x in filas:
        d = (datetime.strptime(x["dt"][:10], "%Y-%m-%d") - arranque).days
        if 0 <= d < nd:
            h, m = x["dt"][11:16].split(":")
            CL[d, int(h) * 6 + int(m) // 10] = x["clase"]
    return CL, [arranque + timedelta(days=i) for i in range(nd)]


# ---------- 1. contar desde una sola carpeta ----------
def contar(hasta):
    cfg = Cfg()
    os.makedirs(CANON, exist_ok=True)
    SB, U, S = importar(cfg)
    SB.contar(hasta)
    print("CSV de clases (única copia):", CLASES_CANON, "sha256", sha_archivo(CLASES_CANON)[:16])
    print("Esto cuenta P, no P evaluables: el gatillo de la enmienda lo da `cobertura` después de `bajar`.")


# ---------- 2. comprobación previa y gatillo ----------
def _scan_ok(f, dt):
    with np.load(f) as z:
        s14, s15 = str(z["key14"]).split("_s")[1][:14], str(z["key15"]).split("_s")[1][:14]
    return s14 == s15 and s14[:11] == f"{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}"


def cobertura(cfg, CL, dias):
    """Por día: fracción de cuadros con L1b C14 y C15 del mismo scan y con ACMF; P evaluables (L1b, ACMF y compuerta de
    nubes abierta con la costumbre de 2026 congelada). No lee una sola radiancia: sólo claves de scan y la ACMF."""
    import s26a_medir as U
    B, M = U.B, U.M
    est26 = np.load(U.ESTAT26)
    out = {"dias": [], "falla": [], "P_evaluables": 0, "dias_con_P_evaluables": 0}
    for d, dia in enumerate(dias):
        n_l1b = n_acm = 0
        pe = 0
        for s in range(144):
            dt = dia + timedelta(minutes=10 * s)
            f = os.path.join(cfg.trab, "l1b", f"{dt:%Y%m%d_%H%M}.npz")
            g = os.path.join(cfg.trab, "acm", f"{dt:%Y%m%d_%H%M}.npz")
            ok1 = os.path.exists(f) and _scan_ok(f, dt)
            ok2 = os.path.exists(g)
            n_l1b += ok1
            n_acm += ok2
            if CL[d, s] == "P" and d > 0 and ok1 and ok2:
                with np.load(g) as z:
                    acm = z["acm"].ravel()
                nd = B.dinamica(acm, est26[s])
                pe += bool(nd[M.AP].mean() <= B.G_MAX)
        fila = {"dia": f"{dia:%Y-%m-%d}", "l1b": n_l1b / 144, "acmf": n_acm / 144,
                "P": int((CL[d] == "P").sum()) if d > 0 else 0, "P_evaluables": pe}
        out["dias"].append(fila)
        if fila["l1b"] < COB_MIN or fila["acmf"] < COB_MIN:
            out["falla"].append(fila["dia"])
        out["P_evaluables"] += pe
        out["dias_con_P_evaluables"] += pe > 0
    out["gatillo"] = out["P_evaluables"] >= MIN_P_GATILLO and out["dias_con_P_evaluables"] >= MIN_DIAS_GATILLO
    return out


def cmd_cobertura():
    cfg = Cfg()
    CL, dias = matriz_clases(leer_clases(cfg.clases), cfg.arranque)
    c = cobertura(cfg, CL, dias)
    for f in c["dias"]:
        print(f)
    print("días que no pasan la comprobación previa:", c["falla"] or "ninguno")
    print(f"P evaluables {c['P_evaluables']} en {c['dias_con_P_evaluables']} días;",
          "GATILLO CUMPLIDO" if c["gatillo"] else "todavía no")


# ---------- 3. negativa ----------
def _git_tiene(rel):
    try:
        r = subprocess.run(["git", "-C", REPO, "ls-tree", "-r", "--name-only", "origin/main", "--", rel],
                           capture_output=True, text=True, timeout=60)
        return bool(r.stdout.strip())
    except Exception:  # noqa: BLE001
        return False


def negativa(cfg, SB, U, S, CL, dias):
    """Aserciones: ningún resultado ni registro de medida previo; un vistazo sólo si ya hay 2 días nuevos con P después
    de su último día (criterio S23b §6)."""
    assert not os.path.exists(cfg.registro), f"ya hay una medida iniciada: {cfg.registro}"
    rr = rutas_resultado(SB, U, S)
    for k, p in rr.items():
        if "vistazo" in k:
            continue
        assert not os.path.exists(p), f"ya existe un resultado: {p}"
    if cfg.ensayo is None:
        for carpeta, nombre in RESULTADOS_CONGELADOS:
            p = os.path.join(OV, carpeta, "resultados", nombre)
            if "vistazo" not in nombre:
                assert not os.path.exists(p), f"ya existe un resultado en este checkout: {p}"
                assert not _git_tiene(f"docs/own_volcat/{carpeta}/resultados/{nombre}"), \
                    f"ya existe un resultado en origin/main: {carpeta}/{nombre}"
    for k, p in rr.items():
        if "vistazo" in k and os.path.exists(p):
            v = json.load(open(p, encoding="utf-8"))
            ult = max(x["dia"] for x in v.get("por_dia", [])) if v.get("por_dia") else f"{cfg.arranque:%Y-%m-%d}"
            despues = sum(1 for d, dia in enumerate(dias) if f"{dia:%Y-%m-%d}" > ult and (CL[d] == "P").any())
            assert despues >= 2, (f"hubo un vistazo ({p}, hasta {ult}); el criterio S23b §6 pide 2 días nuevos con P "
                                  f"después de él y hay {despues}")


# ---------- 4. manifiesto ----------
def manifiesto(cfg, csv_medida, dias):
    out = {"csv_medida": sha_archivo(csv_medida)}
    for p in ENTRADAS_FIJAS + SCRIPTS:
        out[p] = sha_archivo(p) if os.path.exists(p) else "NO EXISTE"
    h = hashlib.sha256()
    n = 0
    for dia in dias:
        for s in range(144):
            dt = dia + timedelta(minutes=10 * s)
            for k in ("l1b", "acm"):
                f = os.path.join(cfg.trab, k, f"{dt:%Y%m%d_%H%M}.npz")
                if os.path.exists(f):
                    h.update(f"{k}/{dt:%Y%m%d_%H%M}".encode())
                    h.update(open(f, "rb").read())
                    n += 1
    out["cubo_por_cuadro"] = h.hexdigest()
    out["cubo_archivos"] = n
    return out


def _diferencias(a, b):
    return [k for k in set(a) | set(b) if a.get(k) != b.get(k)]


# ---------- 5. la medida ----------
class Registro:
    """Registra, sin cambiar nada, lo que calculan los scripts congelados: res de s26a_medir.confirmar (vía lista) y el
    seco de 2025 que alimenta su azar (vía azar)."""

    def __init__(self, U):
        self.U = U
        self.lista0, self.azar0 = U.lista, U.azar
        self.res, self.seco = [], []
        U.lista = self._lista
        U.azar = self._azar

    def _lista(self, res, CL, parte, dias=None):
        self.res.append({"res": res, "CL": CL, "parte": parte, "dias": dias, "pct": self.U.B.PCT_U})
        return self.lista0(res, CL, parte, dias)

    def _azar(self, dias):
        self.seco.append({"dias": dias, "pct": self.U.B.PCT_U})
        return self.azar0(dias)

    def soltar(self):
        self.U.lista, self.U.azar = self.lista0, self.azar0


def medida_enmienda(nombre, res, CL, nuevos, fondo, sinP, alfa, regla):
    """La regla de la enmienda para una confirmación, con F y evaluado de los días nuevos tal como los calculó el script
    congelado. Devuelve el bloque de resultado."""
    k, p = regla["parte"], regla["pct"]
    F = np.array([res[d][k][0] for d in nuevos])
    EV = np.array([res[d][k][1] for d in nuevos])
    AL = np.array([N.alcanzado_dia(F[i], EV[i]) for i in range(len(nuevos))])
    Pm = np.array([CL[d] == "P" for d in nuevos])
    con_P = [i for i in range(len(nuevos)) if Pm[i].any()]
    e_obs = np.array([int((Pm[i] & EV[i]).sum()) for i in con_P])
    a_obs = np.array([int((Pm[i] & EV[i] & AL[i]).sum()) for i in con_P])
    masc = Pm[con_P]
    out = {"P": int(Pm.sum()), "P_evaluados": int(e_obs.sum()), "P_alcanzados": int(a_obs.sum()),
           "R": float(a_obs.sum() / e_obs.sum()) if e_obs.sum() else None, "dias_con_P": len(con_P),
           "dias_con_P_evaluado": int((e_obs > 0).sum()), "nulos": {}}
    fondos = {"2025": (fondo[f"E25_{k}_{p}"], fondo[f"F25_{k}_{p}"], None),
              "2026 sin VOLCAT": (fondo[f"E26_{k}_{p}"], fondo[f"F26_{k}_{p}"], sinP),
              "2024": (fondo[f"E24_{k}_{p}"], fondo[f"F24_{k}_{p}"], None)}
    for nomf, (E, Ff, pool) in fondos.items():
        if not N.decidible(e_obs):
            out["nulos"][nomf] = None
            continue
        ALf = np.array([N.alcanzado_dia(Ff[d], E[d]) for d in range(len(E))])
        ef, af = N.tabla_fondo(masc, E, ALf)
        pool = np.arange(len(E)) if pool is None else np.asarray(pool)
        pv, R, nv, ng, ntot = N.p_dia(e_obs, a_obs, ef, af, pool)
        out["nulos"][nomf] = {"p_dia": pv, "colocaciones_validas": nv, "con_R_mayor_o_igual": ng,
                              "colocaciones_posibles": ntot, "piso": 1 / (1 + nv),
                              "decide": nomf in regla["deciden"]}
    # rótulo (enmienda §3): con más de un fondo que decide, el p es el mayor y la resolución la del más pobre
    if not N.decidible(e_obs):
        ver = "NO DECIDIBLE"
    else:
        ps = [out["nulos"][f]["p_dia"] for f in regla["deciden"]]
        nvs = [out["nulos"][f]["colocaciones_validas"] for f in regla["deciden"]]
        ver = N.veredicto(e_obs, a_obs, max(ps), min(nvs), alfa, regla["r_min"])
    out["veredicto_enmienda"] = ver
    # pN estratificado por día (informativo)
    CLN = np.array([CL[d] == "N" for d in nuevos])
    out["pN_estratificado_informativo"] = N.mantel_haenszel(N.tablas_mh(Pm, EV, AL, CLN))
    out["por_dia"] = [{"dia_indice": int(nuevos[i]), "P": int(Pm[i].sum()), "P_evaluados": int((Pm[i] & EV[i]).sum()),
                       "P_alcanzados": int((Pm[i] & EV[i] & AL[i]).sum()), "disparos": int(F[i].sum())}
                      for i in range(len(nuevos))]
    return out


def medir(cfg, hasta=None, entre_pasos=None, memo=None):
    assert ALFA is not None and SHA_FONDO is not None and all(r["deciden"] for r in REGLAS.values()), \
        "la enmienda todavía no fija alfa, el fondo y los nulos que deciden (calibración)"
    t0 = time.time()
    SB, U, S = importar(cfg)
    filas = leer_clases(cfg.clases)
    CL, dias = matriz_clases(filas, cfg.arranque, hasta)
    if cfg.ensayo is not None:
        assert dias[-1] <= ULTIMO_VISTO, "el ensayo sólo usa días ya vistos (hasta el 24-11-2026)"
    negativa(cfg, SB, U, S, CL, dias)
    # comprobación previa (301, 306) y gatillo de P evaluables (307)
    cob = cobertura(cfg, CL, dias)
    assert not cob["falla"], (f"comprobación previa: los días {cob['falla']} no tienen L1b y ACMF >= {COB_MIN}; "
                              "bajar de nuevo o medir con --hasta el día anterior (enmienda §6)")
    assert cob["gatillo"], (f"gatillo: {cob['P_evaluables']} P evaluables en {cob['dias_con_P_evaluables']} días; "
                            f"hacen falta {MIN_P_GATILLO} en {MIN_DIAS_GATILLO}")
    assert sha_archivo(FONDO_NPZ) == SHA_FONDO, "el fondo del nulo no es el congelado"
    # copia congelada del CSV: los tres scripts leen ESTE archivo (302)
    os.makedirs(cfg.medida, exist_ok=True)
    csv_medida = os.path.join(cfg.medida, "clases_medida.csv")
    with open(csv_medida, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        for x in filas:
            if x["dt"][:10] <= f"{dias[-1]:%Y-%m-%d}":
                w.writerow(x)
    SB.CLASES = csv_medida
    man0 = manifiesto(cfg, csv_medida, dias)
    with open(cfg.registro, "x", encoding="utf-8") as f:          # 'x': falla si otra medida ya lo escribió
        json.dump({"inicio_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                   "dias": [f"{d:%Y-%m-%d}" for d in dias], "cobertura": cob, "manifiesto": man0}, f, indent=1)
    reg = Registro(U)
    try:
        if memo is not None:
            memo(SB, U, S)
        U.B.PCT_U = 5.0
        SB.medir()                                                 # 1. S23b, congelado
        if entre_pasos:
            entre_pasos("S23b", cfg)
        assert not _diferencias(man0, manifiesto(cfg, csv_medida, dias)), \
            f"manifiesto distinto después de S23b: {_diferencias(man0, manifiesto(cfg, csv_medida, dias))}"
        U.confirmar(s25a=True)                                     # 2. S25a, congelado
        if entre_pasos:
            entre_pasos("S25a", cfg)
        assert not _diferencias(man0, manifiesto(cfg, csv_medida, dias)), \
            f"manifiesto distinto después de S25a: {_diferencias(man0, manifiesto(cfg, csv_medida, dias))}"
        U.confirmar()                                              # 3. S26a, congelado
        assert not _diferencias(man0, manifiesto(cfg, csv_medida, dias)), "manifiesto distinto después de S26a"
    finally:
        reg.soltar()
    rr = rutas_resultado(SB, U, S)
    cong = {k: json.load(open(rr[k], encoding="utf-8")) for k in ("S23b", "S25a", "S26a")}
    assert len(reg.res) == 2, f"se esperaban 2 llamadas a lista (S25a y S26a), hubo {len(reg.res)}"
    r25a, r26a = reg.res
    assert r25a["parte"] == "z" and r25a["pct"] == 5.0 and r26a["parte"] == "u"
    nuevos = list(range(1, len(dias)))
    fondo = np.load(FONDO_NPZ)
    # lo que los congelados recalcularon de 2025 tiene que ser el fondo congelado del nulo
    for s_, (k, p) in zip(reg.seco, (("z", 5.0), ("u", r26a["pct"]))):
        assert s_["pct"] == p
        assert np.array_equal(np.array([F for F, _ in s_["dias"]]), fondo[f"F25_{k}_{p}"]), f"fondo 2025 {k} {p}"
        assert np.array_equal(np.array([e for _, e in s_["dias"]]), fondo[f"E25_{k}_{p}"]), f"fondo 2025 {k} {p}"
    assert r26a["pct"] == REGLAS["S26a"]["pct"], "p* de la unión no es el congelado"
    # el anillo de la corrida de S25a (percentil 5) tiene que ser el de S23b, día por día
    for fila in cong["S23b"]["por_dia"]:
        d = [i for i, x in enumerate(dias) if f"{x:%Y-%m-%d}" == fila["dia"]][0]
        F, ev = r25a["res"][d]["a"]
        Ps = np.flatnonzero(CL[d] == "P")
        pe = [bool(ev[s] and F[max(0, s - 1):min(144, s + 2)].any()) for s in Ps if ev[s]]
        assert (len(pe), sum(pe), int(F.sum())) == (fila["P_evaluados"], fila["P_alcanzados"], fila["disparos"]), \
            f"el anillo de S25a no es el de S23b el {fila['dia']}"
    CLf = r25a["CL"]
    assert np.array_equal(np.asarray(CLf, dtype="U4"), np.asarray(CL, dtype="U4")), "S25a midió otras clases"
    assert np.array_equal(np.asarray(r26a["CL"], dtype="U4"), np.asarray(CL, dtype="U4")), "S26a midió otras clases"
    CL26 = fondo["CL"]
    sinP = [d for d in range(len(CL26)) if not (CL26[d] == "P").any()]
    out = {"enmienda": "s30a_enmienda/enmienda_2026-11-26.md", "alfa": ALFA, "dias": [f"{d:%Y-%m-%d}" for d in dias],
           "arranque_sin_contar": f"{dias[0]:%Y-%m-%d}", "cobertura": cob, "manifiesto_sha_csv": man0["csv_medida"],
           "reglas": {}}
    fuente = {"S23b": r25a["res"], "S25a": r25a["res"], "S26a": r26a["res"]}
    for nom, regla in REGLAS.items():
        b = medida_enmienda(nom, fuente[nom], CL, nuevos, fondo, sinP, ALFA, regla)
        for x in b["por_dia"]:
            x["dia"] = f"{dias[x.pop('dia_indice')]:%Y-%m-%d}"
        cg = cong[nom]
        b["regla_congelada_ROTULADA"] = {"veredicto": cg["veredicto"],
                                         "nota": "regla congelada de 25-11 (p25 por cuadro): sin tamaño nominal "
                                                 "(S28b 201, 961, 962); se informa, no decide"}
        out["reglas"][nom] = b
    out["titular"] = f"S26a (unión): {out['reglas']['S26a']['veredicto_enmienda']}"
    out["segundos"] = round(time.time() - t0)
    destino = os.path.join(cfg.canon, "s30a_confirmacion.json")
    json.dump(out, open(destino, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=int)
    if cfg.ensayo is None:
        os.makedirs(RES30, exist_ok=True)
        shutil.copyfile(destino, os.path.join(RES30, "s30a_confirmacion.json"))
    print(json.dumps({k: (v["veredicto_enmienda"], v["regla_congelada_ROTULADA"]["veredicto"], v["P_evaluados"],
                          v["P_alcanzados"], {f: (None if x is None else round(x["p_dia"], 6))
                                              for f, x in v["nulos"].items()})
                      for k, v in out["reglas"].items()}, ensure_ascii=False, indent=1))
    return out


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "contar":
        contar(sys.argv[2])
    elif c == "bajar":
        SB, _, _ = importar(Cfg())
        SB.bajar(sys.argv[2])
    elif c == "cobertura":
        cmd_cobertura()
    elif c == "medir":
        h = sys.argv[sys.argv.index("--hasta") + 1] if "--hasta" in sys.argv else None
        medir(Cfg(), hasta=datetime.strptime(h, "%Y-%m-%d") if h else None)
    elif c == "ensayo":
        import s30a_ensayo
        s30a_ensayo.main(sys.argv[2:])
    else:
        sys.exit(__doc__)
