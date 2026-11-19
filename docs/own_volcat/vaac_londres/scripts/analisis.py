"""Prueba tolerante del London VAAC (Francis et al. 2012, segun Falconieri et al. 2018 §3.2) sobre las
huellas VOLCAT de Nevados de Chillan, nov-2026. Criterio: ../criterio_2026-11-19.md (commiteado antes).

Que mide: para 12 configuraciones declaradas (L0..L3 x banda de 10,8 um C14/C13 x T_ref 255/215 K),
(a) la vara del detector previo del 17-11 (sensibilidad, falsas alarmas por scan y por dia, 16-11,
coincidencia espacial) y (b) el control pareado por pixel (P = huella marcada en el positivo,
C = mismos pixeles marcados en un dia sin pluma con BT C14 parecida).

Uso: python analisis.py      (escribe todo en rutas.RESULTADOS; no toca nada del repo)
"""
import os, sys, json, time
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rutas as R  # noqa: E402
sys.path.insert(0, R.REPO)
from src.process.beta_ratios import cloud_emissivity, beta_ratio  # noqa: E402

OUT = R.RESULTADOS; os.makedirs(OUT, exist_ok=True)
VLAT, VLON = -36.86, -71.38
ll = np.load(R.LATLON); LAT, LON = ll["lat"], ll["lon"]


def _dist_km(lat, lon):
    p1, p2 = np.radians(VLAT), np.radians(lat)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon - VLON) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


DIST = _dist_km(LAT, LON)
SEED = DIST <= 10.0
NEAR30 = DIST <= 30.0
EIGHT = np.ones((3, 3), int)
BOX3 = np.ones((3, 3), int)

# --------------------------------------------------------------- Planck (siempre del L1b)
_co = json.load(open(R.PLANCK_PREV))
CO = {11: tuple(_co["C11"]), 14: tuple(_co["C14"]), 15: tuple(_co["C15"])}
CO[13] = tuple(json.load(open(R.PLANCK13))["C13"])

# --------------------------------------------------------------- carga
SNAP = set(open(R.SNAPSHOT).read().split())
FULL = set(f for f in os.listdir(R.CACHE_PREV) if f.endswith(".npz") and ".tmp" not in f)
HAS13 = set(f for f in os.listdir(R.CACHE13) if f.endswith(".npz") and ".tmp" not in f)


def key(dt):
    return f"{dt:%Y%m%d_%H%M}"


_mem = {}


def load(dt, universo):
    """Escena con b11, b13, b14, b15 (K) o None. `universo` = set de archivos permitidos."""
    k = key(dt) + ".npz"
    if k not in universo or k not in HAS13:
        return None
    if k not in _mem:
        z = np.load(os.path.join(R.CACHE_PREV, k)); z13 = np.load(os.path.join(R.CACHE13, k))
        _mem[k] = {"b11": z["b11"].astype("float64"), "b14": z["b14"].astype("float64"),
                   "b15": z["b15"].astype("float64"), "b13": z13["b13"].astype("float64")}
    return _mem[k]


def referencia(dt, universo, N=10, k=3):
    """Cielo despejado empirico (criterio): mismo slot +-10 min en los N dias previos; por pixel,
    mediana de los k candidatos con BT C14 mas tibia, en las 4 bandas con los MISMOS candidatos."""
    cands = []
    for d in range(1, N + 1):
        for m in (-10, 0, 10):
            c = load(dt - timedelta(days=d) + timedelta(minutes=m), universo)
            if c is not None:
                cands.append(c)
    if len(cands) < 3:
        return None, len(cands)
    s14 = np.stack([c["b14"] for c in cands]); s14f = np.where(np.isfinite(s14), s14, -1e9)
    idx = np.argsort(-s14f, axis=0)[:k]
    out = {}
    for b in ("b11", "b13", "b14", "b15"):
        s = np.stack([c[b] for c in cands])
        out[b] = np.median(np.take_along_axis(s, idx, axis=0), axis=0)
    return out, len(cands)


# --------------------------------------------------------------- el metodo
def poly_b12(b87):
    return 4.2645 - 5.823 * b87 + 2.446 * b87 ** 2


