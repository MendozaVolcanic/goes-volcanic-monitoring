r"""H27: implementa criterio_2026-11-23.md (commit a82c540) sin cambios.

Pregunta: en las ventanas de E10 a E13 (pulsos de tarde que VOLCAT marco), el estadistico de H24 en Chillan queda
mas bajo que lo que da el mismo estadistico, a las mismas horas, en cumbres sin actividad (Antuco, Longavi)?

Por que asi: el fondo propio de Chillan de tarde tiene 3 a 7 dias (conteo, criterio §3); las cumbres, que no tienen
actividad, aportan fondo todos los dias. Que ese fondo represente a Chillan no se supone: se mide de manana (T1),
donde Chillan si tiene fondo propio, y de tarde con los pocos dias propios que hay (T2).

Insumos (solo lectura): cubos de H23 y H24 via h24_medir.cargar(). Importa h24_medir sin modificarlo.
Salidas: resultados\h27_episodios.csv, h27_resumen.json. Uso: python -I h27_medir.py [pruebas]
"""
import csv
import json
import os
import sys
import warnings

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "h24_pulsos_reav", "scripts"))
import h24_medir as H  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RES = os.path.join(os.path.dirname(AQUI), "resultados")

# ---------- parametros del criterio H27 ----------
BASE_SLOTS = 6                 # linea base: cuadros s-6 a s+6 (+-1 h), criterio §5.1
MIN_NULO_SD = 12               # sitio-dia minimos en el nulo de cumbres, §5.2
CONTROLES = ("antuco", "longavi")
FRANJA_KM = 3.0
COTA_PAR = 300.0               # secundaria 1: pareo por cota +-300 m
T1_MED, T1_MAD = 0.5, (0.67, 1.5)
T2_MAX, T2_MIN_N, T2_MIN_DET = 0.20, 8, 2
DECIDEN = ("E10", "E11", "E12", "E13")
TARDE = ("E9", "E10", "E11", "E12", "E13", "E14")
MANANA = ("E1", "E6", "E7")
ZCOTA = H.ZDEM


def zrob(x, nulo, min_n=MIN_NULO_SD):
    nulo = np.asarray([v for v in nulo if np.isfinite(v)])
    if len(nulo) < min_n or not np.isfinite(x):
        return np.nan, len(nulo), np.nan
    med = np.median(nulo)
    mad = 1.4826 * np.median(np.abs(nulo - med))
    if mad <= H.MAD_MIN:
        return np.nan, len(nulo), mad
    return (x - med) / mad, len(nulo), mad


def med_mad(v):
    v = np.asarray([x for x in v if np.isfinite(x)])
    if len(v) == 0:
        return np.nan, np.nan, 0
    m = np.median(v)
    return float(m), float(1.4826 * np.median(np.abs(v - m))), len(v)


def franja(sitio, direc, Hm, W):
    """Mascara sobre W de los pixeles a <= 3 km del eje del sector (como h24_explorar.sectores_x)."""
    la, lo = H.VENT if sitio == "chillan" else H.SITIOS[sitio][:2]
    h = H.CRATER_KM + Hm / 1000.0
    lejos = (H.rumbo(la, lo, *H.SUBSAT) + 180.0) % 360.0
    x, y = H.plano(la, lo)
    x = x - H.PARALAJE * h * np.sin(np.radians(lejos))
    y = y - H.PARALAJE * h * np.cos(np.radians(lejos))
    ux, uy = np.sin(np.radians(direc)), np.cos(np.radians(direc))
    return np.abs(x * uy - y * ux)[W] <= FRANJA_KM


