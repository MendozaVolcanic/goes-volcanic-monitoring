r"""S26b: mide lo que fija criterio_2026-11-25.md (commit 2643ab0). ¿Los disparos nocturnos de la zona del cráter (S25a)
son el calor del cráter?

Reproduce con las funciones de s25a_medir.py, sin cambiar nada: el ensayo en seco de 2025 (tiene que dar 176 de 5.499)
y los disparos de 2026 (tienen que coincidir con D:\goes_notas\s25\s25a\tabla_2026.csv). Cruza con el estado de calor
de cada noche (D:\goes_notas\s26\s26b\calor_chillan_noches.json, de s26b_calor.py) y calcula E1 a E5.

Salida: resultados/s26b_resultado.json y D:\goes_notas\s26\s26b\noches_2026.csv.
Uso: python s26b_medir.py
"""
import csv
import json
import os
import sys
import time
import warnings
from collections import Counter
from datetime import date, datetime, timedelta, timezone

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore", RuntimeWarning)
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
REPO = os.path.abspath(os.path.join(OV, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "s25a_crater", "scripts"))
sys.path.insert(0, REPO)
import s25a_medir as Z  # noqa: E402
from src.process import vrp_nocturno as V  # noqa: E402

S, B, M, H24, C29 = Z.S, Z.B, Z.M, Z.H24, Z.C29
TRAB = r"D:\goes_notas\s26\s26b"
CHI = (-36.863, -71.377)
T25, T26 = datetime(2025, 9, 21, tzinfo=timezone.utc), datetime(2026, 9, 21, tzinfo=timezone.utc)
MIN_EV_NOCHE = 6
ANOM_T = 3.0
CAPA_BAJA_2025 = {"2025-09-30", "2025-10-03", "2025-10-28", "2025-11-06", "2025-11-15", "2025-11-17", "2025-11-18"}
IZ = np.arange(len(Z.ZONA))


def tiempo(t0, d, s):
    return t0 + timedelta(days=int(d), minutes=10 * int(s))


def nocturnos(t0, nd):
    noc = np.zeros((nd, 144), bool)
    clave = np.empty((nd, 144), object)
    for d in range(nd):
        for s in range(144):
            t = tiempo(t0, d, s)
            noc[d, s] = V.es_nocturno(t, *CHI)
            clave[d, s] = V.clave_noche(t).isoformat()
    return noc, clave


def fisher_mayor(a, na, b, nb):
    return float(stats.fisher_exact([[a, na - a], [b, nb - b]], alternative="greater")[1])


def cmh(tablas):
    """Cochran-Mantel-Haenszel (sin corrección de continuidad) y razón de odds común de Mantel-Haenszel.
    Cada tabla: (a, b, c, d) = (caliente con F, caliente sin F, frío con F, frío sin F)."""
    num = den = sa = se = sv = 0.0
    for a, b, c, d in tablas:
        n = a + b + c + d
        if n < 2:
            continue
        num += a * d / n
        den += b * c / n
        r1, r2, c1, c2 = a + b, c + d, a + c, b + d
        sa += a
        se += r1 * c1 / n
        sv += r1 * r2 * c1 * c2 / (n * n * (n - 1))
    if sv == 0:
        return None, None
    chi = (sa - se) ** 2 / sv
    return (num / den if den else float("inf")), float(stats.chi2.sf(chi, 1))


