r"""Nube tenue, exploración 8 (SÓLO cuadros 1 a 5, nivel A; no decide).

Combina R1 (7,3 sólo con ε73 >= 0,1) y R2 (β multicapa ausente al primer casillero) y prueba variantes de R3 para
las tablas de 8,5 µm, con los umbrales que trae la tabla: EMISS10_TOT_MIN_8511_PREDICTORS = 0,05 (ε de la banda 10,
7,3 µm) y EMISS14_TOT_MIN_8511_PREDICTORS = 0,1 (εtot). Mide exactitud (|Δ logit| < 1e-3 en no saturados) y las tres
métricas del criterio por tramo de εtot. Luego describe lo que queda sin calzar.
Salida: ../resultados/nt_explorar8.txt
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_comun as N  # noqa: E402
import nt_regla as R  # noqa: E402

LV, E = N.LV, N.E
out = open(os.path.join(N.RES, "nt_explorar8.txt"), "w", encoding="utf-8")


def p(*a):
    print(*a); print(*a, file=out, flush=True)


ent, agua, v, q = N.cargar(E.ELIGE)
lv = N.logit(v)
sat = N.no_saturado(v)
e73 = R.eps73(ent)
eps = ent["eps"]
C0 = R.contribuciones(ent, agua, r2=False)
C2 = R.contribuciones(ent, agua, r2=True)
TRAMOS = (("<0,2", 0, 0.2), ("0,2-0,5", 0.2, 0.5), (">=0,5", 0.5, 1.01))
f73 = np.isfinite(e73)
VAR85 = {
    "siempre": None,
    "e73>=0,05 (falta→no)": f73 & (e73 >= 0.05),
    "e73>=0,05 (falta→sí)": ~f73 | (e73 >= 0.05),
    "eps>=0,1": eps >= 0.1,
    "e73>=0,05 & eps>=0,1 (falta→no)": f73 & (e73 >= 0.05) & (eps >= 0.1),
    "(e73>=0,05 o falta) & eps>=0,1": (~f73 | (e73 >= 0.05)) & (eps >= 0.1),
}
p("Exactos (|Δlogit|<1e-3) entre no saturados, y métricas del criterio (|ΔP|<=0,05, κ, recuperados) por tramo")
res = {}
for nom, (C, r1, c85) in {
    "base (7 tablas)": (C0, False, None),
    "R1": (C0, True, None),
    "R2": (C2, False, None),
    "R1+R2": (C2, True, None),
    **{f"R1+R2+R3[{k}]": (C2, True, c) for k, c in VAR85.items() if c is not None},
}.items():
    L = R.logit_regla(C, ent, r1=r1, cond85=c85)
    P = LV.prob(L)
    ok = np.abs(L - lv) < 1e-3
    fila = []
    for tn, a, b in TRAMOS:
        s = (eps >= a) & (eps < b)
        m = E.metricas(P[s], v[s])
        fila.append(f"{tn}: exact {ok[s & sat].mean():.4f} dP {m['frac_dif_le_005']:.4f} κ {m['kappa_05']:.3f} rec {m['frac_ge05_recuperada']:.3f}")
    p(f"{nom:38s} | " + " | ".join(fila))
    res[nom] = L

# Lo que queda con R1+R2 (sin R3) en cada tramo: ¿se arregla quitando 8,5? ¿qué variables lo separan?
L = res["R1+R2"]
mal = sat & (np.abs(L - lv) >= 1e-3)
sin85 = sat & (np.abs(L - C2[:, R.J85].sum(1) - lv) < 1e-3)
p(f"\nCon R1+R2: no exactos {mal.sum()} de {sat.sum()} no saturados; de ellos se arreglan quitando las dos de 8,5: {np.mean(sin85[mal]):.4f}")
for tn, a, b in TRAMOS:
    s = (eps >= a) & (eps < b)
    p(f"  {tn}: no exactos {(mal & s).sum()}, arreglables sin 8,5 {(mal & s & sin85).sum()}")
A_ = mal & sin85
B_ = sat & ~mal
for k, x in (("eps", eps), ("e73", e73), ("b85", ent["b85"]), ("b85op", ent["b85op"]), ("b_tot", ent["b_tot"]),
             ("b_op", ent["b_op"]), ("btd", ent["btd"])):
    p(f"   {k:6s} piden sin 8,5: p0/5/50/95/100 {np.nanpercentile(x[A_], [0, 5, 50, 95, 100]).round(4)} falta {np.mean(~np.isfinite(x[A_])):.3f}"
      f" | exactos con 8,5: {np.nanpercentile(x[B_], [0, 5, 50, 95, 100]).round(4)} falta {np.mean(~np.isfinite(x[B_])):.3f}")
# tabla cruzada eps>=0,1 y e73 (>=0,05 / <0,05 / falta) entre exactos con 8,5 y los que piden sin 8,5
for nom, m in (("piden sin 8,5", A_), ("exactos con 8,5", B_)):
    for ce, cm in (("eps<0,1", eps < 0.1), ("eps>=0,1", eps >= 0.1)):
        a1 = (m & cm & f73 & (e73 >= 0.05)).sum(); a2 = (m & cm & f73 & (e73 < 0.05)).sum(); a3 = (m & cm & ~f73).sum()
        p(f"   {nom:16s} {ce:8s}: e73>=0,05 {a1:6d}  e73<0,05 {a2:6d}  e73 falta {a3:6d}")
out.close()

# Repetición donde las tablas de 8,5 aportan algo (|contrib| > 1e-3): si aportan cero, incluirlas u omitirlas da lo
# mismo y el píxel no informa sobre la regla.
out = open(os.path.join(N.RES, "nt_explorar8.txt"), "a", encoding="utf-8")
c85 = C2[:, R.J85].sum(1)
inf = np.abs(c85) > 1e-3
p("\nSólo píxeles donde 8,5 aporta (|contrib| > 1e-3):")
for nom, m in (("piden sin 8,5", A_ & inf), ("exactos con 8,5", B_ & inf)):
    for ce, cm in (("eps<0,1", eps < 0.1), ("eps>=0,1", eps >= 0.1)):
        a1 = (m & cm & f73 & (e73 >= 0.05)).sum(); a2 = (m & cm & f73 & (e73 < 0.05)).sum(); a3 = (m & cm & ~f73).sum()
        p(f"   {nom:16s} {ce:8s}: e73>=0,05 {a1:6d}  e73<0,05 {a2:6d}  e73 falta {a3:6d}")
# ¿qué separa, entre los de e73 falta y eps>=0,1, los que piden sin 8,5 de los exactos con 8,5?
m1 = A_ & inf & (eps >= 0.1) & ~f73
m2 = B_ & inf & (eps >= 0.1) & ~f73
for k, x in (("eps", eps), ("b73", ent["b73"]), ("b85", ent["b85"]), ("b85op", ent["b85op"]), ("b_tot", ent["b_tot"]),
             ("b_op", ent["b_op"]), ("btd", ent["btd"]), ("bt10-clr10", ent["bt10"] - ent["clr10"]),
             ("bt14-clr14", ent["bt14"] - ent["clr14"]), ("clr10", ent["clr10"])):
    p(f"   {k:10s} e73 falta, eps>=0,1 | piden sin 8,5 {np.nanpercentile(x[m1], [0, 5, 50, 95, 100]).round(3)} | "
      f"exactos con 8,5 {np.nanpercentile(x[m2], [0, 5, 50, 95, 100]).round(3)}")
out.close()
