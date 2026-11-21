r"""Vuelta 2, POSTERIOR (no decide), cuadros 1 a 5: residuo de β(12/11) tras la corrección por vapor (H1), por
franja de ε, y Δβ·ε (constante si el residuo viene de un desfase del cielo despejado de 12 µm). Además, el desfase
de BT despejada en C15 que haría coincidir nuestro β con el de VOLCAT (menos 0,2), por píxel.
Escribe ../resultados/posterior_beta_residuo.txt.
"""
import os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vuelta2_beta as V2  # noqa: E402
CS = V2.CS
lin = []
P = lambda *a: lin.append(" ".join(str(x) for x in a))  # noqa: E731
EV, BV, BO, D15 = [], [], [], []
for h in CS.E.ELIGE:
    c = CS.Cuadro(h)
    e14, b12, _ = V2.entradas(c, "H1", "S0")
    # ε15 de VOLCAT oblicuo sin la corrección de vapor, y el cielo despejado de C15 que lo daría
    mu = c.mu
    with np.errstate(all="ignore"):
        bvsin = np.where(c.ev < 0.25, c.bv12 - 0.2, c.bv12)
        e15v = 1 - (1 - c.ev) ** (bvsin / mu)
        ro = CS.E.rad(c.d, c.obs[15], 15); rb = CS.E.rad(c.d, c.tcld["N1"], 15)
        rclr = (ro - e15v * rb) / (1 - e15v)
        d15 = CS.bt_de_rad(rclr, c.d, 15) - c.clr[15]
    EV.append(c.ev.ravel()); BV.append(c.bv12.ravel()); BO.append(b12.ravel()); D15.append(d15.ravel())
ev, bv, bo, d15 = map(np.concatenate, (EV, BV, BO, D15))
ok = np.isfinite(ev) & np.isfinite(bv) & np.isfinite(bo)
P("H1, S0: Delta beta (nuestro - VOLCAT) y Delta beta * eps, por franja de eps_VOLCAT")
for lo, hi in ((.03, .05), (.05, .07), (.07, .1), (.1, .13), (.13, .16), (.16, .2), (.2, .25), (.25, .3), (.3, .4)):
    q = ok & (ev >= lo) & (ev < hi)
    d = bo[q] - bv[q]
    x = d15[q][np.isfinite(d15[q])]
    P(f"  [{lo:.2f},{hi:.2f}) n={q.sum():6d} dbeta med {np.median(d):+.3f}  dbeta*eps med {np.median(d * ev[q]):+.4f}"
      f"  desfase C15 que calza p25/50/75 {np.percentile(x, [25, 50, 75]).round(2)} K")
with open(os.path.join(os.path.dirname(HERE), "resultados", "posterior_beta_residuo.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lin) + "\n")
print("\n".join(lin))

# Prueba directa: β con el ε14 oblicuo de VOLCAT y nuestro ε15 (cielo geocatRTM, N1), más H1.
P("\nbeta con eps14 de VOLCAT y eps15 nuestro (+H1): Delta beta (nuestro - VOLCAT)")
EV2, BV2, BX = [], [], []
for grupo, horas in (("cuadros 1 a 5", CS.E.ELIGE), ("cuadros 6 a 10, posterior", CS.E.VALIDA)):
    EV2, BV2, BX = [], [], []
    for h in horas:
        c = CS.Cuadro(h)
        with np.errstate(all="ignore"):
            e14s = 1 - (1 - c.ev) ** (1 / c.mu)
        e15 = CS.LV.emisividad(CS.E.rad(c.d, c.obs[15], 15), CS.E.rad(c.d, c.clr[15], 15),
                               CS.E.rad(c.d, c.tcld["N1"], 15))
        bx = V2.h2o(CS.LV.beta(e15, e14s), c.ev, V2.TPW[h])
        EV2.append(c.ev.ravel()); BV2.append(c.bv12.ravel()); BX.append(bx.ravel())
    ev2, bv2, bx = map(np.concatenate, (EV2, BV2, BX))
    ok2 = np.isfinite(ev2) & np.isfinite(bv2) & np.isfinite(bx)
    P(f"  {grupo}:")
    for lo, hi in ((.05, .1), (.1, .2), (.2, .25), (.25, .5), (.5, .9)):
        q = ok2 & (ev2 >= lo) & (ev2 < hi)
        d = bx[q] - bv2[q]
        P(f"  [{lo:.2f},{hi:.2f}) n={q.sum():6d} med {np.median(d):+.4f} p5 {np.percentile(d, 5):+.4f} p95 {np.percentile(d, 95):+.4f}  |d|<=0,02: {np.mean(np.abs(d) <= .02):.3f}")
with open(os.path.join(os.path.dirname(HERE), "resultados", "posterior_beta_residuo.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lin) + "\n")
print("\n".join(lin[-13:]))
