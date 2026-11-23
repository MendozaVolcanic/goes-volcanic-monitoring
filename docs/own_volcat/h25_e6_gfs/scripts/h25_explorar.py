r"""H25, enmienda post hoc 1 (exploratoria, no decide): percentil 20 del sector en vez de la mediana, para ver plumas
angostas. Mismo fondo de +-21 dias que el criterio (no se amplia, como si hizo la enmienda 2 de H24).

Uso: python -I h25_explorar.py
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import h25_medir as M25  # noqa: E402
H = M25.H


class MotorP20(M25.Motor25):
    """Mismo calculo que el motor de H24 para D2 con pareo por BT11 esperada, con percentil 20 por cuadro."""

    def S_cuadro(self, sitio, d, s, W, R, det="D2", par="esperada", iny=None, masc=None):
        if not self.F[sitio][d, s]:
            return np.nan
        px = np.concatenate([W, R])
        r11, rd = self.base(sitio, d, s, px)
        if iny is None:
            btd = self.btd[d, s, px].astype(float)
        else:
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
        return float(np.percentile(dif, 20)) if len(dif) >= H.MIN_W else np.nan


def main():
    M25.pruebas()
    r14, r15, acm, co14, co15 = H.cargar()
    M = MotorP20(r14, r15, acm, co14, co15)
    d0, slots, nulos = M25.ventana_e6()
    g = M25.sectores25("chillan")
    Tz = H.gfs_t([H.CRATER_KM * 1000 + M25.H_M, 10000.0])
    f = {"estimador": "p20"}
    En = {}
    for sitio in ("chillan", "longavi"):
        gs = M25.sectores25(sitio)
        Ee, nc = M.E(sitio, d0, slots, gs["W"], gs["R"])
        Ens = {d: M.E(sitio, d, slots, gs["W"], gs["R"])[0] for d in nulos}
        f[f"{sitio}_E"], f[f"{sitio}_cuadros"] = Ee, nc
        f[f"{sitio}_z"], f[f"{sitio}_nnulo"], f[f"{sitio}_mad"] = H.zrob(Ee, list(Ens.values()))
        if sitio == "chillan":
            En = Ens
    Ep, _ = M.E("chillan", d0, slots, g["Wc"], g["R"])
    f["placebo_z"] = H.zrob(Ep, [M.E("chillan", d, slots, g["Wc"], g["R"])[0] for d in nulos])[0]
    fa_n = fa_det = 0
    for k in M25.DESPLAZ:
        sl = M25.corrida(slots, k)
        Ek = En if k == 0 else {d: M.E("chillan", d, sl, g["W"], g["R"])[0] for d in nulos}
        n_k = det_k = 0
        for d, v in Ek.items():
            if np.isfinite(v):
                zi = H.zrob(v, [w for dd, w in Ek.items() if dd != d])[0]
                if np.isfinite(zi):
                    n_k += 1
                    det_k += int(zi <= H.Z_UMBRAL)
        f[f"fa_k{k:+d}"] = f"{det_k}/{n_k}"
        fa_n += n_k
        fa_det += det_k
    f["fa_n"], f["fa_det"], f["fa_tasa"] = fa_n, fa_det, fa_det / fa_n if fa_n else np.nan
    for nombre, eps, masc, iz in [("poder_W_0.05", 0.05, None, 0), ("poder_W_0.15", 0.15, None, 0),
                                  ("poder_franja_0.15", 0.15, g["franja"], 0), ("poder_franja_0.30", 0.30, g["franja"], 0),
                                  ("poder_franja_0.50", 0.50, g["franja"], 0), ("poder_grande", 0.9, None, 1)]:
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
        f[nombre], f[nombre + "_n"] = (float(np.mean(det)) if det else np.nan), len(det)
    valida = f["fa_tasa"] <= H.FA_MAX and f["poder_grande"] >= H.PODER_GRANDE
    if not valida:
        lect = "INVÁLIDA"
    elif not (f["poder_franja_0.15"] >= H.PODER_MIN):
        lect = "PLUMA ANGOSTA SIN PODER"
    elif f["chillan_z"] > H.Z_UMBRAL:
        lect = "SIN SEÑAL (también pluma angosta)"
    else:
        lect = "DUDOSO" if (f["placebo_z"] <= H.Z_UMBRAL or (np.isfinite(f["longavi_z"]) and f["longavi_z"] <= H.Z_UMBRAL)) else "SEÑAL (exploratoria)"
    f["lectura"] = lect
    f = {k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in f.items()}
    json.dump(f, open(os.path.join(M25.RES, "h25_explorar.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(f, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
