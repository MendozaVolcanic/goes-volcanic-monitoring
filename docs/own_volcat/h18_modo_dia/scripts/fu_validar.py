r"""H18 etapa 1, VALIDACIÓN (decide): ¿nuestra lectura de las tablas de DÍA reproduce `ash_probability` de VOLCAT?

Caso de Fuego (GOES-16, 03-06-2018), nivel A (entradas de VOLCAT). Criterio:
criterio_etapa1_validacion_dia_2026-11-22.md (f966a08) y su adenda (b7f8f7a). Variante elegida en los 13 primeros
cuadros con día, regla medida en los 13 siguientes, sobre píxeles de día de tierra. Placebo: NRAT y ρ(0,65)
permutados entre píxeles de día del mismo cuadro (semilla 20261122).

Entrada: npz de fu_extraer.py en D:\goes_notas\s16\modo_dia\npz (fuera del repo). Salida: resultados/.
"""
import glob
import itertools
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import dia_motor as M  # noqa: E402

NPZ = r"D:\goes_notas\s16\modo_dia\npz"
RES = os.path.join(os.path.dirname(AQUI), "resultados")
D, L1, RT, L2 = "geocatDIAGS1__", "geocatL1__", "geocatRTM__", "geocatL2__"


def cargar(horas, placebo=False):
    rng = np.random.default_rng(20261122)
    E, AG, V, VIR, SZ, VZ, RA, Q = [], [], [], [], [], [], [], []
    for h in horas:
        d = np.load(os.path.join(NPZ, f"fu_{h}.npz"))
        g = lambda k: d[k].astype(float).ravel()  # noqa: E731
        sz = g(L1 + "pixel_solar_zenith_angle")
        v = g(L2 + "ash_probability")
        sel = (sz < 85) & np.isfinite(v)
        r2, r7 = g(L1 + "channel_2_reflectance"), g(L1 + "channel_7_reflectance")
        with np.errstate(all="ignore"):
            nrat = r7 / r2
        e = {"eps": g(D + "cloud_emissivity_ch14_tot"), "b_tot": g(D + "cloud_beta_1112_tot"),
             "b_op": g(D + "cloud_beta_1112_opaque"), "b_low": g(D + "cloud_beta_1112_tot_multi_low"),
             "b_mid": g(D + "cloud_beta_1112_tot_multi_mid"), "b73": g(D + "cloud_beta_7311_tot"),
             "b85": g(D + "cloud_beta_8511_tot"), "b85op": g(D + "cloud_beta_8511_opaque"),
             "btd": g(L1 + "channel_14_brightness_temperature") - g(L1 + "channel_15_brightness_temperature"),
             "btclr": g(RT + "channel_14_brightness_temperature_clear"),
             "nrat": nrat, "nrat_lrc": g(D + "ref_rat_nir_lrc"), "ref2": r2}
        e = {k: a[sel] for k, a in e.items()}
        if placebo:
            for k in ("nrat", "nrat_lrc", "ref2"):
                e[k] = rng.permutation(e[k])
        E.append(e)
        AG.append(g(L1 + "pixel_surface_type")[sel] == 0)
        V.append(v[sel]); VIR.append(g(L2 + "ash_probability_IR")[sel])
        SZ.append(sz[sel]); VZ.append(g(L1 + "pixel_satellite_zenith_angle")[sel])
        RA.append(g(L1 + "pixel_relative_azimuth_angle")[sel]); Q.append(np.full(sel.sum(), int(h)))
    cat = lambda X: np.concatenate(X)  # noqa: E731
    ent = {k: cat([e[k] for e in E]) for k in E[0]}
    return ent, cat(AG), cat(V), cat(VIR), cat(SZ), cat(VZ), cat(RA), cat(Q)


def kappa(a, b):
    n = len(a)
    if n == 0:
        return float("nan")
    po = np.mean(a == b)
    pe = np.mean(a) * np.mean(b) + np.mean(~a) * np.mean(~b)
    return float((po - pe) / (1 - pe)) if pe < 1 else float("nan")


def metricas(p, v):
    ok = np.isfinite(p) & np.isfinite(v)
    p, v = p[ok], v[ok]
    if not len(p):
        return {"n": 0}
    a, b = p >= 0.5, v >= 0.5
    m = {"n": int(len(p)), "n_volcat_ge05": int(b.sum()), "n_nuestra_ge05": int(a.sum()),
         "frac_dentro_005": float(np.mean(np.abs(p - v) <= 0.05)), "kappa": kappa(a, b),
         "recuperados": float(np.mean(a[b])) if b.any() else float("nan"),
         "dif_abs_mediana": float(np.median(np.abs(p - v))), "dif_abs_p95": float(np.percentile(np.abs(p - v), 95))}
    m["cumple"] = bool(m["frac_dentro_005"] >= 0.90 and m["kappa"] >= 0.90 and m["recuperados"] >= 0.90)
    return m


def piezas_conv(ent, ag, sz, vz, ra):
    return {c: M.piezas(ent, ag, M.scat_idx(M.angulo_dispersion(sz, vz, ra, c))) for c in ("+", "-")}


VARIANTES = list(itertools.product(("+", "-"), ("n1", "n2", "n3"), (0, 1), (0, 1), (0, 1), (0, 1)))


def nombre(var):
    c, n, d, k, v, i = var
    return f"c{c} {n} d{d} k{k} v{v} i{i}"


def complejidad(var):
    c, n, d, k, v, i = var
    return (n == "n3") + d + k + v + i


