r"""S25b: el detector de S23 (base y umbral de oct-nov 2025) aplicado a oct-nov 2024, otro año tranquilo, fuera de la
muestra. Implementa criterio_2026-11-25.md de esta carpeta (commiteado y empujado antes de abrir 2024).

Por qué: el umbral de S23 salió de un solo año. Si sólo vale en 2025, lo que el detector marca en 2026 podría ser "2026
no es 2025" y no pluma. 2024 tuvo la misma alerta (verde, sin actividad superficial) y otro satélite (GOES-16) en la misma
posición y grilla, así que mide a la vez la transferencia entre años y entre instrumentos.

Uso: python -I s25b_medir.py pruebas | cubo | medir
  pruebas  sólo con 2025: el camino "fuera de muestra" de este script, aplicado a 2025 con la base de cada día sin sí
           mismo, tiene que reproducir el S de 2025 de s23_medir exacto.
  cubo     arma BT11, ACM y M1 de 2024 y corre I1 a I5 (resultados/instrumento_2024.json).
  medir    (a) calibración informativa, (b) falsa alarma de S23a y S23b en 2024, (c) umbral 2024 contra 2025.
"""
import json
import os
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore", RuntimeWarning)
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "s23_fondo_2025", "scripts"))
import s23_medir as S  # noqa: E402  (Detector, disparos, cubo de 2025: sin cambios)
B, M, H24, C29 = S.B, S.M, S.H24, S.C29

DATOS = r"D:\goes_notas\s25\s25b_2024"               # bajada de 2024 (s25b_bajar_2024.py)
TRAB = os.path.join(DATOS, "cubo")                    # cubos derivados de 2024
T0 = datetime(2024, 9, 21)
ND = S.NR                                             # 62 días, la misma ventana de calendario
NPIX = M.NY * M.NX
NOCHE = range(0, 54)                                  # 00:00 a 08:50 UTC (S24)
NOCHE_I4 = S.NOCHE                                    # 03:00 a 08:50 UTC (I4 de S23)
COMUN_MAX, TOP = 3, 5                                 # S24
FA_MAX, FA_MAL, FRANJA_MAX, ESTRICTO = 0.05, 0.10, 0.10, 0.02
U_MED_OK, U_MAX_OK, U_MED_MAL = 0.10, 0.25, 0.20
I1_MIN, I3_MIN, I4_MIN = 0.90, 0.999, 0.90


def _npy24(nombre):
    return os.path.join(TRAB, f"r24_{nombre}.npy")


def _r(x):
    return S._r(x)


# ---------- el camino fuera de muestra ----------
def aplicar(D, acm, m1, estat, base_de_dia):
    """S, k*, compuerta y nube dinámica de un año blanco con la referencia del Detector D.
    estat: nublado de costumbre (144, NPIX) que decide qué píxel se borra; base_de_dia(d) -> base (144, NA)."""
    FD, mm = D._nubes(acm, m1, estat)
    gate = FD <= B.G_MAX
    Sx = np.full(acm.shape[:2], np.nan)
    Kx = np.full(acm.shape[:2], -1, int)
    for d in range(acm.shape[0]):
        Bd = base_de_dia(d)
        for s in range(144):
            if gate[d, s]:
                Sx[d, s], Kx[d, s], _ = M.estadistico(mm[d, s] - Bd[s])
    return Sx, Kx, gate, FD


def pruebas():
    t = time.time()
    D = S.Detector(ref="2025", con_blanco=False)
    Sx, Kx, gate, _ = aplicar(D, D.acmR, D.m1R, D.ESTAT, lambda d: D.base(d))
    a, b = Sx[D.DIASR], D.SR[D.DIASR]
    assert np.array_equal(np.isfinite(a), np.isfinite(b)), "evaluados distintos"
    assert np.allclose(a[np.isfinite(a)], b[np.isfinite(b)], atol=0, rtol=0), "S distinto"
    assert np.array_equal(Kx[D.DIASR], D.KR[D.DIASR]), "tajada distinta"
    # tasa: la media por día de (disparos / evaluados) con el umbral sin cada día tiene que dar el seco de S23
    fas = []
    for d in D.DIASR:
        U, _ = D.umbral(d)
        F, ev = S.disparos(Sx, Kx, d, U)
        if ev.sum():
            fas.append(F.sum() / ev.sum())
    seco = json.load(open(os.path.join(S.RES, "seco.json"), encoding="utf-8"))["fa_media_por_dia"]
    assert abs(np.mean(fas) - seco) < 1e-12, (np.mean(fas), seco)
    assert veredicto_b(0.04, {"x": 0.09}) == "AGUANTA" and veredicto_b(0.04, {"x": 0.11}) == "DEGRADA"
    assert veredicto_b(0.07, {}) == "DEGRADA" and veredicto_b(0.11, {}) == "NO AGUANTA"
    assert veredicto_c(np.full(144, 0.05)) == "ESTABLE" and veredicto_c(np.full(144, 0.3)) == "INESTABLE"
    assert veredicto_c(np.r_[np.full(143, 0.05), 0.3]) == "INTERMEDIO"
    print(f"pruebas OK: el camino fuera de muestra reproduce S y el seco de 2025 ({seco:.6f}) en {time.time() - t:.0f} s")


