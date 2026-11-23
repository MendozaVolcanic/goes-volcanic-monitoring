r"""H25 (S19): E6 (explosion de 2.000 m del 27-10, 09:26 UTC) con la direccion del viento GFS en vez de la del REAV.

Pregunta: si la pluma de E6 se fue hacia el NNE (GFS 16,9 grados, 6,9 m/s; tabla de H10) y no hacia el NO (REAV,
315 grados), la BTD contra la linea base del propio pixel baja en ESE sector mas que en el viento cruzado, y mas que
en dias sin pulso? Implementa criterio_2026-11-23.md sin cambios.

Por que asi: H24 dio E6 SIN SEÑAL con la direccion del REAV; el GFS estaba a 62 grados y con un sector de +-30 la
pluma se habria perdido en buena parte. Se reutiliza el motor de H24 (h24_medir.py) tal cual: mismo cubo, misma
linea base, mismo pareo por BT11 esperada, misma inyeccion; cambian la direccion, la referencia R (sin los pixeles a
+-30 grados de la direccion del REAV, que quedaban dentro del viento cruzado) y las falsas alarmas (5 ventanas).

Uso: python -I h25_medir.py pruebas | conteo | (sin argumento = medir)
"""
import csv
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "h24_pulsos_reav", "scripts"))
import h24_medir as H  # noqa: E402  (motor de H24, sin cambios)

# ---------- parametros del criterio (§4 a §6) ----------
EP = "E6"
H_M = 2000                       # m sobre el crater (REAV)
DIR_GFS = 16.9                   # hacia, grados (H10 tabla_direccion_h10.json, reav_gfs E6, gfs_hacia)
DIR_REAV = 315.0                 # la que uso H24
EXCL_REAV = 30.0                 # R pierde los pixeles a <= 30 grados de DIR_REAV
DESPLAZ = [-2, -1, 0, 1, 2]      # ventanas de falsas alarmas: la de E6 corrida en horas
FRANJA_KM = 3.0
EPS_W = [0.05, 0.10, 0.15, 0.30]
EPS_FRANJA = [0.15, 0.30]


def sectores25(sitio, direc=DIR_GFS, Hm=H_M, excl=DIR_REAV):
    """W, Wc y R de H24 para la direccion dada; R sin los pixeles a <= 30 grados de `excl` (None = R de H24).
    Ademas la franja de +-3 km alrededor del eje dentro de W (mascara booleana sobre W)."""
    g = H.sectores(sitio, direc, Hm)
    la, lo = H.VENT if sitio == "chillan" else H.SITIOS[sitio][:2]
    h = H.CRATER_KM + Hm / 1000.0
    lejos = (H.rumbo(la, lo, *H.SUBSAT) + 180.0) % 360.0
    x, y = H.plano(la, lo)
    x = x - H.PARALAJE * h * np.sin(np.radians(lejos))
    y = y - H.PARALAJE * h * np.cos(np.radians(lejos))
    az = np.degrees(np.arctan2(x, y)) % 360
    if excl is not None:
        g["R"] = g["R"][H.angdif(az[g["R"]], excl) > EXCL_REAV]
    ux, uy = np.sin(np.radians(direc)), np.cos(np.radians(direc))
    g["franja"] = np.abs(x * uy - y * ux)[g["W"]] <= FRANJA_KM
    return g


class Motor25(H.Motor):
    """Motor de H24 con inyeccion restringible a una mascara de W (franja). Sin mascara es identico a H.Motor."""

    def S_cuadro(self, sitio, d, s, W, R, det="D2", par="esperada", iny=None, masc=None):
        if masc is None:
            return super().S_cuadro(sitio, d, s, W, R, det=det, par=par, iny=iny)
        if not self.F[sitio][d, s]:
            return np.nan
        px = np.concatenate([W, R])
        r11, rd = self.base(sitio, d, s, px)
        eps, Tt = iny
        I14 = self.r14[d, s, px].astype(float)
        I15 = self.r15[d, s, px].astype(float)
        e12 = 1 - (1 - eps) ** H.BETA
        m = np.zeros(len(px), bool)
        m[:len(W)] = masc
        I14[m] = (1 - eps) * I14[m] + eps * H.rad_de_bt(Tt, self.co14)
        I15[m] = (1 - e12) * I15[m] + e12 * H.rad_de_bt(Tt, self.co15)
        bt11 = H.bt_de_rad(I14, self.co14)
        x = (bt11 - H.bt_de_rad(I15, self.co15)) - rd
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
        return float(np.median(dif)) if len(dif) >= H.MIN_W else np.nan

    def E(self, sitio, d, slots, W, R, det="D2", par="esperada", iny_por_slot=None, masc=None):
        Ss = []
        for s in slots:
            iny = None if iny_por_slot is None else iny_por_slot[s]
            v = self.S_cuadro(sitio, d, s, W, R, det=det, par=par, iny=iny, masc=masc)
            if np.isfinite(v):
                Ss.append(v)
        return (float(np.median(Ss)) if len(Ss) >= H.MIN_CUADROS else np.nan), len(Ss)


