"""Reconstruye la ventana ABI 83 x 94 del cache (window.json y latlon.npz se perdieron con el scratchpad del
detector del 17-11). Por que asi: el cache de H3 guarda la radiancia de la ventana pero no su posicion; se
lee un bloque grande del mismo NetCDF L1b C14 en S3 y se busca el desplazamiento donde la radiancia coincide
exacta. Despues se calcula lat/lon de cada pixel con la proyeccion geoestacionaria del propio archivo.
Salida: <TRABAJO>/window.json y <TRABAJO>/latlon.npz.
"""
import os, json, sys
import numpy as np, h5py, s3fs
from pyproj import Proj

TRABAJO = sys.argv[1]
CACHE_H3 = r"C:\Users\nmend\AppData\Local\Temp\claude\caac88451b34493f\bd33fd70-a478-403d-be84-fcf2fda5792e\scratchpad\h3\cache"
z = np.load(os.path.join(CACHE_H3, "20261026_0100.npz"))
ref = z["rad14"].astype("float64"); key = "noaa-goes19/ABI-L1b-RadF/2026/299/01/" + str(z["key14"])
fs = s3fs.S3FileSystem(anon=True)
with fs.open(key, "rb", block_size=2**20, cache_type="blockcache") as fo, h5py.File(fo, "r") as f:
    r = f["Rad"]; sf, ao = r.attrs["scale_factor"][0], r.attrs["add_offset"][0]
    x = f["x"][:] * f["x"].attrs["scale_factor"][0] + f["x"].attrs["add_offset"][0]
    y = f["y"][:] * f["y"].attrs["scale_factor"][0] + f["y"].attrs["add_offset"][0]
    gp = f["goes_imager_projection"]; h = float(gp.attrs["perspective_point_height"][0])
    lon0 = float(gp.attrs["longitude_of_projection_origin"][0])
    p = Proj(proj="geos", lon_0=lon0, h=h, ellps="GRS80", sweep="x")
    xc, yc = p(-71.38, -36.86); ic = int(np.argmin(abs(y * h - yc))); jc = int(np.argmin(abs(x * h - xc)))
    Y0, X0 = ic - 150, jc - 150
    blk = r[Y0:Y0 + 300, X0:X0 + 300].astype("float64") * sf + ao
best = None
for dy in range(0, 300 - 83):
    for dx in range(0, 300 - 94):
        d = np.nanmax(abs(blk[dy:dy + 83, dx:dx + 94] - ref))
        if best is None or d < best[0]:
            best = (d, dy, dx)
d, dy, dx = best
y0, x0 = Y0 + dy, X0 + dx
print("max dif", d, "y0", y0, "x0", x0, "chillan px aprox", ic - y0, jc - x0)
assert d < 1e-3, "no calza exacto"
win = {"y0": y0, "y1": y0 + 83, "x0": x0, "x1": x0 + 94, "fuente": key}
json.dump(win, open(os.path.join(TRABAJO, "window.json"), "w"), indent=1)
XX, YY = np.meshgrid(x[x0:x0 + 94] * h, y[y0:y0 + 83] * h)
lo, la = p(XX, YY, inverse=True)
np.savez(os.path.join(TRABAJO, "latlon.npz"), lat=la, lon=lo)
print("lat", la.min(), la.max(), "lon", lo.min(), lo.max())
