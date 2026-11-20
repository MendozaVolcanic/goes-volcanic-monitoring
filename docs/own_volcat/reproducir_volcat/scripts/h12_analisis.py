"""H12: Test 3 original de Francis et al. 2012 en la huella VOLCAT de Chillan, su control y las cumbres sin actividad.

Uso: python h12_analisis.py <salida.txt>
Criterio: docs/own_volcat/reproducir_volcat/criterio_H12_2026-11-20.md (commit ae954b0, antes de medir).

Conjunto A (decide): pares de H11 con cielo despejado calculado directo por pixel (rt_h11). Conjunto B (replica):
pares nuevos de E2 (pareo solo por BT11, comun_h12.pareo_e2) con el cielo despejado de la rejilla de E2 (feat_e2,
rt_e2). Cumbres y llano: huella trasladada, modelo directo (h12_rt_sitios.py). No cambia fisica de ningun modelo.
"""
import os, sys, json, pickle
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h11 as C  # noqa: E402
import comun_h12 as H  # noqa: E402
import h11_analisis as A  # noqa: E402

rt = C.rt
SHAPE = C.LAT.shape
K3 = np.ones((3, 3))


def bt_clr(rclr, co, j):
    return rt.bt_de_rad(rclr[:, j], co)


def nueve(grid_t3, ys, xs):
    """Paso 5: cuantos de los 9 de la caja 3x3 cumplen T3 (vecino sin calculo = no marcado)."""
    g = np.where(np.isfinite(grid_t3), grid_t3, 0.0)
    return ndimage.convolve(g, K3, mode="constant", cval=0.0)[ys, xs]


def variantes(btd, btdc, b85, b12, n9):
    t = H.t3(btd, btdc)
    rej = H.rechazo_beta(b85, b12)
    nomed = ~(np.isfinite(b85) & np.isfinite(b12))
    return {"t3": t, "t3b": t & ~nomed & ~rej, "t3b_cons": t & (nomed | ~rej), "t3_69": t & (n9 >= 6),
            "t1": btd < -2.0, "b_nomed": t & nomed}


def pix_sitio(cj, kp, rol, sitio, dt):
    p = os.path.join(H.RTSIT, f"{cj}_{kp}_{rol}_{sitio}.npz")
    if not os.path.exists(p):
        return None
    z = np.load(p); s = C.load(dt) if C.path_escena(dt) else _load_e2(dt)
    ys, xs = z["ys"], z["xs"]
    robs = np.stack([s["rad"][b][ys, xs] for b in C.BANDS], 1)
    btd = s[14][ys, xs] - s[15][ys, xs]
    btdc = bt_clr(z["rclr"], s["co"][14], 2) - bt_clr(z["rclr"], s["co"][15], 3)
    b85 = np.full(len(ys), np.nan); b12 = np.full(len(ys), np.nan)
    for i in range(len(ys)):
        b85[i], b12[i] = H.beta_francis(robs[i], z["rclr"][i], z["rcld"][i], z["tb"][i], z["ptropo"][i], s[14][ys[i], xs[i]])
    g = np.full(SHAPE, np.nan); g[ys, xs] = H.t3(btd, btdc)
    V = variantes(btd, btdc, b85, b12, nueve(g, ys, xs))
    b11 = bt_clr(z["rclr"], s["co"][14], 2) - s[14][ys, xs]
    return {"btd": btd, "btdc": btdc, "m": H.margen(btd, btdc), "zsfc": z["zsfc"], "b11": b11, **V}


def _load_e2(dt):
    import rt_e2 as E
    return E.load(dt)


