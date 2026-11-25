r"""S26a: un solo detector de pluma para Nevados de Chillán, la unión de la zona de 0 a 4 km del cráter (S25a) y el
anillo de 4 a 40 km (candidata S23b). Implementa criterio_2026-11-25.md (commit 28f963b, empujado antes de calcular
un solo disparo de la unión).

Por qué la unión: el anillo ve la pluma que se aleja (08-11) y la zona la que queda pegada al cráter (14-11, 10-11);
Nicolás mira un solo detector contra VOLCAT. Por qué puede hacer falta bajar el percentil: dos reglas que fallan cada
una ~4 % de los cuadros tranquilos fallan juntas en más del 5 %; el criterio fija cómo corregirlo, sólo con 2025.

Las dos partes se importan sin cambios (s23_medir.Detector y disparos; funciones de s25a_medir). Lo único que se
mueve es s22b_medir.PCT_U, el percentil que usan las dos funciones de umbral.

Uso: python -I s26a_medir.py pruebas | medir | confirmar_s25a [--vistazo] | confirmar [--vistazo]
  medir      ensayo en seco conjunto en 2025 (elige p*), comprobación de que cada parte sola reproduce lo publicado, y
             recuerdo contra VOLCAT de 2026 (DESARROLLO). Escribe resultados/s26a_seco.json, s26a_desarrollo.json y la
             tabla por cuadro en D:\goes_notas\s26\s26a\tabla_2026.csv (para los videos).
  confirmar_s25a  la confirmación congelada de S25a (zona sola, percentil 5), después de `s23b_confirmar.py medir`.
  confirmar  la unión en días nuevos desde el 25-11 (criterio §5): sólo con 20 P en 2 días nuevos; va después de
             S23b y S25a (se niega si falta alguno de sus resultados).
"""
import csv
import hashlib
import json
import os
import sys
import time
import warnings
from datetime import datetime, timedelta

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore", RuntimeWarning)
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "s23_fondo_2025", "scripts"))
sys.path.insert(0, os.path.join(OV, "s25a_crater", "scripts"))
import s23_medir as S  # noqa: E402
import s25a_medir as Z  # noqa: E402
B, M, H24, C29 = S.B, S.M, S.H24, S.C29
assert Z.B is B

TRAB = r"D:\goes_notas\s26\s26a"
ESTAT26 = Z.ESTAT26
SHA_ESTAT26 = Z.SHA_ESTAT26
# ---------- parámetros del criterio ----------
SECO_MAX = 0.05
PCTS = [5.0 - 0.25 * i for i in range(13)]          # 5,0; 4,75; ... ; 2,0 (§2)
R_MIN, P25_MAX, PN_MAX, MIN_P_EVAL, MIN_DIAS_ALC = 0.40, 0.01, 0.05, 10, 3
R_MIN_S25A = 0.25                                    # s25a_crater/criterio_confirmacion_2026-11-25.md §3
RES_S25A = os.path.join(OV, "s25a_crater", "resultados", "s25a_confirmacion.json")
P25_SIN_CORREGIR = 0.01 / 3                          # §5: "confirma con un umbral sin corregir por tres pruebas"
NOCHE, DIA = range(18, 54), range(72, 144)          # 03:00 a 08:50 UTC; 12:00 a 23:50 UTC
REPRO = {"anillo_P": (25, 54), "zona_P": (44, 93), "anillo_seco_media_dia": 0.04279096445833097,
         "zona_seco_global": 176 / 5499}


def _pct(p):
    """Fija el percentil de las dos partes y vacía el caché de umbrales del anillo."""
    B.PCT_U = p


