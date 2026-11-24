r"""S21e: detector de ceniza anclado al crater, sin saber donde mirar. Implementa criterio_2026-11-24.md (commit
6f51c96) con la enmienda 1 (antes de medir, enmienda_1_antes_de_medir_2026-11-24.md).

Pregunta: la firma de ceniza que GOES-19 deja en el pixel junto al crater de Nevados de Chillan (unos -1 K en
11 - 12 um, S20b) sobrevive a buscarla en todos los pixeles a 12 km del crater, sin saber cual mirar?

Por que asi: un detector operativo no sabe que pixel cubre la pluma. Busca el pixel mas bajo de la zona Z. Ese
minimo es bajo aunque no haya pluma (es el extremo de ~65 pixeles con ruido), asi que el umbral sale de los mismos
minimos en dias sin actividad (placebo), a la misma hora.

Medidas (definiciones sin cambios):
- M1(p, t): BTD (C14 - C15) del pixel menos la mediana de la BTD de los pixeles del mismo cuadro con BT11 a +-0,5 K y
  cota a +-300 m (h29_medir.Medidor.medir), con el control a mas de 15 km del crater y minimo 20 pares.
- B(p, h): mediana de M1(p) en los cuadros despejados por E1 (H24.despejada, 80 %) del pozo 21-09 a 21-10 a +-10 min.
- D = M1 - B; S(t) = minimo de D en Z (>= 80 % de Z con D valido).

Uso: python -I s21e_medir.py pruebas | seco | medir | figura
  seco  : solo dias del pozo y placebo (no calcula M1 ni S en los dias con actividad ni en los positivos).
  medir : positivos, nulo del evento, poder e informativo; exige resultados/seco.json.
"""
import csv
import json
import os
import sys
import warnings
from datetime import datetime, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore", RuntimeWarning)
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
FIG = os.path.join(os.path.dirname(AQUI), "figuras")
sys.path.insert(0, os.path.join(OV, "h24_pulsos_reav", "scripts"))
sys.path.insert(0, os.path.join(OV, "h29_pluma_0811", "scripts"))
import h24_medir as H24  # noqa: E402  (cargar, despejada = E1 de H23, EXCLUIDOS, ventanas de los pulsos)
import h29_medir as M29  # noqa: E402  (Medidor: BT11 y BTD con Planck del archivo; medir = M1)
C29 = M29.C

# ---------- parametros del criterio ----------
T0, NDIAS, NY, NX = H24.T0, H24.NDIAS, H24.NY, H24.NX
CRATER_PX = (42, 46)                 # criterio §1 (el mismo de S20c)
R_Z, R_CTRL = 12.0, 15.0             # km: zona Z y control del pareo
PAR_K, COTA_M, MIN_PAR = 0.5, 300.0, 20
W_BASE = 1                           # +-10 min
MIN_BASE = 3
FRAC_Z = 0.80
W_U, W_U2, MIN_U = 6, 12, 20         # +-60 min, +-120 min, minimo de cuadros
PCT_U = 5.0
FA_MAX, POD_MIN, P_MAX = 0.10, 0.80, 0.05
N_POD, SEMILLA = 200, 0
FIRMAS = {"-0.97": 0.97, "-1.46": 1.46}
VOLCAT_CSV = r"D:\goes_notas\s19\h28\resultados\prueba\eventos_chillan_cuadros.csv"

POZO = list(range(0, 31))            # 21-09 a 21-10
EXCL = {(datetime.strptime(s, "%Y-%m-%d") - T0).days for s in H24.EXCLUIDOS}
PLACEBO_TXT = ["2026-10-23", "2026-10-26", "2026-10-31", "2026-11-01", "2026-11-02", "2026-11-03", "2026-11-04",
               "2026-11-05", "2026-11-09", "2026-11-15", "2026-11-17", "2026-11-19", "2026-11-20", "2026-11-21"]
PLACEBO = [(datetime.strptime(s, "%Y-%m-%d") - T0).days for s in PLACEBO_TXT]
EVENTOS = {"25-10": {"dia": "2026-10-25", "cuadros": ["14:20", "14:30"], "verdad": (43, 44), "firma": -0.97},
           "08-11": {"dia": "2026-11-08", "cuadros": ["14:40", "14:50"], "verdad": (44, 46), "firma": -1.46}}
DIAS_POS = {(datetime.strptime(e["dia"], "%Y-%m-%d") - T0).days for e in EVENTOS.values()}

