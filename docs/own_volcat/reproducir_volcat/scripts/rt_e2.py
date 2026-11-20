"""Etapa 2: cielo despejado y nube negra por nivel en una rejilla cada 3 pixeles, para todas las escenas.

Uso: python rt_e2.py escenas [n_procesos]   (corre el modelo en los nodos de cada escena, reanudable)
     python rt_e2.py validar                (compara la interpolacion contra el calculo directo de H11)

Por que una rejilla: el modelo de H3 cuesta ~0,2 s por pixel y la etapa 2 necesita ~1.250 pixeles por escena
(disco de 40 km) en ~800 escenas. Todo lo que entra al modelo (perfil GFS 0,25 grados, presion y temperatura
de superficie del GFS, cenit satelital) es una interpolacion suave, asi que se calcula en un nodo de cada 3
pixeles (6 km) y se interpola bilineal. R_cld de un nivel se interpola solo si los 4 nodos lo tienen sobre la
superficie; si no, queda NaN para ese pixel y nivel. La validacion usa como verdad los pixeles que H11 calculo
directo, y declara el error antes de usar la rejilla.
"""
import os, sys, glob
import numpy as np
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun_h11 as C  # noqa: E402
import rt_niveles as R  # noqa: E402
import huella_png as HP  # noqa: E402