# ---------- las dos partes ----------
class Partes:
    """Anillo (Detector de S23 con la costumbre de 2026 congelada) y zona (funciones de S25a), 2025 y 2026."""

    def __init__(self):
        t = time.time()
        est26 = np.load(ESTAT26)
        assert hashlib.sha256(est26.tobytes()).hexdigest()[:16] == SHA_ESTAT26, "estat_2026 no es el congelado"
        self.est26 = est26
        self.A = S.Detector(ref="2025", con_blanco=True, estat_blanco=est26)
        print(f"anillo listo en {time.time() - t:.0f} s", flush=True)
        # zona: lo mismo que s25a_medir.medir hasta antes de los umbrales
        btd25 = np.load(Z._npy("r25_btd"), mmap_mode="r")
        acm25 = np.load(Z._npy("r25_acm"))
        hay25 = np.isfinite(btd25[:, :, Z.ZONA[0]])
        est25 = Z.costumbre(acm25, hay25)
        FD25, DIN25 = Z.nubes(acm25, est25)
        G25 = FD25 <= B.G_MAX
        USA25 = G25 & H24.despejada("chillan", acm25) & hay25
        btd25 = np.asarray(btd25)
        self.bctrl = Z.base(btd25, USA25, Z.CTRL)
        C25 = Z.regional(btd25, DIN25, self.bctrl)
        IZ = np.arange(len(Z.ZONA))
        self.Z25 = np.ascontiguousarray(btd25[:, :, Z.ZONA])
        del btd25
        self.USA25 = USA25
        BZ = np.array([Z.base(self.Z25, USA25, IZ, excl=d) for d in range(Z.NR)])
        self.SRz, _ = Z.tabla_S(self.Z25, C25, BZ, G25)
        self.bz = Z.base(self.Z25, USA25, IZ)
        btd26 = np.concatenate([np.load(os.path.join(B.TRAB, "dev_btd.npy")), np.load(Z._npy("n26_btd"))])
        acm26 = np.concatenate([np.load(os.path.join(B.TRAB, "dev_acm.npy")),
                                np.load(os.path.join(B.TRAB, "nuevo_acm.npy"))])
        FD26, DIN26 = Z.nubes(acm26, est26)
        self.FD26 = FD26
        C26 = Z.regional(btd26, DIN26, self.bctrl)
        self.STz, self.PTz = Z.tabla_S(btd26[:, :, Z.ZONA], C26, self.bz, FD26 <= B.G_MAX)
        self.CL = B.clases()
        assert self.CL.shape[0] == btd26.shape[0] == B.ND
        print(f"zona lista en {time.time() - t:.0f} s", flush=True)

    # ---- 2025, cada día sin sí mismo ----
    def seco(self, p):
        _pct(p)
        self.A._U = {}
        ULz = [Z.umbral(self.SRz, excl=d) for d in range(Z.NR)]
        out = {"a": [], "z": [], "u": []}                # por día: (F, ev)
        for d in range(Z.NR):
            Ua, _ = self.A.umbral(d)
            Fa, eva = S.disparos(self.A.SR, self.A.KR, d, Ua)
            Fz, evz = Z.disparos(self.SRz, d, ULz[d], ULz[d - 1] if d else None)
            out["a"].append((Fa, eva))
            out["z"].append((Fz, evz))
            out["u"].append((Fa | Fz, eva | evz))
        return out

    # ---- 2026, base y umbral de 2025 con los 62 días ----
    def blanco(self, p):
        _pct(p)
        self.A._U = {}
        Ua, _ = self.A.umbral(None)
        Uz = Z.umbral(self.SRz)
        res = []
        for d in range(B.ND):
            Fa, eva = S.disparos(self.A.ST, self.A.KT, d, Ua)
            Fz, evz = Z.disparos(self.STz, d, Uz)
            res.append({"a": (Fa, eva), "z": (Fz, evz), "u": (Fa | Fz, eva | evz)})
        return res, Ua, Uz


def medidas_seco(dias):
    """Global y media por día de la falsa alarma; dias = lista de (F, ev)."""
    nF = sum(int(F.sum()) for F, _ in dias)
    nE = sum(int(ev.sum()) for _, ev in dias)
    fr = [F.sum() / ev.sum() for F, ev in dias if ev.sum()]
    noche = (sum(int(F[NOCHE].sum()) for F, _ in dias), sum(int(ev[NOCHE].sum()) for _, ev in dias))
    dia = (sum(int(F[DIA].sum()) for F, _ in dias), sum(int(ev[DIA].sum()) for _, ev in dias))
    return {"global": nF / nE if nE else None, "media_por_dia": float(np.mean(fr)) if fr else None,
            "disparos": nF, "evaluados": nE, "noche_03_09": noche, "dia_12_24": dia}