def ventana_e6():
    d0, slots = H.ventanas()[EP]
    nulos = [d for d in range(max(0, d0 - H.VENT_DIAS), min(H.NDIAS, d0 + H.VENT_DIAS + 1))
             if d != d0 and not H.DIA_EXCL[d]]
    return d0, slots, nulos


def corrida(slots, k):
    return [s + 6 * k for s in slots]


def pruebas():
    """Geometria: W, Wc, R disjuntos; R sin pixeles cerca de 315; franja dentro de W; sin mascara = motor de H24."""
    H.pruebas()
    g = sectores25("chillan")
    W, Wc, R = set(g["W"]), set(g["Wc"]), set(g["R"])
    assert not (W & R) and not (Wc & R) and not (W & Wc)
    g24 = sectores25("chillan", excl=None)
    assert set(g["R"]) < set(g24["R"]) and set(g["W"]) == set(g24["W"])
    lejos = (H.rumbo(*H.VENT, *H.SUBSAT) + 180.0) % 360.0
    x, y = H.plano(*H.VENT)
    h = H.CRATER_KM + H_M / 1000.0
    x = x - H.PARALAJE * h * np.sin(np.radians(lejos))
    y = y - H.PARALAJE * h * np.cos(np.radians(lejos))
    az = np.degrees(np.arctan2(x, y)) % 360
    assert np.all(H.angdif(az[g["R"]], DIR_REAV) > EXCL_REAV)
    assert np.all(H.angdif(az[g["W"]], DIR_GFS) <= H.SEMI_W)
    assert 0 < g["franja"].sum() < len(g["W"])
    d0, slots, nulos = ventana_e6()
    assert slots == [9 * 6 + 2, 9 * 6 + 3, 9 * 6 + 4, 9 * 6 + 5, 10 * 6 + 0, 10 * 6 + 1], slots
    assert all(0 <= s < 144 for k in DESPLAZ for s in corrida(slots, k))
    print("pruebas H25 OK; W, Wc, R (sin 315), R de H24, franja:", len(g["W"]), len(g["Wc"]), len(g["R"]),
          len(g24["R"]), int(g["franja"].sum()))
    for s in ("antuco", "longavi"):
        gs = sectores25(s)
        print(f"  {s}: W {len(gs['W'])}, Wc {len(gs['Wc'])}, R {len(gs['R'])}")


def conteo(M):
    """Antes de medir: dias de fondo por ventana (dias nulos con >= 2 cuadros despejados y con linea base) y
    cuadros despejados de E6. No calcula ningun estadistico de deteccion."""
    d0, slots, nulos = ventana_e6()
    out = {"dia_e6": str(H.T0.date() + __import__("datetime").timedelta(days=d0)), "slots_e6": slots,
           "nulos_candidatos": len(nulos)}
    for sitio in H.SITIOS:
        F = M.F[sitio]
        fila = {"e6_cuadros_despejados": int(F[d0, slots].sum())}
        for k in DESPLAZ:
            sl = corrida(slots, k)
            fila[f"k{k:+d}_dias_con_2_despejados"] = int(sum(F[d, sl].sum() >= H.MIN_CUADROS for d in nulos))
        out[sitio] = fila
    print(json.dumps(out, indent=1, ensure_ascii=False))
    return out


