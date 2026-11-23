r"""H29: implementa criterio_2026-11-23.md (commit b10f694) con la enmienda 1 (antes de medir el 08-11):
nulo A por rango, potencia por rango y capa oculta bajo nube mas fria.

Pregunta: los pixeles que VOLCAT publica a mas de 30 km del crater el 08-11 (20:10 a 22:00 UTC), tienen firma de
ceniza en 11 y 12 um? M1: BTD contra pixeles del mismo cuadro con la misma BT11 observada y la misma cota. M2: BT11
contra el anillo vecino de la misma cota. Nulo A: los mismos pixeles en dias sin evento (todo cielo). Nulo B: la
huella corrida dentro del 08-11. Control positivo: una pluma de emisividad eps que llena la fraccion f del pixel.

Por que asi: a esas horas no hay dias despejados para una linea base del pixel (preparar_resumen.json); los
contrastes dentro del cuadro quitan el modo comun sin necesitarla (H22, H24).

Uso: python -I h29_medir.py pruebas | seco | medir
"""
import csv
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import h29_comun as C  # noqa: E402
sys.path.insert(0, os.path.join(AQUI, "..", "..", "h24_pulsos_reav", "scripts"))
import h24_medir as H24  # noqa: E402  (cargar() y gfs_t(): cubos y GFS de 21-09 a 21-11)

T0, NDIAS = H24.T0, H24.NDIAS
assert T0 == datetime(2026, 9, 21) and NDIAS == 62
DIA = {k: (datetime.strptime(k, "%Y-%m-%d") - T0).days for k in ("2026-11-08", "2026-11-04")}
NULOS_TXT = ["2026-10-18", "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-23", "2026-10-26", "2026-10-31",
             "2026-11-01", "2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05", "2026-11-09", "2026-11-15",
             "2026-11-17", "2026-11-19", "2026-11-20", "2026-11-21"]
NULOS = [(datetime.strptime(s, "%Y-%m-%d") - T0).days for s in NULOS_TXT]

# ---------- parametros del criterio ----------
LEJOS_KM, MEDIO_KM = 30.0, 15.0
PAR_K, COTA_M, EXCL_PX, MIN_PAR = 0.5, 300.0, 4, 10           # M1
ANI_MIN, ANI_MAX, MIN_ANI = 2.0, 8.0, 8                       # M2
MIN_PC, MIN_NULO, MIN_CORR, MAX_CORR = 10, 6, 30, 25
Z_SEN, Z_NUL, P_SEN, P_NUL, POT_MIN, FA_MAX = -2.0, -1.0, 0.05, 0.20, 0.80, 0.10
BETA = 0.70
REF = (0.4, 0.5)
F_GRID = [0.1, 0.2, 0.4, 0.7, 1.0]
E_GRID = [0.1, 0.3, 0.5, 0.9]
H_DEFECTO = 3.0
Z = C.ZDEM.ravel()
FILA, COL = np.divmod(np.arange(C.NY * C.NX), C.NX)


def zrob(x, nulo):
    nulo = np.asarray([v for v in nulo if np.isfinite(v)])
    if len(nulo) < MIN_NULO or not np.isfinite(x):
        return np.nan
    med = np.median(nulo)
    mad = 1.4826 * np.median(np.abs(nulo - med))
    return (x - med) / mad if mad > 1e-6 else np.nan


# ---------- huella ----------
def huellas(variante):
    """Dict slot -> mascara (NY, NX) y altura (NY, NX) de la variante 'h14', 'nom' o 'dil' (h14 dilatada 1 px)."""
    z = np.load(os.path.join(C.TRABAJO, "huella_0811.npz"))
    out = {}
    for k in z.files:
        if not k.startswith("h14_"):
            continue
        hhmm = k[4:]
        s = int(hhmm[:2]) * 6 + int(hhmm[2:]) // 10
        if variante == "dil":
            m = ndimage.binary_dilation(z[k], iterations=1)
            h = z[f"alt_h14_{hhmm}"].copy()
            h = np.where(m & ~z[k], np.nan, h)
        else:
            m, h = z[f"{variante}_{hhmm}"], z[f"alt_{variante}_{hhmm}"]
        out[s] = (m, h)
    return out


