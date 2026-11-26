r"""S31c: el anillo del detector S26a partido en dos coronas (4 a 15 y 15 a 40 km). Implementa
criterio_2026-11-26.md (commit d3c9461, empujado antes de calcular un disparo por corona; anexo §8 sobre el R exacto).

Por qué: S30b vio que el anillo marca el rumbo de la pluma de VOLCAT, y post hoc que sus píxeles caen a 26 a 32 km
mientras la huella anclada de VOLCAT llega a 9 a 15 km. Aquí se mira, sin tocar el detector, a qué distancia caen los
8 píxeles de la cola de la tajada que dispara (los que forman su estadístico) y si caen en el tramo que VOLCAT dibuja
más que un píxel cualquiera de la misma tajada (nulo G, permutación por día dentro de la tajada), además de los nulos
R (huella girada) y D (huella de otro día) de S30b, con el día como unidad.

Lee la tabla de S26a (D:\goes_notas\s26\s26a\tabla_2026.csv, hasta el 24-11) y los PNG de VOLCAT de D: (licencia SSEC:
nada de eso va al repo). Escribe resultados/s31c_resultado.json y resultados/s31c_por_cuadro.csv (sólo cifras) y en
D:\goes_notas\s31\s31c\ las huellas en la grilla ABI.

Uso: python -I -B s31c_medir.py
"""
import csv
import json
import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "s30b_huella_volcat", "scripts"))
import s30b_medir as S30  # noqa: E402
import s30b_posthoc2 as S30P  # noqa: E402

M, C29 = S30.M, S30.C29
TRAB = r"D:\goes_notas\s31\s31c"

# ---------- parámetros del criterio ----------
CORTE_KM = 15.0                 # §1: cercana 4 <= DIST < 15, lejana 15 <= DIST <= 40
TOL_RUMBO = 30.0                # §2
B_MC, SEMILLA = 9999, 0         # §3
ENUM_MAX, MIN_CONF = 25000, 1000   # anexo §8: exacto hasta 12^4
P_MAX = 0.01                    # alfa
MIN_P, MIN_DIAS, MIN_FRAC = 10, 3, 0.25
GEOM_CERCA = 107 / 837          # §0, sólo geometría
REPRO_S30B = {"a": 12, "a_px": 7, "a_rumbo": 12, "n": 23, "pR_a": 0.0041}   # anexo §8: exacto
PR_S30B_MC = 0.0037             # S30b, Monte Carlo B=9999

DISTF, SECF, AMASK = S30.DISTF, S30.SECF, S30.AMASK
CERCA = AMASK & (DISTF < CORTE_KM)
LEJOS = AMASK & (DISTF >= CORTE_KM)
MIEMBROS = [M.AP[M.SEC == k] for k in range(12)]
MEDIDAS = ("px_cerca", "px_lejos", "rumbo_cerca", "rumbo_lejos")
NULOS = {"px_cerca": "GRD", "px_lejos": "GRD", "rumbo_cerca": "RD", "rumbo_lejos": "RD"}


# ---------- disparos y coincidencias ----------
def disparo_px(filas, s):
    """Píxeles del disparo del anillo en s-1..s+1 (unión de cola_a) con la tajada de cada uno."""
    pix, ks = [], []
    for t in (s - 1, s, s + 1):
        r = filas.get(t)
        if r is None or r["F_a"] != "1":
            continue
        k = int(r["k_a"])
        for x in r["cola_a"].split(";"):
            if x:
                p = int(x)
                assert AMASK[p] and SECF[p] == k, "cola_a fuera del anillo o de su tajada"
                pix.append(p)
                ks.append(k)
    if not pix:
        return None
    u = {}
    for p, k in zip(pix, ks):
        u[p] = k
    return np.array(list(u), int), np.array(list(u.values()), int)


def angdif_arr(a, b):
    x = np.abs(a - b) % 360
    return np.minimum(x, 360 - x)


