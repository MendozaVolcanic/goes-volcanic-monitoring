r"""H24, enmienda post hoc 2 (commit 7c138fa): analisis EXPLORATORIO, no decide.

X1: linea base y dias nulos con todos los dias no excluidos del 21-09 al 21-11 (no +-21).
X2: estadistico de cola (percentil 20 de las diferencias pareadas en W) ademas de la mediana.
Poder angosto: capa solo en la franja de +-3 km alrededor del eje del sector (pluma angosta), eps 0,15, 0,30, 0,50.
Todo lo demas (pareo por BT11 de linea base, regla z <= -2, falsas alarmas, placebo, cumbres) igual al criterio.

Salidas: resultados\h24_explorar.csv, h24_explorar_resumen.json. Uso: python -I h24_explorar.py
"""
import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h24_medir as H  # noqa: E402

H.VENT_DIAS = 99                      # X1: toda la ventana 21-09 a 21-11
FRANJA_KM = 3.0
ESTIM = {"mediana": np.median, "p20": lambda x: np.percentile(x, 20)}


def sectores_x(sitio, direc, Hm):
    """Como H.sectores, mas la mascara de la franja de +-3 km alrededor del eje dentro de W."""
    g = H.sectores(sitio, direc, Hm)
    la, lo = H.VENT if sitio == "chillan" else H.SITIOS[sitio][:2]
    h = H.CRATER_KM + Hm / 1000.0
    lejos = (H.rumbo(la, lo, *H.SUBSAT) + 180.0) % 360.0
    x, y = H.plano(la, lo)
    x = x - H.PARALAJE * h * np.sin(np.radians(lejos))
    y = y - H.PARALAJE * h * np.cos(np.radians(lejos))
    ux, uy = np.sin(np.radians(direc)), np.cos(np.radians(direc))
    perp = np.abs(x * uy - y * ux)                      # distancia al eje
    g["franja"] = perp[g["W"]] <= FRANJA_KM             # mascara sobre W
    return g


class MotorX(H.Motor):
    def S_cuadro(self, sitio, d, s, W, R, det="D2", par="esperada", iny=None, estim="mediana", masc=None):
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
        nW = len(W)
        xw, kw, xr, kr = x[:nW], r11[:nW], x[nW:], r11[nW:]
        ok = np.isfinite(xr) & np.isfinite(kr)
        xr, kr = xr[ok], kr[ok]
        dif = []
        for xi, ki in zip(xw, kw):
            if np.isfinite(xi) and np.isfinite(ki):
                sel = np.abs(kr - ki) <= H.PAR_K
                if sel.sum() >= H.MIN_REF_PAR:
                    dif.append(xi - np.median(xr[sel]))
        return float(ESTIM[estim](np.array(dif))) if len(dif) >= H.MIN_W else np.nan

    def E(self, sitio, d, slots, W, R, estim="mediana", iny_por_slot=None, masc=None):
        Ss = []
        for s in slots:
            v = self.S_cuadro(sitio, d, s, W, R, iny=None if iny_por_slot is None else iny_por_slot[s],
                              estim=estim, masc=masc)
            if np.isfinite(v):
                Ss.append(v)
        return (float(np.median(Ss)) if len(Ss) >= H.MIN_CUADROS else np.nan), len(Ss)