class Motor27(H.Motor):
    def base(self, sitio, d, s, px):
        """Linea base §5.1: mediana a s-6..s+6 de todos los dias despejados del periodo, sin el dia d; para Chillan
        sin los dias excluidos de H24; >= 3 dias con dato en el pixel."""
        k = (sitio, d, s, px.tobytes())
        if k in self._base:
            return self._base[k]
        F = self.F[sitio]
        bt, bd, dia = [], [], []
        for dd in range(H.NDIAS):
            if dd == d or (sitio == "chillan" and H.DIA_EXCL[dd]):
                continue
            for ss in range(s - BASE_SLOTS, s + BASE_SLOTS + 1):
                if 0 <= ss < 144 and F[dd, ss]:
                    bt.append(self.bt11[dd, ss, px]); bd.append(self.btd[dd, ss, px]); dia.append(dd)
        if not bt:
            out = (np.full(len(px), np.nan), np.full(len(px), np.nan))
        else:
            bt, bd, dia = np.array(bt), np.array(bd), np.array(dia)
            ndias = np.zeros(len(px), int)
            for dd in np.unique(dia):
                ndias += np.isfinite(bt[dia == dd]).any(0)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                r11, rd = np.nanmedian(bt, 0), np.nanmedian(bd, 0)
            r11[ndias < H.MIN_DIAS_REF] = np.nan
            rd[ndias < H.MIN_DIAS_REF] = np.nan
            out = (r11, rd)
        self._base[k] = out
        return out

    def S_cuadro(self, sitio, d, s, W, R, iny=None, masc=None, cota=False):
        if not self.F[sitio][d, s]:
            return np.nan
        px = np.concatenate([W, R])
        r11, rd = self.base(sitio, d, s, px)
        bt11 = self.bt11[d, s, px].astype(float)
        btd = self.btd[d, s, px].astype(float)
        if iny is not None:
            eps, Tt = iny
            I14 = self.r14[d, s, px].astype(float)
            I15 = self.r15[d, s, px].astype(float)
            e12 = 1 - (1 - eps) ** H.BETA
            m = np.zeros(len(px), bool)
            m[:len(W)] = True if masc is None else masc
            I14[m] = (1 - eps) * I14[m] + eps * H.rad_de_bt(Tt, self.co14)
            I15[m] = (1 - e12) * I15[m] + e12 * H.rad_de_bt(Tt, self.co15)
            bt11 = H.bt_de_rad(I14, self.co14)
            btd = bt11 - H.bt_de_rad(I15, self.co15)
        x = btd - rd
        zc = ZCOTA[px]
        nW = len(W)
        xw, kw, zw = x[:nW], r11[:nW], zc[:nW]
        xr, kr, zr = x[nW:], r11[nW:], zc[nW:]
        ok = np.isfinite(xr) & np.isfinite(kr)
        xr, kr, zr = xr[ok], kr[ok], zr[ok]
        dif = []
        for xi, ki, zi in zip(xw, kw, zw):
            if not (np.isfinite(xi) and np.isfinite(ki)):
                continue
            sel = np.abs(kr - ki) <= H.PAR_K               # pareo por BT11 esperada (H24)
            if cota:
                sel &= np.abs(zr - zi) <= COTA_PAR
            if sel.sum() >= H.MIN_REF_PAR:
                dif.append(xi - np.median(xr[sel]))
        return float(np.median(dif)) if len(dif) >= H.MIN_W else np.nan

    def E(self, sitio, d, slots, W, R, iny_por_slot=None, masc=None, cota=False):
        Ss = []
        for s in slots:
            v = self.S_cuadro(sitio, d, s, W, R, iny=None if iny_por_slot is None else iny_por_slot[s],
                              masc=masc, cota=cota)
            if np.isfinite(v):
                Ss.append(v)
        return (float(np.median(Ss)) if len(Ss) >= H.MIN_CUADROS else np.nan), len(Ss)


