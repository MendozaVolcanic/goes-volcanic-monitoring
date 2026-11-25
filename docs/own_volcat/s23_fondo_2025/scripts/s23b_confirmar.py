r"""S23b: confirmación en días nuevos (desde el 25-11-2026) del detector con base y umbral de 2025 y nublado de
costumbre de 2026 congelado. Implementa criterio_S23b_2026-11-25.md (commits 97bdec1 y af46f12).

Subcomandos, en este orden:
  contar AAAA-MM-DD       respalda los PNG nuevos de VOLCAT (s23_volcat_respaldo.py) y clasifica P/N/otro con la regla
                          de H9 (s22b_volcat_clases.py) desde el 25-11 hasta el día dado. Escribe
                          resultados/volcat_clases_desde_25nov.csv. NO usa el detector: contar no gasta la prueba.
  bajar AAAA-MM-DDTHH     baja C14, C15 y ACMF desde el 24-11 00 UTC (arranque) hasta la hora dada a D:\goes_notas\s23\s23b.
  medir                   arma el cubo, corre las comprobaciones de instrumento y mide UNA vez (criterio §6: sólo con
                          20 P o más en 2 días nuevos o más; si no, se niega salvo con --vistazo, que no decide).
Lo grande queda en D:; al repo sólo van clases por cuadro y cifras.
"""
import csv
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
TRAB = r"D:\goes_notas\s23\s23b"
os.environ["H23_DIR"] = TRAB                     # los hijos de la bajada heredan el destino
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s23_medir as S  # noqa: E402
B, M, C29 = S.B, S.M, S.C29
sys.path.insert(0, os.path.join(S.OV, "s22b_pluma_vs_nubes", "scripts"))
sys.path.insert(0, os.path.join(S.OV, "h23_inyeccion", "scripts"))

ARRANQUE = datetime(2026, 11, 24)                # día de arranque (persistencia de las 00:00), no cuenta
NUEVO0 = datetime(2026, 11, 25)
CLASES = os.path.join(S.RES, "volcat_clases_desde_25nov.csv")
ESTAT = os.path.join(TRAB, "estat_2026.npy")
SHA_ESTAT = "e0f093eb6e441cc4"
PNG_S23 = r"D:\goes_notas\s23\volcat_png\Chile_Central_2_km\frames"
MIN_P, MIN_DIAS_P, MIN_P_EVAL = 20, 2, 10
R_MIN, P25_MAX, PN_MAX = 0.40, 0.01, 0.05


