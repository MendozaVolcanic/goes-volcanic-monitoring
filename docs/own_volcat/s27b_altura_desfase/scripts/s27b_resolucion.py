r"""S27b, paso previo: ¿qué resolución en rapidez y en altura se puede esperar con cuadros cada 10 min y píxeles de
2,1 x 2,8 km? Sin un solo dato de pluma: sólo geometría (paralaje de GOES-19 sobre Chillán) y tres perfiles de viento
GFS que S22c ya había bajado y publicado (08-11 15:00 y 18:30, 14-11 18:00 UTC).

Cómo: se pone una pluma sintética a la altura h_real, que sale del cráter y viaja con el viento GFS de esa altura
(rapidez y rumbo) durante Δt + 5 min (la emisión cae a mitad del cuadro). Se calcula dónde la vería GOES-19 (paralaje
a h_real) y se le aplica la regla del criterio §3 tal cual: banda por rapidez, banda por rumbo (S22c) y banda por las
dos. Sólo se guardan los casos que caen dentro del anillo (6 a 38 km). El resultado dice qué anchos de banda esperar
y si h_real queda dentro (que la regla no se equivoque en el caso ideal).

Uso: python -I s27b_resolucion.py   -> resultados/s27b_resolucion.json
"""
import json
import math
import os
import sys
from datetime import datetime

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import s27b_comun as K  # noqa: E402

PERFILES = ["2026-11-08 15:00", "2026-11-08 18:30", "2026-11-14 18:00"]
H_REAL = [3.6, 4.0, 4.7, 5.5, 6.5, 8.0, 10.0, 12.0]
DTS = list(range(10, 121, 10))
RES = os.path.join(os.path.dirname(AQUI), "resultados")


def destino(h, dt_min, vw):
    tw, V = vw
    i = int(np.argmin(np.abs(K.ZS - h)))
    d = V[i] * (dt_min + K.DT_EMISION_MIN / 2) * 60.0 / 1000.0
    az = math.radians(tw[i])
    lat = K.CLAT + d * math.cos(az) / K.KY
    lon = K.CLON + d * math.sin(az) / K.KX
    la, lo = K.aparente(lat, lon, h)
    return d, float(V[i]), float(tw[i]), la, lo


def main():
    out = {"nota": "estimación previa, sin datos de pluma; perfiles GFS ya publicados por S22c", "casos": []}
    for p in PERFILES:
        vw = K.C22.viento(datetime.strptime(p, "%Y-%m-%d %H:%M"))
        for h in H_REAL:
            for dt in DTS:
                d, V, tw, la, lo = destino(h, dt, vw)
                if not 6.0 <= d <= 38.0:
                    continue
                r = K.alturas(la, lo, dt, vw)
                fila = {"perfil": p, "h_real": h, "V_real": round(V, 1), "hacia": round(tw), "dt_min": dt,
                        "d_real_km": round(d, 1)}
                for k in ("rapidez", "rumbo", "rapidez_y_rumbo"):
                    b = r[k]
                    fila[k] = {"banda": b["banda"], "ancho": b["ancho"], "restringe": b["restringe"],
                               "separa_capas": b.get("separa_capas"),
                               "contiene_h_real": bool(b["banda"] is not None
                                                       and b["banda"][0] - 1e-9 <= h <= b["banda"][1] + 1e-9)}
                fila["h_estrella"] = r["h_estrella"]
                out["casos"].append(fila)
    # resumen por perfil y altura real
    res = []
    for p in PERFILES:
        for h in H_REAL:
            cs = [c for c in out["casos"] if c["perfil"] == p and c["h_real"] == h]
            if not cs:
                continue
            fila = {"perfil": p, "h_real": h, "V_real": cs[0]["V_real"], "n_dt": len(cs),
                    "dt_min_rango": [cs[0]["dt_min"], cs[-1]["dt_min"]]}
            for k in ("rapidez", "rapidez_y_rumbo"):
                an = [c[k]["ancho"] for c in cs if c[k]["ancho"] is not None]
                fila[k] = {"ancho_mediano": float(np.median(an)) if an else None,
                           "frac_restringe": round(float(np.mean([c[k]["restringe"] for c in cs])), 2),
                           "frac_separa_capas": round(float(np.mean([bool(c[k]["separa_capas"]) for c in cs])), 2),
                           "frac_contiene_h_real": round(float(np.mean([c[k]["contiene_h_real"] for c in cs])), 2)}
            res.append(fila)
            print(f"{p} h={h:>4} V={fila['V_real']:>5} Δt {fila['dt_min_rango']}: "
                  f"rapidez ancho {fila['rapidez']['ancho_mediano']} restr {fila['rapidez']['frac_restringe']} "
                  f"separa {fila['rapidez']['frac_separa_capas']} | +rumbo ancho "
                  f"{fila['rapidez_y_rumbo']['ancho_mediano']} restr {fila['rapidez_y_rumbo']['frac_restringe']} "
                  f"separa {fila['rapidez_y_rumbo']['frac_separa_capas']} contiene "
                  f"{fila['rapidez_y_rumbo']['frac_contiene_h_real']}", flush=True)
    out["resumen"] = res
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "s27b_resolucion.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
