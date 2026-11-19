"""H10: senal espectral en el sector REAV (R), en la huella VOLCAT (V) y en el sector opuesto (O), contra
control pareado por BT11 (criterio seccion 6). Jornadas 25-10, 27-10 y 28-10 (episodios con direccion).

Regla de asignacion de slots (detalle de implementacion fijado antes de ver numeros de senal): cuando un slot
cae en ventanas de dos episodios de la misma jornada, se asigna al episodio con la hora de inicio mas reciente
que no sea posterior al slot (la columna mas reciente); si ninguna empezo aun, al de inicio mas temprano.
Salida: h10/senal_h10.json y texto por pantalla. Uso: python -I senal_h10.py"""
import os, sys, json
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h10 as C  # noqa: E402

JORN = ("25-10", "27-10", "28-10")
HU = np.load(os.path.join(C.WORK, "huellas_h10.npz"))
rng = np.random.default_rng(20261119)


def asignar():
    por = {}
    for e in C.EP:
        if e[1] in JORN and e[5] is not None:
            for s in C.slots(e):
                por.setdefault((e[1], s), []).append(e)
    out = []
    for (j, s), es in sorted(por.items(), key=lambda x: x[0][1]):
        prev = [e for e in es if C.P(e[2]) <= s]
        e = max(prev, key=lambda e: C.P(e[2])) if prev else min(es, key=lambda e: C.P(e[2]))
        out.append((j, s, e))
    return out


def senales(sc):
    btd = sc["b14"] - sc["b15"]
    return {"BTD": btd, "S": btd + (sc["b14"] - sc["b11"]), "BT11": sc["b14"]}


def auc(pos, ctl):
    """P(pos < ctl) + 0,5 P(pos = ctl): probabilidad de que el escenario sea mas 'ceniza' que el control."""
    pos = pos[np.isfinite(pos)]; ctl = ctl[np.isfinite(ctl)]
    if len(pos) == 0 or len(ctl) == 0:
        return np.nan
    allv = np.concatenate([pos, ctl])
    from scipy.stats import rankdata
    r = rankdata(allv)
    u = r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2
    return 1.0 - u / (len(pos) * len(ctl))


if __name__ == "__main__":
    filas, datos = [], {}
    for j, s, e in asignar():
        h_km = C.ZC_KM + e[4] / 1000.0
        sc = C.escena(s)
        f = dict(jornada=j, slot=f"{s:%Y-%m-%d %H:%M}", ep=e[0], az=e[5], H=e[4])
        if sc is None:
            f["estado"] = "sin_escena"; filas.append(f); continue
        V = HU[C.k(s)] if C.k(s) in HU.files else np.zeros(C.LAT.shape, bool)
        Vd = ndimage.binary_dilation(V, structure=np.ones((3, 3), bool))
        R = C.cuna(e[5], h_km) & ~Vd
        O = C.cuna((e[5] + 180.0) % 360.0, h_km) & ~Vd
        U = R | O | V
        m0 = np.nanmedian(sc["b14"][U])
        best = None
        for c in C.candidatos(s):
            cs = C.escena(c)
            if cs is None:
                continue
            d = np.nanmedian(cs["b14"][U]) - m0
            if np.isfinite(d) and (best is None or abs(d) < abs(best[1])):
                best = (c, d, cs)
        f.update(nR=int(R.sum()), nO=int(O.sum()), nV=int(V.sum()), bt11_med=round(float(m0), 2))
        if best is None or abs(best[1]) > 3.0:
            f["estado"] = "sin_control"; f["dbt11"] = None if best is None else round(float(best[1]), 2)
            filas.append(f); continue
        f.update(estado="pareada", control=f"{best[0]:%Y-%m-%d}", dbt11=round(float(best[1]), 2))
        sp, scn = senales(sc), senales(best[2])
        for reg, M in (("R", R), ("V", V), ("O", O)):
            for sg in sp:
                datos.setdefault((j, reg, sg), []).append((sp[sg][M], scn[sg][M]))
        filas.append(f)

    res = {}
    for (j, reg, sg), lst in sorted(datos.items()):
        pos = np.concatenate([a for a, b in lst]); ctl = np.concatenate([b for a, b in lst])
        a = auc(pos, ctl)
        bs = []
        n = len(lst)
        if n >= 2:
            for _ in range(1000):
                ii = rng.integers(0, n, n)
                pp = np.concatenate([lst[i][0] for i in ii]); cc = np.concatenate([lst[i][1] for i in ii])
                if len(pp):
                    bs.append(auc(pp, cc))
        lo, hi = (np.nanpercentile(bs, [2.5, 97.5]) if bs else (np.nan, np.nan))
        extra = {}
        if sg == "BTD":
            extra = dict(f_pos=float(np.mean(pos[np.isfinite(pos)] < -1)) if np.isfinite(pos).any() else np.nan,
                         f_ctl=float(np.mean(ctl[np.isfinite(ctl)] < -1)) if np.isfinite(ctl).any() else np.nan)
        if sg == "S":
            extra = dict(f_pos=float(np.mean(pos[np.isfinite(pos)] < 1.5)) if np.isfinite(pos).any() else np.nan,
                         f_ctl=float(np.mean(ctl[np.isfinite(ctl)] < 1.5)) if np.isfinite(ctl).any() else np.nan)
        res[f"{j}|{reg}|{sg}"] = dict(auc=float(a), ic=[float(lo), float(hi)], escenas=n, px=int(np.isfinite(pos).sum()),
                                     med_pos=float(np.nanmedian(pos)) if len(pos) else np.nan,
                                     med_ctl=float(np.nanmedian(ctl)) if len(ctl) else np.nan, **extra)
    json.dump(dict(filas=filas, res=res), open(os.path.join(C.WORK, "senal_h10.json"), "w"), indent=1, default=str)
    from collections import Counter
    print("escenas por estado:", Counter((f["jornada"], f["estado"]) for f in filas))
    for kk, v in res.items():
        ex = f" f_pos={v.get('f_pos', float('nan')):.3f} f_ctl={v.get('f_ctl', float('nan')):.3f}" if "f_pos" in v else ""
        print(f"{kk:18s} AUC={v['auc']:.3f} [{v['ic'][0]:.2f}; {v['ic'][1]:.2f}] escenas={v['escenas']:3d} px={v['px']:5d}"
              f" med {v['med_pos']:+.2f}/{v['med_ctl']:+.2f}{ex}")
