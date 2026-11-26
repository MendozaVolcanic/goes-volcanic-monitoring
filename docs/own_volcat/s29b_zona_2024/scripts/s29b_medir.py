r"""S29b: la zona del cráter (S25a, percentil 5) y la unión S26a (zona O anillo, percentil 4,75), con base y umbral de
oct-nov 2025, aplicadas a oct-nov 2024 (GOES-16, Chillán en verde). Implementa criterio_2026-11-25.md de esta carpeta
(commit afd2923, empujado antes de calcular un disparo de la zona o de la unión en 2024).

Por qué: S25b mostró que el anillo aguanta fuera de su año. La zona compara cada píxel de la cumbre consigo mismo en
2025, así que todo lo que cambie sólo en la cumbre de un año a otro entra entero; y S28a vio que de día la zona de
Antuco (sin pluma) sube en 2026. Aquí se mide si en otro año tranquilo la zona y la unión disparan lo que prometen, de
día y de noche por separado.

Las reglas se importan sin cambio: s25a_medir (zona), s23_medir.Detector y disparos (anillo), s25b_medir.aplicar y
_detector_2024 (el anillo en 2024 con el nublado de costumbre de 2024). Lo único que se mueve es s22b_medir.PCT_U.

Uso: python -I s29b_medir.py pruebas | medir
  pruebas  comprobación de código con 2025 (criterio §3): seco de la zona a 5 (176 de 5.499) y de la unión a 4,75
           (269 de 5.499, noche 98 de 1.453, día 105 de 2.704), y el camino fuera de muestra de la zona reproduce S.
  medir    (a) geometría G2 a G4, (b) falsa alarma total, (c) día y noche, (d) día contra Antuco; sensibilidad con el
           nublado de costumbre de 2025. Escribe resultados/s29b_resultado.json.
"""
import json
import os
import sys
import time
import warnings
from datetime import datetime, timedelta

import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore", RuntimeWarning)
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
for sub in ("s23_fondo_2025", "s25a_crater", "s25b_fondo_2024"):
    sys.path.insert(0, os.path.join(OV, sub, "scripts"))
import s23_medir as S  # noqa: E402
import s25a_medir as Z  # noqa: E402
import s25b_medir as SB  # noqa: E402
B, M, H24, C29 = S.B, S.M, S.H24, S.C29
assert Z.B is B and SB.B is B

TRAB = r"D:\goes_notas\s29\s29b"
T0 = datetime(2024, 9, 21)
ND = 62
NOCHE, DIA = range(18, 54), range(72, 144)          # 03:00 a 08:50 UTC; 12:00 a 23:50 UTC (S26a, S28a)
P_ZONA, P_UNION = 5.0, 4.75
FA_MAX, FA_MAL, FRANJA_MAX, ESTRICTO = 0.05, 0.10, 0.10, 0.02
MIN_EV_PERIODO, R_SUBE = 300, 1.5
N_BOOT, SEMILLA = 2000, 0
R_ANTUCO = {"union": 2.64, "zona": 3.66}           # S28a, día (unión y zona a 4,75)
G2_MIN, G2_KM, G3_MAX, G3_CAJA = 0.90, 15.0, 0.25, 12
REPRO = {"zona5": (176, 5499), "union475": (269, 5499), "union475_noche": (98, 1453), "union475_dia": (105, 2704)}


def _pct(p, D=None):
    B.PCT_U = p
    if D is not None:
        D._U = {}


def _r(x):
    return None if (x is None or not np.isfinite(x)) else round(float(x), 5)


# ---------- la zona: referencia de 2025 y camino fuera de muestra ----------
class Zona25:
    """Lo mismo que s26a_medir.Partes hace con la zona en 2025 (sin 2026)."""

    def __init__(self):
        btd25 = np.load(Z._npy("r25_btd"), mmap_mode="r")
        self.acm25 = np.load(Z._npy("r25_acm"))
        self.hay25 = np.isfinite(btd25[:, :, Z.ZONA[0]])
        self.est25 = Z.costumbre(self.acm25, self.hay25)
        FD25, DIN25 = Z.nubes(self.acm25, self.est25)
        self.G25 = FD25 <= B.G_MAX
        self.USA25 = self.G25 & H24.despejada("chillan", self.acm25) & self.hay25
        btd25 = np.asarray(btd25)
        self.bctrl = Z.base(btd25, self.USA25, Z.CTRL)
        self.C25 = Z.regional(btd25, DIN25, self.bctrl)
        IZ = np.arange(len(Z.ZONA))
        self.Z25 = np.ascontiguousarray(btd25[:, :, Z.ZONA])
        self.btd25 = btd25
        self.BZ = np.array([Z.base(self.Z25, self.USA25, IZ, excl=d) for d in range(Z.NR)])
        self.SR, self.PR = Z.tabla_S(self.Z25, self.C25, self.BZ, self.G25)
        self.bz = Z.base(self.Z25, self.USA25, IZ)


