r"""S24: diagnósticos del detector S23b. Implementa criterio_2026-11-25.md (commit 5c83319, empujado antes de medir).

Pregunta A: ¿la pluma del 14-11 tiene firma en 11 menos 12 µm dentro de la huella de VOLCAT, y a qué distancia del
cráter? Compara la media de (M1 menos la base de 2025) en los píxeles de la huella con lo que esos mismos píxeles dan
en los cuadros de 2025 a la misma hora. Control positivo el 08-11 y negativo con la huella girada 180°.
Pregunta B: ¿por qué 2026 dispara menos que 2025 de noche? Concentración de los disparos de 2025 en pocas noches,
qué tienen esas noches y la distribución de S en cada año.

Regla: la de S23b (base y umbral de 2025, nublado de costumbre de 2026 congelado), con s23_medir.py sin cambios.
Uso: python -I s24_medir.py pruebas | medir
"""
import hashlib
import json
import os
import sys

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "s23_fondo_2025", "scripts"))
import s23_medir as S  # noqa: E402
B, M, C29 = S.B, S.M, S.C29

ESTAT = r"D:\goes_notas\s23\s23b\estat_2026.npy"
SHA_ESTAT = "e0f093eb6e441cc4"
PNG_DIRS = [r"D:\goes_notas\s23\volcat_png\Chile_Central_2_km\frames",
            r"D:\goes_notas\s22\volcat_png\Chile_Central_2_km\frames",
            r"D:\goes_notas\s22\s22b\volcat_png\frames",
            r"D:\goes_notas\volcat_validacion_copia_2026-11-21\Chile_Central_2_km\frames"]
BANDAS = {"4-8 km": (4.0, 8.0), "8-15 km": (8.0, 15.0), "15-40 km": (15.0, 40.01), "anillo": (4.0, 40.01)}
MIN_PIX, MIN_CUADROS = 3, 5
Q_SENAL, Q_MITAD, Q_DEBIL = 0.05, 0.10, 0.20
NOCHE = range(0, 54)                      # 00:00 a 08:50 UTC
COMUN_MAX = 3                             # noche común: menos de 3 disparos
TOP, TOP_FRAC, P_B2 = 5, 0.60, 0.01


# ---------- piezas puras (con prueba) ----------
def giro_180():
    """Índice (en AP) del píxel del anillo más cercano al punto opuesto respecto del cráter."""
    ox, oy = -M.AX, -M.AY
    d2 = (M.AX[None, :] - ox[:, None]) ** 2 + (M.AY[None, :] - oy[:, None]) ** 2
    return np.argmin(d2, 1)


def veredicto_banda(qs):
    qs = [q for q in qs if q is not None and np.isfinite(q)]
    if len(qs) < MIN_CUADROS:
        return "SIN DATO"
    med = float(np.median(qs))
    if med <= Q_SENAL and np.mean(np.array(qs) <= Q_MITAD) >= 0.5:
        return "SEÑAL"
    if med <= Q_DEBIL:
        return "DÉBIL"
    return "SIN SEÑAL"


def media_sel(v, sel):
    x = v[sel]
    x = x[np.isfinite(x)]
    return float(x.mean()) if len(x) >= MIN_PIX else np.nan


def pruebas():
    g = giro_180()
    assert g.shape == (M.NA,)
    # el giro de un píxel cae del lado opuesto (acimut a 180° ± 30°) y a distancia parecida
    az = (np.degrees(np.arctan2(M.AX, M.AY)) + 360) % 360
    dd = np.abs(((az[g] - az + 180) % 360) - 180)
    assert np.median(np.abs(dd - 180)) < 15, np.median(np.abs(dd - 180))
    assert np.median(np.abs(M.AD[g] - M.AD)) < 2.0
    assert veredicto_banda([0.01] * 6) == "SEÑAL"
    assert veredicto_banda([0.04, 0.04, 0.04, 0.5, 0.5, 0.5]) == "SIN SEÑAL"   # mediana 0,27
    assert veredicto_banda([0.1, 0.15, 0.15, 0.3, 0.3]) == "DÉBIL"
    assert veredicto_banda([0.01, 0.01, 0.2, 0.2, 0.2]) == "DÉBIL"             # mediana 0,2: no es SEÑAL
    assert veredicto_banda([0.01] * 4) == "SIN DATO"
    assert np.isnan(media_sel(np.array([1.0, np.nan, 2.0]), np.array([True, True, True])))
    assert media_sel(np.array([1.0, 2.0, 3.0, 9.0]), np.array([True, True, True, False])) == 2.0
    print("pruebas OK")


