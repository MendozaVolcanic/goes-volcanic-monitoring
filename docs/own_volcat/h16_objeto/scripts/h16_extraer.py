r"""H16: pasa a npz la tabla de objeto de VOLCAT y los archivos ASHOBJ de Mauna Loa (solo lectura, sin calcular)."""
import glob, os, sys
import numpy as np
from pyhdf.SD import SD, SDC
LUT = r"D:\goes_notas\busqueda_2026-11-20\volcat_static_anc\volcat-ancillary\luts\GOESR_ASH_object_probability_LUT_Jan11_2017_142742.hdf"
REF = glob.glob(r"D:\goes_cache\volcat_test_mauna_loa\ext\mauna*\reference_data")[0]
OUT = r"D:\goes_cache\h16_objeto\ml"
sd = SD(LUT, SDC.READ)
d = {k: np.asarray(sd.select(k)[:]) for k in sd.datasets()}
np.savez_compressed(os.path.join(OUT, "lut_objeto.npz"), **d)
print("lut", len(d))
for f in sorted(glob.glob(os.path.join(REF, "l2_data", "geocatASHOBJ.*.hdf"))):
    h = os.path.basename(f).split(".")[-2]
    s = SD(f, SDC.READ)
    o = {}
    for k in s.datasets():
        a = np.asarray(s.select(k)[:])
        o[k] = a
    s.end()
    s = SD(glob.glob(os.path.join(REF, "diag_data", f"geocatDIAGS1.*.{h}.hdf"))[0], SDC.READ)
    for k in s.datasets():
        if "_obj_" in k or "Object_Mask" in k or "lower_cloud" in k:
            o["DIAGS1__" + k.split("_15_")[-1]] = np.asarray(s.select(k)[:])
    s.end()
    np.savez_compressed(os.path.join(OUT, f"obj_{h}.npz"), **o)
    print(h, o["ASHOBJ_Object_Id"].shape, flush=True)
