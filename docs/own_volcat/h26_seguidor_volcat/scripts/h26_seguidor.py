r"""H26 (S19b): copia de la decisión de VOLCAT (objeto anclado a cráter caliente + criterio temporal + seguimiento)
y su costo. Criterio: docs/own_volcat/h26_seguidor_volcat/criterio_2026-11-23.md (commit 95d6171, antes de medir).

ESTO COPIA UNA REGLA, NO MIDE CENIZA: un acierto dice que reproducimos la decisión de VOLCAT, no que haya ceniza.

Entradas (sólo lectura): cachés L1b de H17 (h17_comun.indice), línea base de H17 (h17_pluma.base), calor de H17
(D:\goes_cache\h17\calor.pkl), huella event_idx ubicada por la etapa 3 (D:, licencia restringida, no va al repo),
clases del PNG de H9 (calor_rayos/resultados/frames_calor.csv).
Escribe (repo): resultados/h26_por_cuadro.csv (sin posiciones de huella), resultados/h26_resumen.json,
resultados/h26_corrida.log.
Uso: python -I h26_seguidor.py
"""
import os
import sys
import glob
import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy import ndimage

AQUI = os.path.dirname(os.path.abspath(__file__))
OWN = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(OWN, "h17_regla_propia", "scripts"))
import h17_comun as K  # noqa: E402
import h17_pluma as P17  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RES = os.path.join(os.path.dirname(AQUI), "resultados")
os.makedirs(RES, exist_ok=True)
FRAMES_H9 = os.path.join(OWN, "calor_rayos", "resultados", "frames_calor.csv")
SITIOS = ("chillan", "antuco", "longavi")
GAP = timedelta(minutes=20)
K3 = np.ones((3, 3), bool)
K5 = np.ones((5, 5), bool)
OCHO = np.ones((3, 3), int)
SEMILLA = 26
LOG = []