# ------------------------------------------------------------------ conjunto A
def rol_A(par, rol):
    dt = C.dtk(par[rol]); s = C.load(dt)
    z = np.load(os.path.join(C.RTDIR, f"{par['pos']}_{rol}.npz"))
    ys, xs, full = z["ys"], z["xs"], z["full"]
    btd = s[14][ys, xs] - s[15][ys, xs]
    btdc = bt_clr(z["rclr"], s["co"][14], 2) - bt_clr(z["rclr"], s["co"][15], 3)
    g = np.full(SHAPE, np.nan); g[ys, xs] = H.t3(btd, btdc)
    idx = {(y, x): i for i, (y, x) in enumerate(zip(ys, xs))}
    Z = C.zonas(par["hv"], par["ash"]); out = {}
    for zn in ("h", "an"):
        yy, xx = np.nonzero(Z[zn]); ii = np.array([idx[(y, x)] for y, x in zip(yy, xx)])
        b85 = np.full(len(ii), np.nan); b12 = np.full(len(ii), np.nan)
        if zn == "h":
            robs = np.stack([s["rad"][b][yy, xx] for b in C.BANDS], 1)
            for q, i in enumerate(ii):
                if full[i]:
                    b85[q], b12[q] = H.beta_francis(robs[q], z["rclr"][i], z["rcld"][i], z["tb"][i], z["ptropo"][i], s[14][yy[q], xx[q]])
        V = variantes(btd[ii], btdc[ii], b85, b12, nueve(g, yy, xx))
        b11 = bt_clr(z["rclr"][ii], s["co"][14], 2) - s[14][yy, xx]
        out[zn] = {"btd": btd[ii], "btdc": btdc[ii], "m": H.margen(btd[ii], btdc[ii]), "zsfc": z["zsfc"][ii], "b11": b11, **V}
    return out


def conjunto_A():
    R = []
    for p in C.pares():
        if not all(os.path.exists(os.path.join(C.RTDIR, f"{p['pos']}_{r}.npz")) for r in ("pos", "ctrl")):
            continue
        r = {"conj": "A", "kpos": p["pos"], "kctrl": p["ctrl"], "dia": p["pos"][:8],
             "estrato": "N" if C.sza(C.dtk(p["pos"])) >= 80 else "D"}
        for rol in ("pos", "ctrl"):
            r[rol] = rol_A(p, rol)
            r["s_" + rol] = {s: pix_sitio("A", p["pos"], rol, s, C.dtk(p[rol])) for s in H.SITIOS}
        R.append(r)
    return R


# ------------------------------------------------------------------ conjunto B
def _tb_interp(w, ys, xs):
    import rt_e2 as E
    ny, nx = len(E.NODOS_Y), len(E.NODOS_X); tb = w["tb"].reshape(ny, nx, -1)
    fy = (ys - E.Y0) / E.PASO; fx = (xs - E.X0) / E.PASO
    iy = np.clip(np.floor(fy).astype(int), 0, ny - 2); ix = np.clip(np.floor(fx).astype(int), 0, nx - 2)
    wy = (fy - iy)[:, None]; wx = (fx - ix)[:, None]
    return (tb[iy, ix] * (1 - wy) * (1 - wx) + tb[iy, ix + 1] * (1 - wy) * wx + tb[iy + 1, ix] * wy * (1 - wx)
            + tb[iy + 1, ix + 1] * wy * wx)


def rol_B(kk, h_grid, con_beta=True):
    import rt_e2 as E
    from rt_niveles import _i2
    dt = C.dtk(kk); f = H.feat(dt)
    ys, xs = f["ys"], f["xs"]; btd = f["btd"]; btdc = f["btd"] + f["btd_bias"]
    g = np.full(SHAPE, np.nan); g[ys, xs] = H.t3(btd, btdc)
    sel = h_grid[ys, xs]; yy, xx = ys[sel], xs[sel]
    b85 = np.full(sel.sum(), np.nan); b12 = np.full(sel.sum(), np.nan)
    if con_beta and sel.any():
        s = E.load(dt); w = np.load(os.path.join(E.RTE2, C.k(dt) + ".npz"))
        rclr, rcld = E.interp(w, yy, xx); tb = _tb_interp(w, yy, xx)
        g2 = dict(np.load(C.path_gfs(dt))); pt = _i2(g2, g2["ptropo"], C.LAT[yy, xx], C.LON[yy, xx])
        robs = np.stack([s["rad"][b][yy, xx] for b in C.BANDS], 1)
        for q in range(len(yy)):
            b85[q], b12[q] = H.beta_francis(robs[q], rclr[q], rcld[q], tb[q], pt[q], s[14][yy[q], xx[q]])
    V = variantes(btd[sel], btdc[sel], b85, b12, nueve(g, yy, xx))
    return {"h": {"btd": btd[sel], "btdc": btdc[sel], "m": H.margen(btd[sel], btdc[sel]), "zsfc": f["zsfc"][sel],
                  "b11": f["btclr11"][sel] - f["bt11"][sel], **V}}


