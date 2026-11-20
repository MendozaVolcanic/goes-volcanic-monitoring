"""H11: senales SECO por pixel, bandera CF por cuadro, AUC y veredicto segun criterio_H11_2026-11-19.md.

Uso: python h11_analisis.py <salida.txt>
Lee los npz de rt_niveles.py (R_clr y R_cld por nivel) y las escenas L1b del cache. No recalcula fisica del
modelo. Bandas: indice 0 = C10 (7,3), 1 = C11 (8,4), 2 = C14 (11,2), 3 = C15 (12,3).
"""
import os, sys, pickle
import numpy as np
from scipy.stats import rankdata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h11 as C  # noqa: E402
rt = C.rt
LPT = np.log(rt.PTOP)          # 33 bordes, de 1000 a 1 hPa (presion decreciente)
I73, I85, I11, I12 = 0, 1, 2, 3
B = rt.BANDS


def cld_en(rcld_px, lp):
    """R_cld (4 bandas) interpolada en ln p sobre los bordes validos de un pixel."""
    ok = np.isfinite(rcld_px[:, 0])
    x = LPT[ok][::-1]; out = np.empty(4)
    for j in range(4):
        out[j] = np.interp(lp, x, rcld_px[ok, j][::-1])
    return out


def eps(robs, rclr, rcld):
    with np.errstate(all="ignore"):
        return (robs - rclr) / (rcld - rclr)


def beta(ea, e11):
    with np.errstate(all="ignore"):
        ok = (ea > 0) & (ea < 1) & (e11 > 0) & (e11 < 1)
        return np.where(ok, np.log1p(-ea) / np.log1p(-e11), np.nan)


def beta_opaco(robs, rclr, rcld_px, ptropo, ia):
    """Bajando desde la tropopausa, primer nivel con eps(a) o eps(11) >= 0,98; beta(a/11) en ese nivel."""
    ok = np.isfinite(rcld_px[:, 0])
    lps = [np.log(ptropo)] + [l for l, v in zip(LPT, ok) if v and l > np.log(ptropo)][::-1]
    lps = np.array(sorted(set(lps)))          # ln p creciente = bajando
    prev = None
    for lp in lps:
        rc = cld_en(rcld_px, lp)
        f = max(eps(robs[ia], rclr[ia], rc[ia]), eps(robs[I11], rclr[I11], rc[I11]))
        if np.isfinite(f) and f >= 0.98:
            if prev is None:
                lx = lp
            else:                               # cruce fino entre el nivel anterior y este
                lx = lp
                for s in np.linspace(prev, lp, 21)[1:]:
                    r2 = cld_en(rcld_px, s)
                    g = max(eps(robs[ia], rclr[ia], r2[ia]), eps(robs[I11], rclr[I11], r2[I11]))
                    if np.isfinite(g) and g >= 0.98:
                        lx = s; break
            rc = cld_en(rcld_px, lx)
            return float(beta(eps(robs[ia], rclr[ia], rc[ia]), eps(robs[I11], rclr[I11], rc[I11])))
        prev = lp
    return np.nan


