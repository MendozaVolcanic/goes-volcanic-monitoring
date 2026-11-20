"""H13: piezas comunes (rutas, cuadros VOLCAT anclados, ventanas de secuencia, dias candidatos a control).

Criterio: docs/own_volcat/temporal_h13/criterio_H13_2026-11-20.md. Reutiliza sin editarlos los scripts de
reproducir_volcat (comun_h11, huella_png, rt_e2, h11_analisis, rt_niveles) y los caches de H3, beta73 y E2,
todo de solo lectura. Lo nuevo (L1b, GFS, nodos RT por hora, variables) va a H13DIR.
"""
import os, sys, glob
import numpy as np
from datetime import datetime, timedelta

AQUI = os.path.dirname(os.path.abspath(__file__))
RV_SCRIPTS = os.path.abspath(os.path.join(AQUI, "..", "..", "reproducir_volcat", "scripts"))
sys.path.insert(0, RV_SCRIPTS)

H13DIR = os.environ.get("H13_DIR", r"D:\goes_cache\h13")   # en D: porque C: quedo casi lleno (20-11)

# Los scratchpads de H3, beta73 y reproducir VOLCAT se borraron el 20-11 para liberar C:. Sus copias rescatadas
# (inventario VOLCAT, huellas, pareos, rt.py, caches L1b y GFS) se copiaron a <H13DIR>/shim con la misma
# estructura. comun_h11 tiene esas rutas escritas como literales: se carga su fuente cambiando solo esos
# literales, sin editar el archivo de la etapa 2.
SHIM = os.path.join(H13DIR, "shim")
os.environ["H11_TRABAJO"] = os.path.join(SHIM, "rv")


def _cargar_comun_h11():
    import types, re
    src = open(os.path.join(RV_SCRIPTS, "comun_h11.py"), encoding="utf-8").read()
    src = re.sub(r'^H3 = r".*"$', lambda _m: f'H3 = r"{os.path.join(SHIM, "h3")}"', src, count=1, flags=re.M)
    src = re.sub(r'^B73 = r".*"$', lambda _m: f'B73 = r"{os.path.join(SHIM, "b73")}"', src, count=1, flags=re.M)
    m = types.ModuleType("comun_h11"); m.__file__ = os.path.join(RV_SCRIPTS, "comun_h11.py")
    sys.modules["comun_h11"] = m
    exec(compile(src, m.__file__, "exec"), m.__dict__)
    return m


C = sys.modules.get("comun_h11") or _cargar_comun_h11()
CACHE13 = os.path.join(H13DIR, "cache"); os.makedirs(CACHE13, exist_ok=True)
GFS13 = os.path.join(H13DIR, "gfs"); os.makedirs(GFS13, exist_ok=True)
RTH = os.path.join(H13DIR, "rt_hora"); os.makedirs(RTH, exist_ok=True)
FEAT13 = os.path.join(H13DIR, "feat"); os.makedirs(FEAT13, exist_ok=True)
PNG13 = os.path.join(H13DIR, "png"); os.makedirs(PNG13, exist_ok=True)

M10 = timedelta(minutes=10)
D0, D1 = datetime(2026, 10, 20), datetime(2026, 11, 19, 23, 50)
CACHES = [os.path.join(C.H3, "cache"), os.path.join(C.B73, "cache"), os.path.join(C.TRABAJO, "cache_e2"), CACHE13]
GFSDIRS = [os.path.join(C.H3, "gfs"), os.path.join(C.B73, "gfs"), os.path.join(C.TRABAJO, "gfs_e2"), GFS13]


def k(dt):
    return f"{dt:%Y%m%d_%H%M}"


def path_escena(dt):
    for d in CACHES:
        p = os.path.join(d, k(dt) + ".npz")
        if os.path.exists(p):
            return p
    return None


def load(dt):
    p = path_escena(dt)
    if p is None:
        return None
    z = np.load(p)
    d = {b: z[f"bt{b}"].astype("float64") for b in C.BANDS}
    d["rad"] = {b: z[f"rad{b}"].astype("float64") for b in C.BANDS}
    d["co"] = {b: tuple(float(c) for c in z[f"co{b}"]) for b in C.BANDS}
    return d


def path_gfs_hora(h):
    for d in GFSDIRS:
        p = os.path.join(d, f"gfs_{h:%Y%m%d%H}.npz")
        if os.path.exists(p):
            return p
    return None


def horas_que_encierran(dt):
    """Horas GFS que encierran el scan (para interpolar el cielo despejado en el tiempo) y el peso de la segunda."""
    h0 = dt.replace(minute=0, second=0, microsecond=0)
    return h0, h0 + timedelta(hours=1), (dt - h0).total_seconds() / 3600.0


def jornada(dt):
    """Fecha local de Chile (UTC - 3): un episodio que cruza la medianoche UTC queda en una sola jornada."""
    return (dt - timedelta(hours=3)).strftime("%Y-%m-%d")


# ------------------------------------------------------------------ cuadros y ventanas
INV = C._INV


def anclados():
    return sorted(t for t, r in INV.items() if r["anc"] and not r["manto"])


def tramos(gap_min=60):
    a = anclados(); out = [[a[0]]]
    for t in a[1:]:
        if t - out[-1][-1] <= timedelta(minutes=gap_min):
            out[-1].append(t)
        else:
            out.append([t])
    return out


def ventana_pos():
    """Todos los scans de 10 min desde 60 min antes del primer cuadro anclado de cada tramo hasta 60 min despues
    del ultimo (los tramos se arman uniendo cuadros anclados separados por <= 60 min)."""
    w = set()
    for tr in tramos():
        t = tr[0] - 6 * M10
        while t <= tr[-1] + 6 * M10:
            w.add(t); t += M10
    return sorted(w)


def limpio_control(dt):
    """Dia candidato a control en el minuto dt: el cuadro dt publicado con barra, y de dt - 90 a dt + 60 min
    ningun cuadro con objeto a <= 50 km ni manto; se toleran hasta 2 cuadros no publicados (sin registro)."""
    r = INV.get(dt)
    if r is None or not r["barra"] or r["manto"] or r["n50"] > 0:
        return False
    faltan = 0
    for m in range(-90, 61, 10):
        q = INV.get(dt + timedelta(minutes=m))
        if q is None:
            faltan += 1
            continue
        if q["n50"] > 0 or q["manto"]:
            return False
    return faltan <= 2


def candidatos(t):
    out = []
    for dd in range(-10, 11):
        c = t + timedelta(days=dd)
        if dd == 0 or not (D0 <= c <= D1) or jornada(c) == jornada(t):
            continue
        if limpio_control(c):
            out.append(c)
    return out


def historia(t, n=3):
    return [t - i * M10 for i in range(n + 1)]


def scans_necesarios():
    s = set(ventana_pos())
    for t in anclados():
        for c in candidatos(t):
            s |= set(historia(c))
    return sorted(s)
