r"""S21c: pruebas A (deteccion en GOES-18), B (altura por estereo) y C (franja de Landsat del 25-10), tal como
las fija criterio_2026-11-24.md (§5, §6, §7). Requiere s21c_bajar.py y s21c_registro.py ya corridos.

Salida: resultados/medir.json y medir.txt; mapas por cuadro en D:\goes_notas\s21\c\medir_mapas.npz (para figuras).
"""
import json
import math
import os
import sys
from datetime import datetime, timedelta

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s21c_comun as K  # noqa: E402
import s21c_registro as REG  # noqa: E402

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resultados")
N = 81
PULSOS = {"E9": (datetime(2026, 10, 28, 15, 34), 1320), "E10": (datetime(2026, 10, 28, 17, 38), 2200),
          "E11": (datetime(2026, 10, 28, 20, 32), 2440), "E12": (datetime(2026, 10, 28, 21, 49), 2020)}
ALTOS = ("E10", "E11", "E12")
DIAS_CTRL = [datetime(2026, 9, 21), datetime(2026, 10, 15), datetime(2026, 10, 16), datetime(2026, 10, 17)]
T_OBS = {s: K.t_obs(s)[1] for s in (18, 19)}
C_INY = (0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20)
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


# ---------- datos ----------
_cache = {}


def cuadro(sat, dt):
    k = (sat, dt)
    if k not in _cache:
        p = K.ruta_cuadro(sat, dt)
        if not os.path.exists(p):
            _cache[k] = None
        else:
            f = np.load(p)
            R = f["rad"].astype(float) * float(f["kappa0"])
            _cache[k] = (R, f["dqf"], int(f["fila0"]), int(f["col0"]))
    return _cache[k]


# ---------- ACMF por cuadro (regla E1, igual que s21c_controles.py) ----------
def e1_por_cuadro():
    import s21c_controles_lib as CL
    return CL.frac_por_cuadro()


# ---------- geometria en la ventana ----------
def sesgo(sat):
    with open(os.path.join(BASE, "registro.json"), encoding="utf-8") as f:
        v = json.load(f)[f"g{sat}_veredicto"]
    return (v["sesgo_filas"], v["sesgo_col"]) if v["verificada"] else (0.0, 0.0), v


def a_ventana(sat, lat, lon, h_m, fila0, col0, b):
    r, c = K.a_pixel(sat, lat, lon, h_m)
    return r - fila0 + b[0], c - col0 + b[1]


def region_S(sat, fila0, col0, b):
    hs = np.arange(K.CRATER_KM + 0.3, K.CRATER_KM + 4.0 + 1e-9, 0.1) * 1000
    pts = [(0.0, 0.0)]
    for rad in np.arange(0.25, 6.0 + 1e-9, 0.25):
        nang = max(8, int(2 * math.pi * rad / 0.25))
        pts += [(rad * math.sin(a), rad * math.cos(a)) for a in np.linspace(0, 2 * math.pi, nang, endpoint=False)]
    de, dn = np.array(pts).T
    lat, lon = K.desplazar(K.VENT[0], K.VENT[1], de, dn)
    S = np.zeros((N, N), bool)
    for h in hs:
        r, c = a_ventana(sat, lat, lon, h, fila0, col0, b)
        ri, ci = np.rint(r).astype(int), np.rint(c).astype(int)
        ok = (ri >= 0) & (ri < N) & (ci >= 0) & (ci < N)
        S[ri[ok], ci[ok]] = True
    return ndimage.binary_dilation(S, np.ones((3, 3), bool))


# ---------- estadistico ----------
def estadistico(Rt, Rp, S, dqf_ok):
    d = Rt - Rp
    ok = np.isfinite(d) & dqf_ok
    d = d - np.nanmedian(d[ok])
    F = ok & ~S
    sig = 1.4826 * np.nanmedian(np.abs(d[F] - np.nanmedian(d[F])))
    an = ok & S & (np.abs(d) > 4 * sig)
    lab, n = ndimage.label(an, structure=np.ones((3, 3)))
    if n == 0:
        return 0.0, 0, sig, d, None
    sumas = ndimage.sum(np.abs(np.nan_to_num(d)), lab, index=np.arange(1, n + 1))
    k = int(np.argmax(sumas)) + 1
    comp = lab == k
    return float(sumas[k - 1]), int(comp.sum()), float(sig), d, comp


