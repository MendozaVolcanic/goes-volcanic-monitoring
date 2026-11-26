r"""S31a, paso 1: inventario SÓLO de VOLCAT (sin el detector). ¿Cuántos cuadros y cuántos días tiene la pluma de
Chillán dibujada fuera de 90° a 180° (fuera del SE habitual)?

Por qué: S30b vio que el anillo del detector S26a apunta al rumbo de la pluma, pero no más que al rumbo de la pluma de
otro día, porque casi todas las plumas van al SE y el anillo ya prefería el SE en 2025 sin pluma. La única forma de
separar "sigue la pluma" de "apunta al SE siempre" son cuadros con la pluma hacia otro lado. Antes de escribir un
criterio hay que saber si existen bastantes DÍAS así (la unidad de los nulos es el día, S28b).

No lee la tabla de disparos de S26a ni nada del detector: sólo las clases de VOLCAT por cuadro (frames_calor.csv y
volcat_clases_22a24nov.csv, regla de H9) y los PNG de VOLCAT guardados en D: (licencia SSEC: las huellas quedan en
D:\goes_notas\s31\s31a\, al repo sólo cifras).

Huella y rumbo con las mismas definiciones de S30b (criterio_2026-11-26.md §1 y §2): huella = unión de los objetos
(8 vecinos, grilla ABI de 2 km) con algún píxel a 10 km o menos del cráter; rumbo = media circular del acimut de sus
píxeles dentro del anillo AMASK (4 a 40 km, sin el bloque 3x3 del cráter). Fuera del SE = rumbo < 90° o > 180°.

Uso: python -I -B s31a_inventario.py
"""
import csv
import json
import os
import sys
import warnings
from collections import Counter, defaultdict

import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
sys.path.insert(0, os.path.join(OV, "h29_pluma_0811", "scripts"))
sys.path.insert(0, os.path.join(OV, "s22a_detector_sectores", "scripts"))
import h29_comun as C29  # noqa: E402
import s22a_medir as M  # noqa: E402  (sólo geometría: AMASK, SEC, AZ, slot)
import s22a_mapas as G  # noqa: E402  (png_volcat)

G.PNG_DIRS.append(r"D:\goes_notas\s22\s22b\volcat_png\frames")
G.PNG_DIRS.append(r"D:\goes_notas\s23\volcat_png\Chile_Central_2_km\frames")
CLASES = [os.path.join(OV, "calor_rayos", "resultados", "frames_calor.csv"),
          os.path.join(OV, "s22b_pluma_vs_nubes", "resultados", "volcat_clases_22a24nov.csv")]
TRAB = r"D:\goes_notas\s31\s31a"
ULTIMO_DIA = "2026-11-24"
ANCLA_KM = 10.0
SE = (90.0, 180.0)

NPIX = M.NY * M.NX
AMASK = M.AMASK.ravel()
AZF = M.AZ.ravel()
SECF = np.full(NPIX, -1, int)
SECF[M.AP] = M.SEC
DISTF = C29.DIST.ravel()


def rumbo_circ(az):
    if not len(az):
        return None, None
    a = np.radians(az)
    c, s = np.cos(a).mean(), np.sin(a).mean()
    return float(np.degrees(np.arctan2(s, c)) % 360), float(np.hypot(c, s))


