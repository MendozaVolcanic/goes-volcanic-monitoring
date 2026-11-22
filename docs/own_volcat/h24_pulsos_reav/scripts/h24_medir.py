r"""H24: implementa criterio_2026-11-22.md (commit f2094f7) sin cambios.

Pregunta: en las ventanas de los 14 episodios REAV (H10), la BTD contra la linea base del propio pixel (D2 de H23)
baja en el sector a favor del viento mas que en el viento cruzado, y mas que en dias sin pulso documentado?

Por que asi: el fondo de la cumbre tiene un corrimiento que dura horas y es coherente en 15 a 20 km (H22, H23).
Comparar el sector de la pluma contra el viento cruzado EN EL MISMO CUADRO cancela la parte comun; el resto lo mide
el nulo de dias sin pulso, y el poder se mide pintando una capa conocida en esos mismos dias y horas.

Insumos (solo lectura): cubos de H23 (D:\goes_notas\s17\h23) y del hueco 24-31-10 (D:\goes_notas\s18\h24).
Salidas: resultados\h24_episodios.csv, h24_resumen.json, h24_resumen.txt. Uso: python -I h24_medir.py [pruebas]
"""
import csv
import glob
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
H23 = r"D:\goes_notas\s17\h23"
H24 = r"D:\goes_notas\s18\h24"
LATLON = r"D:\goes_notas\local_f3a7d295\cache_rescatada\reproducir_volcat\latlon.npz"
DEM = r"D:\goes_cache\etapa3_chillan\dem_ventana.npz"
NY, NX = 83, 94
T0 = datetime(2026, 9, 21)
NDIAS = 62                                   # 21-09 al 21-11
LAT, LON = (np.load(LATLON)[k].ravel() for k in ("lat", "lon"))
ZDEM = np.load(DEM)["zdem"].ravel()

# ---------- parametros del criterio ----------
VENT = (-36.8677, -71.3793)                  # centro de emision (RAV 06-11), criterio §5
SITIOS = {"chillan": (-36.86, -71.38, 3212), "antuco": (-37.41, -71.35, 2979), "longavi": (-36.19, -71.16, 3242)}
CRATER_KM = 3.2                              # tope = 3,2 km + H (como H10)
PARALAJE = 0.93                              # km de corrimiento por km de altura (H10 §4, P0)
SUBSAT = (0.0, -75.2)                        # GOES-19
R_MIN, R_MAX = 4.0, 25.0
SEMI_W, X_MIN, X_MAX = 30.0, 60.0, 120.0
PAR_K = 1.0                                  # pareo por BT11 de linea base, +-1 K
MIN_REF_PAR, MIN_W, MIN_CUADROS = 3, 10, 2
VENT_DIAS, MIN_DIAS_REF, MIN_NULO = 21, 3, 6
Z_UMBRAL, PODER_MIN, PODER_GRANDE, FA_MAX, MAD_MIN = -2.0, 0.80, 0.95, 0.10, 0.01
FRAC_DESPEJADO = 0.80
BETA = 0.70
EPS_PODER = [0.05, 0.10, 0.15, 0.30]