def aplicar_zona(btd, acm, est, bz, bctrl):
    """S de la zona en un año blanco con la base de la zona bz (144, 11) o (nd, 144, 11) y la de los controles bctrl,
    ambas de 2025; est = nublado de costumbre que decide compuerta y nube dinámica de los controles."""
    FD, DIN = Z.nubes(acm, est)
    G = FD <= B.G_MAX
    C = Z.regional(btd, DIN, bctrl)
    Sx, Px = Z.tabla_S(btd[:, :, Z.ZONA], C, bz, G)
    return Sx, Px, G, FD


# ---------- disparos por día ----------
def dias_zona(Sx, U_de_dia):
    out = []
    for d in range(Sx.shape[0]):
        U = U_de_dia(d)
        Up = U_de_dia(d - 1) if d else None
        out.append(Z.disparos(Sx, d, U, Up))
    return out


def dias_anillo(Sx, Kx, U_de_dia):
    return [S.disparos(Sx, Kx, d, U_de_dia(d)) for d in range(Sx.shape[0])]


def unir(a, z):
    return [(Fa | Fz, ea | ez) for (Fa, ea), (Fz, ez) in zip(a, z)]


# ---------- medidas ----------
def medidas(dias):
    nF = sum(int(F.sum()) for F, _ in dias)
    nE = sum(int(ev.sum()) for _, ev in dias)
    fr = [F.sum() / ev.sum() for F, ev in dias if ev.sum()]
    per = {}
    for nom, rg in (("noche", NOCHE), ("dia", DIA)):
        f = sum(int(F[rg].sum()) for F, _ in dias)
        e = sum(int(ev[rg].sum()) for _, ev in dias)
        per[nom] = (f, e)
    franjas = {}
    for b in range(8):
        rg = range(18 * b, 18 * b + 18)
        f = sum(int(F[rg].sum()) for F, _ in dias)
        e = sum(int(ev[rg].sum()) for _, ev in dias)
        franjas[f"{3 * b:02d}-{3 * b + 2:02d} UTC"] = {"disparos": f, "evaluados": e, "tasa": _r(f / e) if e else None}
    return {"global": nF / nE if nE else None, "media_por_dia": float(np.mean(fr)) if fr else None,
            "disparos": nF, "evaluados": nE, "noche": per["noche"], "dia": per["dia"], "franjas": franjas}


def veredicto_b(m24, m25):
    g, md = m24["global"], m24["media_por_dia"]
    if g > FA_MAL or md > FA_MAL:
        return "NO AGUANTA"
    fr_ok = all(v["tasa"] is None or v["tasa"] <= max(FRANJA_MAX, m25["franjas"][k]["tasa"] or 0.0)
                for k, v in m24["franjas"].items())
    if g <= FA_MAX and md <= FA_MAX and fr_ok:
        return "AGUANTA"
    return "DEGRADA"


def por_dia_periodo(dias, rg):
    return np.array([(int(F[rg].sum()), int(ev[rg].sum())) for F, ev in dias])


def bootstrap_R(d24, d25):
    """R = tasa 2024 / tasa 2025 e IC 95 % por remuestreo de días dentro de cada año (S28a)."""
    rng = np.random.default_rng(SEMILLA)
    f24, e24 = d24.sum(0)
    f25, e25 = d25.sum(0)
    R = (f24 / e24) / (f25 / e25) if e24 and e25 and f25 else np.nan
    rs = np.empty(N_BOOT)
    for i in range(N_BOOT):
        a = d24[rng.integers(0, len(d24), len(d24))].sum(0)
        b = d25[rng.integers(0, len(d25), len(d25))].sum(0)
        rs[i] = (a[0] / a[1]) / (b[0] / b[1]) if a[1] and b[1] and b[0] else np.inf
    lo, hi = np.percentile(rs, [2.5, 97.5])
    return float(R), float(lo), float(hi)


