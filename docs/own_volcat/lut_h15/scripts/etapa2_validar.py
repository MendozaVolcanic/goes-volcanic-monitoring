r"""C3 (H15) etapa 2: ¿nuestra lectura de las tablas de VOLCAT reproduce su ash_probability_IR en Mauna Loa?

Criterio: docs/own_volcat/lut_h15/criterio_etapa2_validacion_2026-11-21.md (commit a0d29ea, antes de este script).
Lee los npz de ml_extraer.py (D:\goes_cache\lut_h15\ml) y la máscara de agua de VOLCAT (emisividad de superficie
de C14 constante en el mar, 'Imager_Sea_Surface_Emissivity_Source = CONST') de los npz de C2b. Escribe
resultados/etapa2_validacion.json y resultados/etapa2_variantes.csv.

Uso: python -I etapa2_validar.py
"""
import csv
import itertools
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lut_volcat as LV  # noqa: E402

ML = r"D:\goes_cache\lut_h15\ml"
C2B = r"D:\goes_cache\volcat_test_mauna_loa\npz"
RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
HORAS = ["091600", "092100", "092600", "093100", "093600", "094100", "094600", "095100", "095600", "100130"]
ELIGE, VALIDA = HORAS[:5], HORAS[5:]


def rad(d, bt, ch):
    k = ch - 1
    return LV.planck_rad(bt, d["fk1_planck"][k], d["fk2_planck"][k], d["bc1_planck"][k], d["bc2_planck"][k])


def cuadro(h, gfs):
    d = np.load(os.path.join(ML, f"ml_{h}.npz"))
    c = np.load(os.path.join(C2B, f"c2b_{h}.npz"))
    g = lambda k: d[k].astype(float).ravel()  # noqa: E731
    sfc = c["geocatRTM__channel_14_surface_emissivity"].astype(float).ravel()
    vals, cnt = np.unique(np.round(sfc[np.isfinite(sfc)], 4), return_counts=True)
    agua = np.isclose(sfc, vals[np.argmax(cnt)], atol=1e-4)
    bt = {ch: g(f"geocatL1__channel_{ch}_brightness_temperature") for ch in (7, 10, 14, 15)}
    clr = {ch: g(f"geocatRTM__channel_{ch}_brightness_temperature_clear") for ch in (7, 10, 14, 15)}
    D = "geocatDIAGS1__"
    A = {  # nivel A: entradas de VOLCAT
        "eps": g(D + "cloud_emissivity_ch14_tot"), "b_tot": g(D + "cloud_beta_1112_tot"),
        "b_op": g(D + "cloud_beta_1112_opaque"), "b_low": g(D + "cloud_beta_1112_tot_multi_low"),
        "b_mid": g(D + "cloud_beta_1112_tot_multi_mid"), "b73": g(D + "cloud_beta_7311_tot"),
        "b85": g(D + "cloud_beta_8511_tot"), "b85op": g(D + "cloud_beta_8511_opaque"),
        "btd": bt[14] - bt[15], "btclr": clr[14],
        "ems7": rad(d, bt[7], 7) / rad(d, clr[7], 7),
    }
    # nivel B: eps y beta total nuestros, con el cielo despejado de VOLCAT y nube negra en la tropopausa del GFS
    hh = int(h[:2]) + int(h[2:4]) / 60.0
    w = (hh - 6.0) / 6.0                          # gfs 06Z (22112718_F012) a 12Z (22112800_F012)
    iy = g("geocatRTM__nwp_y_index")
    ix = g("geocatRTM__nwp_x_index")
    ok = np.isfinite(iy) & np.isfinite(ix)
    tt = np.full(iy.shape, np.nan)
    yy, xx = iy[ok].astype(int), ix[ok].astype(int)
    tt[ok] = (1 - w) * gfs["gfs.22112718_F012.hdf"][yy, xx] + w * gfs["gfs.22112800_F012.hdf"][yy, xx]
    e = {ch: LV.emisividad(rad(d, bt[ch], ch), rad(d, clr[ch], ch), rad(d, tt, ch)) for ch in (10, 14, 15)}
    B = dict(A)
    B["eps"] = e[14]
    B["b_tot"] = LV.beta(e[15], e[14])
    B["b73"] = LV.beta(e[10], e[14])
    verdad = g("geocatL2__ash_probability_IR")
    return A, B, agua, verdad