EPISODIOS = [  # id, inicio, fin, H (m), direccion hacia (grados), fuente
    ("E1", "2026-10-25 10:41", "2026-10-25 10:41", 1320, 135.0, "REAV"),
    ("E2", "2026-10-25 11:27", "2026-10-25 11:34", 920, 135.0, "REAV"),
    ("E3", "2026-10-25 13:15", "2026-10-25 13:15", 1540, 135.0, "REAV"),
    ("E4", "2026-10-25 14:44", "2026-10-25 16:48", 1740, 135.0, "REAV"),
    ("E5", "2026-10-25 16:23", "2026-10-25 21:16", 2300, 135.0, "REAV"),
    ("E6", "2026-10-27 09:26", "2026-10-27 09:26", 2000, 315.0, "REAV"),
    ("E7", "2026-10-27 10:26", "2026-10-27 10:26", 960, 22.5, "REAV"),
    ("E8", "2026-10-27 11:04", "2026-10-27 15:00", 1640, 0.0, "REAV"),
    ("E9", "2026-10-28 15:34", "2026-10-28 15:34", 1320, 315.0, "REAV"),
    ("E10", "2026-10-28 17:38", "2026-10-28 17:38", 2200, 315.0, "REAV"),
    ("E11", "2026-10-28 20:32", "2026-10-28 20:32", 2440, 14.8, "GFS"),
    ("E12", "2026-10-28 21:49", "2026-10-28 21:49", 2020, 21.9, "GFS"),
    ("E13", "2026-11-10 21:54", "2026-11-10 22:36", 2400, 45.5, "GFS"),
    ("E14", "2026-11-12 20:03", "2026-11-12 20:03", 400, 118.9, "GFS"),
]
ALTO_H = 1800
EXCLUIDOS = ["2026-10-25", "2026-10-27", "2026-10-28", "2026-11-10", "2026-11-12",      # REAV
             "2026-10-24", "2026-10-29", "2026-10-30", "2026-11-06", "2026-11-07", "2026-11-08",
             "2026-11-13", "2026-11-14", "2026-11-18",                                    # marcas VOLCAT (H21)
             "2026-10-22",                                                                # VCB (H23)
             "2026-11-11", "2026-11-16"]   # enmienda post hoc 1: objetos VOLCAT en frames_calor.csv (H9)
DIA_EXCL = np.zeros(NDIAS, bool)
for s in EXCLUIDOS:
    DIA_EXCL[(datetime.strptime(s, "%Y-%m-%d") - T0).days] = True


def bt_de_rad(rad, co):
    fk1, fk2, bc1, bc2 = co
    with np.errstate(invalid="ignore", divide="ignore"):
        return (fk2 / np.log(fk1 / rad + 1.0) - bc1) / bc2


def rad_de_bt(T, co):
    fk1, fk2, bc1, bc2 = co
    return fk1 / np.expm1(fk2 / (bc1 + bc2 * np.asarray(T, float)))


def hav(lat, lon, la0, lo0):
    p1, p2 = np.radians(la0), np.radians(lat)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon - lo0) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def rumbo(la0, lo0, la1, lo1):
    """Azimut inicial (grados desde el N) de (la0, lo0) a (la1, lo1)."""
    p0, p1, dl = np.radians(la0), np.radians(la1), np.radians(lo1 - lo0)
    y = np.sin(dl) * np.cos(p1)
    x = np.cos(p0) * np.sin(p1) - np.sin(p0) * np.cos(p1) * np.cos(dl)
    return np.degrees(np.arctan2(y, x)) % 360


def plano(la0, lo0):
    """x, y (km) de cada pixel en el plano tangente local de (la0, lo0)."""
    return (LON - lo0) * np.cos(np.radians(la0)) * 111.32, (LAT - la0) * 110.57


def angdif(a, b):
    return np.abs((a - b + 180.0) % 360.0 - 180.0)


# ---------- datos ----------
def cargar():
    """Radiancias (dia, slot, pixel) de 21-09 a 21-11 juntando los cubos de H23 y del hueco, mas ACM y GFS."""
    partes = [(os.path.join(H23, "cubo_oct.npz"), os.path.join(H23, "acm_oct.npz")),
              (os.path.join(H24, "cubo_oct.npz"), os.path.join(H24, "acm_oct.npz")),
              (os.path.join(H23, "cubo_nov.npz"), os.path.join(H23, "acm_nov.npz"))]
    r14 = np.full((NDIAS * 144, NY * NX), np.nan, "float32")
    r15 = r14.copy()
    acm = np.full((NDIAS * 144, NY * NX), 255, "uint8")
    cos = []
    for fc, fa in partes:
        z = np.load(fc)
        t0 = datetime.strptime(str(z["t0"]), "%Y-%m-%d")
        i0 = (t0 - T0).days * 144
        n = z["rad14"].shape[0]
        r14[i0:i0 + n] = z["rad14"].reshape(n, -1)
        r15[i0:i0 + n] = z["rad15"].reshape(n, -1)
        if not os.path.exists(fa):        # hueco 24-31-10: se arma desde los npz por cuadro (como H23 cargar_acm)
            a = np.full((n, NY * NX), 255, "uint8")
            for i in range(n):
                g = os.path.join(os.path.dirname(fa), "acm", f"{t0 + timedelta(minutes=10 * i):%Y%m%d_%H%M}.npz")
                if os.path.exists(g):
                    with np.load(g) as q:
                        a[i] = q["acm"].ravel()
            np.savez_compressed(fa, acm=a)
        a = np.load(fa)["acm"]
        assert a.shape[0] == n, (fa, a.shape, n)
        acm[i0:i0 + n] = a
        cos.append((z["co14"], z["co15"]))
    co14, co15 = cos[-1]
    for c14, c15 in cos:   # los coeficientes de Planck tienen que ser los mismos en los tres cubos
        assert np.max(np.abs(c14 / co14 - 1)) < 1e-5 and np.max(np.abs(c15 / co15 - 1)) < 1e-5
    return r14.reshape(NDIAS, 144, -1), r15.reshape(NDIAS, 144, -1), acm.reshape(NDIAS, 144, -1), co14, co15


