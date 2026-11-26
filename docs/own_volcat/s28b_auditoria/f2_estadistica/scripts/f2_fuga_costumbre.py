r"""F2 (S28b): ¿el ensayo en seco "cada día sin sí mismo" saca el día también del nublado de costumbre?

Por qué: en S22b, S23a, S25a y S26a la línea base y el umbral de 2025 se arman sin el día evaluado, pero el nublado de
costumbre (qué píxel con ACM 2-3 es nieve "de siempre" y no se borra) se calcula UNA vez con los 62 días, incluido el
día evaluado. Un día con nieve o nube persistente propia se "explica a sí mismo" como costumbre: el ensayo en seco es en
parte dentro de la muestra. Si la falsa alarma cambia al sacarlo, p* de S26a (elegido con ese seco y congelado para la
confirmación) podría ser otro.

Medida de primer orden: para cada día d de 2025 se recalcula la costumbre sin d (anillo: como Detector; zona: como
s25a_medir.costumbre) y, con ella, la compuerta, los píxeles borrados y S de ESE día; base y umbral sin d quedan los de
la regla (que a su vez usan la costumbre con d: efecto de segundo orden, no medido). Se comparan el seco global y la
media por día de la unión a percentil 5, 4,75 y 4,5, y del anillo y la zona solos, contra los mismos sin cambio.
Control: con la costumbre completa (sin sacar el día) este camino tiene que reproducir exactamente el seco publicado.
Uso: python -I f2_fuga_costumbre.py
"""
import json
import os
import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s26a_combinado", "scripts"))
import s26a_medir as U  # noqa: E402

S, Z, B, M, H24 = U.S, U.Z, U.B, U.M, U.H24
SAL = r"D:\goes_notas\s28\s28b\f2"


def sumas(acm, usar, e1):
    """Por hora x: suma de ACM 2-3 por píxel y número de cuadros, sobre los cuadros usar & e1; y lo mismo por día."""
    nd = acm.shape[0]
    Sx = np.zeros((nd, 144, acm.shape[2]), np.int16)
    Nx = np.zeros((nd, 144), np.int32)
    for d in range(nd):
        for s in range(144):
            if usar[d, s] and e1[d, s]:
                Sx[d, s] = (acm[d, s] >= 2) & (acm[d, s] <= 3)
                Nx[d, s] = 1
    return Sx, Nx


def costumbre_desde(Ssum, Nsum):
    """La regla de S22b enmienda 1 (±90 o ±180 min, mínimo 20, >= 50 %) desde sumas por hora (144, npix)."""
    est = np.zeros(Ssum.shape, bool)
    for s in range(144):
        for w in B.COSTUMBRE_VENT:
            idx = [(s + k) % 144 for k in range(-w, w + 1)]
            n = Nsum[idx].sum()
            if n >= B.MIN_COSTUMBRE:
                est[s] = Ssum[idx].sum(0) / n >= B.COSTUMBRE
                break
    return est