def episodio(M, Tz, e, ven, iz):
    eid, _, _, Hm, direc, fuente = e
    d0, slots = ven[eid]
    otros = [d for d in range(H.NDIAS) if d != d0]
    propios = [d for d in otros if not H.DIA_EXCL[d]]
    G = {s: H.sectores(s, direc, Hm) for s in H.SITIOS}
    FR = {s: franja(s, direc, Hm, G[s]["W"]) for s in H.SITIOS}
    f = {"ep": eid, "H": Hm, "grupo": "alto" if Hm >= H.ALTO_H else ("bajo" if Hm < 800 else "medio"),
         "direccion": direc, "fuente_dir": fuente, "dia": str(H.T0.date() + __import__("datetime").timedelta(days=d0)),
         "slots": len(slots)}
    for s in H.SITIOS:
        f[f"{s}_nW"], f[f"{s}_nR"], f[f"{s}_nfranja"] = len(G[s]["W"]), len(G[s]["R"]), int(FR[s].sum())
        f[f"{s}_cotaW"] = float(np.nanmean(ZCOTA[G[s]["W"]]))
        f[f"{s}_cotaR"] = float(np.nanmean(ZCOTA[G[s]["R"]]))
        f[f"{s}_contraste_cota"] = f[f"{s}_cotaW"] - f[f"{s}_cotaR"]

    # nulo de cumbres: (sitio, dia) -> E
    nulo = {(c, d): M.E(c, d, slots, G[c]["W"], G[c]["R"])[0] for c in CONTROLES for d in otros}
    vals = list(nulo.values())
    Ech, nc = M.E("chillan", d0, slots, G["chillan"]["W"], G["chillan"]["R"])
    z, nn, mad = zrob(Ech, vals)
    med0 = med_mad(vals)[0]
    f.update({"E": Ech, "cuadros": nc, "z": z, "nnulo": nn, "mad_nulo": mad, "med_nulo": med0})

    # placebo contra el viento (W girado 180 grados) contra el nulo de cumbres con el placebo
    nulo_p = [M.E(c, d, slots, G[c]["Wc"], G[c]["R"])[0] for c in CONTROLES for d in otros]
    Ep, _ = M.E("chillan", d0, slots, G["chillan"]["Wc"], G["chillan"]["R"])
    f["placebo_E"], f["placebo_z"] = Ep, zrob(Ep, nulo_p)[0]

    # cumbres en el mismo cuadro (dia del episodio)
    for c in CONTROLES:
        Ec, ncc = M.E(c, d0, slots, G[c]["W"], G[c]["R"])
        f[f"{c}_E"], f[f"{c}_cuadros"], f[f"{c}_z"] = Ec, ncc, zrob(Ec, vals)[0]
        # secundaria 2: nulo de una sola cumbre (6 sitio-dia minimos, como H24)
        f[f"z_solo_{c}"] = zrob(Ech, [v for (cc, _), v in nulo.items() if cc == c], min_n=H.MIN_NULO)[0]

    # falsas alarmas: cada sitio-dia contra los otros, sin los dos del mismo dia
    fa = []
    for (c, d), v in nulo.items():
        if np.isfinite(v):
            zi = zrob(v, [w for (cc, dd), w in nulo.items() if dd != d])[0]
            if np.isfinite(zi):
                fa.append(bool(zi <= H.Z_UMBRAL))
    f["fa_n"], f["fa_det"] = len(fa), int(np.sum(fa))

    # poder en las cumbres (y en Chillan, informativo)
    variantes = [("capa_0.05", 0.05, False, "tope"), ("capa_0.10", 0.10, False, "tope"),
                 ("capa_0.15", 0.15, False, "tope"), ("franja_0.15", 0.15, True, "tope"),
                 ("franja_0.30", 0.30, True, "tope"), ("franja_0.50", 0.50, True, "tope"),
                 ("grande", 0.90, False, "10km")]
    for nombre, eps, usa_fr, alt in variantes:
        det = []
        for (c, d), v in nulo.items():
            if not np.isfinite(v):
                continue
            Tt = {s: Tz[d, s, iz[alt]] for s in slots}
            if not all(np.isfinite(t) for t in Tt.values()):
                continue
            Ei = M.E(c, d, slots, G[c]["W"], G[c]["R"], iny_por_slot={s: (eps, Tt[s]) for s in slots},
                     masc=FR[c] if usa_fr else None)[0]
            zi = zrob(Ei, [w for (cc, dd), w in nulo.items() if dd != d])[0]
            if np.isfinite(zi):
                det.append(bool(zi <= H.Z_UMBRAL))
        f[f"poder_{nombre}"], f[f"poder_{nombre}_n"] = (float(np.mean(det)) if det else np.nan), len(det)

    # fondo propio de Chillan: T1 (manana), T2 (tarde), poder en Chillan y secundaria 3
    own = {d: M.E("chillan", d, slots, G["chillan"]["W"], G["chillan"]["R"])[0] for d in propios}
    ov = [v for v in own.values() if np.isfinite(v)]
    mo, so, no = med_mad(ov)
    mc, sc, ncu = med_mad(vals)
    f.update({"propio_n": no, "propio_med": mo, "propio_mad": so, "cumbres_med": mc, "cumbres_mad": sc,
              "cumbres_n": ncu})
    f["T1_dmed_en_mad"] = abs(mo - mc) / sc if (np.isfinite(mo) and np.isfinite(sc) and sc > 0) else np.nan
    f["T1_razon_mad"] = so / sc if (np.isfinite(so) and np.isfinite(sc) and sc > 0) else np.nan
    t2 = []
    for d, v in own.items():
        if np.isfinite(v):
            zi = zrob(v, [w for (cc, dd), w in nulo.items() if dd != d])[0]
            if np.isfinite(zi):
                t2.append(bool(zi <= H.Z_UMBRAL))
    f["T2_n"], f["T2_det"] = len(t2), int(np.sum(t2))
    for nombre, eps, usa_fr in (("capa_0.15", 0.15, False), ("franja_0.30", 0.30, True)):
        det = []
        for d, v in own.items():
            if not np.isfinite(v):
                continue
            Tt = {s: Tz[d, s, iz["tope"]] for s in slots}
            if not all(np.isfinite(t) for t in Tt.values()):
                continue
            Ei = M.E("chillan", d, slots, G["chillan"]["W"], G["chillan"]["R"],
                     iny_por_slot={s: (eps, Tt[s]) for s in slots}, masc=FR["chillan"] if usa_fr else None)[0]
            zi = zrob(Ei, [w for (cc, dd), w in nulo.items() if dd != d])[0]
            if np.isfinite(zi):
                det.append(bool(zi <= H.Z_UMBRAL))
        f[f"poder_chillan_{nombre}"], f[f"poder_chillan_{nombre}_n"] = (float(np.mean(det)) if det else np.nan), len(det)
    f["z_nulo_propio"] = zrob(Ech, [v for d, v in own.items() if np.isfinite(v)], min_n=H.MIN_NULO)[0]

    # secundaria 1: pareo por BT11 y cota
    nulo_c = [M.E(c, d, slots, G[c]["W"], G[c]["R"], cota=True)[0] for c in CONTROLES for d in otros]
    Ecc, _ = M.E("chillan", d0, slots, G["chillan"]["W"], G["chillan"]["R"], cota=True)
    f["cota_E"], f["cota_z"] = Ecc, zrob(Ecc, nulo_c)[0]
    return f