def senales(par, rol):
    dt = C.dtk(par[rol]); s = C.load(dt)
    z = np.load(os.path.join(C.RTDIR, f"{par['pos']}_{rol}.npz"))
    ys, xs, full = z["ys"], z["xs"], z["full"]
    n = len(ys)
    robs = np.stack([s["rad"][b][ys, xs] for b in B], 1)
    rclr = z["rclr"]
    btclr = np.stack([rt.bt_de_rad(rclr[:, j], s["co"][b]) for j, b in enumerate(B)], 1)
    btobs = np.stack([s[b][ys, xs] for b in B], 1)
    out = {"ys": ys, "xs": xs, "full": full, "btbias": btclr[:, I11] - btobs[:, I11],
           "btd": btobs[:, I11] - btobs[:, I12], "btd_clr": btclr[:, I11] - btclr[:, I12]}
    out["btd_bias"] = out["btd_clr"] - out["btd"]
    E = {k: np.full(n, np.nan) for k in ("e11", "bt12", "bt85", "bt73", "bo12", "bo85", "e85", "e73", "e12")}
    for i in np.nonzero(full)[0]:
        rc = cld_en(z["rcld"][i], np.log(z["ptropo"][i]))
        e = eps(robs[i], rclr[i], rc)
        E["e11"][i], E["e12"][i], E["e85"][i], E["e73"][i] = e[I11], e[I12], e[I85], e[I73]
        E["bt12"][i] = beta(e[I12], e[I11]); E["bt85"][i] = beta(e[I85], e[I11]); E["bt73"][i] = beta(e[I73], e[I11])
        E["bo12"][i] = beta_opaco(robs[i], rclr[i], z["rcld"][i], z["ptropo"][i], I12)
        E["bo85"][i] = beta_opaco(robs[i], rclr[i], z["rcld"][i], z["ptropo"][i], I85)
    out.update(E)
    e11, b12, bo12, btd = E["e11"], E["bt12"], E["bo12"], out["btd"]
    with np.errstate(invalid="ignore"):
        pre = np.isfinite(b12) & (e11 >= 0.02) & (b12 <= 1.05)
        pre &= np.where(e11 >= 0.5, btd < -1.19 * e11 + 1.14, True)
        pre &= np.where(e11 < 0.5, out["btd_bias"] > -0.70 * e11 + 0.03, True)
        pre &= np.where(btd > 0, np.isfinite(bo12) & (bo12 < 1.36), True)
        a5 = (E["bt85"] > 1.5) & (E["bo85"] > 2.5) & (E["bt73"] > 1.0) & (e11 > 0.01)
    out["pre"] = np.where(full, pre, False).astype(float); out["a5"] = np.where(full, a5, False).astype(float)
    out["pre"][~full] = np.nan; out["a5"][~full] = np.nan
    out["zsfc"] = z["zsfc"]
    return out


def cf_de(bobj, benv):
    if not np.isfinite(bobj) or not np.isfinite(benv):
        return np.nan
    d = bobj - benv
    return 3 if (bobj > 18 or d > 6) else 2 if d > 4 else 1 if d > 2 else 0


def por_par(par):
    z = C.zonas(par["hv"], par["ash"])
    E11, nE = C.bt11_empirico(par)
    r = {"kpos": par["pos"], "kctrl": par["ctrl"], "origen": par["origen"], "dia": par["pos"][:8],
         "estrato": "N" if C.sza(C.dtk(par["pos"])) >= 80 else "D", "nE": nE, "n_h": int(z["h"].sum())}
    for rol in ("pos", "ctrl"):
        s = senales(par, rol); sc = C.load(C.dtk(par[rol]))
        idx = {(y, x): i for i, (y, x) in enumerate(zip(s["ys"], s["xs"]))}
        sel = {zn: np.array([idx[(y, x)] for y, x in zip(*np.nonzero(m))]) for zn, m in z.items()}
        ih, icf = sel["h"], sel["cf"]
        bobj = float(np.nanmean(s["btbias"][ih]))
        ycf, xcf = s["ys"][icf], s["xs"][icf]
        if E11 is not None:
            desp = sc[14][ycf, xcf] >= E11[ycf, xcf] - 3.0
        else:
            desp = np.ones(len(icf), bool)
        benv = float(np.nanmean(s["btbias"][icf][desp])) if desp.any() else np.nan
        benv_sf = float(np.nanmean(s["btbias"][icf]))
        nopre = ih[s["pre"][ih] == 0]
        bobj_np = float(np.nanmean(s["btbias"][nopre])) if len(nopre) else np.nan
        r[rol] = {"h": {k: s[k][ih] for k in ("e11", "bt12", "bo12", "bt85", "bo85", "bt73", "pre", "a5", "btd", "btbias", "e85", "e73", "e12")},
                  "an": {k: s[k][sel["an"]] for k in ("e11", "bt12", "bo12", "bt85", "bo85", "bt73", "pre", "a5")},
                  "bobj": bobj, "benv": benv, "benv_sf": benv_sf, "n_env": int(desp.sum()), "n_cf": len(icf),
                  "CF": cf_de(bobj, benv), "CF_sf": cf_de(bobj, benv_sf), "CF_np": cf_de(bobj_np, benv),
                  "zsfc_h": float(np.nanmedian(s["zsfc"][ih]))}
    return r


# ------------------------------------------------------------------ estadistica
LADO = {"a5": 1, "bt12": -1, "pre": 1, "e11": 1, "bo12": -1, "bt85": 1, "bo85": 1, "bt73": 1}
ES_BETA = {"bt12", "bo12", "bt85", "bo85", "bt73"}


