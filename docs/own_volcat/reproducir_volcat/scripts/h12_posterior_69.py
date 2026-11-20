"""H12, diagnostico POSTERIOR (no decide, escrito despues de ver h12_resultado.txt): Test 3 + 6 de 9 por escena.

Uso: python h12_posterior_69.py <salida.txt>
Por que: en los pares, la variante T3 + 6 de 9 marco 23 % (A) y 37 % (B) de los cuadros con pluma contra 3 % de
los controles y 0 % en cumbres y llano. Antes de proponerla como hipotesis nueva hay que saber cuanto dispara en
las 795 escenas de E2 con la vara del 17-11 (objeto anclado de >= 2 px con uno a <= 10 km; coincidencia con la
ceniza VOLCAT dilatada 1 px a <= 30 km). Mismos datos que el informativo de h12_analisis (feat_e2).
"""
import os, sys
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h11 as C  # noqa: E402
import comun_h12 as H  # noqa: E402

SHAPE = C.LAT.shape


def escena(kk):
    f = H.feat(C.dtk(kk)); D = H.dist_crater()
    t = np.zeros(SHAPE, bool); t3 = H.t3(f["btd"], f["btd"] + f["btd_bias"]); t[f["ys"][t3], f["xs"][t3]] = True
    n9 = ndimage.convolve(t.astype(float), np.ones((3, 3)), mode="constant")
    m = t & (n9 >= 6)
    lab, n = ndimage.label(m, np.ones((3, 3))); anc = np.zeros(SHAPE, bool)
    for i in range(1, n + 1):
        o = lab == i
        if o.sum() >= 2 and (D[o] <= 10).any():
            anc |= o
    ash = np.zeros(SHAPE, bool); a = f["ash"].astype(bool); ash[f["ys"][a], f["xs"][a]] = True
    ashd = ndimage.binary_dilation(ash, np.ones((3, 3), bool))
    sel = m & (D <= 30)
    return {"tipo": str(f["tipo"]), "est": "N" if float(f["sza"]) >= 80 else "D", "jor": H.jornada(C.dtk(kk)),
            "anc": bool(anc.any()), "n30": int(sel.sum()), "dentro": int((sel & ashd).sum())}


if __name__ == "__main__":
    R = [escena(k) for k in sorted(H.escenas_e2())]
    L = ["T3 + 6 de 9 por escena (POSTERIOR, no decide). Vara del 17-11 aplicada a las 795 escenas de E2."]
    for tipo in ("pos", "neg", "manto"):
        for est in ("D", "N", None):
            v = [r for r in R if r["tipo"] == tipo and (est is None or r["est"] == est)]
            if v:
                L.append(f"  {tipo:5s} {est or 'todos':5s} objeto anclado: {sum(r['anc'] for r in v)} de {len(v)} = {np.mean([r['anc'] for r in v]):.3f}")
    neg = [r for r in R if r["tipo"] == "neg"]
    pj = {}
    for r in neg:
        pj[r["jor"]] = pj.get(r["jor"], 0) + r["anc"]
    L.append(f"  negativos: maximo por jornada {max(pj.values())} ({max(pj, key=pj.get)}); jornadas con > 3: {sum(v > 3 for v in pj.values())}")
    pos = [r for r in R if r["tipo"] == "pos"]
    n30 = sum(r["n30"] for r in pos); de = sum(r["dentro"] for r in pos)
    L.append(f"  coincidencia (positivos, px a <= 30 km dentro de la ceniza VOLCAT dilatada 1 px): {de} de {n30} = {de / max(n30, 1):.3f}")
    pjp = {}
    for r in pos:
        a, b = pjp.get(r["jor"], (0, 0)); pjp[r["jor"]] = (a + r["anc"], b + 1)
    L.append("  positivos por jornada: " + "; ".join(f"{j} {a}/{b}" for j, (a, b) in sorted(pjp.items())))
    txt = "\n".join(L)
    open(sys.argv[1], "w", encoding="utf-8").write(txt)
    print(txt)