def clase(f):
    if not (f["cuadros"] >= H.MIN_CUADROS):
        return "SIN DATO (cielo)"
    if f["nnulo"] < MIN_NULO_SD or not np.isfinite(f["z"]):
        return "SIN PODER"
    for k in ("poder_capa_0.15", "poder_franja_0.30"):
        if not (np.isfinite(f[k]) and f[k] >= H.PODER_MIN):
            return "SIN PODER"
    if f["z"] > H.Z_UMBRAL:
        return "SIN SEÑAL"
    plac = np.isfinite(f["placebo_z"]) and f["placebo_z"] <= H.Z_UMBRAL
    cumbre = any(np.isfinite(f[f"{c}_z"]) and f[f"{c}_z"] <= H.Z_UMBRAL for c in CONTROLES)
    return "DUDOSO" if (plac or cumbre) else "SEÑAL"


def pruebas():
    """Pruebas numericas: las de H24, mas zrob con minimo propio, franja dentro de W y base de +-1 h que no usa el
    dia evaluado ni (en Chillan) los dias excluidos."""
    H.pruebas()
    z, n, _ = zrob(-3.0, list(np.linspace(-1, 1, 12)))
    assert n == 12 and z < -2
    assert np.isnan(zrob(-3.0, list(np.linspace(-1, 1, 11)))[0])
    g = H.sectores("antuco", 315.0, 2200)
    fr = franja("antuco", 315.0, 2200, g["W"])
    assert 0 < fr.sum() < len(g["W"]), (fr.sum(), len(g["W"]))
    # base sintetica: 3 dias despejados con BTD conocida; el dia evaluado y los excluidos no entran
    nd = H.NDIAS
    r = np.full((nd, 144, 2), 8.0, "float32")
    co = np.array([8.5e3, 1.2858e3, 0.2105, 0.99925])
    M = Motor27.__new__(Motor27)
    M.co14 = M.co15 = co
    M.bt11 = np.full((nd, 144, 2), 270.0, "float32")
    M.btd = np.full((nd, 144, 2), np.nan, "float32")
    M.r14 = M.r15 = r
    M._base = {}
    Fx = np.zeros((nd, 144), bool)
    excl = int(np.where(H.DIA_EXCL)[0][0])
    for dd, val in ((5, 1.0), (6, 2.0), (7, 3.0), (excl, 100.0), (10, 50.0)):
        Fx[dd, 100] = True
        M.btd[dd, 100] = val
    M.F = {"chillan": Fx, "antuco": Fx}
    px = np.array([0, 1])
    assert np.allclose(M.base("chillan", 10, 104, px)[1], 2.0)              # sin dia 10 ni excluido: 1,2,3
    assert np.isnan(M.base("chillan", 10, 108, px)[1]).all()                 # fuera de +-1 h (por arriba)
    assert np.isnan(M.base("chillan", 10, 93, px)[1]).all()                  # fuera de +-1 h (por abajo)
    assert np.allclose(M.base("chillan", 10, 94, px)[1], 2.0)                # borde de +-1 h
    assert np.allclose(M.base("chillan", 10, 106, px)[1], 2.0)               # borde de +-1 h
    assert np.isnan(M.base("chillan", 10, 107, px)[1]).all()
    M._base = {}
    assert np.allclose(M.base("antuco", 10, 100, px)[1], np.median([1, 2, 3, 100]))  # cumbre: excluido si entra
    print("pruebas H27 OK")