def coincide(hu, dp, j=0, mapa=None):
    """dict medida -> bool, para la huella hu (girada j·30°) y los píxeles del disparo dp (mapeados por mapa)."""
    pix, ks = dp
    if mapa is not None:
        pix = np.array([mapa.get(p, p) for p in pix], int)
    if hu.rumbo is None:
        ok_r = np.zeros(len(pix), bool)
    else:
        ok_r = angdif_arr(30 * ks + 15, (hu.rumbo + 30 * j) % 360) <= TOL_RUMBO
    dentro = hu.dil[j][pix]
    c, l = CERCA[pix], LEJOS[pix]
    return {"px_cerca": bool((c & dentro & ok_r).any()), "px_lejos": bool((l & dentro & ok_r).any()),
            "rumbo_cerca": bool((c & ok_r).any()), "rumbo_lejos": bool((l & ok_r).any())}


def mapa_G(rng, pix_dia):
    """Una permutación por tajada para el día: cada píxel del disparo pasa a otro de su tajada (sin repetir)."""
    por_k = defaultdict(list)
    for p in sorted(pix_dia):
        por_k[int(SECF[p])].append(p)
    mapa = {}
    for k in sorted(por_k):
        orig = por_k[k]
        dest = rng.permutation(MIEMBROS[k])[:len(orig)]
        mapa.update(zip(orig, (int(x) for x in dest)))
    return mapa


# ---------- prueba con los tres nulos ----------
def prueba(items, donantes, rng):
    """items: lista de (dia, Huella, disparo). Devuelve por medida T, n, frac y los nulos que le tocan."""
    dias = sorted({d for d, _, _ in items})
    nd, n = len(dias), len(items)
    idx = {d: i for i, d in enumerate(dias)}
    obs = [coincide(hu, dp) for _, hu, dp in items]
    out = {"n": n, "dias": dias, "medidas": {}}
    if not n:
        return out
    res = {m: {"T": int(sum(o[m] for o in obs)), "frac": sum(o[m] for o in obs) / n} for m in MEDIDAS}
    # R: tabla día x giro
    tab = {m: np.zeros((nd, 12), int) for m in MEDIDAS}
    for d, hu, dp in items:
        for j in range(12):
            c = coincide(hu, dp, j)
            for m in MEDIDAS:
                tab[m][idx[d], j] += c[m]
    confR = 12 ** nd
    J = None if confR <= ENUM_MAX else rng.integers(0, 12, size=(B_MC, nd))
    for m in MEDIDAS:
        T = res[m]["T"]
        if J is None:
            tot = np.zeros(1, int)
            for i in range(nd):
                tot = (tot[:, None] + tab[m][i][None, :]).ravel()
            p, met = float((tot >= T).mean()), f"exacto ({confR} combinaciones)"
        else:
            tot = tab[m][np.arange(nd)[None, :], J].sum(1)
            p, met = float((1 + (tot >= T).sum()) / (B_MC + 1)), f"Monte Carlo B={B_MC}"
        res[m]["R"] = {"p": p, "frac_esperada": float(tot.mean()) / n, "configuraciones": confR,
                       "decide": confR >= MIN_CONF, "metodo": met}
    # G: permutación por día dentro de la tajada (sólo medidas px)
    pix_dia = defaultdict(set)
    for d, _, dp in items:
        pix_dia[d].update(int(p) for p in dp[0])
    totG = {m: np.zeros(B_MC, int) for m in MEDIDAS if "G" in NULOS[m]}
    for b in range(B_MC):
        mapas = {d: mapa_G(rng, pix_dia[d]) for d in dias}
        for d, hu, dp in items:
            c = coincide(hu, dp, 0, mapas[d])
            for m in totG:
                totG[m][b] += c[m]
    for m, tot in totG.items():
        res[m]["G"] = {"p": float((1 + (tot >= res[m]["T"]).sum()) / (B_MC + 1)),
                       "frac_esperada": float(tot.mean()) / n, "decide": nd >= MIN_DIAS,
                       "metodo": f"Monte Carlo B={B_MC}"}
    # D: huella de otro día
    cand = {d: [x for x in sorted(donantes) if x != d] for d in dias}
    confD = int(np.prod([len(cand[d]) for d in dias], dtype=float))
    totD = {m: np.zeros(B_MC, int) for m in MEDIDAS}
    for b in range(B_MC):
        don = {d: cand[d][rng.integers(len(cand[d]))] for d in dias}
        for d, hu, dp in items:
            lst = donantes[don[d]]
            c = coincide(lst[rng.integers(len(lst))], dp)
            for m in MEDIDAS:
                totD[m][b] += c[m]
    for m in MEDIDAS:
        res[m]["D"] = {"p": float((1 + (totD[m] >= res[m]["T"]).sum()) / (B_MC + 1)),
                       "frac_esperada": float(totD[m].mean()) / n, "configuraciones_dia": confD,
                       "decide": confD >= MIN_CONF, "metodo": f"Monte Carlo B={B_MC}"}
    out["medidas"] = res
    return out


