r"""S29a parte 1: nieve, nieve oscurecida, suelo descubierto y nube en la zona de 0 a 4 km de las cumbres de Antuco,
Longaví y Chillán, con Sentinel-2 L2A (Element 84) y Landsat 8/9 C2 L2 (Planetary Computer), oct-nov 2025 y 2026.
Implementa parte1_expectativas_2026-11-25.md (commit c42190c, empujado antes de buscar una escena).

Por qué: la zona de cumbre de Antuco, sin pluma, dispara de día casi 4 veces más en 2026 que en 2025 (S28a). Si la
causa es la superficie (menos nieve, roca al sol, nieve sucia) se ve en la reflectancia; si es una nube baja que
la máscara de GOES no marca, se ve en una imagen tomada cerca de un cuadro que disparó. Esto sólo comprueba: no entra
al detector.

Uso: python -I s29a_optico.py buscar | medir | figuras
"""
import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OV = os.path.abspath(os.path.join(AQUI, "..", ".."))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
FIG = os.path.join(os.path.dirname(AQUI), "figuras")
sys.path.insert(0, os.path.join(OV, "s20b_verdad_alta_res", "scripts"))
import s20b_comun as C  # noqa: E402   (sólo stac_post y pc_token)

TRAB = r"D:\goes_notas\s29\s29a\optico"
E84 = "https://earth-search.aws.element84.com/v1/search"
PC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
# cumbres: h23_comun.SITIOS (Antuco, Longaví) y h29_comun.CRATER (Chillán)
CUMBRES = {"antuco": (-37.41, -71.35), "longavi": (-36.19, -71.16), "chillan": (-36.863, -71.377)}
VENTANAS = {"2025": ("2025-09-21", "2025-11-21"), "2026": ("2026-09-21", "2026-11-24")}   # nada después del 24-11
CRS = "EPSG:32719"
RES_M, MEDIO, R_ZONA = 20.0, 5000.0, 4.0
N = int(2 * MEDIO / RES_M)
NUBE_MAX_ESCENA = 80        # filtro de búsqueda (cobertura de toda la escena); la nube local se mide aparte
# umbrales de la expectativa §1
NDSI_NIEVE, VERDE_NIEVE, VERDE_LIMPIA, NDSI_SUELO = 0.4, 0.3, 0.6, 0.2
TOK = None


def grilla(sitio):
    la, lo = CUMBRES[sitio]
    t = Transformer.from_crs(4326, CRS, always_xy=True)
    cx, cy = t.transform(lo, la)
    tr = from_origin(cx - MEDIO, cy + MEDIO, RES_M, RES_M)
    xx = (np.arange(N) + 0.5) * RES_M - MEDIO
    gx, gy = np.meshgrid(xx, -xx)
    return tr, np.hypot(gx, gy) / 1000.0


def leer(href, tr, escala=1.0, suma=0.0, rs=Resampling.bilinear, nodata=0):
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="2"):
        with rasterio.open(href) as ds:
            with WarpedVRT(ds, crs=CRS, transform=tr, width=N, height=N, resampling=rs,
                           src_nodata=nodata if nodata is not None else ds.nodata, nodata=np.nan,
                           dtype="float32") as v:
                a = v.read(1).astype("float32")
    return np.where(np.isfinite(a), a * escala + suma, np.nan).astype("float32")


# ---------- búsqueda ----------
def buscar():
    os.makedirs(TRAB, exist_ok=True)
    filas = []
    for sitio, (la, lo) in CUMBRES.items():
        pt = {"type": "Point", "coordinates": [lo, la]}
        for año, (a, b) in VENTANAS.items():
            rng = f"{a}T00:00:00Z/{b}T23:59:59Z"
            s2 = C.stac_post(E84, {"collections": ["sentinel-2-l2a"], "intersects": pt, "datetime": rng, "limit": 200,
                                   "query": {"eo:cloud_cover": {"lte": NUBE_MAX_ESCENA}}})["features"]
            ls = C.stac_post(PC, {"collections": ["landsat-c2-l2"], "intersects": pt, "datetime": rng, "limit": 200,
                                  "query": {"platform": {"in": ["landsat-8", "landsat-9"]},
                                            "eo:cloud_cover": {"lte": NUBE_MAX_ESCENA}}})["features"]
            vistos = set()
            for it in s2 + ls:
                p = it["properties"]
                clave = (p.get("platform"), p["datetime"][:16])
                if clave in vistos:          # la misma toma en dos granulos o dos versiones: una basta
                    continue
                vistos.add(clave)
                filas.append({"sitio": sitio, "año": año, "id": it["id"], "coleccion": it["collection"],
                              "plataforma": p.get("platform"), "datetime": p["datetime"],
                              "nube_escena": p.get("eo:cloud_cover")})
            print(sitio, año, len(s2), len(ls), flush=True)
    json.dump(filas, open(os.path.join(TRAB, "escenas.json"), "w"), indent=1)
    print("escenas:", len(filas))


def _item(f):
    if f["coleccion"] == "sentinel-2-l2a":
        return C.stac_post(E84, {"collections": ["sentinel-2-l2a"], "ids": [f["id"]]})["features"][0]
    return C.stac_post(PC, {"collections": ["landsat-c2-l2"], "ids": [f["id"]]})["features"][0]