def veredicto_b(fa, franjas):
    if fa > FA_MAL:
        return "NO AGUANTA"
    if fa <= FA_MAX and all(v is None or v <= FRANJA_MAX for v in franjas.values()):
        return "AGUANTA"
    return "DEGRADA"


def veredicto_c(dif_abs):
    v = np.asarray(dif_abs, float)
    v = v[np.isfinite(v)]
    med, mx = float(np.median(v)), float(v.max())
    if med <= U_MED_OK and mx <= U_MAX_OK:
        return "ESTABLE"
    if med > U_MED_MAL:
        return "INESTABLE"
    return "INTERMEDIO"


# ---------- cubo de 2024 e instrumento (§3) ----------
def _proyeccion(bucket, dt):
    import h5py
    import s3fs
    fs = s3fs.S3FileSystem(anon=True)
    p = f"{bucket}/ABI-L1b-RadF/{dt:%Y}/{dt.timetuple().tm_yday:03d}/{dt:%H}/"
    k = [x for x in fs.ls(p) if "C14_" in x][0]
    with fs.open(k, "rb", block_size=2**18, cache_type="readahead") as fo, h5py.File(fo, "r") as f:
        a = f["goes_imager_projection"].attrs
        return {n: float(np.ravel(a[n])[0]) for n in ("longitude_of_projection_origin", "perspective_point_height",
                                                       "semi_major_axis", "semi_minor_axis")} | {"archivo": k.split("/")[-1]}


