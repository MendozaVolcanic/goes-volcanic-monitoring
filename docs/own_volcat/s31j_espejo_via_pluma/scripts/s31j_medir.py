r"""S31j: espejo de la vía pluma/bocanada de VOLCAT. Implementa criterio_2026-11-27.md de esta carpeta (commit e29dd33,
empujado antes de calcular un solo cuadro del espejo y una sola VRP).

Por qué: VOLCAT publica la pluma de Nevados de Chillán por la vía ASHPLUMEPUFF sin firma de ceniza en el píxel (H15,
H16, H20a) y casi siempre como continuación (H28). Si esa vía es "volcán con calor + objeto débil pegado al cráter +
seguir lo que se movió", un espejo con esas piezas debería publicar los mismos cuadros. Aquí se arma el espejo con lo
público (cabecera de los registros geocatASHOBJ, SECO Parte 2 Tabla 4, H28) y se mide su parecido con VOLCAT en 2026 y
su falsa alarma en 2025 y 2024.

Todo lo de los detectores previos se importa sin cambios (s23_medir, s25b_medir, s26a_medir, s30b_medir, s31c_medir,
s31e_medir). El indicador de calor es el validado de docs/own_volcat/vrp_nocturno (vn_comun, vn_medir), leído sobre los
cuadros que bajó s31j_bajar_calor.py. Lee los PNG de VOLCAT para el solape de huella (licencia SSEC: nada de eso va al
repo). Escribe resultados/s31j_resultado.json y resultados/s31j_por_cuadro.csv (sólo cifras) y en
D:\goes_notas\s31\s31j\ los cubos de z y las tablas de calor.

Uso: python -I -B s31j_medir.py pruebas | medir
"""
import csv
import hashlib
import json
import os
import shutil
import sys
import time
import warnings
from datetime import datetime, timedelta

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

os.environ["VN_DIR"] = r"D:\goes_notas\s31\s31j\calor"     # antes de importar vn_comun
sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
for sub in ("s23_fondo_2025", "s25b_fondo_2024", "s26a_combinado", "s31d_sesgo_se", "s31c_dos_coronas",
            "s31e_anillo_pixel", os.path.join("vrp_nocturno")):
    sys.path.insert(0, os.path.join(OV, sub, "scripts"))
import s23_medir as S  # noqa: E402
import s26a_medir as A26  # noqa: E402
import s31c_medir as C31  # noqa: E402
import s31e_medir as E31  # noqa: E402
B, M = S.B, S.M
S30 = C31.S30
assert C31.M is M and E31.M is M and A26.B is B

TRAB = r"D:\goes_notas\s31\s31j"
CORONA_S31H = r"D:\goes_notas\s31\s31h\corona_T1.npz"
NOCHES_VAL = os.path.join(OV, "vrp_nocturno", "resultados", "noches.csv")
MIN_LIBRE_GB = 6.0

# ---------- parámetros del criterio ----------
ANCLA_KM = 10.0                                   # §2 (a) 2
MIN_PIX = 1                                       # §2 (a) 3
VEL_KM_S = 0.05                                   # §2 (b), H28
DT_MAX = 3                                        # §2 (b): Δt <= 30 min (3 pasos de 10 min)
HIST_DIAS = 15                                    # §2 (a) 1
C_GRID = [-1.0 - 0.25 * i for i in range(10)]     # §3: -1,00 a -3,25
FA_DIA, FA_GLOBAL = E31.FA_CONG_DIA, E31.FA_CONG_GLOBAL
C_CONT_S1 = -1.2815515655446004                   # §5: Φ⁻¹(0,10)
SENS_MIN, FA_MAX = 0.50, 0.10                     # §7
P_MAX = 0.01
B_NULO, SEMILLA, N_BOOT = 9999, 0, 10_000
ENUM_MAX, MIN_CONF = 20000, 1000
T0_25, T0_26 = datetime(2025, 9, 21), B.M.T0
NOCHE_SLOTS = range(0, 72)                        # 00:00 a 11:50 UTC

