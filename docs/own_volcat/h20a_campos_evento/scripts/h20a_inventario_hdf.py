"""H20a: inventario de nombres, formas y atributos de los HDF4 de referencia (sin valores de pixel).
Uso: venv_hdf4 python -I h20a_inventario_hdf.py SALIDA.txt ARCHIVO.hdf [...]
"""
import sys
from pyhdf.SD import SD, SDC

if __name__ == "__main__":
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        for p in sys.argv[2:]:
            sd = SD(p, SDC.READ)
            f.write("#### ARCHIVO %s\n" % p.replace("\\", "/").split("/")[-1])
            for k, v in sd.attributes().items():
                f.write("  GLOBAL %s = %s\n" % (k, str(v)[:200]))
            for n, info in sorted(sd.datasets().items()):
                at = sd.select(n).attributes()
                resto = "; ".join("%s=%s" % (a, str(b)[:160]) for a, b in at.items())
                f.write("%s | %s | %s\n" % (n, info[1], resto))
            sd.end()