def conjunto_B():
    R = []
    for q in H.pareo_e2():
        if q["estado"] != "ok":
            continue
        hg = H.huella_b_grid(q["pos"])
        r = {"conj": "B", "kpos": q["pos"], "kctrl": q["ctrl"], "dia": q["pos"][:8],
             "estrato": "N" if float(H.feat(C.dtk(q["pos"]))["sza"]) >= 80 else "D"}
        for rol in ("pos", "ctrl"):
            r[rol] = rol_B(q[rol], hg)
            r["s_" + rol] = {s: pix_sitio("B", q["pos"], rol, s, C.dtk(q[rol])) for s in H.SITIOS}
        R.append(r)
    return R


def escenas_B():
    """Informativo: objeto T3 anclado (>= 2 px 8-conexos, uno a <= 10 km) por escena de E2."""
    out = []
    for kk, tipo in sorted(H.escenas_e2().items()):
        f = H.feat(C.dtk(kk)); g = np.zeros(SHAPE, bool)
        t = H.t3(f["btd"], f["btd"] + f["btd_bias"]); g[f["ys"][t], f["xs"][t]] = True
        lab, n = ndimage.label(g, np.ones((3, 3)))
        D = H.dist_crater(); anc = False
        for i in range(1, n + 1):
            m = lab == i
            if m.sum() >= 2 and (D[m] <= 10).any():
                anc = True; break
        out.append({"k": kk, "tipo": tipo, "anc": anc, "frac10": float(t[f["dist"] <= 10].mean()),
                    "estrato": "N" if float(f["sza"]) >= 80 else "D"})
    return out


# ------------------------------------------------------------------ estadistica
def pool(R, zona, met, rol):
    return np.concatenate([r[rol][zona][met] for r in R]).astype(float)


def auc_m(R, zona="h"):
    return A.auc(pool(R, zona, "m", "pos"), pool(R, zona, "m", "ctrl"))


def boot(R, n=2000, seed=0):
    rng = np.random.default_rng(seed); dias = sorted({r["dia"] for r in R})
    U = [[r for r in R if r["dia"] == d] for d in dias]; v = []
    for _ in range(n):
        sel = [q for i in rng.integers(0, len(U), len(U)) for q in U[i]]
        v.append(auc_m(sel))
    v = np.array(v); v = v[np.isfinite(v)]
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def frac_cuadros(R, rol, var):
    v = [bool(np.any(r[rol]["h"][var])) for r in R if len(r[rol]["h"][var])]
    return float(np.mean(v)) if v else np.nan, len(v)


def frac_sitio(R, var, sitios=("antuco", "longavi"), roles=("pos", "ctrl")):
    v = []
    for r in R:
        for rol in roles:
            for s in sitios:
                d = r["s_" + rol][s]
                if d is not None and len(d[var]):
                    v.append(bool(np.any(d[var])))
    return (float(np.mean(v)) if v else np.nan), len(v)


