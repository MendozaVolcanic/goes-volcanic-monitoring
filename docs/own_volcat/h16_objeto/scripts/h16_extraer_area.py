import glob, os, numpy as np
from pyhdf.SD import SD, SDC
REF = glob.glob(r"D:\goes_cache\volcat_test_mauna_loa\ext\mauna*\reference_data")[0]
for f in sorted(glob.glob(os.path.join(REF, "l2_data", "geocatL2.*.hdf"))):
    h = os.path.basename(f).split(".")[-2]; s = SD(f, SDC.READ)
    ds = s.select("vcat_ashdet_pix_2_7_10_11_13_14_15_pixel_area"); a = np.asarray(ds[:]).astype(float); at = ds.attributes()
    if at.get("scaling_method",0)==1: a = a*at["scale_factor"]+at["add_offset"]
    np.save(rf"D:\goes_cache\h16_objeto\ml\area_{h}.npy", a); print(h, np.nanpercentile(a,[1,50,99]), at.get("units"))
