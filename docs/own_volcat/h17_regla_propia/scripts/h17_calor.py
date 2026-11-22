r"""H17 etapa 1: detector propio de calor en el cráter a 3,9 µm (VRP por el método del infrarrojo medio) desde la
L1b de GOES-19. Criterio: docs/own_volcat/h17_regla_propia/criterio_H17_2026-11-21.md §1 y §3.

Escribe (repo):  resultados/calor_por_cuadro.csv  (cuadro, sitio, VRP, T10, n calientes, cenit solar, BT14 cráter)
                 resultados/h17_calor_resultado.txt
Escribe (D:):    D:\goes_cache\h17\calor.pkl (lo mismo, para la etapa 2)
La verdad térmica VOLCAT se lee de los archivos de evento (D:, licencia restringida) y sólo se citan los cuatro
valores time_since_10MW por cuadro, que ya publicó H16.
Uso: python -I h17_calor.py
"""
import os
import sys
import glob
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import netCDF4 as nc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h17_comun as K  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados")
SIGMA = 5.670374419e-8
ZONA, A0, A1 = 6.0, 8.0, 14.0
AREA = K.area_pixel()                          # km²
MASK = {s: (K.dist_cumbre(s) <= ZONA, (K.dist_cumbre(s) >= A0) & (K.dist_cumbre(s) <= A1)) for s in K.SITIOS}


def a_mir(co):
    """a de L7(T) ≈ a T⁴ entre 600 y 1.500 K con los Planck del NetCDF (criterio §1)."""
    fk1, fk2, bc1, bc2 = co
    T = np.linspace(600, 1500, 901)
    L = fk1 / (np.exp(fk2 / (bc1 + bc2 * T)) - 1)
    return float(np.sum(L * T ** 4) / np.sum(T ** 8))


def sza(dt, lat, lon):
    """Cenit solar (NOAA, precisión ~0,1°)."""
    doy = dt.timetuple().tm_yday
    g = 2 * np.pi / 365 * (doy - 1 + (dt.hour - 12) / 24 + dt.minute / 1440)
    decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
            + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g)
                    - 0.040849 * np.sin(2 * g))
    tst = dt.hour * 60 + dt.minute + eqt + 4 * lon
    ha = np.radians(tst / 4 - 180)
    la = np.radians(lat)
    c = np.sin(la) * np.sin(decl) + np.cos(la) * np.cos(decl) * np.cos(ha)
    return float(np.degrees(np.arccos(np.clip(c, -1, 1))))


def calor(r7, co7, r14, co14):
    b7, b14 = K.bt(r7, co7), K.bt(r14, co14)
    D = b7 - b14
    a = a_mir(co7)
    out = {}
    for s, (z, r) in MASK.items():
        dr, lr = D[r], r7[r]
        ok = np.isfinite(dr) & np.isfinite(lr)
        if ok.sum() < 20 or not np.isfinite(D[z]).any():
            out[s] = dict(vrp=np.nan, n_cal=0, dmax=np.nan, bt14_cr=np.nan, bt14_an=np.nan)
            continue
        med, mad = np.median(dr[ok]), np.median(np.abs(dr[ok] - np.median(dr[ok])))
        umb = max(2.0, 3 * 1.4826 * mad)
        dz = D - med
        dl = r7 - np.median(lr[ok])
        cal = z & (dz >= umb) & (dl > 0)
        vrp = float(np.nansum(AREA[cal] * 1e6 * SIGMA / a * dl[cal]) / 1e6)   # MW
        # INFORMATIVO (no decide, agregado tras ver la primera corrida): sin el término 3 s del anillo
        cf = z & (dz >= 2.0) & (dl > 0)
        vrp_fijo = float(np.nansum(AREA[cf] * 1e6 * SIGMA / a * dl[cf]) / 1e6)
        # INFORMATIVO: fondo coherente con el test de píxel caliente. El fondo a 3,9 µm de cada píxel es la radiancia
        # de Planck de BT14 del propio píxel + mediana del anillo de D (lo que mediría si tuviera el D del anillo).
        fk1, fk2, bc1, bc2 = co7
        tb = b14 + med
        l7bg = fk1 / (np.exp(fk2 / (bc1 + bc2 * tb)) - 1)
        dlc = r7 - l7bg
        cc = z & (dz >= umb) & (dlc > 0)
        cc2 = z & (dz >= 2.0) & (dlc > 0)
        vrp_ctx = float(np.nansum(AREA[cc] * 1e6 * SIGMA / a * dlc[cc]) / 1e6)
        vrp_ctx_fijo = float(np.nansum(AREA[cc2] * 1e6 * SIGMA / a * dlc[cc2]) / 1e6)
        dd = np.where(z, dz, np.nan)
        out[s] = dict(vrp=vrp, vrp_fijo=vrp_fijo, vrp_ctx=vrp_ctx, vrp_ctx_fijo=vrp_ctx_fijo, n_cal=int(cal.sum()), dmax=float(np.nanmax(dd)), umb=umb,
                      bt14_cr=float(np.nanmax(np.where(z, b14, np.nan))), bt14_an=float(np.nanmedian(b14[r])))
    return out