def mascaras(sc, ref, banda10, tref):
    """Mascaras por prueba para una escena. banda10 = 'b14' o 'b13'. Devuelve dict de arrays bool y
    contadores del filtro beta. ref puede ser None (entonces beta no medible en toda la escena)."""
    b10, b87, b12 = sc[banda10], sc["b11"], sc["b15"]
    fin = np.isfinite(b10) & np.isfinite(b87) & np.isfinite(b12)
    btd = b10 - b12
    s = btd + (b10 - b87)
    t1 = fin & (btd < -2.0)
    t2 = fin & (s < 1.5)
    t3 = fin & (btd >= -2.0) & (btd <= -0.7)
    tent = (t2 | t3) & ~t1
    med = np.zeros(b10.shape, bool); quita = np.zeros(b10.shape, bool)
    if ref is not None and tref is not None:
        r10, r87, r12 = ref[banda10], ref["b11"], ref["b15"]
        c10 = CO[13] if banda10 == "b13" else CO[14]
        ok = fin & np.isfinite(r10) & np.isfinite(r87) & np.isfinite(r12) & \
            (b10 < r10) & (b87 < r87) & (b12 < r12)
        with np.errstate(invalid="ignore", divide="ignore"):
            e10 = cloud_emissivity(np.where(ok, b10, 250.0), tref, np.where(ok, r10, 260.0), c10)
            e87 = cloud_emissivity(np.where(ok, b87, 250.0), tref, np.where(ok, r87, 260.0), CO[11])
            e12 = cloud_emissivity(np.where(ok, b12, 250.0), tref, np.where(ok, r12, 260.0), CO[15])
            be87 = beta_ratio(e87, e10); be12 = beta_ratio(e12, e10)
        med = ok & (e10 >= 0.02) & np.isfinite(be87) & np.isfinite(be12)
        r_lo = med & (be87 <= 0.7); r_hi = med & (be87 >= 1.2)
        r_pol = med & ~r_lo & ~r_hi & (be12 > poly_b12(be87))
        quita = r_lo | r_hi | r_pol
        cont = {"tent": int(tent.sum()), "tent_medible": int((tent & med).sum()),
                "quita_lo": int((tent & r_lo).sum()), "quita_hi": int((tent & r_hi).sum()),
                "quita_pol": int((tent & r_pol).sum())}
    else:
        cont = {"tent": int(tent.sum()), "tent_medible": 0, "quita_lo": 0, "quita_hi": 0, "quita_pol": 0}
    return {"t1": t1, "t2": t2, "t3": t3, "tent": tent, "med": med, "quita": quita, "s": s, "btd": btd,
            "d87": b10 - b87}, cont


def coherencia(m):
    cnt = ndimage.convolve(m.astype(int), BOX3, mode="constant", cval=0)
    return m & (cnt >= 6)


def config_mask(M, nombre):
    base = M["t1"] | M["tent"]
    if nombre == "L0":
        return base
    if nombre == "L1":
        return coherencia(base)
    if nombre == "L2":
        return coherencia(M["t1"] | (M["tent"] & M["med"] & ~M["quita"]))
    if nombre == "L3":
        return coherencia(M["t1"] | (M["tent"] & ~(M["med"] & M["quita"])))
    raise ValueError(nombre)


CONFIGS = []
for banda in ("b14", "b13"):
    CONFIGS += [("L0", banda, None), ("L1", banda, None)]
    for tref in (255.0, 215.0):
        CONFIGS += [("L2", banda, tref), ("L3", banda, tref)]
PRINCIPAL = ("L2", "b14", 255.0)


def cname(c):
    n, b, t = c
    return f"{n}_{'C14' if b == 'b14' else 'C13'}" + (f"_T{int(t)}" if t else "")


def anclado(m):
    lab, n = ndimage.label(m, structure=EIGHT)
    if n == 0:
        return False
    ids = np.unique(lab[SEED & m]); ids = ids[ids > 0]
    if len(ids) == 0:
        return False
    tam = np.bincount(lab.ravel(), minlength=n + 1)
    return bool((tam[ids] >= 2).any())


