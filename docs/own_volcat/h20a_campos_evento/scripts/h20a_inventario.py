"""H20a: inventario de variables y atributos de los NetCDF de evento VOLCAT (sin valores de pixel).
Permitido antes del criterio: solo nombres, dimensiones, tipos y atributos.
Uso: python -I h20a_inventario.py SALIDA.txt ARCHIVO.nc [ARCHIVO2.nc ...]
"""
import sys
import netCDF4 as nc


def inventario(path, f):
    ds = nc.Dataset(path)
    f.write("#### ARCHIVO %s\n" % path.replace("\\", "/").split("/")[-1])
    f.write("## atributos globales\n")
    for k in ds.ncattrs():
        f.write("  %s = %r\n" % (k, str(ds.getncattr(k))[:300]))
    f.write("## dimensiones\n")
    for k, d in ds.dimensions.items():
        f.write("  %s = %d\n" % (k, len(d)))
    f.write("## grupos: %s\n" % list(ds.groups.keys()))
    f.write("## variables: %d\n" % len(ds.variables))
    for k, v in ds.variables.items():
        at = {a: v.getncattr(a) for a in v.ncattrs()}
        ln = at.pop("long_name", "")
        un = at.pop("units", "")
        resto = "; ".join("%s=%s" % (a, str(b)[:120]) for a, b in at.items())
        f.write("%s | %s | %s | long_name=%s | units=%s | %s\n" % (k, v.dtype, ",".join(v.dimensions), ln, un, resto))
    ds.close()


if __name__ == "__main__":
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        for p in sys.argv[2:]:
            inventario(p, f)
