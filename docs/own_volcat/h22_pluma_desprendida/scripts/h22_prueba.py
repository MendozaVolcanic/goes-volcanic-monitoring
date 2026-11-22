r"""H22: la prueba, en funciones que usan igual la medicion de ruido (dias sin evento), la pluma, los placebos y el
control positivo. Una sola implementacion para que el placebo mida exactamente lo que mide la prueba.

Controles pareados: ver medir(). Todos son pixeles del MISMO cuadro, de la misma banda de cota (+- 300 m) y a 4 px o
mas de toda huella de +- 20 min.
"""
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h22_comun as C  # noqa: E402

DZ_M = 300.0
DB11_K = 1.0
DOBS_K = 0.5
EXCL_PX = 4
MIN_CTRL = 10
CLARO_K = -3.0             # un pixel cuenta como despejado si dBT11 >= -3 K
ENTORNO_MIN = 0.5         # un cuadro entra a la poblacion que decide si su entorno lejano esta >= 50 % despejado
EVENTO = "20261114_1630"          # primera deteccion del evento largo
FRAMES_H9 = os.path.join(os.path.dirname(os.path.dirname(C.AQUI)), "calor_rayos", "resultados", "frames_calor.csv")
MEDIDAS = ("d11", "dbtd", "beta", "dbtd8")


def huellas_evento():
    """{clave: dict(wy, wx, + campos SSEC por pixel)} de los 41 cuadros del evento del 14-11 16:30 UTC."""
    out = {}
    for c, f in C.eventos("*_s20261114*.nc"):
        if c < EVENTO:
            continue
        e = C.leer_evento(f)
        m = e["ei"] >= 0
        out[c] = dict(wy=e["wy"][m], wx=e["wx"][m], S=e["S"][m], SL=e["SL"][m], masa=e["masa"][m], alt=e["alt"][m],
                      sza_volcat=e["sza"], ttrop=e["ttrop"], bt11_ev=e["bt11"][m], unidades=(e["masa_unidad"], e["alt_unidad"]))
    return out


def exclusion(HU, c, forma, minutos=20):
    """Mascara de pixeles a menos de EXCL_PX de cualquier huella del evento entre c - minutos y c + minutos."""
    t = datetime.strptime(c, "%Y%m%d_%H%M")
    u = np.zeros(forma, bool)
    for c2, h in HU.items():
        if abs((datetime.strptime(c2, "%Y%m%d_%H%M") - t).total_seconds()) <= minutos * 60:
            u[h["wy"], h["wx"]] = True
    if not u.any():
        return u
    return ndimage.distance_transform_edt(~u) < EXCL_PX


def anillo(HU, c, forma, r0=EXCL_PX, r1=12, minutos=20, solo_lejos=False):
    """Entorno de la huella del cuadro c: pixeles a r0..r1 px de la huella (de sus pixeles a > 30 km si solo_lejos) y
    fuera de la zona de exclusion de +- minutos. No contiene ningun pixel publicado."""
    h = HU[c]
    u = np.zeros(forma, bool)
    m = C.DIST[h["wy"], h["wx"]] > 30 if solo_lejos else np.ones(len(h["wy"]), bool)
    if not m.any():
        return u
    u[h["wy"][m], h["wx"][m]] = True
    d = ndimage.distance_transform_edt(~u)
    return (d >= r0) & (d <= r1) & ~exclusion(HU, c, forma, minutos)


def cielo_entorno(P, i, an, claro_k=CLARO_K):
    """Fraccion del entorno `an` que esta despejada en el cuadro i (dBT11 >= claro_k contra su linea base)."""
    b = P.base(i)
    if b is None or not an.any():
        return np.nan
    return float(((P.b14[i] - b[0])[an] >= claro_k).mean())


def dias_placebo(P, desde="20261026"):
    """Dias sin objeto VOLCAT: todos los cuadros de 16:30 a 23:40 UTC con clase N de H9 (sin ceniza VOLCAT a <= 50 km
    ni en +- 60 min), sin archivo de evento, y con linea base completa (desde el 26-10)."""
    h9 = pd.read_csv(FRAMES_H9, parse_dates=["dt"])
    h9 = h9[(h9.dt.dt.hour * 60 + h9.dt.dt.minute >= 16 * 60 + 30) & (h9.dt.dt.hour * 60 + h9.dt.dt.minute <= 23 * 60 + 40)]
    g = h9.groupby(h9.dt.dt.strftime("%Y%m%d")).clase.agg(lambda s: (s == "N").all() and len(s) >= 30)
    ev = {c[:8] for c, _ in C.eventos()}
    return sorted(d for d, ok in g.items() if ok and d >= desde and d not in ev)