def main():
    horas_todas = sorted(os.path.basename(f)[3:9] for f in glob.glob(os.path.join(NPZ, "fu_*.npz")))
    comp = json.load(open(os.path.join(RES, "fu_comprobaciones.json")))
    con_dia = [x["hora"] for x in comp["cuadros"] if x["n_dia"] > 0]
    assert len(con_dia) == 26 and set(con_dia) <= set(horas_todas)
    elige, valida = con_dia[:13], con_dia[13:]

    # Elección (primera mitad, todos los píxeles de día)
    ent, ag, v, vir, sz, vz, ra, q = cargar(elige)
    PC = piezas_conv(ent, ag, sz, vz, ra)
    filas = []
    for var in VARIANTES:
        p = M.prob(M.logit_variante(PC[var[0]], *var[1:]))
        m = metricas(p, v)
        filas.append({"variante": nombre(var), **m})
    filas.sort(key=lambda r: (-r["frac_dentro_005"], complejidad(VARIANTES[[nombre(x) for x in VARIANTES].index(r["variante"])])))
    elegida = VARIANTES[[nombre(x) for x in VARIANTES].index(filas[0]["variante"])]
    with open(os.path.join(RES, "fu_variantes_eleccion.csv"), "w", encoding="utf-8") as f:
        ks = list(filas[0].keys())
        f.write(",".join(ks) + "\n")
        for r in filas:
            f.write(",".join(str(r[k]) for k in ks) + "\n")
    # Referencia: la IR sola de VOLCAT y nuestras tablas IR solas en la primera mitad (no decide)
    ref_eleccion = {"P_IR_de_VOLCAT_vs_P": metricas(vir, v),
                    "nuestras_IR_solas_vs_P": metricas(M.prob(M.L0 + PC["+"]["ir"]), v),
                    "nuestras_IR_solas_vs_P_IR": metricas(M.prob(M.L0 + PC["+"]["ir"]), vir)}

    # Validación (segunda mitad)
    ent, ag, v, vir, sz, vz, ra, q = cargar(valida)
    PC = piezas_conv(ent, ag, sz, vz, ra)
    L = M.logit_variante(PC[elegida[0]], *elegida[1:])
    p = M.prob(L)
    tierra = ~ag
    eps = ent["eps"]
    out = {"elegida": nombre(elegida), "cuadros_eleccion": elige, "cuadros_validacion": valida,
           "referencia_primera_mitad": ref_eleccion}
    out["tierra_dia"] = metricas(p[tierra], v[tierra])
    out["agua_dia_informativo"] = metricas(p[ag], v[ag])
    t4 = tierra & np.isfinite(eps) & (eps < 0.5)
    m4 = metricas(p[t4], v[t4])
    m4["sin_dato"] = m4.get("n_volcat_ge05", 0) < 30
    m4["cumple_1_y_3"] = bool(not m4["sin_dato"] and m4["frac_dentro_005"] >= 0.90 and m4["recuperados"] >= 0.90)
    out["tramo_eps_lt_05_tierra"] = m4
    out["por_tramo_eps_tierra"] = {}
    for a, b in ((0, 0.1), (0.1, 0.2), (0.2, 0.5), (0.5, 1.01)):
        s = tierra & np.isfinite(eps) & (eps >= a) & (eps < b)
        out["por_tramo_eps_tierra"][f"{a}-{b}"] = metricas(p[s], v[s])
    out["por_cuadro_tierra"] = {}
    for h in valida:
        s = tierra & (q == int(h))
        out["por_cuadro_tierra"][h] = metricas(p[s], v[s])
    # Control negativo: VOLCAT < 0,01, cuántos damos >= 0,5
    neg = tierra & (v < 0.01)
    out["control_negativo"] = {"n": int(neg.sum()), "frac_nuestra_ge05": float(np.mean(p[neg] >= 0.5)) if neg.any() else None}
    # Control positivo = recuperados en tierra_dia (arriba)
    # Placebo
    entp, agp, vp, _, szp, vzp, rap, _ = cargar(valida, placebo=True)
    PCp = piezas_conv(entp, agp, szp, vzp, rap)
    pp = M.prob(M.logit_variante(PCp[elegida[0]], *elegida[1:]))
    mp = metricas(pp[~agp], vp[~agp])
    t = out["tierra_dia"]
    out["placebo_tierra"] = mp
    out["placebo_empeora"] = bool((t["frac_dentro_005"] - mp["frac_dentro_005"] >= 0.05)
                                  or (t["kappa"] - mp["kappa"] >= 0.10))
    # Veredicto
    c13 = t["cumple"]
    if c13 and out["placebo_empeora"] and m4["cumple_1_y_3"]:
        ver = "VALIDA"
    elif c13 and out["placebo_empeora"]:
        ver = "VALIDADA SOLO EN NUBE ESPESA"
    else:
        ver = "NO VALIDA"
    out["veredicto"] = ver
    json.dump(out, open(os.path.join(RES, "fu_validacion.json"), "w"), indent=1)
    print("elegida:", out["elegida"])
    print("primeras 8 variantes:")
    for r in filas[:8]:
        print(f'  {r["variante"]}: dentro {r["frac_dentro_005"]:.3f} kappa {r["kappa"]:.3f} rec {r["recuperados"]:.3f}')
    for k in ("tierra_dia", "agua_dia_informativo", "tramo_eps_lt_05_tierra", "placebo_tierra", "control_negativo"):
        print(k, json.dumps(out[k]))
    print("tramos:", json.dumps(out["por_tramo_eps_tierra"]))
    print("referencia 1a mitad:", json.dumps(ref_eleccion))
    print("placebo empeora:", out["placebo_empeora"])
    print("VEREDICTO:", ver)


if __name__ == "__main__":
    main()