NA = M.NA
AX, AY, AD = M.AX, M.AY, M.AD
NY, NX = M.NY, M.NX
AP2 = np.unravel_index(M.AP, (NY, NX))
K8 = np.ones((3, 3), int)


# ---------- el espejo (§2) ----------
def objetos(z, c):
    """Componentes conexas (8 vecinos) de píxeles del anillo con z <= c. Lista de arreglos de posiciones 0..NA-1."""
    cand = np.isfinite(z) & (z <= c)
    if not cand.any():
        return []
    g = np.zeros((NY, NX), bool)
    g[AP2[0][cand], AP2[1][cand]] = True
    lab, n = ndimage.label(g, K8)
    la = lab[AP2]
    return [np.flatnonzero(la == k) for k in range(1, n + 1)]


def dist_min(obj, arbol):
    d, _ = arbol.query(np.c_[AX[obj], AY[obj]])
    return float(d.min())


def espejo(Z, evaluable, calor, c, c_cont=None):
    """Corre el espejo en orden de tiempo sobre (nd, 144). Devuelve pub (bool), tipo (0 nada, 1 nacimiento,
    2 sólo continuación) y huella del espejo {(d, s): posiciones}."""
    nd = Z.shape[0]
    c_cont = c if c_cont is None else c_cont
    pub = np.zeros((nd, 144), bool)
    tipo = np.zeros((nd, 144), np.int8)
    hue = {}
    i_prev, F_prev = None, np.array([], int)
    for i in range(nd * 144):
        d, s = divmod(i, 144)
        if not evaluable[d, s]:
            continue
        z = Z[d, s]
        F, nac = [], False
        obs = objetos(z, c)
        if calor[d, s]:
            for o in obs:
                if len(o) >= MIN_PIX and AD[o].min() <= ANCLA_KM:
                    F.append(o)
                    nac = True
        if i_prev is not None and len(F_prev) and (i - i_prev) <= DT_MAX:
            radio = VEL_KM_S * 600.0 * (i - i_prev)
            arb = cKDTree(np.c_[AX[F_prev], AY[F_prev]])
            for o in (obs if c_cont == c else objetos(z, c_cont)):
                if dist_min(o, arb) <= radio:
                    F.append(o)
        if F:
            Fu = np.unique(np.concatenate(F))
            pub[d, s] = True
            tipo[d, s] = 1 if nac else 2
            hue[(d, s)] = Fu
        else:
            Fu = np.array([], int)
        i_prev, F_prev = i, Fu
    return pub, tipo, hue


# ---------- calor (§2 (a) 1) ----------
def calor_noches():
    """Noches de Chillán con el indicador validado, sobre los cuadros bajados por s31j_bajar_calor.py."""
    import vn_medir as VM
    assert VM.K.OUT == os.environ["VN_DIR"], VM.K.OUT
    df = VM.cuadros()
    df = df[df.sitio == "Nevados de Chillan"]
    df = VM.visibilidad(df)
    no = VM.noches(df)
    no = no[no.sitio == "Nevados de Chillan"].copy()
    no["noche"] = no.noche.astype(str)
    return df, no


def compuerta_calor(no, t0, nd):
    """(nd, 144) bool: algún indicador encendido en las 15 noches anteriores (§2 (a) 1)."""
    enc = {r.noche for r in no.itertuples() if bool(r.enc)}
    G = np.zeros((nd, 144), bool)
    for d in range(nd):
        dia = (t0 + timedelta(days=d)).date()
        for s in range(144):
            hi = 0 if s >= 66 else 1
            G[d, s] = any(f"{dia - timedelta(days=k)}" in enc for k in range(hi, HIST_DIAS + hi))
    return G


# ---------- medidas ----------
def boot_media(v, rng):
    v = np.asarray(v, float)
    if not len(v):
        return float("nan"), [float("nan")] * 2
    xs = v[rng.integers(0, len(v), (N_BOOT, len(v)))].mean(1)
    return float(v.mean()), [float(x) for x in np.percentile(xs, [2.5, 97.5])]


