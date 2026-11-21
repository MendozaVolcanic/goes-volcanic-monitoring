"""Paso 4: objetos VOLCAT anclados al crater de Chillan por dia/noche en los dias no revisados.
Criterio: criterio_paso4_volcat_nocturno_2026-11-18.md. Uso: python paso4_analisis.py [carpeta_png]"""
import os, sys, re, json
from datetime import datetime, timezone, timedelta
from multiprocessing import Pool
import numpy as np
from PIL import Image
from scipy import ndimage
import paso3_objetos as p
from paso3_objetos import vc

PNG = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "volcat_extra", "png")
rr, cc = np.mgrid[0:755, 0:1000]
DCHI = p.hav(p.LAT0 - rr * p.dp, p.LON0 + cc * p.dp, *p.CHI)
SEED = DCHI <= 10
NEAR50 = DCHI <= 50


def uno(fn):
    m_ = p.RX.search(fn)
    dt = datetime.strptime(f"{m_.group(1)} {m_.group(2)}:{m_.group(3)}:{m_.group(4)}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    try:
        a = np.asarray(Image.open(os.path.join(PNG, fn)).convert("RGB"), dtype="float64")
    except Exception:
        return fn, dt.isoformat(), None, None, None, None
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
    z = p.sza(dt, *p.CHI)
    return fn, dt.isoformat(), bins is not None, (manto or grande), anc, z


if __name__ == "__main__":
    fs = sorted(f for f in os.listdir(PNG) if f.startswith("GOES-19.ABI.") and f.endswith(".png"))
    with Pool(6) as pool:
        res = pool.map(uno, fs, chunksize=8)
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "paso4_res.json"), "w"))
    por = {}
    for fn, t, okb, manto, anc, z in res:
        d = t[:10]; e = por.setdefault(d, {"cuadros": 0, "dia": [], "crep": [], "noche": [], "manto": 0, "sinbarra": 0})
        e["cuadros"] += 1
        if okb is None or not okb:
            e["sinbarra"] += 1; continue
        e["manto"] += manto
        if anc:
            fase = "dia" if z < 80 else ("noche" if z >= 90 else "crep")
            e[fase].append((t[11:16], max(anc), manto))
    for d, e in sorted(por.items()):
        print(d, "cuadros", e["cuadros"], "sin barra", e["sinbarra"], "con manto o sistema grande a <50 km", e["manto"],
              "| anclados dia", len(e["dia"]), "crep", len(e["crep"]), "noche", len(e["noche"]))
        for f in ("noche", "crep"):
            if e[f]:
                print("   ", f, e[f])
        if e["dia"]:
            print("    dia", e["dia"][0][0], "a", e["dia"][-1][0], "tam max", max(x[1] for x in e["dia"]))
    # noches consecutivas
    noct = sorted(datetime.fromisoformat(t) for fn, t, okb, manto, anc, z in res if okb and anc and z >= 90 and not manto)
    cons = sum(1 for a, b in zip(noct, noct[1:]) if b - a <= timedelta(minutes=10, seconds=30))
    print("cuadros nocturnos anclados sin manto:", len(noct), " pares consecutivos (10 min):", cons)