def par(sat, t, S):
    a, b = cuadro(sat, t), cuadro(sat, t - timedelta(minutes=10))
    if a is None or b is None:
        return None
    dq = (a[1] == 0) & (b[1] == 0)
    if (~dq[S]).mean() > 0.10:
        return "DQF"
    return a[0], b[0], dq


def pval(M, nulo):
    nulo = np.asarray(nulo)
    return (1 + int((nulo >= M).sum())) / (1 + len(nulo))


def mirada(sat, t):
    return t + timedelta(seconds=T_OBS[sat])


def en_pulso(t):
    m = mirada(18, t)
    return any(ini <= m <= ini + timedelta(minutes=30) for ini, _ in PULSOS.values())


def columna(sat, fila0, col0, b, H_m):
    """Pixeles de una columna vertical de 1 px de ancho desde el crater hasta H_m sobre el crater."""
    r0, c0 = a_ventana(sat, *K.VENT, K.CRATER_KM * 1000, fila0, col0, b)
    r1, c1 = a_ventana(sat, *K.VENT, K.CRATER_KM * 1000 + H_m, fila0, col0, b)
    s = np.linspace(0, 1, 200)
    rr, cc = np.rint(r0 + s * (r1 - r0)).astype(int), np.rint(c0 + s * (c1 - c0)).astype(int)
    m = np.zeros((N, N), bool)
    ok = (rr >= 0) & (rr < N) & (cc >= 0) & (cc < N)
    m[rr[ok], cc[ok]] = True
    return m


