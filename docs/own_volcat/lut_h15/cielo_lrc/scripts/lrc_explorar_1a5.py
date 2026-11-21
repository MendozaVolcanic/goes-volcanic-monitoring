r"""EXPLORACIÓN (cuadros 1 a 5, no decide): ¿alguna cantidad del LRC o de la vecindad reproduce el ε(11) de VOLCAT
en nube tenue y su gradiente con la distancia a la nube espesa?

Candidatas (signo esperado: VOLCAT tiene ε(11) MÁS BAJO que el nuestro):
  base        ε nadir con geocatRTM, nube negra N1 (V1, N1, S0 de cielo_sesgo)
  a_lrc_clr   cielo despejado de C14 tomado en el LRC
  a_lrc_tcld  nube negra = BT14 observada en el LRC (signo esperado al revés: LRC más tibio que el punto frío)
  b_lrc_eps   ε del LRC propagado (signo al revés por construcción: ε(LRC) >= ε(píxel))
  c_max3/5    BT14 observada = máxima en 3x3 / 5x5
  d_med3      ε nadir con filtro de mediana 3x3
  d_clr_suave cielo despejado de C14 suavizado 25x25
  d_clr_vec   cielo despejado = geocatRTM − sesgo mediano local de los despejados de VOLCAT (12 px; ya descartado
              en cielo_sesgo, se repite como referencia)
  d_nwc21     cielo despejado = BT14 más tibia de 21x21 (Neighboring Warmest Center del ACM)
  d_nwc21_min cielo despejado = mín(geocatRTM, BT14 más tibia de 21x21)
LRC: filtro de gradiente sobre ε(11) nadir propio con mediana 3x3, parada 0,7 (tabla 1 del LRC, ATBD ACM, fila
Volcanic Ash). Escribe ../resultados/lrc_explorar_1a5.json.
"""
import json
import os
import sys

import numpy as np
from scipy.ndimage import maximum_filter, median_filter, uniform_filter

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun as C  # noqa: E402


def candidatas(c):
    base = C.eps_nadir(c)
    b14 = c.obs[14]
    med = median_filter(np.where(np.isfinite(base), base, 0.0), 3)
    r, k = C.lrc(med, stop=0.7)
    out = {"base": base}
    out["a_lrc_clr"] = C.eps_nadir(c, clr14=C.tomar(c.clr[14], r, k))
    out["a_lrc_tcld"] = C.eps_nadir(c, tcld=C.tomar(b14, r, k))
    out["b_lrc_eps"] = C.tomar(base, r, k)
    out["c_max3"] = C.eps_nadir(c, obs14=maximum_filter(b14, 3))
    out["c_max5"] = C.eps_nadir(c, obs14=maximum_filter(b14, 5))
    out["d_med3"] = med
    out["d_clr_suave"] = C.eps_nadir(c, clr14=uniform_filter(c.clr[14], 25, mode="nearest"))
    s = c.sesgo("L", "M1", 50, 14)
    out["d_clr_vec"] = C.eps_nadir(c, clr14=np.where(np.isfinite(s), c.clr[14] - s, c.clr[14]))
    nwc = maximum_filter(b14, 21)
    out["d_nwc21"] = C.eps_nadir(c, clr14=nwc)
    out["d_nwc21_min"] = C.eps_nadir(c, clr14=np.minimum(c.clr[14], nwc))
    lrc_dist = np.where(r >= 0, np.hypot(r - np.indices(r.shape)[0], k - np.indices(r.shape)[1]), np.nan)
    return out, lrc_dist


def main():
    acc = {}
    EV, DI, LD = [], [], []
    for h in C.E.ELIGE:
        c = C.CS.Cuadro(h)
        cand, ld = candidatas(c)
        for n, v in cand.items():
            acc.setdefault(n, []).append(v.ravel())
        EV.append(c.ev.ravel()); DI.append(C.distancia_espesa(c).ravel()); LD.append(ld.ravel())
        print(h, flush=True)
    ev, dist, ld = map(np.concatenate, (EV, DI, LD))
    out = {"cuadros": C.E.ELIGE}
    for n, v in acc.items():
        out[n] = C.resumen(ev, np.concatenate(v), dist)
    s0 = np.isfinite(ev) & (ev >= 0.05) & (ev < 0.3)
    out["distancia_al_lrc_tenue_px_p5_p50_p95"] = [float(x) for x in np.nanpercentile(ld[s0], [5, 50, 95])]
    out["tenue_que_es_su_propio_lrc"] = float(np.mean(ld[s0] == 0))
    with open(os.path.join(C.RES, "lrc_explorar_1a5.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    for n in acc:
        r = out[n]
        print(f"{n:12s}", {k: (v["frac_le_001"], round(v["deps_mediana"], 4)) for k, v in r.items() if k.startswith("eps_")},
              {k: round(v["deps_mediana"], 4) for k, v in r["tenue_0.05_0.3_por_distancia"].items()})
    print("dist LRC", out["distancia_al_lrc_tenue_px_p5_p50_p95"], out["tenue_que_es_su_propio_lrc"])


if __name__ == "__main__":
    main()
