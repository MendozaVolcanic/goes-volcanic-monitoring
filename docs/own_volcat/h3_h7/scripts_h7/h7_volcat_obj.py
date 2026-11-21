"""H7: objetos VOLCAT por cuadro (28-10, 29-10, 10-11, 14-11) y su huella en la grilla ABI de la ventana.

Decodificacion igual que paso3/paso4/pruebaA (sesiones anteriores): pixel con ceniza = pixel que
volcat_colorbar.classify_pixels asigna a un bloque de la barra Ash_Height (saturacion >= 0,2), dentro de la
zona util del mapa (VALIDO: sin titulo, globo, logos ni pixeles sobreimpresos fijos). Objetos de 8 vecinos
sobre todo el mapa; fuera los mantos (> 5 % del mapa, MAX_SECTOR_FRAC) y el ruido (<= 3 px).
Distancia al crater por haversine desde el centro de cada pixel del PNG (grilla CE del sector).

Huella en ABI: union de dos mapeos (cada pixel ABI toma el pixel VOLCAT mas cercano, como huellas.py; y cada
pixel VOLCAT del objeto marca su pixel ABI mas cercano), para que un objeto chico no se pierda al remuestrear.
Salida: objetos.json y huellas_h7.npz (claves 'YYYYMMDD_HHMM_anc' y '_50').
"""
import os, sys, re, json, math
from datetime import datetime
from multiprocessing import Pool
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

from pathlib import Path  # noqa: E402
# Raiz del repo desde la ubicacion del script (docs/own_volcat/<prueba>/<scripts>/). Antes: ruta fija a un
# worktree ya borrado; aqui solo se usa para importar src/.
REPO = str(Path(__file__).resolve().parents[4])
sys.path.insert(0, REPO)
from src.process import volcat_colorbar as vc  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DET = r"C:\Users\nmend\AppData\Local\Temp\claude\d6ea8719dcf88502\536a0873-47fb-4b33-9ee5-de0197c3f321\scratchpad\det"
PNG_OCT = r"C:\Users\nmend\AppData\Local\Temp\claude\3960f3d64983ed82\91527e04-4416-4efd-b41a-e8b2d704158c\scratchpad\volcat_extra\png"
PNG_NOV = r"C:\Users\nmend\AppData\Local\Temp\claude\58c6c65788fdfd96\9c58fda3-6424-4269-8b61-4905a4c1d033\scratchpad\volcat_chillan_10min\png"
FREQ = r"C:\Users\nmend\AppData\Local\Temp\claude\58c6c65788fdfd96\9c58fda3-6424-4269-8b61-4905a4c1d033\scratchpad\volcat_chillan_10min\frecuencia_pixel_clasificado.npy"
DIAS = {"2026-10-28": PNG_OCT, "2026-10-29": PNG_OCT, "2026-11-10": PNG_NOV, "2026-11-14": PNG_NOV}

dp = math.degrees(72.80000305175781 / 206264.796875)
LAT0 = -31.8007698059082 + 36 * dp
LON0 = 278.9210815429688 - 360.0
VLAT, VLON = -36.86, -71.38
_F = np.load(FREQ)
VALIDO = _F <= 0.2 * 2181
VALIDO[:70] = False
VALIDO[640:, :140] = False
VALIDO[640:, 840:] = False
RX = re.compile(r"ABI\.(\d{4}-\d{2}-\d{2})\.(\d{2})-(\d{2})-(\d{2})\.Ash_Height")


