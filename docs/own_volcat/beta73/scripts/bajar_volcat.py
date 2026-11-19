"""Paso 4: baja los PNG Ash_Height de Chile_Central_2_km de los dias no revisados. Uso: python paso4_bajar.py [contar]"""
import os, re, sys, time, shutil
from concurrent.futures import ThreadPoolExecutor
import requests

B = "https://volcano.ssec.wisc.edu/data/sector_imagery/Chile_Central_2_km/ABI/GOES-19/Ash_Height"
OUT = "C:/Users/nmend/AppData/Local/Temp/claude/f4710304fa6a9a5b/6cc950d4-5fd7-4e45-a0af-882008093b90/scratchpad/b73/png_new"
DIAS = [f"2026-10-{d:02d}" for d in range(3, 25)] + ["2026-11-18", "2026-11-19"]
S = requests.Session(); S.headers["User-Agent"] = "research-script"


def lista(d):
    for i in range(4):
        try:
            r = S.get(f"{B}/{d}/", timeout=60)
            if r.status_code == 200:
                return sorted(set(re.findall(r'href="(GOES-19\.ABI\.[^"]+\.png)"', r.text)))
        except Exception:
            pass
        time.sleep(3 * (i + 1))
    return []


def baja(args):
    d, n = args
    dst = os.path.join(OUT, n)
    if os.path.exists(dst):
        return 0
    for i in range(4):
        try:
            r = S.get(f"{B}/{d}/{n}", timeout=60)
            if r.status_code == 200 and r.content[:8] == b"\x89PNG\r\n\x1a\n":
                open(dst + ".tmp", "wb").write(r.content); os.replace(dst + ".tmp", dst)
                return len(r.content)
        except Exception:
            pass
        time.sleep(3 * (i + 1))
    print("FALLA", n, flush=True)
    return 0


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    tareas = [(d, n) for d in DIAS for n in lista(d)]
    print("cuadros listados", len(tareas), "estimado %.0f MB" % (len(tareas) * 0.49), flush=True)
    if len(sys.argv) > 1:
        sys.exit()
    if shutil.disk_usage("C:\\").free < 5e9:
        sys.exit("disco < 5 GB")
    t0 = time.time(); tot = 0
    with ThreadPoolExecutor(4) as ex:
        for k, b in enumerate(ex.map(baja, tareas), 1):
            tot += b
            if k % 100 == 0:
                print(k, "%.0f MB %.0fs" % (tot / 1e6, time.time() - t0), flush=True)
                if shutil.disk_usage("C:\\").free < 5e9:
                    sys.exit("disco < 5 GB")
    print("listo", len(tareas), "%.0f MB" % (tot / 1e6), flush=True)
