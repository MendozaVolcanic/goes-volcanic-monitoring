r"""H26, enmienda post hoc 1: diagnóstico del control positivo (informativo, no decide).
Enmienda: docs/own_volcat/h26_seguidor_volcat/enmienda_posthoc_1_2026-11-23.md (commit 6ac919e, antes de calcular).
Mismos tramos que h26_seguidor.py (semilla 26, misma lista elegible). Escribe resultados/h26_diagnostico_cp.csv y
resultados/h26_diagnostico_cp.log.
Uso: python -I h26_diagnostico_cp.py
"""
import os
import sys
import glob
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h26_seguidor as S  # noqa: E402

K, P17 = S.K, S.P17
LOG = []


def p(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print(s, flush=True)


def main():
    idx = K.indice()
    cs, T, b11, btd = P17.cargar_ir(idx)
    D11 = np.full_like(b11, np.nan)
    DD = np.full_like(btd, np.nan)
    con_base = np.zeros(len(cs), bool)
    for i in range(len(cs)):
        _, B11, Bd = P17.base(i, T, b11, btd)
        if B11 is not None:
            D11[i], DD[i], con_base[i] = b11[i] - B11, btd[i] - Bd, True
    cal = pd.read_pickle(os.path.join(K.H17, "calor.pkl"))
    GATE = {s: S.compuerta(cal, s, T) for s in S.SITIOS}
    h9 = pd.read_csv(S.FRAMES_H9, parse_dates=["dt"])
    h9["f"] = h9.dt.dt.date
    evs = {datetime.strptime(os.path.basename(f).split("_s")[1][:12], "%Y%m%d%H%M")
           for f in glob.glob(os.path.join(K.EVDIR, "*.nc"))}
    dias_v = set(h9[(h9.clase == "P") | (h9.n_anc > 0)].f) | {e.date() for e in evs}
    fechas = np.array([t.date() for t in T])
    dias_sin = [d for d in sorted(set(fechas)) if d not in dias_v]
    ini = [i for i in range(len(cs) - 3)
           if fechas[i] in dias_sin and all(con_base[i + k] for k in range(4))
           and all(T[i + k + 1] - T[i + k] == timedelta(minutes=10) for k in range(3))
           and all(GATE["chillan"][i + k] for k in range(4))]
    rng = np.random.default_rng(S.SEMILLA)
    elegidos = sorted(rng.choice(ini, size=20, replace=False))
    p("tramos:", len(elegidos), "de", len(ini), "elegibles")

    filas = []
    for s in S.SITIOS:
        sint = S.pluma_sintetica(s)
        sd = ndimage.binary_dilation(sint, S.K3)
        for i0 in elegidos:
            seg = S.Seguidor()
            for k in range(4):
                i = i0 + k
                d11, dd = D11[i].copy(), DD[i].copy()
                nan_iny = int((~np.isfinite(d11[sint]) | ~np.isfinite(dd[sint])).sum())
                d11[sint] -= 3.0
                dd[sint] -= 1.5
                cand = S.candidatos("R1", d11, dd)
                obs = S.objetos(cand, s)
                gate = bool(GATE[s][i]) if s == "chillan" else True
                m = seg.paso(T[i], obs, gate)
                if k < 2:
                    continue
                obj_p = [n for mm, n, a in obs if (mm & sint).any()]
                otros = [n for mm, n, a in obs if not (mm & sint).any() and (mm & m).any()]
                fuera = int((m & ~sd).sum())
                tol = S.iou(m, sint)[0]
                filas.append(dict(sitio=s, inicio=cs[i0], k=k + 1, dispara=bool(m.any()),
                                  pluma_en_mascara=bool((m & sint).any()), iou=tol,
                                  n_obj_pluma=max(obj_p, default=0), n_obj_otros=len(otros), px_fuera=fuera,
                                  nan_inyectados=nan_iny, npx=int(m.sum())))
    df = pd.DataFrame(filas)
    df.to_csv(os.path.join(S.RES, "h26_diagnostico_cp.csv"), index=False, float_format="%.4f")

    for s, g in df.groupby("sitio", sort=False):
        t = g.groupby("inicio").agg(dispara=("dispara", "all"), pluma=("pluma_en_mascara", "all"),
                                    iou_min=("iou", "min"), n_obj_pluma=("n_obj_pluma", "max"),
                                    otros=("n_obj_otros", "max"), fuera=("px_fuera", "max"),
                                    nan=("nan_inyectados", "max"))
        t["pasa"] = t.dispara & (t.iou_min >= 0.5)

        def causa(r):
            if r.pasa:
                return "pasa"
            if not r.dispara or not r.pluma:
                return "a_no_dispara"
            if r.n_obj_pluma > 6:
                return "c_fusion"
            if r.otros > 0:
                return "b_otras_pistas"
            return "d_otra"
        t["causa"] = t.apply(causa, axis=1)
        p(f"\n== {s} ==")
        p(f"pasa {int(t.pasa.sum())}/20 | dispara en 3 y 4 con la pluma en la máscara {int((t.dispara & t.pluma).sum())}"
          f"/20 | IoU >= 0,5 en 3 y 4 {int((t.iou_min >= 0.5).sum())}/20")
        p("causas:", t.causa.value_counts().to_dict())
        p(f"objeto de la pluma (px, máx por tramo): mediana {t.n_obj_pluma.median():.0f}, máx {t.n_obj_pluma.max()}"
          f" | tramos con otras pistas en la máscara: {int((t.otros > 0).sum())} | px fuera mediana "
          f"{t.fuera.median():.0f} | píxeles inyectados sin base (NaN): {int(t.nan.sum())}")
        p(t.to_string())
    open(os.path.join(S.RES, "h26_diagnostico_cp.log"), "w", encoding="utf-8").write("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main()