def hav(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


rr, cc = np.mgrid[0:755, 0:1000]
DCHI = hav(LAT0 - rr * dp, LON0 + cc * dp, VLAT, VLON)
ll = np.load(os.path.join(DET, "latlon.npz")); LAT, LON = ll["lat"], ll["lon"]
RR = np.rint((LAT0 - LAT) / dp).astype(int); CC = np.rint((LON - LON0) / dp).astype(int)
_kx = np.cos(np.radians(VLAT))
TREE = cKDTree(np.c_[LAT.ravel(), LON.ravel() * _kx])


def a_abi(mask_png, hmap, W):
    out = np.zeros(LAT.shape, bool)
    ins = (RR >= 0) & (RR < hmap) & (CC >= 0) & (CC < W)
    out[ins] = mask_png[RR[ins], CC[ins]]
    ys, xs = np.nonzero(mask_png)
    if len(ys):
        la, lo = LAT0 - ys * dp, LON0 + xs * dp
        dd, ii = TREE.query(np.c_[la, lo * _kx])
        ok = dd < 0.03  # solo pixeles VOLCAT que caen dentro de la ventana ABI
        out.ravel()[ii[ok]] = True
    return out


def uno(arg):
    fn, carpeta = arg
    m_ = RX.search(fn)
    dt = datetime.strptime(f"{m_.group(1)} {m_.group(2)}:{m_.group(3)}:{m_.group(4)}", "%Y-%m-%d %H:%M:%S")
    try:
        a = np.asarray(Image.open(os.path.join(carpeta, fn)).convert("RGB"), dtype="float64")
    except Exception as e:  # noqa: BLE001
        return dict(fn=fn, dt=dt.isoformat(), err=repr(e)), None, None
    H, W = a.shape[:2]; hmap = int(vc.MAP_FRAC * H)
    bins = vc.palette_bins(a[hmap:]); m = a[:hmap]
    if bins is None:
        return dict(fn=fn, dt=dt.isoformat(), err="sin_barra"), None, None
    cmask = vc._saturation(m) >= 0.2
    ok = np.zeros(cmask.shape, bool)
    if cmask.any():
        ok[cmask] = vc.classify_pixels(m[cmask], bins)["ok"]
    ok &= VALIDO[:hmap, :W]
    lab, n = ndimage.label(ok, structure=np.ones((3, 3), int))
    tam = np.bincount(lab.ravel(), minlength=n + 1); tam[0] = 0
    D = DCHI[:hmap, :W]
    objs = []
    anc_ids, near_ids = [], []
    if n:
        dmin = ndimage.minimum(D, lab, range(1, n + 1))
        for i in range(1, n + 1):
            s = int(tam[i])
            if s <= 3:
                continue
            manto = s / ok.size > vc.MAX_SECTOR_FRAC
            d = float(dmin[i - 1])
            if d <= 50 or manto:
                objs.append(dict(px=s, dmin_km=round(d, 1), manto=bool(manto), anclado=bool(d <= 10 and not manto)))
            if manto:
                continue
            if d <= 50:
                near_ids.append(i)
            if d <= 10:
                anc_ids.append(i)
    hanc = a_abi(np.isin(lab, anc_ids), hmap, W) if anc_ids else np.zeros(LAT.shape, bool)
    h50 = a_abi(np.isin(lab, near_ids), hmap, W) if near_ids else np.zeros(LAT.shape, bool)
    rec = dict(fn=fn, dt=dt.isoformat(), objs=objs, n50=len(near_ids), nanc=len(anc_ids),
               px_anc=int(sum(tam[i] for i in anc_ids)), abi_anc=int(hanc.sum()), abi_50=int(h50.sum()))
    return rec, hanc, h50


if __name__ == "__main__":
    tareas = []
    for dia, carpeta in DIAS.items():
        for fn in sorted(os.listdir(carpeta)):
            if fn.startswith("GOES-19.ABI.") and f".{dia}." in fn and fn.endswith(".png"):
                tareas.append((fn, carpeta))
    with Pool(6) as pool:
        res = pool.map(uno, tareas, chunksize=4)
    hu = {}
    for rec, ha, h5 in res:
        if ha is not None:
            k = datetime.fromisoformat(rec["dt"]).strftime("%Y%m%d_%H%M")
            hu[k + "_anc"] = ha; hu[k + "_50"] = h5
    json.dump([r[0] for r in res], open(os.path.join(HERE, "objetos.json"), "w"), indent=0)
    np.savez_compressed(os.path.join(HERE, "huellas_h7.npz"), **hu)
    print("cuadros", len(res), "errores", sum(1 for r in res if "err" in r[0]))
    for d in DIAS:
        rs = [r[0] for r in res if r[0]["dt"].startswith(d) and "err" not in r[0]]
        print(d, "cuadros", len(rs), "con objeto<=50km", sum(r["n50"] > 0 for r in rs), "anclados", sum(r["nanc"] > 0 for r in rs),
              "con manto", sum(any(o["manto"] for o in r["objs"]) for r in rs),
              "obj>500px cerca", sum(any(o["px"] > 500 and o["dmin_km"] <= 50 for o in r["objs"]) for r in rs))