def auc(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float); x = x[np.isfinite(x)]; y = y[np.isfinite(y)]
    if len(x) == 0 or len(y) == 0:
        return np.nan
    r = rankdata(np.concatenate([x, y]))
    return (r[:len(x)].sum() - len(x) * (len(x) + 1) / 2) / (len(x) * len(y))


def pool(R, met, zona):
    x = np.concatenate([r["pos"][zona][met] for r in R]) * LADO[met]
    y = np.concatenate([r["ctrl"][zona][met] for r in R]) * LADO[met]
    return x, y


def boot_dia(R, met, n=2000, seed=0):
    rng = np.random.default_rng(seed); dias = sorted({r["dia"] for r in R})
    U = [[r for r in R if r["dia"] == d] for d in dias]; v = []
    for _ in range(n):
        sel = [q for i in rng.integers(0, len(U), len(U)) for q in U[i]]
        v.append(auc(*pool(sel, met, "h")))
    v = np.array(v); v = v[np.isfinite(v)]
    return (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) else (np.nan, np.nan)


def bloque(R, met, nombre=""):
    x, y = pool(R, met, "h")
    nx, ny = int(np.isfinite(x).sum()), int(np.isfinite(y).sum())
    if met in ES_BETA and (nx < 20 or ny < 20):
        return {"met": met, "medible": False, "nx": nx, "ny": ny}, f"  {met:5s} no medible (validos {nx}/{ny})"
    A = auc(x, y); Aan = auc(*pool(R, met, "an")); lo, hi = boot_dia(R, met)
    dias = sorted({r["dia"] for r in R})
    pd = [(d, auc(*pool([r for r in R if r["dia"] == d], met, "h"))) for d in dias]
    dpos = sum(1 for _, a in pd if np.isfinite(a) and a > 0.5)
    sep = A >= 0.70 and lo > 0.55 and (A - Aan) >= 0.10 and dpos >= 2
    med = (np.nanmedian(x) * LADO[met], np.nanmedian(y) * LADO[met])
    txt = (f"  {met:5s} AUC={A:.3f} IC95dia=[{lo:.3f},{hi:.3f}] anillo={Aan:.3f} h-an={A - Aan:+.3f} dias>0,5={dpos}/{len(pd)}"
           f" | mediana pos/ctrl {med[0]:+.3f}/{med[1]:+.3f} (n {nx}/{ny}) | SEPARA={sep}")
    return {"met": met, "medible": True, "A": A, "lo": lo, "hi": hi, "Aan": Aan, "dpos": dpos, "sep": sep, "pd": pd}, txt


