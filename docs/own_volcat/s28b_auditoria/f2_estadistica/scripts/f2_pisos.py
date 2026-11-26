r"""F2 (S28b): barrido de pisos de nulos por permutación, corrimiento o remuestreo en S23 a S28a.

Por qué: un p de permutación con n réplicas no puede bajar de 1/(n+1). Si el criterio pide p <= umbral con
1/(n+1) > umbral, la condición es inalcanzable y el veredicto que depende de ella está escrito antes del dato.

Instrumento, sin leer informes: (1) busca en resultados/*.json toda clave que cuente réplicas (n_corrimientos,
replicas_validas, n_perm, n_boot, ...) y todo p que salga de un nulo empírico; (2) busca en criterio*.md los umbrales
de p ("p ... <= 0,0x"); (3) para cada par carpeta, piso = 1/(n+1) contra cada umbral del criterio.
Pregunta 1 del instrumento: si el piso de un criterio estuviera roto, ¿esto lo vería? Sí, si el json guarda n.
Control positivo: el p mínimo observado en un json no puede quedar bajo su piso (si queda, el p no es de permutación).

Uso: python -I f2_pisos.py
"""
import glob
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
OV = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
CARP = ["s23_fondo_2025", "s24_dia14_noche", "s25a_crater", "s25b_fondo_2024", "s26a_combinado",
        "s26b_noche_crater", "s27a_noche_causa", "s27b_altura_desfase", "s28a_vecinas"]
CLAVE_N = re.compile(r"(n_corrimientos|n_perm|n_permutaciones|replicas|n_boot|n_replicas|n_rep|n_nulos|corrimientos)$",
                     re.I)
CLAVE_P = re.compile(r"^p(_|$)|p_corrimiento|p_perm|p_emp", re.I)
UMB = re.compile(r"p[^\n|]{0,40}?(?:≤|<=|<)\s*0[,.](\d+)")


def recorrer(x, ruta=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from recorrer(v, f"{ruta}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from recorrer(v, f"{ruta}[{i}]")
    else:
        yield ruta, x


def main():
    out = {}
    for c in CARP:
        umbrales = set()
        for fn in glob.glob(os.path.join(OV, c, "criterio*.md")):
            for m in UMB.finditer(open(fn, encoding="utf-8").read()):
                umbrales.add(float("0." + m.group(1)))
        ns, ps = [], []
        for fn in glob.glob(os.path.join(OV, c, "resultados", "*.json")):
            try:
                J = json.load(open(fn, encoding="utf-8"))
            except Exception as e:  # noqa: BLE001
                print("no lee", fn, e)
                continue
            for ruta, v in recorrer(J):
                hoja = ruta.rsplit("/", 1)[-1].split("[")[0]
                if CLAVE_N.search(hoja) and isinstance(v, (int, float)) and not isinstance(v, bool):
                    ns.append((os.path.basename(fn), ruta, v))
                if CLAVE_P.search(hoja) and isinstance(v, (int, float)) and not isinstance(v, bool):
                    ps.append((os.path.basename(fn), ruta, v))
        filas = []
        for f, r, n in ns:
            piso = 1.0 / (n + 1)
            filas.append({"json": f, "ruta": r, "n": n, "piso": round(piso, 5),
                          "umbrales_inalcanzables": sorted(u for u in umbrales if piso > u)})
        out[c] = {"umbrales_p_en_criterio": sorted(umbrales), "conteos_de_replicas": filas,
                  "p_min_en_json": min((v for *_, v in ps), default=None), "n_p": len(ps)}
    for c, v in out.items():
        print(f"== {c}: umbrales {v['umbrales_p_en_criterio']}; p en json {v['n_p']}, mín {v['p_min_en_json']}")
        for f in v["conteos_de_replicas"]:
            marca = "  <== INALCANZABLE " + str(f["umbrales_inalcanzables"]) if f["umbrales_inalcanzables"] else ""
            print(f"   {f['json']} {f['ruta']}: n={f['n']} piso={f['piso']}{marca}")
    dest = r"D:\goes_notas\s28\s28b\f2\pisos.json"
    json.dump(out, open(dest, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("escrito", dest)


if __name__ == "__main__":
    main()