# ---------- huella de VOLCAT en la grilla ABI ----------
def png_de(dia, s):
    pre = f"{dia}_{M.hhmm(s).replace(':', '-')}"
    for c in PNG_DIRS:
        if os.path.isdir(c):
            for f in os.listdir(c):
                if f.startswith(pre) and f.endswith(".png") and "_annot" not in f:
                    return os.path.join(c, f)
    return None


def huella(dia, s):
    fn = png_de(dia, s)
    if fn is None:
        return None
    ok, mid, barra = C29.decodifica_png(fn)
    if not barra:
        return None
    ash, _ = C29.a_abi(ok, mid)
    return ash.ravel()[M.AP]


# ---------- pregunta A ----------
def pregunta_a(D, B0, dia):
    d = B.dia_idx(dia)
    rot = giro_180()
    filas = []
    for s in np.flatnonzero((D.CLT[d] == "P") & D.GATET[d]):
        fp = huella(dia, s)
        if fp is None:
            filas.append({"hora": M.hhmm(s), "sin_png": True})
            continue
        fr = np.zeros(M.NA, bool)
        fr[rot[fp]] = True
        v = D.mmT[d, s] - B0[s]
        nulos = [(dd, x) for dd in D.DIASR for x in range(144) if M.dslot(x, s) <= S.W_AZAR and D.GATER[dd, x]]
        W = np.array([D.mmR[dd, x] - D.base(dd)[x] for dd, x in nulos])
        fila = {"hora": M.hhmm(s), "S": S._r(D.ST[d, s]), "k": int(D.KT[d, s]), "n_huella_anillo": int(fp.sum()),
                "n_nulo": len(nulos)}
        for nom, (a, b) in BANDAS.items():
            banda = (M.AD >= a) & (M.AD < b)
            for etiq, sel in (("huella", fp & banda), ("giro", fr & banda)):
                H = media_sel(v, sel)
                if np.isfinite(H):
                    Hn = np.array([media_sel(w, sel) for w in W])
                    Hn = Hn[np.isfinite(Hn)]
                    q = float(np.mean(Hn <= H)) if len(Hn) >= 20 else np.nan
                else:
                    q = np.nan
                fila[f"{etiq} {nom}"] = {"n_pix": int(sel.sum()), "H": S._r(H), "q": S._r(q)}
        filas.append(fila)
    ver = {}
    for etiq in ("huella", "giro"):
        for nom in BANDAS:
            qs = [f[f"{etiq} {nom}"]["q"] for f in filas if f"{etiq} {nom}" in f]
            qs = [q for q in qs if q is not None]
            ver[f"{etiq} {nom}"] = {"veredicto": veredicto_banda(qs), "cuadros": len(qs),
                                    "mediana_q": S._r(np.median(qs)) if qs else None,
                                    "frac_q_le_0.10": S._r(np.mean(np.array(qs) <= Q_MITAD)) if qs else None}
    return {"dia": dia, "cuadros_P_con_compuerta": len(filas), "veredictos": ver, "cuadros": filas}


