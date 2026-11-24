r"""S21b prueba 1: la franja de pluma de Landsat 8 del 25-10 14:34 UTC, puesta con paralaje en la grilla de C02, C05 y
C06 de GOES-19, contra los mismos pixeles en los dias despejados anteriores al 24-10 (criterio §1).

Por que asi: la huella viene de un sensor independiente, asi que la unica pregunta es si la reflectancia de GOES en
esos pixeles se mueve como predice la pluma que Landsat vio. S mide cuanto de lo esperado aparece (1 = todo, 0 =
nada); el nulo corre la huella a otros lugares con fondo comparable; el ensayo en seco hace de evento a cada dia base.

Uso: python -I s21b_prueba1.py   -> ../resultados/prueba1.json, prueba1.log, ../figuras/prueba1_*.png
"""
import json
import os
import sys
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s21b_comun as C  # noqa: E402

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(AQUI, "resultados")
FIG = os.path.join(AQUI, "figuras")
EVENTO = "2026-10-25"
BASE = ["2026-09-27", "2026-10-15", "2026-10-16", "2026-10-17"]
BASE_SENS = ["2026-11-02", "2026-11-04"]
BANDAS = ["C02", "C05", "C06"]
ALFA = 0.05 / 3
MIN_CORR = 200
NUBE_RHO05, NUBE_FRAC, NUBE_KM = 0.30, 0.05, 15.0
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


def cuadro(dia, hhmm):
    return C.reflectancia(datetime.strptime(f"{dia} {hhmm}", "%Y-%m-%d %H:%M"))


def nublado(rho, geo):
    """Regla del criterio §1.1: mas del 5 % de los pixeles C05 a 15 km del crater con rho05 > 0,30."""
    e, n = geo["C05"].km_desde(C.CRATER[0], C.CRATER[1], 0.0)
    cerca = np.hypot(e, n) <= NUBE_KM
    v = rho["C05"][cerca]
    return float(np.nanmean(v > NUBE_RHO05)), bool(np.nanmean(v > NUBE_RHO05) > NUBE_FRAC)


def S_de(P, A):
    m = np.isfinite(A) & np.isfinite(P) & (P != 0)
    if m.sum() == 0:
        return np.nan, 0.0
    return float(np.sum(P[m] * A[m]) / np.sum(P[m] ** 2)), float(np.sum(P[m] ** 2))


def corrimientos(f, A, B, banda):
    """S en todos los corrimientos validos de la huella (criterio §1.4). Devuelve (S_real, array S_nulo)."""
    ny, nx = f.shape
    rr, cc = np.nonzero(f > 0)
    fv = f[rr, cc]
    P0 = C.esperado(fv, B[rr, cc], banda)
    S0, E0 = S_de(P0, A[rr, cc])
    reales = set(zip(rr.tolist(), cc.tolist()))
    out = []
    for dr in range(-rr.min(), ny - rr.max()):
        for dc in range(-cc.min(), nx - cc.max()):
            if dr == 0 and dc == 0:
                continue
            r2, c2 = rr + dr, cc + dc
            if any((a, b) in reales for a, b in zip(r2.tolist(), c2.tolist())):
                continue
            Bv, Av = B[r2, c2], A[r2, c2]
            if not (np.isfinite(Bv).all() and np.isfinite(Av).all()):
                continue
            P = C.esperado(fv, Bv, banda)
            S, E = S_de(P, Av)
            if 0.5 * E0 <= E <= 2.0 * E0:
                out.append(S)
    return S0, np.array(out)


def p_de(S0, nulo):
    return float(np.mean(nulo >= S0)) if len(nulo) else np.nan


def medir(rho_ev, rhos_base, f, banda, iny=None):
    stack = np.stack([r[banda] for r in rhos_base])
    B = np.nanmedian(stack, 0)
    A = rho_ev[banda] - B
    if iny is not None:
        A = A + iny * C.esperado(f, B, banda)
    S0, nulo = corrimientos(f, A, B, banda)
    return S0, nulo, A, B


