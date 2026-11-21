r"""Etapa 1 de C3 (H15): vuelca la estructura de las LUT de VOLCAT para ABI (HDF4).

Corre con D:\goes_notas\busqueda_2026-11-20\venv_hdf4\Scripts\python.exe -I.
Escribe nombres, formas, tipos, atributos de cada SDS y atributos globales, más
estadísticas por conjunto (min, max, suma, fracción de ceros). No copia las tablas.
"""
import sys
import numpy as np
from pyhdf.SD import SD, SDC

sys.stdout.reconfigure(encoding="utf-8")
LUT = r"D:\goes_notas\busqueda_2026-11-20\volcat_static_anc\volcat-ancillary\luts"
ARCH = {
    "pixel": LUT + r"\GOESR_ASH_pixel_probability_LUT_Jan11_2017_142740.hdf",
    "objeto": LUT + r"\GOESR_ASH_object_probability_LUT_Jan11_2017_142742.hdf",
}


def fmt(v):
    if isinstance(v, (list, tuple)) and len(v) > 12:
        return f"[{len(v)} valores: {v[:6]} ... {v[-3:]}]"
    return repr(v)


def main(cual, salida):
    sd = SD(ARCH[cual], SDC.READ)
    with open(salida, "w", encoding="utf-8") as f:
        f.write(f"# {ARCH[cual]}\n## Atributos globales\n")
        for k, v in sorted(sd.attributes().items()):
            f.write(f"{k} = {fmt(v)}\n")
        f.write("\n## Conjuntos\n")
        for name, (dims, shape, typ, idx) in sorted(sd.datasets().items(), key=lambda x: x[1][3]):
            ds = sd.select(name)
            a = ds.get()
            a = np.asarray(a)
            st = ""
            if a.size and np.issubdtype(a.dtype, np.number):
                st = (f" min={a.min():.4g} max={a.max():.4g} sum={a.sum():.6g} "
                      f"ceros={np.mean(a == 0):.3f}")
            f.write(f"{idx:4d} {name} dims={dims} shape={shape} type={typ}{st}\n")
            for k, v in ds.attributes().items():
                f.write(f"      @{k} = {fmt(v)}\n")
            for dn, dinfo in ds.dimensions(full=1).items():
                f.write(f"      dim {dn}: {dinfo}\n")
            if a.size <= 64:
                f.write(f"      valores = {np.round(a.ravel(), 5).tolist()}\n")
            ds.endaccess()
    sd.end()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
