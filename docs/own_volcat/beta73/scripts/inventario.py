"""beta73, inventario: cuadros VOLCAT con objeto anclado al crater de Chillan (regla de paso4_analisis.py).

Objeto = componente conexa (8 vecinos) de pixeles con ceniza (volcat_colorbar.classify_pixels, saturacion >= 0,2,
zona util VALIDO) de 4 a 500 px que toca el disco de 10 km del crater. Se marca manto si algun objeto supera
MAX_SECTOR_FRAC del mapa o hay un sistema > 500 px a <= 50 km. Fase: dia si cenit solar < 80, noche si >= 90,
crepusculo entre medio. No calcula nada de L1b: solo lee PNG.
Uso: python inventario.py salida.json carpeta_png [carpeta_png ...]
"""
import os, sys, json
from datetime import datetime, timezone
from multiprocessing import Pool
import numpy as np
from PIL import Image
from scipy import ndimage

PR = r"C:\Users\nmend\AppData\Local\Temp\claude\3960f3d64983ed82\91527e04-4416-4efd-b41a-e8b2d704158c\scratchpad\pruebas"
sys.path.insert(0, PR)
import paso3_objetos as p  # noqa: E402
from paso3_objetos import vc  # noqa: E402

rr, cc = np.mgrid[0:755, 0:1000]
DCHI = p.hav(p.LAT0 - rr * p.dp, p.LON0 + cc * p.dp, *p.CHI)
SEED = DCHI <= 10
NEAR50 = DCHI <= 50


def uno(path):
    fn = os.path.basename(path)
    m_ = p.RX.search(fn)
    dt = datetime.strptime(f"{m_.group(1)} {m_.group(2)}:{m_.group(3)}:{m_.group(4)}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    z = p.sza(dt, *p.CHI)
    try:
        a = np.asarray(Image.open(path).convert("RGB"), dtype="float64")
    except Exception:
        return dict(fn=fn, t=dt.isoformat(), barra=None, manto=None, anc=[], sza=z, n50=0)
    H, W = a.shape[:2]; hmap = int(vc.MAP_FRAC * H)
    bins = vc.palette_bins(a[hmap:]); m = a[:hmap]
    cmask = vc._saturation(m) >= 0.2
    ok = np.zeros(cmask.shape, bool)
    if cmask.any() and bins is not None:
        ok[cmask] = vc.classify_pixels(m[cmask], bins)["ok"]
    ok &= p.VALIDO[:hmap, :W]
    lab, n = ndimage.label(ok, structure=np.ones((3, 3), int))
    tam = np.bincount(lab.ravel(), minlength=n + 1); tam[0] = 0
    manto = bool((tam / ok.size > vc.MAX_SECTOR_FRAC).any())
    ids = np.unique(lab[SEED[:hmap, :W] & ok]); ids = ids[ids > 0]
    anc = [int(tam[i]) for i in ids if 4 <= tam[i] <= 500]
    near = np.unique(lab[NEAR50[:hmap, :W] & ok]); near = near[near > 0]
    grande = bool(any(tam[i] > 500 for i in near))
    # cuadro con algo de ceniza a <= 50 km (para excluir dias de control)
    n50 = int((ok & NEAR50[:hmap, :W]).sum())
    return dict(fn=fn, t=dt.isoformat(), barra=bins is not None, manto=bool(manto or grande), anc=anc, sza=z, n50=n50)


if __name__ == "__main__":
    out = sys.argv[1]
    fs = []
    for d in sys.argv[2:]:
        fs += [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.startswith("GOES-19.ABI.") and f.endswith(".png")]
    with Pool(6) as pool:
        res = pool.map(uno, fs, chunksize=8)
    json.dump(res, open(out + ".tmp", "w")); os.replace(out + ".tmp", out)
    print("cuadros", len(res))