DIST = C29.DIST
BLOQUE = np.zeros((NY, NX), bool)
BLOQUE[CRATER_PX[0] - 1:CRATER_PX[0] + 2, CRATER_PX[1] - 1:CRATER_PX[1] + 2] = True
ZMASK = (DIST <= R_Z) & ~BLOQUE
ZP = np.flatnonzero(ZMASK.ravel())
NZ = len(ZP)
ZR, ZC = np.divmod(ZP, NX)
CTRL = np.flatnonzero((DIST > R_CTRL).ravel())
ZDEM = C29.ZDEM.ravel()
COTA_OK = np.abs(ZDEM[CTRL][None, :] - ZDEM[ZP][:, None]) <= COTA_M          # (NZ, nC)


def dia_idx(s):
    return (datetime.strptime(s, "%Y-%m-%d") - T0).days


def slot(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 6 + int(m) // 10


def hhmm(s):
    return f"{s // 6:02d}:{s % 6 * 10:02d}"


def fecha(d):
    return f"{T0 + timedelta(days=d):%Y-%m-%d}"


def dslot(a, b):
    """Diferencia de hora del dia en cuadros, circular (la ventana de +-60 min cruza la medianoche)."""
    x = abs(a - b) % 144
    return min(x, 144 - x)


# ---------- M1, linea base, D, S ----------
class Detector:
    def __init__(self, bt11, btd, E1):
        self.bt11, self.btd, self.E1 = bt11, btd, E1
        self.m1 = {}
        self._B = {}
        self._S = {}
        self._U = {}

    def m1_cuadro(self, d, s, btd_px=None):
        """M1 de los pixeles de Z en (d, s). btd_px: dict {pixel plano: BTD} que reemplaza la del pixel (pruebas)."""
        k = (d, s)
        if btd_px is None and k in self.m1:
            return self.m1[k]
        bt, bd = self.bt11[d, s], self.btd[d, s]
        btc = bt[CTRL].astype("float64")
        bdc = bd[CTRL]
        okc = np.isfinite(btc) & np.isfinite(bdc)
        out = np.full(NZ, np.nan)
        for i, p in enumerate(ZP):
            b11 = float(bt[p])
            bdd = float(bd[p]) if (btd_px is None or p not in btd_px) else float(btd_px[p])
            if not (np.isfinite(b11) and np.isfinite(bdd)):
                continue
            sel = okc & COTA_OK[i] & (np.abs(btc - b11) <= PAR_K)
            if sel.sum() >= MIN_PAR:
                out[i] = bdd - float(np.median(bdc[sel]))
        if btd_px is None:
            self.m1[k] = out
        return out

    def base(self, s):
        """B(p, h): mediana de M1 en los cuadros del pozo despejados por E1 a +-10 min; >= 3 cuadros con dato."""
        if s not in self._B:
            v = []
            for d in POZO:
                for ss in range(s - W_BASE, s + W_BASE + 1):
                    if 0 <= ss < 144 and self.E1[d, ss]:
                        v.append(self.m1_cuadro(d, ss))
            if not v:
                b, n = np.full(NZ, np.nan), np.zeros(NZ, int)
            else:
                v = np.array(v)
                n = np.isfinite(v).sum(0)
                b = np.nanmedian(v, 0)
                b[n < MIN_BASE] = np.nan
            self._B[s] = (b, n, len(v))
        return self._B[s]

    def D(self, d, s):
        return self.m1_cuadro(d, s) - self.base(s)[0]

    def S(self, d, s):
        """(S, indice en Z del minimo, fraccion de Z con D valido); S NaN si la fraccion es < 0,80."""
        if (d, s) not in self._S:
            self._S[(d, s)] = self._S_calc(d, s)
        return self._S[(d, s)]

    def _S_calc(self, d, s):
        Dv = self.D(d, s)
        ok = np.isfinite(Dv)
        fr = float(ok.mean())
        if fr < FRAC_Z:
            return np.nan, -1, fr
        i = int(np.nanargmin(Dv))
        return float(Dv[i]), i, fr


# ---------- umbral, nulo del evento, poder ----------
def pool_placebo(det, s, w, excluir=()):
    """Cuadros placebo (d, x) despejados por E1 y evaluados, con |hora - s| <= w cuadros."""
    out = []
    for d in PLACEBO:
        if d in excluir:
            continue
        for x in range(144):
            if dslot(x, s) <= w and det.E1[d, x] and np.isfinite(det.S(d, x)[0]):
                out.append((d, x))
    return out


def umbral(det, s, excluir=()):
    """U(h): percentil 5 de S en los placebo despejados a +-60 min; si hay < 20, +-120 min; si no, None."""
    k = (s, tuple(excluir))
    if k not in det._U:
        det._U[k] = _umbral(det, s, excluir)
    return det._U[k]


def _umbral(det, s, excluir):
    for w in (W_U, W_U2):
        pool = pool_placebo(det, s, w, excluir)
        if len(pool) >= MIN_U:
            Ss = np.array([det.S(d, x)[0] for d, x in pool])
            por_dia = {}
            for d, _ in pool:
                por_dia[fecha(d)[5:]] = por_dia.get(fecha(d)[5:], 0) + 1
            return {"U": float(np.percentile(Ss, PCT_U)), "ventana_min": 10 * w, "n": len(pool),
                    "por_dia": por_dia, "pool": pool}
    return {"U": None, "ventana_min": None, "n": len(pool_placebo(det, s, W_U2, excluir)), "por_dia": {}, "pool": []}


def nulo_pares(det, s1, s2, w):
    """Minimo de S en cada par de cuadros consecutivos placebo despejados y evaluados del mismo dia, con los dos
    cuadros dentro de [s1 - w, s2 + w] (la ventana del evento, enmienda 1)."""
    out = []
    for d in PLACEBO:
        for x in range(max(0, s1 - w), min(143, s2 + w)):
            y = x + 1
            if y > s2 + w:
                continue
            a, b = det.S(d, x)[0], det.S(d, y)[0]
            if det.E1[d, x] and det.E1[d, y] and np.isfinite(a) and np.isfinite(b):
                out.append(min(a, b))
    return np.array(out)


def cheb(i, rc):
    return max(abs(int(ZR[i]) - rc[0]), abs(int(ZC[i]) - rc[1]))


def poder(det, U, pool, a, rng):
    """200 inyecciones: cuadro placebo al azar (con reposicion si el pool es menor) y pixel al azar de Z; se resta
    `a` K a la BTD del pixel (D baja en a exacto: el control esta a > 15 km). Acierto: S <= U y minimo a <= 1 pixel."""
    hits, perdidas = 0, 0
    reps = len(pool) < N_POD
    fi = rng.choice(len(pool), N_POD, replace=reps)
    pj = rng.integers(0, NZ, N_POD)
    for f, j in zip(fi, pj):
        d, x = pool[f]
        Dv = det.D(d, x).copy()
        if not np.isfinite(Dv[j]):
            perdidas += 1
        Dv[j] -= a
        i = int(np.nanargmin(Dv))
        if Dv[i] <= U and max(abs(int(ZR[i]) - int(ZR[j])), abs(int(ZC[i]) - int(ZC[j]))) <= 1:
            hits += 1
    return {"poder": hits / N_POD, "inyecciones": N_POD, "con_reposicion": bool(reps),
            "pool": len(pool), "pixel_inyectado_sin_D": perdidas}


# ---------- datos ----------
def cargar():
    r14, r15, acm, co14, co15 = H24.cargar()
    E1 = H24.despejada("chillan", acm)
    M = M29.Medidor(r14, r15, co14, co15, None, [])
    del r14, r15
    return M, E1, acm


def preparar(det, dias):
    for d in dias:
        for x in range(144):
            det.m1_cuadro(d, x)


# ---------- pruebas ----------
def pruebas(M=None, E1=None):
    assert NZ > 50 and (DIST.ravel()[ZP] <= R_Z).all() and not BLOQUE.ravel()[ZP].any()
    assert not np.intersect1d(ZP, CTRL).size and (DIST.ravel()[CTRL] > R_CTRL).all()
    assert len(PLACEBO) == 14 and not (set(PLACEBO) & EXCL) and not (set(PLACEBO) & set(POZO))
    assert not (set(POZO) & EXCL) and DIAS_POS <= EXCL
    assert dslot(2, 140) == 6 and dslot(80, 86) == 6
    assert cheb(int(np.flatnonzero((ZR == 43) & (ZC == 44))[0]), (44, 45)) == 1
    n = 4
    if M is not None:
        # M1 vectorizado = h29_medir.Medidor.medir con el control a > 15 km y 20 pares (criterio §2)
        old = M29.MIN_PAR
        M29.MIN_PAR = MIN_PAR
        ex4 = (DIST <= R_CTRL).ravel()
        det = Detector(M.bt11, M.btd, E1)
        rng = np.random.default_rng(1)
        comp, fin = 0, 0
        for d, s in [(5, 80), (40, 30), (55, 100), (10, 140), (20, 86)]:
            m = det.m1_cuadro(d, s)
            for i in rng.choice(NZ, 15, replace=False):
                ref = M.medir(d, s, int(ZP[i]), ex4, ex4)[0]
                assert (np.isnan(ref) and np.isnan(m[i])) or abs(ref - m[i]) < 1e-9, (d, s, i, ref, m[i])
                comp += 1
                fin += int(np.isfinite(ref))
        M29.MIN_PAR = old
        # inyectar en la BTD de un pixel de Z baja su M1 en a exacto y no toca el resto
        d, s = 5, 80
        m = det.m1_cuadro(d, s)
        i = int(np.flatnonzero(np.isfinite(m))[0])
        m2 = det.m1_cuadro(d, s, btd_px={int(ZP[i]): float(M.btd[d, s, ZP[i]]) - 0.97})
        assert abs((m[i] - m2[i]) - 0.97) < 1e-5 and np.allclose(np.delete(m, i), np.delete(m2, i), equal_nan=True)
        n += 2
        assert fin > comp // 2, fin
        print(f"M1 = Medidor.medir en {comp} pixeles-cuadro ({fin} con valor); inyeccion exacta")
    print(f"pruebas OK ({n} de {n}); Z {NZ} pixeles, control {len(CTRL)} pixeles")


# ---------- ensayo en seco (§6) ----------
def ventana_positivos(det):
    """Slots de la ventana de decision: union de las ventanas de U de los cuatro cuadros positivos. Solo usa el
    conteo de placebo (no lee los positivos)."""
    sl = set()
    for e in EVENTOS.values():
        for c in e["cuadros"]:
            s = slot(c)
            u = umbral(det, s)
            w = (u["ventana_min"] or 120) // 10
            sl |= {x for x in range(144) if dslot(x, s) <= w}
    return sorted(sl)


def seco_loo(det, slots):
    """Deja fuera un dia placebo cada vez: U con los otros 13, tasa de disparo en el dia excluido."""
    por_dia = {}
    for j in PLACEBO:
        fr, dis, sinU = 0, 0, 0
        for x in slots:
            if not det.E1[j, x]:
                continue
            S = det.S(j, x)[0]
            if not np.isfinite(S):
                continue
            u = umbral(det, x, excluir=(j,))
            if u["U"] is None:
                sinU += 1
                continue
            fr += 1
            dis += S <= u["U"]
        por_dia[fecha(j)] = {"cuadros": fr, "disparos": int(dis), "sin_umbral": sinU,
                             "tasa": dis / fr if fr else None}
    tasas = [v["tasa"] for v in por_dia.values() if v["tasa"] is not None]
    return {"por_dia": por_dia, "dias_con_cuadros": len(tasas),
            "falsa_alarma_media": float(np.mean(tasas)) if tasas else None,
            "cuadros_total": sum(v["cuadros"] for v in por_dia.values()),
            "disparos_total": sum(v["disparos"] for v in por_dia.values())}


def seco():
    M, E1, _ = cargar()
    pruebas(M, E1)
    det = Detector(M.bt11, M.btd, E1)
    preparar(det, POZO)
    preparar(det, PLACEBO)
    out = {"criterio": "criterio_2026-11-24.md (6f51c96) + enmienda 1 antes de medir",
           "Z_pixeles": NZ, "control_pixeles": len(CTRL), "crater_px": CRATER_PX,
           "placebo": PLACEBO_TXT, "pozo": f"{fecha(POZO[0])} a {fecha(POZO[-1])}"}
    # cobertura de los positivos sin leerlos: base y umbral a su hora
    cob = {}
    for k, e in EVENTOS.items():
        for c in e["cuadros"]:
            s = slot(c)
            b, n, nf = det.base(s)
            u = umbral(det, s)
            cob[f"{k} {c}"] = {"cuadros_pozo_E1_pm10": nf, "pixeles_Z_con_base": int(np.isfinite(b).sum()),
                               "U": u["U"], "ventana_U_min": u["ventana_min"], "n_U": u["n"],
                               "placebo_por_dia": u["por_dia"],
                               "pixel_verdad_con_base": bool(np.isfinite(b[int(np.flatnonzero((ZR == e["verdad"][0]) & (ZC == e["verdad"][1]))[0])]))}
    out["cobertura_positivos"] = cob
    sl = ventana_positivos(det)
    out["ventana_decision"] = [hhmm(sl[0]), hhmm(sl[-1])]
    out["seco_decide"] = seco_loo(det, sl)
    fa = out["seco_decide"]["falsa_alarma_media"]
    out["valida"] = fa is not None and fa <= FA_MAX
    out["seco_todas_las_horas_informativo"] = {k: v for k, v in seco_loo(det, list(range(144))).items() if k != "por_dia"}
    # placebo: cuantos cuadros evaluados y despejados hay por dia (todas las horas)
    out["placebo_cuadros_por_dia"] = {fecha(d): {"evaluados": int(sum(np.isfinite(det.S(d, x)[0]) for x in range(144))),
                                                 "evaluados_E1": int(sum(det.E1[d, x] and np.isfinite(det.S(d, x)[0]) for x in range(144)))}
                                      for d in PLACEBO}
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "seco.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in out.items() if k != "placebo_cuadros_por_dia"}, ensure_ascii=False, indent=1))


# ---------- medida (§3 a §5, §7) ----------
def idx_z(rc):
    return int(np.flatnonzero((ZR == rc[0]) & (ZC == rc[1]))[0])


def cuadro_info(det, d, s, U):
    S, i, fr = det.S(d, s)
    r = {"cuadro": f"{fecha(d)} {hhmm(s)}", "E1": bool(det.E1[d, s]), "frac_Z_valida": round(fr, 3),
         "S": None if not np.isfinite(S) else round(S, 3), "U": None if U is None else round(U, 3)}
    if np.isfinite(S):
        r["min_px"] = [int(ZR[i]), int(ZC[i])]
        r["min_dist_km"] = round(float(DIST[ZR[i], ZC[i]]), 1)
        r["dispara"] = None if U is None else bool(S <= U)
    return r


def medir():
    seco_res = json.load(open(os.path.join(RES, "seco.json"), encoding="utf-8"))
    M, E1, acm = cargar()
    pruebas(M, E1)
    det = Detector(M.bt11, M.btd, E1)
    preparar(det, POZO)
    preparar(det, PLACEBO)
    out = {"criterio": "criterio_2026-11-24.md (6f51c96) + enmienda 1 antes de medir",
           "seco_valida": seco_res["valida"], "seco_falsa_alarma": seco_res["seco_decide"]["falsa_alarma_media"],
           "eventos": {}}
    pod_097 = []
    for k, e in EVENTOS.items():
        d = dia_idx(e["dia"])
        s1, s2 = slot(e["cuadros"][0]), slot(e["cuadros"][1])
        iv = idx_z(e["verdad"])
        r = {"cuadros": {}, "verdad_px": e["verdad"]}
        ws = []
        for c in e["cuadros"]:
            s = slot(c)
            u = umbral(det, s)
            ci = cuadro_info(det, d, s, u["U"])
            Dv = det.D(d, s)
            ci["U_ventana_min"], ci["U_n"], ci["U_por_dia"] = u["ventana_min"], u["n"], u["por_dia"]
            ci["D_verdad"] = None if not np.isfinite(Dv[iv]) else round(float(Dv[iv]), 3)
            ci["M1_verdad"] = round(float(det.m1_cuadro(d, s)[iv]), 3) if np.isfinite(det.m1_cuadro(d, s)[iv]) else None
            ci["B_verdad"] = round(float(det.base(s)[0][iv]), 3) if np.isfinite(det.base(s)[0][iv]) else None
            ci["rango_verdad_en_Z"] = int(np.sum(Dv[np.isfinite(Dv)] <= Dv[iv])) if np.isfinite(Dv[iv]) else None
            ci["pixeles_Z_validos"] = int(np.isfinite(Dv).sum())
            if "min_px" in ci:
                ci["localiza"] = max(abs(ci["min_px"][0] - e["verdad"][0]), abs(ci["min_px"][1] - e["verdad"][1])) <= 1
                ci["dist_min_a_verdad_px"] = max(abs(ci["min_px"][0] - e["verdad"][0]), abs(ci["min_px"][1] - e["verdad"][1]))
            ci["acm_verdad"] = int(acm[d, s, e["verdad"][0] * NX + e["verdad"][1]])
            # poder por cuadro positivo
            ci["poder"] = {}
            if u["U"] is not None:
                for nom, a in FIRMAS.items():
                    ci["poder"][nom] = poder(det, u["U"], u["pool"], a, np.random.default_rng(SEMILLA))
            r["cuadros"][c] = ci
            ws.append((u["ventana_min"] or 0) // 10)
        # evento: dispara, localiza, p
        cs = list(r["cuadros"].values())
        dis = [c.get("dispara") for c in cs]
        r["dispara"] = any(x is True for x in dis)
        r["localiza"] = any(c.get("dispara") is True and c.get("localiza") for c in cs)
        Sv = [c["S"] for c in cs if c["S"] is not None]
        r["S_evento"] = min(Sv) if Sv else None
        w = max(ws) if all(ws) else 0
        if w and r["S_evento"] is not None:
            nulo = nulo_pares(det, s1, s2, w)
            r["nulo_pares_n"] = int(len(nulo))
            r["nulo_pares_p5_p50"] = [round(float(np.percentile(nulo, 5)), 3), round(float(np.percentile(nulo, 50)), 3)] if len(nulo) else None
            r["p"] = float(np.mean(nulo <= r["S_evento"])) if len(nulo) else None
            r["ventana_nulo"] = [hhmm(max(0, s1 - w)), hhmm(min(143, s2 + w))]
        else:
            r["p"] = None
        r["cumple"] = bool(r["dispara"] and r["localiza"] and r["p"] is not None and r["p"] <= P_MAX)
        r["sin_nulo"] = any(c["U"] is None for c in cs)
        out["eventos"][k] = r
        pod_097 += [c["poder"]["-0.97"]["poder"] for c in cs if "-0.97" in c["poder"]]
        print(k, json.dumps(r, ensure_ascii=False, default=str), flush=True)
    # veredicto
    cumple = [r["cumple"] for r in out["eventos"].values()]
    p097 = min(pod_097) if pod_097 else None
    out["poder_097_min_4_cuadros"] = p097
    if not seco_res["valida"]:
        ver = "INVÁLIDA"
    elif any(r["sin_nulo"] for r in out["eventos"].values()):
        ver = "NO CONCLUYENTE (sin nulo)"
    elif all(cumple):
        ver = "DETECTA SIN SABER DÓNDE MIRAR"
    elif any(cumple):
        ver = "PARCIAL"
    elif p097 is not None and p097 >= POD_MIN:
        ver = "NO DETECTA"
    else:
        ver = "SIN PODER"
    out["veredicto"] = ver
    print("VEREDICTO", ver, "poder -0,97 min", p097, flush=True)
    out["informativo"] = informativo(det, E1)
    json.dump(out, open(os.path.join(RES, "s21e_resultado.json"), "w", encoding="utf-8"), indent=1,
              ensure_ascii=False, default=str)
    figura(det)


# ---------- informativo (§7) ----------
def informativo(det, E1):
    inf = {}
    Ucache = {}

    def U_de(s):
        if s not in Ucache:
            Ucache[s] = umbral(det, s)["U"]
        return Ucache[s]

    # 1. tasa de disparo por hora en todos los cuadros placebo (U sin el propio dia)
    por_hora = {}
    for h in range(24):
        a = {"E1": [0, 0], "todos": [0, 0], "sin_umbral": 0}
        for j in PLACEBO:
            for x in range(h * 6, h * 6 + 6):
                S = det.S(j, x)[0]
                if not np.isfinite(S):
                    continue
                u = umbral(det, x, excluir=(j,))["U"]
                if u is None:
                    a["sin_umbral"] += 1
                    continue
                a["todos"][0] += 1
                a["todos"][1] += int(S <= u)
                if E1[j, x]:
                    a["E1"][0] += 1
                    a["E1"][1] += int(S <= u)
        por_hora[f"{h:02d}"] = a
    inf["placebo_por_hora_UTC"] = por_hora
    # 2. los 60 cuadros con archivo de evento de VOLCAT y los 4 nacimientos
    filas = list(csv.DictReader(open(VOLCAT_CSV, encoding="utf-8")))
    vol = []
    for f in filas:
        dd, hm = f["hora"].split(" ")
        d = dia_idx(f"2026-{dd[3:5]}-{dd[0:2]}")
        s = slot(hm)
        ci = cuadro_info(det, d, s, U_de(s))
        ci["nacimiento"] = f["nacimiento"] == "True"
        vol.append(ci)
    inf["volcat_60"] = resumen_grupo(vol)
    inf["volcat_60_cuadros"] = vol
    inf["volcat_nacimientos"] = [v for v in vol if v["nacimiento"]]
    # 3. pulsos del OVDAS (H24), manana (inicio < 15:00 UTC, mediodia local) y tarde
    ven = H24.ventanas()
    pul = {"manana": [], "tarde": []}
    for e in H24.EPISODIOS:
        eid = e[0]
        t = datetime.strptime(e[1], "%Y-%m-%d %H:%M")
        d, slots = ven[eid]
        grupo = "manana" if t.hour < 15 else "tarde"
        cs = [cuadro_info(det, d, s, U_de(s)) for s in slots]
        pul[grupo].append({"ep": eid, "inicio_UTC": e[1], "H_m": e[3], "cuadros": len(cs),
                           "evaluados": sum(c["S"] is not None for c in cs),
                           "con_umbral": sum(c.get("dispara") is not None for c in cs),
                           "disparan": sum(c.get("dispara") is True for c in cs),
                           "E1": sum(c["E1"] for c in cs),
                           "detalle": [c for c in cs if c.get("dispara") is True]})
    inf["pulsos_ovdas"] = {g: {"episodios": v, **resumen_grupo(None, ep_list=v)} for g, v in pul.items()}
    return inf


def resumen_grupo(cs, ep_list=None):
    if ep_list is not None:
        return {"cuadros": sum(e["cuadros"] for e in ep_list), "evaluados": sum(e["evaluados"] for e in ep_list),
                "con_umbral": sum(e["con_umbral"] for e in ep_list), "disparan": sum(e["disparan"] for e in ep_list),
                "episodios_con_disparo": sum(e["disparan"] > 0 for e in ep_list)}
    return {"cuadros": len(cs), "E1": sum(c["E1"] for c in cs), "evaluados": sum(c["S"] is not None for c in cs),
            "con_umbral": sum(c.get("dispara") is not None for c in cs),
            "disparan": sum(c.get("dispara") is True for c in cs)}


def figura(det):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(FIG, exist_ok=True)
    fig, ax = plt.subplots(1, 4, figsize=(13, 3.6), constrained_layout=True)
    r0, r1 = ZR.min() - 1, ZR.max() + 2
    c0, c1 = ZC.min() - 1, ZC.max() + 2
    k = 0
    for nom, e in EVENTOS.items():
        d = dia_idx(e["dia"])
        for c in e["cuadros"]:
            s = slot(c)
            Dv = det.D(d, s)
            img = np.full((NY, NX), np.nan)
            img.ravel()[ZP] = Dv
            a = ax[k]
            im = a.imshow(img[r0:r1, c0:c1], cmap="RdBu", vmin=-2, vmax=2, extent=(c0 - .5, c1 - .5, r1 - .5, r0 - .5))
            a.plot(CRATER_PX[1], CRATER_PX[0], "k^", mfc="none", ms=9, label="cráter")
            a.plot(e["verdad"][1], e["verdad"][0], "s", mfc="none", mec="lime", ms=11, mew=2, label="píxel de verdad")
            S, i, _ = det.S(d, s)
            if i >= 0:
                a.plot(ZC[i], ZR[i], "x", c="k", ms=10, mew=2, label="mínimo de Z")
            a.set_title(f"{e['dia'][8:10]}-{e['dia'][5:7]} {c} UTC  S {S:+.2f} K", fontsize=9)
            a.set_xlabel("columna ABI")
            if k == 0:
                a.set_ylabel("fila ABI (norte arriba)")
                h, l = a.get_legend_handles_labels()
            k += 1
    fig.colorbar(im, ax=ax, shrink=0.85, label="D = M1 - B (K)")
    fig.legend(h, l, loc="outside lower center", ncol=3, fontsize=8)
    fig.savefig(os.path.join(FIG, "mapa_D_positivos.png"), dpi=90)


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else ""
    if modo == "pruebas":
        M, E1, _ = cargar()
        pruebas(M, E1)
    elif modo == "seco":
        seco()
    elif modo == "medir":
        medir()
    elif modo == "figura":
        M, E1, _ = cargar()
        det = Detector(M.bt11, M.btd, E1)
        figura(det)
    else:
        print(__doc__)
