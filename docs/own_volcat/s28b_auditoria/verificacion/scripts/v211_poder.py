r"""V211: el poder de las dos partes de la unión al percentil p* = 4,75 (el criterio de S26a dice "no se recalcula").

Sólo 2025 (año de referencia, ya visto). Repite, con el percentil como parámetro, los dos cálculos de poder ya
publicados, usando las funciones de la COPIA de los scripts (D:\goes_notas\s28\s28b\v301\repo):
  anillo: el cuerpo de `s23_medir.poder` (200 pares, firma en los píxeles del rayo, dos cuadros seguidos, tajada vecina);
  zona:   el bloque de poder de `s25a_medir.medir` (200 pares, firma en 2 píxeles de la zona, dos cuadros seguidos).
Control del instrumento: a percentil 5 tiene que dar lo publicado (anillo 0,01 y 0,585; zona 0,14 y 0,785). Si no lo
da, el número a 4,75 no vale.

No mide el poder de la UNIÓN: ningún criterio define qué firma se inyecta en las dos partes a la vez.

Uso: python -I -B v211_poder.py
"""
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
V = r"D:\goes_notas\s28\s28b\v301"
OVC = os.path.join(V, "repo", "docs", "own_volcat")
os.environ.setdefault("V301_TRAB", os.path.join(V, "trab_base"))
os.environ.setdefault("V301_ARRANQUE", "2026-11-07")
os.environ.setdefault("V301_CLASES", os.path.join(V, "clases_08a11.csv"))
sys.path.insert(0, os.path.join(OVC, "s23_fondo_2025", "scripts"))
sys.path.insert(0, os.path.join(OVC, "s25a_crater", "scripts"))
import s23_medir as S  # noqa: E402
import s25a_medir as Z  # noqa: E402
B, M, H24 = S.B, S.M, S.H24
assert S.__file__.startswith(V) and Z.__file__.startswith(V)
AQUI = os.path.dirname(os.path.abspath(__file__))