def fa_anual(pub, ev, rng=None):
    por = [(int(pub[d][ev[d]].sum()), int(ev[d].sum())) for d in range(pub.shape[0]) if ev[d].any()]
    fr = [a / b for a, b in por]
    out = {"media_dia": float(np.mean(fr)) if fr else float("nan"),
           "global": sum(a for a, _ in por) / max(sum(b for _, b in por), 1),
           "dias": len(por), "dias_con_publicado": sum(a > 0 for a, _ in por),
           "publicados": sum(a for a, _ in por), "evaluables": sum(b for _, b in por)}
    if rng is not None:
        out["media_dia_ic95"] = boot_media(fr, rng)[1]
    return out


def calibrar(Z25, ev25, sin_calor):
    """§3: FA de 2025 sin compuerta por c; c por día (sin ese día) y c de los 62 días."""
    tab, pubs = {}, {}
    for c in C_GRID:
        pub, _, _ = espejo(Z25, ev25, sin_calor, c)
        pubs[c] = pub
        tab[c] = [(int(pub[d][ev25[d]].sum()), int(ev25[d].sum())) for d in range(pub.shape[0])]
        print(f"  calibración c {c:+.2f}: FA global {sum(a for a, _ in tab[c]) / sum(b for _, b in tab[c]):.4f}",
              flush=True)

    def elegir(excl):
        for c in C_GRID:                                   # de más laxo a más estricto
            fil = [(a, b) for d, (a, b) in enumerate(tab[c]) if d != excl and b > 0]
            md = np.mean([a / b for a, b in fil])
            gl = sum(a for a, _ in fil) / sum(b for _, b in fil)
            if md <= FA_DIA and gl <= FA_GLOBAL:
                return c
        return None
    c_dia = [elegir(d) for d in range(Z25.shape[0])]
    resumen = {f"{c:+.2f}": {"media_dia": float(np.mean([a / b for a, b in tab[c] if b])),
                             "global": sum(a for a, _ in tab[c]) / sum(b for _, b in tab[c])} for c in C_GRID}
    return elegir(None), c_dia, pubs, resumen


def nulo_D(pub26, CL, rng):
    """§4 (b): cada día con P toma un donante sin P; T* = horas P publicadas en el donante."""
    dias_p = [d for d in range(CL.shape[0]) if (CL[d] == "P").any()]
    don = [d for d in range(CL.shape[0]) if (CL[d] != "").any() and not (CL[d] == "P").any()]
    slots = {d: np.flatnonzero(CL[d] == "P") for d in dias_p}
    T = int(sum(pub26[d, slots[d]].sum() for d in dias_p))
    tab = np.array([[pub26[x, slots[d]].sum() for x in don] for d in dias_p])     # (dias_p, donantes)
    idx = rng.integers(0, len(don), (B_NULO, len(dias_p)))
    Ts = tab[np.arange(len(dias_p))[None, :], idx].sum(1)
    return {"T": T, "n_P": int(sum(len(v) for v in slots.values())), "dias_P": len(dias_p), "donantes": len(don),
            "configuraciones": float(len(don)) ** len(dias_p), "p": (1 + int((Ts >= T).sum())) / (B_NULO + 1),
            "Tstar_media": float(Ts.mean()), "Tstar_p95": float(np.percentile(Ts, 95))}


