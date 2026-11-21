r"""H15 nivel B: ¿qué cielo despejado y qué nube negra usa VOLCAT para εtot y β? Aplica el criterio
`docs/own_volcat/lut_h15/cielo_sesgo/criterio_2026-11-21.md` (commit e88017d, antes de este script).

Pasos: (1) elige (V, N) en los cuadros 1 a 5 con nube espesa; (2) elige S en los cuadros 1 a 5 con nube tenue;
(3) valida en los cuadros 6 a 10; (4) nivel B de la etapa 2 con la variante de 7 tablas sin εtot × BTD.

Lee D:\goes_cache\lut_h15\ml (npz de ml_extraer.py), D:\goes_cache\volcat_test_mauna_loa\npz (máscara de agua)
y D:\goes_cache\lut_h15\cielo_sesgo\gfs_punto_frio.npz (gfs_punto_frio.py). Escribe en ../resultados/.

Uso: python -I cielo_sesgo.py
"""
import itertools
import json
import os
import sys

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.ndimage import uniform_filter

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "scripts"))
import lut_volcat as LV  # noqa: E402
import etapa2_validar as E  # noqa: E402

RES = os.path.join(os.path.dirname(HERE), "resultados")
CF = r"D:\goes_cache\lut_h15\cielo_sesgo\gfs_punto_frio.npz"
SH = (301, 500)
BANDAS = (10, 14, 15)
VENT = 12
MIN_DESP = 5
GFS_T = dict(np.load(os.path.join(E.ML, "gfs_ttropo.npz")))
GFS_CF = dict(np.load(CF))


def bt_de_rad(r, d, ch):
    k = ch - 1
    with np.errstate(all="ignore"):
        teff = d["fk2_planck"][k] / np.log1p(d["fk1_planck"][k] / r)
    return (teff - d["bc1_planck"][k]) / d["bc2_planck"][k]


def campo_gfs(h, d, campos):
    f = lambda k: d[k].astype(float)  # noqa: E731
    hh = int(h[:2]) + int(h[2:4]) / 60.0
    w = (hh - 6.0) / 6.0
    iy, ix = f("geocatRTM__nwp_y_index"), f("geocatRTM__nwp_x_index")
    ok = np.isfinite(iy) & np.isfinite(ix) & (iy >= 0) & (ix >= 0)
    out = np.full(iy.shape, np.nan)
    yy, xx = iy[ok].astype(int), ix[ok].astype(int)
    out[ok] = (1 - w) * campos["gfs.22112718_F012.hdf"][yy, xx] + w * campos["gfs.22112800_F012.hdf"][yy, xx]
    return out


class Cuadro:
    def __init__(self, h):
        self.h = h
        d = np.load(os.path.join(E.ML, f"ml_{h}.npz"))
        self.d = d
        f = lambda k: d[k].astype(float)  # noqa: E731
        self.obs = {b: f(f"geocatL1__channel_{b}_brightness_temperature") for b in BANDAS}
        self.clr = {b: f(f"geocatRTM__channel_{b}_brightness_temperature_clear") for b in BANDAS}
        self.ev = f("geocatDIAGS1__cloud_emissivity_ch14_tot")
        self.bv12 = f("geocatDIAGS1__cloud_beta_1112_tot")
        self.bv73 = f("geocatDIAGS1__cloud_beta_7311_tot")
        self.mu = np.cos(np.radians(f("geocatL1__pixel_satellite_zenith_angle")))
        self.tcld = {"N0": campo_gfs(h, d, GFS_T), "N1": campo_gfs(h, d, GFS_CF)}
        # máscaras de despejado
        self.m1 = ~np.isfinite(self.ev)
        b14, c14 = self.obs[14], self.clr[14]
        sd = np.sqrt(np.maximum(uniform_filter(b14 ** 2, 3) - uniform_filter(b14, 3) ** 2, 0))
        self.m2 = (b14 >= c14 - 2) & (np.abs((b14 - self.obs[15]) - (c14 - self.clr[15])) <= 1) & (sd <= 0.5)
        self.m2 &= np.isfinite(b14) & np.isfinite(c14)
        self._loc = {}
        A, _B, agua, v = E.cuadro(h, GFS_T)
        self.A, self.agua, self.verdad = A, agua, v

    def sesgo(self, tipo, masc, q, banda):
        """Per_q del sesgo (despejado − observado) en K, 2D; NaN = sin corrección."""
        m = self.m1 if masc == "M1" else self.m2
        b = self.clr[banda] - self.obs[banda]
        bm = np.where(m & np.isfinite(b), b, np.nan)
        if tipo == "G":
            return np.full(SH, np.nanpercentile(bm, q))
        key = (masc, banda)
        if key not in self._loc:
            n = uniform_filter(np.isfinite(bm).astype(float), 2 * VENT + 1, mode="constant") * (2 * VENT + 1) ** 2
            sel = (np.round(n) >= MIN_DESP) & np.isfinite(self.ev)
            pad = np.pad(bm, VENT, constant_values=np.nan)
            win = sliding_window_view(pad, (2 * VENT + 1, 2 * VENT + 1))
            yy, xx = np.where(sel)
            vals = win[yy, xx].reshape(len(yy), -1)
            res = {}
            for qq in (25, 50, 75):
                o = np.full(SH, np.nan)
                o[yy, xx] = np.nanpercentile(vals, qq, axis=1)
                res[qq] = o
            self._loc[key] = res
        return self._loc[key][q]

    def eps(self, V, N, S):
        """ε14 (con V), β(12/11), β(7,3/11) nuestros, 2D."""
        tc = self.tcld[N]
        e = {}
        for b in BANDAS:
            clr = self.clr[b]
            if S != "S0":
                tipo, masc, q, bandas = S
                if b in bandas:
                    s = self.sesgo(tipo, masc, q, b)
                    clr = np.where(np.isfinite(s), clr - s, clr)
            e[b] = LV.emisividad(E.rad(self.d, self.obs[b], b), E.rad(self.d, clr, b), E.rad(self.d, tc, b))
        b12 = LV.beta(e[15], e[14])
        b73 = LV.beta(e[10], e[14])
        e14 = e[14]
        if V == "V1":
            with np.errstate(all="ignore"):
                e14 = 1 - (1 - e14) ** self.mu
        return e14, b12, b73


