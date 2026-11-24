r"""S21b prueba 2: los pulsos de la tarde del 28-10 (E10 17:38, E11 20:32, E12 21:49 UTC) en C02 y C05 de GOES-19,
como cambio entre el cuadro de antes del pulso y el de despues, alrededor del crater aparente (criterio §2).

Por que asi: de tarde no hay dias de control suficientes para comparar el mismo cuadro contra otros dias (son 3), y el
fondo de nieve y laderas cambia con el sol. Lo que si se puede preguntar es si entre el cuadro previo y el del pulso
aparece algo que sale del crater hacia algun lado, mas de lo que cambia esa misma corona entre dos cuadros igual de
separados en tardes despejadas sin pulso. Antuco y Longavi, en los mismos cuadros, separan la pluma de los cumulos de
cumbre, que de tarde tambien salen de la cumbre.

Uso: python -I s21b_prueba2.py   -> ../resultados/prueba2.json, prueba2.log, ../figuras/prueba2_*.png
"""
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s21b_comun as C  # noqa: E402

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(AQUI, "resultados")
FIG = os.path.join(AQUI, "figuras")
DIA = "2026-10-28"
PULSOS = [  # id, inicio REAV, R, P, informativos
    ("E10", "17:38", "17:20", "17:40", ["17:30"]),
    ("E11", "20:32", "20:20", "20:30", ["20:40"]),
    ("E12", "21:49", "21:30", "21:50", ["21:40", "22:00"]),
]
NULOS = ["2026-09-21", "2026-10-17", "2026-11-04"]
DECIDEN = ["C02", "C05"]
INFO = ["C06"]
ALFA = 0.025
R_MIN, R_MAX = 1.0, 10.0
SECT_W, SECT_PASO = 30.0, 15.0
FRANJA_ANCHO, FRANJA_R0, FRANJA_R1 = 1.2, 1.0, 8.0
E1_MIN = 0.80
T0_CUBO = datetime(2026, 9, 21)
LOG = []
_CACHE = {}


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


def dt(dia, hhmm):
    return datetime.strptime(f"{dia} {hhmm}", "%Y-%m-%d %H:%M")


def rho(t):
    if t not in _CACHE:
        _CACHE[t] = C.reflectancia(t)
    return _CACHE[t]


# ---------- despejado E1 (criterio §2.4) ----------
_E1 = np.load(os.path.join(C.TRABAJO, "desp_e1.npz"))["fr"]


def e1(t):
    d, s = (t.date() - T0_CUBO.date()).days, t.hour * 6 + t.minute // 10
    return float(_E1[d, s]) if 0 <= d < _E1.shape[0] else np.nan


def despejado(t):
    """E1 >= 0,80; si el cuadro da 0 (sin ACMF en el cubo) se acepta si los dos vecinos lo estan."""
    v = e1(t)
    if v >= E1_MIN:
        return True
    if v == 0.0:
        return e1(t - timedelta(minutes=10)) >= E1_MIN and e1(t + timedelta(minutes=10)) >= E1_MIN
    return False


# ---------- geometria de sectores ----------
_SECT = {}


def sectores(banda, sitio):
    """Mascaras del anillo y de los 24 sectores alrededor del crater aparente del sitio, en la grilla de la banda."""
    k = (banda, sitio)
    if k not in _SECT:
        g = C._GEO[banda]
        la, lo, h = C.CUMBRES[sitio]
        e, n = g.km_desde(la, lo, h)
        r = np.hypot(e, n)
        az = np.degrees(np.arctan2(e, n)) % 360
        anillo = (r >= R_MIN) & (r <= R_MAX)
        sec = []
        for c in np.arange(0, 360, SECT_PASO):
            d = np.abs((az - c + 180) % 360 - 180)
            sec.append(anillo & (d <= SECT_W / 2))
        _SECT[k] = (anillo, sec, e, n)
    return _SECT[k]


def T_de(dR, banda, sitio):
    """T = max_s |media(dR en s) - mediana(dR en el anillo)|; devuelve (T, centro del sector que salta, m_s - m)."""
    anillo, sec, _, _ = sectores(banda, sitio)
    m = np.nanmedian(dR[anillo])
    ms = np.array([np.nanmean(dR[s]) - m for s in sec])
    i = int(np.nanargmax(np.abs(ms)))
    return float(np.abs(ms[i])), float(i * SECT_PASO), float(ms[i])