def veredicto_c(R, lo, hi, e24):
    if e24 < MIN_EV_PERIODO:
        return "NO DECIDIBLE"
    if R >= R_SUBE and lo > 1:
        return "NO AGUANTA (sube)"
    if R < R_SUBE and lo > 1:
        return "SUBE POCO"
    if hi < 1:
        return "MÁS ESTRICTO"
    if R <= R_SUBE:
        return "AGUANTA"
    return "NO CONCLUYENTE"


def lectura_d(R, lo, hi, r_antuco):
    if hi < r_antuco:
        return "LA SUBIDA DIURNA ES DE 2026"
    if R >= R_SUBE and lo > 1:
        return "EL DÍA VARÍA ENTRE AÑOS"
    return "NO CONCLUYENTE"


def periodos(d24, d25):
    out = {}
    for nom, rg in (("noche", NOCHE), ("dia", DIA)):
        a, b = por_dia_periodo(d24, rg), por_dia_periodo(d25, rg)
        R, lo, hi = bootstrap_R(a, b)
        f24, e24 = a.sum(0)
        f25, e25 = b.sum(0)
        out[nom] = {"2024": [int(f24), int(e24)], "tasa_2024": _r(f24 / e24) if e24 else None,
                    "2025": [int(f25), int(e25)], "tasa_2025": _r(f25 / e25) if e25 else None,
                    "R": _r(R), "IC95": [_r(lo), _r(hi)], "veredicto": veredicto_c(R, lo, hi, e24),
                    "tasa_2024_sobre_5pct": bool(e24 and f24 / e24 > 0.05)}
    return out


def top_dias(dias, n=5):
    tot = sum(int(F.sum()) for F, _ in dias)
    orden = sorted(range(len(dias)), key=lambda d: -int(dias[d][0].sum()))[:n]
    return {"dias": [{"dia": f"{T0 + timedelta(days=d):%Y-%m-%d}", "disparos": int(dias[d][0].sum()),
                      "evaluados": int(dias[d][1].sum()),
                      "horas": [M.hhmm(s) for s in np.flatnonzero(dias[d][0])][:40]} for d in orden],
            "fraccion_top": _r(sum(int(dias[d][0].sum()) for d in orden) / tot) if tot else None}


def pares(dias, Px):
    """Cuántas veces cada píxel de la zona entra en el par de un disparo."""
    c = np.zeros(len(Z.ZONA), int)
    for d, (F, _) in enumerate(dias):
        for s in np.flatnonzero(F):
            for j in Px[d, s]:
                if j >= 0:
                    c[j] += 1
    return {f"{divmod(int(Z.ZONA[j]), M.NX)}": int(c[j]) for j in range(len(Z.ZONA))}


