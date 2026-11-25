r"""S25b: vigía de la bajada. Lanza s25b_bajar_2024.py <cual> y, si el conteo de archivos de esa carpeta no cambia en
ESTANCADO segundos, mata el árbol de procesos (taskkill /T) y relanza; las escrituras son atómicas, así que no se daña nada.

Por qué: la primera corrida del ACMF (25-11-2026) se colgó 3 h 45 min en una lectura de S3 sin timeout, y el vigía de
entonces sumaba L1B y ACMF, así que no lo vio. Uso: python -I s25b_vigia.py l1b|acm nproc [max_relanzadas]
"""
import os
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = r"D:\goes_notas\s25\s25b_2024"
ESTANCADO, PASO = 600, 60


def contar(cual):
    return sum(1 for f in os.listdir(os.path.join(DATOS, cual)) if f.endswith(".npz") and ".tmp." not in f)


if __name__ == "__main__":
    cual, n = sys.argv[1], sys.argv[2]
    maxr = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    for vez in range(maxr):
        log = open(os.path.join(DATOS, f"bajar_{cual}_vigia{vez}.log"), "w", encoding="utf-8")
        p = subprocess.Popen([sys.executable, "-I", os.path.join(AQUI, "s25b_bajar_2024.py"), cual, n],
                             stdout=log, stderr=subprocess.STDOUT)
        ult, t_ult = contar(cual), time.time()
        while p.poll() is None:
            time.sleep(PASO)
            c = contar(cual)
            if c != ult:
                ult, t_ult = c, time.time()
            elif time.time() - t_ult > ESTANCADO:
                print(f"vez {vez}: estancado en {c} por {ESTANCADO} s, relanzo", flush=True)
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
                p.wait()
                break
        log.close()
        if p.returncode == 0:
            print(f"vez {vez}: FIN con {contar(cual)} archivos", flush=True)
            break
    for f in os.listdir(os.path.join(DATOS, cual)):
        if ".tmp." in f:
            os.remove(os.path.join(DATOS, cual, f))