def poblacion(hu, dmin, dmax):
    """Lista de (slot, pixel plano, altura km) de la huella con distancia en (dmin, dmax]."""
    pc = []
    for s, (m, h) in sorted(hu.items()):
        sel = m & (C.DIST > dmin) & (C.DIST <= dmax)
        for p in np.flatnonzero(sel.ravel()):
            hk = h.ravel()[p]
            pc.append((s, int(p), float(hk) if np.isfinite(hk) else H_DEFECTO))
    return pc


def mascaras_excl(hu):
    """Por slot: exclusion de pares (union de huellas a +-20 min dilatada 4 px) y del anillo (huella del cuadro
    dilatada 1 px). Mas la union de todo el dia (para validar corrimientos del nulo B)."""
    ex4, ex1 = {}, {}
    todas = np.zeros((C.NY, C.NX), bool)
    for s, (m, _) in hu.items():
        todas |= m
    for s in hu:
        u = np.zeros((C.NY, C.NX), bool)
        for ss in range(s - 2, s + 3):
            if ss in hu:
                u |= hu[ss][0]
        ex4[s] = ndimage.binary_dilation(u, iterations=EXCL_PX).ravel() if u.any() else u.ravel()
        ex1[s] = ndimage.binary_dilation(hu[s][0], iterations=1).ravel() if hu[s][0].any() else hu[s][0].ravel()
    return ex4, ex1, ndimage.binary_dilation(todas, iterations=EXCL_PX)


# ---------- medidas ----------
class Medidor:
    def __init__(self, r14, r15, co14, co15, Tgfs, alturas):
        self.r14, self.r15, self.co14, self.co15 = r14, r15, co14, co15
        self.bt11 = C.bt_de_rad(r14.astype("float64"), co14).astype("float32")
        self.btd = (self.bt11 - C.bt_de_rad(r15.astype("float64"), co15)).astype("float32")
        self.Tgfs, self.alturas = Tgfs, alturas

    def pintar(self, d, s, p, hk, f, eps):
        """BT11 y BTD del pixel p con la pluma (f, eps) a la T del GFS de la altura hk."""
        Tt = self.Tgfs[d, s, self.alturas.index(round(hk * 1000))]
        if not np.isfinite(Tt):
            return np.nan, np.nan
        if float(self.bt11[d, s, p]) <= Tt:          # enmienda 1: bajo algo mas frio, la capa no se ve
            return float(self.bt11[d, s, p]), float(self.btd[d, s, p])
        e11, e12 = f * eps, f * (1 - (1 - eps) ** BETA)
        I14 = (1 - e11) * float(self.r14[d, s, p]) + e11 * C.rad_de_bt(Tt, self.co14)
        I15 = (1 - e12) * float(self.r15[d, s, p]) + e12 * C.rad_de_bt(Tt, self.co15)
        b11 = float(C.bt_de_rad(I14, self.co14))
        return b11, b11 - float(C.bt_de_rad(I15, self.co15))

    def medir(self, d, s, p, ex4, ex1, extra=None, iny=None, hk=None):
        """(M1, M2) de un pixel-cuadro. extra: pixeles a excluir ademas (huella corrida del nulo B)."""
        bt, bd = self.bt11[d, s], self.btd[d, s]
        if iny is None:
            b11, bdd = float(bt[p]), float(bd[p])
        else:
            b11, bdd = self.pintar(d, s, p, hk, *iny)
        if not (np.isfinite(b11) and np.isfinite(bdd)):
            return np.nan, np.nan
        cota = np.abs(Z - Z[p]) <= COTA_M
        ok = np.isfinite(bt) & np.isfinite(bd) & cota
        base1 = ok & ~ex4
        base2 = ok & ~ex1
        if extra is not None:
            base1 &= ~extra
            base2 &= ~extra
        par = base1 & (np.abs(bt - b11) <= PAR_K)
        m1 = bdd - float(np.median(bd[par])) if par.sum() >= MIN_PAR else np.nan
        r = np.hypot(FILA - FILA[p], COL - COL[p])
        ani = base2 & (r >= ANI_MIN) & (r <= ANI_MAX)
        m2 = b11 - float(np.median(bt[ani])) if ani.sum() >= MIN_ANI else np.nan
        return m1, m2

    def estadistico(self, d, pc, ex4, ex1, iny=None, corr=None, extra=None):
        """Mediana de M1 y M2 sobre los pixeles-cuadro validos; NaN si hay menos de MIN_PC. corr = (dr, dc)."""
        v1, v2 = [], []
        for s, p, hk in pc:
            q = p if corr is None else int((FILA[p] + corr[0]) * C.NX + COL[p] + corr[1])
            m1, m2 = self.medir(d, s, q, ex4[s], ex1[s], extra=None if extra is None else extra.get(s),
                                iny=iny, hk=hk)
            v1.append(m1)
            v2.append(m2)
        v1, v2 = np.array(v1), np.array(v2)
        e = [float(np.median(v[np.isfinite(v)])) if np.isfinite(v).sum() >= MIN_PC else np.nan for v in (v1, v2)]
        return e[0], e[1], int(np.isfinite(v1).sum()), int(np.isfinite(v2).sum())


