r"""S20b, prueba 1 (TER-01 y TER-02): la pluma de huella conocida por Sentinel-2 o Landsat, puesta en la grilla ABI
con su fraccion de pixel f, deja firma en BT11 o en la BTD (11 - 12 um) del cuadro GOES-19 mas cercano?

Medidas por pixel: M1 y M2 de H29 (h29_medir.Medidor, sin cambios). M1 = BTD del pixel menos la mediana de la BTD
de los pixeles del mismo cuadro con BT11 a +-0,5 K y cota a +-300 m, lejos de la pluma. M2 = BT11 del pixel menos la
mediana del anillo de 2 a 8 pixeles con la misma cota.
Estadistico por posicion: pendiente por el origen k = sum(f * M) / sum(f^2) sobre los pixeles con f >= 0,02 fuera
del bloque de 3 x 3 del crater (la senal de una pluma que llenara el pixel, si crece en proporcion a f).
Decide (nulo espacio-temporal): D = k del cuadro del evento - mediana de k en los dias base despejados, en la
posicion real y en cada corrimiento de la huella dentro de la ventana; p = fraccion de corrimientos con D igual o
mas bajo que el real. D quita el efecto fijo de la superficie (cada lugar contra su propia historia despejada) y el
corrimiento quita el modo comun del dia.
Dias base: todo el cubo (21-09 a 21-11) sin los dias excluidos por H24 ni los dos eventos, con el cuadro o uno de
sus vecinos de +-10 min despejado por la regla E1 de H23 (un valor por dia: mediana de sus cuadros despejados).
Control positivo y ensayo en seco: cada dia base hace de evento contra los demas; sin pintar da las falsas alarmas,
pintado con la f medida y eps11 (capa a la T del GFS a la altura H; oculta si el pixel ya esta mas frio) da la
potencia.

Uso: python -I s20b_medir.py esperado   (solo dias nulos: senal esperada, potencia y falsas alarmas)
     python -I s20b_medir.py medir      (el dia del evento; solo despues de commitear y empujar el criterio)
"""
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, "..", "..", "h29_pluma_0811", "scripts"))
import s20b_comun as S  # noqa: E402
import h29_medir as M29  # noqa: E402  (Medidor, corrimientos: M1 y M2 de H29 sin tocar)
H24 = M29.H24
C29 = M29.C

RES = os.path.join(os.path.dirname(AQUI), "resultados")
T0, NDIAS = H24.T0, H24.NDIAS
F_PESO = 0.02
SUMA_F_MIN = 0.20
MIN_NULO, MIN_CORR, MAX_CORR, EXCL_PX = 6, 30, 25, 4
EPS_REF = 0.5
E_GRID = [0.1, 0.3, 0.5, 0.9]
EVENTOS = {"2026-10-25": {"hora": "14:34:31", "cuadros": ["14:20", "14:30"]},
           "2026-11-08": {"hora": "14:53:02", "cuadros": ["14:40", "14:50"]}}
L1B = {"2026-10-25": r"D:\goes_notas\s18\h24\l1b", "2026-11-08": r"D:\goes_notas\s17\h23\l1b"}
ACM = DESP = None
FILA, COL = np.divmod(np.arange(S.NY * S.NX), S.NX)


def dia_idx(s):
    return (datetime.strptime(s, "%Y-%m-%d") - T0).days


def nulos_de(dia, s):
    """Dias nulos: todo el cubo (21-09 a 21-11), fuera de los dias excluidos por H24 y de los dos eventos, con al
    menos uno de los cuadros s-1, s, s+1 despejado por la regla E1 de H23. Devuelve {dia: [cuadros despejados]}.
    Por que todo el cubo y +-10 min: a media manana hay 4 a 6 dias despejados por cuadro en dos meses."""
    ev = {dia_idx(x) for x in EVENTOS}
    out = {}
    for d in range(NDIAS):
        if d in ev or H24.DIA_EXCL[d]:
            continue
        ss = [x for x in (s - 1, s, s + 1) if DESP[d, x]]
        if ss:
            out[d] = ss
    return out


def hora_chillan(dia, cuadro):
    """Hora estimada del barrido de la fila de Chillan: inicio + fraccion del angulo y del disco x duracion.
    Aproximacion lineal: el L1b no trae hora por fila y el disco se intercala con CONUS y mesoescala."""
    k = str(np.load(os.path.join(L1B[dia], f"{dia.replace('-', '')}_{cuadro.replace(':', '')}.npz"))["key14"])
    s = datetime.strptime(k.split("_s")[1][:13], "%Y%j%H%M%S")
    e = datetime.strptime(k.split("_e")[1][:13], "%Y%j%H%M%S")
    _, y = S.barrido(S.CRATER[0], S.CRATER[1], 3000.0)
    frac = (0.151844 - float(y)) / (2 * 0.151844)
    return s + (e - s) * frac, s, e


