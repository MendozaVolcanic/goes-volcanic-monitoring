r"""V102 (auditoría S28b), segundo script: ¿las noches de 2026 que disparan se parecen a las noches de capa baja de 2025?

Por qué: la única razón que justificaría quitar las noches de 3 o más disparos sólo en 2025 es que en 2026 esas
noches sean otra cosa (pluma) y no el mismo episodio de capa baja. S24 midió en B2 qué distingue a los cuadros que
disparan en 2025 (más anillo con ACM 1, anillo menos frío que el control). Aquí se calculan las MISMAS dos variables,
con las mismas fórmulas de s24_medir.py:160-161, en los cuadros de noche de 2026 (hasta el 24-11-2026), y se guarda
el detalle por cuadro (hora, disparo, clase de VOLCAT, tajada) de las noches de 2026 con disparo.

No modifica nada de las carpetas auditadas. Uso: python -I -B v102_noches_2026.py <carpeta_de_salida>
"""
import hashlib
import json
import os
import sys

import numpy as np
from scipy import stats

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s24_dia14_noche", "scripts"))
import s24_medir as X  # noqa: E402

S, B, M = X.S, X.B, X.M
SALIDA = sys.argv[1]


def main():
    os.makedirs(SALIDA, exist_ok=True)
    assert B.NUEVOS[-1] == "2026-11-24" and B.fecha(B.ND - 1) == "2026-11-24"
    estat = np.load(X.ESTAT)
    assert hashlib.sha256(estat.tobytes()).hexdigest()[:16] == X.SHA_ESTAT
    D = S.Detector(ref="2025", con_blanco=True, estat_blanco=estat)
    U0, _ = D.umbral(None)
    ap, ct = M.AP, M.CTRL
    bt25 = np.load(S._npy("bt11"), mmap_mode="r")
    bt26dev, _, _ = B.cargar_dev()
    bt26nue = np.load(os.path.join(B.TRAB, "nuevo_bt11.npy"), mmap_mode="r")

    def cov(b, acm):
        b = np.asarray(b)
        return float((acm[ap] == 1).mean()), float(np.nanmedian(b[ap]) - np.nanmedian(b[ct]))

    r25 = []
    for d in D.DIASR:
        Ud, _ = D.umbral(d)
        F, ev = S.disparos(D.SR, D.KR, d, Ud)
        for s in X.NOCHE:
            if ev[s]:
                a, i = cov(bt25[d, s], D.acmR[d, s])
                r25.append((f"{S.T0R + S.timedelta(days=d):%Y-%m-%d}", s, bool(F[s]), a, i))
    r26 = []
    for d in range(B.ND):
        F, ev = S.disparos(D.ST, D.KT, d, U0)
        for s in X.NOCHE:
            if ev[s]:
                b = bt26dev[d, s] if d < B.NDEV else bt26nue[d - B.NDEV, s]
                a, i = cov(b, D.acmT[d, s])
                r26.append((B.fecha(d), s, bool(F[s]), a, i, str(D.CLT[d, s]), int(D.KT[d, s]),
                            float(D.ST[d, s]), U0[s]))
    assert max(r[0] for r in r26) <= "2026-11-24"
    F25 = np.array([r[2] for r in r25])
    F26 = np.array([r[2] for r in r26])
    out = {"n": {"2025_evaluados": len(r25), "2025_disparos": int(F25.sum()),
                 "2026_evaluados": len(r26), "2026_disparos": int(F26.sum())}}

    def med(v):
        return None if len(v) == 0 else round(float(np.median(v)), 4)

    for j, nom in ((3, "acm1"), (4, "inv")):
        x25 = np.array([r[j] for r in r25])
        x26 = np.array([r[j] for r in r26])
        ok25, ok26 = np.isfinite(x25), np.isfinite(x26)
        a, b, c, e = x25[F25 & ok25], x25[~F25 & ok25], x26[F26 & ok26], x26[~F26 & ok26]
        out[nom] = {
            "mediana_2025_disparan": med(a), "mediana_2025_no": med(b),
            "mediana_2026_disparan": med(c), "mediana_2026_no": med(e),
            "p_MW_2025_disparan_vs_no": float(stats.mannwhitneyu(a, b, alternative="two-sided")[1]),
            "p_MW_2026_disparan_vs_no": float(stats.mannwhitneyu(c, e, alternative="two-sided")[1]) if len(c) else None,
            "p_MW_2026_disparan_vs_2025_disparan": float(stats.mannwhitneyu(c, a, alternative="two-sided")[1]) if len(c) else None,
            "p_MW_2026_disparan_vs_2025_no": float(stats.mannwhitneyu(c, b, alternative="two-sided")[1]) if len(c) else None}
    # por noche de 2026 con disparo
    noches = sorted({r[0] for r in r26 if r[2]})
    det = {}
    for k in noches:
        rr = [r for r in r26 if r[0] == k]
        ff = [r for r in rr if r[2]]
        det[k] = {"evaluados": len(rr), "disparos": len(ff),
                  "horas_disparo_UTC": [M.hhmm(r[1]) for r in ff],
                  "clase_VOLCAT_en_disparos": [r[5] for r in ff],
                  "clases_VOLCAT_de_la_noche": {c: sum(1 for r in rr if r[5] == c) for c in sorted({r[5] for r in rr})},
                  "tajadas": [r[6] for r in ff],
                  "acm1_mediana_disparos": med([r[3] for r in ff]), "inv_mediana_disparos": med([r[4] for r in ff]),
                  "acm1_mediana_noche": med([r[3] for r in rr]), "inv_mediana_noche": med([r[4] for r in rr])}
    out["noches_2026_con_disparo"] = det
    # lo mismo por noche de 2025 con 3 o más
    det25 = {}
    for k in sorted({r[0] for r in r25 if r[2]}):
        rr = [r for r in r25 if r[0] == k]
        ff = [r for r in rr if r[2]]
        det25[k] = {"evaluados": len(rr), "disparos": len(ff), "horas_disparo_UTC": [M.hhmm(r[1]) for r in ff],
                    "acm1_mediana_disparos": med([r[3] for r in ff]), "inv_mediana_disparos": med([r[4] for r in ff])}
    out["noches_2025_con_disparo"] = det25
    # clases de VOLCAT de noche en 2026 (para saber cuánto P nocturno hay)
    out["clases_VOLCAT_noche_2026_evaluados"] = {c: sum(1 for r in r26 if r[5] == c) for c in sorted({r[5] for r in r26})}
    json.dump(out, open(os.path.join(SALIDA, "v102_noches_2026.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