def solape(items, rng):
    """§4 (c): items = [(día, Huella, posiciones del espejo)]; nulo R por giro de día."""
    if not items:
        return {"n": 0, "H": 0, "decide": False}
    dias = sorted(set(d for d, _, _ in items))
    jd = {d: i for i, d in enumerate(dias)}
    grid = [M.AP[p] for _, _, p in items]
    hit = np.array([[bool(hu.dil[j][g].any()) for j in range(12)] for (_, hu, _), g in zip(items, grid)])
    di = np.array([jd[d] for d, _, _ in items])
    H = int(hit[:, 0].sum())
    n = len(dias)
    if 12 ** n <= ENUM_MAX:
        import itertools
        Ts = np.array([hit[np.arange(len(items)), np.array(js)[di]].sum() for js in itertools.product(range(12), repeat=n)])
        p = float((Ts >= H).mean())
        modo = "exacto"
    else:
        J = rng.integers(0, 12, (B_NULO, n))
        Ts = hit[np.arange(len(items))[None, :], J[:, di]].sum(1)
        p = (1 + int((Ts >= H).sum())) / (B_NULO + 1)
        modo = "monte carlo"
    return {"n": len(items), "dias": n, "H": H, "frac": H / len(items), "p_R": p, "modo": modo,
            "configuraciones": 12 ** n, "decide": 12 ** n >= MIN_CONF and len(items) >= 10,
            "frac_esperada": float(hit.mean())}


def parecido(pub, tipo, hue, ev, CL, rng, nombre):
    """§4 (a), (b), (c), (e) en 2026."""
    con = np.isin(CL, ["P", "N", "otro"])
    out = {}
    P = CL == "P"
    out["P_total"] = int(P.sum())
    out["P_evaluables"] = int((P & ev).sum())
    out["P_dias_evaluables"] = int(sum((P[d] & ev[d]).any() for d in range(CL.shape[0])))
    out["P_publicados"] = int((P & pub).sum())
    out["Sens_P"] = out["P_publicados"] / max(out["P_total"], 1)
    out["Sens_P_evaluables"] = out["P_publicados"] / max(out["P_evaluables"], 1)
    out["Sens_P_por_dia"] = {B.fecha(d): [int((P[d] & pub[d]).sum()), int(P[d].sum()), int((P[d] & ev[d]).sum())]
                             for d in range(CL.shape[0]) if P[d].any()}
    for cl in ("N", "otro"):
        m = (CL == cl) & ev
        fr = [(pub[d] & m[d]).sum() / m[d].sum() for d in range(CL.shape[0]) if m[d].any()]
        out[f"FA_{cl}"] = {"media_dia": float(np.mean(fr)) if fr else float("nan"),
                           "media_dia_ic95": boot_media(fr, rng)[1],
                           "global": float((pub & m).sum() / max(m.sum(), 1)), "dias": len(fr),
                           "publicados": int((pub & m).sum()), "evaluables": int(m.sum())}
    out["sin_clase_publicados"] = int((pub & ~con).sum())
    # (e) arrastre
    out["P_nacimiento"] = int((P & (tipo == 1)).sum())
    out["P_solo_arrastre"] = int((P & (tipo == 2)).sum())
    mN = (CL == "N") & ev
    out["N_nacimiento"] = int((mN & (tipo == 1)).sum())
    out["N_solo_arrastre"] = int((mN & (tipo == 2)).sum())
    # (b)
    out["nulo_D"] = nulo_D(pub, CL, np.random.default_rng(SEMILLA))
    # (c)
    items = []
    for d, s in zip(*np.nonzero(P & pub)):
        hu = E31.H(int(d), int(s))
        if hu is not None:
            items.append((int(d), hu, hue[(int(d), int(s))]))
    out["solape"] = solape(items, np.random.default_rng(SEMILLA))
    print(f"  {nombre}: Sens_P {out['P_publicados']}/{out['P_total']} (evaluables {out['P_evaluables']}), "
          f"FA_N {out['FA_N']['media_dia']:.4f}, p_D {out['nulo_D']['p']:.4f}, solape {out['solape'].get('H')}/"
          f"{out['solape'].get('n')}", flush=True)
    return out