def gfs_t(zs):
    """T del aire en Chillan (K) a las alturas zs (m) para cada (dia, slot); interpolacion lineal sin saltar > 6 h."""
    la, lo, _ = SITIOS["chillan"]
    fs = sorted(set(glob.glob(os.path.join(H23, "gfs", "gfs_*.npz")) + glob.glob(os.path.join(H24, "gfs", "gfs_*.npz"))),
                key=os.path.basename)
    vistos, hs, Tz = set(), [], []
    for f in fs:
        b = os.path.basename(f)
        if b in vistos:
            continue
        vistos.add(b)
        z = np.load(f)
        fi, fj = (z["lat"][0] - la) / 0.25, (lo - z["lon"][0]) / 0.25
        i0, j0 = int(np.floor(fi)), int(np.floor(fj))
        wi, wj = fi - i0, fj - j0

        def bil(a):
            return ((1 - wi) * (1 - wj) * a[..., i0, j0] + (1 - wi) * wj * a[..., i0, j0 + 1]
                    + wi * (1 - wj) * a[..., i0 + 1, j0] + wi * wj * a[..., i0 + 1, j0 + 1])
        T, Z = bil(z["T"]), bil(z["Z"])
        Tz.append(np.interp(zs, Z, T))
        hs.append((datetime.strptime(b[4:14], "%Y%m%d%H") - T0).total_seconds() / 3600)
    hs, Tz = np.array(hs), np.array(Tz)
    th = np.arange(NDIAS * 144) / 6.0
    k = np.searchsorted(hs, th, "right") - 1
    ok = (k >= 0) & (k < len(hs) - 1)
    ok[ok] &= (hs[k[ok] + 1] - hs[k[ok]]) <= 6.0
    out = np.stack([np.where(ok, np.interp(th, hs, Tz[:, i]), np.nan) for i in range(len(zs))], 1)
    return out.reshape(NDIAS, 144, len(zs))


# ---------- geometria ----------
def despejada(sitio, acm):
    """H23 E1: >= 80 % del terreno bajo del sitio (10 a 30 km, cota < 1.300 m) despejado (ACM 0 o 1)."""
    la, lo, h = SITIOS[sitio]
    d = hav(LAT, LON, la - 0.93 * h / 1000.0 / 111.2, lo)
    bajo = np.where((d >= 10.0) & (d <= 30.0) & (ZDEM < 1300.0))[0]
    return (acm[:, :, bajo] <= 1).mean(2) >= FRAC_DESPEJADO


def sectores(sitio, direc, H):
    """Pixeles W (pluma), Wc (placebo contra el viento) y R (viento cruzado) para un sitio, direccion y altura."""
    la, lo = VENT if sitio == "chillan" else SITIOS[sitio][:2]
    h = CRATER_KM + H / 1000.0
    lejos = (rumbo(la, lo, *SUBSAT) + 180.0) % 360.0
    x, y = plano(la, lo)
    x = x - PARALAJE * h * np.sin(np.radians(lejos))
    y = y - PARALAJE * h * np.cos(np.radians(lejos))
    r = np.hypot(x, y)
    az = np.degrees(np.arctan2(x, y)) % 360
    anillo = (r >= R_MIN) & (r <= R_MAX)
    a = angdif(az, direc)
    return {"W": np.where(anillo & (a <= SEMI_W))[0], "Wc": np.where(anillo & (a >= 180 - SEMI_W))[0],
            "R": np.where(anillo & (a >= X_MIN) & (a <= X_MAX))[0]}


