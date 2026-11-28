r"""S31j: baja C07 y C14 de NOAA S3 (GOES-19, sin credenciales) sólo en la ventana de Nevados de Chillán, cada 30 min
de noche, para la compuerta de calor del espejo (indicador VRP nocturno validado, docs/own_volcat/vrp_nocturno).

Usa vn_bajar.tarea y vn_comun sin cambios; sólo cambia la carpeta de salida (VN_DIR) y la lista de noches:
2025: 30-08 a 21-11 (la compuerta mira 15 días atrás desde el 21-09 y la visibilidad 7 noches más).
2026: 28-09 a 24-11 (las clases de VOLCAT empiezan el 20-10; mismo margen). Ningún día posterior al 24-11-2026.
Descarga sola: no calcula VRP ni mira nada (eso lo hace s31j_medir.py después del criterio).
Uso: python -I -B s31j_bajar_calor.py [nproc]
"""
import os
import sys
import time
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed

os.environ["VN_DIR"] = r"D:\goes_notas\s31\s31j\calor"
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "vrp_nocturno", "scripts"))
import vn_bajar as VB  # noqa: E402
K = VB.K
J0 = VB.SITIOS.index("Nevados de Chillan")
TRAMOS = [(datetime(2025, 8, 30), datetime(2025, 11, 21)), (datetime(2026, 9, 28), datetime(2026, 11, 24))]


def lista():
    T = []
    for d0, d1 in TRAMOS:
        for d in VB.noches(d0, d1):
            for t in VB.cuadros_noche(d):
                T.append(f"{t:%Y%m%d_%H%M}")
    return sorted(set(T))


if __name__ == "__main__":
    assert K.OUT == r"D:\goes_notas\s31\s31j\calor", K.OUT
    os.makedirs(K.L1B, exist_ok=True)
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    T = lista()
    assert max(T) <= "20261124_1030"
    print("cuadros", len(T), flush=True)
    t0 = time.time()
    hechas = 0
    with ProcessPoolExecutor(n) as ex:
        fut = [ex.submit(VB.tarea, c, [J0]) for c in T]
        for f in as_completed(fut):
            c, falta, s = f.result()
            hechas += 1
            if falta:
                print("falta", c, falta, flush=True)
            if hechas % 100 == 0:
                print(f"{hechas}/{len(T)} {time.time() - t0:.0f}s", flush=True)
    print("FIN", hechas, f"{time.time() - t0:.0f}s", flush=True)