def p(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print(s, flush=True)


# ---------------------------------------------------------------- geometría por sitio
GEO = {}
for s in SITIOS:
    d = K.dist_cumbre(s)
    yc, xc = np.unravel_index(np.argmin(d), d.shape)
    GEO[s] = dict(dist=d, Z=d <= 6.0, DOM=d <= 30.0, yc=int(yc), xc=int(xc))

# orientación de la grilla: necesaria para inyectar hacia el ESE y para reflejar la huella
SGN_S = 1 if K.LAT[-1, K.LAT.shape[1] // 2] < K.LAT[0, K.LAT.shape[1] // 2] else -1   # +y es hacia el sur
SGN_E = 1 if K.LON[K.LON.shape[0] // 2, -1] > K.LON[K.LON.shape[0] // 2, 0] else -1   # +x es hacia el este


def candidatos(var, d11, dd):
    with np.errstate(invalid="ignore"):
        if var == "R2":
            return (np.abs(d11) >= 1.0) | (dd <= -0.5)
        return (d11 <= -1.0) & (dd <= -0.5)


def objetos(cand, s):
    g = GEO[s]
    lab, n = ndimage.label(cand & g["DOM"], structure=OCHO)
    out = []
    for j in range(1, n + 1):
        m = lab == j
        out.append((m, int(m.sum()), bool((m & g["Z"]).any())))
    return out


class Seguidor:
    """Copia de la decisión (criterio §3, pasos 4 a 6)."""

    def __init__(self):
        self.t_prev = None
        self.anc_prev = None
        self.pista = None

    def paso(self, t, obs, gate):
        vacio = np.zeros(K.LAT.shape, bool)
        if self.t_prev is None or t - self.t_prev > GAP:
            self.anc_prev, self.pista = vacio, vacio
        out = vacio.copy()
        if self.pista.any():
            zona = ndimage.binary_dilation(self.pista, K5)
            for m, n, _ in obs:
                if n <= 200 and (m & zona).any():
                    out |= m
        anc_t = vacio.copy()
        for m, n, a in obs:
            if a and 1 <= n <= 70:
                anc_t |= m
        if gate and self.anc_prev.any():
            zona = ndimage.binary_dilation(self.anc_prev, K3)
            for m, n, a in obs:
                if a and 1 <= n <= 70 and (m & zona).any():
                    out |= m
        self.t_prev, self.anc_prev, self.pista = t, anc_t, out
        return out


def iou(mask, hu):
    """(IoU tolerante a 1 px, IoU exacto, recuperados, |huella|)."""
    if not hu.any() and not mask.any():
        return np.nan, np.nan, 0, 0
    rec = int((hu & ndimage.binary_dilation(mask, K3)).sum())
    cor = int((mask & ndimage.binary_dilation(hu, K3)).sum())
    tol = (rec + cor) / (hu.sum() + mask.sum())
    ex = (hu & mask).sum() / (hu | mask).sum()
    return float(tol), float(ex), rec, int(hu.sum())


def reflejar(hu, s):
    g = GEO[s]
    out = np.zeros_like(hu)
    ys, xs = np.nonzero(hu)
    ry, rx = 2 * g["yc"] - ys, 2 * g["xc"] - xs
    ok = (ry >= 0) & (ry < hu.shape[0]) & (rx >= 0) & (rx < hu.shape[1])
    out[ry[ok], rx[ok]] = True
    return out


def pluma_sintetica(s):
    """6 píxeles 8-conexos desde el píxel de la cumbre corrida hacia el ESE (rumbo 112,5°)."""
    g = GEO[s]
    m = np.zeros(K.LAT.shape, bool)
    for k in range(6):
        m[g["yc"] + SGN_S * int(round(k * np.tan(np.radians(22.5)))), g["xc"] + SGN_E * k] = True
    assert ndimage.label(m, structure=OCHO)[1] == 1
    return m


def huellas():
    z = np.load(K.E3INV)
    h = {}
    for kk in z.files:
        c, v = kk.split("__")
        h.setdefault(c, {})[v] = z[kk]
    return h


def compuerta(cal, s, T):
    """Algún cuadro nocturno con vrp_ctx >= 10 MW en las 24 h previas (incluido t)."""
    x = cal[(cal.sitio == s) & (cal.sza >= 90) & (cal.vrp_ctx >= 10.0)].dt.sort_values().values
    out = []
    for t in T:
        t64 = np.datetime64(t)
        i = np.searchsorted(x, t64, side="right")
        out.append(bool(i > 0 and x[i - 1] >= t64 - np.timedelta64(24, "h")))
    return np.array(out)


def main():
    p("H26 seguidor. Generado", datetime.now().strftime("%Y-%m-%d %H:%M"), "| criterio commit 95d6171")
    idx = K.indice()
    cs, T, b11, btd = P17.cargar_ir(idx)
    p("cuadros con C14+C15:", len(cs), "|", cs[0], "a", cs[-1])

    # línea base de H17 para cada cuadro
    D11 = np.full_like(b11, np.nan)
    DD = np.full_like(btd, np.nan)
    con_base = np.zeros(len(cs), bool)
    for i in range(len(cs)):
        _, B11, Bd = P17.base(i, T, b11, btd)
        if B11 is not None:
            D11[i], DD[i], con_base[i] = b11[i] - B11, btd[i] - Bd, True
    p("cuadros con base:", int(con_base.sum()))

    # I3: rango de BT11
    fin = b11[np.isfinite(b11)]
    I3 = bool(fin.min() >= 180 and fin.max() <= 330)
    p(f"I3 rango BT11 {fin.min():.1f} a {fin.max():.1f} K -> {'pasa' if I3 else 'FALLA'}")

    cal = pd.read_pickle(os.path.join(K.H17, "calor.pkl"))
    GATE = {s: compuerta(cal, s, T) for s in SITIOS}
    sza = cal[cal.sitio == "chillan"].set_index("cuadro").sza
    periodo = np.array([("noche" if z >= 90 else "dia" if z < 80 else "crepusculo") if np.isfinite(z) else "?"
                        for z in (sza.get(c, np.nan) for c in cs)])
    for s in SITIOS:
        p(f"compuerta encendida {s}: {GATE[s][con_base].mean():.3f} de los cuadros con base")

    # días con VOLCAT
    h9 = pd.read_csv(FRAMES_H9, parse_dates=["dt"])
    h9["f"] = h9.dt.dt.date
    evs = {datetime.strptime(os.path.basename(f).split("_s")[1][:12], "%Y%m%d%H%M")
           for f in glob.glob(os.path.join(K.EVDIR, "*.nc"))}
    dias_v = set(h9[(h9.clase == "P") | (h9.n_anc > 0)].f) | {e.date() for e in evs}
    fechas = np.array([t.date() for t in T])
    dias_ir = sorted(set(fechas))
    dias_sin = [d for d in dias_ir if d not in dias_v]
    p("días con VOLCAT:", len(dias_v), sorted(str(d) for d in dias_v))
    p("días sin VOLCAT con IR:", len(dias_sin), [str(d) for d in dias_sin])
    claseP = set(h9[h9.clase == "P"].dt)

    HU = huellas()
    clave = {c: i for i, c in enumerate(cs)}
    ev_cs = sorted(HU)
    I1 = all(c in clave and con_base[clave[c]] for c in ev_cs) and len(ev_cs) == 60
    p("I1 cuadros de evento:", len(ev_cs), "con C14+C15 y base:", sum(c in clave and con_base[clave[c]] for c in ev_cs),
      "->", "pasa" if I1 else "FALLA")
    difs = []
    hmask = {}
    for c in ev_cs:
        wy, wx = HU[c]["wy"].astype(int), HU[c]["wx"].astype(int)
        m = np.zeros(K.LAT.shape, bool)
        m[wy, wx] = True
        hmask[c] = m
        if c in clave:
            difs += list(np.abs(b11[clave[c]][wy, wx] - HU[c]["bt11"].astype(float)))
    difs = np.array(difs)
    I2 = bool(np.nanmedian(difs) <= 0.5)
    p(f"I2 |BT11 nuestra - BT11 evento| en la huella: mediana {np.nanmedian(difs):.3f} K, p90 "
      f"{np.nanpercentile(difs, 90):.3f} K (n {len(difs)}) -> {'pasa' if I2 else 'FALLA'}")

    # ------------------------------------------------------------ corrida del seguidor
    variantes = {"R1": ("R1", True), "R1_sin_compuerta": ("R1", False), "R2": ("R2", True)}
    filas = []
    salida = {}
    for s in SITIOS:
        for v, (cv, usa_gate) in variantes.items():
            seg = Seguidor()
            for i, c in enumerate(cs):
                if not con_base[i]:
                    continue
                obs = objetos(candidatos(cv, D11[i], DD[i]), s)
                gate = bool(GATE[s][i]) if usa_gate else True
                m = seg.paso(T[i], obs, gate)
                salida[(s, v, c)] = m
        for i, c in enumerate(cs):    # R0, nulo geométrico
            if con_base[i]:
                salida[(s, "R0", c)] = GEO[s]["Z"].copy() if GATE[s][i] else np.zeros(K.LAT.shape, bool)

    VARS = list(variantes) + ["R0"]
    for s in SITIOS:
        for v in VARS:
            for i, c in enumerate(cs):
                if not con_base[i]:
                    continue
                m = salida[(s, v, c)]
                f = dict(cuadro=c, sitio=s, variante=v, periodo=periodo[i], gate=bool(GATE[s][i]),
                         dispara=bool(m.any()), npx=int(m.sum()), dia_volcat=fechas[i] in dias_v,
                         claseP=T[i] in claseP, evento=c in HU)
                if s == "chillan" and c in HU:
                    tol, ex, rec, nh = iou(m, hmask[c])
                    tolr, _, _, _ = iou(m, reflejar(hmask[c], s))
                    f.update(iou_tol=tol, iou_ex=ex, rec=rec, n_huella=nh, iou_reflejada=tolr)
                filas.append(f)
    df = pd.DataFrame(filas)
    df.to_csv(os.path.join(RES, "h26_por_cuadro.csv"), index=False, float_format="%.4f")

    # ------------------------------------------------------------ control positivo
    rng = np.random.default_rng(SEMILLA)
    sint = pluma_sintetica("chillan")
    ini = []
    for i in range(len(cs) - 3):
        if fechas[i] in dias_sin and all(con_base[i + k] for k in range(4)) and \
                all(T[i + k + 1] - T[i + k] == timedelta(minutes=10) for k in range(3)) and \
                all(GATE["chillan"][i + k] for k in range(4)):
            ini.append(i)
    p("\ncontrol positivo: tramos elegibles (4 cuadros de 10 min, día sin VOLCAT, base y compuerta):", len(ini))
    elegidos = rng.choice(ini, size=min(20, len(ini)), replace=False) if ini else []
    pc = []
    for i0 in sorted(elegidos):
        seg = Seguidor()
        ok, ious = True, []
        for k in range(4):
            i = i0 + k
            d11 = D11[i].copy()
            dd = DD[i].copy()
            d11[sint] -= 3.0
            dd[sint] -= 1.5
            m = seg.paso(T[i], objetos(candidatos("R1", d11, dd), "chillan"), bool(GATE["chillan"][i]))
            if k >= 2:
                tol = iou(m, sint)[0]
                ious.append(tol)
                ok &= bool(m.any()) and tol >= 0.5
        pc.append(dict(inicio=cs[i0], pasa=ok, iou3=ious[0], iou4=ious[1]))
    pcd = pd.DataFrame(pc)
    frac_pc = float(pcd.pasa.mean()) if len(pcd) else np.nan
    CP = bool(len(pcd) >= 20 and frac_pc >= 0.90)
    p(f"control positivo: pasa {int(pcd.pasa.sum()) if len(pcd) else 0} de {len(pcd)} tramos ({frac_pc:.2f}); IoU "
      f"mediano cuadros 3-4 {np.nanmedian(pcd[['iou3', 'iou4']].values) if len(pcd) else np.nan:.3f} -> "
      f"{'pasa' if CP else 'FALLA'}")

    # ------------------------------------------------------------ métricas
    res = dict(criterio="95d6171", n_cuadros=len(cs), n_con_base=int(con_base.sum()), I1=I1, I2=I2, I3=I3,
               I2_mediana_K=float(np.nanmedian(difs)), control_positivo=dict(n=len(pcd), frac=frac_pc, pasa=CP),
               dias_volcat=sorted(str(d) for d in dias_v), dias_sin_volcat=[str(d) for d in dias_sin], var={})
    p("\n== Concordancia con event_idx (Chillán, 60 cuadros) ==")
    for v in VARS:
        e = df[(df.sitio == "chillan") & (df.variante == v) & df.evento]
        r = dict(iou_tol_mediana=float(e.iou_tol.median()), iou_ex_mediana=float(e.iou_ex.median()),
                 iou_reflejada_mediana=float(e.iou_reflejada.median()),
                 frac_recuperada=float(e.rec.sum() / e.n_huella.sum()), dispara_eventos=float(e.dispara.mean()),
                 n_eventos=len(e))
        pP = df[(df.sitio == "chillan") & (df.variante == v) & df.claseP]
        r["dispara_claseP"] = float(pP.dispara.mean()) if len(pP) else np.nan
        r["n_claseP"] = len(pP)
        n = df[(df.sitio == "chillan") & (df.variante == v) & ~df.dia_volcat]
        r["FA_chillan_cuadros"] = float(n.dispara.mean())
        r["n_FA_chillan"] = len(n)
        r["FA_chillan_dias"] = float(n.groupby(n.cuadro.str[:8]).dispara.any().mean())
        for s in ("antuco", "longavi"):
            x = df[(df.sitio == s) & (df.variante == v)]
            r[f"FA_{s}"] = float(x.dispara.mean())
            r[f"FA_{s}_dias"] = float(x.groupby(x.cuadro.str[:8]).dispara.any().mean())
        r["por_periodo"] = {}
        for per in ("dia", "crepusculo", "noche"):
            a = e[e.periodo == per]
            b = n[n.periodo == per]
            r["por_periodo"][per] = dict(n_ev=len(a), iou_tol=float(a.iou_tol.median()) if len(a) else None,
                                         dispara_ev=float(a.dispara.mean()) if len(a) else None,
                                         n_fa=len(b), FA=float(b.dispara.mean()) if len(b) else None)
        res["var"][v] = r
        p(f"{v:17s} IoU tol med {r['iou_tol_mediana']:.3f} (exacto {r['iou_ex_mediana']:.3f}, reflejada "
          f"{r['iou_reflejada_mediana']:.3f}) | recuperada {r['frac_recuperada']:.3f} | dispara en eventos "
          f"{r['dispara_eventos']:.3f}, en clase P {r['dispara_claseP']:.3f} (n {r['n_claseP']}) | FA Chillán "
          f"{r['FA_chillan_cuadros']:.3f} (n {r['n_FA_chillan']}, días {r['FA_chillan_dias']:.2f}) | FA Antuco "
          f"{r['FA_antuco']:.3f} Longaví {r['FA_longavi']:.3f}")
        for per, q in r["por_periodo"].items():
            p(f"      {per:11s} eventos {q['n_ev']:2d} IoU {q['iou_tol']} dispara {q['dispara_ev']} | FA n {q['n_fa']} "
              f"{q['FA']}")

    # nulo no degenerado (I3, segunda parte)
    viva = bool(df[(df.sitio != "chillan") & (df.variante == "R1_sin_compuerta")].dispara.any())
    p("seguidor vivo en controles (dispara alguna vez en Antuco o Longaví sin compuerta):", viva)
    res["seguidor_vivo_controles"] = viva

    # ------------------------------------------------------------ veredicto (R1)
    r1, r0 = res["var"]["R1"], res["var"]["R0"]
    fa_ctrl = max(res["var"]["R1_sin_compuerta"]["FA_antuco"], res["var"]["R1_sin_compuerta"]["FA_longavi"])
    conc = (r1["iou_tol_mediana"] >= 0.30 and r1["frac_recuperada"] >= 0.50 and
            r1["iou_tol_mediana"] > r0["iou_tol_mediana"] and r1["iou_tol_mediana"] > r1["iou_reflejada_mediana"])
    if not (I1 and I2 and I3 and viva):
        ver = "SIN DATO"
    elif not CP:
        ver = "SIN PODER"
    elif not conc:
        ver = "NO COPIA"
    elif r1["FA_chillan_cuadros"] <= 0.05 and fa_ctrl <= 0.05:
        ver = "COPIA"
    else:
        ver = "COPIA CARA"
    res["FA_controles_decide"] = fa_ctrl
    res["veredicto"] = ver
    p(f"\nFA controles (R1 sin compuerta, el peor de Antuco y Longaví): {fa_ctrl:.3f}")
    p("VEREDICTO H26 (R1):", ver)

    # por evento (informativo)
    p("\n== Por evento (R1, informativo) ==")
    e = df[(df.sitio == "chillan") & (df.variante == "R1") & df.evento].copy()
    e["ev"] = e.cuadro.map(lambda c: {"20261113": "13-11 VCB", "20261118": "18-11"}.get(
        c[:8], "14-11 12:40" if c < "20261114_1600" else "14-11 16:30"))
    for g, x in e.groupby("ev"):
        p(f"{g:12s} cuadros {len(x):2d} dispara {x.dispara.mean():.2f} IoU tol med {x.iou_tol.median():.3f} "
          f"recuperada {x.rec.sum()}/{x.n_huella.sum()}")
    json.dump(res, open(os.path.join(RES, "h26_resumen.json"), "w", encoding="utf-8"), indent=1, default=str,
              ensure_ascii=False)
    open(os.path.join(RES, "h26_corrida.log"), "w", encoding="utf-8").write("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main()