def poder_anillo(D, pct):
    B.PCT_U = pct
    D._U = {}
    pares = []
    for d in D.DIASR:
        U, _ = D.umbral(d)
        for s in range(1, 144):
            if (U[s] is not None and U[s - 1] is not None and np.isfinite(D.SR[d, s]) and np.isfinite(D.SR[d, s - 1])):
                pares.append((d, s))
    rng = np.random.default_rng(B.SEMILLA)
    elegidos = rng.choice(len(pares), B.N_POD, replace=len(pares) < B.N_POD)
    azs = rng.uniform(0, 360, B.N_POD)
    out = {"pares": len(pares)}
    for a in B.FIRMAS:
        hits = 0
        for e, az in zip(elegidos, azs):
            d, s = pares[e]
            Bd = D.base(d)
            U, _ = D.umbral(d)
            sel = M.pixeles_rayo(az)
            ksec = int(az // 30) % M.NSEC
            res = []
            for x in (s - 1, s):
                v = D.mmR[d, x] - Bd[x]
                v[sel] -= a
                res.append(M.estadistico(v))
            (S1, k1, _), (S2, k2, _) = res
            if (np.isfinite(S1) and np.isfinite(S2) and S1 <= U[s - 1] and S2 <= U[s] and M.vecinos(k1, k2)
                    and M.vecinos(k2, ksec)):
                hits += 1
        out[f"{a:.2f}"] = hits / B.N_POD
    return out


class Zona:
    def __init__(self):
        btd25 = np.load(Z._npy("r25_btd"), mmap_mode="r")
        acm25 = np.load(Z._npy("r25_acm"))
        hay25 = np.isfinite(btd25[:, :, Z.ZONA[0]])
        est25 = Z.costumbre(acm25, hay25)
        FD25, DIN25 = Z.nubes(acm25, est25)
        G25 = FD25 <= B.G_MAX
        USA25 = G25 & H24.despejada("chillan", acm25) & hay25
        btd25 = np.asarray(btd25)
        bctrl = Z.base(btd25, USA25, Z.CTRL)
        self.C25 = Z.regional(btd25, DIN25, bctrl)
        IZ = np.arange(len(Z.ZONA))
        self.Z25 = np.ascontiguousarray(btd25[:, :, Z.ZONA])
        del btd25
        self.BZ = np.array([Z.base(self.Z25, USA25, IZ, excl=d) for d in range(Z.NR)])
        self.SR, _ = Z.tabla_S(self.Z25, self.C25, self.BZ, G25)

    def poder(self, pct):
        B.PCT_U = pct
        SR = self.SR
        UL = [Z.umbral(SR, excl=d) for d in range(Z.NR)]
        nF = nE = 0
        for d in range(Z.NR):
            F, ev = Z.disparos(SR, d, UL[d], UL[d - 1] if d else None)
            nF += int(F.sum())
            nE += int(ev.sum())
        rng = np.random.default_rng(Z.SEMILLA)
        pares = [(d, s) for d in range(Z.NR) for s in range(1, 144)
                 if np.isfinite(SR[d, s]) and np.isfinite(SR[d, s - 1]) and UL[d][s] is not None
                 and UL[d][s - 1] is not None]
        elig = rng.choice(len(pares), size=min(Z.N_POD, len(pares)), replace=False)
        out = {"pares": len(pares), "seco": [nF, nE, nF / nE]}
        for firma in Z.FIRMAS:
            hits = 0
            for i in elig:
                d, s = pares[i]
                px = rng.choice(len(Z.ZONA), size=Z.N_INY, replace=False)
                ok = True
                for x in (s - 1, s):
                    A = (self.Z25[d, x] - self.BZ[d, x] - self.C25[d, x]).copy()
                    A[px] -= firma
                    v, _ = Z.estadistico(A)
                    ok &= bool(np.isfinite(v) and v <= UL[d][x])
                hits += ok
            out[str(firma)] = hits / len(elig)
        return out


def main():
    out = {}
    zona = Zona()
    for p in (5.0, 4.75):
        out[f"zona_pct_{p}"] = zona.poder(p)
        print("zona", p, out[f"zona_pct_{p}"], flush=True)
    B.PCT_U = 5.0
    D = S.Detector(ref="2025", con_blanco=False)
    for p in (5.0, 4.75):
        out[f"anillo_pct_{p}"] = poder_anillo(D, p)
        print("anillo", p, out[f"anillo_pct_{p}"], flush=True)
    # Azar por hora (r25) de cada regla: ¿hay horas en que un cuadro nuevo puede evaluarse (hay umbral) y r25 no está
    # definido? Ahí p25 saldría NaN y `p25 <= 0.01` sería falso: NO CONFIRMA sin que nadie lo decida.
    for p, reglas in ((5.0, ("a", "z")), (4.75, ("u",))):
        B.PCT_U = p
        D._U = {}
        ULz = [Z.umbral(zona.SR, excl=d) for d in range(Z.NR)]
        Ua, _ = D.umbral(None)
        Uz = Z.umbral(zona.SR)
        sl = {"a": [], "z": [], "u": []}
        al = {"a": [], "z": [], "u": []}
        for d in range(Z.NR):
            Ud, _ = D.umbral(d)
            Fa, eva = S.disparos(D.SR, D.KR, d, Ud)
            Fz, evz = Z.disparos(zona.SR, d, ULz[d], ULz[d - 1] if d else None)
            for k, (F, ev) in (("a", (Fa, eva)), ("z", (Fz, evz)), ("u", (Fa | Fz, eva | evz))):
                for s in np.flatnonzero(ev):
                    sl[k].append(s)
                    al[k].append(B.alcanzado(F, ev, s)[1])
        for k in reglas:
            r = S.azar_por_hora(sl[k], al[k])
            hay_u = {"a": [Ua[s] is not None for s in range(144)], "z": [Uz[s] is not None for s in range(144)]}
            hay_u["u"] = [x or y for x, y in zip(hay_u["a"], hay_u["z"])]
            out[f"r25_{k}_pct_{p}"] = {
                "horas_con_r25_NaN": [M.hhmm(s) for s in range(144) if not np.isfinite(r[s])],
                "horas_con_umbral_y_r25_NaN": [M.hhmm(s) for s in range(144) if hay_u[k][s] and not np.isfinite(r[s])],
                "horas_sin_umbral": [M.hhmm(s) for s in range(144) if not hay_u[k][s]],
                "r25_min_max": [float(np.nanmin(r)), float(np.nanmax(r))],
                "horas_con_r25_cero": int(np.sum(r == 0))}
            print(f"r25 {k} a percentil {p}:", out[f"r25_{k}_pct_{p}"], flush=True)
    out["control_pct5_reproduce_lo_publicado"] = bool(
        out["anillo_pct_5.0"]["0.33"] == 0.01 and out["anillo_pct_5.0"]["0.97"] == 0.585
        and out["zona_pct_5.0"]["0.33"] == 0.14 and out["zona_pct_5.0"]["0.97"] == 0.785)
    print("control a percentil 5 reproduce lo publicado:", out["control_pct5_reproduce_lo_publicado"])
    json.dump(out, open(os.path.join(AQUI, "..", "V301_salidas", "v211_poder.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
