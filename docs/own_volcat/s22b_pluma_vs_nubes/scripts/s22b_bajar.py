r"""S22b: baja C14, C15 y la máscara de nubes ACMF de GOES-19 (NOAA S3, sin credenciales) en la ventana del detector,
del 22-11-2026 00:00 UTC hasta la hora pedida, reutilizando sin cambios las funciones de H23 (h23_bajar.hora y
h23_bajar_acm.hora). Sólo cambia el tramo de días: los bloques de H23 terminan el 21-11.

Todo va a H23_DIR, que aquí se fuerza a D:\goes_notas\s22\s22b (carpeta nueva; no toca la de H23 ni la de S22a/S22c).
Los procesos hijos heredan la variable de entorno, así que escriben en la misma carpeta.
Uso: python -I s22b_bajar.py l1b|acm AAAA-MM-DDTHH [nproc]
"""
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta

os.environ["H23_DIR"] = r"D:\goes_notas\s22\s22b"
AQUI = os.path.dirname(os.path.abspath(__file__))
H23S = os.path.abspath(os.path.join(AQUI, "..", "..", "h23_inyeccion", "scripts"))
sys.path.insert(0, H23S)
import h23_comun as K  # noqa: E402

INICIO = datetime(2026, 11, 22)

if __name__ == "__main__":
    cual = sys.argv[1]
    fin = datetime.strptime(sys.argv[2], "%Y-%m-%dT%H")
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    if cual == "l1b":
        import h23_bajar as B
        os.makedirs(K.L1B, exist_ok=True)
    else:
        import h23_bajar_acm as B
        os.makedirs(B.ACM, exist_ok=True)
    assert K.H23 == r"D:\goes_notas\s22\s22b", K.H23
    horas = []
    h = INICIO
    while h <= fin:
        horas.append(h)
        h += timedelta(hours=1)
    print(cual, "horas", len(horas), "->", K.H23, flush=True)
    t0 = time.time()
    tot, sin = 0, []
    with ProcessPoolExecutor(n) as ex:
        fut = [ex.submit(B.hora, h) for h in horas]
        for i, f in enumerate(as_completed(fut), 1):
            try:
                _, hechos, faltas = f.result()
            except Exception as e:  # noqa: BLE001
                print("EXCEPCION", repr(e)[:120], flush=True)
                continue
            tot += hechos
            sin += faltas
            if i % 12 == 0:
                print(f"{i}/{len(horas)} horas, {tot} cuadros, {len(sin)} sin dato, {time.time() - t0:.0f}s", flush=True)
    print("FIN", tot, "cuadros;", len(sin), "sin dato;", f"{time.time() - t0:.0f}s", flush=True)
    for c, b in sorted(sin):
        print("sin_dato", c, b)