# --------------------------------------------------------------- conjuntos (identicos al 17-11)
TAB = pd.read_csv(R.CUADROS)
_pos = TAB[TAB.toca_crater_10km == 1].slot_utc
POS = {d: [datetime.strptime(s, "%Y-%m-%d %H:%M") for s in _pos if s.startswith(f"2026-11-{d:02d}")]
       for d in (8, 10, 11, 14)}


def slots(day, h0, h1):
    t = day.replace(hour=h0[0], minute=h0[1]); out = []
    while t <= day.replace(hour=h1[0], minute=h1[1]):
        out.append(t); t += timedelta(minutes=10)
    return out


NEG_AJ, NEG_PR = [1, 2, 3, 4, 5, 6], [9, 12, 13, 15]
GRUPOS = {}
for d in (8, 10):
    for dt in POS[d]: GRUPOS[dt] = ("pos_aj", d)
for d in (11, 14):
    for dt in POS[d]: GRUPOS[dt] = ("pos_pr", d)
for d in NEG_AJ + NEG_PR:
    for dt in slots(datetime(2026, 11, d), (14, 0), (23, 50)):
        if dt.minute % 20 == 0:
            GRUPOS[dt] = ("neg_aj" if d in NEG_AJ else "neg_pr", d)
for dt in slots(datetime(2026, 11, 16), (8, 20), (12, 0)):
    GRUPOS[dt] = ("d16", 16)

HUE = np.load(R.HUELLAS); HUED = np.load(R.HUELLAS_DIL)


