r"""Etapa 1 de C3 (H15): exporta las densidades de la LUT de píxel de VOLCAT (ABI) a un npz en D:.

Corre con el python de venv_hdf4 (pyhdf). El npz queda FUERA del repo (D:\goes_cache\lut_h15).
Guarda cada conjunto *_ASH_*_PIX / *_CLD_*_PIX con su forma original (orden numpy = inverso del
dblarr de IDL que declara el atributo global del mismo nombre) y los atributos globales numéricos.
"""
import json
import sys

import numpy as np
from pyhdf.SD import SD, SDC

sys.stdout.reconfigure(encoding="utf-8")
LUT = (r"D:\goes_notas\busqueda_2026-11-20\volcat_static_anc\volcat-ancillary\luts"
       r"\GOESR_ASH_pixel_probability_LUT_Jan11_2017_142740.hdf")
OUT = r"D:\goes_cache\lut_h15\lut_pixel.npz"


def main():
    sd = SD(LUT, SDC.READ)
    out = {}
    for name in sd.datasets():
        if name.endswith("_PIX") or "BINS" in name:
            out[name] = np.asarray(sd.select(name).get())
    attrs = {k: (v if not isinstance(v, (bytes,)) else v.decode())
             for k, v in sd.attributes().items()}
    sd.end()
    out["__attrs__"] = np.array(json.dumps(attrs, default=str))
    np.savez_compressed(OUT, **out)
    print(f"{len(out) - 1} conjuntos -> {OUT}")


if __name__ == "__main__":
    main()