# ---------- pregunta B ----------
def pregunta_b(D, U0):
    bt = np.load(S._npy("bt11"), mmap_mode="r")
    ap, ct = M.AP, M.CTRL
    n25, f25, rows = {}, {}, []
    for d in D.DIASR:
        Ud, _ = D.umbral(d)
        F, ev = S.disparos(D.SR, D.KR, d, Ud)
        sl = [s for s in NOCHE if ev[s]]
        n25[d], f25[d] = len(sl), int(sum(F[s] for s in sl))
        for s in sl:
            b = np.asarray(bt[d, s])
            rows.append({"F": bool(F[s]), "FD": float(D.FDR[d, s]), "acm1": float((D.acmR[d, s][ap] == 1).mean()),
                         "inv": float(np.nanmedian(b[ap]) - np.nanmedian(b[ct])), "bt_ctrl": float(np.nanmedian(b[ct])),
                         "k": int(D.KR[d, s])})
    n26, f26, k26 = 0, 0, []
    por_noche_26 = {}
    for d in range(B.ND):
        F, ev = S.disparos(D.ST, D.KT, d, U0)
        sl = [s for s in NOCHE if ev[s]]
        n26 += len(sl)
        f = int(sum(F[s] for s in sl))
        f26 += f
        k26 += [int(D.KT[d, s]) for s in sl if F[s]]
        if f:
            por_noche_26[B.fecha(d)] = f
    tot25 = sum(f25.values())
    orden = sorted(f25, key=lambda d: -f25[d])
    top = orden[:TOP]
    frac_top = sum(f25[d] for d in top) / tot25 if tot25 else None
    com = [d for d in D.DIASR if f25[d] < COMUN_MAX]
    nc, fc = sum(n25[d] for d in com), sum(f25[d] for d in com)
    p_fisher = float(stats.fisher_exact([[fc, nc - fc], [f26, n26 - f26]], alternative="two-sided")[1])
    epis = bool(frac_top is not None and frac_top >= TOP_FRAC and p_fisher > 0.05)
    b2 = {}
    Fv = np.array([r["F"] for r in rows])
    for c in ("FD", "acm1", "inv", "bt_ctrl"):
        x = np.array([r[c] for r in rows])
        a, b = x[Fv & np.isfinite(x)], x[~Fv & np.isfinite(x)]
        p = float(stats.mannwhitneyu(a, b, alternative="two-sided")[1]) if len(a) and len(b) else None
        b2[c] = {"mediana_disparan": S._r(np.median(a)) if len(a) else None, "mediana_no": S._r(np.median(b)),
                 "dif": S._r(np.median(a) - np.median(b)) if len(a) else None, "p": p,
                 "asociado": bool(p is not None and p <= P_B2)}

    def cuant(Sm, gate, acm):
        v = np.concatenate([Sm[d, list(NOCHE)] for d in range(Sm.shape[0])])
        v = v[np.isfinite(v)]
        hay = np.array([[(acm[d, s] != 255).any() for s in NOCHE] for d in range(acm.shape[0])])
        g = gate[:, list(NOCHE)]
        return {"p5": S._r(np.percentile(v, 5)), "p25": S._r(np.percentile(v, 25)), "p50": S._r(np.percentile(v, 50)),
                "n": int(len(v)), "frac_pasan_compuerta": S._r(g[hay].mean())}

    return {"B1": {"disparos_noche_2025": tot25, "evaluados_noche_2025": sum(n25.values()),
                   "tasa_2025": S._r(tot25 / max(sum(n25.values()), 1)),
                   "disparos_noche_2026": f26, "evaluados_noche_2026": n26, "tasa_2026": S._r(f26 / max(n26, 1)),
                   "top_noches_2025": [{"dia": f"{S.T0R + S.timedelta(days=d):%Y-%m-%d}", "disparos": f25[d],
                                        "evaluados": n25[d]} for d in orden[:10]],
                   "frac_top5": S._r(frac_top), "noches_comunes_2025": len(com), "evaluados_comunes": nc,
                   "disparos_comunes": fc, "tasa_comunes_2025": S._r(fc / max(nc, 1)), "p_fisher_comunes_vs_2026": p_fisher,
                   "veredicto": "EPISÓDICO" if epis else "NO EPISÓDICO", "noches_2026_con_disparo": por_noche_26},
            "B2": b2,
            "B2_tajadas": {"2025": np.bincount([r["k"] for r in rows if r["F"]], minlength=12).tolist(),
                           "2026": np.bincount(k26, minlength=12).tolist()},
            "B3": {"2025": cuant(D.SR, D.GATER, D.acmR), "2026": cuant(D.ST, D.GATET, D.acmT)}}


def medir():
    estat = np.load(ESTAT)
    assert hashlib.sha256(estat.tobytes()).hexdigest()[:16] == SHA_ESTAT, "estat_2026 cambió"
    D = S.Detector(ref="2025", con_blanco=True, estat_blanco=estat)
    B0 = D.base(None)
    U0, _ = D.umbral(None)
    out = {"criterio": "criterio_2026-11-25.md (5c83319)"}
    out["A_14-11"] = pregunta_a(D, B0, "2026-11-14")
    out["A_control_08-11"] = pregunta_a(D, B0, "2026-11-08")
    v08 = out["A_control_08-11"]["veredictos"]["huella anillo"]["veredicto"]
    out["A_valida"] = v08 == "SEÑAL"
    out["B"] = pregunta_b(D, U0)
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "s24_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    res = {k: (v["veredictos"] if isinstance(v, dict) and "veredictos" in v else v) for k, v in out.items()}
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    {"pruebas": pruebas, "medir": medir}[sys.argv[1]]()