# ---------- motor ----------
class Motor:
    def __init__(self, r14, r15, acm, co14, co15):
        self.co14, self.co15 = co14, co15
        self.r14, self.r15 = r14, r15
        self.bt11 = bt_de_rad(r14.astype("float64"), co14).astype("float32")
        self.btd = (self.bt11 - bt_de_rad(r15.astype("float64"), co15)).astype("float32")
        self.F = {s: despejada(s, acm) for s in SITIOS}
        self._base = {}

    def base(self, sitio, d, s, px):
        """Linea base de (dia d, slot s) en los pixeles px: mediana de BT11 y BTD a la misma hora (s-1, s, s+1) en
        los otros dias despejados de +-21 dias, sin dias excluidos; pide >= 3 dias con dato en el pixel."""
        k = (sitio, d, s, px.tobytes())
        if k in self._base:
            return self._base[k]
        F = self.F[sitio]
        bt, bd, dia = [], [], []
        for dd in range(max(0, d - VENT_DIAS), min(NDIAS, d + VENT_DIAS + 1)):
            if dd == d or DIA_EXCL[dd]:
                continue
            for ss in (s - 1, s, s + 1):
                if 0 <= ss < 144 and F[dd, ss]:
                    bt.append(self.bt11[dd, ss, px]); bd.append(self.btd[dd, ss, px]); dia.append(dd)
        if not bt:
            out = (np.full(len(px), np.nan), np.full(len(px), np.nan))
        else:
            bt, bd, dia = np.array(bt), np.array(bd), np.array(dia)
            ndias = np.zeros(len(px), int)
            for dd in np.unique(dia):
                ndias += np.isfinite(bt[dia == dd]).any(0)
            with np.errstate(invalid="ignore"), __import__("warnings").catch_warnings():
                __import__("warnings").simplefilter("ignore", RuntimeWarning)
                r11, rd = np.nanmedian(bt, 0), np.nanmedian(bd, 0)
            r11[ndias < MIN_DIAS_REF] = np.nan
            rd[ndias < MIN_DIAS_REF] = np.nan
            out = (r11, rd)
        self._base[k] = out
        return out

    def S_cuadro(self, sitio, d, s, W, R, det="D2", par="esperada", iny=None):
        """Estadistico de un cuadro. iny = (eps, T_tope) pinta la capa sobre W. Devuelve NaN si no es valido."""
        if not self.F[sitio][d, s]:
            return np.nan
        px = np.concatenate([W, R])
        r11, rd = self.base(sitio, d, s, px)
        if iny is None:
            bt11, btd = self.bt11[d, s, px].astype(float), self.btd[d, s, px].astype(float)
        else:
            eps, Tt = iny
            I14 = self.r14[d, s, px].astype(float)
            I15 = self.r15[d, s, px].astype(float)
            e12 = 1 - (1 - eps) ** BETA
            m = np.arange(len(px)) < len(W)
            I14[m] = (1 - eps) * I14[m] + eps * rad_de_bt(Tt, self.co14)
            I15[m] = (1 - e12) * I15[m] + e12 * rad_de_bt(Tt, self.co15)
            bt11 = bt_de_rad(I14, self.co14)
            btd = bt11 - bt_de_rad(I15, self.co15)
        x = (btd - rd) if det == "D2" else (bt11 - r11)
        clave = r11 if par == "esperada" else bt11
        nW = len(W)
        xw, kw = x[:nW], clave[:nW]
        xr, kr = x[nW:], clave[nW:]
        okr = np.isfinite(xr) & np.isfinite(kr)
        xr, kr = xr[okr], kr[okr]
        dif = []
        for xi, ki in zip(xw, kw):
            if not (np.isfinite(xi) and np.isfinite(ki)):
                continue
            sel = np.abs(kr - ki) <= PAR_K
            if sel.sum() >= MIN_REF_PAR:
                dif.append(xi - np.median(xr[sel]))
        return float(np.median(dif)) if len(dif) >= MIN_W else np.nan

    def E(self, sitio, d, slots, W, R, det="D2", par="esperada", iny_por_slot=None):
        """Estadistico de un episodio o de un dia: mediana de S en los cuadros validos; NaN si hay menos de 2."""
        Ss = []
        for s in slots:
            iny = None if iny_por_slot is None else iny_por_slot[s]
            v = self.S_cuadro(sitio, d, s, W, R, det=det, par=par, iny=iny)
            if np.isfinite(v):
                Ss.append(v)
        return (float(np.median(Ss)) if len(Ss) >= MIN_CUADROS else np.nan), len(Ss)


