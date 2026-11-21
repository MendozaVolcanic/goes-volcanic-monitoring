"""C2b: inventario de estructura de los archivos del caso de prueba de Mauna Loa (sin calcular nada).

Lista, para un archivo de cada tipo (geocatL1, geocatRTM, geocatL2, geocatL2S1, geocatASHOBJ, geocatDIAG,
geocatDIAGS1, geocatHOTOBJ, geocatICEOBJ y un NetCDF de evento), los atributos globales y cada SDS o variable
con forma, tipo y sus atributos. Sirve para escribir el criterio con nombres reales antes de medir, y para
responder que variables traen (probabilidad, sesgo local, emisividad, beta). Tambien busca en los atributos
cualquier mencion de licencia o condicion de uso.

Uso: python -I c2b_estructura.py <carpeta reference_data> <salida.txt>. Lee HDF4 con el python que tenga pyhdf
(venv_hdf4) y NetCDF con el que tenga netCDF4; lo que no pueda leer lo anota y sigue.
"""
import os, sys, glob, re
sys.stdout.reconfigure(encoding="utf-8")
try:
    from pyhdf.SD import SD, SDC  # venv con HDF4
except ImportError:
    SD = None

TIPOS = ["l1_data/geocatL1", "rtm_data/geocatRTM", "l2_data/geocatL2.", "l2_data/geocatL2S1", "l2_data/geocatASHOBJ",
         "diag_data/geocatDIAG.", "diag_data/geocatDIAGS1", "l2_data/geocatHOTOBJ", "l2_data/geocatICEOBJ"]
CLAVES = re.compile(r"licen|restrict|terms|condition|copyright|disclaim|approved|use ", re.I)


def corto(v, n=160):
    s = repr(v)
    return s if len(s) <= n else s[:n] + "..."


def hdf(path, w):
    sd = SD(path, SDC.READ)
    w(f"\n######## {os.path.basename(path)}")
    for k, v in sd.attributes().items():
        w(f"  @{k} = {corto(v, 300)}")
    for name, (dims, shape, typ, idx) in sorted(sd.datasets().items(), key=lambda x: x[1][-1]):
        ds = sd.select(name)
        at = ds.attributes()
        w(f"  {name} {ds.info()[2]} tipo={typ} | " + "; ".join(f"{k}={corto(v, 80)}" for k, v in at.items()))
    sd.end()


def nc(path, w):
    try:
        import netCDF4
    except ImportError:
        w(f"(sin netCDF4: no se lee {os.path.basename(path)})"); return
    d = netCDF4.Dataset(path)
    w(f"\n######## {os.path.basename(path)}")
    for k in d.ncattrs():
        w(f"  @{k} = {corto(d.getncattr(k), 300)}")
    def grupo(g, pre=""):
        for n, v in g.variables.items():
            w(f"  {pre}{n} {v.shape} {v.dtype} | " + "; ".join(f"{k}={corto(v.getncattr(k), 80)}" for k in v.ncattrs()))
        for gn, gg in g.groups.items():
            grupo(gg, pre + gn + "/")
    grupo(d); d.close()


def main(ref, out):
    lineas = []
    w = lineas.append
    for t in TIPOS:
        fs = sorted(glob.glob(os.path.join(ref, t + "*.hdf")))
        if not fs:
            w(f"\n(no hay {t})"); continue
        w(f"\n==== {t}: {len(fs)} archivos")
        if SD is None:
            w("(sin pyhdf: no se lee HDF4)"); continue
        hdf(fs[0], w)
    for f in sorted(glob.glob(os.path.join(ref, "events", "*.nc")))[:1] + sorted(glob.glob(os.path.join(ref, "events", "*vid*.nc")))[:1]:
        nc(f, w)
    lic = [l for l in lineas if CLAVES.search(l)]
    w("\n==== lineas con posibles condiciones de uso")
    lineas.extend(lic if lic else ["(ninguna)"])
    open(out, "w", encoding="utf-8").write("\n".join(lineas))
    print(len(lineas), "lineas ->", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