# ---------- prueba A ----------
def prueba_A(sat, S, fila0, col0, b, acm):
    dias28 = [datetime(2026, 10, 28, 15, 0) + timedelta(minutes=10 * i) for i in range(46)]
    nulo_a, nulo_b, pares_nulos = [], [], []
    for t in dias28:
        if en_pulso(t):
            continue
        x = par(sat, t, S)
        if x is None or isinstance(x, str):
            continue
        M = estadistico(x[0], x[1], S, x[2])[0]
        nulo_a.append(M)
        pares_nulos.append((t, x))
    for d in DIAS_CTRL:
        for i in range(52):
            t = d.replace(hour=14) + timedelta(minutes=10 * i)
            if t.hour > 22 or (t.hour == 22 and t.minute > 30):
                break
            fa, fb = acm.get(t), acm.get(t - timedelta(minutes=10))
            if fa is None or fb is None or fa < 0.8 or fb < 0.8:
                continue
            x = par(sat, t, S)
            if x is None or isinstance(x, str):
                continue
            M = estadistico(x[0], x[1], S, x[2])[0]
            nulo_b.append(M)
            pares_nulos.append((t, x))
    nulo = nulo_a + nulo_b
    log(f"GOES-{sat}: nulo (a) 28-10 n={len(nulo_a)}, (b) controles n={len(nulo_b)}; "
        f"M nulo: mediana {np.median(nulo):.3f}, p95 {np.percentile(nulo, 95):.3f}, max {max(nulo):.3f}")
    res = {"nulo_a": nulo_a, "nulo_b": nulo_b, "pulsos": {}}
    mapas = {}
    for nom, (ini, H) in PULSOS.items():
        cands = sorted(t for t in dias28 + [datetime(2026, 10, 28, 22, 40)]
                       if mirada(18, t) >= ini)[:2]
        pre = cands[0] - timedelta(minutes=10)
        filas = {}
        for rot, t in (("pre", pre), ("post1", cands[0]), ("post2", cands[1])):
            x = par(sat, t, S)
            if x is None or isinstance(x, str):
                filas[rot] = {"t": f"{t:%H:%M}", "estado": "SIN DATO" if x is None else "DQF"}
                continue
            M, n, sig, d, comp = estadistico(x[0], x[1], S, x[2])
            filas[rot] = {"t": f"{t:%H:%M}", "mirada": f"{mirada(sat, t):%H:%M:%S}", "M": round(M, 4), "n": n,
                          "sigma": round(sig, 4), "p": round(pval(M, nulo), 4),
                          "p_a": round(pval(M, nulo_a), 4), "p_b": round(pval(M, nulo_b), 4) if nulo_b else None}
            mapas[f"g{sat}_{nom}_{rot}_R"] = x[0]
            mapas[f"g{sat}_{nom}_{rot}_dR"] = d
            mapas[f"g{sat}_{nom}_{rot}_comp"] = comp if comp is not None else np.zeros((N, N), bool)
            if comp is not None:
                w = np.abs(np.nan_to_num(d)) * comp
                rr, cc = np.nonzero(comp)
                filas[rot]["centroide"] = [float((w[rr, cc] * rr).sum() / w[rr, cc].sum()),
                                           float((w[rr, cc] * cc).sum() / w[rr, cc].sum())]
                filas[rot]["disp_px"] = float(np.sqrt(np.average((rr - filas[rot]["centroide"][0]) ** 2 +
                                                                 (cc - filas[rot]["centroide"][1]) ** 2,
                                                                 weights=w[rr, cc])) / math.sqrt(len(rr)))
                filas[rot]["pix"] = [[int(a), int(c)] for a, c in zip(rr, cc)]
        res["pulsos"][nom] = {"H": H, "cuadros": filas}
        if sat == 18:
            # poder por inyeccion de columna
            col = columna(18, fila0, col0, b, H)
            c80 = {}
            for signo, nomb in ((-1, "oscura"), (1, "clara")):
                c80[nomb] = None
                for c in C_INY:
                    det = 0
                    for _, (Rt, Rp, dq) in pares_nulos:
                        Ri = Rt.copy()
                        Ri[col] += signo * c
                        M = estadistico(Ri, Rp, S, dq)[0]
                        det += pval(M, nulo) <= 0.05
                    if det / len(pares_nulos) >= 0.8:
                        c80[nomb] = c
                        break
            p1 = filas["post1"].get("p")
            p2 = filas["post2"].get("p")
            ps = [p for p in (p1, p2) if p is not None]
            pp = min(1.0, 2 * min(ps)) if ps else None
            peor = None if None in c80.values() else max(c80.values())
            ncomp = [filas[r]["n"] for r in ("post1", "post2") if filas[r].get("p") == min(ps)][0] if ps else 0
            ppre = filas["pre"].get("p")
            if pp is None or ppre is None:
                ver = "SIN DATO"
            elif pp <= 0.05 and ncomp >= 3 and ppre > 0.05:
                ver = "SEÑAL"
            elif pp <= 0.05 and ppre <= 0.05:
                ver = "ACTIVIDAD PREVIA"
            elif pp <= 0.05:
                ver = "NO CONCLUYENTE (p <= 0,05 con componente de menos de 3 px: caso no previsto en el criterio)"
            elif peor is not None and peor <= 0.10:
                ver = "SIN SEÑAL"
            else:
                ver = "SIN PODER"
            res["pulsos"][nom].update({"p_pulso": pp, "c80": c80, "veredicto": ver})
            log(f"  {nom} (H {H} m): pre {filas['pre']}, post1 p {p1}, post2 p {p2} -> p_pulso {pp}; "
                f"c80 {c80}; VEREDICTO {ver}")
        else:
            log(f"  {nom} GOES-19 (sin veredicto): " + "; ".join(
                f"{r} {filas[r].get('t')} p {filas[r].get('p')} n {filas[r].get('n')}" for r in filas))
    return res, mapas