def main():
    t = time.time()
    # ---------- 2025, idéntico a s25a_medir.medir ----------
    btd25 = np.load(Z._npy("r25_btd"), mmap_mode="r")
    acm25 = np.load(Z._npy("r25_acm"))
    hay25 = np.isfinite(btd25[:, :, Z.ZONA[0]])
    est25 = Z.costumbre(acm25, hay25)
    FD25, DIN25 = Z.nubes(acm25, est25)
    G25 = FD25 <= B.G_MAX
    E125 = H24.despejada("chillan", acm25)
    USA25 = G25 & E125 & hay25
    btd25 = np.asarray(btd25)
    bctrl = Z.base(btd25, USA25, Z.CTRL)
    C25 = Z.regional(btd25, DIN25, bctrl)
    Z25 = np.ascontiguousarray(btd25[:, :, Z.ZONA])
    BZ = np.array([Z.base(Z25, USA25, IZ, excl=d) for d in range(Z.NR)])
    SR, PR = Z.tabla_S(Z25, C25, BZ, G25)
    UL = [Z.umbral(SR, excl=d) for d in range(Z.NR)]
    F25 = np.zeros((Z.NR, 144), bool)
    EV25 = np.zeros((Z.NR, 144), bool)
    for d in range(Z.NR):
        F25[d], EV25[d] = Z.disparos(SR, d, UL[d], UL[d - 1] if d else None)
    seco = (int(F25.sum()), int(EV25.sum()))
    assert seco == (176, 5499), seco
    print(f"2025 reproducido: {seco} en {time.time() - t:.0f} s", flush=True)
    U25 = Z.umbral(SR)

    # ---------- 2026, idéntico a s25a_medir.medir ----------
    est26 = np.load(Z.ESTAT26)
    btd26 = np.concatenate([np.load(os.path.join(B.TRAB, "dev_btd.npy")), np.load(Z._npy("n26_btd"))])
    acm26 = np.concatenate([np.load(os.path.join(B.TRAB, "dev_acm.npy")), np.load(os.path.join(B.TRAB, "nuevo_acm.npy"))])
    FD26, DIN26 = Z.nubes(acm26, est26)
    G26 = FD26 <= B.G_MAX
    C26 = Z.regional(btd26, DIN26, bctrl)
    bz = Z.base(Z25, USA25, IZ)
    ST, PT = Z.tabla_S(btd26[:, :, Z.ZONA], C26, bz, G26)
    ND = btd26.shape[0]
    F26 = np.zeros((ND, 144), bool)
    EV26 = np.zeros((ND, 144), bool)
    for d in range(ND):
        F26[d], EV26[d] = Z.disparos(ST, d, U25)
    # contra la tabla de S25a
    dif = 0
    with open(os.path.join(Z.TRAB, "tabla_2026.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d = (datetime.strptime(r["dia"], "%Y-%m-%d").date() - T26.date()).days
            s = M.slot(r["hora"])
            dif += (bool(int(r["F"])) != F26[d, s]) + (bool(int(r["evaluado"])) != EV26[d, s])
    assert dif == 0, dif
    print(f"2026 reproducido contra tabla_2026.csv: F {int(F26.sum())}, evaluados {int(EV26.sum())}", flush=True)
    E126 = H24.despejada("chillan", acm26)

    # ---------- BT11 de la zona (E5) ----------
    bt25 = np.load(r"D:\goes_notas\s23\s23a\r25_bt11.npy")
    bt26 = np.concatenate([np.load(os.path.join(B.TRAB, "dev_bt11.npy")), np.load(os.path.join(B.TRAB, "nuevo_bt11.npy"))])
    assert bt25.shape == btd25.shape and bt26.shape == btd26.shape, (bt25.shape, bt26.shape)
    bzT = Z.base(np.ascontiguousarray(bt25[:, :, Z.ZONA]), USA25, IZ)
    bctrlT = Z.base(bt25, USA25, Z.CTRL)
    C26T = Z.regional(bt26, DIN26, bctrlT)
    AT26 = bt26[:, :, Z.ZONA] - bzT[None] - C26T          # (ND, 144, 11)

    # ---------- noche, calor ----------
    noc25, cl25 = nocturnos(T25, Z.NR)
    noc26, cl26 = nocturnos(T26, ND)
    calor = json.load(open(os.path.join(TRAB, "calor_chillan_noches.json"), encoding="utf-8"))
    estado = {k: v["estado"] for k, v in calor.items()}

    # reproducción contra la validación (noches.csv)
    val = {}
    with open(os.path.join(OV, "vrp_nocturno", "resultados", "noches.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["sitio"] == "Nevados de Chillan":
                val[r["noche"]] = ("encendido" if r["enc"] == "True" else
                                   "bajo_limite" if r["con_dato"] == "True" else "sin_dato")
    comp = {k: (val[k], estado[k]) for k in sorted(set(val) & set(estado))}
    distintas = {k: v for k, v in comp.items() if v[0] != v[1]}

    # ---------- por noche ----------
    def por_noche(F, EV, noc, cl, nd, clear=None):
        out = {}
        for d in range(nd):
            for s in range(144):
                if not (noc[d, s] and EV[d, s]) or (clear is not None and not clear[d, s]):
                    continue
                k = cl[d, s]
                o = out.setdefault(k, [0, 0])
                o[0] += int(F[d, s])
                o[1] += 1
        return out

    pn26 = por_noche(F26, EV26, noc26, cl26, ND)
    pn25 = por_noche(F25, EV25, noc25, cl25, Z.NR)
    pn26c = por_noche(F26, EV26, noc26, cl26, ND, E126)
    pn25c = por_noche(F25, EV25, noc25, cl25, Z.NR, E125)

    def suma(pn, filtro):
        a = sum(v[0] for k, v in pn.items() if filtro(k))
        n = sum(v[1] for k, v in pn.items() if filtro(k))
        return a, n

    def tasas(pn, est_):
        return [v[0] / v[1] for k, v in pn.items() if v[1] >= MIN_EV_NOCHE and estado.get(k) == est_]

    # E1
    enc, baj = tasas(pn26, "encendido"), tasas(pn26, "bajo_limite")
    e1 = {"noches_encendidas": len(enc), "noches_bajo_limite": len(baj),
          "mediana_tasa_encendidas": float(np.median(enc)) if enc else None,
          "mediana_tasa_bajo_limite": float(np.median(baj)) if baj else None,
          "p_mannwhitney_encendidas_mayor": (float(stats.mannwhitneyu(enc, baj, alternative="greater").pvalue)
                                             if enc and baj else None)}
    ae, ne = suma(pn26, lambda k: estado.get(k) == "encendido")
    ab, nb = suma(pn26, lambda k: estado.get(k) == "bajo_limite")
    e1["cuadros_encendidas"] = [ae, ne]
    e1["cuadros_bajo_limite"] = [ab, nb]
    e1["p_fisher_cuadros_informativo"] = fisher_mayor(ae, ne, ab, nb) if ne and nb else None

    # E2: cuadros :00/:30 visibles, por noche
    idx26 = {}
    for d in range(ND):
        for s in range(144):
            idx26[tiempo(T26, d, s).strftime("%Y-%m-%dT%H:%MZ")] = (d, s)
    tablas, n_cal, n_frio, det_e2 = [], 0, 0, []
    for k, v in calor.items():
        ref = v.get("referencia_k")
        ref = None if ref in (None, "None") else float(ref)
        if ref is None:
            continue
        a = b = c = dd = 0
        for iso, (vrp, b14) in v["cuadros"].items():
            if iso not in idx26 or vrp is None or b14 is None or not np.isfinite(vrp) or not np.isfinite(b14):
                continue
            d, s = idx26[iso]
            if not (EV26[d, s] and noc26[d, s]) or b14 < ref - V.VARA_VISIBLE_K:
                continue
            f = bool(F26[d, s])
            if vrp >= V.UMBRAL_MW:
                a += f
                b += not f
            else:
                c += f
                dd += not f
        if (a + b) and (c + dd):
            tablas.append((a, b, c, dd))
            det_e2.append({"noche": k, "caliente": [a, a + b], "frio": [c, c + dd]})
        n_cal += a + b
        n_frio += c + dd
    orc, pc = cmh(tablas)
    sa = [sum(x[i] for x in tablas) for i in range(4)]
    e2 = {"noches_con_ambos": len(tablas), "cuadros_calientes_visibles": n_cal, "cuadros_frios_visibles": n_frio,
          "en_estratos": {"caliente_F": sa[0], "caliente": sa[0] + sa[1], "frio_F": sa[2], "frio": sa[2] + sa[3]},
          "OR_mantel_haenszel": orc, "p_cmh_bilateral": pc, "por_noche": det_e2}

    # E3
    a25, n25 = suma(pn25, lambda k: True)
    a25c, n25c = suma(pn25c, lambda k: True)
    a25m, n25m = suma(pn25, lambda k: k not in CAPA_BAJA_2025)
    a25cm, n25cm = suma(pn25c, lambda k: k not in CAPA_BAJA_2025)
    pre = lambda k: k <= "2026-10-11"  # noqa: E731
    grupos26 = {
        "bajo_limite": lambda k: estado.get(k) == "bajo_limite",
        "epoca_21-09_a_11-10": pre,
        "epoca_21-09_a_11-10_sin_encendidas": lambda k: pre(k) and estado.get(k) != "encendido",
        "encendido": lambda k: estado.get(k) == "encendido",
        "sin_dato": lambda k: estado.get(k) == "sin_dato",
        "desde_24-10": lambda k: k >= "2026-10-24",
        "todas": lambda k: True}
    e3 = {"2025": {"todas": [a25, n25], "despejadas_E1": [a25c, n25c],
                   "sin_capa_baja": [a25m, n25m], "despejadas_E1_sin_capa_baja": [a25cm, n25cm]}}
    for g, fil in grupos26.items():
        a, n = suma(pn26, fil)
        ac, nc = suma(pn26c, fil)
        e3[g] = {"cuadros": [a, n], "tasa": a / n if n else None,
                 "p_vs_2025": fisher_mayor(a, n, a25, n25) if n else None,
                 "p_vs_2025_sin_capa_baja": fisher_mayor(a, n, a25m, n25m) if n else None,
                 "despejadas_E1": [ac, nc], "tasa_E1": ac / nc if nc else None,
                 "p_E1_vs_2025_E1": fisher_mayor(ac, nc, a25c, n25c) if nc else None,
                 "p_E1_vs_2025_E1_sin_capa_baja": fisher_mayor(ac, nc, a25cm, n25cm) if nc else None,
                 "noches": sum(1 for k in pn26 if fil(k))}
    e3["2025"]["tasa"] = a25 / n25

    # E5
    def anom(sel):
        v = []
        for d, s in zip(*np.nonzero(sel)):
            for j in PT[d, s]:
                if j >= 0 and np.isfinite(AT26[d, s, j]):
                    v.append(float(AT26[d, s, j]))
        v = np.array(v)
        return {"n_valores": int(v.size), "mediana_K": float(np.median(v)) if v.size else None,
                "p10_K": float(np.percentile(v, 10)) if v.size else None,
                "p90_K": float(np.percentile(v, 90)) if v.size else None,
                "frac_mayor_3K": float((v >= ANOM_T).mean()) if v.size else None}

    nocF = noc26 & F26
    nocNoF = noc26 & EV26 & ~F26
    enc_m = np.vectorize(lambda k: estado.get(k) == "encendido")(cl26)
    e5 = {"F_noche": anom(nocF), "F_noche_cuadros": int(nocF.sum()),
          "noche_evaluados_sin_F": anom(nocNoF),
          "F_noche_noches_encendidas": anom(nocF & enc_m), "F_noche_otras": anom(nocF & ~enc_m),
          "F_dia_informativo": anom(~noc26 & F26)}
    # zona entera (los 11 píxeles) de noche con F: ¿está la cumbre más caliente que en 2025?
    z = AT26[nocF]
    e5["zona_entera_F_noche_mediana_K"] = float(np.nanmedian(z))
    e5["zona_entera_F_noche_max_por_cuadro_mediana_K"] = float(np.nanmedian(np.nanmax(z, 1)))

    # informativo: píxeles
    def pix(sel):
        c = Counter()
        for d, s in zip(*np.nonzero(sel)):
            for j in PT[d, s]:
                if j >= 0:
                    p = int(Z.ZONA[j])
                    c[f"({p // M.NX},{p % M.NX}) {C29.DIST.ravel()[p]:.1f} km"] += 1
        return dict(c.most_common())

    la, lo = V.cumbre_aparente(-36.863, -71.377, 3212.0)
    dz = C29.hav(C29.LAT.ravel()[Z.ZONA], C29.LON.ravel()[Z.ZONA], la, lo) if hasattr(C29, "LAT") else None
    info = {"pixeles_F_noche_encendidas": pix(nocF & enc_m), "pixeles_F_noche_otras": pix(nocF & ~enc_m),
            "cumbre_aparente": [float(la), float(lo)],
            "distancia_cumbre_aparente_km": ({f"({int(p) // M.NX},{int(p) % M.NX})": round(float(x), 2)
                                              for p, x in zip(Z.ZONA, dz)} if dz is not None else None)}

    # veredicto
    n_baj6 = len(baj)
    _, n_pre = suma(pn26, pre)
    p_sin = [e3["bajo_limite"]["p_vs_2025"], e3["epoca_21-09_a_11-10"]["p_vs_2025"]]
    exceso_sin_calor = any(p is not None and p <= 0.01 for p in p_sin)
    med5 = e5["F_noche"]["mediana_K"]
    p1 = e1["p_mannwhitney_encendidas_mayor"]
    if (n_baj6 < 5 and n_pre < 100) or e5["F_noche_cuadros"] < 20:
        ver = "NO DECIDIBLE"
    elif p1 is not None and p1 <= 0.01 and (e3["bajo_limite"]["p_vs_2025"] or 1) > 0.05 and med5 >= ANOM_T:
        ver = "EL CALOR EXPLICA"
    elif exceso_sin_calor and med5 < ANOM_T:
        ver = "EL CALOR NO EXPLICA"
        if (p1 is not None and p1 <= 0.01) or (pc is not None and pc <= 0.01):
            ver += " (asociados, no causa)"
    else:
        ver = "MIXTO"
    out = {"veredicto": ver, "criterio": "criterio_2026-11-25.md (2643ab0)",
           "reproduccion": {"seco_2025": seco, "tabla_2026_diferencias": dif,
                            "calor_vs_validacion_noches_comparadas": len(comp), "calor_vs_validacion_distintas": distintas},
           "E1": e1, "E2": e2, "E3": e3, "E5": e5, "informativo": info,
           "noches_bajo_limite_con_6": n_baj6, "cuadros_nocturnos_epoca_previa": n_pre}
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "s26b_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    with open(os.path.join(TRAB, "noches_2026.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["noche", "estado_calor", "vrp_max_mw", "n_visibles", "disparos", "evaluados", "disparos_E1", "evaluados_E1"])
        for k in sorted(pn26):
            c = calor.get(k, {})
            w.writerow([k, estado.get(k), c.get("vrp_max_mw"), c.get("n_visibles"), *pn26[k], *pn26c.get(k, [0, 0])])
    with open(os.path.join(TRAB, "noches_2025.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["noche", "disparos", "evaluados", "disparos_E1", "evaluados_E1"])
        for k in sorted(pn25):
            w.writerow([k, *pn25[k], *pn25c.get(k, [0, 0])])
    print(json.dumps({k: v for k, v in out.items() if k not in ("E2",)}, ensure_ascii=False, indent=1, default=str))
    print("E2:", json.dumps({k: v for k, v in e2.items() if k != "por_noche"}, ensure_ascii=False))
    print(f"total {time.time() - t:.0f} s")


if __name__ == "__main__":
    main()