def corrimientos(pc, todas):
    """(dr, dc) validos para el nulo B: todos los pixeles dentro de la ventana y a >= 4 px de toda huella del dia."""
    out = []
    for dr in range(-MAX_CORR, MAX_CORR + 1):
        for dc in range(-MAX_CORR, MAX_CORR + 1):
            if (dr, dc) == (0, 0):
                continue
            ok = True
            for _, p, _ in pc:
                r, c = FILA[p] + dr, COL[p] + dc
                if not (0 <= r < C.NY and 0 <= c < C.NX) or todas[r, c]:
                    ok = False
                    break
            if ok:
                out.append((dr, dc))
    return out


def bajo_min(x, nulo):
    """Enmienda 1: lado de senal temporal = bajo el minimo del nulo."""
    nulo = [v for v in nulo if np.isfinite(v)]
    return (np.isfinite(x) and len(nulo) >= MIN_NULO and x < min(nulo)) if nulo else False


def clase(e, nulo, p, pot):
    nulo = [v for v in nulo if np.isfinite(v)]
    if not (np.isfinite(e) and np.isfinite(p)) or len(nulo) < MIN_NULO:
        return "SIN DATO"
    sz, sp = e < min(nulo), p <= P_SEN
    if sz and sp:
        return "SEÑAL"
    if sz or sp:
        return "SOSPECHA"
    if e >= np.percentile(nulo, 25) and p > P_NUL:
        return "SIN FIRMA" if (np.isfinite(pot) and pot >= POT_MIN) else "SIN PODER"
    return "NO CONCLUYENTE"


