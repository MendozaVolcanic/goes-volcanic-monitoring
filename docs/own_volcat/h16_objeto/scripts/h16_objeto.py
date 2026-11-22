r"""H16: probabilidad de OBJETO de VOLCAT con su tabla pública (criterio_2026-11-21.md, commit 22c46b1/fcbe3a7).

Por qué existe: la etapa 3 (PR 79) mostró que la probabilidad por píxel de VOLCAT no separa la huella de Chillán.
VOLCAT decide publicar con el objeto (SECO Parte 2, §4.2 y Tabla 4). Este módulo reproduce el término de objeto:
para cada tabla (SSD) los píxeles del objeto caen en casillas (SSL); las 10 casillas con más área son los
clasificadores; cada una se lee en la densidad (área de la casilla, casilla, rango) de la tabla, para ceniza y nube.

Lo LEÍDO está en el criterio §1; lo fijado con objetos de un píxel de Mauna Loa (índices de casilla, β total en la
tabla "opaca" de 8,5 µm, BTD fuera del modo IR) en §2. Entrada: un arreglo por variable con los píxeles del objeto.

Tabla: D:\goes_cache\h16_objeto\ml\lut_objeto.npz (exportada de la HDF4 de SSEC; fuera del repo).
"""
import numpy as np

LUT = r"D:\goes_cache\h16_objeto\ml\lut_objeto.npz"
PRIOR = 0.001                                   # OBJECT_ASH_PROB_CLIMO, leído
_L = None


def lut():
    global _L
    if _L is None:
        z = np.load(LUT)
        _L = {k: z[k] for k in z.files}
    return _L


def edges():
    L = lut()
    return {"eps": L["EMISS14_TOT_BINS_OBJ"], "b": L["BETA1112_TOT_BINS_OBJ"], "bop": L["BETA1112_OPAQUE_BINS_OBJ"],
            "b85": L["BETA8511_TOT_BINS_OBJ"], "b85op": L["BETA8511_OPAQUE_BINS_OBJ"], "b73": L["BETA7311_TOT_BINS_OBJ"],
            "btd": L["BTD1112_BINS_OBJ"], "sd": L["BT14_SDEV_BINS_OBJ"], "area": L["AREA_BINS_OBJ"]}


def ibin(x, e):
    """Bin por borde inferior (el último bin abierto hacia arriba, como los _BINS_FULL_OBJ); bajo el primero, bin 0."""
    return np.clip(np.searchsorted(e, np.asarray(x, float), side="right") - 1, 0, len(e) - 1)


def isd(sd, regla):
    """Bin de desviación de BT11. 'tal': bordes leídos. 'sin075': [0,75; 1,0) va al bin de 0,5 (el bin 0,75 nunca
    aparece en Mauna Loa, criterio §2)."""
    e = edges()["sd"]
    i = ibin(sd, e)
    if regla == "sin075":
        i = np.where(i == 3, 2, i)
    return i


# (tabla, variables en orden de casilla: la primera es la más rápida). Criterio §2.
TABLAS_IR = [
    ("BT14_SDEV", [("eps", "eps"), ("sd", None)]),
    ("BETASW1_TOT", [("eps", "eps"), ("b", "b")]),
    ("BETASW1_OPAQUE", [("eps", "eps"), ("bop", "bop")]),
    ("BETASW1_TOT_BETA8511_TOT", [("b", "b"), ("b85", "b85"), ("eps", "eps")]),
    ("BETASW1_OPAQUE_BETA8511_OPAQUE", [("b", "b"), ("b85op", "b85op"), ("eps", "eps")]),   # eje β = total (§2)
    ("BETASW1_TOT_BETA7311_TOT", [("b", "b"), ("b73", "b73"), ("eps", "eps")]),
]


def casillas(px, tabla, sdregla):
    """Índice de casilla por píxel para una tabla, y máscara de píxeles que entran (variables finitas)."""
    E = edges()
    vs = dict(TABLAS_IR)[tabla]
    p = np.zeros(len(px["eps"]), int)
    ok = np.ones(len(p), bool)
    mul = 1
    for var, ek in vs:
        x = px[var]
        ok &= np.isfinite(x)
        i = isd(x, sdregla) if var == "sd" else ibin(x, E[ek])
        p += i * mul
        mul *= len(E["sd" if var == "sd" else ek])
    return p, ok


def termino(px, area, modo="IR", sdregla="tal", desempate="menor", b73="finito", detalle=False):
    """log10 de T_ceniza y T_nube de un objeto. px: dict de arreglos 1D (eps, b, bop, b85, b85op, b73, sd);
    area: km² por píxel. b73: 'finito' o 'eps01' (además εtot >= 0,1)."""
    L = lut()
    E = edges()
    lt = {"ASH": 0.0, "CLD": 0.0}
    filas = []
    ie = ibin(px["eps"], E["eps"])
    for tabla, _ in TABLAS_IR:
        p, ok = casillas(px, tabla, sdregla)
        ok &= np.isfinite(px["eps"])
        if tabla == "BETASW1_TOT_BETA7311_TOT" and b73 == "eps01":
            ok &= px["eps"] >= 0.1
        if not ok.any():
            continue
        cs, inv = np.unique(p[ok], return_inverse=True)
        ar = np.bincount(inv, weights=area[ok])
        eb = np.zeros(len(cs), int)
        np.maximum.at(eb, inv, ie[ok])                 # todos los píxeles de una casilla comparten iε
        orden = np.lexsort((cs if desempate == "menor" else -cs, -ar))[:10]
        for k, j in enumerate(orden):
            if eb[j] == 0:                             # εtot < 0,03: factor 1 (SECO 2 §4.2.2)
                continue
            ia = ibin(ar[j], E["area"])
            f = {c: float(L[f"EMISS14_{tabla}_PDF_{modo}_{c}_OBJ"][ia, cs[j], k]) for c in ("ASH", "CLD")}
            for c in f:
                lt[c] += np.log10(f[c])
            if detalle:
                filas.append(dict(tabla=tabla, rango=k, casilla=int(cs[j]), area=float(ar[j]),
                                  l10_razon=np.log10(f["ASH"] / f["CLD"])))
    return (lt["ASH"], lt["CLD"], filas) if detalle else (lt["ASH"], lt["CLD"])


def prob(la, lc, prior=PRIOR):
    """Posterior desde log10 de los términos (estable para términos de 1e-50)."""
    lo = np.log10(prior / (1 - prior)) + la - lc
    return 1.0 / (1.0 + 10.0 ** (-np.clip(lo, -300, 300)))