def main():
    t = time.time()
    X = U.Partes()
    A = X.A
    # ---- anillo: sumas de la costumbre de 2025 como Detector (DIASR, NULR, E1R) ----
    usarA = np.zeros(A.NULR.shape, bool)
    usarA[A.DIASR] = A.NULR[A.DIASR]
    SA, NA_ = sumas(A.acmR, usarA, A.E1R)
    SAt, NAt = SA.sum(0, dtype=np.int32), NA_.sum(0)
    estA_full = costumbre_desde(SAt, NAt)
    assert (estA_full == A.ESTAT).all(), "no reproduce la costumbre del anillo"
    # ---- zona: como s25a_medir.costumbre(acm25, hay25) ----
    btd25 = np.load(Z._npy("r25_btd"), mmap_mode="r")
    acm25 = np.load(Z._npy("r25_acm"))
    hay25 = np.isfinite(btd25[:, :, Z.ZONA[0]])
    e125 = H24.despejada("chillan", acm25)
    SZ, NZ = sumas(acm25, hay25, e125)
    SZt, NZt = SZ.sum(0, dtype=np.int32), NZ.sum(0)
    estZ_full = costumbre_desde(SZt, NZt)
    assert (estZ_full == Z.costumbre(acm25, hay25)).all(), "no reproduce la costumbre de la zona"
    print(f"costumbres reproducidas, {time.time() - t:.0f} s", flush=True)
    IZ = np.arange(len(Z.ZONA))
    BZ = [Z.base(X.Z25, X.USA25, IZ, excl=d) for d in range(Z.NR)]
    # S por día con la costumbre sin el día (primer orden)
    SRa = A.SR.copy()
    KRa = A.KR.copy()
    SRz = X.SRz.copy()
    cambios = {"anillo_pixeles_costumbre_distintos_media": [], "zona_pixeles_costumbre_distintos_media": []}
    for d in range(Z.NR):
        estA = costumbre_desde(SAt - SA[d], NAt - NA_[d])
        estZ = costumbre_desde(SZt - SZ[d], NZt - NZ[d])
        cambios["anillo_pixeles_costumbre_distintos_media"].append(float((estA != A.ESTAT).sum(1).mean()))
        cambios["zona_pixeles_costumbre_distintos_media"].append(float((estZ != estZ_full).sum(1).mean()))
        # anillo, día d
        Bd = A.base(d)
        for s in range(144):
            SRa[d, s], KRa[d, s] = np.nan, -1
            if not (A.acmR[d, s] != 255).any():
                continue
            nd = B.dinamica(A.acmR[d, s], estA[s])
            if nd[M.AP].mean() <= B.G_MAX:
                mm = A.m1R[d, s].copy()
                mm[B.borde(nd)[M.AP]] = np.nan
                SRa[d, s], KRa[d, s], _ = M.estadistico(mm - Bd[s])
        # zona, día d
        FDd, DINd = Z.nubes(acm25[d:d + 1], estZ)
        Cd = Z.regional(np.asarray(btd25[d:d + 1]), DINd, X.bctrl)
        Sd, _ = Z.tabla_S(X.Z25[d:d + 1], Cd, BZ[d][None], FDd <= B.G_MAX)
        SRz[d] = Sd[0]
    print(f"S sin el día en la costumbre, {time.time() - t:.0f} s", flush=True)
    out = {"cambios_costumbre": {k: [round(min(v), 1), round(float(np.mean(v)), 1), round(max(v), 1)]
                                 for k, v in cambios.items()}}
    for p in (5.0, 4.75, 4.5):
        U._pct(p)
        A._U = {}
        ULz = [Z.umbral(X.SRz, excl=d) for d in range(Z.NR)]
        fila = {}
        for nom, (sa, ka, sz) in (("publicado", (A.SR, A.KR, X.SRz)), ("costumbre_sin_el_dia", (SRa, KRa, SRz))):
            dias = {"a": [], "z": [], "u": []}
            for d in range(Z.NR):
                Ua, _ = A.umbral(d)
                Fa, eva = S.disparos(sa, ka, d, Ua)
                Fz, evz = Z.disparos(sz, d, ULz[d], ULz[d - 1] if d else None)
                dias["a"].append((Fa, eva))
                dias["z"].append((Fz, evz))
                dias["u"].append((Fa | Fz, eva | evz))
            fila[nom] = {k: {kk: (round(vv, 5) if isinstance(vv, float) else vv)
                             for kk, vv in U.medidas_seco(v).items() if kk in ("global", "media_por_dia", "disparos",
                                                                                 "evaluados")}
                         for k, v in dias.items()}
        out[str(p)] = fila
        print(p, json.dumps(fila), flush=True)
    json.dump(out, open(os.path.join(SAL, "fuga_costumbre.json"), "w", encoding="utf-8"), indent=1)
    print(f"fin {time.time() - t:.0f} s")


if __name__ == "__main__":
    main()