def veredicto(r, orc, orc_tajada_pR):
    """Criterio §5."""
    if r["n"] < MIN_P or len(r["dias"]) < MIN_DIAS:
        return "NO DECIDIBLE (pocos cuadros o días)"
    if orc["medidas"]["px_cerca"]["G"]["p"] > P_MAX:
        return "SIN PODER (el oráculo no pasa el nulo G en la corona cercana)"
    pc, rl = r["medidas"]["px_cerca"], r["medidas"]["rumbo_lejos"]
    if pc["G"]["p"] <= P_MAX and pc["R"]["p"] <= P_MAX:
        v = "VE EL TRAMO DE VOLCAT" if pc["frac"] >= MIN_FRAC else "VE EL TRAMO DE VOLCAT, PARCIAL"
        if pc["D"]["p"] <= P_MAX and orc["medidas"]["px_cerca"]["D"]["p"] <= P_MAX:
            return v + ", y sigue a esta pluma"
        return v + ", sin separar esta pluma de la de otro día"
    if pc["G"]["p"] > P_MAX and rl["R"]["p"] <= P_MAX and orc_tajada_pR <= P_MAX:
        return "SÓLO LEJOS"
    return "NO DECIDIBLE"


def oraculo(hn):
    """Píxeles del oráculo: los de la huella vecina en su tajada con más píxeles en el anillo (criterio §4)."""
    ring = hn.h[AMASK[hn.h]]
    if not len(ring):
        return None
    k = int(np.argmax(np.bincount(SECF[ring], minlength=12)))
    pix = ring[SECF[ring] == k]
    return pix.astype(int), np.full(len(pix), k, int)


# ---------- comprobación de código ----------
def comprobar_s30b(items_a):
    """Con la huella anclada, las funciones de S30b sobre los mismos P tienen que dar 12, 7, 12 de 23 y p_R 0,0037."""
    n = len(items_a)
    tot = {"a": 0, "a_px": 0, "a_rumbo": 0}
    dias = sorted({d for d, _, _, _ in items_a})
    tab = np.zeros((len(dias), 12), int)
    for d, hu, di, _ in items_a:
        c = S30.coincide(hu, di)
        for k in tot:
            tot[k] += c[k]
        for j in range(12):
            tab[dias.index(d), j] += S30.coincide(hu, di, j)["a"]
    t = np.zeros(1, int)
    for i in range(len(dias)):
        t = (t[:, None] + tab[i][None, :]).ravel()
    pR = float((t >= tot["a"]).mean())
    got = {**tot, "n": n, "pR_a": round(pR, 4)}
    sd = (pR * (1 - pR) / B_MC) ** 0.5
    ok = got == REPRO_S30B and abs(PR_S30B_MC - pR) < 3 * sd
    print("comprobación S30b:", got, "OK" if ok else "NO REPRODUCE", flush=True)
    if not ok:
        sys.exit("no reproduce S30b: se para")
    return got