def azar(dias):
    sl, al = [], []
    for F, ev in dias:
        for s in np.flatnonzero(ev):
            sl.append(s)
            al.append(B.alcanzado(F, ev, s)[1])
    return S.azar_por_hora(sl, al)


def recuerdo(PN, r25):
    """R, p25 y pN de una lista de (d, s, clase, alcanzado)."""
    P = [(d, s, a) for d, s, c, a in PN if c == "P"]
    N = [(d, s, a) for d, s, c, a in PN if c == "N"]
    te, th = len(P), int(sum(a for *_, a in P))
    p25 = S.poisson_binomial_cola([r25[s] for _, s, _ in P], th) if te else None
    psl = {s for _, s, _ in P}
    cerca = [a for _, s, a in N if any(M.dslot(s, x) <= S.W_AZAR for x in psl)]
    pN = (float(stats.fisher_exact([[th, te - th], [int(sum(cerca)), len(cerca) - int(sum(cerca))]],
                                   alternative="greater")[1]) if te and cerca else None)
    return {"P_evaluados": te, "P_alcanzados": th, "R": th / te if te else None,
            "E25": float(sum(r25[s] for _, s, _ in P)), "p25": p25, "N_cerca": len(cerca),
            "N_cerca_alcanzados": int(sum(cerca)), "pN": pN,
            "dias_P_evaluado": len({d for d, _, _ in P}), "dias_P_alcanzado": len({d for d, _, a in P if a})}


def lista(res, CL, parte, dias=None):
    out = []
    for d in (range(len(res)) if dias is None else dias):
        F, ev = res[d][parte]
        for s in np.flatnonzero(ev):
            if CL[d, s] in ("P", "N"):
                out.append((d, s, CL[d, s], B.alcanzado(F, ev, s)[1]))
    return out


def _r(x):
    return None if (x is None or not np.isfinite(x)) else round(float(x), 5)


def cola_anillo(A, d, s):
    """Los 8 píxeles (índices de la grilla) de la cola de la tajada del mínimo, como los pinta S23."""
    base = A.base(None)
    idx = np.flatnonzero(M.SEC == A.KT[d, s])
    v = (A.mmT[d, s] - base[s])[idx]
    o = np.argsort(np.where(np.isfinite(v), v, np.inf))[:M.NCOLA]
    return M.AP[idx[o]]