def elegir_cuadro(dia):
    t = datetime.strptime(f"{dia} {EVENTOS[dia]['hora']}", "%Y-%m-%d %H:%M:%S")
    filas = []
    for c in EVENTOS[dia]["cuadros"]:
        hc, s, e = hora_chillan(dia, c)
        filas.append({"cuadro": c, "inicio": f"{s:%H:%M:%S}", "fin": f"{e:%H:%M:%S}",
                      "hora_chillan_estimada": f"{hc:%H:%M:%S}", "dt_min": round((hc - t).total_seconds() / 60, 1)})
    filas.sort(key=lambda r: abs(r["dt_min"]))
    return filas


def slot(cuadro):
    h, m = cuadro.split(":")
    return int(h) * 6 + int(m) // 10


class Prueba:
    def __init__(self, M, dia, variante="f"):
        z = np.load(os.path.join(S.TRABAJO, f"mascara_{dia}.npz"))
        self.f = z[variante].ravel()
        self.H = float(z["H"]) + {"f": 0.0, "f_menos": -1000.0, "f_mas": 1000.0}[variante]
        bloque = z["bloque"].ravel()
        self.pix = np.flatnonzero((self.f >= F_PESO) & ~bloque)
        self.w = self.f[self.pix]
        ex = (self.f > 0).reshape(S.NY, S.NX) | z["bloque"]
        self.ex4 = ndimage.binary_dilation(ex, iterations=EXCL_PX).ravel()
        self.ex1 = ndimage.binary_dilation(ex, iterations=1).ravel()
        self.todas = ndimage.binary_dilation(ex, iterations=EXCL_PX)
        self.M = M
        self.hk = round(self.H) / 1000.0

    def k(self, d, s, iny_eps=None, corr=None):
        """(k1, k2, n1, n2): pendientes por el origen de M1 y M2 contra f."""
        v1, v2, w1, w2 = [], [], [], []
        for p, f in zip(self.pix, self.w):
            q = p if corr is None else int((FILA[p] + corr[0]) * S.NX + COL[p] + corr[1])
            iny = None if iny_eps is None else (float(f), iny_eps)
            m1, m2 = self.M.medir(d, s, q, self.ex4, self.ex1, iny=iny, hk=self.hk)
            if np.isfinite(m1):
                v1.append(m1)
                w1.append(f)
            if np.isfinite(m2):
                v2.append(m2)
                w2.append(f)
        out = []
        for v, w in ((v1, w1), (v2, w2)):
            v, w = np.array(v), np.array(w)
            out.append(float((w * v).sum() / (w * w).sum()) if w.sum() >= SUMA_F_MIN else np.nan)
        return out[0], out[1], len(v1), len(v2)

    def corrimientos(self):
        out = []
        for dr in range(-MAX_CORR, MAX_CORR + 1):
            for dc in range(-MAX_CORR, MAX_CORR + 1):
                if (dr, dc) == (0, 0):
                    continue
                r, c = FILA[self.pix] + dr, COL[self.pix] + dc
                if ((r < 0) | (r >= S.NY) | (c < 0) | (c >= S.NX)).any():
                    continue
                if self.todas[r, c].any():
                    continue
                out.append((dr, dc))
        return out


def nombre(d):
    return f"{T0 + timedelta(days=d):%Y-%m-%d}"


def hhmm(x):
    return f"{x // 6:02d}:{x % 6 * 10:02d}"


PASO_CORR = 2          # se usa uno de cada dos corrimientos validos (costo); el p se informa con cuantos hubo
P_SEN_D, P_NUL_D, POT_MIN_D = 0.05, 0.20, 0.80
FA_INVALIDO = 2        # dias nulos con p <= 0,05 en el ensayo en seco a partir de los cuales la prueba es INVALIDA


def tabla_k(P, d, slots, corr):
    """k1 y k2 de (d, s) en la posicion real (fila 0) y en cada corrimiento (filas 1..): array (len(slots), 1+nc, 2)."""
    out = np.full((len(slots), 1 + len(corr), 2), np.nan)
    for a, s in enumerate(slots):
        out[a, 0] = P.k(d, s)[:2]
        for b, c in enumerate(corr):
            out[a, 1 + b] = P.k(d, s, corr=c)[:2]
    return out


def anomalia(K_ev, K_base):
    """D = k del dia (mediana de sus cuadros) - mediana entre dias base de su k (mediana de sus cuadros), por
    posicion (real y corrimientos). K_ev: (ns, 1+nc, 2); K_base: lista de (ns_b, 1+nc, 2)."""
    ev = np.nanmedian(K_ev, axis=0)
    base = np.nanmedian(np.stack([np.nanmedian(k, axis=0) for k in K_base]), axis=0)
    return ev - base                                     # (1+nc, 2)