def contar(hasta):
    subprocess.run([sys.executable, "-I", os.path.join(AQUI, "s23_volcat_respaldo.py")], check=True)
    import s22b_volcat_clases as VC
    VC.PNG_DIRS[:] = [PNG_S23] + VC.PNG_DIRS
    fin = datetime.strptime(hasta, "%Y-%m-%d")
    dias, d = set(), NUEVO0
    while d <= fin:
        dias.add(f"{d:%Y-%m-%d}")
        d += timedelta(days=1)
    inv = VC.inventario(dias | {f"{ARRANQUE:%Y-%m-%d}"})
    cl = VC.clases(inv)
    with open(CLASES, "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["dt", "clase", "n_anc", "max_anc", "n50", "barra", "manto"])
        for dt in sorted(cl):
            if f"{dt:%Y-%m-%d}" in dias:
                r = inv[dt]
                wr.writerow([f"{dt:%Y-%m-%d %H:%M}", cl[dt], len(r["anc"]), max(r["anc"]) if r["anc"] else 0,
                             r["n50"], r["barra"], r["manto"]])
    cnt = {}
    for dt, c in cl.items():
        if f"{dt:%Y-%m-%d}" in dias:
            cnt.setdefault(f"{dt:%Y-%m-%d}", {"P": 0, "N": 0, "otro": 0})[c] += 1
    for k in sorted(cnt):
        print(k, cnt[k])
    nP = sum(v["P"] for v in cnt.values())
    dP = sum(1 for v in cnt.values() if v["P"])
    print(f"P en días nuevos: {nP} en {dP} días; la medida exige {MIN_P} en {MIN_DIAS_P} días:",
          "LISTO PARA MEDIR" if nP >= MIN_P and dP >= MIN_DIAS_P else "todavía no")


def bajar(hasta, n=8):
    import h23_bajar as BL
    import h23_bajar_acm as BA
    import h23_comun as K
    assert K.H23 == TRAB, K.H23
    fin = datetime.strptime(hasta, "%Y-%m-%dT%H")
    horas, h = [], ARRANQUE
    while h <= fin:
        horas.append(h)
        h += timedelta(hours=1)
    for nom, mod, carpeta in (("l1b", BL, K.L1B), ("acm", BA, BA.ACM)):
        os.makedirs(carpeta, exist_ok=True)
        t0, tot, sin = time.time(), 0, []
        with ProcessPoolExecutor(n) as ex:
            for f in as_completed([ex.submit(mod.hora, x) for x in horas]):
                try:
                    _, hechos, faltas = f.result()
                except Exception as e:  # noqa: BLE001
                    print("EXCEPCION", repr(e)[:120], flush=True)
                    continue
                tot += hechos
                sin += faltas
        print(f"FIN {nom}: {tot} cuadros, {len(sin)} sin dato, {time.time() - t0:.0f} s", flush=True)


def _cubo(dias):
    """BT11, ACM y M1 por (día, slot) con las comprobaciones de cubo_nuevo de S22b (I1 a I3)."""
    n = len(dias) * 144
    r = {b: np.full((n, S.NPIX), np.nan, "float32") for b in (14, 15)}
    acm = np.full((n, S.NPIX), 255, "uint8")
    co = {14: [], 15: []}
    pres, scan_dist, ult = 0, 0, -1
    for i in range(n):
        dt = dias[0] + timedelta(minutes=10 * i)
        f = os.path.join(TRAB, "l1b", f"{dt:%Y%m%d_%H%M}.npz")
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
        g = os.path.join(TRAB, "acm", f"{dt:%Y%m%d_%H%M}.npz")
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
            "ultimo": f"{dias[0] + timedelta(minutes=10 * ult):%Y-%m-%d %H:%M}", "scan_distinto": scan_dist,
            "congelados": cong, "bt11_en_rango": float(((v > 180) & (v < 330)).mean()) if v.size else 0.0,
            "acm_presentes": int((acm != 255).any(1).sum())}
    inst["falla"] = [k for k, ok in (("I1", inst["cobertura"] >= 0.95), ("I2", scan_dist == 0),
                                     ("I3", inst["bt11_en_rango"] >= 0.999 and cong == 0)) if not ok]
    m1 = np.full((n, M.NA), np.nan, np.float32)
    for i in range(n):
        if hay[i]:
            m1[i] = M.m1_cuadro(bt11[i], btd[i])
    nd = len(dias)
    return bt11.reshape(nd, 144, -1), acm.reshape(nd, 144, -1), m1.reshape(nd, 144, -1), inst