# ---------- medir: §2 y §3 ----------
def medir():
    os.makedirs(TRAB, exist_ok=True)
    os.makedirs(RES, exist_ok=True)
    X = Partes()
    # comprobación de código a percentil 5 (§2)
    sec5 = X.seco(5.0)
    ma, mz, mu = (medidas_seco(sec5[k]) for k in ("a", "z", "u"))
    res5, _, _ = X.blanco(5.0)
    rA = azar(sec5["a"])
    rZ = azar(sec5["z"])
    ra = recuerdo(lista(res5, X.CL, "a"), rA)
    rz = recuerdo(lista(res5, X.CL, "z"), rZ)
    repro = {"anillo_seco_media_dia": ma["media_por_dia"], "zona_seco_global": mz["global"],
             "anillo_P": (ra["P_alcanzados"], ra["P_evaluados"]), "zona_P": (rz["P_alcanzados"], rz["P_evaluados"])}
    ok = (abs(repro["anillo_seco_media_dia"] - REPRO["anillo_seco_media_dia"]) < 1e-9
          and abs(repro["zona_seco_global"] - REPRO["zona_seco_global"]) < 1e-9
          and tuple(repro["anillo_P"]) == REPRO["anillo_P"] and tuple(repro["zona_P"]) == REPRO["zona_P"])
    print("reproducción a percentil 5:", json.dumps(repro), "OK" if ok else "NO REPRODUCE", flush=True)
    if not ok:
        json.dump({"reproduccion": repro, "esperado": REPRO}, open(os.path.join(RES, "s26a_reproduccion_FALLA.json"),
                                                                   "w", encoding="utf-8"), indent=1)
        sys.exit("no reproduce: error de código, no se mira la unión")
    # elección de p* (§2)
    tabla_p, pstar, secos = [], None, {5.0: sec5}
    for p in PCTS:
        sec = secos.get(p) or X.seco(p)
        secos[p] = sec
        mu_p = medidas_seco(sec["u"])
        tabla_p.append({"pct": p, "union": mu_p, "anillo": medidas_seco(sec["a"]), "zona": medidas_seco(sec["z"])})
        print(f"p {p:.2f}: unión global {mu_p['global']:.4f}, media por día {mu_p['media_por_dia']:.4f}", flush=True)
        if mu_p["global"] <= SECO_MAX and mu_p["media_por_dia"] <= SECO_MAX:
            pstar = p
            break
    seco_out = {"criterio": "criterio_2026-11-25.md (28f963b)", "reproduccion_pct5": repro, "p_estrella": pstar,
                "veredicto_seco": "pasa" if pstar is not None else "NO SIRVE", "por_percentil": tabla_p}
    json.dump(seco_out, open(os.path.join(RES, "s26a_seco.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    p = pstar if pstar is not None else 5.0
    sec = secos[p]
    r25 = {k: azar(sec[k]) for k in ("a", "z", "u")}
    res, Ua, Uz = X.blanco(p)
    CL = X.CL
    R = {k: recuerdo(lista(res, CL, k), r25[k]) for k in ("a", "z", "u")}
    ru = R["u"]
    if pstar is None:
        ver = "NO SIRVE"
    elif ru["p25"] <= P25_MAX and ru["pN"] is not None and ru["pN"] <= PN_MAX and ru["R"] >= R_MIN \
            and ru["dias_P_alcanzado"] >= MIN_DIAS_ALC:
        ver = "ALCANZA (desarrollo)"
    elif ru["p25"] <= P25_MAX:
        ver = "PARCIAL (desarrollo)"
    else:
        ver = "NO ALCANZA (desarrollo)"
    # por día y episodios
    por_dia, eps_t, eps_h = [], 0, 0
    for d in range(B.ND):
        Ps = np.flatnonzero(CL[d] == "P")
        F, ev = res[d]["u"]
        if not len(Ps) and not F.any():
            continue
        fila = {"dia": B.fecha(d), "P": int(len(Ps))}
        for k, nom in (("a", "anillo"), ("z", "zona"), ("u", "union")):
            Fk, evk = res[d][k]
            pe = [B.alcanzado(Fk, evk, s)[1] for s in Ps if evk[s]]
            fila[nom] = {"P_evaluados": len(pe), "P_alcanzados": int(sum(pe)), "disparos": int(Fk.sum())}
        Fa, eva = res[d]["a"]
        Fz, evz = res[d]["z"]
        fila["P_alcanzados_por_los_dos"] = int(sum(1 for s in Ps if ev[s] and B.alcanzado(Fa, eva, s)[1]
                                                   and B.alcanzado(Fz, evz, s)[1]))
        Nd = [s for s in np.flatnonzero(ev) if CL[d, s] == "N"]
        fila["N_evaluados"] = len(Nd)
        fila["N_con_disparo"] = int(sum(F[s] for s in Nd))
        por_dia.append(fila)
        for ep in (M.episodios(list(Ps)) if len(Ps) else []):
            if ev[ep].any():
                eps_t += 1
                eps_h += bool(F[max(0, ep[0] - 3):min(144, ep[-1] + 4)].any())
    # sin cada día (desarrollo)
    dias_P = sorted({d for d in range(B.ND) if (CL[d] == "P").any()})
    sin = {}
    for x in dias_P:
        q = recuerdo(lista(res, CL, "u", [d for d in range(B.ND) if d != x]), r25["u"])
        sin[B.fecha(x)] = {k: q[k] for k in ("P_evaluados", "P_alcanzados", "R", "p25", "pN")}
    # tasa de disparo de los N de 2026 contra 2025, de día y de noche
    def tasa(pares, rango):
        v = [F[s] for F, ev in pares for s in np.flatnonzero(ev) if s in rango]
        return {"n": len(v), "fraccion": float(np.mean(v)) if v else None}
    Nu = [(res[d]["u"][0], res[d]["u"][1] & (CL[d] == "N")) for d in range(B.ND)]
    tasas = {"N_2026_dia": tasa(Nu, DIA), "N_2026_noche": tasa(Nu, NOCHE),
             "2025_dia": tasa(sec["u"], DIA), "2025_noche": tasa(sec["u"], NOCHE)}
    out = {"rotulo": "DESARROLLO: los P de 21-09 a 24-11-2026 ya se miraron; describe, no prueba (criterio §3)",
           "p_estrella": pstar, "veredicto": ver, "union": ru, "anillo_a_p": R["a"], "zona_a_p": R["z"],
           "episodios": eps_t, "episodios_alcanzados": eps_h, "tasas_disparo": tasas, "por_dia": por_dia,
           "sin_cada_dia": sin,
           "umbral_anillo_por_hora": {M.hhmm(s): _r(Ua[s]) if Ua[s] is not None else None for s in range(0, 144, 6)},
           "umbral_zona_por_hora": {M.hhmm(s): _r(Uz[s]) if Uz[s] is not None else None for s in range(0, 144, 6)}}
    json.dump(out, open(os.path.join(RES, "s26a_desarrollo.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1, default=int)
    # tabla por cuadro (para los videos; en D:, no en el repo)
    with open(os.path.join(TRAB, "tabla_2026.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dia", "hora", "clase", "ev_a", "F_a", "S_a", "U_a", "k_a", "cola_a", "ev_z", "F_z", "S_z", "U_z",
                    "px1", "px2", "FD"])
        for d in range(B.ND):
            (Fa, eva), (Fz, evz) = res[d]["a"], res[d]["z"]
            for s in range(144):
                cola = ";".join(str(i) for i in cola_anillo(X.A, d, s)) if Fa[s] else ""
                w.writerow([B.fecha(d), M.hhmm(s), CL[d, s], int(eva[s]), int(Fa[s]), _r(X.A.ST[d, s]),
                            _r(Ua[s]) if Ua[s] is not None else None, int(X.A.KT[d, s]), cola, int(evz[s]),
                            int(Fz[s]), _r(X.STz[d, s]), _r(Uz[s]) if Uz[s] is not None else None,
                            int(Z.ZONA[X.PTz[d, s, 0]]) if X.PTz[d, s, 0] >= 0 else -1,
                            int(Z.ZONA[X.PTz[d, s, 1]]) if X.PTz[d, s, 1] >= 0 else -1, _r(X.FD26[d, s])])
    print(json.dumps({k: v for k, v in out.items() if k not in ("por_dia", "sin_cada_dia")}, ensure_ascii=False,
                     indent=1, default=int))


# ---------- confirmar: §5 (días nuevos desde el 25-11-2026) ----------
def _cubo_nuevo(dias, carpeta):
    """BT11, BTD (todos los píxeles), ACM y M1 de los días nuevos, con I1 a I3 como s23b_confirmar._cubo."""
    n = len(dias) * 144
    r = {b: np.full((n, S.NPIX), np.nan, "float32") for b in (14, 15)}
    acm = np.full((n, S.NPIX), 255, "uint8")
    co = {14: [], 15: []}
    pres, scan_dist, ult = 0, 0, -1
    for i in range(n):
        dt = dias[0] + timedelta(minutes=10 * i)
        f = os.path.join(carpeta, "l1b", f"{dt:%Y%m%d_%H%M}.npz")
        if os.path.exists(f):
            with np.load(f) as z:
                s14, s15 = str(z["key14"]).split("_s")[1][:14], str(z["key15"]).split("_s")[1][:14]
                if s14 != s15 or s14[:11] != f"{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}":
                    scan_dist += 1
                else:
                    for b in (14, 15):
                        r[b][i] = z[f"rad{b}"].ravel()
                        co[b].append(z[f"co{b}"])
                    pres += 1
                    ult = i
        g = os.path.join(carpeta, "acm", f"{dt:%Y%m%d_%H%M}.npz")
        if os.path.exists(g):
            with np.load(g) as z:
                acm[i] = z["acm"].ravel()
    cof = {b: np.median(np.array(co[b]), 0) for b in (14, 15)}
    bt11 = C29.bt_de_rad(r[14].astype("float64"), cof[14]).astype("float32")
    btd = (bt11 - C29.bt_de_rad(r[15].astype("float64"), cof[15])).astype("float32")
    hay = np.isfinite(bt11).any(1)
    cong = sum(1 for i in range(1, n) if hay[i] and hay[i - 1] and np.array_equal(r[14][i], r[14][i - 1], equal_nan=True))
    v = bt11[np.isfinite(bt11)]
    inst = {"cuadros_hasta_el_ultimo": ult + 1, "presentes": pres, "cobertura": pres / max(ult + 1, 1),
            "scan_distinto": scan_dist, "congelados": cong,
            "bt11_en_rango": float(((v > 180) & (v < 330)).mean()) if v.size else 0.0}
    inst["falla"] = [k for k, ok in (("I1", inst["cobertura"] >= 0.95), ("I2", scan_dist == 0),
                                     ("I3", inst["bt11_en_rango"] >= 0.999 and cong == 0)) if not ok]
    m1 = np.full((n, M.NA), np.nan, np.float32)
    for i in range(n):
        if hay[i]:
            m1[i] = M.m1_cuadro(bt11[i], btd[i])
    nd = len(dias)
    return btd.reshape(nd, 144, -1), acm.reshape(nd, 144, -1), m1.reshape(nd, 144, -1), inst


def confirmar(vistazo=False, s25a=False):
    """s25a=True: la confirmación congelada de S25a (zona sola, percentil 5, R >= 0,25), que va antes que la unión."""
    import s23b_confirmar as SB
    with open(SB.CLASES, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    ult = max(datetime.strptime(x["dt"][:10], "%Y-%m-%d") for x in filas)
    dias = [SB.ARRANQUE + timedelta(days=i) for i in range((ult - SB.ARRANQUE).days + 1)]
    CL = np.full((len(dias), 144), "", object)
    for x in filas:
        CL[(datetime.strptime(x["dt"][:10], "%Y-%m-%d") - SB.ARRANQUE).days, M.slot(x["dt"][11:16])] = x["clase"]
    nP, dP = int((CL == "P").sum()), int(((CL == "P").any(1)).sum())
    if (nP < SB.MIN_P or dP < SB.MIN_DIAS_P) and not vistazo:
        print(f"criterio §5: {nP} P en {dP} días nuevos; hacen falta {SB.MIN_P} en {SB.MIN_DIAS_P}. No se mide.")
        return
    previos = [os.path.join(S.RES, "s23b_resultado.json")] + ([] if s25a else [RES_S25A])
    for previo in previos:
        if not os.path.exists(previo) and not vistazo:
            sys.exit(f"criterio §5: el orden es S23b, S25a, S26a; falta {previo}")
    if s25a:
        p, parte, r_min = 5.0, "z", R_MIN_S25A
    else:
        seco = json.load(open(os.path.join(RES, "s26a_seco.json"), encoding="utf-8"))
        p, parte, r_min = seco["p_estrella"], "u", R_MIN
        assert p is not None, "la unión no pasó el ensayo en seco: NO SIRVE, no se confirma"
    X = Partes()
    sec = X.seco(p)
    r25 = azar(sec[parte])
    btd, acm, m1, inst = _cubo_nuevo(dias, SB.TRAB)
    _pct(p)
    X.A._U = {}
    Ua, _ = X.A.umbral(None)
    Uz = Z.umbral(X.SRz)
    FD, mm = X.A._nubes(acm, m1, X.est26)
    GATE = FD <= B.G_MAX
    B0 = X.A.base(None)
    Sa = np.full(CL.shape, np.nan)
    Ka = np.full(CL.shape, -1, int)
    for d in range(len(dias)):
        for s in range(144):
            if GATE[d, s]:
                Sa[d, s], Ka[d, s], _ = M.estadistico(mm[d, s] - B0[s])
    _, DIN = Z.nubes(acm, X.est26)
    C = Z.regional(btd, DIN, X.bctrl)
    Sz, _ = Z.tabla_S(btd[:, :, Z.ZONA], C, X.bz, GATE)
    res = []
    for d in range(len(dias)):
        Fa, eva = S.disparos(Sa, Ka, d, Ua)
        Fz, evz = Z.disparos(Sz, d, Uz)
        res.append({"u": (Fa | Fz, eva | evz), "a": (Fa, eva), "z": (Fz, evz)})
    nuevos = list(range(1, len(dias)))                     # el día 0 (24-11) es sólo arranque
    ru = recuerdo(lista(res, CL, parte, nuevos), r25)
    if inst["falla"]:
        ver = "INVÁLIDA"
    elif ru["P_evaluados"] < MIN_P_EVAL or ru["dias_P_evaluado"] < 2:
        ver = "NO DECIDIBLE"
    elif ru["p25"] <= P25_MAX and ru["R"] >= r_min and ru["pN"] is not None and ru["pN"] <= PN_MAX:
        ver = "CONFIRMA"
    elif ru["p25"] <= P25_MAX:
        ver = "PARCIAL"
    else:
        ver = "NO CONFIRMA"
    if ver in ("CONFIRMA", "PARCIAL") and ru["p25"] > P25_SIN_CORREGIR:
        ver += " (con un umbral sin corregir por tres pruebas)"
    por_dia = []
    for d in nuevos:
        Ps = np.flatnonzero(CL[d] == "P")
        fila = {"dia": f"{dias[d]:%Y-%m-%d}", "P": int(len(Ps))}
        for k in ("a", "z", "u"):
            F, ev = res[d][k]
            pe = [B.alcanzado(F, ev, s)[1] for s in Ps if ev[s]]
            fila[k] = {"P_evaluados": len(pe), "P_alcanzados": int(sum(pe)), "disparos": int(F.sum())}
        por_dia.append(fila)
    # tasa de disparo de los N nuevos, de día y de noche (S25a §3 la pide)
    tas = {}
    for nom, rg in (("dia", DIA), ("noche", NOCHE)):
        v = [res[d][parte][0][s] for d in nuevos for s in rg if res[d][parte][1][s] and CL[d, s] == "N"]
        tas[nom] = {"n": len(v), "fraccion": float(np.mean(v)) if v else None}
    out = {"veredicto": ver if not vistazo else f"VISTAZO (no decide): {ver}",
           "regla": "S25a, zona sola a percentil 5" if s25a else "S26a, unión a p*", "percentil": p,
           "instrumento": inst, "P_total": nP, "dias_con_P": dP, "medida": ru, "tasa_disparo_N_nuevos": tas,
           "por_dia": por_dia}
    if s25a:
        destino = RES_S25A.replace(".json", "_vistazo.json") if vistazo else RES_S25A
    else:
        destino = os.path.join(RES, "s26a_confirmacion_vistazo.json" if vistazo else "s26a_confirmacion.json")
    json.dump(out, open(destino, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=int)
    print(json.dumps(out, ensure_ascii=False, indent=1, default=int))


# ---------- pruebas de código ----------
def pruebas():
    F1 = np.zeros(144, bool)
    F2 = np.zeros(144, bool)
    e1 = np.zeros(144, bool)
    e2 = np.zeros(144, bool)
    e1[:10] = True
    e2[5:20] = True
    F1[3] = True
    F2[15] = True
    m = medidas_seco([(F1 | F2, e1 | e2)])
    assert m["evaluados"] == 20 and m["disparos"] == 2 and abs(m["global"] - 0.1) < 1e-12
    # recuerdo: un P alcanzado por el cuadro vecino, un N cerca sin disparo
    CL = np.full((1, 144), "", object)
    CL[0, 16], CL[0, 18] = "P", "N"
    r = recuerdo(lista([{"u": (F2, e2)}], CL, "u"), np.full(144, 0.1))
    assert r["P_evaluados"] == 1 and r["P_alcanzados"] == 1 and r["N_cerca"] == 1 and r["N_cerca_alcanzados"] == 0
    assert abs(r["p25"] - 0.1) < 1e-12
    assert PCTS[0] == 5.0 and PCTS[-1] == 2.0 and len(PCTS) == 13
    print("pruebas OK")


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "confirmar":
        confirmar(vistazo="--vistazo" in sys.argv)
    elif c == "confirmar_s25a":
        confirmar(vistazo="--vistazo" in sys.argv, s25a=True)
    else:
        {"pruebas": pruebas, "medir": medir}[c]()