def p_de(D, i):
    """p: fraccion de corrimientos con D igual o mas bajo que la posicion real (una cola, la de la ceniza/frio)."""
    real, cs = D[0, i], D[1:, i]
    cs = cs[np.isfinite(cs)]
    if not np.isfinite(real) or len(cs) < MIN_CORR:
        return np.nan, len(cs)
    return float((cs <= real).mean()), len(cs)


def veredicto_D(p, pot, fa):
    if fa >= FA_INVALIDO:
        return "INVÁLIDO"
    if not np.isfinite(p):
        return "SIN DATO"
    if p <= P_SEN_D:
        return "SEÑAL"
    if p > P_NUL_D:
        return "SIN FIRMA" if pot >= POT_MIN_D else "SIN PODER"
    return "NO CONCLUYENTE"


def nulos_y_tablas(P, dia, s, corr):
    nul = nulos_de(dia, s)
    tablas = {d: tabla_k(P, d, sl, corr) for d, sl in nul.items()}
    return nul, tablas


def seco_y_potencia(P, nul, tablas, eps_lista):
    """Cada dia nulo, en el lugar del evento, contra los demas como base: p sin pintar (falsas alarmas) y p con la
    pluma pintada en la posicion real con eps11 (potencia). Solo se pinta la posicion real; los corrimientos quedan
    como estan, igual que el dia del evento."""
    seco = {}
    pot = {str(e): [] for e in eps_lista}
    senal = {str(e): [] for e in eps_lista}
    for d, sl in nul.items():
        base = [tablas[x] for x in nul if x != d]
        if len(base) < MIN_NULO - 1:
            continue
        D = anomalia(tablas[d], base)
        seco[nombre(d)] = [p_de(D, 0)[0], p_de(D, 1)[0]]
        for e in eps_lista:
            Kp = tablas[d].copy()
            for a, s in enumerate(sl):
                Kp[a, 0] = P.k(d, s, iny_eps=e)[:2]
            Dp = anomalia(Kp, base)
            senal[str(e)].append(Dp[0] - D[0])
            ok = [p_de(Dp, i)[0] for i in (0, 1)]
            pot[str(e)].append(ok)
    out = {"seco_p": {k: [round(x, 4) if np.isfinite(x) else None for x in v] for k, v in seco.items()}}
    for i, nom in ((0, "M1"), (1, "M2")):
        ps = [v[i] for v in seco.values() if np.isfinite(v[i])]
        out[nom] = {"falsas_alarmas_seco": int(sum(p <= P_SEN_D for p in ps)), "dias_seco": len(ps),
                    "potencia": {}, "senal_esperada_D": {}}
        for e in eps_lista:
            pe = [v[i] for v in pot[str(e)] if np.isfinite(v[i])]
            out[nom]["potencia"][str(e)] = [round(float(np.mean([p <= P_SEN_D for p in pe])), 3) if pe else None, len(pe)]
            dd = [x[i] for x in senal[str(e)] if np.isfinite(x[i])]
            out[nom]["senal_esperada_D"][str(e)] = round(float(np.median(dd)), 3) if dd else None
    return out


def esperado(M):
    """Solo dias nulos: senal esperada, potencia y ensayo en seco con el nulo espacio-temporal."""
    out = {}
    for dia in EVENTOS:
        filas = elegir_cuadro(dia)
        s = slot(filas[0]["cuadro"])
        P = Prueba(M, dia)
        corr = P.corrimientos()[::PASO_CORR]
        nul, tablas = nulos_y_tablas(P, dia, s, corr)
        r = {"cuadros": filas, "cuadro_decide": filas[0]["cuadro"], "H_m": round(P.H),
             "pixeles": [{"fila": int(FILA[p]), "col": int(COL[p]), "f": round(float(f), 3)} for p, f in zip(P.pix, P.w)],
             "suma_f": round(float(P.w.sum()), 3), "corrimientos_usados": len(corr),
             "dias_nulos": {nombre(d): [hhmm(x) for x in sl] for d, sl in nul.items()},
             "acm_poblacion_dia_evento": [int(x) for x in ACM[dia_idx(dia), s, P.pix]],
             "despejada_E1_dia_evento": bool(DESP[dia_idx(dia), s])}
        r.update(seco_y_potencia(P, nul, tablas, E_GRID))
        j = int(np.argmax(P.w))
        pm = P.pix[j]
        e1, e2, oc = [], [], 0
        for d, sl in nul.items():
            for x in sl:
                m1, m2 = M.medir(d, x, pm, P.ex4, P.ex1, hk=P.hk)
                q1, q2 = M.medir(d, x, pm, P.ex4, P.ex1, iny=(float(P.w[j]), EPS_REF), hk=P.hk)
                e1.append(q1 - m1)
                e2.append(q2 - m2)
                oc += float(M.bt11[d, x, pm]) <= M.Tgfs[d, x, M.alturas.index(round(P.H))]
        r["pixel_mayor_f"] = {"fila": int(FILA[pm]), "col": int(COL[pm]), "f": round(float(P.w[j]), 3),
                              "dM1_eps05_mediana_K": round(float(np.nanmedian(e1)), 3),
                              "dM2_eps05_mediana_K": round(float(np.nanmedian(e2)), 3),
                              "cuadros_con_capa_oculta": int(oc), "cuadros": len(e1)}
        out[dia] = r
        print(json.dumps(r, ensure_ascii=False), flush=True)
    return out


