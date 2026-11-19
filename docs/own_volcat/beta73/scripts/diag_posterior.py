"""beta73, diagnostico POSTERIOR (no decide, se escribio despues de ver las tablas): el exceso de C10 del
estrato N, esta solo en la huella, o en toda la ventana? Y el GFS ve mas humedad en la troposfera media la
noche positiva que la de control?
Por par N: mediana (positivo - control) de BT10 - BT14 en huella, anillo y lejos (> 20 px de la huella, sin
ceniza VOLCAT); agua precipitable sobre 600 hPa del GFS en el crater (positivo y control)."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import os, json
import numpy as np
from datetime import datetime
from scipy import ndimage
import comun_b73 as C
import metricas_b73 as M

HU = np.load(os.path.join(C.HERE, "huellas_b73.npz"))
PA = [p for p in json.load(open(os.path.join(C.HERE, "pareo_b73.json"))) if p["estado"] == "ok"]
CHI = (-36.86, -71.38)
iy, ix = np.unravel_index(np.argmin((M.LAT - CHI[0]) ** 2 + (M.LON - CHI[1]) ** 2), M.LAT.shape)


def pw600(dt):
    g = M.gfs(dt); la, lo = np.array([M.LAT[iy, ix]]), np.array([M.LON[iy, ix]])
    q = np.array([M._i2(g, g["q"][i], la, lo)[0] for i in range(len(g["p"]))]); p = g["p"]
    ps = M._i2(g, g["psfc"], la, lo)[0]
    sel = (p <= 600) & (p >= 100)
    pp, qq = p[sel][::-1], q[sel][::-1]          # 100 -> 600 hPa ascendente
    return float(np.trapezoid(qq, pp * 100) / 9.80665), float(M._i2(g, g["q"][list(p).index(500)], la, lo)[0] * 1e3), float(ps)


print("estrato par | d(BT10-BT14) pos-ctrl K: huella / anillo / lejos | PW 100-600 hPa (mm) pos/ctrl | q500 (g/kg) pos/ctrl")
for p in PA:
    for est in ("N", "D"):
        pass
    dp = datetime.strptime(p["pos"], "%Y%m%d_%H%M"); dc = datetime.strptime(p["ctrl"], "%Y%m%d_%H%M")
    hv = HU["h_" + p["pos"]]; ash = HU["a_" + p["pos"]]
    ring = ndimage.binary_dilation(hv, np.ones((13, 13), bool)) & ~ndimage.binary_dilation(hv, np.ones((3, 3), bool)) & ~ash
    far = ~ndimage.binary_dilation(hv | ash, np.ones((41, 41), bool))
    sp, sc = C.load(dp), C.load(dc)
    d = (sp[10] - sp[14]) - (sc[10] - sc[14])
    a, b = pw600(dp), pw600(dc)
    print(f"{p['estrato']} {p['pos']}-{p['ctrl'][6:8]}/{p['ctrl'][4:6]} | {np.nanmedian(d[hv]):+.2f} / {np.nanmedian(d[ring]):+.2f} / {np.nanmedian(d[far]):+.2f} (n lejos {far.sum()})"
          f" | {a[0]:.2f}/{b[0]:.2f} | {a[1]:.2f}/{b[1]:.2f}")


# --- mismo diagnostico sobre los pares del indicio (H3, casos 1 y 2: 28-10 y 29-10), y correlacion en beta73
if __name__ == "__main__":
    from scipy.stats import spearmanr
    H3P = json.load(open(os.path.join(C.H3, "pareo.json"))); H3H = np.load(os.path.join(C.H3, "huellas_h3.npz"))
    print("\nPares del indicio (H3 casos 1 y 2), mismo calculo:")
    for p in H3P:
        if p.get("estado") != "ok" or p["caso"] not in (1, 2):
            continue
        dp = datetime.strptime(p["pos"], "%Y%m%d_%H%M"); dc = datetime.strptime(p["ctrl"], "%Y%m%d_%H%M")
        hv = H3H[p["pos"]]
        ring = ndimage.binary_dilation(hv, np.ones((13, 13), bool)) & ~ndimage.binary_dilation(hv, np.ones((3, 3), bool))
        far = ~ndimage.binary_dilation(hv, np.ones((41, 41), bool))
        sp, sc = C.load(dp), C.load(dc)
        d = (sp[10] - sp[14]) - (sc[10] - sc[14]); a, b = pw600(dp), pw600(dc)
        print(f"caso {p['caso']} {p['pos']}-{p['ctrl'][6:8]}/{p['ctrl'][4:6]} | {np.nanmedian(d[hv]):+.2f} / {np.nanmedian(d[ring]):+.2f} / {np.nanmedian(d[far]):+.2f}"
              f" | {a[0]:.2f}/{b[0]:.2f} | {a[1]:.2f}/{b[1]:.2f}")
    xs, ys = [], []
    for p in PA:
        dp = datetime.strptime(p["pos"], "%Y%m%d_%H%M"); dc = datetime.strptime(p["ctrl"], "%Y%m%d_%H%M")
        hv = HU["h_" + p["pos"]]; ash = HU["a_" + p["pos"]]
        far = ~ndimage.binary_dilation(hv | ash, np.ones((41, 41), bool))
        sp, sc = C.load(dp), C.load(dc)
        xs.append(pw600(dp)[0] - pw600(dc)[0]); ys.append(np.nanmedian(((sp[10] - sp[14]) - (sc[10] - sc[14]))[far]))
    r = spearmanr(xs, ys)
    print(f"\n49 pares: Spearman entre dPW(100-600 hPa, GFS) y d(BT10-BT14) lejos de la huella: rho={r.statistic:+.2f} p={r.pvalue:.1e}")