# ---------- prueba B ----------
def prueba_B(A18, A19, fila0, b, nav):
    out = {}
    km_px18 = 1 / math.hypot(1.116, 1.332)
    for nom in ALTOS:
        if A18["pulsos"][nom].get("veredicto") != "SEÑAL":
            continue
        for rot in ("post1", "post2"):
            f18 = A18["pulsos"][nom]["cuadros"][rot]
            f19 = A19["pulsos"][nom]["cuadros"][rot]
            if f18.get("p", 1) > 0.05 or "centroide" not in f18:
                continue
            fila = {"p18": f18["p"], "p19": f19.get("p")}
            # GOES-18 solo: largo a lo largo de la columna
            r0, c0 = a_ventana(18, *K.VENT, K.CRATER_KM * 1000, fila0[18][0], fila0[18][1], b[18])
            u = np.array([1.116, 1.332]) / math.hypot(1.116, 1.332)
            lar = max(((r - r0) * u[0] + (c - c0) * u[1]) for r, c in f18["pix"])
            fila["altura_mono_km_sobre_crater"] = round(lar * km_px18, 2)
            if f19.get("p") is not None and f19["p"] <= 0.10 and "centroide" in f19:
                obs = {}
                for s, f in ((18, f18), (19, f19)):
                    obs[s] = (f["centroide"][0] + fila0[s][0] - b[s][0], f["centroide"][1] + fila0[s][1] - b[s][1])
                de, dn, h, rms, J = K.triangular(obs)
                sig_px = max(0.5, f18.get("disp_px", 0), f19.get("disp_px", 0))
                cov = np.linalg.inv(J.T @ J) * sig_px ** 2
                sh = math.sqrt(cov[2, 2] + 0.10 ** 2 + (nav[18]["diferencia_px"] * km_px18) ** 2)
                fila.update({"de_km": round(de, 2), "dn_km": round(dn, 2), "h_km": round(h, 2),
                             "h_sobre_crater_km": round(h - K.CRATER_KM, 2), "sigma_h_km": round(sh, 2),
                             "residuo_px": round(rms, 2), "altura_medida": rms <= 1.5})
                Hr = A18["pulsos"][nom]["H"] / 1000
                fila["compatible_REAV"] = abs(h - K.CRATER_KM - Hr) < 2 * sh + 0.3
            out[f"{nom}_{rot}"] = fila
            log(f"  Estereo {nom} {rot}: {fila}")
    if not out:
        log("  Prueba B: no corre (ningun pulso con SEÑAL en GOES-18).")
    return out