def zrob(x, nulo):
    nulo = np.asarray([v for v in nulo if np.isfinite(v)])
    if len(nulo) < MIN_NULO or not np.isfinite(x):
        return np.nan, len(nulo), np.nan
    med = np.median(nulo)
    mad = 1.4826 * np.median(np.abs(nulo - med))
    if mad <= MAD_MIN:
        return np.nan, len(nulo), mad
    return (x - med) / mad, len(nulo), mad


def ventanas():
    """Slots (dia, lista de slots) de cada episodio con la regla de asignacion del criterio §4."""
    ini = {e[0]: datetime.strptime(e[1], "%Y-%m-%d %H:%M") for e in EPISODIOS}
    fin = {e[0]: datetime.strptime(e[2], "%Y-%m-%d %H:%M") for e in EPISODIOS}
    slot0 = {k: v.replace(minute=v.minute // 10 * 10) for k, v in ini.items()}
    asign = {}
    for k in ini:
        t = slot0[k]
        while t <= fin[k] + timedelta(minutes=60):
            cand = [j for j in ini if slot0[j] <= t <= fin[j] + timedelta(minutes=60)]
            dueno = max(cand, key=lambda j: slot0[j])
            asign.setdefault(dueno, set()).add(t)
            t += timedelta(minutes=10)
    out = {}
    for k, ts in asign.items():
        ts = sorted(ts)
        d = (ts[0].date() - T0.date()).days
        assert all((t.date() - T0.date()).days == d for t in ts)
        out[k] = (d, [t.hour * 6 + t.minute // 10 for t in ts])
    return out


def episodio(M, Tz, e, ven, zs_idx):
    eid, _, _, H, direc, fuente = e
    d0, slots = ven[eid]
    nulos = [d for d in range(max(0, d0 - VENT_DIAS), min(NDIAS, d0 + VENT_DIAS + 1)) if d != d0 and not DIA_EXCL[d]]
    fila = {"ep": eid, "H": H, "grupo": "alto" if H >= ALTO_H else ("bajo" if H < 800 else "medio"),
            "direccion": direc, "fuente_dir": fuente, "dia": f"{T0 + timedelta(days=d0):%Y-%m-%d}",
            "slots": len(slots), "dias_nulos_candidatos": len(nulos)}
    res = {}
    for sitio in SITIOS:
        g = sectores(sitio, direc, H)
        fila[f"{sitio}_nW"], fila[f"{sitio}_nR"] = len(g["W"]), len(g["R"])
        for det, par in (("D2", "esperada"), ("D1", "esperada"), ("D2", "observada")):
            if sitio != "chillan" and (det, par) != ("D2", "esperada"):
                continue
            tag = f"{sitio}_{det}_{par}"
            Ee, nc = M.E(sitio, d0, slots, g["W"], g["R"], det=det, par=par)
            En = {d: M.E(sitio, d, slots, g["W"], g["R"], det=det, par=par)[0] for d in nulos}
            z, nn, mad = zrob(Ee, list(En.values()))
            fila[f"{tag}_E"], fila[f"{tag}_cuadros"], fila[f"{tag}_z"], fila[f"{tag}_nnulo"] = Ee, nc, z, nn
            fila[f"{tag}_mad"] = mad
            res[tag] = En
            if (sitio, det, par) == ("chillan", "D2", "esperada"):
                # placebo contra el viento (mismo R)
                Ep, _ = M.E(sitio, d0, slots, g["Wc"], g["R"])
                Enp = [M.E(sitio, d, slots, g["Wc"], g["R"])[0] for d in nulos]
                fila["placebo_E"], fila["placebo_z"] = Ep, zrob(Ep, Enp)[0]
                # falsas alarmas: cada dia nulo contra los otros
                fa = []
                for d in En:
                    if np.isfinite(En[d]):
                        zi = zrob(En[d], [v for dd, v in En.items() if dd != d])[0]
                        if np.isfinite(zi):
                            fa.append(zi <= Z_UMBRAL)
                fila["fa_n"], fila["fa_det"] = len(fa), int(np.sum(fa))
                # poder: capa inyectada en W en cada dia nulo, contra el nulo sin inyectar de los otros dias
                for eps, iz, nombre in [(x, zs_idx["tope"], f"poder_{x:.2f}") for x in EPS_PODER] + \
                                       [(0.9, zs_idx["10km"], "poder_grande")]:
                    det_ok = []
                    for d in En:
                        if not np.isfinite(En[d]):
                            continue
                        Tt = {s: Tz[d, s, iz] for s in slots}
                        if not all(np.isfinite(v) for v in Tt.values()):
                            continue
                        Ei = M.E(sitio, d, slots, g["W"], g["R"], iny_por_slot={s: (eps, Tt[s]) for s in slots})[0]
                        zi = zrob(Ei, [v for dd, v in En.items() if dd != d])[0]
                        if np.isfinite(zi):
                            det_ok.append(zi <= Z_UMBRAL)
                    fila[f"{nombre}_n"] = len(det_ok)
                    fila[nombre] = float(np.mean(det_ok)) if det_ok else np.nan
    return fila, res


def clase(f):
    if not (f["chillan_D2_esperada_cuadros"] >= MIN_CUADROS):
        return "SIN DATO (cielo)"
    if f["chillan_D2_esperada_nnulo"] < MIN_NULO or not np.isfinite(f.get("poder_0.15", np.nan)) \
            or f["poder_0.15"] < PODER_MIN or not np.isfinite(f["chillan_D2_esperada_z"]):
        return "SIN PODER"
    z = f["chillan_D2_esperada_z"]
    if z > Z_UMBRAL:
        return "SIN SEÑAL"
    plac = np.isfinite(f["placebo_z"]) and f["placebo_z"] <= Z_UMBRAL
    cumbre = any(np.isfinite(f[f"{s}_D2_esperada_z"]) and f[f"{s}_D2_esperada_z"] <= Z_UMBRAL for s in ("antuco", "longavi"))
    return "DUDOSO" if (plac or cumbre) else "SEÑAL"


def pruebas():
    """Pruebas numericas con datos sinteticos: Planck ida y vuelta, inyeccion e=0 identidad, e=1 da T_tope,
    geometria (W, Wc, R disjuntos), ventanas (asignacion), z robusto."""
    co = np.array([8.5e3, 1.2858e3, 0.2105, 0.99925])
    T = np.array([250.0, 270.0, 290.0])
    assert np.allclose(bt_de_rad(rad_de_bt(T, co), co), T, atol=1e-6)
    I = rad_de_bt(np.array([270.0]), co)
    for eps, esp in ((0.0, 270.0), (1.0, 250.0)):
        I2 = (1 - eps) * I + eps * rad_de_bt(250.0, co)
        assert abs(bt_de_rad(I2, co)[0] - esp) < 1e-6
    g = sectores("chillan", 135.0, 2000)
    assert len(set(g["W"]) & set(g["R"])) == 0 and len(set(g["Wc"]) & set(g["R"])) == 0 and len(set(g["W"]) & set(g["Wc"])) == 0
    assert len(g["W"]) > 30 and len(g["R"]) > 60, (len(g["W"]), len(g["R"]))
    ven = ventanas()
    assert ven["E5"][1][0] == 16 * 6 + 2 and ven["E4"][1][-1] == 16 * 6 + 1, (ven["E5"][1][:2], ven["E4"][1][-2:])
    assert ven["E7"][1][-1] == 10 * 6 + 5 and ven["E8"][1][0] == 11 * 6
    assert ven["E6"][1] == [9 * 6 + 2, 9 * 6 + 3, 9 * 6 + 4, 9 * 6 + 5, 10 * 6 + 0, 10 * 6 + 1]
    z, n, _ = zrob(-3.0, [0, 1, -1, 0.5, -0.5, 0.2, -0.2])
    assert n == 7 and z < -2
    assert np.isnan(zrob(-3.0, [0, 1, -1])[0])
    lejos = (rumbo(*VENT, *SUBSAT) + 180) % 360
    assert 170 < lejos < 185, lejos
    print("pruebas OK (8 de 8); paralaje hacia", round(lejos, 1), "grados; W, Wc, R de E6-like:", len(g["W"]), len(g["Wc"]), len(g["R"]))


def main():
    pruebas()
    r14, r15, acm, co14, co15 = cargar()
    hay = np.isfinite(r14).any(2)
    print("cuadros presentes por bloque:", int(hay[:33].sum()), int(hay[33:41].sum()), int(hay[41:].sum()), flush=True)
    M = Motor(r14, r15, acm, co14, co15)
    alturas = sorted({CRATER_KM * 1000 + e[3] for e in EPISODIOS})
    zs = alturas + [10000.0]
    Tz_all = gfs_t(zs)
    ven = ventanas()
    filas = []
    for e in EPISODIOS:
        zs_idx = {"tope": alturas.index(CRATER_KM * 1000 + e[3]), "10km": len(alturas)}
        f, _ = episodio(M, Tz_all, e, ven, zs_idx)
        f["clase"] = clase(f)
        filas.append(f)
        print(e[0], f["clase"], "z", round(f["chillan_D2_esperada_z"], 2) if np.isfinite(f["chillan_D2_esperada_z"]) else "nan",
              "cuadros", f["chillan_D2_esperada_cuadros"], "nulo", f["chillan_D2_esperada_nnulo"],
              "poder015", f.get("poder_0.15"), "grande", f.get("poder_grande"), flush=True)
    os.makedirs(RES, exist_ok=True)
    claves = sorted({k for f in filas for k in f}, key=lambda k: (k != "ep", k))
    with open(os.path.join(RES, "h24_episodios.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, claves)
        w.writeheader()
        for f in filas:
            w.writerow(f)
    # veredicto global
    fa_n = sum(f["fa_n"] for f in filas)
    fa_det = sum(f["fa_det"] for f in filas)
    tasa_fa = fa_det / fa_n if fa_n else np.nan
    altos = [f for f in filas if f["grupo"] == "alto"]
    senal = sum(f["clase"] == "SEÑAL" for f in altos)
    decid = sum(f["clase"] in ("SEÑAL", "SIN SEÑAL") for f in altos)
    grande_ok = all((not np.isfinite(f.get("poder_grande", np.nan))) or f["poder_grande"] >= PODER_GRANDE for f in filas)
    if not (tasa_fa <= FA_MAX) or not grande_ok:
        ver = "INVÁLIDO"
    elif senal >= 2 and senal >= 0.5 * decid:
        ver = "LOS PULSOS ALTOS SE VEN"
    elif decid >= 3 and senal == 0:
        ver = "NI LOS PULSOS ALTOS SE VEN"
    else:
        ver = "NO CONCLUYENTE"
    resumen = {"criterio_commit": "f2094f7", "veredicto": ver, "falsas_alarmas": {"n": fa_n, "detecta": fa_det, "tasa": tasa_fa},
               "control_grande_ok": grande_ok, "altos": {"n": len(altos), "decidibles": decid, "senal": senal},
               "clases": {f["ep"]: f["clase"] for f in filas}}
    json.dump(resumen, open(os.path.join(RES, "h24_resumen.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(resumen, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pruebas":
        pruebas()
    else:
        main()