_FR = {}


def franja(banda, az):
    if (banda, az) not in _FR:
        _FR[(banda, az)] = _franja(banda, az)
    return _FR[(banda, az)]


def _franja(banda, az):
    """f por pixel de una franja de 1,2 km de ancho, de 1 a 8 km del crater aparente de Chillan, hacia az."""
    g = C._GEO[banda]
    _, _, e, n = sectores(banda, "chillan")
    # submuestreo 10x10: offsets dentro del pixel en km, con el tamano local del pixel
    de = np.gradient(e, axis=1)
    dn = np.gradient(n, axis=0)
    u = (np.arange(10) + 0.5) / 10 - 0.5
    ux, uy = np.meshgrid(u, u)
    s, c = np.sin(np.radians(az)), np.cos(np.radians(az))
    f = np.zeros(g.shape)
    for a, b in zip(ux.ravel(), uy.ravel()):
        ee, nn = e + a * de, n + b * dn
        along = ee * s + nn * c
        cross = np.abs(ee * c - nn * s)
        f += ((along >= FRANJA_R0) & (along <= FRANJA_R1) & (cross <= FRANJA_ANCHO / 2))
    return f / 100.0


def con_luz(t):
    """El cuadro tiene reflectancia en al menos la mitad del anillo de Chillan en C02 y C05 (despues de la puesta
    del sol no hay: correccion de implementacion, informe §6)."""
    for b in DECIDEN:
        anillo = sectores(b, "chillan")[0]
        if np.mean(np.isfinite(rho(t)[b][anillo])) < 0.5:
            return False
    return True


