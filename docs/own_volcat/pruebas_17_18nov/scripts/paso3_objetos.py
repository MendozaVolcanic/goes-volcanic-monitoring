"""Paso 3 (H2): objetos VOLCAT por tamano y distancia al volcan GVP mas cercano.
Criterio: criterio_paso3_objetos_lejos_2026-11-18.md (carpeta de notas). Solo lectura de PNG ya bajados."""
import sys, json, math, re
from pathlib import Path
from datetime import datetime, timezone
from multiprocessing import Pool
import numpy as np
from PIL import Image
from scipy import ndimage

REPO = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\Goes\.claude\worktrees\investigacion-volcat-deteccion-f4df71")
sys.path.insert(0, str(REPO))
from src.process import volcat_colorbar as vc  # noqa: E402

PNG = Path(r"C:\Users\nmend\AppData\Local\Temp\claude\58c6c65788fdfd96\9c58fda3-6424-4269-8b61-4905a4c1d033\scratchpad\volcat_chillan_10min\png")
OUT = Path(__file__).resolve().parent
GVP = OUT.parent / "gvp" / "gvp.json"
dp = math.degrees(72.80000305175781 / 206264.796875)
LAT0 = -31.8007698059082 + 36 * dp
LON0 = 278.9210815429688 - 360.0
CHI = (-36.86, -71.38)
# Zona util del mapa: fuera el titulo (filas < 70), el globo (abajo izq.), los logos (abajo der.) y todo
# pixel que se clasifica en > 20 % de los cuadros (sobreimpreso fijo; en el mapa 70-640 no hay ninguno).
_FREQ = np.load(Path(r"C:\Users\nmend\AppData\Local\Temp\claude\58c6c65788fdfd96\9c58fda3-6424-4269-8b61-4905a4c1d033\scratchpad\volcat_chillan_10min\frecuencia_pixel_clasificado.npy"))
VALIDO = _FREQ <= 0.2 * 2181
VALIDO[:70] = False
VALIDO[640:, :140] = False
VALIDO[640:, 840:] = False
RX = re.compile(r"ABI\.(\d{4}-\d{2}-\d{2})\.(\d{2})-(\d{2})-(\d{2})\.Ash_Height")


def hav(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def sza(dt, lat, lon):
    """Angulo cenital solar aproximado (NOAA, error < 1 grado)."""
    doy = dt.timetuple().tm_yday; hr = dt.hour + dt.minute / 60 + dt.second / 3600
    g = 2 * math.pi / 365 * (doy - 1 + (hr - 12) / 24)
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    tst = hr * 60 + eqt + 4 * lon
    ha = math.radians(tst / 4 - 180)
    la = math.radians(lat)
    c = math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)
    return math.degrees(math.acos(max(-1, min(1, c))))


def objetos(fn):
    m_ = RX.search(fn.name)
    dt = datetime.strptime(f"{m_.group(1)} {m_.group(2)}:{m_.group(3)}:{m_.group(4)}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    a = np.asarray(Image.open(fn).convert("RGB"), dtype="float64")
    H, W = a.shape[:2]; hmap = int(vc.MAP_FRAC * H)
    bins = vc.palette_bins(a[hmap:])
    m = a[:hmap]
    cmask = vc._saturation(m) >= 0.2
    ok = np.zeros(cmask.shape, bool)
    if cmask.any() and bins is not None:
        ok[cmask] = vc.classify_pixels(m[cmask], bins)["ok"]
    ok &= VALIDO[:hmap, :W]
    lab, n = ndimage.label(ok, structure=np.ones((3, 3), int))
    rows = []
    if n:
        tam = np.bincount(lab.ravel(), minlength=n + 1)
        cy = ndimage.mean(np.arange(hmap)[:, None] * np.ones((1, W)), lab, range(1, n + 1))
        cx = ndimage.mean(np.ones((hmap, 1)) * np.arange(W)[None, :], lab, range(1, n + 1))
        for i in range(1, n + 1):
            s = int(tam[i])
            if s <= 3:
                continue
            manto = s / ok.size > vc.MAX_SECTOR_FRAC
            lat = LAT0 - cy[i - 1] * dp; lon = LON0 + cx[i - 1] * dp
            rows.append((dt.isoformat(), s, bool(manto), float(lat), float(lon), sza(dt, lat, lon)))
    return fn.name, bins is not None, hmap, W, rows


if __name__ == "__main__":
    files = sorted(p for p in PNG.glob("GOES-19.ABI.*.png"))
    with Pool(6) as pool:
        res = pool.map(objetos, files, chunksize=8)
    json.dump({"res": res}, open(OUT / "paso3_objetos.json", "w"))
    print("cuadros", len(res), "sin barra", sum(1 for r in res if not r[1]))