def bandas(f):
    """Reflectancias azul, verde, rojo, SWIR1 y máscara de nube en la grilla de la cumbre (caché en D:)."""
    global TOK
    cache = os.path.join(TRAB, f"{f['sitio']}_{f['id']}.npz")
    if os.path.exists(cache):
        return dict(np.load(cache))
    tr, _ = grilla(f["sitio"])
    it = _item(f)
    if it["collection"] == "landsat-c2-l2":
        if TOK is None:
            TOK = C.pc_token()
        h = {k: it["assets"][k]["href"] + "?" + TOK for k in ("blue", "green", "red", "swir16", "qa_pixel")}
        b = {k: leer(h[k], tr, 2.75e-5, -0.2) for k in ("blue", "green", "red", "swir16")}
        qa = leer(h["qa_pixel"], tr, rs=Resampling.nearest, nodata=1)
        q = np.nan_to_num(qa, nan=1).astype(np.uint32)
        b["nube"] = ((q >> 3) & 1).astype(bool) | ((q >> 1) & 1).astype(bool)
        b["sombra"] = ((q >> 4) & 1).astype(bool)
        b["valido"] = np.isfinite(qa) & ((q & 1) == 0)
    else:
        p = it["properties"]
        suma = 0.0 if p.get("earthsearch:boa_offset_applied", False) else -0.1
        b = {k: leer(it["assets"][k]["href"], tr, 1e-4, suma) for k in ("blue", "green", "red", "swir16")}
        scl = leer(it["assets"]["scl"]["href"], tr, rs=Resampling.nearest, nodata=0)
        b["nube"] = np.isin(scl, [8, 9, 10])
        b["sombra"] = scl == 3
        b["valido"] = np.isfinite(scl) & (scl > 0)
    np.savez_compressed(cache, **b)
    return b


def clases(b):
    with np.errstate(invalid="ignore", divide="ignore"):
        nd = (b["green"] - b["swir16"]) / (b["green"] + b["swir16"])
        dato = b["valido"] & np.isfinite(nd) & np.isfinite(b["green"])
        nube = dato & b["nube"]
        claro = dato & ~b["nube"]
        nieve = claro & (nd > NDSI_NIEVE) & (b["green"] > VERDE_NIEVE)
        limpia = nieve & (b["green"] > VERDE_LIMPIA)
        sucia = nieve & ~limpia
        suelo = claro & (nd < NDSI_SUELO)
    return dato, nube, claro, nieve, limpia, sucia, suelo, nd


def medir_uno(f):
    try:
        b = bandas(f)
    except Exception as e:  # noqa: BLE001
        return {**f, "error": repr(e)[:200]}
    _, dist = grilla(f["sitio"])
    z = dist <= R_ZONA
    dato, nube, claro, nieve, limpia, sucia, suelo, nd = clases(b)
    nz, nc = int((z & dato).sum()), int((z & claro).sum())
    out = {**f, "pix_zona": int(z.sum()), "dato_zona": nz, "nube_zona": _fr((z & nube).sum(), nz),
           "claro_zona": nc}
    for k, m in (("nieve", nieve), ("nieve_limpia", limpia), ("nieve_sucia", sucia), ("suelo", suelo)):
        out[k] = _fr((z & m).sum(), nc)
    out["verde_nieve_mediana"] = _r(np.nanmedian(b["green"][z & nieve])) if (z & nieve).any() else None
    # anillo de 4 a 5 km: ¿hay nube alrededor aunque no sobre la cumbre?
    a = (dist > R_ZONA) & (dist <= 5.0)
    out["nube_4a5km"] = _fr((a & nube).sum(), (a & dato).sum())
    return out


def _fr(a, b):
    return round(float(a) / float(b), 4) if b else None


def _r(x):
    return None if x is None or not np.isfinite(x) else round(float(x), 4)


def medir():
    filas = json.load(open(os.path.join(TRAB, "escenas.json")))
    t = time.time()
    with ThreadPoolExecutor(6) as ex:
        out = list(ex.map(medir_uno, filas))
    for o in out:
        o["dia"] = o["datetime"][:10]
        o["hora"] = o["datetime"][11:16]
    out.sort(key=lambda o: (o["sitio"], o["datetime"]))
    os.makedirs(RES, exist_ok=True)
    campos = ["sitio", "año", "dia", "hora", "plataforma", "id", "nube_escena", "dato_zona", "nube_zona", "claro_zona",
              "nieve", "nieve_limpia", "nieve_sucia", "suelo", "verde_nieve_mediana", "nube_4a5km", "error"]
    with open(os.path.join(RES, "s29a_optico_escenas.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} escenas, {sum('error' in o for o in out)} con error, {time.time() - t:.0f} s")


def figura(sitio, iid, nombre):
    """Color verdadero (izquierda) y SWIR1-verde-rojo (derecha, nieve celeste, nube blanca) con el círculo de 4 km."""
    from PIL import Image, ImageDraw
    b = dict(np.load(os.path.join(TRAB, f"{sitio}_{iid}.npz")))

    def st(x, hi):
        return (np.clip(np.nan_to_num(x) / hi, 0, 1) * 255).astype("uint8")
    tc = np.dstack([st(b["red"], 1.0), st(b["green"], 1.0), st(b["blue"], 1.0)])
    fc = np.dstack([st(b["swir16"], 0.6), st(b["green"], 1.0), st(b["red"], 1.0)])
    im = Image.fromarray(np.hstack([tc, np.full((N, 6, 3), 255, "uint8"), fc]))
    d = ImageDraw.Draw(im)
    r = R_ZONA * 1000 / RES_M
    for x0 in (0, N + 6):
        d.ellipse([x0 + N / 2 - r, N / 2 - r, x0 + N / 2 + r, N / 2 + r], outline=(255, 0, 255), width=2)
    im.save(nombre)


if __name__ == "__main__":
    {"buscar": buscar, "medir": medir}[sys.argv[1]]()
