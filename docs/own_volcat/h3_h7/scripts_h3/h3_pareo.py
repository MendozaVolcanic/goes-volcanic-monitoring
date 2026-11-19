"""H3 paso 2b: pareo del control por BT11 (mirando SOLO C14) y lista de horas GFS necesarias.
Salida: h3/pareo.json y texto en pantalla (va a h3_resultado.txt)."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))  # modulos propios, explicito (python -I)
import os, json
import numpy as np
import comun_h3 as C
from fetch_gfs import archivo

if __name__ == "__main__":
    out, horas = [], set()
    print("== Pareo de control por BT11 (C14), criterio: |dif mediana huella| <= 3 K")
    for caso, dt, m in C.positivos():
        kk = C.k(dt)
        if m["estado"] != "ok":
            print(f"caso {caso} {kk}: DESCARTADO antes de medir ({m['estado']}, n_px={m.get('n_px')})")
            out.append({"caso": caso, "pos": kk, "estado": m["estado"]}); continue
        hv = C.HUE[kk]
        if C.load(dt) is None:
            print(f"caso {caso} {kk}: sin escena L1b"); out.append({"caso": caso, "pos": kk, "estado": "sin_l1b"}); continue
        m0, (cb, dbest), filas = C.pareo(caso, dt, hv)
        txt = " ".join(f"{c:%d-%m}:{'NA' if d is None else f'{d:+.1f}'}" for c, d in filas)
        estado = "ok" if (cb is not None and abs(dbest) <= 3.0) else "sin_control"
        print(f"caso {caso} {kk} n={int(hv.sum())} BT11med={m0:.2f} K -> control {cb:%Y-%m-%d} dBT11={dbest:+.2f} K [{estado}] | {txt}")
        out.append({"caso": caso, "pos": kk, "estado": estado, "n_px": int(hv.sum()), "bt11_pos": m0,
                    "ctrl": C.k(cb) if cb is not None else None, "dbt11": dbest,
                    "faltan": [f"{c:%Y%m%d}" for c, d in filas if d is None]})
        horas.add(archivo(dt)[0])
        if estado == "ok":
            horas.add(archivo(cb)[0])
    json.dump(out, open(os.path.join(C.HERE, "pareo.json"), "w"), indent=1)
    open(os.path.join(C.HERE, "gfs_horas.txt"), "w").write(" ".join(f"{h:%Y%m%d%H%M}" for h in sorted(horas)))
    print("horas GFS necesarias:", len(horas))
