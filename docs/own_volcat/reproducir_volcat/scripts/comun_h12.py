"""H12: piezas comunes. Test 3 original de Francis et al. 2012 (ec. 3, p. 3) y su filtro beta (ec. 5).

Criterio: docs/own_volcat/reproducir_volcat/criterio_H12_2026-11-20.md (commit ae954b0, antes de medir).
Reutiliza sin editarlos comun_h11 (pares de H11, huellas, escenas, GFS), rt_niveles (modelo radiativo de H3)
y rt_e2 (rejilla de E2). Solo lectura sobre los datos de H11 y E2; escribe en <TRABAJO>/h12.
"""
import os, sys, json, glob
from datetime import timedelta
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h11 as C  # noqa: E402

rt = C.rt
FEAT = os.path.join(C.TRABAJO, "feat_e2")
RTE2 = os.path.join(C.TRABAJO, "rt_e2")
# Salida fuera del repo (datos derivados). Defecto: copia durable en D: de la carpeta de notas de la sesion de
# rescate (copiada el 21-11, ver INVENTARIO_REPRODUCIBILIDAD.md); la carpeta de notas se puede borrar sin aviso.
OUT = os.environ.get("H12_OUT", r"D:\goes_notas\local_f3a7d295\h12_datos\h12")
os.makedirs(OUT, exist_ok=True)
RTSIT = os.path.join(OUT, "rt_sitios"); os.makedirs(RTSIT, exist_ok=True)
LPT = np.log(rt.PTOP)

CRATER_PX = (41, 46)
SITIOS = {"antuco": (62, 46), "longavi": (15, 57), "llano": (32, 17)}   # pixel mas cercano (criterio)


# ------------------------------------------------------------------ Test 3 y margen
def t3(btd, btd_clr):
    with np.errstate(invalid="ignore"):
        return (btd < 0.7) & (btd < btd_clr - 1.0)


def margen(btd, btd_clr):
    return np.minimum(0.7 - btd, btd_clr - 1.0 - btd)


def jornada(dt):
    return f"{dt - timedelta(hours=3):%Y-%m-%d}"


# ------------------------------------------------------------------ filtro beta (ec. 5), altura de emision BT11 - 5 K
def rcld_emision(rcld_px, tb_px, ptropo, t_obj):
    """R_cld (4 bandas) en el nivel donde T del GFS = t_obj, bajando desde la tropopausa. None si no cruza."""
    ok = np.isfinite(rcld_px[:, 0]) & np.isfinite(tb_px) & (LPT > np.log(ptropo) - 1e-9)
    idx = np.nonzero(ok)[0][::-1]           # presion creciente = bajando desde la tropopausa
    if len(idx) == 0:
        return None
    prev = None
    for i in idx:
        if tb_px[i] >= t_obj:
            if prev is None:
                return rcld_px[i].copy()
            t0, t1 = tb_px[prev], tb_px[i]
            w = 0.0 if t1 == t0 else (t_obj - t0) / (t1 - t0)
            return rcld_px[prev] * (1 - w) + rcld_px[i] * w   # lineal en T entre bordes vecinos (ln p monotono)
        prev = i
    return None


def beta_francis(robs, rclr, rcld_px, tb_px, ptropo, bt11obs):
    """(beta85, beta12) con la nube negra a BT11 - 5 K. Bandas: 0 = C10, 1 = C11, 2 = C14, 3 = C15."""
    rc = rcld_emision(rcld_px, tb_px, ptropo, bt11obs - 5.0)
    if rc is None:
        return np.nan, np.nan
    with np.errstate(all="ignore"):
        e = (robs - rclr) / (rc - rclr)
    def b(ea, e11):  # noqa: E306
        return np.log1p(-ea) / np.log1p(-e11) if (0 < ea < 1 and 0 < e11 < 1) else np.nan
    return b(e[1], e[2]), b(e[3], e[2])


def rechazo_beta(b85, b12):
    """True = la ec. 5 borra la bandera tentativa. NaN en b85 o b12 = no medible (se trata aparte)."""
    return (b85 <= 0.7) | (b85 >= 1.2) | (b12 > 4.264 - 5.823 * b85 + 2.446 * b85 ** 2)


