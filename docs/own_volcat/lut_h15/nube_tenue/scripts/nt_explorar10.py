r"""Nube tenue, exploración 10 (SÓLO cuadros 1 a 5, nivel A; no decide).

Candidata R3 leída de los atributos de la tabla: las tablas de β(8,5/11) se descartan cuando la nube es tenue
(εtot < EMISS14_TOT_MIN_8511_PREDICTORS = 0,1, o ε(7,3) < EMISS10_TOT_MIN_8511_PREDICTORS = 0,05; ε73 ausente cuenta
como bajo) Y β(8,5/11) total cae en la franja ambigua entre BETA8511_TOT_MAX_8511_PREDICTORS = 1,05 y
BETA8511_TOT_MIN_8511_PREDICTORS = 2,0. Se prueban variantes (sólo εtot, sólo ε73, con y sin la franja, con β
opaco) y se mide exactitud y métricas por tramo.
Salida: ../resultados/nt_explorar10.txt
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_comun as N  # noqa: E402
import nt_regla as R  # noqa: E402

LV, E = N.LV, N.E
out = open(os.path.join(N.RES, "nt_explorar10.txt"), "w", encoding="utf-8")


def p(*a):
    print(*a); print(*a, file=out, flush=True)


ent, agua, v, q = N.cargar(E.ELIGE)
lv = N.logit(v)
sat = N.no_saturado(v)
e73 = R.eps73(ent)
eps = ent["eps"]
b85 = ent["b85"]
C2 = R.contribuciones(ent, agua, r2=True)
c85 = C2[:, R.J85].sum(1)
inf = sat & (np.abs(c85) > 1e-3)
L12 = R.logit_regla(C2, ent, r1=True)
con = inf & (np.abs(L12 - lv) < 1e-3)
sin = inf & (np.abs(L12 - c85 - lv) < 1e-3) & ~con
bajo73 = ~np.isfinite(e73) | (e73 < 0.05)
franja = (b85 > 1.05) & (b85 < 2.0)
franja_op = (ent["b85op"] > 1.05) & (ent["b85op"] < 2.0)
tenue = (eps < 0.1) | bajo73
VAR = {
    "tenue(eps<0,1 o e73<0,05)": tenue,
    "tenue & franja b85": tenue & franja,
    "eps<0,1 & franja": (eps < 0.1) & franja,
    "e73<0,05 & franja": bajo73 & franja,
    "tenue & (franja b85 o franja b85op)": tenue & (franja | franja_op),
    "tenue & franja b85 & franja b85op": tenue & franja & franja_op,
    "tenue & b85>1,05": tenue & (b85 > 1.05),
}
TRAMOS = (("<0,2", 0, 0.2), ("0,2-0,5", 0.2, 0.5), (">=0,5", 0.5, 1.01))
p(f"informativos: con 8,5 {con.sum()}, sólo sin 8,5 {sin.sum()}")
for nom, omite in VAR.items():
    acc_c = np.mean(~omite[con]); acc_s = np.mean(omite[sin])
    L = R.logit_regla(C2, ent, r1=True, cond85=~omite)
    P = LV.prob(L)
    ok = np.abs(L - lv) < 1e-3
    fila = []
    for tn, a, b in TRAMOS:
        s = (eps >= a) & (eps < b)
        mm = E.metricas(P[s], v[s])
        fila.append(f"{tn}: exact {ok[s & sat].mean():.4f} dP {mm['frac_dif_le_005']:.4f} κ {mm['kappa_05']:.3f} rec {mm['frac_ge05_recuperada']:.3f}")
    p(f"{nom:36s} acierta con {acc_c:.4f} sin {acc_s:.4f} | " + " | ".join(fila))

# Los mal clasificados por la mejor candidata
omite = tenue & franja
for nom, mm in (("con 8,5 pero la regla omite", con & omite), ("sin 8,5 pero la regla usa", sin & ~omite)):
    p(f"\n{nom}: {mm.sum()}")
    for k, x in (("eps", eps), ("e73", e73), ("b85", b85), ("b85op", ent["b85op"]), ("b_tot", ent["b_tot"]),
                 ("bt10-clr10", ent["bt10"] - ent["clr10"]), ("btd", ent["btd"])):
        p(f"   {k:10s} p0/5/50/95/100 {np.nanpercentile(x[mm], [0, 5, 50, 95, 100]).round(4) if mm.any() else '-'} falta {np.mean(~np.isfinite(x[mm])) if mm.any() else 0:.3f}")
out.close()