# ---------- geometría (criterio §2) ----------
def geometria(acm24, acm25):
    bt24 = np.load(SB._npy24("bt11"), mmap_mode="r")
    bt25 = np.load(S._npy("bt11"), mmap_mode="r")
    e24, e25 = H24.despejada("chillan", acm24), H24.despejada("chillan", acm25)

    def media(bt, e1, nd):
        sel = [(d, s) for d in range(nd) for s in NOCHE if e1[d, s] and np.isfinite(bt[d, s]).any()]
        return np.nanmean(np.array([np.asarray(bt[d, s]) for d, s in sel]), 0), len(sel)
    m24, n24 = media(bt24, e24, ND)
    m25, n25 = media(bt25, e25, S.NR)
    cerca = (C29.DIST.ravel() < G2_KM) & np.isfinite(m24) & np.isfinite(m25)
    g2 = float(np.corrcoef(m24[cerca], m25[cerca])[0, 1])
    f24, f25 = m24.reshape(M.NY, M.NX), m25.reshape(M.NY, M.NX)
    cy, cx = 42, 46
    k = G3_CAJA
    best = (np.inf, 0.0, 0.0)
    pasos = np.round(np.arange(-1.0, 1.0001, 0.05), 2)
    for dy in pasos:
        for dx in pasos:
            sh = ndimage.shift(f24, (dy, dx), order=1, mode="nearest")
            a = sh[cy - k:cy + k + 1, cx - k:cx + k + 1]
            b = f25[cy - k:cy + k + 1, cx - k:cx + k + 1]
            ok = np.isfinite(a) & np.isfinite(b)
            dd = a[ok] - b[ok]
            e = float(np.mean((dd - dd.mean()) ** 2))
            if e < best[0]:
                best = (e, float(dy), float(dx))
    sh0 = f24[cy - k:cy + k + 1, cx - k:cx + k + 1] - f25[cy - k:cy + k + 1, cx - k:cx + k + 1]
    e0 = float(np.nanmean((sh0 - np.nanmean(sh0)) ** 2))
    cub = json.load(open(os.path.join(TRAB, "cubo_2024.json"), encoding="utf-8"))
    g4 = (cub["cobertura_l1b"] >= 0.90 and cub["cobertura_acm"] >= 0.90 and cub["bt11_en_rango"] >= 0.999
          and cub["congelados"] == 0)
    at = json.load(open(os.path.join(RES, "geometria_atributos.json"), encoding="utf-8"))
    g1 = all(at["goes16_2024"][x] == at["goes19_2025"][x] for x in at["goes16_2024"] if x != "archivo")
    zona_frio = {"2024": int(Z.ZONA[np.nanargmin(m24[Z.ZONA])]), "2025": int(Z.ZONA[np.nanargmin(m25[Z.ZONA])])}
    out = {"G1_atributos_iguales": g1, "G2_correlacion": _r(g2), "G2_pixeles": int(cerca.sum()),
           "G2_noches_2024": n24, "G2_noches_2025": n25,
           "G3_corrimiento_px": {"dy": best[1], "dx": best[2]}, "G3_error_cuadratico": {"mejor": _r(best[0]),
                                                                                         "sin_corrimiento": _r(e0)},
           "G4_cubo": {k2: cub[k2] for k2 in ("cobertura_l1b", "cobertura_acm", "bt11_en_rango", "congelados",
                                              "scan_distinto_descartados")},
           "pixel_mas_frio_de_la_zona": zona_frio,
           "bt11_dif_mediana_zona_2024_menos_2025": _r(np.nanmedian(m24[Z.ZONA] - m25[Z.ZONA]))}
    falla = [g for g, ok in (("G1", g1), ("G2", g2 >= G2_MIN),
                             ("G3", abs(best[1]) <= G3_MAX and abs(best[2]) <= G3_MAX), ("G4", g4)) if not ok]
    out["falla"] = falla
    out["veredicto_a"] = "COMPARABLE" if not falla else "INVÁLIDA para la zona"
    return out, (e24, e25)


def btd_zona_informativa(btd24, e24, Zr):
    """BTD media de noches despejadas: zona y controles de su cota, 2024 menos 2025 (informativo)."""
    e25 = H24.despejada("chillan", Zr.acm25)

    def media(btd, e1, nd):
        sel = [(d, s) for d in range(nd) for s in NOCHE if e1[d, s] and np.isfinite(btd[d, s, Z.ZONA[0]])]
        return np.nanmean(np.array([np.asarray(btd[d, s]) for d, s in sel]), 0)
    m24, m25 = media(btd24, e24, ND), media(Zr.btd25, e25, Z.NR)
    ctrl = np.unique(np.concatenate([Z.CTRL[i] for i in Z.CTRL_P]))
    return {"btd_zona_dif_mediana": _r(np.nanmedian(m24[Z.ZONA] - m25[Z.ZONA])),
            "btd_controles_cota_dif_mediana": _r(np.nanmedian(m24[ctrl] - m25[ctrl])),
            "btd_zona_dif_por_pixel": {f"{divmod(int(p), M.NX)}": _r(m24[p] - m25[p]) for p in Z.ZONA}}


# ---------- pruebas (criterio §3) ----------
def _seco_2025(Zr, D25, p):
    _pct(p, D25)
    ULz = [Z.umbral(Zr.SR, excl=d) for d in range(Z.NR)]
    dz = dias_zona(Zr.SR, lambda d: ULz[d])
    da = dias_anillo(D25.SR, D25.KR, lambda d: D25.umbral(d)[0])
    return {"z": dz, "a": da, "u": unir(da, dz)}


