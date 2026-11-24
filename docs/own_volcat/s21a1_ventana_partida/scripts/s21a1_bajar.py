r"""S21a1: baja capas de HLS L30 v2.0 (tesela T19HBV) de LP DAAC a D:\goes_notas\s21\a1\hls\<granulo>\.

Token de Earthdata leido de C:\Users\nmend\.earthdata_token (nunca se imprime; el _netrc esta vencido y no se usa).
Corta al primer error. No sobreescribe lo que ya esta.

Uso: python -I s21a1_bajar.py <granulo> <capa> [<capa> ...]
     ej. python -I s21a1_bajar.py HLS.L30.T19HBV.2026258T143426.v2.0 Fmask
"""
import os
import sys

import requests

BASE = "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/HLSL30.020"
DEST = r"D:\goes_notas\s21\a1\hls"
TOKEN = os.path.expanduser(r"~\.earthdata_token")


def bajar(gran, capa, ses):
    os.makedirs(os.path.join(DEST, gran), exist_ok=True)
    f = os.path.join(DEST, gran, f"{gran}.{capa}.tif")
    if os.path.exists(f) and os.path.getsize(f) > 0:
        print("ya esta", os.path.basename(f), os.path.getsize(f), flush=True)
        return
    r = ses.get(f"{BASE}/{gran}/{gran}.{capa}.tif", timeout=300, stream=True)
    if r.status_code != 200:
        raise SystemExit(f"error HTTP {r.status_code} en {gran}.{capa}; se corta")
    tmp = f + ".parcial"
    with open(tmp, "wb") as fh:
        for b in r.iter_content(1 << 20):
            fh.write(b)
    os.replace(tmp, f)
    print("bajado", os.path.basename(f), os.path.getsize(f), flush=True)


def main():
    gran, capas = sys.argv[1], sys.argv[2:]
    with open(TOKEN, encoding="utf-8") as fh:
        tok = fh.read().strip()
    ses = requests.Session()
    ses.headers["Authorization"] = f"Bearer {tok}"
    for c in capas:
        bajar(gran, c, ses)


if __name__ == "__main__":
    main()