def correr(M, dia_ev, variante, dmin, dmax, potencia=True, nulo_b=True):
    hu = huellas(variante)
    pc = poblacion(hu, dmin, dmax)
    ex4, ex1, todas = mascaras_excl(hu)
    nulos = [d for d in NULOS if d != dia_ev]
    out = {"variante": variante, "dist": [dmin, dmax], "dia_ev": f"{T0 + timedelta(days=dia_ev):%Y-%m-%d}",
           "n_pixeles_cuadro": len(pc), "slots": sorted({s for s, _, _ in pc})}
    e1, e2, n1, n2 = M.estadistico(dia_ev, pc, ex4, ex1)
    out.update(E_M1=e1, E_M2=e2, validos_M1=n1, validos_M2=n2)
    En = {d: M.estadistico(d, pc, ex4, ex1) for d in nulos}
    for k, i in (("M1", 0), ("M2", 1)):
        vals = {d: v[i] for d, v in En.items()}
        out[f"nulo_{k}"] = {f"{T0 + timedelta(days=d):%m-%d}": (round(v, 3) if np.isfinite(v) else None)
                            for d, v in vals.items()}
        out[f"nulo_{k}_validos"] = int(sum(np.isfinite(v) for v in vals.values()))
        out[f"z_{k}"] = zrob(out[f"E_{k}"], list(vals.values()))     # informativo (enmienda 1)
        fin = [v for v in vals.values() if np.isfinite(v)]
        out[f"nulo_{k}_min_p25_med"] = [round(float(x), 3) for x in (min(fin), np.percentile(fin, 25), np.median(fin))] if fin else []
        out[f"rango_{k}"] = int(sum(v <= out[f"E_{k}"] for v in fin)) if np.isfinite(out[f"E_{k}"]) else None
        fa = [bajo_min(v, [w for dd, w in vals.items() if dd != d]) for d, v in vals.items() if np.isfinite(v)]
        out[f"fa_{k}"] = (int(sum(fa)), len(fa))
    if nulo_b:
        cs = corrimientos(pc, todas)
        eb1, eb2 = [], []
        for dr, dc in cs:
            extra = {}
            for s, p, _ in pc:
                q = int((FILA[p] + dr) * C.NX + COL[p] + dc)
                extra.setdefault(s, np.zeros(C.NY * C.NX, bool))[q] = True
            ex = {s: ndimage.binary_dilation(v.reshape(C.NY, C.NX), iterations=1).ravel() for s, v in extra.items()}
            # pares: fuera de la huella real (ex4) y de la corrida (sin dilatar); anillo: fuera de ambas dilatadas 1 px
            b1, b2 = [], []
            for s, p, _ in pc:
                q = int((FILA[p] + dr) * C.NX + COL[p] + dc)
                m1, _ = M.medir(dia_ev, s, q, ex4[s], ex1[s], extra=extra[s])
                _, m2 = M.medir(dia_ev, s, q, ex4[s], ex1[s] | ex[s])
                b1.append(m1)
                b2.append(m2)
            b1, b2 = np.array(b1), np.array(b2)
            eb1.append(float(np.median(b1[np.isfinite(b1)])) if np.isfinite(b1).sum() >= MIN_PC else np.nan)
            eb2.append(float(np.median(b2[np.isfinite(b2)])) if np.isfinite(b2).sum() >= MIN_PC else np.nan)
        for k, eb in (("M1", eb1), ("M2", eb2)):
            eb = np.array([x for x in eb if np.isfinite(x)])
            out[f"corr_{k}_validos"] = int(len(eb))
            out[f"corr_{k}_cuartiles"] = [round(float(q), 3) for q in np.percentile(eb, [5, 25, 50, 75, 95])] if len(eb) else []
            out[f"p_{k}"] = float(np.mean(eb <= out[f"E_{k}"])) if (len(eb) >= MIN_CORR and np.isfinite(out[f"E_{k}"])) else np.nan
    if potencia:
        grid = {}
        for f in F_GRID:
            for eps in E_GRID:
                det = {"M1": [], "M2": []}
                for d in nulos:
                    if not np.isfinite(En[d][0]) and not np.isfinite(En[d][1]):
                        continue
                    i1, i2, _, _ = M.estadistico(d, pc, ex4, ex1, iny=(f, eps))
                    for k, i, iv in (("M1", 0, i1), ("M2", 1, i2)):
                        if np.isfinite(iv):
                            det[k].append(bajo_min(iv, [v[i] for dd, v in En.items() if dd != d]))
                grid[f"{f:.1f}x{eps:.1f}"] = {k: (round(float(np.mean(v)), 3) if v else None, len(v)) for k, v in det.items()}
        out["potencia"] = grid
        ref = grid[f"{REF[0]:.1f}x{REF[1]:.1f}"]
        out["pot_ref_M1"], out["pot_ref_M2"] = ref["M1"][0], ref["M2"][0]
        for k in ("M1", "M2"):
            lim = [f * e for f in F_GRID for e in E_GRID
                   if grid[f"{f:.1f}x{e:.1f}"][k][0] is not None and grid[f"{f:.1f}x{e:.1f}"][k][0] >= POT_MIN]
            out[f"limite_fe_{k}"] = min(lim) if lim else None
    for k in ("M1", "M2"):
        fa_n, fa_t = out[f"fa_{k}"]
        if fa_t and fa_n / fa_t > FA_MAX:
            out[f"clase_{k}"] = "INVÁLIDO"
        elif out[f"validos_{k}"] < MIN_PC or out[f"nulo_{k}_validos"] < MIN_NULO or \
                (nulo_b and out.get(f"corr_{k}_validos", 0) < MIN_CORR):
            out[f"clase_{k}"] = "SIN DATO"
        else:
            out[f"clase_{k}"] = clase(out[f"E_{k}"], [v[0 if k == "M1" else 1] for v in En.values()],
                                      out.get(f"p_{k}", np.nan), out.get(f"pot_ref_{k}", np.nan))
    return out


def descriptivo(M, acm, dia_ev, pc):
    """Informativo, no decide: BT11 y BTD absolutas de los pixeles lejanos, T del GFS a la altura VOLCAT, ACMF."""
    filas = []
    for s, p, hk in pc:
        Tt = M.Tgfs[dia_ev, s, M.alturas.index(round(hk * 1000))]
        filas.append({"hora": f"{s // 6:02d}:{s % 6 * 10:02d}", "dist_km": round(float(C.DIST.ravel()[p]), 1),
                      "cota_m": round(float(Z[p])), "alt_volcat_km": hk, "T_gfs_K": round(float(Tt), 1),
                      "BT11_K": round(float(M.bt11[dia_ev, s, p]), 2), "BTD_K": round(float(M.btd[dia_ev, s, p]), 2),
                      "acm": int(acm[dia_ev, s, p])})
    return filas


