"""Paso 2 (H1 b): canales solares en la huella VOLCAT contra el mismo lugar en dias sin pluma.
Criterio: criterio_paso2_canales_solares_2026-11-18.md (carpeta de notas)."""
import os, sys, json, math
from datetime import timezone
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SOL = os.path.join(os.path.dirname(HERE), "solar")
sys.path.insert(0, HERE)
import fetch_solar as fsol  # noqa: E402
import paso3_objetos as p  # noqa: E402
sys.path.insert(0, fsol.DET)
import comun as C  # noqa: E402

H = np.load(os.path.join(fsol.DET, "volcat", "huellas.npz"))
RSUN_AU2 = (6.957e8 / 1.495978707e11) ** 2   # (radio solar / 1 UA)^2
TSUN = 5778.0


def escena(dt):
    f = os.path.join(SOL, f"{dt:%Y%m%d_%H%M}.npz")
    if not os.path.exists(f):
        return None
    z = np.load(f); m = json.loads(str(z["meta"]))
    r = z["rad02"].astype("float64") * m["C02"]["kappa0"]
    b = r.reshape(83, 4, 94, 4)
    r065 = np.nanmean(b, axis=(1, 3)); sd065 = np.nanstd(b, axis=(1, 3))
    c7, c14 = m["C07"], m["C14"]
    L14 = z["rad14"].astype("float64")
    with np.errstate(invalid="ignore", divide="ignore"):
        T14 = (c14["planck_fk2"] / np.log(c14["planck_fk1"] / L14 + 1) - c14["planck_bc1"]) / c14["planck_bc2"]
        Te = c7["planck_bc1"] + c7["planck_bc2"] * T14
        B7 = c7["planck_fk1"] / (np.exp(c7["planck_fk2"] / Te) - 1)
        Bsun = c7["planck_fk1"] / (np.exp(c7["planck_fk2"] / TSUN) - 1)
        d = c7.get("earth_sun_distance_anomaly_in_AU", 1.0)
        E7 = math.pi * Bsun * RSUN_AU2 / d ** 2
        th = p.sza(dt.replace(tzinfo=timezone.utc), C.VLAT, C.VLON)
        top = E7 * math.cos(math.radians(th)) / math.pi
        r39 = (z["rad07"].astype("float64") - B7) / (top - B7)
        ratio = np.where(r065 > 0.02, r39 / r065, np.nan)
    return {"T14": T14, "r065": r065, "sd065": sd065, "r39": r39, "ratio": ratio, "sza": th}


def auc(a, b):
    a = np.asarray(a); b = np.asarray(b)
    a = a[np.isfinite(a)]; b = b[np.isfinite(b)]
    if len(a) == 0 or len(b) == 0:
        return float("nan")
    from scipy.stats import rankdata
    r = rankdata(np.concatenate([a, b]))   # empates: rango promedio
    u = r[:len(a)].sum() - len(a) * (len(a) + 1) / 2
    return u / (len(a) * len(b))   # P(pos > control)


pos, _ = fsol.plan()
SEN = ("ratio", "r065", "sd065")
par = {k: ([], []) for k in SEN}; todo = {k: ([], []) for k in SEN}
pordia = {}
filas = []; r39p = []; r39c = []
for dt in pos:
    m = H[C.key(dt)]
    sp = escena(dt)
    if sp is None:
        continue
    t_pos = np.nanmedian(sp["T14"][m])
    cands = []
    for d in C.NEG_AJ_DIAS + C.NEG_PR_DIAS:
        sc = escena(dt.replace(day=d))
        if sc is not None:
            cands.append((abs(np.nanmedian(sc["T14"][m]) - t_pos), d, sc))
    if not cands:
        continue
    cands.sort(key=lambda x: x[0])
    dif, dctl, sc = cands[0]
    filas.append((dt, dctl, round(float(t_pos), 1), round(float(dif), 1), int(m.sum()), round(sp["sza"], 1)))
    pd_ = pordia.setdefault(dt.day, {k: ([], []) for k in SEN})
    r39p.extend(sp["r39"][m]); r39c.extend(sc["r39"][m])
    for k in SEN:
        par[k][0].extend(sp[k][m]); par[k][1].extend(sc[k][m])
        pd_[k][0].extend(sp[k][m]); pd_[k][1].extend(sc[k][m])
        todo[k][0].extend(sp[k][m])
        for _, _, s2 in cands:
            todo[k][1].extend(s2[k][m])

print("pares", len(filas), "de", len(pos), "positivos con sol alto")
for f in filas:
    print(f"  {f[0]:%m-%d %H:%M} control dia {f[1]:02d}  BT11 huella {f[2]} K  |dif| {f[3]} K  px {f[4]}  cenit {f[5]}")
print("\n== Control pareado (decide)")
sep = {}
for k in SEN:
    a = auc(*par[k]); sep[k] = abs(a - 0.5)
    print(f" {k:6s} AUC={a:.3f}  |AUC-0,5|={abs(a-0.5):.3f}  mediana pos {np.nanmedian(par[k][0]):.3f}  control {np.nanmedian(par[k][1]):.3f}  n={np.isfinite(par[k][0]).sum()}/{np.isfinite(par[k][1]).sum()}")
v = "APOYA" if max(sep.values()) >= 0.20 else ("FALSA" if max(sep.values()) < 0.10 else "NO CONCLUYENTE")
print(" veredicto segun criterio:", v)
print("\n== Sensibilidad: los 10 dias negativos juntos")
for k in SEN:
    a = auc(*todo[k]); print(f" {k:6s} AUC={a:.3f}  mediana pos {np.nanmedian(todo[k][0]):.3f}  control {np.nanmedian(todo[k][1]):.3f}")
print("\n== Por dia (control pareado)")
for d, dd in sorted(pordia.items()):
    print(f" dia {d:02d}: " + "  ".join(f"{k} {auc(*dd[k]):.2f}" for k in SEN) + f"  (px {np.isfinite(dd['r065'][0]).sum()})")
fr = lambda x: np.mean(np.asarray(x)[np.isfinite(x)] > 0.5)
print("\nfraccion ratio > 0,5: positivos %.2f  control pareado %.2f  todos los controles %.2f"
      % (fr(par["ratio"][0]), fr(par["ratio"][1]), fr(todo["ratio"][1])))
print("(r39 se informa, no decide) mediana pos %.3f  control pareado %.3f  AUC %.3f"
      % (np.nanmedian(r39p), np.nanmedian(r39c), auc(r39p, r39c)))
