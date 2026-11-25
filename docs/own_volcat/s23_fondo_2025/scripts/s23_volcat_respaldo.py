r"""S23: respalda en D: todos los PNG Ash_Height de VOLCAT (Chile_Central_2_km, GOES-19) que SSEC todavía publica y
que no están ya guardados en alguna de las carpetas de respaldo anteriores. Pedido por Nicolás el 24-11-2026.

Por qué: SSEC guarda unos 30 días y borra un día por día. La meta del detector propio es llegar a lo que VOLCAT mostró
de Chillán en oct-nov 2026; lo que no se guarda ahora no se puede volver a mirar.
Mismas funciones del dashboard que s22b_volcat_bajar.py (src.fetch.volcat_api, sólo lectura). Guarda también el
listado de SSEC con la hora en que se pidió.

Destino D:\goes_notas\s23\volcat_png\Chile_Central_2_km\frames (licencia SSEC: nunca al repo ni al Space).
Uso: python -I s23_volcat_respaldo.py
"""
import json
import os
import shutil
import sys
from datetime import datetime, timezone

import requests

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, RAIZ)
from src.fetch.volcat_api import _frame_meta, _query_frames_estado  # noqa: E402

SECTOR = "Chile_Central_2_km"
DEST = r"D:\goes_notas\s23\volcat_png\Chile_Central_2_km\frames"
YA = [r"D:\goes_notas\s22\volcat_png\Chile_Central_2_km\frames", r"D:\goes_notas\s22\s22b\volcat_png\frames",
      r"D:\goes_notas\volcat_validacion_copia_2026-11-21\Chile_Central_2_km\frames"]

if __name__ == "__main__":
    os.makedirs(DEST, exist_ok=True)
    frames, coords, err = _query_frames_estado(SECTOR, "ABI", "Ash_Height", "GOES-19")
    if err:
        print("error de listado:", err)
        sys.exit(1)
    ahora = datetime.now(timezone.utc)
    json.dump({"pedido_utc": f"{ahora:%Y-%m-%dT%H:%M:%SZ}", "frames": frames},
              open(os.path.join(os.path.dirname(DEST), f"listado_{ahora:%Y%m%d_%H%M}.json"), "w"), indent=0)
    ya = set()
    for d in YA:
        if os.path.isdir(d):
            ya |= {f for f in os.listdir(d) if f.endswith(".png")}
    print("listados", len(frames), "de", frames[0]["datetime"], "a", frames[-1]["datetime"], "; ya guardados antes",
          sum(f"{f['datetime']}.png" in ya for f in frames), flush=True)
    n, fallas = 0, 0
    for i, f in enumerate(frames):
        nombre = f"{f['datetime']}.png"
        out = os.path.join(DEST, nombre)
        if nombre in ya or os.path.exists(out):
            continue
        if shutil.disk_usage(DEST).free < 6 * 2**30:
            print("CORTE: D: bajo 6 GB libres")
            break
        url = _frame_meta(f, SECTOR, "ABI", "Ash_Height", coords)["image_url"]
        try:
            r = requests.get(url, timeout=60)
        except requests.RequestException as e:
            print("falla", f["datetime"], repr(e)[:80])
            fallas += 1
            continue
        if r.status_code == 200 and r.content:
            tmp = out + ".tmp"
            open(tmp, "wb").write(r.content)
            os.replace(tmp, out)
            n += 1
            if n % 200 == 0:
                print(n, "bajados, va en", f["datetime"], flush=True)
        else:
            print("falla", f["datetime"], r.status_code)
            fallas += 1
    print("FIN bajados", n, "fallas", fallas, flush=True)
