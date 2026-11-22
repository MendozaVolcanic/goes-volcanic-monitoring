"""H19: inventario de variables de un HDF4 (nombre, forma, tipo, atributos, rango).
Uso: python -I h19_inventario.py archivo.hdf [archivo2.hdf ...]
Solo lee. No ejecuta nada del paquete de SSEC."""
import sys
import numpy as np
from pyhdf.SD import SD, SDC

for path in sys.argv[1:]:
    sd = SD(path, SDC.READ)
    print("=====", path.replace("\\", "/").split("/")[-1])
    for k, v in sd.attributes().items():
        print("  ATTR", k, str(v)[:300])
    for name, info in sorted(sd.datasets().items(), key=lambda kv: kv[1][3]):
        dims, shape, typ, idx = info
        ds = sd.select(name)
        at = ds.attributes()
        extra = ""
        try:
            n = int(np.prod(shape)) if shape else 1
            if 0 < n <= 4_000_000:
                a = np.asarray(ds.get())
                if a.dtype.kind in "fiu":
                    fill = at.get("_FillValue", None)
                    m = np.ones(a.shape, bool) if fill is None else (a != fill)
                    if a.dtype.kind == "f":
                        m &= np.isfinite(a) & (a > -900)
                    if m.any():
                        extra = " validos=%d min=%.5g max=%.5g" % (m.sum(), a[m].min(), a[m].max())
                    else:
                        extra = " validos=0"
                else:
                    extra = " txt=" + repr(a.tobytes()[:80])
        except Exception as e:  # noqa
            extra = " (no leido: %s)" % e
        ats = {k: (str(v)[:80]) for k, v in at.items()
               if k in ("long_name", "units", "scale_factor", "add_offset", "_FillValue", "description")}
        print("  %-70s %s t=%s%s %s" % (name, shape, typ, extra, ats if ats else ""))
    sd.end()