def verdad_termica():
    v = {}
    for f in sorted(glob.glob(os.path.join(K.EVDIR, "*.nc"))):
        t = datetime.strptime(os.path.basename(f).split("_s")[1][:12], "%Y%m%d%H%M")
        with nc.Dataset(f) as d:
            x = d["volcano_thermal_activity"]
            ts = float(x.getncattr("time_since_10MW"))
        v[t] = ts
    return v


def main():
    idx = K.indice()
    filas = []
    for c in sorted(idx):
        if 7 not in idx[c] or 14 not in idx[c]:
            continue
        dt = datetime.strptime(c, "%Y%m%d_%H%M")
        r7, co7 = K.banda(idx, c, 7)
        r14, co14 = K.banda(idx, c, 14)
        for s, d in calor(r7, co7, r14, co14).items():
            la, lo, _ = K.SITIOS[s]
            filas.append(dict(cuadro=c, dt=dt, sitio=s, sza=sza(dt, la, lo), **d))
    df = pd.DataFrame(filas)
    df["T10"] = df.vrp >= 10.0
    df["periodo"] = np.where(df.sza >= 90, "noche", np.where(df.sza < 80, "dia", "crepusculo"))
    df.to_pickle(os.path.join(K.H17, "calor.pkl"))
    df.drop(columns=["dt"]).round(3).to_csv(os.path.join(RES, "calor_por_cuadro.csv"), index=False)

    L = []
    p = lambda *a: L.append(" ".join(str(x) for x in a))  # noqa: E731
    p("H17 etapa 1, calor propio a 3,9 µm. Generado", datetime.now().strftime("%Y-%m-%d %H:%M"))
    ch = df[df.sitio == "chillan"].set_index("dt")
    p("cuadros con C07+C14:", len(ch), "| noche", int((ch.periodo == "noche").sum()), "dia",
      int((ch.periodo == "dia").sum()), "crepusculo", int((ch.periodo == "crepusculo").sum()))
    p("a (L7 ≈ a T^4, Planck del NetCDF):", f"{a_mir(K.banda(idx, sorted(c for c in idx if 7 in idx[c])[0], 7)[1]):.4e}",
      "| area pixel crater km2:", round(float(AREA[MASK['chillan'][0]].mean()), 2))

    p("\n== C1: cuadros VOLCAT con volcano_thermal_activity (time_since_10MW) ==")
    vt = verdad_termica()
    pos = [t for t, v in vt.items() if v == 0.0]
    nulo = [t for t, v in vt.items() if v < -1e8]
    ts = sorted(vt)
    ini = [t for i, t in enumerate(ts) if i == 0 or t - ts[i - 1] > timedelta(minutes=60)]   # inicio de evento (H14)
    p("inicios de evento:", [f"{t:%d-%m %H:%M}" for t in ini], "| con 10MW=0:", [f"{t:%d-%m %H:%M}" for t in pos],
      "| cuadros con relleno:", len(nulo))
    hits = 0
    for t in ini:
        etiqueta = "10MW=0" if t in pos else "relleno"
        r = ch.loc[t] if t in ch.index else None
        vec = [ch.loc[t + timedelta(minutes=m)] for m in (-10, 10) if t + timedelta(minutes=m) in ch.index]
        dia = ch[ch.index.date == t.date()]
        if r is None:
            p(f"{t:%d-%m %H:%M} VOLCAT {etiqueta}: SIN C07 en el scan")
        else:
            hits += int(t in pos and r.T10)
            p(f"{t:%d-%m %H:%M} VOLCAT {etiqueta}: VRP {r.vrp:.1f} MW T10={bool(r.T10)} n_cal={r.n_cal} "
              f"dmax={r.dmax:.2f} K umb={r.umb:.2f} sza={r.sza:.1f} BT14 crater-anillo={r.bt14_cr - r.bt14_an:.1f} K")
        p(f"   ±1 scan: {[round(v.vrp, 1) for v in vec]} | dia UTC: {len(dia)} cuadros, T10 en {int(dia.T10.sum())}, "
          f"VRP max {dia.vrp.max():.1f} MW")
    p(f"C1: T10 en {hits} de {len(pos)} cuadros con time_since_10MW = 0 (pide >= 2) ->",
      "CUMPLE" if hits >= 2 else "NO CUMPLE")

    p("\n== C2: especificidad en Antuco y Longaví ==")
    ct = df[df.sitio != "chillan"]
    c2 = True
    for per, vara in (("noche", 0.02), ("dia", 0.05), ("crepusculo", None)):
        s = ct[(ct.periodo == per) & ct.vrp.notna()]
        f = s.T10.mean() if len(s) else np.nan
        sc = df[(df.sitio == "chillan") & (df.periodo == per) & df.vrp.notna()]
        txt = "" if vara is None else ("cumple" if f <= vara else "NO cumple")
        if vara is not None and not f <= vara:
            c2 = False
        p(f"{per}: controles {len(s)} cuadros, T10 {f:.4f} (vara {vara}) {txt} | Chillán {len(sc)} cuadros, "
          f"T10 {sc.T10.mean():.3f}, VRP mediana {sc.vrp.median():.2f} MW, p90 {sc.vrp.quantile(.9):.1f}")
    for s in ("antuco", "longavi"):
        for per in ("noche", "dia"):
            x = df[(df.sitio == s) & (df.periodo == per) & df.vrp.notna()]
            p(f"   {s} {per}: {len(x)} cuadros, T10 {x.T10.mean():.4f}, VRP p99 {x.vrp.quantile(.99):.1f} MW")
    p("C2:", "CUMPLE" if c2 else "NO CUMPLE")
    ver = ("cumple" if (hits >= 2 and c2) else "sensible pero ruidoso" if hits >= 2 else "no recupera")
    p("\nVEREDICTO ETAPA 1:", ver)

    p("\n== INFORMATIVO, NO DECIDE (agregado tras la primera corrida): sensibilidad del umbral ==")
    p("Variantes: umbral por píxel fijo de 2 K sin el término 3 s del anillo (vrp_fijo), y corte de 10 o 5 MW.")
    p("vrp_ctx = mismo test de píxel caliente, pero fondo a 3,9 µm = Planck7(BT14 del píxel + mediana_R(D)), coherente "
      "con el test; vrp_ctx_fijo = lo mismo con umbral fijo de 2 K.")
    for col, u in (("vrp", 5.0), ("vrp_fijo", 10.0), ("vrp_fijo", 5.0), ("vrp_ctx", 10.0), ("vrp_ctx", 5.0),
                   ("vrp_ctx_fijo", 10.0), ("vrp_ctx_fijo", 5.0)):
        h = [bool(ch.loc[t, col] >= u) for t in pos if t in ch.index]
        fa = {per: df[(df.sitio != "chillan") & (df.periodo == per) & df[col].notna()][col].ge(u).mean()
              for per in ("noche", "dia")}
        frc = {per: df[(df.sitio == "chillan") & (df.periodo == per) & df[col].notna()][col].ge(u).mean()
               for per in ("noche", "dia")}
        p(f"{col} >= {u} MW: cuadros VOLCAT 10MW=0 con dato {len(h)}, detectados {sum(h)} | controles noche "
          f"{fa['noche']:.4f} día {fa['dia']:.4f} | Chillán noche {frc['noche']:.3f} día {frc['dia']:.3f}")
    for t in ini:
        if t in ch.index:
            r = ch.loc[t]
            p(f"   {t:%d-%m %H:%M}: vrp_fijo {r.vrp_fijo:.1f} MW | vrp_ctx {r.vrp_ctx:.1f} MW | "
              f"vrp_ctx_fijo {r.vrp_ctx_fijo:.1f} MW")
    for col in ("vrp_ctx", "vrp_ctx_fijo"):
        for s in ("chillan", "antuco", "longavi"):
            for per in ("noche", "dia"):
                x = df[(df.sitio == s) & (df.periodo == per) & df[col].notna()][col]
                p(f"   {col} {s} {per}: mediana {x.median():.1f} p90 {x.quantile(.9):.1f} p99 {x.quantile(.99):.1f} MW")

    p("\n== Descriptivo: fracción diaria de cuadros con T10 (noche | día) ==")
    df["fecha"] = df.dt.dt.date
    for f, g in df[df.vrp.notna()].groupby("fecha"):
        fila = []
        for s in ("chillan", "antuco", "longavi"):
            for per in ("noche", "dia"):
                x = g[(g.sitio == s) & (g.periodo == per)]
                fila.append(f"{x.T10.mean():.2f}({len(x)})" if len(x) else "  -  ")
        p(f"{f}  chillan {fila[0]} | {fila[1]}   antuco {fila[2]} | {fila[3]}   longavi {fila[4]} | {fila[5]}")
    open(os.path.join(RES, "h17_calor_resultado.txt"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