def main():
    t0 = time.time()
    log = open(os.path.join(OUT, "analisis.log"), "w", encoding="utf-8")

    def P(*a):
        s = " ".join(str(x) for x in a); print(s, flush=True); log.write(s + "\n"); log.flush()

    targets = sorted(GRUPOS)
    faltan = [dt for dt in targets if load(dt, SNAP) is None]
    faltan13 = [dt for dt in targets if key(dt) + ".npz" in SNAP and key(dt) + ".npz" not in HAS13]
    targets = [dt for dt in targets if load(dt, SNAP) is not None]
    P("targets", len(targets), "faltan", len(faltan), "de ellos sin C13 (pero con C11/14/15):", len(faltan13))
    conteo = pd.Series([GRUPOS[d][0] for d in targets]).value_counts().to_dict()
    P("por grupo", conteo)

    # ---- escena por escena: mascaras de las 12 configuraciones
    filas = []; cont_beta = []; diag = []
    masks_pos = {}
    for i, dt in enumerate(targets):
        g, d = GRUPOS[dt]
        sc = load(dt, SNAP); ref, nc = referencia(dt, SNAP)
        kk = key(dt).replace("_", "_")
        hd = HUED[kk] if kk in HUED.files else np.zeros(LAT.shape, bool)
        hu = HUE[kk] if kk in HUE.files else np.zeros(LAT.shape, bool)
        for c in CONFIGS:
            n, banda, tref = c
            M, cont = mascaras(sc, ref, banda, tref)
            m = config_mask(M, n)
            near = m & NEAR30
            filas.append({"cfg": cname(c), "slot": f"{dt:%Y-%m-%d %H:%M}", "grupo": g, "dia": d,
                          "ncand_ref": nc, "det": anclado(m), "npx": int(m.sum()),
                          "n_near": int(near.sum()), "n_in": int((near & hd).sum())})
            if n == "L2":
                cont.update(cfg=cname(c), slot=f"{dt:%Y-%m-%d %H:%M}", grupo=g,
                            tent_huella=int((M["tent"] & hu).sum()),
                            medible_huella=int((M["tent"] & M["med"] & hu).sum()))
                cont_beta.append(cont)
            if g.startswith("pos") and hu.any():
                masks_pos.setdefault(dt, {})[cname(c)] = m[hu]
        for banda in ("b14", "b13"):
            M, _ = mascaras(sc, None, banda, None)
            if g.startswith("pos") and hu.any():
                sel = hu
                diag.append({"conj": "huella_pos", "banda": banda, "s": M["s"][sel], "btd": M["btd"][sel],
                             "d87": M["d87"][sel]})
            elif g.startswith("neg"):
                sel = SEED & np.isfinite(M["s"])
                diag.append({"conj": "disco10_neg", "banda": banda, "s": M["s"][sel], "btd": M["btd"][sel],
                             "d87": M["d87"][sel]})
        if i % 100 == 0:
            P(f"escena {i}/{len(targets)} {time.time()-t0:.0f}s")
    df = pd.DataFrame(filas); df.to_csv(os.path.join(OUT, "por_scan.csv"), index=False)
    pd.DataFrame(cont_beta).to_csv(os.path.join(OUT, "filtro_beta.csv"), index=False)

    # ---- vara del 17-11
    res = []
    for c in CONFIGS:
        x = df[df.cfg == cname(c)]; r = {"cfg": cname(c)}
        for g in ("pos_aj", "pos_pr"):
            s = x[x.grupo == g]; r[f"sens_{g[4:]}"] = s.det.mean(); r[f"n_{g}"] = len(s); r[f"det_{g}"] = int(s.det.sum())
            r[f"coinc_{g[4:]}"] = s.n_in.sum() / s.n_near.sum() if s.n_near.sum() else float("nan")
            r[f"px30_{g[4:]}"] = int(s.n_near.sum())
        for g in ("neg_aj", "neg_pr"):
            s = x[x.grupo == g]; r[f"fa_{g[4:]}"] = s.det.mean(); r[f"fa_n_{g[4:]}"] = int(s.det.sum()); r[f"n_{g}"] = len(s)
            pdia = s.groupby("dia").det.sum().astype(int).to_dict(); r[f"fa_dia_{g[4:]}"] = json.dumps(pdia)
            r[f"fa_max_dia_{g[4:]}"] = max(pdia.values()); r[f"px_scan_{g[4:]}"] = s.npx.mean()
        s = x[x.grupo == "d16"]; r["d16"] = s.det.mean(); r["d16_n"] = f"{int(s.det.sum())}/{len(s)}"
        for sfx in ("pr", "aj"):
            k = (r[f"sens_{sfx}"] >= 0.5, r[f"fa_{sfx}"] <= 0.02 and r[f"fa_max_dia_{sfx}"] <= 3,
                 r["d16"] <= 0.10, bool(np.isfinite(r[f"coinc_{sfx}"]) and r[f"coinc_{sfx}"] >= 0.5))
            r[f"cumple_{sfx}"] = "".join("S" if v else "n" for v in k)
        res.append(r)
    tab = pd.DataFrame(res); tab.to_csv(os.path.join(OUT, "vara.csv"), index=False)
    P("\n== VARA (cumple_xx = criterios 1,2,3,4: S/n) ==")
    P(tab[["cfg", "det_pos_aj", "n_pos_aj", "det_pos_pr", "n_pos_pr", "fa_n_aj", "fa_max_dia_aj", "fa_n_pr",
           "fa_max_dia_pr", "d16_n", "coinc_aj", "px30_aj", "coinc_pr", "px30_pr", "px_scan_aj", "px_scan_pr",
           "cumple_aj", "cumple_pr"]].to_string(index=False))

    # ---- control pareado por pixel (cache completo)
    pares = []
    neg_dias = NEG_AJ + NEG_PR
    for dt in sorted(masks_pos):
        kk = key(dt); hu = HUE[kk]
        if hu.sum() < 3:
            continue
        sc = load(dt, SNAP); med_pos = np.nanmedian(sc["b14"][hu])
        mejor = None
        for d in neg_dias:
            for dm in (0, -10, 10):
                cdt = datetime(2026, 11, d, dt.hour, dt.minute) + timedelta(minutes=dm)
                fila = TAB[TAB.slot_utc == f"{cdt:%Y-%m-%d %H:%M}"]
                if fila.empty or int(fila.publicado.iloc[0]) != 1:
                    continue
                fr = fila.iloc[0]
                if fr.deteccion > 0 and not (fr.dist_min_km > 50):
                    continue
                c = load(cdt, FULL)
                if c is None:
                    continue
                dif = abs(np.nanmedian(c["b14"][hu]) - med_pos)
                if mejor is None or dif < mejor[0]:
                    mejor = (dif, cdt)
                break  # minuto exacto si existe; si no, +-10
        if mejor is None or mejor[0] > 3.0:
            pares.append({"pos": f"{dt:%Y-%m-%d %H:%M}", "ctrl": None, "dif_bt": None if mejor is None else mejor[0],
                          "npx": int(hu.sum())})
            continue
        cdt = mejor[1]; csc = load(cdt, FULL); cref, _ = referencia(cdt, FULL)
        pref, _ = referencia(dt, FULL)
        fila = {"pos": f"{dt:%Y-%m-%d %H:%M}", "ctrl": f"{cdt:%Y-%m-%d %H:%M}", "dif_bt": mejor[0], "npx": int(hu.sum())}
        for c in CONFIGS:
            n, banda, tref = c
            Mp, _ = mascaras(sc, pref, banda, tref); Mc, _ = mascaras(csc, cref, banda, tref)
            fila[f"P_{cname(c)}"] = int(config_mask(Mp, n)[hu].sum())
            fila[f"C_{cname(c)}"] = int(config_mask(Mc, n)[hu].sum())
        for banda in ("b14", "b13"):
            Mc, _ = mascaras(csc, None, banda, None)
            diag.append({"conj": "huella_ctrl", "banda": banda, "s": Mc["s"][hu], "btd": Mc["btd"][hu],
                         "d87": Mc["d87"][hu]})
        pares.append(fila)
    pp = pd.DataFrame(pares); pp.to_csv(os.path.join(OUT, "pares.csv"), index=False)
    ok = pp[pp.ctrl.notna()]
    P(f"\n== CONTROL PAREADO == positivos con huella>=3: {len(pp)}, con control: {len(ok)}, "
      f"sin control (>3 K o sin candidato): {len(pp) - len(ok)}; px huella con control: {int(ok.npx.sum())}; "
      f"dif BT C14 mediana {ok.dif_bt.median():.2f} K")
    pc = []
    for c in CONFIGS:
        Pf = ok[f"P_{cname(c)}"].sum() / ok.npx.sum(); Cf = ok[f"C_{cname(c)}"].sum() / ok.npx.sum()
        pc.append({"cfg": cname(c), "P": Pf, "C": Cf, "P_menos_C": Pf - Cf})
    pc = pd.DataFrame(pc); pc.to_csv(os.path.join(OUT, "pareado.csv"), index=False)
    P(pc.to_string(index=False))

    # ---- diagnostico fisico
    P("\n== DIAGNOSTICO: percentiles 5/25/50/75/95 ==")
    dg = []
    for conj in ("huella_pos", "huella_ctrl", "disco10_neg"):
        for banda in ("b14", "b13"):
            xs = [r for r in diag if r["conj"] == conj and r["banda"] == banda]
            if not xs:
                continue
            row = {"conj": conj, "banda10": "C14" if banda == "b14" else "C13"}
            for v in ("s", "btd", "d87"):
                a = np.concatenate([r[v] for r in xs]); a = a[np.isfinite(a)]
                row["n"] = len(a)
                row[v] = " / ".join(f"{q:.2f}" for q in np.percentile(a, [5, 25, 50, 75, 95]))
                if v == "s":
                    row["frac_s<1.5"] = float((a < 1.5).mean())
            dg.append(row)
    dg = pd.DataFrame(dg); dg.to_csv(os.path.join(OUT, "diagnostico.csv"), index=False)
    P(dg.to_string(index=False))

    fb = pd.DataFrame(cont_beta)
    P("\n== FILTRO BETA (L2, sumas sobre todas las escenas) ==")
    P(fb.groupby(["cfg", "grupo"])[["tent", "tent_medible", "quita_lo", "quita_hi", "quita_pol", "tent_huella",
                                    "medible_huella"]].sum().to_string())
    P(f"\nlisto {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