def informe(R):
    L = []
    L.append(f"Pares: {len(R)} | dias: {len({r['dia'] for r in R})} | N (cenit >= 80): {sum(r['estrato'] == 'N' for r in R)}"
             f" | D: {sum(r['estrato'] == 'D' for r in R)} | pixeles de huella: {sum(r['n_h'] for r in R)}")
    L.append("\n== Por par: pos ctrl estrato n_h | CF pos/ctrl (sin filtro nube, obj sin prefiltro) | BTbias_obj pos/ctrl | BTbias_env pos/ctrl | n_env/n_cf | frac pre pos/ctrl | frac A5 pos/ctrl | zsfc GFS huella")
    for r in R:
        p, c = r["pos"], r["ctrl"]
        L.append(f"{r['kpos']} {r['kctrl']} {r['estrato']} {r['n_h']:3d} | {p['CF']}/{c['CF']} ({p['CF_sf']}/{c['CF_sf']}, {p['CF_np']}/{c['CF_np']})"
                 f" | {p['bobj']:+6.2f}/{c['bobj']:+6.2f} | {p['benv']:+6.2f}/{c['benv']:+6.2f} | {p['n_env']}/{p['n_cf']} {c['n_env']}/{c['n_cf']}"
                 f" | {np.nanmean(p['h']['pre']):.2f}/{np.nanmean(c['h']['pre']):.2f} | {np.nanmean(p['h']['a5']):.2f}/{np.nanmean(c['h']['a5']):.2f} | {p['zsfc_h']:.0f} m")
    res = {}
    for nombre, sel in (("AGRUPADO (decide)", lambda r: True), ("Estrato N (informativo)", lambda r: r["estrato"] == "N"),
                        ("Estrato D (informativo)", lambda r: r["estrato"] == "D")):
        RR = [r for r in R if sel(r)]
        if not RR:
            continue
        L.append(f"\n==== {nombre}: {len(RR)} pares, {len({r['dia'] for r in RR})} dias")
        for v in ("CF", "CF_sf", "CF_np"):
            cp = [r["pos"][v] for r in RR]; cc = [r["ctrl"][v] for r in RR]
            fp = np.mean([x >= 3 for x in cp if np.isfinite(x)]) if any(np.isfinite(cp)) else np.nan
            fc = np.mean([x >= 3 for x in cc if np.isfinite(x)]) if any(np.isfinite(cc)) else np.nan
            L.append(f"  {v:6s} CF>=3 pos={fp:.3f} ctrl={fc:.3f} | distribucion pos {np.bincount([int(x) for x in cp if np.isfinite(x)], minlength=4)} ctrl {np.bincount([int(x) for x in cc if np.isfinite(x)], minlength=4)}"
                     f" | sin valor pos/ctrl {sum(not np.isfinite(x) for x in cp)}/{sum(not np.isfinite(x) for x in cc)}")
            res[(nombre, v)] = (fp, fc)
        bob = np.array([r["pos"]["bobj"] for r in RR]); boc = np.array([r["ctrl"]["bobj"] for r in RR])
        bep = np.array([r["pos"]["benv"] for r in RR]); bec = np.array([r["ctrl"]["benv"] for r in RR])
        L.append(f"  medianas BTbias_obj pos/ctrl {np.nanmedian(bob):+.2f}/{np.nanmedian(boc):+.2f} K; BTbias_env pos/ctrl {np.nanmedian(bep):+.2f}/{np.nanmedian(bec):+.2f} K;"
                 f" diferencia obj-env pos/ctrl {np.nanmedian(bob - bep):+.2f}/{np.nanmedian(boc - bec):+.2f} K")
        a5p = np.mean([np.nansum(r["pos"]["h"]["a5"]) > 0 for r in RR]); a5c = np.mean([np.nansum(r["ctrl"]["h"]["a5"]) > 0 for r in RR])
        L.append(f"  A5 por cuadro (>=1 pixel en la huella): pos={a5p:.3f} ctrl={a5c:.3f}")
        for met in ("a5", "bt12", "pre", "e11", "bo12", "bt85", "bo85", "bt73"):
            d, t = bloque(RR, met); L.append(t); res[(nombre, met)] = d
    # veredicto
    fp, fc = res[("AGRUPADO (decide)", "CF")]
    g = lambda m: res[("AGRUPADO (decide)", m)]  # noqa: E731
    sep = [m for m in ("a5", "bt12") if g(m).get("sep")]
    debil = all((not g(m).get("medible", False)) or g(m)["A"] < 0.60 for m in ("a5", "bt12", "pre"))
    if fp < 0.5:
        v = "SE FALSA (a): CF_pos < 0,50"
    elif fc >= 0.8 and fp >= 0.8 and sep:
        v = f"SE SOSTIENE: CF_ctrl y CF_pos >= 0,80 y separa {sep}"
    elif fc >= 0.8 and debil:
        v = "SE FALSA (b): CF_ctrl >= 0,80 y ni A5, ni beta_tot(12/11), ni los prefiltros llegan a AUC 0,60 del lado de la ceniza"
    else:
        v = "NO CONCLUYENTE"
    L.append(f"\nCF>=3 agrupado: pos={fp:.3f} ctrl={fc:.3f}; separan: {sep or 'ninguna'}\nVEREDICTO H11: {v}")
    return "\n".join(L)


if __name__ == "__main__":
    R = []
    for p in C.pares():
        if all(os.path.exists(os.path.join(C.RTDIR, f"{p['pos']}_{r}.npz")) for r in ("pos", "ctrl")):
            R.append(por_par(p))
        else:
            print("sin rt:", p["pos"], flush=True)
    pickle.dump(R, open(os.path.join(C.TRABAJO, "h11_pares.pkl"), "wb"))
    txt = informe(R)
    open(sys.argv[1], "w", encoding="utf-8").write(txt)
    print(txt)
