r"""S28b F4: ¿la compuerta de nubes de Antuco y Longaví (S27a, S28a) depende de constantes de Chillán?

Por qué: el "nublado de costumbre" que decide qué nube es dinámica (y por eso qué cuadros pasan la compuerta y qué
píxeles se borran) se arma en S23/S25a con los cuadros despejados por E1 de CHILLÁN (`despejada("chillan")`), y el de
2026 congelado (`estat_2026.npy`) además con los cuadros N de VOLCAT de CHILLÁN. S28a usa esos mismos mapas en las
vecinas (2025 el de Chillán 2025, 2026 el congelado). Si el mapa de 2026 difiere del de 2025 por cómo se eligió y no
por el cielo, la fracción de cuadros que pasa la compuerta cambia entre años por construcción, y la razón 2026/2025 de
S28a compara cuadros elegidos distinto. Aquí se mide sólo con la máscara ACM (no se calcula BTD, ni S, ni disparos):
fracción de cuadros que pasan la compuerta (nube dinámica en el anillo <= 0,5) con los mapas usados, y con un mapa
propio de cada vecina construido IGUAL en los dos años (todos los cuadros con dato, E1 de la vecina).
Días: 21-09 a 21-11-2025 y 21-09 a 24-11-2026 (nada posterior al 24-11-2026).

Uso: python -I f4_costumbre_vecinas.py   (D:\goes_notas\s28\s28b\f4\f4_costumbre_vecinas.json)
"""
import hashlib
import json
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(OV, "s25a_crater", "scripts"))
import s25a_medir as Z  # noqa: E402  (costumbre, constantes; importa s23, s22b, s22a)

B, M, H24, C29 = Z.B, Z.M, Z.H24, Z.C29
OUT = r"D:\goes_notas\s28\s28b\f4"
SITIOS = {"antuco": (-37.41, -71.35), "longavi": (-36.19, -71.16), "chillan": None}
NOCHE, DIA = range(18, 54), range(90, 126)     # 03-09 UTC y 15-21 UTC (las de S27a D4; NOCHE = la de S26a)


def costumbre_sitio(acm, usar, sitio):
    """Z.costumbre con E1 del sitio en vez de E1 de Chillán (misma regla: COSTUMBRE_VENT, MIN_COSTUMBRE, 0,5)."""
    e1 = H24.despejada(sitio, acm)
    ss_all = [(d, s) for d in range(acm.shape[0]) for s in range(144) if usar[d, s] and e1[d, s]]
    nub = np.array([(acm[d, s] >= 2) & (acm[d, s] <= 3) for d, s in ss_all])
    ss = np.array([s for _, s in ss_all])
    est = np.zeros((144, acm.shape[2]), bool)
    for s in range(144):
        dd = np.abs(ss - s) % 144
        dd = np.minimum(dd, 144 - dd)
        for w in B.COSTUMBRE_VENT:
            m = dd <= w
            if m.sum() >= B.MIN_COSTUMBRE:
                est[s] = nub[m].mean(0) >= B.COSTUMBRE
                break
    return est


def anillo_de(sitio):
    if sitio == "chillan":
        return M.AP
    la, lo = SITIOS[sitio]
    d = C29.hav(C29.LAT, C29.LON, la, lo)
    i, j = np.unravel_index(np.argmin(d), d.shape)
    bl = np.zeros_like(d, bool)
    bl[i - 1:i + 2, j - 1:j + 2] = True
    return np.flatnonzero(((d >= M.R_IN) & (d <= M.R_OUT) & ~bl).ravel())


def pasa(acm, est, ring):
    hay = (acm != 255).any(2)
    a = acm[:, :, ring]
    dyn = (a >= 2) & (a <= 3) & ~est[None, :, ring]
    fd = dyn.mean(2)
    g = (fd <= B.G_MAX) & hay
    return g, hay


def tasas(g, hay):
    return {p: round(float(g[:, list(r)].sum() / max(hay[:, list(r)].sum(), 1)), 4)
            for p, r in (("noche", NOCHE), ("dia", DIA))}


def main():
    acm25 = np.load(Z._npy("r25_acm"))
    acm26 = np.concatenate([np.load(os.path.join(B.TRAB, "dev_acm.npy")),
                            np.load(os.path.join(B.TRAB, "nuevo_acm.npy"))])
    assert acm26.shape[0] == 65, acm26.shape
    hay25 = (acm25 != 255).any(2)
    hay26 = (acm26 != 255).any(2)
    est26 = np.load(Z.ESTAT26)
    sha = hashlib.sha256(est26.tobytes()).hexdigest()[:16]
    est25_ch = Z.costumbre(acm25, hay25)           # E1 de Chillán (como S28a para la zona; el del anillo usa m1 finito)
    out = {"sha_estat26": sha, "sitios": {}}
    for sitio in ("chillan", "antuco", "longavi"):
        ring = anillo_de(sitio)
        g25u, h25 = pasa(acm25, est25_ch, ring)
        g26u, h26 = pasa(acm26, est26, ring)
        r = {"pixeles_anillo": int(len(ring)),
             "usado_por_S28a": {"2025": tasas(g25u, h25), "2026": tasas(g26u, h26)},
             "costumbre_pixeles_marcados_media_por_hora": {"2025_chillan": round(float(est25_ch[:, ring].sum(1).mean()), 1),
                                                          "2026_congelado": round(float(est26[:, ring].sum(1).mean()), 1)}}
        if sitio != "chillan":
            e25 = costumbre_sitio(acm25, hay25, sitio)
            e26 = costumbre_sitio(acm26, hay26, sitio)
            g25p, _ = pasa(acm25, e25, ring)
            g26p, _ = pasa(acm26, e26, ring)
            r["propio_igual_en_ambos_años"] = {"2025": tasas(g25p, h25), "2026": tasas(g26p, h26)}
            r["costumbre_pixeles_marcados_media_por_hora"].update(
                {"2025_propio": round(float(e25[:, ring].sum(1).mean()), 1),
                 "2026_propio": round(float(e26[:, ring].sum(1).mean()), 1)})
            r["cuadros_distintos_en_compuerta_2026_usado_vs_propio"] = int((g26u != g26p)[h26].sum())
            r["cuadros_distintos_en_compuerta_2025_usado_vs_propio"] = int((g25u != g25p)[h25].sum())
        for k in ("usado_por_S28a", "propio_igual_en_ambos_años"):
            if k in r:
                r[k]["razon_2026_2025"] = {p: (round(r[k]["2026"][p] / r[k]["2025"][p], 3) if r[k]["2025"][p] else None)
                                           for p in ("noche", "dia")}
        out["sitios"][sitio] = r
        print(sitio, json.dumps(r, ensure_ascii=False), flush=True)
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "f4_costumbre_vecinas.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)


if __name__ == "__main__":
    main()