def pruebas(Zr=None, D25=None):
    t = time.time()
    Zr = Zr or Zona25()
    D25 = D25 or S.Detector(ref="2025", con_blanco=False)
    # el camino fuera de muestra, con la base de cada día sin sí mismo, reproduce el S de 2025
    Sx, Px, G, _ = aplicar_zona(Zr.btd25, Zr.acm25, Zr.est25, Zr.BZ, Zr.bctrl)
    assert np.array_equal(np.isfinite(Sx), np.isfinite(Zr.SR)), "evaluados distintos"
    assert np.array_equal(Sx[np.isfinite(Sx)], Zr.SR[np.isfinite(Zr.SR)]), "S distinto"
    assert np.array_equal(Px, Zr.PR)
    s5 = _seco_2025(Zr, D25, P_ZONA)
    m = medidas(s5["z"])
    assert (m["disparos"], m["evaluados"]) == REPRO["zona5"], (m["disparos"], m["evaluados"])
    s475 = _seco_2025(Zr, D25, P_UNION)
    m = medidas(s475["u"])
    assert (m["disparos"], m["evaluados"]) == REPRO["union475"], (m["disparos"], m["evaluados"])
    assert m["noche"] == REPRO["union475_noche"] and m["dia"] == REPRO["union475_dia"], (m["noche"], m["dia"])
    # veredictos
    m25 = {"franjas": {"a": {"tasa": 0.12}}}
    assert veredicto_b({"global": 0.04, "media_por_dia": 0.04, "franjas": {"a": {"tasa": 0.11}}}, m25) == "AGUANTA"
    assert veredicto_b({"global": 0.04, "media_por_dia": 0.04, "franjas": {"a": {"tasa": 0.13}}}, m25) == "DEGRADA"
    assert veredicto_b({"global": 0.04, "media_por_dia": 0.11, "franjas": {}}, m25) == "NO AGUANTA"
    assert veredicto_c(2.0, 1.1, 3, 400) == "NO AGUANTA (sube)" and veredicto_c(1.2, 1.05, 2, 400) == "SUBE POCO"
    assert veredicto_c(0.4, 0.1, 0.9, 400) == "MÁS ESTRICTO" and veredicto_c(1.2, 0.5, 3, 400) == "AGUANTA"
    assert veredicto_c(2.0, 0.8, 5, 400) == "NO CONCLUYENTE" and veredicto_c(1, 0.5, 2, 200) == "NO DECIDIBLE"
    assert lectura_d(1.0, 0.5, 2.0, 2.64) == "LA SUBIDA DIURNA ES DE 2026"
    assert lectura_d(2.0, 1.2, 4.0, 2.64) == "EL DÍA VARÍA ENTRE AÑOS"
    assert lectura_d(1.6, 0.8, 4.0, 2.64) == "NO CONCLUYENTE"
    print(f"pruebas OK en {time.time() - t:.0f} s", flush=True)
    return s5, s475