# ---------- medir ----------
def medir():
    t0 = time.time()
    os.makedirs(RES, exist_ok=True)
    os.makedirs(TRAB, exist_ok=True)
    T = S30.leer_tabla()
    repro26 = S30.comprobar(T)
    P = [(d, s) for d in sorted(T) for s in sorted(T[d]) if T[d][s]["clase"] == "P"]
    cache = {}

    def H(tipo, d, s):
        key = (tipo, d, s)
        if key not in cache:
            f = S30.huella if tipo == "anclada" else S30P.huella_40
            st, h = f(d, s) if 0 <= s < 144 else ("fuera", None)
            cache[key] = S30.Huella(h) if st == "ok" else None
        return cache[key]

    out = {"criterio": "criterio_2026-11-26.md (d3c9461 + anexo §8)", "comprobacion_S26a": repro26,
           "geometria": {"px_anillo": int(AMASK.sum()), "px_cerca": int(CERCA.sum()), "frac_cerca": GEOM_CERCA},
           "huellas": {}}
    filas_csv = {}
    rng = np.random.default_rng(SEMILLA)
    sel = {"todo": lambda s: True, "dia": lambda s: s >= 72, "noche": lambda s: s < 72}
    orc_tajada = {}
    for tipo in ("anclada", "ceniza_40km"):
        donantes, items, orcs, items_s30 = defaultdict(list), [], [], []
        for d, s in P:
            hu = H(tipo, d, s)
            if hu is None:
                continue
            donantes[d].append(hu)
            dp = disparo_px(T[d], s)
            if dp is not None:
                items.append((d, hu, dp, s))
                if tipo == "anclada":
                    items_s30.append((d, hu, S30.disparos(T[d], s), s))
            hn = H(tipo, d, s - 1) or H(tipo, d, s + 1)
            if hn is not None:
                od = oraculo(hn)
                if od is not None:
                    orcs.append((d, hu, od, s))
                if tipo == "anclada":
                    orc_tajada.setdefault("items", []).append((d, hu, S30.oraculo_disparos(hn), s))
        print(tipo, "P con huella:", sum(len(v) for v in donantes.values()), "evaluados:", len(items),
              "oráculo:", len(orcs), flush=True)
        if tipo == "anclada":
            out["comprobacion_S30b"] = comprobar_s30b(items_s30)
            np.savez_compressed(os.path.join(TRAB, "huellas_anclada.npz"),
                                **{f"{d}_{s:03d}": H(tipo, d, s).h for d, s in P if H(tipo, d, s) is not None})
        bloque = {}
        for per, f in sel.items():
            its = [(d, hu, dp) for d, hu, dp, s in items if f(s)]
            ois = [(d, hu, dp) for d, hu, dp, s in orcs if f(s)]
            r = prueba(its, donantes, rng)
            o = prueba(ois, donantes, rng)
            if tipo == "anclada" and per not in orc_tajada:
                ot = S30.prueba([(d, hu, di) for d, hu, di, s in orc_tajada["items"] if f(s)], "a", donantes, rng,
                                usar_R=True, usar_D=False)
                orc_tajada[per] = ot
            otp = orc_tajada[per]["R"]["p"] if orc_tajada[per].get("R") else 1.0
            r["veredicto"] = veredicto(r, o, otp)
            if tipo == "ceniza_40km" and r.get("medidas"):
                pl = r["medidas"]["px_lejos"]
                r["px_lejos_en_ceniza_desprendida"] = bool(pl["G"]["p"] <= P_MAX and pl["R"]["p"] <= P_MAX)
            bloque[per] = {"detector": r, "oraculo": o, "oraculo_tajada_S30b_pR": otp}
            fmt = {m: (v["T"], v.get("G", {}).get("p"), v["R"]["p"], v["D"]["p"]) for m, v in r["medidas"].items()}
            fmo = {m: (v["T"], v.get("G", {}).get("p"), v["R"]["p"], v["D"]["p"]) for m, v in o["medidas"].items()}
            print(f"{tipo} {per}: n {r['n']} días {len(r['dias'])} | {fmt} | {r['veredicto']}", flush=True)
            print(f"   oráculo n {o['n']}: {fmo} | oráculo tajada p_R {otp}  ({time.time() - t0:.0f} s)", flush=True)
        out["huellas"][tipo] = bloque
        for d, hu, dp, s in items:
            c = coincide(hu, dp)
            fila = filas_csv.setdefault((d, s), {
                "dia": d, "hora": M.hhmm(s), "periodo": "noche" if s < 72 else "dia",
                "px_disparo": len(dp[0]), "px_cerca": int(CERCA[dp[0]].sum()), "px_lejos": int(LEJOS[dp[0]].sum()),
                "km_disparo_mediana": round(float(np.median(DISTF[dp[0]])), 1),
                "tajadas_disparo": " ".join(str(k) for k in sorted(set(dp[1].tolist())))})
            ring = hu.h[AMASK[hu.h]]
            fila[f"huella_{tipo}_km_max_anillo"] = round(float(DISTF[ring].max()), 1) if len(ring) else ""
            fila[f"huella_{tipo}_rumbo"] = "" if hu.rumbo is None else round(hu.rumbo, 1)
            for m in MEDIDAS:
                fila[f"{m}_{tipo}"] = int(c[m])
    out["oraculo_tajada_S30b"] = {k: v for k, v in orc_tajada.items() if k != "items"}

    # descriptivo: fracción de los píxeles del disparo en la corona cercana
    desc = {"geometria": GEOM_CERCA}
    ev = [r for r in filas_csv.values()]
    desc["P_evaluados"] = {"px": sum(r["px_disparo"] for r in ev), "cerca": sum(r["px_cerca"] for r in ev)}
    porclase = defaultdict(lambda: [0, 0, 0])
    for d in sorted(T):
        for s, r in T[d].items():
            if r["F_a"] != "1":
                continue
            pix = np.array([int(x) for x in r["cola_a"].split(";") if x], int)
            c = "P" if r["clase"] == "P" else ("N" if r["clase"] == "N" else "sin_clase")
            porclase[c][0] += 1
            porclase[c][1] += len(pix)
            porclase[c][2] += int(CERCA[pix].sum())
    desc["disparos_2026_por_clase"] = {c: {"cuadros": v[0], "px": v[1], "cerca": v[2],
                                           "frac_cerca": v[2] / v[1] if v[1] else None}
                                       for c, v in sorted(porclase.items())}
    for k in ("P_evaluados",):
        desc[k]["frac_cerca"] = desc[k]["cerca"] / desc[k]["px"]
    out["descriptivo"] = desc
    print("descriptivo:", json.dumps(desc, ensure_ascii=False), flush=True)

    json.dump(out, open(os.path.join(RES, "s31c_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))
    filas = [filas_csv[k] for k in sorted(filas_csv)]
    campos = []
    for f in filas:
        campos += [c for c in f if c not in campos]
    with open(os.path.join(RES, "s31c_por_cuadro.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    print(f"listo en {time.time() - t0:.0f} s:", os.path.join(RES, "s31c_resultado.json"), flush=True)


def pruebas():
    """Prueba sintética, sin datos de VOLCAT ni disparos reales."""
    rng = np.random.default_rng(1)
    k = 4
    cerca_k = MIEMBROS[k][CERCA[MIEMBROS[k]]]
    lejos_k = MIEMBROS[k][LEJOS[MIEMBROS[k]]]
    hu = S30.Huella(cerca_k)                                  # huella = corona cercana de la tajada 4
    assert hu.rumbo is not None and abs(hu.rumbo - 135) < 15
    dp_c = (cerca_k[:8], np.full(8, k))
    dp_l = (lejos_k[-8:], np.full(8, k))
    c = coincide(hu, dp_c)
    assert c["px_cerca"] and not c["px_lejos"] and c["rumbo_cerca"] and not c["rumbo_lejos"], c
    c = coincide(hu, dp_l)
    assert not c["px_cerca"] and c["rumbo_lejos"] and not c["rumbo_cerca"], c
    assert not coincide(hu, dp_c, 6)["px_cerca"] and not coincide(hu, dp_c, 6)["rumbo_cerca"]
    for _ in range(200):
        mp = mapa_G(rng, set(int(p) for p in np.r_[dp_c[0], dp_l[0], MIEMBROS[7][:5]]))
        assert len(set(mp.values())) == len(mp), "G no es inyectiva"
        assert all(SECF[a] == SECF[b] for a, b in mp.items()), "G cambia de tajada"
        for dp in (dp_c, dp_l):
            a, b = coincide(hu, dp), coincide(hu, dp, 0, mp)
            assert (a["rumbo_cerca"] or a["rumbo_lejos"]) == (b["rumbo_cerca"] or b["rumbo_lejos"])
    # G desordena la distancia: una cola de 8 cercanos casi nunca queda entera cerca
    fr = np.mean([CERCA[[mapa_G(rng, set(int(p) for p in dp_c[0]))[int(p)] for p in dp_c[0]]].mean()
                  for _ in range(500)])
    assert 0.05 < fr < 0.25, fr
    print("pruebas sintéticas OK; fracción cercana bajo G:", round(float(fr), 3))


if __name__ == "__main__":
    pruebas() if sys.argv[1:] == ["pruebas"] else medir()