# ------------------------------------------------------------------ conjunto B: pareo nuevo (solo BT11)
def feat(dt):
    p = os.path.join(FEAT, C.k(dt) + ".npz")
    return dict(np.load(p, allow_pickle=True)) if os.path.exists(p) else None


def escenas_e2():
    """Escenas de E2 tal como las uso E2: los negativos a menos de 60 min de un objeto VOLCAT quedan fuera
    (C._limpio, igual que e2_clasificador.cargar). Correccion posterior del 20-11: la primera version no
    aplicaba el filtro y metia 10 negativos del 13-11 (665 en vez de 655), 8 de ellos como control en B."""
    out = {}
    for f in sorted(glob.glob(os.path.join(FEAT, "*.npz"))):
        kk = os.path.basename(f)[:-4]
        z = np.load(f, allow_pickle=True)
        if str(z["tipo"]) == "neg" and not C._limpio(C.dtk(kk)):
            continue
        out[kk] = str(z["tipo"])
    return out


def pareo_e2():
    p = os.path.join(OUT, "pareo_e2.json")
    if os.path.exists(p):
        return json.load(open(p))
    E = escenas_e2(); negs = [C.dtk(k) for k, t in E.items() if t == "neg"]
    res = []
    for kk, t in sorted(E.items()):
        if t != "pos":
            continue
        dt = C.dtk(kk); z = feat(dt); h = z["ash"].astype(bool)
        if h.sum() == 0:
            res.append({"pos": kk, "ctrl": None, "estado": "sin_huella"}); continue
        mpos = float(np.nanmedian(z["bt11"][h]))
        cands = []
        for n in negs:
            if jornada(n) == jornada(dt):
                continue
            dmin = abs((n.hour * 60 + n.minute) - (dt.hour * 60 + dt.minute))
            dmin = min(dmin, 1440 - dmin)
            if dmin <= 10:
                zn = feat(n); cands.append((abs(float(np.nanmedian(zn["bt11"][h])) - mpos), dmin, C.k(n)))
        if not cands:
            res.append({"pos": kk, "ctrl": None, "estado": "sin_candidatos"}); continue
        d, dm, kc = min(cands)
        res.append({"pos": kk, "ctrl": kc if d <= 3.0 else None, "estado": "ok" if d <= 3.0 else "dif_bt11>3K",
                    "dbt11": round(d, 3), "dmin": dm, "n_cand": len(cands), "n_h": int(h.sum())})
    json.dump(res, open(p, "w"), indent=1)
    return res


def huella_b_grid(kpos):
    z = feat(C.dtk(kpos)); m = np.zeros(C.LAT.shape, bool)
    m[z["ys"][z["ash"].astype(bool)], z["xs"][z["ash"].astype(bool)]] = True
    return m


# ------------------------------------------------------------------ huella trasladada a cumbres y llano
_PNGDIRS = [os.path.join(C.B73, "png_new"), os.path.join(C.TRABAJO, "png_e2")]


def ceniza_volcat(dt):
    """Ceniza VOLCAT en toda la ventana para la escena dt: PNG decodificado; si no hay, huellas de H3/b73."""
    import huella_png as HP
    r = C._INV.get(dt)
    if r is not None:
        for d in _PNGDIRS:
            p = os.path.join(d, r["fn"])
            if os.path.exists(p):
                ash, _, ok = HP.decodifica(p)
                if ok:
                    return ash, "png"
    kk = C.k(dt)
    if "a_" + kk in C._HUB:
        return C._HUB["a_" + kk].astype(bool), "huellas_b73"
    if kk in C._HU3:
        return C._HU3[kk].astype(bool), "huellas_h3"
    return np.zeros(C.LAT.shape, bool), "sin_mascara"


def trasladar(h, sitio):
    dy = SITIOS[sitio][0] - CRATER_PX[0]; dx = SITIOS[sitio][1] - CRATER_PX[1]
    ys, xs = np.nonzero(h); ys2, xs2 = ys + dy, xs + dx
    ok = (ys2 >= 0) & (ys2 < C.LAT.shape[0]) & (xs2 >= 0) & (xs2 < C.LAT.shape[1])
    m = np.zeros(C.LAT.shape, bool); m[ys2[ok], xs2[ok]] = True
    return m, int((~ok).sum())


def dist_crater():
    import huella_png as HP
    return HP.DIST
