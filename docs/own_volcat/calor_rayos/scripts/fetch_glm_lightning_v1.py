"""H9: rayos GLM cerca de Chillan desde la SALIDA PUBLICADA de Lightning-v1 (repo publico MendozaVolcanic/Lightning-v1).

Lightning-v1 escribe cada ~5 min `docs/data/glm_latest.json` con los destellos GLM-L2-LCFA de los ultimos 15 min a
<= 100 km de cada volcan, y lo commitea. La historia del archivo en git es la serie publicada. Aqui se baja cada
version (raw.githubusercontent.com/<sha>/...) del 19-10 22:00 UTC al 19-11 13:00 UTC y se guarda, por version,
el encabezado (scan_utc, ventana, error) y la entrada de "Nevados de Chillan" completa (posiciones incluidas).
No lee el data/ local de otro proyecto. Reanudable: una linea JSON por sha en glm_versiones.jsonl.
Uso: python fetch_glm_lightning_v1.py
"""
import os, json, subprocess, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

SCR = r"C:\Users\nmend\AppData\Local\Temp\claude\11c46882e3e16008\ea70ca80-5f81-4c66-8568-aa962b07902e\scratchpad\glm"
os.makedirs(SCR, exist_ok=True)
SHAS = os.path.join(SCR, "commits.json")
OUT = os.path.join(SCR, "glm_versiones.jsonl")
REPO = "MendozaVolcanic/Lightning-v1"
PATH = "docs/data/glm_latest.json"


def commits():
    if os.path.exists(SHAS):
        return json.load(open(SHAS))
    cmd = ["gh", "api", "--paginate",
           f"repos/{REPO}/commits?path={PATH}&since=2026-10-19T22:00:00Z&until=2026-11-19T13:00:00Z&per_page=100",
           "--jq", ".[] | [.sha, .commit.author.date] | @tsv"]
    txt = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    out = [l.split("\t") for l in txt.strip().splitlines()]
    json.dump(out, open(SHAS, "w"))
    return out


def uno(sha, fecha, ses):
    url = f"https://raw.githubusercontent.com/{REPO}/{sha}/{PATH}"
    for i in range(5):
        try:
            r = ses.get(url, timeout=30)
            if r.status_code == 200:
                d = r.json()
                chi = [v for v in d.get("volcanoes", []) if "Chill" in v.get("volcano", "")]
                return dict(sha=sha, commit=fecha, scan_utc=d.get("scan_utc"), window=d.get("window_minutes"),
                            error=d.get("error"), source=d.get("source"), chillan=chi[0] if chi else None)
            if r.status_code == 404:
                return dict(sha=sha, commit=fecha, http=404)
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2 * (i + 1))
    return None


def main():
    cs = commits()
    hechos = set()
    if os.path.exists(OUT):
        for l in open(OUT, encoding="utf-8"):
            try:
                hechos.add(json.loads(l)["sha"])
            except Exception:  # noqa: BLE001
                pass
    falta = [(s, f) for s, f in cs if s not in hechos]
    print("versiones", len(cs), "faltan", len(falta), flush=True)
    ses = requests.Session(); ses.headers["User-Agent"] = "goes-h9-analisis"
    n = 0; t0 = time.time()
    with open(OUT, "a", encoding="utf-8") as fo, ThreadPoolExecutor(12) as ex:
        futs = [ex.submit(uno, s, f, ses) for s, f in falta]
        for fu in as_completed(futs):
            r = fu.result(); n += 1
            if r is not None:
                fo.write(json.dumps(r) + "\n"); fo.flush()
            if n % 500 == 0:
                print(n, f"{time.time()-t0:.0f}s", flush=True)
    print("listo", n, flush=True)


if __name__ == "__main__":
    main()