def veredicto(S0, p, n):
    if n < MIN_CORR:
        return "SIN NULO"
    return "SEÑAL" if (S0 > 0 and p <= ALFA) else "SIN SEÑAL"


def prueba(hhmm, H, base, etiqueta, completo=True):
    rho_ev = cuadro(EVENTO, hhmm)
    geo = C._GEO
    m = np.load(C.MASCARA)
    rb = {}
    for d in base:
        r = cuadro(d, hhmm)
        if r is None:
            log(f"  base {d} {hhmm}: sin archivo")
            continue
        fr, nub = nublado(r, geo)
        log(f"  base {d} {hhmm}: fraccion rho05>0,30 a 15 km = {fr:.3f} -> {'DESCARTADO' if nub else 'ok'}")
        if not nub:
            rb[d] = r
    fr, nub = nublado(rho_ev, geo)
    log(f"  evento {EVENTO} {hhmm}: fraccion rho05>0,30 a 15 km = {fr:.3f}")
    res = {"cuadro": hhmm, "H_m": H, "dias_base": list(rb), "bandas": {}}
    if len(rb) < 3:
        res["veredicto"] = "INVÁLIDA (menos de 3 días base)"
        return res
    for b in BANDAS:
        f = geo[b].fraccion(m["pluma"], H)
        S0, nulo, A, B = medir(rho_ev, list(rb.values()), f, b)
        p = p_de(S0, nulo)
        rr, cc = np.unravel_index(np.argmax(f), f.shape)
        st = np.stack([r[b] for r in rb.values()])
        Pmap = C.esperado(f, B, b)
        d = {"S": round(S0, 3), "p": round(p, 4), "corrimientos": int(len(nulo)),
             "S_nulo_p5_p50_p95": [round(float(x), 3) for x in np.nanpercentile(nulo, [5, 50, 95])] if len(nulo) else None,
             "veredicto": veredicto(S0, p, len(nulo)),
             "pixeles_huella": int((f > 0).sum()), "f_max": round(float(f.max()), 3),
             "pixel_mayor_f": {"fila": int(rr), "col": int(cc), "f": round(float(f[rr, cc]), 3),
                               "rho_evento": round(float(rho_ev[b][rr, cc]), 4),
                               "rho_base": [round(float(x), 4) for x in st[:, rr, cc]],
                               "A": round(float(A[rr, cc]), 4), "esperado_P": round(float(Pmap[rr, cc]), 4)},
             "suma_fA": round(float(np.nansum(f * A)), 4), "suma_fP": round(float(np.nansum(f * Pmap)), 4)}
        if completo:
            # ensayo en seco y poder: cada dia base hace de evento contra los otros
            seco, pod, pod_med = [], [], []
            for dd, r in rb.items():
                otros = [x for k, x in rb.items() if k != dd]
                S1, n1, _, _ = medir(r, otros, f, b)
                seco.append(p_de(S1, n1) <= ALFA and S1 > 0)
                S2, n2, _, _ = medir(r, otros, f, b, iny=1.0)
                pod.append(p_de(S2, n2) <= ALFA and S2 > 0)
                S3, n3, _, _ = medir(r, otros, f, b, iny=0.5)
                pod_med.append(p_de(S3, n3) <= ALFA and S3 > 0)
            d["falsas_alarmas_seco"] = [int(sum(seco)), len(seco)]
            d["poder"] = round(float(np.mean(pod)), 2)
            d["poder_mitad"] = round(float(np.mean(pod_med)), 2)
            if sum(seco) >= 2:
                d["veredicto"] = "INVÁLIDA (falsas alarmas en seco)"
            elif d["veredicto"] == "SIN SEÑAL" and d["poder"] < 0.5:
                d["veredicto"] = "SIN PODER"
        res["bandas"][b] = d
        log(f"  [{etiqueta}] {b}: S {S0:+.3f} p {p:.4f} (n {len(nulo)}) -> {d['veredicto']}"
            + (f"; seco {d['falsas_alarmas_seco']} poder {d['poder']} (mitad {d['poder_mitad']})" if completo else ""))
        if completo and hhmm == "14:30" and etiqueta == "decide":
            np.savez_compressed(os.path.join(C.TRABAJO, f"prueba1_{b}.npz"), A=A, B=B, f=f, P=Pmap, nulo=nulo,
                                lat=geo[b].lat, lon=geo[b].lon)
    return res