def medir(P, i, wy, wx, excl, iny=None, extra=None):
    """Tabla por pixel de huella del cuadro i, con tres controles pareados del mismo cuadro:
      (sin prefijo) control D, el que decide: cota +- 300 m, linea base de BT11 +- 1 K, y control DESPEJADO
                    (dBT11 >= CLARO_K). Responde: el pixel publicado, contra lo que se espera con cielo despejado.
      A_            igual pero con todo el cielo (despejado o nublado). Sensibilidad.
      B_            cota +- 300 m y BT11 OBSERVADA +- 0,5 K (convencion anterior del proyecto). Sensibilidad; es el
                    unico que compara la BTD contra nube meteorologica de igual temperatura.
    iny = (e11, tnube, beta): mezcla una capa semitransparente en los pixeles de la huella antes de medir (control
    positivo). Devuelve DataFrame o None si no hay linea base."""
    base = P.base(i)
    if base is None:
        return None
    B11, Bd, Bd8, nb = base
    b14, b15 = P.b14[i].astype("float64").copy(), P.b15[i].astype("float64").copy()
    if iny is not None:
        e11, tn, be = iny
        e12 = 1.0 - (1.0 - e11) ** be
        for b, co, e in ((b14, P.co14, e11), (b15, P.co15, e12)):
            r = (1 - e) * C.rad_de_bt(b[wy, wx], co) + e * C.rad_de_bt(tn, co)
            b[wy, wx] = C.bt(r, co)
    d11 = b14 - B11
    btd = b14 - b15
    dbtd = btd - Bd
    dbtd8 = (P.b11[i] - b14) - Bd8
    beta, e11m = C.beta_base(b14, b15, B11, B11 - Bd, P.co14, P.co15)
    campos = dict(d11=d11, dbtd=dbtd, beta=beta, dbtd8=dbtd8, btd=btd)
    valido = np.isfinite(d11) & np.isfinite(dbtd) & ~excl
    claro = d11 >= CLARO_K
    filas = []
    for k, (y, x) in enumerate(zip(wy, wx)):
        f = dict(wy=int(y), wx=int(x), dist=float(C.DIST[y, x]), z=float(C.ZDEM[y, x]), B11=float(B11[y, x]),
                 bt11=float(b14[y, x]), e11=float(e11m[y, x]))
        for m in campos:
            f[m] = float(campos[m][y, x])
        cota = valido & (np.abs(C.ZDEM - C.ZDEM[y, x]) <= DZ_M)
        pa = cota & (np.abs(B11 - B11[y, x]) <= DB11_K)
        for pre, pool in (("", pa & claro), ("A_", pa), ("B_", cota & (np.abs(b14 - b14[y, x]) <= DOBS_K))):
            n = int(pool.sum())
            f[f"{pre}n_ctrl"] = n
            if n < MIN_CTRL:
                continue
            for m in campos:
                v = campos[m][pool]
                v = v[np.isfinite(v)]
                if len(v) >= MIN_CTRL and np.isfinite(f[m]):
                    f[f"{pre}c_{m}"] = float(np.median(v))
                    # rango: probabilidad de que un control sea MAYOR que el pixel de pluma (pluma mas baja -> 1)
                    f[f"{pre}r_{m}"] = float((v > f[m]).mean() + 0.5 * (v == f[m]).mean())
        if extra is not None:
            for kk, vv in extra.items():
                f[kk] = float(vv[k])
        filas.append(f)
    df = pd.DataFrame(filas)
    for pre in ("", "A_", "B_"):
        for m in campos:
            for q in ("c", "r"):
                if f"{pre}{q}_{m}" not in df:
                    df[f"{pre}{q}_{m}"] = np.nan
    df["cuadro"] = P.cs[i]
    df["sza"] = C.sza(P.T[i])
    df["n_base"] = nb
    return df