def leer_clases():
    cl = {}
    for fn in CLASES:
        with open(fn, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                dia = r["dt"][:10]
                if dia <= ULTIMO_DIA:
                    cl[(dia, M.slot(r["dt"][11:16]))] = r["clase"]
    return cl


def huellas(dia, s):
    ash, err = G.png_volcat(dia, s)
    if ash is None:
        return err, None, None
    lab, n = ndimage.label(ash, structure=np.ones((3, 3), int))
    cerca = np.unique(lab[(C29.DIST <= ANCLA_KM) & (lab > 0)]) if n else np.array([], int)
    h = np.flatnonzero(np.isin(lab, cerca[cerca > 0]).ravel()) if n else np.array([], int)
    todo40 = np.flatnonzero((ash & (C29.DIST <= 40.0)).ravel())
    return "ok", h, todo40


def fuera_se(r):
    return r is not None and not (SE[0] <= r <= SE[1])


def main():
    os.makedirs(RES, exist_ok=True)
    os.makedirs(TRAB, exist_ok=True)
    cl = leer_clases()
    dias = sorted({d for d, _ in cl})
    print("clases:", dias[0], "a", dias[-1], len(dias), "días;", Counter(cl.values()), flush=True)
    filas, guardar = [], {}
    for (dia, s), c in sorted(cl.items()):
        if c not in ("P", "otro"):
            continue
        st, h, t40 = huellas(dia, s)
        f = {"dia": dia, "hora": M.hhmm(s), "clase": c, "png": st}
        if st == "ok":
            ring = h[AMASK[h]]
            r, R = rumbo_circ(AZF[ring])
            r40, R40 = rumbo_circ(AZF[t40[AMASK[t40]]])
            f.update({"huella_px": len(h), "huella_px_anillo": len(ring),
                      "tajadas": " ".join(str(x) for x in sorted(set(SECF[ring]))),
                      "tajada_moda": int(np.argmax(np.bincount(SECF[ring], minlength=12))) if len(ring) else "",
                      "rumbo": None if r is None else round(r, 1), "R_circ": None if R is None else round(R, 2),
                      "fuera_SE": "" if r is None else int(fuera_se(r)),
                      "dist_max_km": round(float(DISTF[h].max()), 1) if len(h) else None,
                      "todo40_px_anillo": int(AMASK[t40].sum()),
                      "rumbo_todo40": None if r40 is None else round(r40, 1),
                      "fuera_SE_todo40": "" if r40 is None else int(fuera_se(r40))})
            if c == "P":
                guardar[f"{dia}_{s:03d}"] = h
        filas.append(f)
    np.savez_compressed(os.path.join(TRAB, "huellas_P.npz"), **guardar)
    campos = ["dia", "hora", "clase", "png", "huella_px", "huella_px_anillo", "tajadas", "tajada_moda", "rumbo", "R_circ",
              "fuera_SE", "dist_max_km", "todo40_px_anillo", "rumbo_todo40", "fuera_SE_todo40"]
    with open(os.path.join(RES, "s31a_inventario_volcat.csv"), "w", encoding="utf-8", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)

    # resumen por día (sólo P, la clase del criterio)
    res = {"clases_desde": dias[0], "clases_hasta": dias[-1], "dias_con_clase": len(dias),
           "conteo_clases": dict(Counter(cl.values())), "por_dia_P": {}, "otro_por_dia": {}}
    pd_ = defaultdict(lambda: Counter())
    for f in filas:
        if f["clase"] != "P":
            continue
        q = pd_[f["dia"]]
        q["P"] += 1
        q["con_png"] += f["png"] == "ok"
        q["con_rumbo"] += f.get("rumbo") is not None
        q["fuera_SE"] += f.get("fuera_SE") == 1
        q["fuera_SE_todo40"] += f.get("fuera_SE_todo40") == 1
    for d, q in sorted(pd_.items()):
        rr = [f["rumbo"] for f in filas if f["dia"] == d and f["clase"] == "P" and f.get("rumbo") is not None]
        med, Rd = rumbo_circ(np.array(rr)) if rr else (None, None)
        res["por_dia_P"][d] = {**q, "rumbos": rr, "rumbo_medio_dia": None if med is None else round(med, 1)}
    po = defaultdict(lambda: Counter())
    for f in filas:
        if f["clase"] == "otro" and f["png"] == "ok":
            q = po[f["dia"]]
            q["otro"] += 1
            q["con_rumbo_anclado"] += f.get("rumbo") is not None
            q["fuera_SE_anclado"] += f.get("fuera_SE") == 1
    res["otro_por_dia"] = {d: dict(q) for d, q in sorted(po.items())}
    P = [f for f in filas if f["clase"] == "P"]
    res["totales_P"] = {"P": len(P), "con_png": sum(f["png"] == "ok" for f in P),
                        "con_rumbo": sum(f.get("rumbo") is not None for f in P),
                        "fuera_SE": sum(f.get("fuera_SE") == 1 for f in P),
                        "dias_con_P": len(pd_),
                        "dias_con_algun_P_fuera_SE": sorted(d for d, q in pd_.items() if q["fuera_SE"]),
                        "dias_con_algun_P_fuera_SE_todo40": sorted(d for d, q in pd_.items() if q["fuera_SE_todo40"])}
    json.dump(res, open(os.path.join(RES, "s31a_inventario_volcat.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))
    print(json.dumps(res["totales_P"], ensure_ascii=False), flush=True)
    for d, q in res["por_dia_P"].items():
        print(d, {k: v for k, v in q.items()}, flush=True)
    print("otro:", res["otro_por_dia"], flush=True)


if __name__ == "__main__":
    main()
