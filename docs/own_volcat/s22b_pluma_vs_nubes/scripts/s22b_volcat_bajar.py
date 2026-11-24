r"""S22b: guarda en D: los PNG Ash_Height de VOLCAT (Chile_Central_2_km, GOES-19) que faltan desde el último cuadro
guardado (24-11 11:40 UTC) hasta el último publicado, con las mismas funciones del dashboard que usa
scripts/harvest_volcat_validacion.py (src.fetch.volcat_api, sólo lectura). SSEC guarda unos 30 días: lo que no se
guarda se pierde.

Destino D:\goes_notas\s22\s22b\volcat_png\frames (licencia SSEC: nunca al repo ni al Space). Sólo baja; no clasifica.
Uso: python -I s22b_volcat_bajar.py AAAA-MM-DDTHH:MM
"""
import os
import sys
from datetime import datetime, timezone

import requests

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, RAIZ)
from src.fetch.volcat_api import _frame_meta, _query_frames_estado  # noqa: E402

DEST = r"D:\goes_notas\s22\s22b\volcat_png\frames"
FMT = "%Y-%m-%d_%H-%M-%S"

if __name__ == "__main__":
    desde = datetime.strptime(sys.argv[1], "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
    frames, coords, err = _query_frames_estado("Chile_Central_2_km", "ABI", "Ash_Height", "GOES-19")
    if err:
        print("error de listado:", err)
    os.makedirs(DEST, exist_ok=True)
    n = 0
    for f in frames or []:
        t = datetime.strptime(f["datetime"], FMT).replace(tzinfo=timezone.utc)
        if t < desde:
            continue
        out = os.path.join(DEST, f"{f['datetime']}.png")
        if os.path.exists(out):
            continue
        url = _frame_meta(f, "Chile_Central_2_km", "ABI", "Ash_Height", coords)["image_url"]
        r = requests.get(url, timeout=60)
        if r.status_code == 200 and r.content:
            open(out, "wb").write(r.content)
            n += 1
        else:
            print("falla", f["datetime"], r.status_code)
    print("bajados", n, "ultimo listado", frames[-1]["datetime"] if frames else None)