def medir(vistazo=False):
    with open(CLASES, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    ult = max(datetime.strptime(x["dt"][:10], "%Y-%m-%d") for x in filas)
    dias = [ARRANQUE + timedelta(days=i) for i in range((ult - ARRANQUE).days + 1)]
    CL = np.full((len(dias), 144), "", object)
    for x in filas:
        d = (datetime.strptime(x["dt"][:10], "%Y-%m-%d") - ARRANQUE).days
        CL[d, M.slot(x["dt"][11:16])] = x["clase"]
    nP = int((CL == "P").sum())
    dP = int(((CL == "P").any(1)).sum())
    if (nP < MIN_P or dP < MIN_DIAS_P) and not vistazo:
        print(f"criterio §6: {nP} P en {dP} días nuevos; hacen falta {MIN_P} en {MIN_DIAS_P}. No se mide.")
        return
    import hashlib
    estat = np.load(ESTAT)
    assert hashlib.sha256(estat.tobytes()).hexdigest()[:16] == SHA_ESTAT, "estat_2026 cambió: no es el congelado"
    bt, acm, m1, inst = _cubo(dias)
    D = S.Detector(ref="2025", con_blanco=False)
    FD, mm = D._nubes(acm, m1, estat)
    GATE = FD <= B.G_MAX
    B0 = D.base(None)
    U, _ = D.umbral(None)
    Sx = np.full(CL.shape, np.nan)
    Kx = np.full(CL.shape, -1, int)
    for d in range(len(dias)):
        for s in range(144):
            if GATE[d, s]:
                Sx[d, s], Kx[d, s], _ = M.estadistico(mm[d, s] - B0[s])
    _, sl25, al25, _ = S._seco_2025(D)
    r25 = S.azar_por_hora(sl25, al25)
    P, N, por_dia, eps_t, eps_h = [], [], [], 0, 0
    for d in range(1, len(dias)):                      # el día 0 (24-11) es sólo arranque
        F, ev = S.disparos(Sx, Kx, d, U)
        for s in np.flatnonzero(ev):
            a = B.alcanzado(F, ev, s)[1]
            if CL[d, s] == "P":
                P.append((d, s, a))
            elif CL[d, s] == "N":
                N.append((d, s, a))
        Ps = np.flatnonzero(CL[d] == "P")
        for ep in (M.episodios(list(Ps)) if len(Ps) else []):
            if ev[ep].any():
                eps_t += 1
                eps_h += bool(F[max(0, ep[0] - 3):min(144, ep[-1] + 4)].any())
        pe = [a for dd, _, a in P if dd == d]
        por_dia.append({"dia": f"{dias[d]:%Y-%m-%d}", "P": int(len(Ps)), "P_evaluados": len(pe),
                        "P_alcanzados": int(sum(pe)), "N_evaluados": int(sum(1 for dd, *_ in N if dd == d)),
                        "disparos": int(F.sum()), "tajadas": np.bincount(Kx[d][F], minlength=12).tolist(),
                        "horas_disparos": [M.hhmm(s) for s in np.flatnonzero(F)]})
    te, th = len(P), int(sum(a for *_, a in P))
    p25 = S.poisson_binomial_cola([r25[s] for _, s, _ in P], th) if te else None
    psl = {s for _, s, _ in P}
    cerca = [a for _, s, a in N if any(M.dslot(s, x) <= S.W_AZAR for x in psl)]
    pN = (float(stats.fisher_exact([[th, te - th], [int(sum(cerca)), len(cerca) - int(sum(cerca))]],
                                   alternative="greater")[1]) if te and cerca else None)
    R = th / te if te else None
    dias_P_eval = len({d for d, _, _ in P})
    if inst["falla"]:
        ver = "INVÁLIDA"
    elif te < MIN_P_EVAL or dias_P_eval < 2:
        ver = "NO DECIDIBLE"
    elif p25 <= P25_MAX and R >= R_MIN and pN is not None and pN <= PN_MAX:
        ver = "CONFIRMA"
    elif p25 <= P25_MAX:
        ver = "PARCIAL"
    else:
        ver = "NO CONFIRMA"
    out = {"veredicto": ver if not vistazo else f"VISTAZO (no decide): {ver}", "instrumento": inst,
           "P_total": nP, "dias_con_P": dP, "P_evaluados": te, "P_alcanzados": th, "R": R, "dias_con_P_evaluado": dias_P_eval,
           "E25": float(sum(r25[s] for _, s, _ in P)), "p25": p25, "N_cerca_de_P": len(cerca),
           "N_cerca_alcanzados": int(sum(cerca)), "pN": pN, "N_evaluados": len(N),
           "episodios": eps_t, "episodios_alcanzados": eps_h, "por_dia": por_dia}
    nombre = "s23b_vistazo.json" if vistazo else "s23b_resultado.json"
    json.dump(out, open(os.path.join(S.RES, nombre), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "contar":
        contar(sys.argv[2])
    elif c == "bajar":
        bajar(sys.argv[2])
    elif c == "medir":
        medir(vistazo="--vistazo" in sys.argv)