def metricas(p, v):
    ok = np.isfinite(p) & np.isfinite(v)
    p, v = p[ok], v[ok]
    if not len(p):
        return {}
    a, b = p >= 0.5, v >= 0.5
    po = np.mean(a == b)
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    from scipy.stats import spearmanr
    return {
        "n": int(ok.sum()), "n_volcat_ge05": int(b.sum()), "n_nuestra_ge05": int(a.sum()),
        "frac_dif_le_005": float(np.mean(np.abs(p - v) <= 0.05)),
        "kappa_05": float(kappa),
        "frac_ge05_recuperada": float(a[b].mean()) if b.any() else float("nan"),
        "frac_lt05_recuperada": float((~a[~b]).mean()) if (~b).any() else float("nan"),
        "dif_abs_mediana": float(np.median(np.abs(p - v))), "dif_abs_p95": float(np.percentile(np.abs(p - v), 95)),
        "spearman": float(spearmanr(p, v).correlation),
    }


def cumple(m):
    return bool(m and m["frac_dif_le_005"] >= 0.90 and m["kappa_05"] >= 0.90 and m["frac_ge05_recuperada"] >= 0.90)


def main():
    T = LV.Tablas()
    gfs = dict(np.load(os.path.join(ML, "gfs_ttropo.npz")))
    datos = {h: cuadro(h, gfs) for h in HORAS}

    def pila(horas, nivel, var):
        P, V = [], []
        for h in horas:
            A, B, agua, v = datos[h]
            ent = A if nivel == "A" else B
            L, _ = LV.log_odds(T, var[0], ent, agua, modo=var[1], comb=var[2])
            P.append(LV.prob(L))
            V.append(v)
        return np.concatenate(P), np.concatenate(V)

    variantes = list(itertools.product(["S1", "S2", "S3"], ["a", "b", "c"], ["J", "C1", "C0"]))
    filas = []
    for var in variantes:
        m = metricas(*pila(ELIGE, "A", var))
        filas.append({"conjunto": var[0], "fuera_de_eje": var[1], "combinacion": var[2], **m})
        print(var, round(m["frac_dif_le_005"], 4), round(m["kappa_05"], 4), flush=True)
    mejor = max(filas, key=lambda f: f["frac_dif_le_005"])
    var = (mejor["conjunto"], mejor["fuera_de_eje"], mejor["combinacion"])
    out = {"variante_elegida": var, "eleccion_cuadros_1_5_nivelA": mejor}
    for nivel in ("A", "B"):
        m = metricas(*pila(VALIDA, nivel, var))
        out[f"validacion_cuadros_6_10_nivel{nivel}"] = m
        out[f"cumple_nivel{nivel}"] = cumple(m)
    # diagnóstico del nivel B: nuestro eps y beta contra los de VOLCAT
    dif = {}
    for k in ("eps", "b_tot", "b73"):
        a = np.concatenate([datos[h][0][k] for h in VALIDA])
        b = np.concatenate([datos[h][1][k] for h in VALIDA])
        ok = np.isfinite(a) & np.isfinite(b) & (np.abs(a) < 5) & (np.abs(b) < 5)
        dd = b[ok] - a[ok]
        dif[k] = {"n": int(ok.sum()), "mediana": float(np.median(dd)), "p05": float(np.percentile(dd, 5)),
                  "p95": float(np.percentile(dd, 95)), "frac_abs_le_001": float(np.mean(np.abs(dd) <= 0.01))}
    out["nivelB_menos_volcat_cuadros_6_10"] = dif
    out["fraccion_agua"] = float(np.mean(np.concatenate([datos[h][2] for h in HORAS])))
    out["etapa2_aprobada"] = out["cumple_nivelA"] and out["cumple_nivelB"]
    with open(os.path.join(RES, "etapa2_variantes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    with open(os.path.join(RES, "etapa2_validacion.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