def rotulo(r, fa25):
    if r["P_evaluables"] < 10 or r["P_dias_evaluables"] < 3:
        return "NO DECIDIBLE"
    sens_ok = r["Sens_P"] >= SENS_MIN
    pd_ok = r["nulo_D"]["p"] <= P_MAX
    if not (sens_ok and pd_ok):
        por = [x for x, ok in (("Sens_P < 0,50", sens_ok), ("p_D > 0,01", pd_ok)) if not ok]
        return "NO REPRODUCE (" + " y ".join(por) + ")"
    fa_ok = r["FA_N"]["media_dia"] <= FA_MAX and fa25 <= FA_MAX
    base = "REPRODUCE" if fa_ok else "REPRODUCE CON FALSA ALARMA ALTA"
    so = r["solape"]
    if not so.get("decide"):
        return base + ", huella sin decidir"
    return base + (", y calza la huella" if so["frac"] >= 0.5 and so["p_R"] <= P_MAX else ", sin calzar la huella")


def _json(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, np.bool_):
        return bool(o)
    raise TypeError(type(o))


def guardar(res):
    os.makedirs(RES, exist_ok=True)
    json.dump(res, open(os.path.join(RES, "s31j_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1, default=_json)


# ---------- pruebas sintéticas (§6.4) ----------
def pruebas():
    # un píxel del anillo a ~6 km y otro a ~11 km del cráter, y vecinos lejanos para la continuación
    i6 = int(np.argmin(np.abs(AD - 6.0)))
    i11 = int(np.argmin(np.abs(AD - 11.5)))
    assert AD[i6] <= ANCLA_KM < AD[i11]

    def cubo(n, pix_por_cuadro):
        Z = np.zeros((1, 144, NA), np.float32)
        for s, pos in pix_por_cuadro.items():
            Z[0, s, pos] = -5.0
        return Z
    ev = np.ones((1, 144), bool)
    cal = np.ones((1, 144), bool)
    # nace con calor, no sin calor, no a 11 km
    p, t, _ = espejo(cubo(1, {10: [i6]}), ev, cal, -2.0)
    assert p[0, 10] and t[0, 10] == 1
    p, _, _ = espejo(cubo(1, {10: [i6]}), ev, ~cal, -2.0)
    assert not p[0, 10]
    p, _, _ = espejo(cubo(1, {10: [i11]}), ev, cal, -2.0)
    assert not p[0, 10]

    # continuación: píxel a distancia dada de i6
    def a_dist(km):
        dd = np.hypot(AX - AX[i6], AY - AY[i6])
        ok = np.flatnonzero((AD > ANCLA_KM + 2) & (np.abs(dd - km) < 1.5))
        return int(ok[np.argmin(np.abs(dd[ok] - km))]), float(dd[ok][np.argmin(np.abs(dd[ok] - km))])
    # el anillo llega a 40 km del cráter: desde un píxel a 6 km no hay pares a más de ~46 km, así que el radio de
    # 60 y 90 km se prueba por el lado que sí se puede (33 km pasa con uno o dos cuadros sin evaluar)
    assert [VEL_KM_S * 600 * k for k in (1, 2, 3)] == [30.0, 60.0, 90.0]
    for km, gap, espera in ((27.5, 0, True), (33.0, 0, False), (33.0, 1, True), (40.0, 2, True), (20.0, 3, False)):
        j, dj = a_dist(km)
        evx = ev.copy()
        evx[0, 11:11 + gap] = False
        calx = cal.copy()
        calx[0, 11:] = False                      # sin calor después del nacimiento: sólo puede continuar
        p, t, _ = espejo(cubo(1, {10: [i6], 11 + gap: [j]}), evx, calx, -2.0)
        lim = VEL_KM_S * 600 * (gap + 1)
        assert p[0, 11 + gap] == espera and (not espera or t[0, 11 + gap] == 2), (km, gap, dj, lim, p[0, 11 + gap])
    print("pruebas sintéticas OK", flush=True)


# ---------- medida ----------
def medir():
    t0 = time.time()
    os.makedirs(TRAB, exist_ok=True)
    libre = shutil.disk_usage("D:\\").free / 1e9
    assert libre > MIN_LIBRE_GB + 1, f"D: con {libre:.1f} GB"
    pruebas()
    res = {"criterio": "criterio_2026-11-27.md (e29dd33) y enmienda_1_antes_de_medir_2026-11-27.md",
           "rotulo_desarrollo": "DESARROLLO: días de 2024, 2025 y 2026 (hasta el 24-11) ya vistos; nada de esto confirma"}
    est26 = np.load(A26.ESTAT26)
    assert hashlib.sha256(est26.tobytes()).hexdigest()[:16] == A26.SHA_ESTAT26, "estat_2026 no es el congelado"
    D = S.Detector(ref="2025", con_blanco=True, estat_blanco=est26)
    D.SR0 = D.SR.copy()
    assert all(B.fecha(d) <= "2026-11-24" for d in range(B.ND)), "días posteriores al 24-11"
    CL = D.CLT
    import s25b_medir as X24
    D24 = X24._detector_2024()
    acm24, m124 = np.load(X24._npy24("acm")), np.load(X24._npy24("m1"))
    FD24, mm24 = D._nubes(acm24, m124, D24.ESTAT)
    gate24 = FD24 <= B.G_MAX
    del D24
    print(f"detectores listos ({time.time() - t0:.0f} s)", flush=True)

    # ---- comprobación de código (§6) ----
    rep = {}
    rng = np.random.default_rng(1)
    B0 = D.base(None)
    m1 = 0
    for d, s in zip(rng.integers(0, len(D.DIASR), 300), rng.integers(0, 144, 300)):
        if D.GATER[d, s]:
            a = M.estadistico(D.mmR[d, s] - D.base(d)[s])[0]
            m1 += not (a == D.SR0[d, s] or (np.isnan(a) and np.isnan(D.SR0[d, s])))
        if D.GATET[d, s]:
            a = M.estadistico(D.mmT[d, s] - B0[s])[0]
            m1 += not (a == D.ST[d, s] or (np.isnan(a) and np.isnan(D.ST[d, s])))
    rep["1_S_congelado_distintos"] = m1
    Z25, _, _, _ = E31.anio_2025(D)
    Z26, _, _, _ = E31.blanco(D, D.mmT, D.GATET)
    Z24, _, _, _ = E31.blanco(D, mm24, gate24)
    Z25, Z26, Z24 = Z25["T1"], Z26["T1"], Z24["T1"]
    np.savez_compressed(os.path.join(TRAB, "z_T1.npz"), Z25=Z25, Z26=Z26, Z24=Z24)
    print(f"z de los tres años lista ({time.time() - t0:.0f} s)", flush=True)
    CI = np.flatnonzero(AD < 15.0)
    ref = np.load(CORONA_S31H)
    dif, mismas = 0.0, True
    for nom, Zx in (("Z25", Z25), ("Z26", Z26), ("Z24", Z24)):
        a, b = Zx[:, :, CI], ref[nom]
        mismas &= bool(np.array_equal(np.isfinite(a), np.isfinite(b)))
        x = np.abs(a - b)
        dif = max(dif, float(np.nanmax(x)) if np.isfinite(x).any() else 0.0)
    rep["2_corona_dif_max"], rep["2_corona_mismas_posiciones"] = dif, mismas
    # 3: indicador de calor contra la validación
    dfc, no = calor_noches()
    no.to_csv(os.path.join(TRAB, "noches_chillan.csv"), index=False)
    dfc.to_csv(os.path.join(TRAB, "cuadros_calor_chillan.csv"), index=False)
    val = {r["noche"]: r for r in csv.DictReader(open(NOCHES_VAL, encoding="utf-8"))
           if r["sitio"] == "Nevados de Chillan"}
    comp = [f"{datetime(2026, 10, 5) + timedelta(days=k):%Y-%m-%d}" for k in range(15)]     # enmienda 1
    mio = {r.noche: r for r in no.itertuples()}
    enc_ok = n10_ok = n_cmp = 0
    for n in comp:
        if n in val and n in mio:
            n_cmp += 1
            enc_ok += (val[n]["enc"] == "True") == bool(mio[n].enc)
            n10_ok += int(val[n]["n10"]) == int(mio[n].n10)
    rep["3_noches_comparadas"], rep["3_enc_iguales"], rep["3_n10_iguales"] = n_cmp, enc_ok, n10_ok
    ok = (m1 == 0 and dif <= 1e-6 and mismas and n_cmp == len(comp) and enc_ok == n_cmp
          and n10_ok >= 0.9 * n_cmp)
    rep["4_sinteticas"] = "OK"
    print("comprobación de código:", json.dumps(rep, ensure_ascii=False), "OK" if ok else "NO REPRODUCE", flush=True)
    res["comprobacion"] = rep
    if not ok:
        res["veredicto"] = "INVÁLIDA"
        guardar(res)
        sys.exit("la comprobación de código falla: se para")
    guardar(res)

    # ---- evaluables y compuerta de calor ----
    ev25 = D.GATER & np.isfinite(Z25).any(2)
    ev26 = D.GATET & np.isfinite(Z26).any(2)
    ev24 = gate24 & np.isfinite(Z24).any(2)
    G25 = compuerta_calor(no, T0_25, Z25.shape[0])
    G26 = compuerta_calor(no, T0_26, Z26.shape[0])
    no25 = no[no.noche < "2026-01-01"]
    no26 = no[no.noche >= "2026-01-01"]
    res["calor"] = {"noches_2025": int(len(no25)), "con_dato_2025": int(no25.con_dato.sum()),
                    "encendidas_2025": int(no25.enc.sum()), "noches_2026": int(len(no26)),
                    "con_dato_2026": int(no26.con_dato.sum()), "encendidas_2026": int(no26.enc.sum()),
                    "encendidas_lista_2026": sorted(no26[no26.enc].noche.tolist()),
                    "encendidas_lista_2025": sorted(no25[no25.enc].noche.tolist()),
                    "compuerta_abierta_frac_2025": float(G25[ev25].mean()),
                    "compuerta_abierta_frac_2026_con_clase": float(G26[ev26 & (CL != "")].mean()),
                    "P_con_compuerta_cerrada": int(((CL == "P") & ~G26).sum())}
    print("calor:", json.dumps(res["calor"], ensure_ascii=False), flush=True)
    guardar(res)

    # ---- §3 umbral c ----
    uno25 = np.ones_like(ev25)
    c_all, c_dia, pubs25, tabla_c = calibrar(Z25, ev25, uno25)
    res["calibracion"] = {"c_62_dias": c_all, "c_por_dia": c_dia, "tabla_sin_compuerta_2025": tabla_c}
    if c_all is None or any(c is None for c in c_dia):
        res["veredicto"] = "NO SIRVE"
        guardar(res)
        sys.exit("ningún c cumple la falsa alarma: NO SIRVE")
    print(f"c = {c_all} (por día: {sorted(set(c_dia))})", flush=True)

    # ---- (d) falsa alarma 2025 (con y sin compuerta, c sin el día) y 2024 ----
    rngb = np.random.default_rng(SEMILLA)
    pub25_sin = np.array([pubs25[c_dia[d]][d] for d in range(Z25.shape[0])])
    corr = {c: espejo(Z25, ev25, G25, c)[0] for c in sorted(set(c_dia))}
    pub25_con = np.array([corr[c_dia[d]][d] for d in range(Z25.shape[0])])
    res["fa_2025_con_compuerta"] = fa_anual(pub25_con, ev25, rngb)
    res["fa_2025_sin_compuerta"] = fa_anual(pub25_sin, ev25, rngb)
    pub24, tipo24, _ = espejo(Z24, ev24, np.ones_like(ev24), c_all)
    res["fa_2024_sin_compuerta"] = fa_anual(pub24, ev24, rngb)
    print("FA 2025 con/sin compuerta, 2024 sin:", res["fa_2025_con_compuerta"]["media_dia"],
          res["fa_2025_sin_compuerta"]["media_dia"], res["fa_2024_sin_compuerta"]["media_dia"], flush=True)
    guardar(res)

    # ---- 2026: principal, sin compuerta (descriptivo) y S1 ----
    pub26, tipo26, hue26 = espejo(Z26, ev26, G26, c_all)
    res["principal"] = parecido(pub26, tipo26, hue26, ev26, CL, rngb, "principal")
    res["veredicto"] = rotulo(res["principal"], res["fa_2025_con_compuerta"]["media_dia"])
    print("VEREDICTO:", res["veredicto"], flush=True)
    guardar(res)
    pub26n, tipo26n, hue26n = espejo(Z26, ev26, np.ones_like(ev26), c_all)
    res["sin_compuerta_2026"] = parecido(pub26n, tipo26n, hue26n, ev26, CL, rngb, "sin compuerta")
    pub26s, tipo26s, hue26s = espejo(Z26, ev26, G26, c_all, C_CONT_S1)
    res["S1"] = parecido(pub26s, tipo26s, hue26s, ev26, CL, rngb, "S1")
    s1_25 = {c: espejo(Z25, ev25, uno25, c, C_CONT_S1)[0] for c in sorted(set(c_dia))}
    res["S1"]["fa_2025_sin_compuerta"] = fa_anual(np.array([s1_25[c_dia[d]][d] for d in range(Z25.shape[0])]), ev25)
    res["S1"]["fa_2024_sin_compuerta"] = fa_anual(espejo(Z24, ev24, np.ones_like(ev24), c_all, C_CONT_S1)[0], ev24)
    guardar(res)

    # ---- (f) descriptivos ----
    noche = np.zeros((1, 144), bool)
    noche[0, list(NOCHE_SLOTS)] = True
    P = CL == "P"
    res["descriptivos"] = {
        "P_publicados_dia_noche": [int((P & pub26 & ~noche).sum()), int((P & pub26 & noche).sum())],
        "N_publicados_dia_noche": [int(((CL == "N") & pub26 & ~noche).sum()), int(((CL == "N") & pub26 & noche).sum())],
        "dist_nacimiento_km_2026": [float(AD[hue26[k]].min()) for k in hue26 if tipo26[k] == 1],
        "dist_nacimiento_km_2025_sin_compuerta": [],
        "nacimientos_volcat": {}}
    for f, h in M.NACIMIENTOS:
        d, s = B.dia_idx(f), M.slot(h)
        res["descriptivos"]["nacimientos_volcat"][f"{f} {h}"] = {
            "clase": CL[d, s], "evaluable": bool(ev26[d, s]), "calor": bool(G26[d, s]), "publicado": bool(pub26[d, s]),
            "tipo": int(tipo26[d, s]), "z_min_10km": float(np.nanmin(np.where(AD <= ANCLA_KM, Z26[d, s], np.nan)))
            if np.isfinite(Z26[d, s]).any() else None}
    _, tipo25, hue25 = espejo(Z25, ev25, uno25, c_all)
    res["descriptivos"]["dist_nacimiento_km_2025_sin_compuerta"] = [float(AD[v].min()) for k, v in hue25.items()
                                                                    if tipo25[k] == 1]
    guardar(res)

    # ---- por cuadro (sólo cifras) ----
    with open(os.path.join(RES, "s31j_por_cuadro.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo)
        w.writerow(["dia", "hora", "clase", "evaluable", "calor", "publicado", "tipo", "publicado_S1",
                    "publicado_sin_compuerta", "n_pix", "dist_min_km"])
        for d in range(B.ND):
            for s in range(144):
                h = hue26.get((d, s))
                w.writerow([B.fecha(d), M.hhmm(s), CL[d, s], int(ev26[d, s]), int(G26[d, s]), int(pub26[d, s]),
                            int(tipo26[d, s]), int(pub26s[d, s]), int(pub26n[d, s]),
                            len(h) if h is not None else 0, round(float(AD[h].min()), 2) if h is not None else ""])
    res["segundos"] = round(time.time() - t0)
    guardar(res)
    print(f"FIN ({time.time() - t0:.0f} s)", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pruebas":
        pruebas()
    elif len(sys.argv) > 1 and sys.argv[1] == "medir":
        medir()
    else:
        print(__doc__)