def medir(M, Tz):
    d0, slots, nulos = ventana_e6()
    f = {"ep": EP, "H": H_M, "dir_gfs": DIR_GFS, "dir_reav_excluida_de_R": DIR_REAV, "dia": str(d0),
         "nulos_candidatos": len(nulos)}
    En_por = {}
    for sitio in H.SITIOS:
        g = sectores25(sitio)
        f[f"{sitio}_nW"], f[f"{sitio}_nR"] = len(g["W"]), len(g["R"])
        Ee, nc = M.E(sitio, d0, slots, g["W"], g["R"])
        En = {d: M.E(sitio, d, slots, g["W"], g["R"])[0] for d in nulos}
        z, nn, mad = H.zrob(Ee, list(En.values()))
        f[f"{sitio}_E"], f[f"{sitio}_cuadros"], f[f"{sitio}_z"], f[f"{sitio}_nnulo"], f[f"{sitio}_mad"] = Ee, nc, z, nn, mad
        En_por[sitio] = En
    g = sectores25("chillan")
    En = En_por["chillan"]
    # placebo contra el viento
    Ep, _ = M.E("chillan", d0, slots, g["Wc"], g["R"])
    f["placebo_E"], f["placebo_z"] = Ep, H.zrob(Ep, [M.E("chillan", d, slots, g["Wc"], g["R"])[0] for d in nulos])[0]
    # falsas alarmas en 5 ventanas
    fa_n, fa_det = 0, 0
    for k in DESPLAZ:
        sl = corrida(slots, k)
        Ek = En if k == 0 else {d: M.E("chillan", d, sl, g["W"], g["R"])[0] for d in nulos}
        n_k, det_k = 0, 0
        for d, v in Ek.items():
            if np.isfinite(v):
                zi = H.zrob(v, [w for dd, w in Ek.items() if dd != d])[0]
                if np.isfinite(zi):
                    n_k += 1
                    det_k += int(zi <= H.Z_UMBRAL)
        f[f"fa_k{k:+d}"] = f"{det_k}/{n_k}"
        fa_n += n_k
        fa_det += det_k
    f["fa_n"], f["fa_det"] = fa_n, fa_det
    f["fa_tasa"] = fa_det / fa_n if fa_n else np.nan
    # poder
    pruebas_poder = [(f"poder_W_{e:.2f}", e, None, 0) for e in EPS_W] + \
                    [(f"poder_franja_{e:.2f}", e, g["franja"], 0) for e in EPS_FRANJA] + [("poder_grande", 0.9, None, 1)]
    for nombre, eps, masc, iz in pruebas_poder:
        det = []
        for d, v in En.items():
            if not np.isfinite(v):
                continue
            Tt = {s: Tz[d, s, iz] for s in slots}
            if not all(np.isfinite(t) for t in Tt.values()):
                continue
            Ei = M.E("chillan", d, slots, g["W"], g["R"], iny_por_slot={s: (eps, Tt[s]) for s in slots}, masc=masc)[0]
            zi = H.zrob(Ei, [w for dd, w in En.items() if dd != d])[0]
            if np.isfinite(zi):
                det.append(zi <= H.Z_UMBRAL)
        f[nombre] = float(np.mean(det)) if det else np.nan
        f[nombre + "_n"] = len(det)
    # secundarias (informan, no deciden)
    for tag, kw in (("sec_D1", {"det": "D1"}), ("sec_par_observada", {"par": "observada"})):
        Ee, _ = M.E("chillan", d0, slots, g["W"], g["R"], **kw)
        f[tag + "_z"] = H.zrob(Ee, [M.E("chillan", d, slots, g["W"], g["R"], **kw)[0] for d in nulos])[0]
    g24 = sectores25("chillan", excl=None)
    Ee, _ = M.E("chillan", d0, slots, g24["W"], g24["R"])
    f["sec_R_de_H24_z"] = H.zrob(Ee, [M.E("chillan", d, slots, g24["W"], g24["R"])[0] for d in nulos])[0]
    return f


def clase(f):
    if f["fa_tasa"] > H.FA_MAX or not (f["poder_grande"] >= H.PODER_GRANDE):
        return "INVÁLIDO"
    if f["chillan_cuadros"] < H.MIN_CUADROS:
        return "SIN DATO (cielo)"
    if f["chillan_nnulo"] < H.MIN_NULO or not np.isfinite(f["chillan_z"]) or not (f["poder_W_0.15"] >= H.PODER_MIN):
        return "SIN PODER"
    z = f["chillan_z"]
    if z > H.Z_UMBRAL:
        return "SIN SEÑAL"
    plac = np.isfinite(f["placebo_z"]) and f["placebo_z"] <= H.Z_UMBRAL
    cumbre = any(np.isfinite(f[f"{s}_z"]) and f[f"{s}_z"] <= H.Z_UMBRAL for s in ("antuco", "longavi"))
    return "DUDOSO" if (plac or cumbre) else "SEÑAL"


def main(modo):
    if modo == "pruebas":
        pruebas()
        return
    pruebas()
    r14, r15, acm, co14, co15 = H.cargar()
    M = Motor25(r14, r15, acm, co14, co15)
    os.makedirs(RES, exist_ok=True)
    if modo == "conteo":
        out = conteo(M)
        json.dump(out, open(os.path.join(RES, "h25_conteo_fondo.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        return
    Tz = H.gfs_t([H.CRATER_KM * 1000 + H_M, 10000.0])
    f = medir(M, Tz)
    f["clase"] = clase(f)
    f = {k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in f.items()}
    json.dump(f, open(os.path.join(RES, "h25_resultado.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    with open(os.path.join(RES, "h25_resultado.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, list(f))
        w.writeheader()
        w.writerow(f)
    print(json.dumps(f, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "medir")