def figura():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 3, figsize=(10.5, 6.6))
    for j, b in enumerate(BANDAS):
        z = np.load(os.path.join(C.TRABAJO, f"prueba1_{b}.npz"))
        e, n = C._GEO[b].km_desde(C.CRATER[0], C.CRATER[1], 0.0)
        sel = (np.abs(e) < 14) & (n > -18) & (n < 8)
        rows, cols = np.nonzero(sel)
        r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
        ext = [e[r0, c0], e[r0, c1 - 1], n[r1 - 1, c0], n[r0, c0]]
        v = 0.15 if b == "C02" else 0.06
        a0 = ax[0, j].imshow(z["A"][r0:r1, c0:c1], cmap="RdBu_r", vmin=-v, vmax=v, extent=ext, aspect="equal")
        ax[0, j].contour(e[r0:r1, c0:c1], n[r0:r1, c0:c1], z["f"][r0:r1, c0:c1], [0.05], colors="k", linewidths=0.8)
        ax[0, j].set_title(f"{b}: anomalía 25-10 14:30", fontsize=9)
        fig.colorbar(a0, ax=ax[0, j], shrink=0.8)
        a1 = ax[1, j].imshow(z["P"][r0:r1, c0:c1], cmap="RdBu_r", vmin=-v, vmax=v, extent=ext, aspect="equal")
        ax[1, j].set_title(f"{b}: esperado por el modelo", fontsize=9)
        fig.colorbar(a1, ax=ax[1, j], shrink=0.8)
        for a in ax[:, j]:
            a.plot(0, 0, "^", mfc="none", mec="k", ms=7)
            a.set_xlabel("km este del cráter (grilla ABI, al elipsoide)", fontsize=8)
            a.tick_params(labelsize=7)
    ax[0, 0].set_ylabel("km norte", fontsize=8)
    ax[1, 0].set_ylabel("km norte", fontsize=8)
    fig.suptitle("S21b prueba 1: reflectancia, 25-10 menos mediana de 4 días despejados (contorno: huella f > 0,05)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "prueba1_mapas.png"), dpi=80)


def main():
    m = np.load(C.MASCARA)
    H = float(m["H"])
    out = {"criterio": "criterio_2026-11-24.md", "evento": EVENTO, "H_m": H}
    log("== decide: 14:30, H de S20b, base antes del 24-10")
    out["decide"] = prueba("14:30", H, BASE, "decide")
    log("== informativo: 14:20 y 14:40")
    out["14:20"] = prueba("14:20", H, BASE, "14:20", completo=False)
    out["14:40"] = prueba("14:40", H, BASE, "14:40", completo=False)
    log("== informativo: H - 1 km y H + 1 km (14:30)")
    out["H-1km"] = prueba("14:30", H - 1000, BASE, "H-1km", completo=False)
    out["H+1km"] = prueba("14:30", H + 1000, BASE, "H+1km", completo=False)
    log("== informativo: base con 02-11 y 04-11 (14:30)")
    out["base_ampliada"] = prueba("14:30", H, BASE + BASE_SENS, "base+nov", completo=False)
    json.dump(out, open(os.path.join(RES, "prueba1.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    open(os.path.join(RES, "prueba1.log"), "w", encoding="utf8").write("\n".join(LOG) + "\n")
    figura()


if __name__ == "__main__":
    main()