def main():
    pruebas()
    r14, r15, acm, co14, co15 = H.cargar()
    M = Motor27(r14, r15, acm, co14, co15)
    alturas = sorted({H.CRATER_KM * 1000 + e[3] for e in H.EPISODIOS})
    Tz = H.gfs_t(alturas + [10000.0])
    ven = H.ventanas()
    filas = []
    for e in H.EPISODIOS:
        if e[0] not in TARDE + MANANA:
            continue
        iz = {"tope": alturas.index(H.CRATER_KM * 1000 + e[3]), "10km": len(alturas)}
        f = episodio(M, Tz, e, ven, iz)
        f["clase"] = clase(f)
        filas.append(f)
        print(e[0], f["clase"], "z", f["z"], "cuadros", f["cuadros"], "nulo", f["nnulo"],
              "capa015", f["poder_capa_0.15"], "franja030", f["poder_franja_0.30"], "grande", f["poder_grande"],
              "FA", f["fa_det"], "/", f["fa_n"], "T1", f["T1_dmed_en_mad"], f["T1_razon_mad"],
              "T2", f["T2_det"], "/", f["T2_n"], flush=True)
    os.makedirs(RES, exist_ok=True)
    claves = sorted({k for f in filas for k in f}, key=lambda k: (k != "ep", k))
    with open(os.path.join(RES, "h27_episodios.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, claves)
        w.writeheader()
        for f in filas:
            w.writerow(f)
    por = {f["ep"]: f for f in filas}
    tarde = [por[k] for k in TARDE if k in por]
    fa_n, fa_det = sum(f["fa_n"] for f in tarde), sum(f["fa_det"] for f in tarde)
    tasa_fa = fa_det / fa_n if fa_n else np.nan
    t1 = {k: {"dmed_en_mad": por[k]["T1_dmed_en_mad"], "razon_mad": por[k]["T1_razon_mad"],
              "n_propio": por[k]["propio_n"]} for k in MANANA}
    t1_calc = all(np.isfinite(v["dmed_en_mad"]) and np.isfinite(v["razon_mad"]) and v["n_propio"] >= H.MIN_NULO
                  for v in t1.values())
    t1_ok = t1_calc and all(v["dmed_en_mad"] <= T1_MED and T1_MAD[0] <= v["razon_mad"] <= T1_MAD[1]
                            for v in t1.values())
    t2_n, t2_det = sum(f["T2_n"] for f in tarde), sum(f["T2_det"] for f in tarde)
    t2_sin_dato = t2_n < T2_MIN_N
    t2_falla = (not t2_sin_dato) and t2_det >= T2_MIN_DET and t2_det / t2_n > T2_MAX
    deciden = [por[k] for k in DECIDEN]
    grande_ok = all((not np.isfinite(f["poder_grande"])) or f["poder_grande"] >= H.PODER_GRANDE
                    for f in deciden if f["nnulo"] >= MIN_NULO_SD)
    senal = sum(f["clase"] == "SEÑAL" for f in deciden)
    decid = sum(f["clase"] in ("SEÑAL", "SIN SEÑAL") for f in deciden)
    if not (tasa_fa <= H.FA_MAX) or not grande_ok or (t1_calc and not t1_ok) or t2_falla:
        ver = "INVÁLIDO"
    elif not t1_calc or t2_sin_dato:
        ver = "NO CONCLUYENTE"
    elif senal >= 2 and senal >= 0.5 * decid:
        ver = "LOS PULSOS DE TARDE SE VEN"
    elif decid >= 3 and senal == 0:
        ver = "LOS PULSOS DE TARDE NO SE VEN"
    else:
        ver = "NO CONCLUYENTE"
    resumen = {"criterio_commit": "a82c540", "veredicto": ver,
               "falsas_alarmas": {"n": fa_n, "detecta": fa_det, "tasa": tasa_fa},
               "T1": {"calculable": t1_calc, "pasa": t1_ok, "por_episodio": t1},
               "T2": {"n": t2_n, "detecta": t2_det, "sin_dato": t2_sin_dato, "falla": t2_falla},
               "control_grande_ok": grande_ok, "deciden": {"senal": senal, "decidibles": decid},
               "clases": {f["ep"]: f["clase"] for f in filas}}
    json.dump(resumen, open(os.path.join(RES, "h27_resumen.json"), "w", encoding="utf-8"), indent=1,
              ensure_ascii=False, default=float)
    print(json.dumps(resumen, indent=1, ensure_ascii=False, default=float))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pruebas":
        pruebas()
    else:
        main()
