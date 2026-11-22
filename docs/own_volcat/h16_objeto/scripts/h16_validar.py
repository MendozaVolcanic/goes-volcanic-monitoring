r"""H16 §3 y §4 del criterio: elige variante en los cuadros 1 a 5 de Mauna Loa y valida en los 6 a 10.

Verdad: Feature_Prob_Term_IR y Non_Feature_Prob_Term_IR de cada objeto ASHOBJ (VOLCAT). Entradas por píxel: las de
VOLCAT (DIAGS1: εtot, β) y desviación de BT11 3 × 3 nuestra sobre su BT11 de la L1. Píxeles del objeto: índices
ASHOBJ (base 1). Área por píxel: pixel_area de su L2.
Insumos fuera del repo: D:\goes_cache\lut_h15\ml (ml_extraer.py del PR 75) y D:\goes_cache\h16_objeto\ml
(h16_extraer.py). Escribe resultados/validacion_mauna_loa.json y validacion_objetos.csv.
Uso: python -I h16_validar.py
"""
import csv
import itertools
import json
import os
import sys

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h16_objeto as O  # noqa: E402

ML = r"D:\goes_cache\lut_h15\ml"
OB = r"D:\goes_cache\h16_objeto\ml"
RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
HORAS = ["091600", "092100", "092600", "093100", "093600", "094100", "094600", "095100", "095600", "100130"]
ELIGE, VALIDA = HORAS[:5], HORAS[5:]


def sdev3(bt, ddof):
    w = sliding_window_view(np.pad(bt, 1, mode="edge"), (3, 3))
    return np.nanstd(w, axis=(2, 3), ddof=ddof)


def cuadro(h):
    d = np.load(os.path.join(ML, f"ml_{h}.npz"))
    g = lambda k: d[k].astype(float)  # noqa: E731
    D = "geocatDIAGS1__"
    bt14 = g("geocatL1__channel_14_brightness_temperature")
    P = {"eps": g(D + "cloud_emissivity_ch14_tot"), "b": g(D + "cloud_beta_1112_tot"),
         "bop": g(D + "cloud_beta_1112_opaque"), "b85": g(D + "cloud_beta_8511_tot"),
         "b85op": g(D + "cloud_beta_8511_opaque"), "b73": g(D + "cloud_beta_7311_tot"),
         "sd0": sdev3(bt14, 0), "sd1": sdev3(bt14, 1)}
    area = np.load(os.path.join(OB, f"area_{h}.npy"))
    o = np.load(os.path.join(OB, f"obj_{h}.npz"))
    sz = o["ASHOBJ_Object_Size"].astype(int)
    x = o["ASHOBJ_Object_X_Index"].astype(int) - 1
    y = o["ASHOBJ_Object_Y_Index"].astype(int) - 1
    cs = np.concatenate([[0], np.cumsum(sz)])
    objs = []
    for i in range(len(sz)):
        yy, xx = y[cs[i]:cs[i + 1]], x[cs[i]:cs[i + 1]]
        objs.append(dict(h=h, i=i, n=int(sz[i]), px={k: v[yy, xx] for k, v in P.items()}, area=area[yy, xx],
                         ta=np.log10(o["ASHOBJ_Feature_Prob_Term_IR"][i]),
                         tc=np.log10(o["ASHOBJ_Non_Feature_Prob_Term_IR"][i]),
                         p=float(o["ASHOBJ_Feature_Prob_IR"][i])))
    return objs


def evaluar(objs, var):
    sdv, regla, desemp, b73 = var
    out = []
    for ob in objs:
        px = dict(ob["px"])
        px["sd"] = px[sdv]
        la, lc = O.termino(px, ob["area"], sdregla=regla, desempate=desemp, b73=b73)
        out.append((la, lc))
    return np.array(out)


def metricas(objs, T):
    ta = np.array([o["ta"] for o in objs]); tc = np.array([o["tc"] for o in objs])
    dodds = np.abs((T[:, 0] - T[:, 1]) - (ta - tc))
    exacto = (np.abs(T[:, 0] - ta) < 0.01) & (np.abs(T[:, 1] - tc) < 0.01)
    pv = np.array([o["p"] for o in objs]); pn = O.prob(T[:, 0], T[:, 1])
    return {"n": int(len(objs)), "mediana_dlog10odds": float(np.median(dodds)),
            "frac_dentro_1_decada": float(np.mean(dodds <= 1.0)), "frac_exacto": float(np.mean(exacto)),
            "p90_dlog10odds": float(np.percentile(dodds, 90)),
            "n_P05_volcat": int((pv >= 0.5).sum()), "n_P05_nuestro": int((pn >= 0.5).sum()),
            "concuerdan_P05": int(((pv >= 0.5) == (pn >= 0.5)).sum())}, dodds, pn


def main():
    todos = {h: cuadro(h) for h in HORAS}
    sel = lambda hs, m: [o for h in hs for o in todos[h] if m(o)]  # noqa: E731
    multi = lambda o: o["n"] >= 2 and o["ta"] < 0  # noqa: E731
    uno = lambda o: o["n"] == 1 and o["ta"] < 0  # noqa: E731
    variantes = list(itertools.product(("sd0", "sd1"), ("tal", "sin075"), ("menor", "mayor"), ("finito", "eps01")))
    elige = sel(ELIGE, multi)
    tabla = []
    for v in variantes:
        m, _, _ = metricas(elige, evaluar(elige, v))
        tabla.append((m["mediana_dlog10odds"], v, m))
        print("elige", v, {k: round(m[k], 3) for k in ("mediana_dlog10odds", "frac_dentro_1_decada", "frac_exacto")}, flush=True)
    tabla.sort(key=lambda t: t[0])
    mejor = tabla[0][1]
    print("variante elegida:", mejor)
    val = sel(VALIDA, multi)
    Tv = evaluar(val, mejor)
    mv, dodds, pn = metricas(val, Tv)
    mu, _, _ = metricas(sel(VALIDA, uno), evaluar(sel(VALIDA, uno), mejor))
    valida = mv["mediana_dlog10odds"] <= 0.3 and mv["frac_dentro_1_decada"] >= 0.8
    res = {"variante": dict(zip(("sd", "regla_sd", "desempate", "b73"), mejor)),
           "eleccion_cuadros_1a5": [{"variante": list(t[1]), **t[2]} for t in tabla],
           "validacion_cuadros_6a10_multi": mv, "info_cuadros_6a10_un_pixel": mu,
           "umbral": "mediana |dlog10 odds| <= 0,3 y >= 80 % dentro de 1 decada", "valida": bool(valida)}
    os.makedirs(RES, exist_ok=True)
    json.dump(res, open(os.path.join(RES, "validacion_mauna_loa.json"), "w", encoding="utf-8"), indent=1)
    with open(os.path.join(RES, "validacion_objetos.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cuadro", "objeto", "n_px", "l10_Tceniza_volcat", "l10_Tnube_volcat", "l10_Tceniza_nuestro",
                    "l10_Tnube_nuestro", "P_volcat", "P_nuestro"])
        for o, t, p in zip(val, Tv, pn):
            w.writerow([o["h"], o["i"], o["n"], round(o["ta"], 4), round(o["tc"], 4), round(t[0], 4), round(t[1], 4),
                        f"{o['p']:.4g}", f"{p:.4g}"])
    print(json.dumps({k: res[k] for k in ("variante", "validacion_cuadros_6a10_multi", "info_cuadros_6a10_un_pixel", "valida")},
                     indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