def resumen(df, medidas=MEDIDAS, pre=""):
    """Estadistico agrupado de un conjunto de pixeles-cuadro: D = mediana(pixel - mediana de sus controles),
    AUC = media del rango pareado (0,5 = no separa; > 0,5 = la pluma queda mas BAJA que sus controles).
    frio = fraccion de pixeles mas de 3 K bajo la mediana de sus controles."""
    out = dict(n=int(len(df)))
    for m in medidas:
        s = df[df[f"{pre}c_{m}"].notna()] if len(df) else df
        if len(s) == 0:
            out.update({f"n_{m}": 0, f"D_{m}": np.nan, f"auc_{m}": np.nan, f"med_{m}": np.nan})
            continue
        out[f"n_{m}"] = int(len(s))
        out[f"med_{m}"] = float(s[m].median())
        out[f"D_{m}"] = float((s[m] - s[f"{pre}c_{m}"]).median())
        out[f"auc_{m}"] = float(s[f"{pre}r_{m}"].mean())
        if m == "d11":
            out["frio"] = float(((s[m] - s[f"{pre}c_{m}"]) < CLARO_K).mean())
    return out


def tramo_sza(s):
    return "<50" if s < 50 else "50-70" if s < 70 else "70-85" if s < 85 else ">=85"


def tabla_dia(P, HU, dia, iny=None, solo_lejos=False, corr=(0, 0), con_extra=False, todas=None):
    """Tabla por pixel de la huella del evento puesta en el dia `dia` (el 14-11 = la pluma; otro dia = placebo
    temporal). corr = (dy, dx) corre la huella dentro de la ventana (placebo espacial). Agrega por cuadro el estado
    del cielo del entorno: f_t (entorno de toda la huella) y f_l (entorno de los pixeles a > 30 km)."""
    forma = C.LAT.shape
    todas = todas or HU          # todas las huellas del evento: definen la exclusion y el entorno
    tablas = []
    for c, h in HU.items():
        i = P.pos.get(f"{dia}_{c[9:]}")
        if i is None or P.base(i) is None:
            continue
        wy, wx = h["wy"], h["wx"]
        m = np.ones(len(wy), bool)
        if solo_lejos:
            m = C.DIST[wy, wx] > 30
            if not m.any():
                continue
        ex = exclusion(todas, c, forma)
        extra = {k: h[k][m] for k in ("S", "SL", "masa", "alt")} if con_extra else None
        df = medir(P, i, wy[m] + corr[0], wx[m] + corr[1], ex, iny=iny, extra=extra)
        df["dist"] = C.DIST[wy[m], wx[m]]      # el grupo lo define la huella real, tambien en el placebo espacial
        df["f_t"] = cielo_entorno(P, i, anillo(todas, c, forma))
        df["f_l"] = cielo_entorno(P, i, anillo(todas, c, forma, solo_lejos=True))
        tablas.append(df)
    if not tablas:
        return None
    T = pd.concat(tablas, ignore_index=True)
    T["dia"] = dia
    T["hora"] = T.cuadro.str[9:]
    T["lejos"] = T.dist > 30
    T["tramo"] = T.sza.map(tramo_sza)
    T["elegible"] = np.where(T.lejos, T.f_l, T.f_t) >= ENTORNO_MIN
    return T


def grupos(T):
    """Poblaciones. La que decide es la primera."""
    return {"lejos, entorno despejado": T.lejos & T.elegible,
            "lejos, entorno nublado": T.lejos & ~T.elegible,
            "lejos, todo": T.lejos,
            "cerca, entorno despejado": ~T.lejos & T.elegible,
            "cerca, entorno despejado, cenit <50": ~T.lejos & T.elegible & (T.tramo == "<50"),
            "cerca, entorno despejado, cenit 50-70": ~T.lejos & T.elegible & (T.tramo == "50-70"),
            "cerca, entorno despejado, cenit 70-85": ~T.lejos & T.elegible & (T.tramo == "70-85"),
            "cerca, entorno despejado, 22:20-22:50": ~T.lejos & T.elegible & T.hora.between("2220", "2250"),
            "lejos, entorno despejado, 22:20-22:50": T.lejos & T.elegible & T.hora.between("2220", "2250"),
            "cerca, entorno nublado": ~T.lejos & ~T.elegible,
            "cerca, todo": ~T.lejos}