def episodio(M, Tz, e, ven, iz):
    eid, _, _, Hm, direc, _ = e
    d0, slots = ven[eid]
    nulos = [d for d in range(H.NDIAS) if d != d0 and not H.DIA_EXCL[d]]
    filas = []
    for estim in ("mediana", "p20"):
        f = {"ep": eid, "estim": estim, "H": Hm, "grupo": "alto" if Hm >= H.ALTO_H else ("bajo" if Hm < 800 else "medio")}
        for sitio in H.SITIOS:
            g = sectores_x(sitio, direc, Hm)
            Ee, nc = M.E(sitio, d0, slots, g["W"], g["R"], estim=estim)
            En = {d: M.E(sitio, d, slots, g["W"], g["R"], estim=estim)[0] for d in nulos}
            z, nn, mad = H.zrob(Ee, list(En.values()))
            f[f"{sitio}_E"], f[f"{sitio}_cuadros"], f[f"{sitio}_z"], f[f"{sitio}_nnulo"] = Ee, nc, z, nn
            if sitio != "chillan":
                continue
            f["nfranja"] = int(g["franja"].sum())
            Ep, _ = M.E(sitio, d0, slots, g["Wc"], g["R"], estim=estim)
            f["placebo_z"] = H.zrob(Ep, [M.E(sitio, d, slots, g["Wc"], g["R"], estim=estim)[0] for d in nulos])[0]
            fa = []
            for d, v in En.items():
                if np.isfinite(v):
                    zi = H.zrob(v, [w for dd, w in En.items() if dd != d])[0]
                    if np.isfinite(zi):
                        fa.append(zi <= H.Z_UMBRAL)
            f["fa_n"], f["fa_det"] = len(fa), int(np.sum(fa))
            for nombre, eps, masc, izz in [("poder_W_0.15", 0.15, None, iz), ("poder_franja_0.15", 0.15, g["franja"], iz),
                                           ("poder_franja_0.30", 0.30, g["franja"], iz),
                                           ("poder_franja_0.50", 0.50, g["franja"], iz),
                                           ("poder_grande", 0.9, None, -1)]:
                det = []
                for d, v in En.items():
                    if not np.isfinite(v):
                        continue
                    Tt = {s: Tz[d, s, izz] for s in slots}
                    if not all(np.isfinite(t) for t in Tt.values()):
                        continue
                    Ei = M.E(sitio, d, slots, g["W"], g["R"], estim=estim,
                             iny_por_slot={s: (eps, Tt[s]) for s in slots}, masc=masc)[0]
                    zi = H.zrob(Ei, [w for dd, w in En.items() if dd != d])[0]
                    if np.isfinite(zi):
                        det.append(zi <= H.Z_UMBRAL)
                f[nombre] = float(np.mean(det)) if det else np.nan
                f[nombre + "_n"] = len(det)
        f["clase"] = clase(f)
        filas.append(f)
        print(eid, estim, f["clase"], "z", f["chillan_z"], "cuadros", f["chillan_cuadros"], "nulo", f["chillan_nnulo"],
              "franja030", f.get("poder_franja_0.30"), "W015", f.get("poder_W_0.15"), "placebo", f.get("placebo_z"),
              "antuco", f["antuco_z"], "longavi", f["longavi_z"], flush=True)
    return filas


def clase(f):
    if not f["chillan_cuadros"] >= H.MIN_CUADROS:
        return "SIN DATO (cielo)"
    p = f.get("poder_franja_0.30", np.nan)
    if f["chillan_nnulo"] < H.MIN_NULO or not np.isfinite(p) or p < H.PODER_MIN or not np.isfinite(f["chillan_z"]):
        return "SIN PODER"
    if f["chillan_z"] > H.Z_UMBRAL:
        return "SIN SEÑAL"
    plac = np.isfinite(f["placebo_z"]) and f["placebo_z"] <= H.Z_UMBRAL
    cum = any(np.isfinite(f[f"{s}_z"]) and f[f"{s}_z"] <= H.Z_UMBRAL for s in ("antuco", "longavi"))
    return "DUDOSO" if (plac or cum) else "SEÑAL"


def main():
    r14, r15, acm, co14, co15 = H.cargar()
    M = MotorX(r14, r15, acm, co14, co15)
    alturas = sorted({H.CRATER_KM * 1000 + e[3] for e in H.EPISODIOS})
    Tz = H.gfs_t(alturas + [10000.0])
    ven = H.ventanas()
    filas = []
    for e in H.EPISODIOS:
        filas += episodio(M, Tz, e, ven, alturas.index(H.CRATER_KM * 1000 + e[3]))
    claves = sorted({k for f in filas for k in f}, key=lambda k: (k not in ("ep", "estim"), k))
    with open(os.path.join(H.RES, "h24_explorar.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, claves)
        w.writeheader()
        w.writerows(filas)
    res = {"enmienda_commit": "7c138fa", "rotulo": "EXPLORATORIO, no decide"}
    for estim in ("mediana", "p20"):
        fs = [f for f in filas if f["estim"] == estim]
        fa_n, fa_d = sum(f["fa_n"] for f in fs), sum(f["fa_det"] for f in fs)
        altos = [f for f in fs if f["grupo"] == "alto"]
        sen = sum(f["clase"] == "SEÑAL" for f in altos)
        dec = sum(f["clase"] in ("SEÑAL", "SIN SEÑAL") for f in altos)
        tasa = fa_d / fa_n if fa_n else float("nan")
        grande = all((not np.isfinite(f["poder_grande"])) or f["poder_grande"] >= H.PODER_GRANDE for f in fs)
        if not (tasa <= H.FA_MAX) or not grande:
            v = "INVÁLIDO"
        elif sen >= 2 and sen >= 0.5 * dec:
            v = "LOS PULSOS ALTOS SE VEN"
        elif dec >= 3 and sen == 0:
            v = "NI LOS PULSOS ALTOS SE VEN"
        else:
            v = "NO CONCLUYENTE"
        res[estim] = {"veredicto_exploratorio": v, "falsas_alarmas": [fa_d, fa_n, tasa], "control_grande_ok": grande,
                      "altos_decidibles": dec, "altos_senal": sen, "clases": {f["ep"]: f["clase"] for f in fs}}
    json.dump(res, open(os.path.join(H.RES, "h24_explorar_resumen.json"), "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
