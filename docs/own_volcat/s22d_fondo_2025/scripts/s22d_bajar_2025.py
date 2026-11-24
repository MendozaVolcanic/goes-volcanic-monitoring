r"""S22d: baja C14, C15 y la máscara de nubes ACMF de GOES-19 (NOAA S3, sin credenciales) en la ventana del detector,
del 21-09-2025 al 21-11-2025: el fondo SIN PLUMA de la misma estación.

Por qué: Nicolás (24-11-2026) confirmó que Nevados de Chillán tiene pluma todos los días desde la erupción de julio de
2026 (ceniza de 1 a 2 km sobre el cráter desde septiembre) y que octubre y noviembre de 2025 estuvieron tranquilos.
Todo control "sin actividad" de sep-nov 2026 tenía pluma. Este fondo reemplaza esos controles con el mismo sol, la
misma nieve y la misma geometría (GOES-19 ya en 75,2° O desde abril de 2025, misma grilla fija ABI).

Reutiliza sin cambios h23_bajar.hora y h23_bajar_acm.hora (misma ventana, mismo método que los cubos de 2026).
Todo va a H23_DIR = D:\goes_notas\s22\s22d_2025. Corta solo si D: baja de 6 GB libres.
Uso: python -I s22d_bajar_2025.py l1b|acm [nproc]
"""
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta

os.environ["H23_DIR"] = r"D:\goes_notas\s22\s22d_2025"
AQUI = os.path.dirname(os.path.abspath(__file__))
H23S = os.path.abspath(os.path.join(AQUI, "..", "..", "h23_inyeccion", "scripts"))
sys.path.insert(0, H23S)
import h23_comun as K  # noqa: E402

INICIO, FIN = datetime(2025, 9, 21), datetime(2025, 11, 21, 23)

if __name__ == "__main__":
    cual = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    if cual == "l1b":
        import h23_bajar as B
        os.makedirs(K.L1B, exist_ok=True)
    else:
        import h23_bajar_acm as B
        os.makedirs(B.ACM, exist_ok=True)
    assert K.H23 == r"D:\goes_notas\s22\s22d_2025", K.H23
    horas, h = [], INICIO
    while h <= FIN:
        horas.append(h)
        h += timedelta(hours=1)
    print(cual, "horas", len(horas), "->", K.H23, flush=True)
    t0, tot, sin = time.time(), 0, []
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
            if i % 24 == 0:
                print(f"{i}/{len(horas)} horas, {tot} cuadros, {len(sin)} sin dato, {time.time() - t0:.0f}s", flush=True)
    print("FIN", tot, "cuadros;", len(sin), "sin dato;", f"{time.time() - t0:.0f}s", flush=True)
    for c, b in sorted(sin)[:200]:
        print("sin_dato", c, b)