def cubo(nproc=6):
    os.makedirs(TRAB, exist_ok=True)
    n = ND * 144
    r = {b: np.full((n, NPIX), np.nan, "float32") for b in (14, 15)}
    acm = np.full((n, NPIX), 255, "uint8")
    co = {14: [], 15: []}
    pres, scan_dist, n_acm = 0, 0, 0
    for i in range(n):
        dt = T0 + timedelta(minutes=10 * i)
        f = os.path.join(DATOS, "l1b", f"{dt:%Y%m%d_%H%M}.npz")
        if os.path.exists(f):
            with np.load(f) as z:
                s14, s15 = str(z["key14"]).split("_s")[1][:14], str(z["key15"]).split("_s")[1][:14]
                assert "_G16_" in str(z["key14"]) and "_G16_" in str(z["key15"])
                if s14 != s15 or s14[:11] != f"{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}":
                    scan_dist += 1
                else:
                    for b in (14, 15):
                        r[b][i] = z[f"rad{b}"].ravel()
                        co[b].append(z[f"co{b}"])
                    pres += 1
        g = os.path.join(DATOS, "acm", f"{dt:%Y%m%d_%H%M}.npz")
        if os.path.exists(g):
            with np.load(g) as z:
                acm[i] = z["acm"].ravel()
                n_acm += 1
    cof = {b: np.median(np.array(co[b]), 0) for b in (14, 15)}
    var_co = {b: float(np.max(np.abs(np.array(co[b]) / cof[b] - 1))) for b in (14, 15)}
    bt11 = C29.bt_de_rad(r[14].astype("float64"), cof[14]).astype("float32")
    btd = (bt11 - C29.bt_de_rad(r[15].astype("float64"), cof[15])).astype("float32")
    hay = np.isfinite(bt11).any(1)
    cong = sum(1 for i in range(1, n) if hay[i] and hay[i - 1] and np.array_equal(r[14][i], r[14][i - 1], equal_nan=True))
    v = bt11[np.isfinite(bt11)]
    # I4 contra 2025
    acm3 = acm.reshape(ND, 144, NPIX)
    bt3 = bt11.reshape(ND, 144, NPIX)
    e1 = H24.despejada("chillan", acm3)
    acm25 = np.load(S._npy("acm"))
    bt25 = np.load(S._npy("bt11"), mmap_mode="r")
    e125 = H24.despejada("chillan", acm25)
    sel24 = [(d, s) for d in range(ND) for s in NOCHE_I4 if e1[d, s] and hay[d * 144 + s]]
    sel25 = [(d, s) for d in range(S.NR) for s in NOCHE_I4 if e125[d, s] and np.isfinite(bt25[d, s]).any()]
    m24 = np.nanmean(np.array([bt3[d, s] for d, s in sel24]), 0)
    m25 = np.nanmean(np.array([np.asarray(bt25[d, s]) for d, s in sel25]), 0)
    ok = np.isfinite(m24) & np.isfinite(m25)
    corr = float(np.corrcoef(m24[ok], m25[ok])[0, 1]) if ok.sum() > 100 else float("nan")
    pr16 = _proyeccion("noaa-goes16", datetime(2024, 10, 15, 6))
    pr19 = _proyeccion("noaa-goes19", datetime(2025, 10, 15, 6))
    i5 = all(pr16[k] == pr19[k] for k in pr16 if k != "archivo")
    co25 = [np.load(os.path.join(S.REF, "l1b", "20251015_0600.npz"))[f"co{b}"] for b in (14, 15)]
    inst = {"cuadros": n, "l1b_presentes": pres, "cobertura_l1b": pres / n, "acm_presentes": n_acm,
            "cobertura_acm": n_acm / n, "scan_distinto_descartados": scan_dist, "congelados": cong,
            "bt11_en_rango": float(((v > 180) & (v < 330)).mean()) if v.size else 0.0,
            "planck_g16_c14": cof[14].tolist(), "planck_g16_c15": cof[15].tolist(),
            "planck_g19_c14": co25[0].tolist(), "planck_g19_c15": co25[1].tolist(),
            "planck_dif_rel_g16_g19_c14": (cof[14] / co25[0] - 1).tolist(),
            "planck_dif_rel_g16_g19_c15": (cof[15] / co25[1] - 1).tolist(),
            "planck_variacion_dentro_de_2024": var_co,
            "I4_noches_2024": len(sel24), "I4_noches_2025": len(sel25), "I4_correlacion": corr,
            "I5_proyeccion_g16": pr16, "I5_proyeccion_g19": pr19, "I5_iguales": i5}
    inst["falla"] = [k for k, okk in (("I1", inst["cobertura_l1b"] >= I1_MIN and inst["cobertura_acm"] >= I1_MIN),
                                      ("I3", inst["bt11_en_rango"] >= I3_MIN and cong == 0),
                                      ("I4", np.isfinite(corr) and corr >= I4_MIN), ("I5", i5)) if not okk]
    inst["veredicto_a"] = "COMPARABLE" if not inst["falla"] else "INVÁLIDA"
    os.makedirs(RES, exist_ok=True)
    json.dump(inst, open(os.path.join(RES, "instrumento_2024.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(inst, ensure_ascii=False, indent=1), flush=True)
    t = time.time()
    btd3 = btd.reshape(ND, 144, NPIX)
    with ProcessPoolExecutor(nproc) as ex:
        m1 = np.array(list(ex.map(S._m1_dia, [(bt3[d], btd3[d]) for d in range(ND)])), np.float32)
    print(f"M1 de 2024 en {time.time() - t:.0f} s", flush=True)
    np.save(_npy24("acm"), acm3)
    np.save(_npy24("m1"), m1)
    np.save(_npy24("bt11"), bt3)


# ---------- medida (§5) ----------
def _detector_2024():
    """Detector con 2024 como referencia (U24 y nublado de costumbre de 2024): s23_medir.Detector leyendo los cubos de 2024."""
    viejo = S._npy
    S._npy = _npy24
    try:
        return S.Detector(ref="2025", con_blanco=False)       # 'ref=2025' = "año tranquilo entero como referencia"
    finally:
        S._npy = viejo


def _tasas(Sx, Kx, U):
    """Disparos por día con el umbral U; filas (día, slot, F, k) de los evaluados."""
    filas, fa_dia = [], []
    for d in range(Sx.shape[0]):
        F, ev = S.disparos(Sx, Kx, d, U)
        if ev.sum():
            fa_dia.append(F.sum() / ev.sum())
        filas += [(d, int(s), bool(F[s]), int(Kx[d, s])) for s in np.flatnonzero(ev)]
    return np.array(fa_dia), filas


def _franjas(filas):
    out = {}
    for b in range(8):
        v = [f for _, s, f, _ in filas if s // 18 == b]
        out[f"{3 * b:02d}-{3 * b + 2:02d} UTC"] = {"n": len(v), "tasa": _r(np.mean(v)) if v else None}
    return out


def _noche(filas):
    nd, fd = {}, {}
    for d, s, f, _ in filas:
        if s in NOCHE:
            nd[d] = nd.get(d, 0) + 1
            fd[d] = fd.get(d, 0) + f
    tot, n = sum(fd.values()), sum(nd.values())
    orden = sorted(fd, key=lambda d: -fd[d])
    com = [d for d in nd if fd[d] < COMUN_MAX]
    nc, fc = sum(nd[d] for d in com), sum(fd[d] for d in com)
    p = float(stats.fisher_exact([[fc, nc - fc], [2, 1409 - 2]], alternative="two-sided")[1]) if nc else None
    return {"evaluados": n, "disparos": tot, "tasa": _r(tot / max(n, 1)),
            "frac_top5": _r(sum(fd[d] for d in orden[:TOP]) / tot) if tot else None,
            "top_noches": [{"dia": f"{T0 + timedelta(days=d):%Y-%m-%d}", "disparos": fd[d], "evaluados": nd[d]}
                           for d in orden[:8]],
            "noches_comunes": len(com), "evaluados_comunes": nc, "disparos_comunes": fc,
            "tasa_comunes": _r(fc / max(nc, 1)), "tasa_comunes_2025": 0.0014, "p_fisher_vs_2025": p}


def btd_media(ref, t0, sel):
    """BTD media (C14 menos C15) de los cuadros sel, leída de los npz de la bajada con los coeficientes de cada archivo."""
    acc, n = np.zeros(NPIX), np.zeros(NPIX)
    for d, s in sel:
        dt = t0 + timedelta(days=d, minutes=10 * s)
        with np.load(os.path.join(ref, "l1b", f"{dt:%Y%m%d_%H%M}.npz")) as z:
            b = (C29.bt_de_rad(z["rad14"].astype("float64"), z["co14"])
                 - C29.bt_de_rad(z["rad15"].astype("float64"), z["co15"])).ravel()
        ok = np.isfinite(b)
        acc[ok] += b[ok]
        n[ok] += 1
    return np.where(n > 0, acc / np.maximum(n, 1), np.nan)


def medir():
    inst = json.load(open(os.path.join(RES, "instrumento_2024.json"), encoding="utf-8"))
    if inst["falla"]:
        out = {"veredicto_a": "INVÁLIDA", "falla": inst["falla"]}
        json.dump(out, open(os.path.join(RES, "s25b_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(out)
        return
    t = time.time()
    D25 = S.Detector(ref="2025", con_blanco=False)
    D24 = _detector_2024()
    acm24, m124 = np.load(_npy24("acm")), np.load(_npy24("m1"))
    B0, (U25, _) = D25.base(None), D25.umbral(None)
    seco25 = json.load(open(os.path.join(S.RES, "seco.json"), encoding="utf-8"))
    out = {"criterio": "criterio_2026-11-25.md", "instrumento": {k: inst[k] for k in (
        "cobertura_l1b", "cobertura_acm", "I4_correlacion", "I5_iguales", "planck_dif_rel_g16_g19_c14",
        "planck_dif_rel_g16_g19_c15")}, "veredicto_a": inst["veredicto_a"]}
    # (a) calibración informativa: BT11, BTD y M1 medios de noches despejadas, 2024 contra 2025
    bt24 = np.load(_npy24("bt11"), mmap_mode="r")
    bt25 = np.load(S._npy("bt11"), mmap_mode="r")
    sel = {a: [(d, s) for d in range(ND) for s in NOCHE_I4 if D.E1R[d, s] and np.isfinite(D.m1R[d, s]).any()]
           for a, D in (("2024", D24), ("2025", D25))}
    med = {}
    for a, D, bt, ref, t0 in (("2024", D24, bt24, DATOS, T0), ("2025", D25, bt25, S.REF, S.T0R)):
        med[a] = {"bt11": np.nanmean(np.array([np.asarray(bt[d, s]) for d, s in sel[a]]), 0),
                  "m1": np.nanmean(np.array([D.m1R[d, s] for d, s in sel[a]]), 0),
                  "btd": btd_media(ref, t0, sel[a])}
    cal = {"noches_despejadas_2024": len(sel["2024"]), "noches_despejadas_2025": len(sel["2025"]),
           "bt11_dif_mediana_2024_menos_2025": _r(np.nanmedian(med["2024"]["bt11"] - med["2025"]["bt11"])),
           "btd_dif_mediana_2024_menos_2025": _r(np.nanmedian(med["2024"]["btd"] - med["2025"]["btd"])),
           "btd_media_2024": _r(np.nanmedian(med["2024"]["btd"])), "btd_media_2025": _r(np.nanmedian(med["2025"]["btd"]))}
    a, b = med["2024"]["m1"], med["2025"]["m1"]
    ok = np.isfinite(a) & np.isfinite(b)
    cal["m1_anillo_dif_mediana"] = _r(np.median(a[ok] - b[ok]))
    cal["m1_anillo_correlacion"] = _r(np.corrcoef(a[ok], b[ok])[0, 1])
    out["a_calibracion_informativa"] = cal
    # (b) falsa alarma fuera de muestra
    out["b"] = {}
    for nom, estat in (("S23a", D25.ESTAT), ("S23b", D24.ESTAT)):
        Sx, Kx, gate, FD = aplicar(D25, acm24, m124, estat, lambda d: B0)
        fa_dia, filas = _tasas(Sx, Kx, U25)
        fr = _franjas(filas)
        FA = float(fa_dia.mean())
        hay = (acm24 != 255).any(2)
        out["b"][nom] = {"FA24_media_por_dia": _r(FA), "FA25_seco": _r(seco25["fa_media_por_dia"]),
                         "tasa_por_cuadro": _r(np.mean([f for *_, f, _ in filas])), "evaluados": len(filas),
                         "frac_pasan_compuerta": _r(gate[hay].mean()), "nube_dinamica_mediana": _r(np.nanmedian(FD)),
                         "por_franja_2024": fr, "por_franja_2025": seco25["por_hora"], "noche": _noche(filas),
                         "tajadas_disparos": np.bincount([k for *_, f, k in filas if f], minlength=12).tolist(),
                         "veredicto": veredicto_b(FA, {k: v["tasa"] for k, v in fr.items()}),
                         "mas_estricto_fuera_de_muestra": FA < ESTRICTO,
                         "por_dia": [{"dia": f"{T0 + timedelta(days=d):%Y-%m-%d}",
                                      "evaluados": sum(1 for dd, *_ in filas if dd == d),
                                      "disparos": sum(f for dd, _, f, _ in filas if dd == d)} for d in range(ND)]}
        if nom == "S23b":
            p5 = {}
            for h in range(24):
                cols = [x for x in range(144) if M.dslot(x, 6 * h) <= 6]
                v = Sx[:, cols].ravel()
                v = v[np.isfinite(v)]
                p5[f"{h:02d}"] = {"p5_S24_base2025": _r(np.percentile(v, 5)) if len(v) >= 40 else None,
                                  "U25": _r(U25[6 * h]), "n": int(len(v))}
            out["c_informativo_p5_S24_con_base_2025"] = p5
    # (c) estabilidad del umbral
    U24, _ = D24.umbral(None)
    dif = np.array([abs(U24[s] - U25[s]) if (U24[s] is not None and U25[s] is not None) else np.nan for s in range(144)])
    # ruido de muestreo: U con los días pares contra los impares de 2025
    par, impar = [d for d in D25.DIASR if d % 2 == 0], [d for d in D25.DIASR if d % 2 == 1]

    def u_sub(D, dias):
        guard = D.DIASR
        D.DIASR, D._U = dias, {}
        try:
            return D.umbral(None)[0]
        finally:
            D.DIASR, D._U = guard, {}
    Up, Ui = u_sub(D25, par), u_sub(D25, impar)
    ruido = np.array([abs(Up[s] - Ui[s]) if (Up[s] is not None and Ui[s] is not None) else np.nan for s in range(144)])
    out["c"] = {"mediana_abs_dif": _r(np.nanmedian(dif)), "max_abs_dif": _r(np.nanmax(dif)),
                "slot_max": M.hhmm(int(np.nanargmax(dif))), "slots_comparados": int(np.isfinite(dif).sum()),
                "mediana_dif_con_signo_U24_menos_U25": _r(np.nanmedian([U24[s] - U25[s] for s in range(144)
                                                                         if U24[s] is not None and U25[s] is not None])),
                "veredicto": veredicto_c(dif),
                "ruido_pares_vs_impares_2025": {"mediana_abs": _r(np.nanmedian(ruido)), "max_abs": _r(np.nanmax(ruido))},
                "U_por_hora": {M.hhmm(s): {"U24": _r(U24[s]), "U25": _r(U25[s])} for s in range(0, 144, 6)}}
    out["segundos"] = round(time.time() - t)
    json.dump(out, open(os.path.join(RES, "s25b_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    res = {k: v for k, v in out.items() if k not in ("b", "c_informativo_p5_S24_con_base_2025")}
    res["b"] = {n: {k: v for k, v in x.items() if k not in ("por_dia", "por_franja_2025")} for n, x in out["b"].items()}
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    {"pruebas": pruebas, "cubo": cubo, "medir": medir}[sys.argv[1]]()