BANDS_SETS = {"B1": (14,), "B2": (14, 15), "B3": (14, 15, 10)}


def variantes_S():
    out = ["S0"]
    for tipo, masc, q, bs in itertools.product(("G", "L"), ("M1", "M2"), (25, 50, 75), ("B1", "B2", "B3")):
        out.append((tipo, masc, q, BANDS_SETS[bs], bs))
    return out


def nombre_S(S):
    return "S0" if S == "S0" else f"{S[0]}_{S[1]}_p{S[2]}_{S[4]}"


def s4(S):
    return S if S == "S0" else S[:4]


def comparar(cs, V, N, S, lo, hi, hi_incl=True):
    E14, EV, B12, BV12, B73, BV73 = [], [], [], [], [], []
    for c in cs:
        e14, b12, b73 = c.eps(V, N, s4(S))
        sel = np.isfinite(c.ev) & np.isfinite(e14) & (c.ev >= lo) & ((c.ev <= hi) if hi_incl else (c.ev < hi))
        E14.append(e14[sel]); EV.append(c.ev[sel])
        B12.append(b12[sel]); BV12.append(c.bv12[sel]); B73.append(b73[sel]); BV73.append(c.bv73[sel])
    e14, ev, b12, bv12, b73, bv73 = map(np.concatenate, (E14, EV, B12, BV12, B73, BV73))
    de = e14 - ev
    ok12 = np.isfinite(b12) & np.isfinite(bv12)
    ok73 = np.isfinite(b73) & np.isfinite(bv73)
    db12 = b12[ok12] - bv12[ok12]
    db73 = b73[ok73] - bv73[ok73]
    return {
        "n": int(len(de)), "frac_eps_le_001": float(np.mean(np.abs(de) <= 0.01)) if len(de) else float("nan"),
        "deps_p05_p50_p95": [float(x) for x in np.percentile(de, [5, 50, 95])] if len(de) else [],
        "n_beta1211": int(ok12.sum()),
        "frac_b1211_le_002": float(np.mean(np.abs(db12) <= 0.02)) if len(db12) else float("nan"),
        "db1211_p05_p50_p95": [float(x) for x in np.percentile(db12, [5, 50, 95])] if len(db12) else [],
        "n_beta7311": int(ok73.sum()),
        "frac_b7311_le_002": float(np.mean(np.abs(db73) <= 0.02)) if len(db73) else float("nan"),
        "db7311_p05_p50_p95": [float(x) for x in np.percentile(db73, [5, 50, 95])] if len(db73) else [],
    }


def nivel_B(cs, V, N, S, T):
    LV.CONJUNTOS["S2sinBTD"] = [t for t in LV.IR_S1 + LV.IR_8511 if t[0] != "EMISS14_TOT_BTD1112_IR"]
    P, Vv, EPS = [], [], []
    for c in cs:
        e14, b12, b73 = c.eps(V, N, s4(S))
        B = dict(c.A)
        B["eps"], B["b_tot"], B["b73"] = e14.ravel(), b12.ravel(), b73.ravel()
        L, _ = LV.log_odds(T, "S2sinBTD", B, c.agua, modo="b", comb="J")
        P.append(LV.prob(L)); Vv.append(c.verdad); EPS.append(c.A["eps"])
    p, v, e = map(np.concatenate, (P, Vv, EPS))
    out = {"todo": {**E.metricas(p, v), "cumpliria_regla_etapa2": E.cumple(E.metricas(p, v))}}
    for lo, hi in ((0.0, 0.2), (0.2, 0.5), (0.5, 1.01)):
        s = (e >= lo) & (e < hi)
        out[f"eps_{lo}_{hi}"] = E.metricas(p[s], v[s])
    return out


