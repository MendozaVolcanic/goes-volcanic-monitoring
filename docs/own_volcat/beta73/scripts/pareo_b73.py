"""beta73: control pareado por BT11 (mirando SOLO C14), criterio seccion 3. Misma regla que comun_h3.pareo.
Salida: pareo_b73.json, y gfs_ctrl_args.txt con las horas de control para fetch_gfs_b73.py."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import os, json
import numpy as np
import comun_b73 as C

if __name__ == "__main__":
    HU = np.load(os.path.join(C.HERE, "huellas_b73.npz")); META = json.load(open(os.path.join(C.HERE, "huellas_b73.json")))
    out, ctrl = [], []
    print("== Pareo de control por BT11 (C14), |dif mediana huella| <= 3 K")
    for dt, est in C.positivos():
        kk = C.k(dt); m = META[kk]
        if m["estado"] != "ok":
            print(f"{kk} {est}: DESCARTADO antes de medir ({m['estado']}, n_px={m['n_px']})")
            out.append({"pos": kk, "estrato": est, "estado": m["estado"]}); continue
        hv = HU["h_" + kk]; s = C.load(dt)
        if s is None:
            print(f"{kk} {est}: sin escena L1b"); out.append({"pos": kk, "estrato": est, "estado": "sin_l1b"}); continue
        m0 = float(np.nanmedian(s[14][hv])); filas = []
        for c in C.candidatos(dt):
            sc = C.load(c)
            filas.append((c, None if sc is None else float(np.nanmedian(sc[14][hv])) - m0))
        okf = [(c, d) for c, d in filas if d is not None and np.isfinite(d)]
        cb, db = min(okf, key=lambda x: abs(x[1])) if okf else (None, None)
        est_p = "ok" if (cb is not None and abs(db) <= 3.0) else "sin_control"
        txt = " ".join(f"{c:%d-%m}:{'NA' if d is None else f'{d:+.1f}'}" for c, d in filas)
        print(f"{kk} {est} n={int(hv.sum())} BT11med={m0:.2f} K -> control {cb:%Y-%m-%d} dBT11={db:+.2f} K [{est_p}] | {txt}")
        out.append({"pos": kk, "estrato": est, "estado": est_p, "n_px": int(hv.sum()), "bt11_pos": m0,
                    "ctrl": C.k(cb) if cb is not None else None, "dbt11": db,
                    "n_cand_con_escena": len(okf), "faltan": [C.k(c) for c, d in filas if d is None]})
        if est_p == "ok":
            ctrl.append(f"{cb:%Y%m%d%H%M}")
    json.dump(out, open(os.path.join(C.HERE, "pareo_b73.json"), "w"), indent=1)
    open(os.path.join(C.HERE, "gfs_ctrl_args.txt"), "w").write(" ".join(ctrl))
    print("pares ok:", sum(o["estado"] == "ok" for o in out), "de", len(out))