# ---------- medir ----------
def medir():
    t = time.time()
    Zr = Zona25()
    D25 = S.Detector(ref="2025", con_blanco=False)
    s5, s475 = pruebas(Zr, D25)
    print(f"2025 y pruebas en {time.time() - t:.0f} s", flush=True)
    btd24 = np.load(os.path.join(TRAB, "r24_btd.npy"))
    acm24 = np.load(os.path.join(TRAB, "r24_acm.npy"))
    acm24_s25b = np.load(SB._npy24("acm"))
    assert np.array_equal(acm24, acm24_s25b), "el ACM de 2024 no coincide con el cubo de S25b"
    geo, (e24, _) = geometria(acm24, Zr.acm25)
    print("geometría:", json.dumps(geo, ensure_ascii=False), flush=True)
    out = {"criterio": "criterio_2026-11-25.md (afd2923)", "a_geometria": geo}
    if geo["falla"]:
        out["veredicto"] = "INVÁLIDA para la zona: no se mide (b) ni (c)"
        json.dump(out, open(os.path.join(RES, "s29b_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False,
                  indent=1)
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return
    out["a_btd_informativa"] = btd_zona_informativa(btd24, e24, Zr)
    hay24 = np.isfinite(btd24[:, :, Z.ZONA[0]])
    est24 = Z.costumbre(acm24, hay24)
    D24 = SB._detector_2024()
    m124 = np.load(SB._npy24("m1"))
    B0 = D25.base(None)
    out["costumbre_zona_vs_anillo_2024_iguales"] = bool(np.array_equal(est24, D24.ESTAT))
    vers = {}
    for nom_est, est_z, est_a in (("costumbre_2024", est24, D24.ESTAT), ("costumbre_2025", Zr.est25, D25.ESTAT)):
        S24z, P24z, Gz, FDz = aplicar_zona(btd24, acm24, est_z, Zr.bz, Zr.bctrl)
        Sa, Ka, Ga, FDa = SB.aplicar(D25, acm24, m124, est_a, lambda d: B0)
        res = {}
        for nom, p, ref in (("zona_5", P_ZONA, s5["z"]), ("union_475", P_UNION, s475["u"]),
                            ("zona_475", P_UNION, s475["z"]), ("anillo_475", P_UNION, s475["a"])):
            _pct(p, D25)
            Uz = Z.umbral(Zr.SR)
            Ua, _ = D25.umbral(None)
            dz = dias_zona(S24z, lambda d: Uz)
            da = dias_anillo(Sa, Ka, lambda d: Ua)
            dias = {"zona_5": dz, "zona_475": dz, "anillo_475": da, "union_475": unir(da, dz)}[nom]
            m24, m25 = medidas(dias), medidas(ref)
            r = {"2024": m24, "2025": {k: m25[k] for k in ("global", "media_por_dia", "disparos", "evaluados",
                                                           "noche", "dia")},
                 "franjas_2025": m25["franjas"], "veredicto_b": veredicto_b(m24, m25),
                 "mas_estricto": bool(m24["global"] < ESTRICTO and m24["media_por_dia"] < ESTRICTO),
                 "c_periodos": periodos(dias, ref), "top_dias": top_dias(dias),
                 "racimo_16_18nov2024": int(sum(int(dias[d][0].sum()) for d in (56, 57, 58))),
                 "por_dia": [{"dia": f"{T0 + timedelta(days=d):%Y-%m-%d}", "disparos": int(F.sum()),
                              "evaluados": int(ev.sum())} for d, (F, ev) in enumerate(dias)]}
            if nom.startswith("zona"):
                r["pares_pixeles_2024"] = pares(dz, P24z)
                r["pares_pixeles_2025"] = pares(ref, Zr.PR)
            if nom in ("union_475", "zona_475"):
                parte = "union" if nom == "union_475" else "zona"
                dd = r["c_periodos"]["dia"]
                r["d_contra_antuco"] = {"R_antuco_2026": R_ANTUCO[parte], "R_2024": dd["R"], "IC95": dd["IC95"],
                                        "lectura": lectura_d(dd["R"], dd["IC95"][0], dd["IC95"][1], R_ANTUCO[parte])}
            res[nom] = r
            print(f"{nom_est} {nom}: global {m24['global']:.4f}, media por día {m24['media_por_dia']:.4f}, "
                  f"{r['veredicto_b']}; noche {r['c_periodos']['noche']['veredicto']}, "
                  f"día {r['c_periodos']['dia']['veredicto']}", flush=True)
        res["compuerta"] = {"zona_frac_pasa": _r(np.nanmean(Gz[(acm24 != 255).any(2)])),
                            "anillo_frac_pasa": _r(np.nanmean(Ga[(acm24 != 255).any(2)])),
                            "nube_dinamica_mediana_zona": _r(np.nanmedian(FDz))}
        vers[nom_est] = res
    out["b_c_d"] = vers
    out["umbral_zona_5_por_hora"] = None
    _pct(P_ZONA, D25)
    Uz5 = Z.umbral(Zr.SR)
    out["umbral_zona_5_por_hora"] = {M.hhmm(s): _r(Uz5[s]) if Uz5[s] is not None else None for s in range(0, 144, 6)}
    v = vers["costumbre_2024"]
    out["veredicto"] = {"zona_S25a": v["zona_5"]["veredicto_b"], "union_S26a": v["union_475"]["veredicto_b"],
                        "zona_noche": v["zona_5"]["c_periodos"]["noche"]["veredicto"],
                        "zona_dia": v["zona_5"]["c_periodos"]["dia"]["veredicto"],
                        "union_noche": v["union_475"]["c_periodos"]["noche"]["veredicto"],
                        "union_dia": v["union_475"]["c_periodos"]["dia"]["veredicto"],
                        "d_union": v["union_475"]["d_contra_antuco"]["lectura"],
                        "d_zona": v["zona_475"]["d_contra_antuco"]["lectura"]}
    out["segundos"] = round(time.time() - t)
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "s29b_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1, default=int)
    print(json.dumps(out["veredicto"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    {"pruebas": pruebas, "medir": medir}[sys.argv[1]]()