def main():
    print("cargando cuadros...", flush=True)
    C = {h: Cuadro(h) for h in E.HORAS}
    c15 = [C[h] for h in E.ELIGE]
    c610 = [C[h] for h in E.VALIDA]
    out = {"criterio": "docs/own_volcat/lut_h15/cielo_sesgo/criterio_2026-11-21.md (commit e88017d)"}

    # cobertura de la corrección local (informativo)
    cob = {}
    for masc in ("M1", "M2"):
        for grupo, cs in (("1a5", c15), ("6a10", c610)):
            tot = con = 0
            for c in cs:
                s = c.sesgo("L", masc, 50, 14)
                sel = np.isfinite(c.ev) & (c.ev >= 0.05) & (c.ev <= 0.9)
                tot += sel.sum(); con += (sel & np.isfinite(s)).sum()
            cob[f"{masc}_{grupo}"] = {"pixeles_0.05_0.9": int(tot), "con_correccion_local": int(con),
                                      "fraccion": float(con / tot)}
        sb = {b: [float(x) for x in np.nanpercentile(np.concatenate(
            [(c.clr[b] - c.obs[b])[(c.m1 if masc == "M1" else c.m2)] for c in c15]), [25, 50, 75])] for b in BANDAS}
        cob[f"{masc}_sesgo_desp_menos_obs_p25_50_75_cuadros_1a5"] = sb
        cob[f"{masc}_fraccion_despejada_1a5"] = float(np.mean([(c.m1 if masc == "M1" else c.m2).mean() for c in c15]))
    out["cobertura"] = cob
    print(json.dumps(cob, indent=1), flush=True)

    # paso 1: (V, N) con nube espesa, cuadros 1 a 5, S0
    p1 = {}
    for V, N in itertools.product(("V0", "V1"), ("N0", "N1")):
        p1[f"{V}_{N}"] = comparar(c15, V, N, "S0", 0.85, 0.98)
        print("paso1", V, N, round(p1[f"{V}_{N}"]["frac_eps_le_001"], 4), flush=True)
    vn = max(p1, key=lambda k: p1[k]["frac_eps_le_001"])
    V, N = vn.split("_")
    out["paso1_VN_cuadros_1a5_eps_0.85_0.98"] = p1
    out["paso1_elegido"] = vn

    # paso 2: S con nube tenue, cuadros 1 a 5
    p2 = {}
    for S in variantes_S():
        p2[nombre_S(S)] = comparar(c15, V, N, S, 0.05, 0.5, hi_incl=False)
        m = p2[nombre_S(S)]
        print("paso2", nombre_S(S), round(m["frac_eps_le_001"], 4), round(m["frac_b1211_le_002"], 4), flush=True)
    orden = {"S0": 0, "G": 1, "L": 2}
    mejor = max(m["frac_eps_le_001"] for m in p2.values())
    cand = [k for k, m in p2.items() if m["frac_eps_le_001"] >= mejor - 0.002]
    mejor_b = max(p2[k]["frac_b1211_le_002"] for k in cand)
    cand = [k for k in cand if p2[k]["frac_b1211_le_002"] >= mejor_b - 0.002]
    sel = min(cand, key=lambda k: orden[k.split("_")[0]])
    S = next(s for s in variantes_S() if nombre_S(s) == sel)
    out["paso2_S_cuadros_1a5_eps_0.05_0.5"] = p2
    out["paso2_elegido"] = sel
    print("elegido:", V, N, sel, flush=True)

    # paso 3: validación, cuadros 6 a 10
    val = comparar(c610, V, N, S, 0.05, 0.9)
    val["cumple"] = bool(val["frac_eps_le_001"] >= 0.80 and val["frac_b1211_le_002"] >= 0.80)
    out["paso3_validacion_cuadros_6a10_eps_0.05_0.9"] = val
    out["paso3_por_tramo"] = {f"{lo}_{hi}": comparar(c610, V, N, S, lo, hi, hi_incl=(hi == 0.9))
                             for lo, hi in ((0.05, 0.2), (0.2, 0.5), (0.5, 0.9))}
    out["paso3_V0_con_N_S_elegidos"] = comparar(c610, "V0", N, S, 0.05, 0.9)
    out["paso3_V1_N_S0"] = comparar(c610, V, N, "S0", 0.05, 0.9)
    print("validacion:", json.dumps(val, indent=1), flush=True)

    # paso 4: nivel B de la etapa 2, 7 tablas sin εtot × BTD
    T = LV.Tablas()
    out["paso4_nivelB_S2sinBTD_cuadros_6a10"] = nivel_B(c610, V, N, S, T)
    out["paso4_nivelB_S2sinBTD_V0_N0_S0_referencia_H15"] = nivel_B(c610, "V0", "N0", "S0", T)
    for k in ("paso4_nivelB_S2sinBTD_cuadros_6a10", "paso4_nivelB_S2sinBTD_V0_N0_S0_referencia_H15"):
        print(k, {x: {y: (round(z, 3) if isinstance(z, float) else z) for y, z in m.items()
                      if y in ("n", "n_volcat_ge05", "frac_dif_le_005", "kappa_05", "frac_ge05_recuperada")}
                  for x, m in out[k].items()}, flush=True)

    with open(os.path.join(RES, "cielo_sesgo.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print("ok", os.path.join(RES, "cielo_sesgo.json"))


if __name__ == "__main__":
    main()
