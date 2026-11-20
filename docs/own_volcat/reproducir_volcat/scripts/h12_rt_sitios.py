"""H12: cielo despejado y nube negra en la huella trasladada a Antuco, Nevado de Longavi y el llano.

Uso: python h12_rt_sitios.py contar          (pareo del conjunto B y numero de pixeles, sin modelo)
     python h12_rt_sitios.py correr [n_proc] (modelo radiativo, reanudable)

Por que: el Test 3 depende del cielo despejado modelado, que en la cumbre de Chillan tiene el error de terreno
del GFS. Para saber si el test mide ese error y no la pluma, se aplica a cumbres sin actividad con el mismo tipo
de error, en las mismas escenas y con la misma huella (forma y tamano) trasladada. Mismo modelo de H11
(rt_niveles.tarea, sin cambiar su fisica). Exclusiones del criterio: fuera de la ventana, a menos de 20 km del
crater de Chillan, y ceniza VOLCAT en esa escena.
"""
import os, sys, json
import numpy as np
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h11 as C  # noqa: E402
import comun_h12 as H  # noqa: E402
import rt_niveles as R  # noqa: E402


def pares_todos():
    """[(conjunto, kpos, kctrl, huella en grilla)] de A (H11) y B (pareo nuevo de E2)."""
    out = [("A", p["pos"], p["ctrl"], p["hv"]) for p in C.pares()]
    for q in H.pareo_e2():
        if q["estado"] == "ok":
            out.append(("B", q["pos"], q["ctrl"], H.huella_b_grid(q["pos"])))
    return out


def tareas():
    D = H.dist_crater(); T = []; meta = []
    _cache = {}
    for cj, kp, kc, h in pares_todos():
        for rol, kk in (("pos", kp), ("ctrl", kc)):
            dt = C.dtk(kk)
            if kk not in _cache:
                _cache[kk] = H.ceniza_volcat(dt)
            ash, fuente = _cache[kk]
            for s in H.SITIOS:
                m, fuera = H.trasladar(h, s)
                n0 = int(m.sum())
                m &= D >= 20.0
                n20 = n0 - int(m.sum())
                nash = int((m & ash).sum()); m &= ~ash
                ys, xs = np.nonzero(m)
                out = os.path.join(H.RTSIT, f"{cj}_{kp}_{rol}_{s}.npz")
                meta.append({"conj": cj, "pos": kp, "rol": rol, "escena": kk, "sitio": s, "n_tras": n0, "fuera": fuera,
                             "menos20km": n20, "ceniza": nash, "n": len(ys), "mascara": fuente,
                             "falta": (C.path_gfs(dt) is None) or (H.C.path_escena(dt) is None and not os.path.exists(os.path.join(C.TRABAJO, "cache_e2", kk + ".npz")))})
                if len(ys) and not meta[-1]["falta"]:
                    T.append((out, dt, ys, xs, np.ones(len(ys), bool)))
    json.dump(meta, open(os.path.join(H.OUT, "sitios_meta.json"), "w"), indent=0)
    return T, meta


if __name__ == "__main__":
    T, meta = tareas()
    pe = H.pareo_e2()
    print("pareo B:", {e: sum(1 for q in pe if q["estado"] == e) for e in {q["estado"] for q in pe}})
    print("tareas", len(T), "pixeles", sum(len(t[2]) for t in T), "faltan", sum(m["falta"] for m in meta))
    for s in H.SITIOS:
        mm = [m for m in meta if m["sitio"] == s]
        print(s, "n", sum(m["n"] for m in mm), "fuera", sum(m["fuera"] for m in mm), "<20km", sum(m["menos20km"] for m in mm),
              "ceniza", sum(m["ceniza"] for m in mm), "cuadros vacios", sum(m["n"] == 0 for m in mm), "de", len(mm))
    print("mascaras:", {f: sum(1 for m in meta if m["mascara"] == f) for f in {m["mascara"] for m in meta}})
    if sys.argv[1] == "correr":
        npr = int(sys.argv[2]) if len(sys.argv) > 2 else 8
        T = [t for t in T if not os.path.exists(t[0])]
        T.sort(key=lambda t: -len(t[2]))
        with Pool(npr) as pool:
            for out, msg in pool.imap_unordered(R.tarea, T):
                print(os.path.basename(out), msg, flush=True)