def medir(M):
    out = {}
    for dia in EVENTOS:
        filas = elegir_cuadro(dia)
        d0 = dia_idx(dia)
        res_dia = {}
        for variante in ("f", "f_menos", "f_mas"):
            P = Prueba(M, dia, variante)
            corr = P.corrimientos()[::PASO_CORR]
            for fila in filas:
                s = slot(fila["cuadro"])
                nul, tablas = nulos_y_tablas(P, dia, s, corr)
                sp = seco_y_potencia(P, nul, tablas, [EPS_REF])
                K_ev = tabla_k(P, d0, [s], corr)
                D = anomalia(K_ev, list(tablas.values()))
                k_ev = K_ev[0, 0]
                r = {"cuadro": fila["cuadro"], "corrimientos": len(corr), "dias_nulos": len(nul),
                     "acm_poblacion": [int(x) for x in ACM[d0, s, P.pix]], "despejada_E1": bool(DESP[d0, s])}
                for i, nom in ((0, "M1"), (1, "M2")):
                    p, nc = p_de(D, i)
                    pot = sp[nom]["potencia"][str(EPS_REF)][0] or 0.0
                    fa = sp[nom]["falsas_alarmas_seco"]
                    r[nom] = {"k_evento": round(float(k_ev[i]), 3) if np.isfinite(k_ev[i]) else None,
                              "D": round(float(D[0, i]), 3) if np.isfinite(D[0, i]) else None,
                              "D_corrimientos_p5_p50_p95": [round(float(x), 3) for x in
                                                           np.nanpercentile(D[1:, i], [5, 50, 95])],
                              "p": round(p, 4) if np.isfinite(p) else None, "corrimientos_validos": nc,
                              "potencia_ref": pot, "falsas_alarmas_seco": [fa, sp[nom]["dias_seco"]],
                              "veredicto": veredicto_D(p, pot, fa) if len(nul) >= MIN_NULO else "SIN DATO"}
                j = int(np.argmax(P.w))
                m1, m2 = M.medir(d0, s, P.pix[j], P.ex4, P.ex1, hk=P.hk)
                b1 = [np.nanmedian([M.medir(d, x, P.pix[j], P.ex4, P.ex1, hk=P.hk)[0] for x in sl]) for d, sl in nul.items()]
                b2 = [np.nanmedian([M.medir(d, x, P.pix[j], P.ex4, P.ex1, hk=P.hk)[1] for x in sl]) for d, sl in nul.items()]
                r["pixel_mayor_f"] = {"fila": int(FILA[P.pix[j]]), "col": int(COL[P.pix[j]]), "f": round(float(P.w[j]), 3),
                                      "M1": round(float(m1), 3), "M1_base_mediana": round(float(np.nanmedian(b1)), 3),
                                      "M2": round(float(m2), 3), "M2_base_mediana": round(float(np.nanmedian(b2)), 3),
                                      "BT11": round(float(M.bt11[d0, s, P.pix[j]]), 2),
                                      "BTD": round(float(M.btd[d0, s, P.pix[j]]), 3)}
                res_dia[f"{variante}_{fila['cuadro']}"] = r
                print(dia, variante, json.dumps(r, ensure_ascii=False), flush=True)
        out[dia] = {"cuadros": filas, "resultados": res_dia}
    return out


def main():
    modo = sys.argv[1]
    global ACM, DESP
    r14, r15, ACM, co14, co15 = H24.cargar()
    DESP = H24.despejada("chillan", ACM)
    alturas = sorted({round(float(np.load(os.path.join(S.TRABAJO, f"mascara_{d}.npz"))["H"]) + dz)
                      for d in EVENTOS for dz in (-1000, 0, 1000)})
    Tg = H24.gfs_t(np.array(alturas, float))
    M = M29.Medidor(r14, r15, co14, co15, Tg, alturas)
    if modo == "esperado":
        out = esperado(M)
        fn = "esperado.json"
    elif modo == "medir":
        out = medir(M)
        fn = "s20b_resultado.json"
    else:
        raise SystemExit(__doc__)
    with open(os.path.join(RES, fn), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
