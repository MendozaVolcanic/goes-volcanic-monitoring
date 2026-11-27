r"""S31g: busca, solo por metadatos, las pasadas finas sobre el crater de Nevados de Chillan del 19 al 27-11-2026.

Por que solo metadatos: la regla de eleccion de S21a1 (criterio_2026-11-24.md §1) empieza por el catalogo (paso 0) y
sigue con la Fmask de HLS (paso 1). Mientras la pasada no este en el archivo, no hay nada que elegir ni que medir.
Fuentes: USGS LandsatLook STAC (Landsat C2 L1 y L2, la primera en publicar), Planetary Computer (Landsat C2 L2 y
Sentinel-2 L2A), Element 84 (Sentinel-2 L2A) y CMR de NASA (HLS L30 y S30). No lee ningun pixel, ningun termico, y
nada de GOES.

Uso: python -I -B s31g_catalogo.py   (escribe resultados/catalogo_<fecha UTC>.json)
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(AQUI), "resultados")
PT = {"type": "Point", "coordinates": [-71.377, -36.863]}     # crater (s20b_comun.CRATER)
RNG = "2026-11-19T00:00:00Z/2026-11-28T00:00:00Z"
BBOX_CHILE = [-80, -45, -60, -20]


def post(url, body):
    r = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=120))


def main():
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    out = {"consulta_utc": ahora, "rango": RNG, "punto": PT["coordinates"], "fuentes": {}}
    stac = {
        "USGS landsat-c2l1": ("https://landsatlook.usgs.gov/stac-server/search", "landsat-c2l1"),
        "USGS landsat-c2l2-sr": ("https://landsatlook.usgs.gov/stac-server/search", "landsat-c2l2-sr"),
        "PC landsat-c2-l2": ("https://planetarycomputer.microsoft.com/api/stac/v1/search", "landsat-c2-l2"),
        "PC sentinel-2-l2a": ("https://planetarycomputer.microsoft.com/api/stac/v1/search", "sentinel-2-l2a"),
        "E84 sentinel-2-l2a": ("https://earth-search.aws.element84.com/v1/search", "sentinel-2-l2a"),
    }
    for nom, (url, col) in stac.items():
        try:
            fs = post(url, {"collections": [col], "intersects": PT, "datetime": RNG, "limit": 50})["features"]
            out["fuentes"][nom] = sorted(([f["id"], f["properties"]["datetime"], f["properties"].get("eo:cloud_cover")]
                                          for f in fs), key=lambda x: x[1])
        except Exception as e:  # noqa: BLE001
            out["fuentes"][nom] = f"ERROR {e}"
    for sn in ("HLSL30", "HLSS30"):
        u = (f"https://cmr.earthdata.nasa.gov/search/granules.json?short_name={sn}&version=2.0"
             f"&point=-71.377,-36.863&temporal=2026-11-19T00:00:00Z,2026-11-28T00:00:00Z&page_size=50")
        try:
            es = json.load(urllib.request.urlopen(u, timeout=120))["feed"]["entry"]
            out["fuentes"][f"CMR {sn}"] = [[e["title"], e["time_start"], e.get("cloud_cover")] for e in es]
        except Exception as e:  # noqa: BLE001
            out["fuentes"][f"CMR {sn}"] = f"ERROR {e}"
    # Landsat 8 en todo Chile: si no hay ninguna escena L8 despues del 14-11, la del 26-11 falta por demora de
    # proceso de USGS, no por nube ni por la orbita
    lat = {}
    for plat in ("LANDSAT_8", "LANDSAT_9"):
        fs = post("https://landsatlook.usgs.gov/stac-server/search",
                  {"collections": ["landsat-c2l1"], "bbox": BBOX_CHILE, "datetime": "2026-11-10T00:00:00Z/2026-11-28T00:00:00Z",
                   "limit": 100, "query": {"platform": {"eq": plat}}})["features"]
        ds = sorted({f["properties"]["datetime"][:10] for f in fs})
        lat[plat] = {"escenas": len(fs), "ultima_fecha_adquirida": ds[-1] if ds else None}
    out["landsat_en_chile_desde_10_11"] = lat
    # demora de proceso de Landsat 8 en el path 233, de los ids L1 (fecha de adquisicion y fecha de proceso)
    fs = post("https://landsatlook.usgs.gov/stac-server/search",
              {"collections": ["landsat-c2l1"], "intersects": PT, "datetime": "2026-09-01T00:00:00Z/2026-11-28T00:00:00Z",
               "limit": 100})["features"]
    dem = []
    for f in fs:
        p = f["id"].split("_")
        if p[0] == "LC08" and p[2].startswith("233"):
            a, b = datetime.strptime(p[3], "%Y%m%d"), datetime.strptime(p[4], "%Y%m%d")
            dem.append([f["id"], (b - a).days])
    out["landsat8_path233_demora_proceso_dias"] = sorted(dem)
    os.makedirs(RES, exist_ok=True)
    f = os.path.join(RES, f"catalogo_{ahora[:10]}.json")
    with open(f, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
