r"""H23 (enmienda post hoc 1): baja la mascara de cielo despejado de NOAA (ABI-L2-ACMF de GOES-19, bucket publico
noaa-goes19) en la ventana del detector, para los dias de prueba. Es la misma grilla fija de 2 km de la L1b.

Por que: la poblacion "entorno despejado" del criterio se definia solo contra la linea base propia, y la primera
corrida mostro (comprobacion I5) que esa linea base estaba contaminada por nubes. La mascara de NOAA es un
producto externo e independiente de nuestra linea base; se usa solo en los pixeles del entorno, no en el pixel
donde se inyecta.

Guarda en H23_DIR\acm\<cuadro>.npz: acm (0 despejado, 1 probablemente despejado, 2 probablemente nublado,
3 nublado, 255 sin dato) y dqf. Reanudable. Uso: python -I h23_bajar_acm.py [nproc] [oct|nov|todo] [rev]
"""
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h23_comun as K  # noqa: E402

ACM = os.path.join(K.H23, "acm")
TRAMOS = {"oct": K.BLOQUE_OCT, "nov": K.BLOQUE_NOV}       # enmienda 1 (E3): todos los dias de cada bloque
_fs = None


def fs():
    global _fs
    if _fs is None:
        import s3fs
        _fs = s3fs.S3FileSystem(anon=True)
    return _fs


def hora(h):
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
            p = f"noaa-goes19/ABI-L2-ACMF/{h:%Y}/{h.timetuple().tm_yday:03d}/{h:%H}/"
            try:
                lst = fs().ls(p)
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
                with fs().open(kk[0], "rb", block_size=2**18, cache_type="readahead") as fo, h5py.File(fo, "r") as f:
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
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    cual = sys.argv[2] if len(sys.argv) > 2 else "todo"
    os.makedirs(ACM, exist_ok=True)
    horas = []
    for c in (["oct", "nov"] if cual == "todo" else [cual]):
        a, b = TRAMOS[c]
        horas += [a + timedelta(hours=i) for i in range(((b - a).days + 1) * 24)]
    if len(sys.argv) > 3 and sys.argv[3] == "rev":
        horas = horas[::-1]
    print("horas", len(horas), flush=True)
    t0 = time.time()
    tot, sin = 0, []
    with ProcessPoolExecutor(n) as ex:
        fut = [ex.submit(hora, h) for h in horas]
        for i, f in enumerate(as_completed(fut), 1):
            try:
                h, hechos, faltas = f.result()
            except Exception as e:  # noqa: BLE001   (cruce con otra corrida: se reintenta en la proxima)
                print("EXCEPCION", repr(e)[:120], flush=True)
                continue
            tot += hechos
            sin += faltas
            if i % 50 == 0:
                print(f"{i}/{len(horas)} horas, {tot} cuadros, {len(sin)} sin dato, {time.time() - t0:.0f}s", flush=True)
    print("FIN", tot, "cuadros;", len(sin), "sin dato;", f"{time.time() - t0:.0f}s", flush=True)
    for c, b in sorted(sin):
        print("sin_dato", c, b)