PASO = 3
RADIO = 40.0
RTE2 = os.path.join(C.TRABAJO, "rt_e2"); os.makedirs(RTE2, exist_ok=True)
CACHE_E2 = os.path.join(C.TRABAJO, "cache_e2")
NY, NX = C.LAT.shape
REG = HP.DIST <= RADIO
_ry, _rx = np.nonzero(REG)
Y0, Y1 = (_ry.min() // PASO) * PASO, min(NY - 1, (_ry.max() // PASO + 1) * PASO)
X0, X1 = (_rx.min() // PASO) * PASO, min(NX - 1, (_rx.max() // PASO + 1) * PASO)
NODOS_Y = np.arange(Y0, Y1 + 1, PASO); NODOS_X = np.arange(X0, X1 + 1, PASO)


def path_escena(dt):
    p = C.path_escena(dt)
    if p is None:
        q = os.path.join(CACHE_E2, C.k(dt) + ".npz")
        return q if os.path.exists(q) else None
    return p


def load(dt):
    p = path_escena(dt)
    z = np.load(p)
    d = {b: z[f"bt{b}"].astype("float64") for b in C.BANDS}
    d["rad"] = {b: z[f"rad{b}"].astype("float64") for b in C.BANDS}
    d["co"] = {b: tuple(float(c) for c in z[f"co{b}"]) for b in C.BANDS}
    return d


def nodos():
    yy, xx = np.meshgrid(NODOS_Y, NODOS_X, indexing="ij")
    return yy.ravel(), xx.ravel()


def interp(z, ys, xs):
    """Interpola los campos del npz de nodos a los pixeles (ys, xs). Devuelve rclr (n,4) y rcld (n,33,4)."""
    ny, nx = len(NODOS_Y), len(NODOS_X)
    rc = z["rclr"].reshape(ny, nx, 4); rd = z["rcld"].reshape(ny, nx, R.NB, 4)
    fy = (ys - Y0) / PASO; fx = (xs - X0) / PASO
    iy = np.clip(np.floor(fy).astype(int), 0, ny - 2); ix = np.clip(np.floor(fx).astype(int), 0, nx - 2)
    wy = (fy - iy)[:, None]; wx = (fx - ix)[:, None]
    def bil(a):  # noqa: E306
        sh = (-1,) + (1,) * (a.ndim - 2)
        w00 = ((1 - wy) * (1 - wx)).reshape(sh); w01 = ((1 - wy) * wx).reshape(sh)
        w10 = (wy * (1 - wx)).reshape(sh); w11 = (wy * wx).reshape(sh)
        return a[iy, ix] * w00 + a[iy, ix + 1] * w01 + a[iy + 1, ix] * w10 + a[iy + 1, ix + 1] * w11
    return bil(rc), bil(rd)   # NaN se propaga: un nivel bajo la superficie en cualquier nodo queda NaN


def lista_escenas():
    """Escenas con etiqueta: positivos (anclados, sin manto), limpias, y el manto del 16-11."""
    out = []
    for dt, r in sorted(C._INV.items()):
        if path_escena(dt) is None:
            continue
        if r["manto"]:
            t = "manto"
        elif r["anc"]:
            t = "pos"
        elif r["barra"] and r["n50"] == 0:
            t = "neg"
        else:
            continue
        out.append((dt, t))
    return out


def tarea(dt):
    ys, xs = nodos()
    return R.tarea((os.path.join(RTE2, C.k(dt) + ".npz"), dt, ys, xs, np.ones(len(ys), bool)))


def validar():
    """Pixeles de H11 (calculo directo) cuya escena ya tiene nodos: error de BT de cielo despejado por banda,
    de R_cld en la tropopausa y de eps_tot(11)."""
    import h11_analisis as A
    err_bt = []; err_e = []; err_cld = []; n_nan = 0; n = 0
    for f in sorted(glob.glob(os.path.join(C.RTDIR, "*.npz"))):
        b = os.path.basename(f); par, rol = b[:13], b[14:-4]
        pp = [p for p in C.pares() if p["pos"] == par][0]; dt = C.dtk(pp[rol])
        g = os.path.join(RTE2, C.k(dt) + ".npz")
        if not os.path.exists(g):
            continue
        z = np.load(f); w = np.load(g); s = load(dt)
        sel = z["full"] & ((z["ys"] >= Y0) & (z["ys"] <= Y1) & (z["xs"] >= X0) & (z["xs"] <= X1))
        ys, xs = z["ys"][sel], z["xs"][sel]
        rc, rd = interp(w, ys, xs)
        for i, j in enumerate(np.nonzero(sel)[0]):
            for q, bb in enumerate(C.BANDS):
                err_bt.append((q, C.rt.bt_de_rad(rc[i, q], s["co"][bb]) - C.rt.bt_de_rad(z["rclr"][j, q], s["co"][bb])))
            lp = np.log(z["ptropo"][j])
            okd = np.isfinite(rd[i][:, 0]).sum() >= 3
            if not okd:
                n_nan += 1; continue
            c_ex = A.cld_en(z["rcld"][j], lp); c_in = A.cld_en(rd[i], lp)
            ro = s["rad"][14][ys[i], xs[i]]
            err_cld.append(C.rt.bt_de_rad(c_in[2], s["co"][14]) - C.rt.bt_de_rad(c_ex[2], s["co"][14]))
            err_e.append(A.eps(ro, rc[i, 2], c_in[2]) - A.eps(ro, z["rclr"][j, 2], c_ex[2]))
            n += 1
    e = np.array([v for _, v in err_bt]); q = np.array([k for k, _ in err_bt])
    for k, bb in enumerate(C.BANDS):
        v = np.abs(e[q == k]); print(f"BT clr C{bb}: n={len(v)} p50={np.median(v):.3f} p95={np.percentile(v, 95):.3f} max={v.max():.3f} K")
    v = np.abs(err_cld); print(f"BT R_cld tropopausa C14: p95={np.percentile(v, 95):.3f} max={v.max():.3f} K")
    v = np.abs(err_e); print(f"eps_tot(11): p50={np.median(v):.4f} p95={np.percentile(v, 95):.4f} max={v.max():.4f} | pixeles {n}, sin niveles {n_nan}")


if __name__ == "__main__":
    if sys.argv[1] == "validar":
        validar()
    else:
        npr = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        E = lista_escenas()
        print("escenas", len(E), {t: sum(1 for _, x in E if x == t) for t in ("pos", "neg", "manto")}, "nodos por escena", len(nodos()[0]), flush=True)
        todo = [dt for dt, _ in E if not os.path.exists(os.path.join(RTE2, C.k(dt) + ".npz"))]
        with Pool(npr) as pool:
            for out, msg in pool.imap_unordered(tarea, todo):
                print(os.path.basename(out), msg, flush=True)