def pares_nulos(R, P, ventana_min):
    d_frames = int((P - R).total_seconds() // 600)
    out = []
    for dia in NULOS:
        base = dt(dia, R.strftime("%H:%M"))
        for k in range(-ventana_min // 10, ventana_min // 10 + 1):
            F = base + timedelta(minutes=10 * k)
            G = F + timedelta(minutes=10 * d_frames)
            if not (despejado(F) and despejado(G)):
                continue
            if rho(F) is None or rho(G) is None:
                continue
            if not (con_luz(F) and con_luz(G)):
                continue
            out.append((F, G))
    return out


def pulso(pid, inicio, hr, hp, informativos):
    R, P = dt(DIA, hr), dt(DIA, hp)
    res = {"pulso": pid, "inicio_REAV": inicio, "R": hr, "P": hp,
           "hora_chillan_R": f"{C.hora_chillan(R):%H:%M:%S}", "hora_chillan_P": f"{C.hora_chillan(P):%H:%M:%S}",
           "E1_R": e1(R), "E1_P": e1(P)}
    for vent in (60, 90, 120):
        nul = pares_nulos(R, P, vent)
        if len(nul) >= 39:
            break
    res["ventana_nulo_min"] = vent
    res["n_nulo"] = len(nul)
    res["nulo_por_dia"] = {d: sum(1 for F, _ in nul if F.strftime("%Y-%m-%d") == d) for d in NULOS}
    log(f"== {pid} ({inicio}): R {hr} P {hp}; nulo {len(nul)} pares a +-{vent} min {res['nulo_por_dia']}")
    dR_ev = {b: rho(P)[b] - rho(R)[b] for b in DECIDEN + INFO}
    res["bandas"] = {}
    for b in DECIDEN + INFO:
        rb = {}
        for sitio in ("chillan", "antuco", "longavi"):
            T0, az, sgn = T_de(dR_ev[b], b, sitio)
            Tn = np.array([T_de(rho(G)[b] - rho(F)[b], b, sitio)[0] for F, G in nul])
            p = (1 + np.sum(Tn >= T0)) / (1 + len(Tn))
            rb[sitio] = {"T": round(T0, 4), "sector_az": az, "signo": round(sgn, 4), "p": round(float(p), 4),
                         "T_nulo_p50_p95_max": [round(float(x), 4) for x in np.percentile(Tn, [50, 95, 100])]}
        # poder (solo Chillan, bandas que deciden)
        if b in DECIDEN:
            Tn_ch = np.array([T_de(rho(G)[b] - rho(F)[b], b, "chillan")[0] for F, G in nul])
            hits, hits_m, hits_n = [], [], []
            for i, (F, G) in enumerate(nul):
                otros = np.delete(Tn_ch, i)
                for az in range(0, 360, 45):
                    f = franja(b, az)
                    Bg = rho(G)[b]
                    for factor, lista in ((1.0, hits), (0.5, hits_m)):
                        G_iny = Bg + factor * C.esperado(f, Bg, b)
                        Ti = T_de(G_iny - rho(F)[b], b, "chillan")[0]
                        lista.append((1 + np.sum(otros >= Ti)) / (1 + len(otros)) <= ALFA)
                        if factor == 1.0:
                            hits_n.append((1 + np.sum(Tn_ch >= Ti)) / (1 + len(Tn_ch)) <= ALFA)
                            res.setdefault("_Tiny", {}).setdefault(b, []).append(Ti)
            rb["poder"] = round(float(np.mean(hits)), 3)
            rb["poder_mitad"] = round(float(np.mean(hits_m)), 3)
            res.setdefault("_hits", {})[b] = (np.array(hits), np.array(hits_m), np.array(hits_n))
            rb["T_pintado_p5_p50_p95"] = [round(float(x), 4) for x in np.percentile(res["_Tiny"][b], [5, 50, 95])]
        rb["informativos"] = {}
        for hi in informativos:
            I = dt(DIA, hi)
            if rho(I) is None:
                continue
            d_frames = int((I - R).total_seconds() // 600)
            nul_i = []
            for dia in NULOS:
                base = dt(dia, hr)
                for k in range(-vent // 10, vent // 10 + 1):
                    F = base + timedelta(minutes=10 * k)
                    G = F + timedelta(minutes=10 * d_frames)
                    if (despejado(F) and despejado(G) and rho(F) is not None and rho(G) is not None
                            and con_luz(F) and con_luz(G)):
                        nul_i.append((F, G))
            T0, az, sgn = T_de(rho(I)[b] - rho(R)[b], b, "chillan")
            Tn = np.array([T_de(rho(G)[b] - rho(F)[b], b, "chillan")[0] for F, G in nul_i])
            rb["informativos"][hi] = {"T": round(T0, 4), "sector_az": az, "signo": round(sgn, 4),
                                      "p": round(float((1 + np.sum(Tn >= T0)) / (1 + len(Tn))), 4), "n": len(Tn)}
        res["bandas"][b] = rb
        ch = rb["chillan"]
        log(f"  {b}: Chillan T {ch['T']:.4f} az {ch['sector_az']:.0f} signo {ch['signo']:+.4f} p {ch['p']:.3f} | "
            f"Antuco p {rb['antuco']['p']:.3f} | Longavi p {rb['longavi']['p']:.3f}"
            + (f" | poder {rb['poder']} (mitad {rb['poder_mitad']})" if b in DECIDEN else "")
            + f" | info {rb['informativos']}")
    # regla §2.5
    sen, oro = False, False
    for b in DECIDEN:
        rb = res["bandas"][b]
        if rb["chillan"]["p"] <= ALFA:
            if rb["antuco"]["p"] <= ALFA or rb["longavi"]["p"] <= ALFA:
                oro = True
            else:
                sen = True
    res["veredicto"] = "SEÑAL" if sen else ("POSIBLE NUBE OROGRÁFICA" if oro else "SIN SEÑAL")
    # poder del pulso con la misma regla que decide: la franja pintada en las dos bandas a la vez, acierto si
    # alguna de las dos da p <= 0,025 (la cumbre de control no se pinta, asi que no puede anular el acierto)
    h = res.pop("_hits")
    res["poder_pulso"] = round(float(np.mean(h["C02"][0] | h["C05"][0])), 3)
    res["poder_pulso_mitad"] = round(float(np.mean(h["C02"][1] | h["C05"][1])), 3)
    res["poder_pulso_contra_todos"] = round(float(np.mean(h["C02"][2] | h["C05"][2])), 3)
    res.pop("_Tiny", None)
    res["con_poder"] = bool(res["poder_pulso"] >= 0.8)
    log(f"  -> {res['veredicto']} (poder del pulso {res['poder_pulso']}, mitad {res['poder_pulso_mitad']}, "
        f"contra los n pares {res['poder_pulso_contra_todos']})")
    return res


def descriptivo():
    """Anomalia de cada cuadro del 28-10 (16:00 a 22:30) contra la mediana de los dias de control a la misma hora,
    con el mismo estadistico de sectores (sin decision, criterio §2.7)."""
    filas = []
    t = dt(DIA, "16:00")
    while t <= dt(DIA, "22:30"):
        r = rho(t)
        ctl = [rho(dt(d, t.strftime("%H:%M"))) for d in NULOS]
        ctl = [c for c, d in zip(ctl, NULOS) if c is not None and despejado(dt(d, t.strftime("%H:%M")))]
        fila = {"hora": t.strftime("%H:%M"), "E1": e1(t), "n_control": len(ctl)}
        if r is not None and len(ctl) >= 2:
            for b in DECIDEN:
                A = r[b] - np.nanmedian(np.stack([c[b] for c in ctl]), 0)
                for sitio in ("chillan", "antuco"):
                    T0, az, sgn = T_de(A, b, sitio)
                    fila[f"{b}_{sitio}"] = [round(T0, 4), az, round(sgn, 4)]
        filas.append(fila)
        t += timedelta(minutes=10)
    return filas


def figura(res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 3, figsize=(10.5, 6.8))
    for j, (pid, _, hr, hp, _) in enumerate(PULSOS):
        R, P = dt(DIA, hr), dt(DIA, hp)
        for i, b in enumerate(DECIDEN):
            _, _, e, n = sectores(b, "chillan")
            dR = rho(P)[b] - rho(R)[b]
            sel = (np.abs(e) < 13) & (np.abs(n) < 13)
            rows, cols = np.nonzero(sel)
            r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
            ext = [e[r0, c0], e[r0, c1 - 1], n[r1 - 1, c0], n[r0, c0]]
            v = 0.08 if b == "C02" else 0.04
            im = ax[i, j].imshow(dR[r0:r1, c0:c1], cmap="RdBu_r", vmin=-v, vmax=v, extent=ext, aspect="equal")
            for rr in (R_MIN, R_MAX):
                th = np.linspace(0, 2 * np.pi, 200)
                ax[i, j].plot(rr * np.sin(th), rr * np.cos(th), "k:", lw=0.6)
            ch = res[j]["bandas"][b]["chillan"]
            a = np.radians(ch["sector_az"])
            ax[i, j].plot([R_MIN * np.sin(a), R_MAX * np.sin(a)], [R_MIN * np.cos(a), R_MAX * np.cos(a)], "k-", lw=0.8)
            ax[i, j].plot(0, 0, "^", mfc="none", mec="k", ms=7)
            ax[i, j].set_title(f"{pid} {b}: {hp} menos {hr}, p {ch['p']:.2f}", fontsize=9)
            ax[i, j].tick_params(labelsize=7)
            fig.colorbar(im, ax=ax[i, j], shrink=0.8)
    for a in ax[1]:
        a.set_xlabel("km este del cráter aparente", fontsize=8)
    for a in ax[:, 0]:
        a.set_ylabel("km norte", fontsize=8)
    fig.suptitle("S21b prueba 2: cambio de reflectancia entre el cuadro previo y el del pulso, 28-10 (línea: sector que "
                 "más cambia)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "prueba2_pulsos.png"), dpi=80)


def main():
    out = {"criterio": "criterio_2026-11-24.md", "dia": DIA, "nulos": NULOS, "pulsos": []}
    for p in PULSOS:
        out["pulsos"].append(pulso(*p))
    n_sen = sum(r["veredicto"] == "SEÑAL" for r in out["pulsos"])
    n_pod = sum(r["con_poder"] for r in out["pulsos"])
    if n_sen >= 2:
        ep = "CONFIRMA"
    elif n_sen == 0 and n_pod >= 2:
        ep = "DESCARTA"
    else:
        ep = "NO CONCLUYENTE"
    out["episodio"] = {"pulsos_con_senal": n_sen, "pulsos_con_poder": n_pod, "veredicto": ep}
    log(f"== EPISODIO 28-10: {ep} ({n_sen} de 3 con SEÑAL; {n_pod} con poder)")
    out["descriptivo"] = descriptivo()
    json.dump(out, open(os.path.join(RES, "prueba2.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    open(os.path.join(RES, "prueba2.log"), "w", encoding="utf8").write("\n".join(LOG) + "\n")
    figura(out["pulsos"])


if __name__ == "__main__":
    main()