# ---------- prueba C ----------
def prueba_C(fila0, b):
    from pyproj import Transformer  # noqa: F401
    glat, glon = REG.grilla()
    z = np.load(r"D:\goes_notas\s20b\mascara_2026-10-25.npz")
    pl = z["pluma"]
    DEN = {}
    H_vaac = float(z["H"])
    out = {}

    def fraccion(sat, lat, lon, h, b_):
        r, c = a_ventana(sat, lat, lon, h, fila0[sat][0], fila0[sat][1], b_)
        ri, ci = np.rint(r).astype(int), np.rint(c).astype(int)
        ok = (ri >= 0) & (ri < N) & (ci >= 0) & (ci < N)
        m = np.zeros((N, N))
        np.add.at(m, (ri[ok], ci[ok]), 1)
        return m

    for sat in (18, 19):
        ctrl = {}
        res = {}
        for rot in ("14:20", "14:30", "14:40"):
            hh, mm = map(int, rot.split(":"))
            ev = cuadro(sat, datetime(2026, 10, 25, hh, mm))
            cs = [cuadro(sat, datetime(2026, 10, d, hh, mm)) for d in (15, 16, 17)]
            cs = [c[0] for c in cs if c is not None]
            if ev is None or len(cs) < 2:
                res[rot] = {"estado": "SIN DATO"}
                continue
            dR = ev[0] - np.nanmedian(np.stack(cs), 0)
            ctrl[rot] = dR

            def A_de(lat, lon, h):
                kden = (sat, round(float(h), 1))
                if kden not in DEN:
                    DEN[kden] = fraccion(sat, glat.ravel(), glon.ravel(), h, b[sat])
                den = DEN[kden]
                num = fraccion(sat, lat, lon, h, b[sat])
                f = np.where(den > 0, num / np.maximum(den, 1), 0)
                P = f >= 0.25
                if P.sum() == 0:
                    return None, f, P
                ring = ndimage.binary_dilation(P, np.ones((3, 3)), iterations=3) & ~P & (f == 0)
                return float(np.nanmean(dR[P]) - np.nanmean(dR[ring])), f, P

            lat0, lon0 = glat[pl], glon[pl]
            A0, f0, P0 = A_de(lat0, lon0, H_vaac)
            fila = {"A": None if A0 is None else round(A0, 4), "nP": int(P0.sum())}
            if rot == "14:30" and A0 is not None:
                nul = []
                for de in range(-12, 13):
                    for dn in range(-12, 13):
                        if de == 0 and dn == 0:
                            continue
                        la, lo = K.desplazar(lat0, lon0, de, dn)
                        A1, f1, P1 = A_de(la, lo, H_vaac)
                        if A1 is None or ((f1 > 0) & (f0 > 0)).any():
                            continue
                        nul.append(A1)
                nul = np.array(nul)
                fila["n_corrimientos"] = int(len(nul))
                fila["p"] = round(float((1 + (np.abs(nul) >= abs(A0)).sum()) / (1 + len(nul))), 4)
                fila["veredicto"] = "SEÑAL" if fila["p"] <= 0.05 else "SIN SEÑAL"
                barrido = {}
                for h in np.arange(3.2, 7.0 + 1e-9, 0.2):
                    a, _, _ = A_de(lat0, lon0, h * 1000)
                    barrido[f"{h:.1f}"] = None if a is None else round(a, 4)
                fila["A_por_altura"] = barrido
                val = {k: abs(v) for k, v in barrido.items() if v is not None}
                fila["altura_max_A_km"] = max(val, key=val.get) if val else None
                np.savez_compressed(os.path.join(K.TRABAJO, f"pruebaC_g{sat}.npz"), dR=dR, f0=f0, P0=P0,
                                    ev=ev[0])
            res[rot] = fila
        out[f"g{sat}"] = res
        log(f"  Prueba C GOES-{sat}: {res}")
    return out


if __name__ == "__main__":
    acm = e1_por_cuadro()
    fila0, b, nav, S = {}, {}, {}, {}
    for sat in (18, 19):
        c = cuadro(sat, datetime(2026, 10, 28, 17, 30))
        fila0[sat] = (c[2], c[3])
        b[sat], nav[sat] = sesgo(sat)
        S[sat] = region_S(sat, c[2], c[3], b[sat])
        log(f"GOES-{sat}: sesgo de navegacion usado {b[sat]} ({nav[sat]}); region S {int(S[sat].sum())} px")
    A, mapas = {}, {}
    for sat in (18, 19):
        A[sat], m = prueba_A(sat, S[sat], fila0[sat][0], fila0[sat][1], b[sat], acm)
        mapas.update(m)
    altos = [A[18]["pulsos"][k]["veredicto"] for k in ALTOS]
    nS, nSS = altos.count("SEÑAL"), altos.count("SIN SEÑAL")
    glob = "SEÑAL" if nS >= 2 else ("SIN SEÑAL" if nS == 0 and nSS >= 2 else "NO CONCLUYENTE")
    log(f"VEREDICTO GLOBAL prueba A (E10, E11, E12): {altos} -> {glob}")
    B = prueba_B(A[18], A[19], fila0, b, nav)
    C = prueba_C(fila0, b)
    mapas["S18"], mapas["S19"] = S[18], S[19]
    np.savez_compressed(os.path.join(K.TRABAJO, "medir_mapas.npz"), **mapas)
    with open(os.path.join(BASE, "medir.json"), "w", encoding="utf-8") as f:
        json.dump({"A": {str(k): v for k, v in A.items()}, "global_A": glob, "B": B, "C": C,
                   "sesgo": {str(k): v for k, v in b.items()}, "nav": {str(k): v for k, v in nav.items()},
                   "fila0": {str(k): v for k, v in fila0.items()}}, f, indent=1, ensure_ascii=False)
    with open(os.path.join(BASE, "medir.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(LOG) + "\n")
