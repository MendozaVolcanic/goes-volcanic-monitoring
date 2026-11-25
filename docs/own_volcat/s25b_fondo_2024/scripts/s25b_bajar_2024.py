r"""S25b: baja C14, C15 y la máscara de nubes ACMF de GOES-16 (NOAA S3, bucket noaa-goes16, sin credenciales) en la
ventana del detector, del 21-09-2024 al 21-11-2024: un segundo fondo sin pluma, fuera de la muestra de 2025.

Por qué: la referencia del detector (línea base por píxel y umbral) sale de oct-nov 2025 (S23). Falta saber si un umbral
calibrado en un solo año aguanta otro año. En 2024 Chillán estaba en alerta técnica verde (REAV del 15-11-2024, un sismo
VT de ML 3,0 sin actividad superficial; sin actividad superficial desde oct-2022 según SERNAGEOMIN). GOES-East era
entonces GOES-16, en la misma posición (75,2° O) y con la misma grilla fija ABI que GOES-19 desde abril de 2025.

Variante de h23_bajar.py y h23_bajar_acm.py, que tienen el bucket noaa-goes19 escrito adentro. No se tocan: aquí se
reemplaza el listado (L1b) y se repite la lectura del ACMF con el bucket de GOES-16. Mismo método, misma ventana
(h23_comun.WIN), mismos coeficientes de Planck leídos de cada NetCDF (los de GOES-16, no los de GOES-19).
Escrituras atómicas (temporal por proceso + os.replace): dos corridas pueden cruzarse sin dañarse.
Todo va a D:\goes_notas\s25\s25b_2024. Corta solo si D: baja de 6 GB libres.
Uso: python -I s25b_bajar_2024.py l1b|acm [nproc] [rev]
"""
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta

import numpy as np

os.environ["H23_DIR"] = r"D:\goes_notas\s25\s25b_2024"
AQUI = os.path.dirname(os.path.abspath(__file__))
H23S = os.path.abspath(os.path.join(AQUI, "..", "..", "h23_inyeccion", "scripts"))
sys.path.insert(0, H23S)
import h23_comun as K  # noqa: E402
import h23_bajar as BL  # noqa: E402

BUCKET = "noaa-goes16"
INICIO, FIN = datetime(2024, 9, 21), datetime(2024, 11, 21, 23)
ACM = os.path.join(K.H23, "acm")


def listar16(h):
    p = f"{BUCKET}/ABI-L1b-RadF/{h:%Y}/{h.timetuple().tm_yday:03d}/{h:%H}/"
    for i in range(4):
        try:
            return BL.fs().ls(p)
        except FileNotFoundError:
            return []
        except Exception:  # noqa: BLE001
            time.sleep(2 * (i + 1))
    return []


BL.listar = listar16          # h23_bajar.hora busca `listar` en su módulo: así lista GOES-16 (también en los hijos)


def hora_l1b(h):
    BL.listar = listar16
    return BL.hora(h)


def hora_acm(h):
    """Copia de h23_bajar_acm.hora con el bucket de GOES-16."""
    import h5py
    if shutil.disk_usage(K.H23).free < 6 * 2**30:
        return h, 0, [("DISCO", "")]
    W = K.WIN
    lst, hechos, faltas = None, 0, []
    for m in range(0, 60, 10):
        dt = h + timedelta(minutes=m)
        out = os.path.join(ACM, K.clave(dt) + ".npz")
        if os.path.exists(out):
            hechos += 1
            continue
        if lst is None:
            p = f"{BUCKET}/ABI-L2-ACMF/{h:%Y}/{h.timetuple().tm_yday:03d}/{h:%H}/"
            try:
                lst = BL.fs().ls(p)
            except Exception:  # noqa: BLE001
                lst = []
        tag = f"_s{dt:%Y}{dt.timetuple().tm_yday:03d}{dt:%H%M}"
        kk = [x for x in lst if tag in x]
        if not kk:
            faltas.append((K.clave(dt), "sin archivo"))
            continue
        err = None
        for i in range(4):
            try:
                with BL.fs().open(kk[0], "rb", block_size=2**18, cache_type="readahead") as fo, \
                        h5py.File(fo, "r") as f:
                    acm = f["ACM"][W["y0"]:W["y1"], W["x0"]:W["x1"]]
                    dqf = f["DQF"][W["y0"]:W["y1"], W["x0"]:W["x1"]]
                tmp = out + f".{os.getpid()}.tmp.npz"
                np.savez_compressed(tmp, acm=acm, dqf=dqf, key=np.array(kk[0].split("/")[-1]))
                os.replace(tmp, out)
                hechos += 1
                err = None
                break
            except Exception as e:  # noqa: BLE001
                err = e
                time.sleep(2 * (i + 1))
        if err is not None:
            faltas.append((K.clave(dt), repr(err)[:80]))
    return h, hechos, faltas


if __name__ == "__main__":
    cual = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    assert K.H23 == r"D:\goes_notas\s25\s25b_2024", K.H23
    os.makedirs(K.L1B if cual == "l1b" else ACM, exist_ok=True)
    f = hora_l1b if cual == "l1b" else hora_acm
    horas, h = [], INICIO
    while h <= FIN:
        horas.append(h)
        h += timedelta(hours=1)
    if len(sys.argv) > 3 and sys.argv[3] == "rev":
        horas = horas[::-1]
    print(cual, BUCKET, "horas", len(horas), "->", K.H23, flush=True)
    t0, tot, sin = time.time(), 0, []
    with ProcessPoolExecutor(n) as ex:
        fut = [ex.submit(f, h) for h in horas]
        for i, fu in enumerate(as_completed(fut), 1):
            try:
                _, hechos, faltas = fu.result()
            except Exception as e:  # noqa: BLE001
                print("EXCEPCION", repr(e)[:120], flush=True)
                continue
            tot += hechos
            sin += faltas
            if i % 24 == 0:
                print(f"{i}/{len(horas)} horas, {tot} cuadros, {len(sin)} sin dato, {time.time() - t0:.0f}s", flush=True)
    print("FIN", tot, "cuadros;", len(sin), "sin dato;", f"{time.time() - t0:.0f}s", flush=True)
    for c, b in sorted(sin)[:300]:
        print("sin_dato", c, b)