def pruebas():
    co = np.array([8.5e3, 1.2858e3, 0.2105, 0.99925])
    T = np.array([250.0, 270.0, 290.0])
    assert np.allclose(C.bt_de_rad(C.rad_de_bt(T, co), co), T, atol=1e-6)
    I = C.rad_de_bt(280.0, co)
    for fe, esp in ((0.0, 280.0), (1.0, 250.0)):
        I2 = (1 - fe) * I + fe * C.rad_de_bt(250.0, co)
        assert abs(float(C.bt_de_rad(I2, co)) - esp) < 1e-6
    a = np.zeros((C.NY, C.NX), bool)
    a[10, 20] = True
    b, _ = C.corre(a, np.where(a, 1.0, np.nan), (-1, -1))
    assert b[9, 19] and b.sum() == 1
    assert zrob(-3.0, [0, 1, -1, 0.5, -0.5, 0.2, -0.2]) < -2 and np.isnan(zrob(-3.0, [0, 1]))
    hu = huellas("h14")
    pc = poblacion(hu, LEJOS_KM, 1e9)
    assert len(pc) == 17, len(pc)
    print("pruebas OK (5 de 5); pixeles-cuadro lejanos:", len(pc))


def main(modo):
    pruebas()
    if modo == "pruebas":
        return
    r14, r15, acm, co14, co15 = H24.cargar()
    alturas = sorted({round(h * 1000) for v in ("h14", "nom", "dil")
                      for _, _, h in poblacion(huellas(v), MEDIO_KM, 1e9)} | {round(H_DEFECTO * 1000)})
    Tgfs = H24.gfs_t([float(a) for a in alturas])
    M = Medidor(r14, r15, co14, co15, Tgfs, alturas)
    os.makedirs(C.RES, exist_ok=True)
    if modo == "seco":
        res = correr(M, DIA["2026-11-04"], "h14", LEJOS_KM, 1e9)
        json.dump(res, open(os.path.join(C.RES, "seco_0411.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False,
                  default=float)
        print(json.dumps({k: v for k, v in res.items() if k not in ("potencia",)}, ensure_ascii=False, default=float))
        print("potencia:", json.dumps(res["potencia"]))
        return
    d0 = DIA["2026-11-08"]
    todo = {"criterio_commit": "b10f694", "enmienda_1": "ver git log"}
    todo["principal"] = correr(M, d0, "h14", LEJOS_KM, 1e9)
    print("principal", {k: todo["principal"].get(k) for k in ("E_M1", "E_M2", "z_M1", "z_M2", "p_M1", "p_M2",
                                                             "pot_ref_M1", "pot_ref_M2", "clase_M1", "clase_M2")}, flush=True)
    for v in ("nom", "dil"):
        todo[f"sens_{v}"] = correr(M, d0, v, LEJOS_KM, 1e9, potencia=(v == "dil"))
        print(v, {k: todo[f"sens_{v}"].get(k) for k in ("E_M1", "E_M2", "z_M1", "z_M2", "p_M1", "p_M2", "clase_M1", "clase_M2")}, flush=True)
    todo["info_15_30km"] = correr(M, d0, "h14", MEDIO_KM, LEJOS_KM)
    print("15-30", {k: todo["info_15_30km"].get(k) for k in ("E_M1", "E_M2", "z_M1", "z_M2", "p_M1", "p_M2", "clase_M1", "clase_M2")}, flush=True)
    json.dump(todo, open(os.path.join(C.RES, "h29_resultado.json"), "w", encoding="utf-8"), indent=1,
              ensure_ascii=False, default=float)
    # descriptivo por pixel-cuadro: va a D: (lleva posicion implicita via distancia/cota); al repo solo agregados
    pc = poblacion(huellas("h14"), LEJOS_KM, 1e9)
    filas = descriptivo(M, acm, d0, pc)
    with open(os.path.join(C.TRABAJO, "descriptivo_lejanos.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print(json.dumps(filas, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "medir")