def med(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return f"{np.median(x):+.2f}" if len(x) else "  nan"


def fisica(R, L):
    def sit(var, sitios=("antuco", "longavi")):
        v = [r["s_" + rol][s][var] for r in R for rol in ("pos", "ctrl") for s in sitios if r["s_" + rol][s] is not None]
        return np.concatenate(v) if v else np.array([])
    for nombre, f in (("huella pos", lambda v: pool(R, "h", v, "pos")), ("huella ctrl", lambda v: pool(R, "h", v, "ctrl")),
                      ("cumbres", lambda v: sit(v)), ("llano", lambda v: sit(v, ("llano",)))):
        btd, btdc = f("btd"), f("btdc")
        zs, b11 = f("zsfc"), f("b11")
        L.append(f"    {nombre:12s} zsfc GFS {np.nanmedian(zs) if len(zs) else np.nan:5.0f} m | BT11clr-BT11 {med(b11)} | BTD {med(btd)} | BTD_clr {med(btdc)} | BTD_clr-BTD {med(btdc - btd)} | "
                 f"BTD<0,7: {np.mean(btd < 0.7):.2f} | BTD<BTDclr-1: {np.mean(btd < btdc - 1):.2f} | T3 px: {np.mean(H.t3(btd, btdc)):.2f} (n {len(btd)})")


VARS = (("t3", "T3"), ("t3b", "T3+beta (no medible = borra)"), ("t3b_cons", "T3+beta (no medible = queda)"),
        ("t3_69", "T3+6 de 9"), ("t1", "Test 1 (BTD<-2)"))


def bloque(R, nombre, L, con_anillo):
    if not R:
        return {}
    L.append(f"\n==== {nombre}: {len(R)} pares, {len({r['dia'] for r in R})} dias, px huella {sum(len(r['pos']['h']['m']) for r in R)}")
    a = auc_m(R); lo, hi = boot(R)
    aan = auc_m(R, "an") if con_anillo else np.nan
    dias = sorted({r["dia"] for r in R}); pd = [(d, auc_m([r for r in R if r["dia"] == d])) for d in dias]
    dpos = sum(1 for _, x in pd if np.isfinite(x) and x > 0.5)
    L.append(f"  AUC margen huella={a:.3f} IC95dia=[{lo:.3f},{hi:.3f}] anillo={aan:.3f} h-an={a - aan:+.3f} dias>0,5={dpos}/{len(pd)}")
    L.append("  por dia: " + " ".join(f"{d}:{x:.2f}" for d, x in pd))
    res = {"auc": a, "lo": lo, "hi": hi, "aan": aan, "dpos": dpos, "ndias": len(pd)}
    for var, txt in VARS:
        fp, n = frac_cuadros(R, "pos", var); fc, _ = frac_cuadros(R, "ctrl", var)
        fs, ns = frac_sitio(R, var); fa, _ = frac_sitio(R, var, ("antuco",)); fl, _ = frac_sitio(R, var, ("longavi",))
        fll, _ = frac_sitio(R, var, ("llano",))
        fsp, _ = frac_sitio(R, var, roles=("pos",)); fsc, _ = frac_sitio(R, var, roles=("ctrl",))
        pxp = np.mean(pool(R, "h", var, "pos")); pxc = np.mean(pool(R, "h", var, "ctrl"))
        L.append(f"  {txt:30s} cuadros P_pos={fp:.3f} P_ctrl={fc:.3f} dif={fp - fc:+.3f} (n {n}) | px pos/ctrl {pxp:.3f}/{pxc:.3f}"
                 f" | P_cumbre={fs:.3f} (antuco {fa:.3f}, longavi {fl:.3f}; hora pos {fsp:.3f}, hora ctrl {fsc:.3f}; n {ns}) | llano {fll:.3f}")
        res[var] = {"pp": fp, "pc": fc, "ps": fs}
    if con_anillo:
        L.append(f"  anillo 2-6 px: T3 px pos/ctrl {np.mean(pool(R, 'an', 't3', 'pos')):.3f}/{np.mean(pool(R, 'an', 't3', 'ctrl')):.3f}")
    nb = np.mean(pool(R, "h", "b_nomed", "pos")); L.append(f"  T3 con beta no medible (huella pos, fraccion de px): {nb:.3f}")
    L.append("  fisica (medianas, K):"); fisica(R, L)
    return res


def veredicto(rA, rB):
    t = rA["t3"]
    c1 = (rA["auc"] >= 0.70 and rA["lo"] > 0.55 and (rA["auc"] - rA["aan"]) >= 0.10 and rA["dpos"] >= 2
          and (t["pp"] - t["pc"]) >= 0.30 and rB["auc"] >= 0.65 and (rB["t3"]["pp"] - rB["t3"]["pc"]) >= 0.20)
    if c1:
        return "SE SOSTIENE: el Test 3 separa la pluma"
    if t["pc"] >= 0.50 and t["ps"] >= 0.50:
        return "SE FALSA: el Test 3 mide el terreno (P_ctrl >= 0,50 y P_cumbre >= 0,50)"
    if t["pp"] < 0.30:
        return "SE FALSA: el Test 3 no ve la pluma (P_pos < 0,30)"
    return "NO CONCLUYENTE"


def estrato_separa(r):
    t = r["t3"]
    return (r["auc"] >= 0.70 and r["lo"] > 0.55 and (r["auc"] - r["aan"]) >= 0.10 and r["dpos"] >= 2
            and (t["pp"] - t["pc"]) >= 0.30 and r["ndias"] >= 3)


if __name__ == "__main__":
    RA = conjunto_A(); RB = conjunto_B(); EB = escenas_B()
    pickle.dump({"A": RA, "B": RB, "escB": EB}, open(os.path.join(H.OUT, "h12.pkl"), "wb"))
    L = []
    pe = H.pareo_e2()
    L.append(f"Conjunto A (H11): {len(RA)} pares | Conjunto B (E2, pareo nuevo): {len(RB)} pares; pareo "
             + str({e: sum(1 for q in pe if q['estado'] == e) for e in sorted({q['estado'] for q in pe})}))
    meta = json.load(open(os.path.join(H.OUT, "sitios_meta.json")))
    L.append("Sitios: " + "; ".join(f"{s}: {sum(m['n'] for m in meta if m['sitio'] == s)} px, ceniza VOLCAT excluida "
                                    f"{sum(m['ceniza'] for m in meta if m['sitio'] == s)}" for s in H.SITIOS)
             + " | mascara VOLCAT usada: " + str({f: sum(1 for m in meta if m['mascara'] == f) // 3 for f in sorted({m['mascara'] for m in meta})}))
    res = {}
    for cj, R, an in (("A", RA, True), ("B", RB, False)):
        for nombre, sel in (("AGRUPADO", lambda r: True), ("NOCHE (cenit >= 80)", lambda r: r["estrato"] == "N"),
                            ("DIA", lambda r: r["estrato"] == "D")):
            res[(cj, nombre)] = bloque([r for r in R if sel(r)], f"Conjunto {cj} {nombre}", L, an)
    L.append("\n==== Conjunto B entero (informativo): escenas con objeto T3 anclado (>= 2 px, uno a <= 10 km)")
    for tipo in ("pos", "neg", "manto"):
        for est in ("D", "N", None):
            v = [e for e in EB if e["tipo"] == tipo and (est is None or e["estrato"] == est)]
            if v:
                L.append(f"  {tipo:5s} {est or 'todos':5s} {sum(e['anc'] for e in v)} de {len(v)} = {np.mean([e['anc'] for e in v]):.3f}"
                         f" | fraccion media de px T3 a <= 10 km {np.mean([e['frac10'] for e in v]):.3f}")
    v = veredicto(res[("A", "AGRUPADO")], res[("B", "AGRUPADO")])
    L.append(f"\nVEREDICTO H12: {v}")
    for est in ("NOCHE (cenit >= 80)", "DIA"):
        r = res.get(("A", est))
        if r and estrato_separa(r):
            L.append(f"  Nota: en el conjunto A, estrato {est}, se cumple la regla 1 (a confirmar con criterio nuevo)")
    txt = "\n".join(L)
    open(sys.argv[1], "w", encoding="utf-8").write(txt)
    print(txt)
